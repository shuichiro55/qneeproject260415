from .base import *

ALLOWED_HOSTS = ['*']

SECRET_KEY = 'django-insecure-egglb64b%uak^4quaeg^zmt3e=pxvjb4l9ix(-j1vx$r4y1zrg'
#SECRET_KEY = '_kl%xsko4i=-l=23j-b8#tve+wy1^t2-ut((pv*w*0vbge$1y_'

# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases

#DATABASES = {
#  'default': {
#    'ENGINE': 'django.db.backends.sqlite3',
#    'NAME': BASE_DIR / 'db.sqlite3',
#  }
#}

DATABASES = {
  'default': {
    'ENGINE': 'django.db.backends.mysql',
    'NAME': 'qnee_db',
    'USER': 'shuichiro',
    'PASSWORD': '921Story552@',
    'HOST': 'localhost',  # 'mysql',
    'PORT': '53306',
    'ATOMIC_REQUESTS': True, # 最後まで問題なければcommit、例外あればトランザクションはロールバック
  }
}