import datetime
import logging
from django.http import JsonResponse

now = datetime.datetime.now().strftime("%d-%m-%Y")
logging.basicConfig(filename=f'logs/{now}.log', format='%(asctime)s:%(levelname)s:%(message)s\n')


def log_exceptions(info):
    """
        Log all the views exceptions into particular files.
    """

    def inner_function(func):
        def wrapper(*args, **kwargs):
            try:
                return_value = func(*args, **kwargs)
                return return_value
            except Exception as e:
                print(f'Exception in function: {func.__name__}\n{e}')
                logging.warning(e, exc_info=True)
                return JsonResponse({"error": "Could not process request", "message": info})

        return wrapper

    return inner_function
