from .base import *

ALLOWED_HOSTS = ['*']

SECRET_KEY = 'django-insecure-egglb64b%uak^4quaeg^zmt3e=pxvjb4l9ix(-j1vx$r4y1zrg'
#SECRET_KEY = '_kl%xsko4i=-l=23j-b8#tve+wy1^t2-ut((pv*w*0vbge$1y_'

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
      'level': 'DEBUG',
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
