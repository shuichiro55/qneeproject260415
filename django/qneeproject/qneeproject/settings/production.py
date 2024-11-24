from .base import *

# .envファイルから読み取るための対応。.envファイルは.gitignoreに加える 24/11/23
# なお、environ.Env()は環境変数からも、バージョン管理外のファイルからも読み取り可能
import os
import environ

env = environ.Env()
envpath = os.path.join(BASE_DIR, '.env')
env.read_env(envpath)

SECRET_KEY =env('SECRET_KEY')
ALLOWED_HOSTS =env.list('ALLOWED_HOSTS')
print(f'ALLOWED_HOSTS={ALLOWED_HOSTS}')
#ALLOWED_HOSTS = ['*']

# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases

DATABASES = {
  'default': {
    'ENGINE': 'django.db.backends.sqlite3',
    'NAME': BASE_DIR / 'db.sqlite3',
  }
}

#DATABASES = {
#  'default': {
#    'ENGINE': 'django.db.backends.mysql',
#    'NAME': 'qnee_db',
#    'USER': 'root',
#    'PASSWORD': 'password',
#    'HOST': 'mysql',
#    'PORT': '53306',
#    'ATOMIC_REQUESTS': True, # 最後まで問題なければcommit、例外あればトランザクションはロールバック
#  }
#}