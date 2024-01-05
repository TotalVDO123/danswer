from danswer.configs.chat_configs import QA_PROMPT_OVERRIDE
from danswer.configs.chat_configs import QA_TIMEOUT
from danswer.db.models import Prompt
from danswer.llm.exceptions import GenAIDisabledException
from danswer.llm.factory import get_default_llm
from danswer.one_shot_answer.interfaces import QAModel
from danswer.one_shot_answer.qa_block import PromptBasedQAHandler
from danswer.one_shot_answer.qa_block import QABlock
from danswer.one_shot_answer.qa_block import QAHandler
from danswer.one_shot_answer.qa_block import SingleMessageQAHandler
from danswer.one_shot_answer.qa_block import SingleMessageScratchpadHandler
from danswer.one_shot_answer.qa_block import WeakLLMQAHandler
from danswer.utils.logger import setup_logger

logger = setup_logger()


def get_default_qa_handler(
    chain_of_thought: bool = False,
    user_selection: str | None = QA_PROMPT_OVERRIDE,
) -> QAHandler:
    if user_selection:
        if user_selection.lower() == "default":
            return SingleMessageQAHandler()
        if user_selection.lower() == "cot":
            return SingleMessageScratchpadHandler()
        if user_selection.lower() == "weak":
            return WeakLLMQAHandler()

        raise ValueError("Invalid Question-Answering prompt selected")

    if chain_of_thought:
        return SingleMessageScratchpadHandler()

    return SingleMessageQAHandler()


def get_default_qa_model(
    api_key: str | None = None,
    timeout: int = QA_TIMEOUT,
    chain_of_thought: bool = False,
) -> QAModel:
    llm = get_default_llm(api_key=api_key, timeout=timeout)
    qa_handler = get_default_qa_handler(chain_of_thought=chain_of_thought)

    return QABlock(
        llm=llm,
        qa_handler=qa_handler,
    )


def get_prompt_qa_model(
    prompt: Prompt,
    api_key: str | None = None,
    timeout: int = QA_TIMEOUT,
    llm_version: str | None = None,
) -> QAModel:
    return QABlock(
        llm=get_default_llm(
            api_key=api_key,
            timeout=timeout,
            gen_ai_model_version_override=llm_version,
        ),
        qa_handler=PromptBasedQAHandler(
            system_prompt=prompt.system_prompt, task_prompt=prompt.task_prompt
        ),
    )


def get_question_answer_model(
    prompt: Prompt | None,
    api_key: str | None = None,
    timeout: int = QA_TIMEOUT,
    chain_of_thought: bool = False,
    llm_version: str | None = None,
    qa_model_version: str | None = QA_PROMPT_OVERRIDE,
) -> QAModel | None:
    if chain_of_thought:
        raise NotImplementedError("COT has been disabled")

    if prompt is not None and chain_of_thought:
        raise RuntimeError(
            "Cannot choose COT prompt with a customized Prompt object. "
            "User can prompt the model to output COT themselves if they want."
        )

    try:
        llm = get_default_llm(
            api_key=api_key,
            timeout=timeout,
            gen_ai_model_version_override=llm_version,
        )
    except GenAIDisabledException:
        return None

    if qa_model_version == "weak":
        qa_handler: QAHandler = WeakLLMQAHandler(
            system_prompt=system_prompt, task_prompt=task_prompt
        )
    else:
        qa_handler = SingleMessageQAHandler(
            system_prompt=system_prompt, task_prompt=task_prompt
        )

    return QABlock(llm=llm, qa_handler=qa_handler)
