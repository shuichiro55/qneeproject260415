from .base import *
import environ

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

env = environ.Env()
envpath = '/var/www/app1/web/qneeproject/.env'
env.read_env(envpath)

# --- ここを追加・修正 --- 20260927
# .env から SECRET_KEY を読み込む（見つからない場合のデフォルト値も設定可能）
SECRET_KEY = env('SECRET_KEY', default='django-insecure-fallback-dev-key')

# 開発環境では「http」しか対応していない
PROTOCOL = os.environ.get('SITE_PROTOCOL', 'http')
DOMAIN = os.environ.get('SITE_DOMAIN', 'localhost:8000')
SITE_URL = f"{PROTOCOL}://{DOMAIN}"

LOGGING = {

  # スキームバージョンは「1」固定
  'version': 1,
  # 既存のロガーを無効化するかどうか
  'disable_existing_loggers': False,


  # ログのフォーマットを定義するフォーマッタ
  # 出力例 [2026-09-09 07:44:02] INFO [app.main:25] サーバーを起動しました。
  'formatters': {
    # 開発環境用のフォーマッタ
    'developement': {
      'format': '[%(asctime)s] %(levelname)s [%(name)s:%(lineno)s] %(message)s',
      'datefmt': '%Y-%m-%d %H:%M:%S',
    },
  },

  # ログの出力先やフォーマットを定義するハンドラ
  'handlers': {

    # 標準出力をするために定義（各ログ設定内のhandlersで'console'と指定）
    'console': {
      'class': 'logging.StreamHandler', # StreamHandler(標準出力機能)を使用
      'formatter': 'developement', # 下記で定義したformatterを使用する
    },
  },


  # ログの出力レベルを定義するロガー
  'loggers': {

    # Djangoのロガー
    # データベースクエリやリクエスト処理等、Djangoのフレームワークのログ)
    'django': {
      'handlers': ['console'],
      'level': 'INFO',
      # DEBUG以上の重要度（DEBUG, INFO, WARNING, ERROR, CRITICAL）の情報を出力
      'propagate': True,
    },

    # アプリケーションのロガー
    # 自分でprint関数などで出力した内容
    'qneeproject': {
      'handlers': ['console'],
      'level': 'DEBUG',
      'propagate': True,
    },
    # その他のロガー
    '': {
      'handlers': ['console'],
      'level': 'DEBUG',
      'propagate': True,
    },
  },
}

# DATABASESはbase.py

# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases

#DATABASES = {
#  'default': {
#    'ENGINE': 'django.db.backends.sqlite3',
#    'NAME': BASE_DIR / 'db.sqlite3',
#  }
#}
