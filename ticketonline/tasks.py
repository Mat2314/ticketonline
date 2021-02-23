from .celery import app
import datetime
import logging
import os
from ticketonline.apps.events.models import Reservation
from datetime import timedelta
import pytz

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


@app.task
def reservation_expired():
    """
    Task is a worker which checks every minute whether there are any expired reservations with PENDING status
    and if so, it changes reservation status to CANCELLED.
    :return:
    """
    try:
        # Get all pending reservations and current datetime
        pending_reservations = Reservation.objects.filter(status="PENDING")
        now = datetime.datetime.utcnow().replace(tzinfo=pytz.utc)

        # Iterate over reservations and change their status if 15 minutes buffer has already passed
        for reservation in pending_reservations:
            if reservation.pending_until < now:
                reservation.status = "CANCELLED"
                reservation.save()
    except Exception as e:
        print(e)
        logging.warning(e, exc_info=True)


@app.task
def remove_old_reservations():
    """
    Task removes reservations older than 100 days.
    :return:
    """
    try:
        reservations = Reservation.objects.all()
        now = datetime.datetime.utcnow().replace(tzinfo=pytz.utc)

        for reservation in reservations:
            if reservation.reservation_date < now - timedelta(days=100):
                # Remove reservations older than 100 days
                reservation.delete()

    except Exception as e:
        print(e)
        logging.warning(e, exc_info=True)
