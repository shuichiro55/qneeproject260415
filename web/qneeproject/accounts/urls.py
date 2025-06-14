#from accounts.form import EmailAuthenticationForm  #INSTALLED_APPSに登録済み
from django.urls import path
from . import views
#from .form import SignupForm

app_name = 'accounts'   #23/12/29 動かないので加えてみた

urlpatterns = [

  path('login_buyer/', views.MyLoginView_buyer.as_view(), name='login_buyer'),
  path('login_buyer/<token>', views.MyLoginView_buyer.as_view(), name='login_buyer'),

  path('login_seller/', views.MyLoginView_seller.as_view(), name='login_seller'),
  path('login_seller/<token>', views.MyLoginView_seller.as_view(), name='login_seller'),

  path('login_admin/', views.MyLoginView_admin.as_view(), name='login_admin'),
  path('login_admin/<token>', views.MyLoginView_admin.as_view(), name='login_admin'),

  path('login_redirect/', views.MyLoginRedirect, name='login_redirect'),

  path('logout_buyer/', views.MyLogoutView_buyer, name='logout_buyer'),
  path('logout_seller/', views.MyLogoutView_seller, name='logout_seller'),
  path('logout_admin/', views.MyLogoutView_admin, name='logout_admin'),

  #path('logout_admin/', views.MyLogoutView_admin, name='logout_admin'),
  #path('logout_buyer/', views.MyLogoutView_buyer, name='logout_buyer'),
  #path('logout_seller/', views.MyLogoutView_seller, name='logout_seller'),

  path('user_create_buyer/', views.UserCreateView_buyer.as_view(), name='user_create_buyer'),
  path('user_create2_buyer', views.UserCreateView2_buyer.as_view(), name='user_create2_buyer'),

  path('user_create_seller/', views.UserCreateView_seller.as_view(), name='user_create_seller'),
  path('user_create2_seller', views.UserCreateView2_seller.as_view(), name='user_create2_seller'),

  path('user_create_admin/', views.UserCreateView_admin.as_view(), name='user_create_admin'),
  path('user_create2_admin', views.UserCreateView2_admin.as_view(), name='user_create2_admin'),

  path('entity_set_buyer/<token>/', views.EntitySetView_buyer.as_view(), name='entity_set_buyer'),
  path('<int:user_id>/entity_set_buyer/', views.EntitySetView_buyer.as_view(), name='entity_set_buyer'),

  path('entity_create_buyer/<token>/', views.EntityCreateView_buyer.as_view(), name='entity_create_buyer'),
  path('entity_create_seller/<token>/', views.EntityCreateView_seller.as_view(), name='entity_create_seller'),   

  path('<int:user_id>/entity_create_buyer/', views.EntityCreateView_buyer.as_view(), name='entity_create_buyer'),
  path('<int:user_id>/entity_create_seller/', views.EntityCreateView_seller.as_view(), name='entity_create_seller'),

  #開発用
  path('<int:user_id>/<int:entity_id>/agreement_confirm_buyer/', views.AgreementConfirmView_buyer.as_view(), name='agreement_confirm_buyer'),
  path('<int:user_id>/<int:entity_id>/agreement_confirm_seller/', views.AgreementConfirmView_seller.as_view(), name='agreement_confirm_seller'),

  path('<int:user_id>/password_change_buyer/', views.MyPasswordChangeView_buyer.as_view(), name='password_change_buyer'),
  path('password_change2_buyer/', views.MyPasswordChange2View_buyer.as_view(), name='password_change2_buyer'),

  path('<int:user_id>/password_change_seller/', views.MyPasswordChangeView_seller.as_view(), name='password_change_seller'),
  path('password_change2_seller/', views.MyPasswordChange2View_seller.as_view(), name='password_change2_seller'),

  path('<int:user_id>/password_change_admin/', views.MyPasswordChangeView_admin.as_view(), name='password_change_admin'),
  path('password_change2_admin/', views.MyPasswordChange2View_admin.as_view(), name='password_change2_admin'),

  # 25/04/27 <int:user_id>は要否検討
  path('<int:user_id>/mypage_admin/', views.MyPageView_admin.as_view(), name='mypage_admin'),
  path('mypage_admin/', views.MyPageView_admin.as_view(), name='mypage_admin'),

  path('<int:user_id>/mypage_seller/', views.MyPageView_seller.as_view(), name='mypage_seller'),
  path('mypage_seller/', views.MyPageView_seller.as_view(), name='mypage_seller'),

  path('<int:user_id>/mypage_buyer/', views.MyPageView_buyer.as_view(), name='mypage_buyer'),
  path('mypage_buyer/', views.MyPageView_buyer.as_view(), name='mypage_buyer'),

  path('contact_buyer/', views.ContactView_buyer.as_view(), name='contact_buyer'),  # 24/06/30追加
  path('contact_seller/', views.ContactView_seller.as_view(), name='contact_seller'),  # 24/06/30追加

  path('<int:user_id>/<int:entity_id>/info_edit_seller/', views.InfoEditView_seller.as_view(), name='info_edit_seller'),  # 24/08/21追加
  path('info_edit_seller/', views.InfoEditView_seller.as_view(), name='info_edit_seller'),  # 24/08/21追加

  #path('<int:user_id>/<int:entity_id>/info_edit_buyer/', views.InfoEditView_buyer.as_view(), name='info_buyer_seller'),  # 25/05/15追加
  #path('info_edit_buyer/', views.InfoEditView_seller.as_view(), name='info_edit_buyer'),  # 25/05/15追加

  path('bankaccount_create_before/<token>', views.BankAccountCreateView_before.as_view(), name='bankaccount_create_before'),  # 24/07/14追加
  ## <int:entity_id>だけでよくないか、BankAccountCreateView_beforeでtx_idからentityを抽出している 24/07/21
  path('<int:entity_id>/bankaccount_create/', views.BankAccountCreateView.as_view(), name='bankaccount_create'),  # 24/07/14追加
  path('<int:tx_id>/<int:entity_id>/bankaccount_create/', views.BankAccountCreateView.as_view(), name='bankaccount_create'),  # 24/07/14追加

]