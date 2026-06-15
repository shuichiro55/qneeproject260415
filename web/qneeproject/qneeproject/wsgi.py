"""
WSGI config for qneeproject project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'qneeproject.settings.production')
# Djangoの設定いついて、wsgi.py内で設定ファイル*.pyを指定する

application = get_wsgi_application()
# WSGIアプリケーションオブジェクトをセット