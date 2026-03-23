#from accounts.form import EmailAuthenticationForm  #INSTALLED_APPSに登録済み
from django.urls import path
from . import views

# 2025/10/10時点で参照せず
#from django.urls import re_path
#from django.conf import settings
#from django.conf.urls.static import static

app_name = 'send'

urlpatterns = [

  path('invitationSets/', views.InvitationSetsView.as_view(), name='invitationSets'),
  path('<int:buyUser_id>/<int:buyEntity>/invitationSets/', views.InvitationSetsView.as_view(), name='invitationSets'),

  path('invitationAgt/', views.InvitationAgtView.as_view(), name='invitationAgt'),

  # 小原さんのコード
  path('register/', views.register, name='register'),
  #path('member/', views.member, name='member'),
  #path('<int:user_id><int:entity_id>/member/', views.member, name='member'),  path('import/', views.import_csv, name='import'),
  path('export/', views.export_csv, name='export'),  # 251010追加 txlist_buyer_mail_settings.htmlから呼ばれている 
  path('import/finalize/', views.finalize_import, name='finalize_import'),

]
