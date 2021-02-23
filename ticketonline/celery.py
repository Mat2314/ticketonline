from celery import Celery
from ticketonline import celeryconfig
from celery.schedules import crontab

app = Celery('ticketonline', broker='amqp://guest:guest@rabbitmq:5672', backend='rpc://',
             include=['ticketonline.tasks'])

app.config_from_object(celeryconfig)

app.conf.beat_schedule = {
    'clean_old_logs': {
        'task': 'ticketonline.tasks.clean_old_logs',
        'schedule': crontab(day_of_month="*", hour="1, 23", minute='0'),
    },
    'cancel_expired_reservations': {
        'task': 'ticketonline.tasks.reservation_expired',
        'schedule': crontab(minute="*")
    },
    'remove_old_reservations': {
        'task': 'ticketonline.tasks.remove_old_reservations',
        'schedule': crontab(day_of_month="*", hour="1", minute="0")
    }
}

if __name__ == '__main__':
    app.start()
