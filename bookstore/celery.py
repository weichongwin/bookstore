import os
from celery import Celery

#设置django的默认设置模型
os.environ.setdefault('DJANGO_SETTINGS_MODULE','bookstore.settings')

app = Celery('bookstore',broker='redis://:950815@127.0.0.1:6379/6')

app.config_from_object('django.conf:settings', namespace='CELERY')

app.autodiscover_tasks()

@app.task(bind=True)
def debug_task(self):
    print('Request: {0!r}'.format(self.request))