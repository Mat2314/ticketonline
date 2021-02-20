from .celery import app
import datetime
import logging
import os

now = datetime.datetime.now().strftime("%d-%m-%Y")
logging.basicConfig(filename='logs/{now}.log', format='%(asctime)s:%(levelname)s:%(message)s\n')


@app.task
def clean_old_logs():
    """
    Task is responsible for cleaning (deleting) old files with logs.
    If there are more than MAX_FILES, the oldest file is being deleted until the amount
    of log files is proper.
    :return:
    """
    try:
        # Remove general logs older than 60 days
        directory = 'logs/'
        files = os.listdir(f'{directory}')
        MAX_FILES = 60

        if len(files) > MAX_FILES:
            while len(files) > MAX_FILES:
                oldest_file = files[0]
                smallest_timestamp = os.path.getmtime(f'{directory}{oldest_file}')

                for _file in files:
                    timestamp = os.path.getmtime(f'{directory}{_file}')
                    if timestamp < smallest_timestamp:
                        smallest_timestamp = timestamp
                        oldest_file = _file

                os.remove(f'{directory}{oldest_file}')
                files = os.listdir(f'{directory}')

    except Exception as e:
        print(e)
        logging.warning(e, exc_info=True)
        return
