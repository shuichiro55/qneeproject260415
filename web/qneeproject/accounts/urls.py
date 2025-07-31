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

  path('userCreate1_buyer/', views.UserCreateView1_buyer.as_view(), name='userCreate1_buyer'),
  path('userCreate2_buyer/', views.UserCreateView2_buyer.as_view(), name='userCreate2_buyer'),

  path('userCreate1_seller/', views.UserCreateView1_seller.as_view(), name='userCreate1_seller'),
  path('userCreate2_seller/', views.UserCreateView2_seller.as_view(), name='userCreate2_seller'),

  path('userCreate1_admin/', views.UserCreateView1_admin.as_view(), name='userCreate1_admin'),
  path('userCreate2_admin/', views.UserCreateView2_admin.as_view(), name='userCreate2_admin'),

  #path('entitySet_buyer/<token>/', views.EntitySetView_buyer.as_view(), name='entitySet_buyer'),
  #path('<int:user_id>/entity_set_buyer/', views.EntitySetView_buyer.as_view(), name='entity_set_buyer'),

  path('entityCreate_buyer/<token>/', views.EntityCreateView_buyer.as_view(), name='entityCreate_buyer'),
  path('entityCreate_seller/<token>/', views.EntityCreateView_seller.as_view(), name='entityCreate_seller'),   

  path('entityCreate_buyer/', views.EntityCreateView_buyer.as_view(), name='entityCreate_buyer'),
  path('entityCreate_seller/', views.EntityCreateView_seller.as_view(), name='entityCreate_seller'),

  #path('<int:user_id>/entityCreate_buyer/', views.EntityCreateView_buyer.as_view(), name='entityCreate_buyer'),
  #path('<int:user_id>/entityCreate_seller/', views.EntityCreateView_seller.as_view(), name='entityCreate_seller'),

  #開発用
  path('<int:user_id>/<int:entity_id>/agreement_confirm_buyer/', views.AgreementConfirmView_buyer.as_view(), name='agreement_confirm_buyer'),
  path('<int:user_id>/<int:entity_id>/agreement_confirm_seller/', views.AgreementConfirmView_seller.as_view(), name='agreement_confirm_seller'),

  # ★★★ 25/06/17追加 テストはこれから 
  path('userAdd_buyer/<token>', views.UserAddView_buyer.as_view(), name='userAdd_buyer'),

  path('<int:user_id>/passwordChange_buyer/', views.MyPasswordChangeView_buyer.as_view(), name='passwordChange_buyer'),
  path('passwordChange2_buyer/', views.MyPasswordChange2View_buyer.as_view(), name='passwordChange2_buyer'),

  path('<int:user_id>/passwordChange_seller/', views.MyPasswordChangeView_seller.as_view(), name='passwordChange_seller'),
  path('passwordChange2_seller/', views.MyPasswordChange2View_seller.as_view(), name='passwordChange2_seller'),

  path('<int:user_id>/passwordChange_admin/', views.MyPasswordChangeView_admin.as_view(), name='passwordChange_admin'),
  path('passwordChange2_admin/', views.MyPasswordChange2View_admin.as_view(), name='passwordChange2_admin'),

  # 25/04/27 <int:user_id>は要否検討
  path('<int:user_id>/mypage_admin/', views.MyPageView_admin.as_view(), name='mypage_admin'),
  path('mypage_admin/', views.MyPageView_admin.as_view(), name='mypage_admin'),

  path('<int:user_id>/mypage_seller/', views.MyPageView_seller.as_view(), name='mypage_seller'),
  path('mypage_seller/', views.MyPageView_seller.as_view(), name='mypage_seller'),

  path('<int:user_id>/mypage_buyer/', views.MyPageView_buyer.as_view(), name='mypage_buyer'),
  path('mypage_buyer/', views.MyPageView_buyer.as_view(), name='mypage_buyer'),

  path('contact_buyer/', views.ContactView_buyer.as_view(), name='contact_buyer'),  # 24/06/30追加
  path('contact_seller/', views.ContactView_seller.as_view(), name='contact_seller'),  # 24/06/30追加

  path('<int:user_id>/infoEdit_seller/', views.InfoEditView_seller.as_view(), name='infoEdit_seller'),  # 24/08/21追加
  path('infoEdit_seller/', views.InfoEditView_seller.as_view(), name='infoEdit_seller'),  # 24/08/21追加

  #path('<int:user_id>/<int:entity_id>/infoEdit_buyer/', views.InfoEditView_buyer.as_view(), name='info_buyer_seller'),  # 25/05/15追加
  #path('infoEdit_buyer/', views.InfoEditView_seller.as_view(), name='infoEdit_buyer'),  # 25/05/15追加

  path('bankAccountCreate_before/<token>', views.BankAccountCreateView_before.as_view(), name='bankAccountCreate_before'),  # 24/07/14追加
  ## <int:entity_id>だけでよくないか、BankAccountCreateView_beforeでtx_idからentityを抽出している 24/07/21
  path('bankAccountCreate/', views.BankAccountCreateView.as_view(), name='bankAccountCreate'),  # 24/07/14追加
  #path('<int:entity_id>/bankAccountCreate/', views.BankAccountCreateView.as_view(), name='bankAccountCreate'),  # 24/07/14追加
  path('<int:tx_id>/bankAccountCreate/', views.BankAccountCreateView.as_view(), name='bankAccountCreate'),  # 24/07/14追加

]