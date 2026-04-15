from __future__ import absolute_import, unicode_literals
import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'qneeproject.settings.local')

app = Celery('qneeproject')

# 'CELERY_' という接頭辞を持つ設定を、設定ファイルからsettings.pyから読み込む
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

# Celery Beatの設定
from datetime import date
import calendar

today = date.today()

# calendar.monthrangeは指定した年月の日数（月末）を返す
endOfMonth = calendar.monthrange(today.year, today.month)[1]

app.conf.beat_schedule = {
  'run-every-10th-20th-EOMONTH': {
    'task': 'send.tasks.sendServInfoMailNow',
    'schedule': crontab(day_of_month='10,20,'+ str(endOfMonth), hour=8, minute=0),
    'args': (),
  },
}
