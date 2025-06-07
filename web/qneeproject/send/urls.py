#from accounts.form import EmailAuthenticationForm  #INSTALLED_APPSに登録済み
from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

# 2025/02/15時点で参照せず
from django.urls import re_path

app_name = 'send'

urlpatterns = [

  path('regular_send/', views.RegularSendView.as_view(), name='regular_send'),

]
