from sqlalchemy.orm import Session

from danswer.configs.chat_configs import BASE_RECENCY_DECAY
from danswer.configs.chat_configs import DISABLE_LLM_DOC_RELEVANCE
from danswer.configs.chat_configs import EDIT_KEYWORD_QUERY
from danswer.configs.chat_configs import FAVOR_RECENT_DECAY_MULTIPLIER
from danswer.configs.chat_configs import HYBRID_ALPHA
from danswer.configs.chat_configs import HYBRID_ALPHA_KEYWORD
from danswer.configs.chat_configs import NUM_RETURNED_HITS
from danswer.db.models import User
from danswer.llm.interfaces import LLM
from danswer.natural_language_processing.search_nlp_models import QueryAnalysisModel
from danswer.search.enums import LLMEvaluationType
from danswer.search.enums import RecencyBiasSetting
from danswer.search.models import BaseFilters
from danswer.search.models import IndexFilters
from danswer.search.models import SearchQuery
from danswer.search.models import SearchRequest
from danswer.search.models import SearchType
from danswer.search.postprocessing.reranker import get_reranking_settings
from danswer.search.preprocessing.access_filters import build_access_filters_for_user
from danswer.search.retrieval.search_runner import remove_stop_words_and_punctuation
from danswer.secondary_llm_flows.source_filter import extract_source_filter
from danswer.secondary_llm_flows.time_filter import extract_time_filter
from danswer.utils.logger import setup_logger
from danswer.utils.threadpool_concurrency import FunctionCall
from danswer.utils.threadpool_concurrency import run_functions_in_parallel
from danswer.utils.timing import log_function_time


logger = setup_logger()


def query_analysis(query: str) -> tuple[bool, list[str]]:
    analysis_model = QueryAnalysisModel()
    return analysis_model.predict(query)


