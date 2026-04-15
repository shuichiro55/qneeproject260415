# この下の3行は後で消す 25/02/28
import sys
print(sys.executable)

import pymysql
pymysql.install_as_MySQLdb()

# 260331 celery.py があっても、Djangoの起動時にCeleryアプリが
# 読み込まれない場合があるとのことで追加
from .settings.celery import app as celery_app

__all__ = ('celery_app',)