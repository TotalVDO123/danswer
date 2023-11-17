from collections.abc import Callable
from concurrent.futures import as_completed
from concurrent.futures import ThreadPoolExecutor
from typing import Any

from danswer.utils.logger import setup_logger

logger = setup_logger()


def run_functions_tuples_in_parallel(
    functions_with_args: list[tuple[Callable, tuple]],
    allow_failures: bool = False,
) -> list[Any]:
    """
    Executes multiple functions in parallel and returns a list of the results for each function.

    Args:
        functions_with_args: List of tuples each containing the function callable and a tuple of arguments.
        allow_failures: if se to True, then the function result will just be None

    Returns:
        dict: A dictionary mapping function names to their results or error messages.
    """
    results = []
    with ThreadPoolExecutor(max_workers=len(functions_with_args)) as executor:
        future_to_index = {
            executor.submit(func, *args): i
            for i, (func, args) in enumerate(functions_with_args)
        }

        for future in as_completed(future_to_index):
            index = future_to_index[future]
            try:
                results.append((index, future.result()))
            except Exception as e:
                logger.exception(f"Function at index {index} failed due to {e}")
                results.append((index, None))

                if not allow_failures:
                    raise

    results.sort(key=lambda x: x[0])
    return [result for index, result in results]


def run_functions_dict_in_parallel(
    functions_with_args: dict[Callable, tuple],
    allow_failures: bool = False,
) -> dict[str, Any]:
    """
    Executes multiple functions in parallel and returns a dictionary with the results.
    More explicit than the tuples approach but cannot be used to parallelize the same function with
    multiple inputs

    Args:
        functions_with_args (dict): A dictionary mapping functions to a tuple of arguments.
        allow_failures: if se to True, then the function result will just be None

    Returns:
        dict: A dictionary mapping function names to their results or error messages.
    """
    results = {}
    with ThreadPoolExecutor(max_workers=len(functions_with_args)) as executor:
        future_to_function = {
            executor.submit(func, *args): func.__name__
            for func, args in functions_with_args.items()
        }

        for future in as_completed(future_to_function):
            function_name = future_to_function[future]
            try:
                results[function_name] = future.result()
            except Exception as e:
                logger.exception(f"Function {function_name} failed due to {e}")
                results[function_name] = None

                if not allow_failures:
                    raise

    return results