@log_function_time(print_only=True)
def retrieval_preprocessing(
    search_request: SearchRequest,
    user: User | None,
    llm: LLM,
    db_session: Session,
    bypass_acl: bool = False,
    skip_query_analysis: bool = False,
    base_recency_decay: float = BASE_RECENCY_DECAY,
    favor_recent_decay_multiplier: float = FAVOR_RECENT_DECAY_MULTIPLIER,
) -> SearchQuery:
    """Logic is as follows:
    Any global disables apply first
    Then any filters or settings as part of the query are used
    Then defaults to Persona settings if not specified by the query
    """
    query = search_request.query
    limit = search_request.limit
    offset = search_request.offset
    persona = search_request.persona

    preset_filters = search_request.human_selected_filters or BaseFilters()
    if persona and persona.document_sets and preset_filters.document_set is None:
        preset_filters.document_set = [
            document_set.name for document_set in persona.document_sets
        ]

    time_filter = preset_filters.time_cutoff
    source_filter = preset_filters.source_type

    auto_detect_time_filter = True
    auto_detect_source_filter = True
    if not search_request.enable_auto_detect_filters:
        logger.debug("Retrieval details disables auto detect filters")
        auto_detect_time_filter = False
        auto_detect_source_filter = False
    elif persona and persona.llm_filter_extraction is False:
        logger.debug("Persona disables auto detect filters")
        auto_detect_time_filter = False
        auto_detect_source_filter = False

    if (
        time_filter is not None
        and persona
        and persona.recency_bias != RecencyBiasSetting.AUTO
    ):
        auto_detect_time_filter = False
        logger.debug("Not extract time filter - already provided")
    if source_filter is not None:
        logger.debug("Not extract source filter - already provided")
        auto_detect_source_filter = False

    # Based on the query figure out if we should apply any hard time filters /
    # if we should bias more recent docs even more strongly
    run_time_filters = (
        FunctionCall(extract_time_filter, (query, llm), {})
        if auto_detect_time_filter
        else None
    )

    # Based on the query, figure out if we should apply any source filters
    run_source_filters = (
        FunctionCall(extract_source_filter, (query, llm, db_session), {})
        if auto_detect_source_filter
        else None
    )

    run_query_analysis = (
        None if skip_query_analysis else FunctionCall(query_analysis, (query,), {})
    )

    functions_to_run = [
        filter_fn
        for filter_fn in [
            run_time_filters,
            run_source_filters,
            run_query_analysis,
        ]
        if filter_fn
    ]
    parallel_results = run_functions_in_parallel(functions_to_run)

    predicted_time_cutoff, predicted_favor_recent = (
        parallel_results[run_time_filters.result_id]
        if run_time_filters
        else (None, None)
    )
    predicted_source_filters = (
        parallel_results[run_source_filters.result_id] if run_source_filters else None
    )

    # The extracted keywords right now are not very reliable, not using for now
    # Can maybe use for highlighting
    is_keyword, extracted_keywords = (
        parallel_results[run_query_analysis.result_id]
        if run_query_analysis
        else (None, None)
    )

    all_query_terms = query.split()
    processed_keywords = (
        remove_stop_words_and_punctuation(all_query_terms)
        if EDIT_KEYWORD_QUERY
        else all_query_terms
    )

    user_acl_filters = (
        None if bypass_acl else build_access_filters_for_user(user, db_session)
    )
    final_filters = IndexFilters(
        source_type=preset_filters.source_type or predicted_source_filters,
        document_set=preset_filters.document_set,
        time_cutoff=preset_filters.time_cutoff or predicted_time_cutoff,
        tags=preset_filters.tags,  # Tags are never auto-extracted
        access_control_list=user_acl_filters,
    )

    llm_evaluation_type = LLMEvaluationType.BASIC
    if search_request.evaluation_type is not LLMEvaluationType.UNSPECIFIED:
        llm_evaluation_type = search_request.evaluation_type

    elif persona:
        llm_evaluation_type = (
            LLMEvaluationType.BASIC
            if persona.llm_relevance_filter
            else LLMEvaluationType.SKIP
        )

    if DISABLE_LLM_DOC_RELEVANCE:
        if llm_evaluation_type:
            logger.info(
                "LLM chunk filtering would have run but has been globally disabled"
            )
        llm_evaluation_type = LLMEvaluationType.SKIP

    rerank_settings = search_request.rerank_settings
    # If not explicitly specified by the query, use the current settings
    if rerank_settings is None:
        saved_reranking_settings = get_reranking_settings()
        if not saved_reranking_settings:
            rerank_settings = None
        # For non-streaming flows, the rerank settings are applied at the search_request level
        elif not saved_reranking_settings.disable_for_streaming:
            rerank_settings = saved_reranking_settings.to_reranking_model_detail()

    # Decays at 1 / (1 + (multiplier * num years))
    if persona and persona.recency_bias == RecencyBiasSetting.NO_DECAY:
        recency_bias_multiplier = 0.0
    elif persona and persona.recency_bias == RecencyBiasSetting.BASE_DECAY:
        recency_bias_multiplier = base_recency_decay
    elif persona and persona.recency_bias == RecencyBiasSetting.FAVOR_RECENT:
        recency_bias_multiplier = base_recency_decay * favor_recent_decay_multiplier
    else:
        if predicted_favor_recent:
            recency_bias_multiplier = base_recency_decay * favor_recent_decay_multiplier
        else:
            recency_bias_multiplier = base_recency_decay

    hybrid_alpha = HYBRID_ALPHA_KEYWORD if is_keyword else HYBRID_ALPHA
    if search_request.hybrid_alpha:
        hybrid_alpha = search_request.hybrid_alpha

    return SearchQuery(
        query=query,
        processed_keywords=processed_keywords,
        search_type=SearchType.KEYWORD if is_keyword else SearchType.SEMANTIC,
        evaluation_type=llm_evaluation_type,
        filters=final_filters,
        hybrid_alpha=hybrid_alpha,
        recency_bias_multiplier=recency_bias_multiplier,
        num_hits=limit if limit is not None else NUM_RETURNED_HITS,
        offset=offset or 0,
        rerank_settings=rerank_settings,
        chunks_above=search_request.chunks_above,
        chunks_below=search_request.chunks_below,
        full_doc=search_request.full_doc,
    )
