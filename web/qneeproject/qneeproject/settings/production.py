from .base import *

# .envファイルから読み取るための対応。.envファイルは.gitignoreに加える 24/11/23
# なお、environ.Env()は環境変数からも、バージョン管理外のファイルからも読み取り可能
import os
import environ

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

env = environ.Env()
envpath = os.path.join(BASE_DIR, '.env')
env.read_env(envpath)

SECRET_KEY =env('SECRET_KEY')
ALLOWED_HOSTS =env.list('ALLOWED_HOSTS')
print(f'ALLOWED_HOSTS={ALLOWED_HOSTS}')
#ALLOWED_HOSTS = ['*']

LOGGING = {

  # スキームバージョンは「1」固定
  'version': 1,
  # 既存のロガーを無効化するかどうか
  'disable_existing_loggers': False,

  # ログのフォーマットを定義するフォーマッタ
  # 出力例 [2026-09-09 07:44:02] INFO [app.main:25] サーバーを起動しました。
  'formatters': {   
    # 本番環境用のフォーマッタ
    'production': {
      'format': '[%(asctime)s] %(levelname)s [%(name)s:%(lineno)s] %(message)s',
      'datefmt': '%Y-%m-%d %H:%M:%S',
    },
  },

  # ログの出力先やフォーマットを定義するハンドラ
  'handlers': {

    # 標準出力をするために定義（各ログ設定内のhandlersで'console'と指定）
    'file': {
      'level': 'DEBUG',
      'class': 'logging.FileHandler',
      'filename': '/var/log/{}/app.log'.format(PROJECT_NAME),
      'formatter': 'production', # 下記で定義したformatterを使用する
    },
  },

  # ログの出力レベルを定義するロガー
  'loggers': {

    # Djangoのロガー
    # データベースクエリやリクエスト処理等、Djangoのフレームワークのログ)
    'django': {
      'handlers': ['file'],
      'level': 'DEBUG',
      # DEBUG以上の重要度（DEBUG, INFO, WARNING, ERROR, CRITICAL）の情報を出力
      'propagate': True,
    },

    # アプリケーションのロガー
    # 自分でprint関数などで出力した内容
    'qneeproject': {
      'handlers': ['file'],
      'level': 'DEBUG',
      'propagate': True,
    },
    # その他のロガー
    '': {
      'handlers': ['file'],
      'level': 'DEBUG',
      'propagate': True,
    },
  },
}

# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases

#DATABASES = {
#  'default': {
#    'ENGINE': 'django.db.backends.sqlite3',
#    'NAME': BASE_DIR / 'db.sqlite3',
#  }
#}

# 本番環境でのPROTOCOL, DOMAIN, SITE_URLを設定
PROTOCOL = os.environ.get('SITE_PROTOCOL', 'https')
DOMAIN = os.environ.get('SITE_DOMAIN', 'localhost:8000')
SITE_URL = f"{PROTOCOL}://{DOMAIN}"

#DATABASES = {
#  'default': {
#    'ENGINE': 'django.db.backends.mysql',
#    'NAME': 'qnee_db',
#    'USER': 'shuichiro',
#    'PASSWORD': '921Story552@',
#    'HOST': 'localhost',
#    'PORT': '3306',
#    'ATOMIC_REQUESTS': True, # 最後まで問題なければcommit、例外あればトランザクションはロールバック
#  }
#eixt}