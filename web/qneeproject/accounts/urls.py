#from accounts.form import EmailAuthenticationForm  #INSTALLED_APPSに登録済み
from django.urls import path, reverse_lazy
from . import views
#from .form import SignupForm

from .models import CustomUser

app_name = 'accounts'   #23/12/29 動かないので加えてみた

urlpatterns = [

  path('login_buyer/', views.MyLoginView_buyer.as_view(), name='login_buyer'),
  path('login_buyer/<str:token>', views.MyLoginView_buyer.as_view(), name='login_buyer'),
  path('login_buyer/<str:afterLogin>/<str:token>', views.MyLoginView_buyer.as_view(), name='login_buyer'),

  path('login_seller/', views.MyLoginView_seller.as_view(), name='login_seller'),
  path('login_seller/<token>', views.MyLoginView_seller.as_view(), name='login_seller'),
  path('login_seller/<str:afterLogin>/<str:token>', views.MyLoginView_seller.as_view(), name='login_seller'),

  path('login_admin/', views.MyLoginView_admin.as_view(), name='login_admin'),
  path('login_admin/<token>', views.MyLoginView_admin.as_view(), name='login_admin'),
  path('login_admin/<str:afterLogin>/<str:token>', views.MyLoginView_admin.as_view(), name='login_admin'),

  path('login_redirect/', views.MyLoginRedirect, name='login_redirect'),

  path('logout_buyer/', views.MyLogoutView_buyer, name='logout_buyer'),
  path('logout_seller/', views.MyLogoutView_seller, name='logout_seller'),
  path('logout_admin/', views.MyLogoutView_admin, name='logout_admin'),

  #path('logout_admin/', views.MyLogoutView_admin, name='logout_admin'),
  #path('logout_buyer/', views.MyLogoutView_buyer, name='logout_buyer'),
  #path('logout_seller/', views.MyLogoutView_seller, name='logout_seller'),

  path('userCreate_buyer/', views.UserCreateView_buyer.as_view(), name='userCreate_buyer'),
  path('userCreate_seller/', views.UserCreateView_seller.as_view(), name='userCreate_seller'),
  path('userCreate_admin/', views.UserCreateView_admin.as_view(), name='userCreate_admin'),

  #path('entitySet_buyer/<token>/', views.EntitySetView_buyer.as_view(), name='entitySet_buyer'),
  #path('<int:user_id>/entity_set_buyer/', views.EntitySetView_buyer.as_view(), name='entity_set_buyer'),

  path('entityCreate_buyer/<token>/', views.EntityCreateView_buyer.as_view(), name='entityCreate_buyer'),
  path('entityCreate_seller/<token>/', views.EntityCreateView_seller.as_view(), name='entityCreate_seller'),   

  path('entityCreate_buyer/', views.EntityCreateView_buyer.as_view(), name='entityCreate_buyer'),
  path('entityCreate_seller/', views.EntityCreateView_seller.as_view(), name='entityCreate_seller'),

  # テスト用（開発段階だけ）
  path('<int:user_id>/entityCreate_buyer/', views.EntityCreateView_buyer.as_view(), name='entityCreate_buyer'),
  path('<int:user_id>/entityCreate_seller/', views.EntityCreateView_seller.as_view(), name='entityCreate_seller'),

  path('agreementConfirm_buyer/', views.AgreementConfirmView_buyer.as_view(), name='agreementConfirm_buyer'),
  path('agreementConfirm_seller/', views.AgreementConfirmView_seller.as_view(), name='agreementConfirm_seller'),

  # 開発段階だけ設定
  path('<int:user_id>/<int:entity_id>/agreementConfirm_buyer/', views.AgreementConfirmView_buyer.as_view(), name='agreementConfirm_buyer'),
  path('<int:user_id>/<int:entity_id>/agreementConfirm_seller/', views.AgreementConfirmView_seller.as_view(), name='agreementConfirm_seller'),

  # ★★ 25/08/29追加 テストはこれから
  #path('permissionList_buyer', views.PermissionUpdateView_buyer.as_view(), name='permissionList_buyer'),
  path('permissionSets_buyer', views.PermissionSetsView_buyer.as_view(), name='permissionSets_buyer'),
  path('permissionSets_seller', views.PermissionSetsView_seller.as_view(), name='permissionSets_seller'),
  path('permissionSets_admin', views.PermissionSetsView_admin.as_view(), name='permissionSets_admin'),

  # ★★ 25/06/17追加 テストはこれから、 tokenは申請したユーザーのid
  path('<str:token>/userAddPre_buyer', views.UserAddPreView_buyer.as_view(), name='userAddPre_buyer'),
  path('<str:token>/userAddPre_seller', views.UserAddPreView_seller.as_view(), name='userAddPre_seller'),
  path('<str:token>/buyUserAddPre_admin', views.BuyUserAddPreView_admin.as_view(), name='buyUserAddPre_admin'),

  # userAddPreViewから呼ばれるView
  path('<int:applyUser_id>/userAdd_buyer', views.UserAddView_buyer.as_view(), name='userAdd_buyer'),
  path('<int:applyUser_id>/userAdd_seller', views.UserAddView_seller.as_view(), name='userAdd_seller'),
  path('<int:applyUser_id>/buyUserAdd_admin', views.BuyUserAddView_admin.as_view(), name='buyUserAdd_admin'),

  # InfoEdit.htmlから呼ばれるView
  path('userAdd_buyer', views.UserAddView_buyer.as_view(), name='userAdd_buyer'),
  path('userAdd_seller', views.UserAddView_seller.as_view(), name='userAdd_seller'),
  path('buyUserAdd_admin', views.BuyUserAddView_admin.as_view(), name='buyUserAdd_admin'),

  path('<str:token>/corpInfoUpdatePre_admin', views.CorpInfoUpdatePreView_admin.as_view(), name='corpInfoUpdatePre_admin'),
  path('<int:corpInfo_id>/corpInfoUpdate_admin', views.CorpInfoUpdateView_admin.as_view(), name='corpInfoUpdate_admin'),
  path('corpInfoUpdate_admin', views.CorpInfoUpdateView_admin.as_view(), name='corpInfoUpdate_admin'),

  path('passwordChange_buyer/', views.MyPasswordChangeView_buyer.as_view(), name='passwordChange_buyer'),
  #path('passwordChange2_buyer/', views.MyPasswordChange2View_buyer.as_view(), name='passwordChange2_buyer'),

  path('passwordChange_seller/', views.MyPasswordChangeView_seller.as_view(), name='passwordChange_seller'),
  #path('passwordChange2_seller/', views.MyPasswordChange2View_seller.as_view(), name='passwordChange2_seller'),

  path('passwordChange_admin/', views.MyPasswordChangeView_admin.as_view(), name='passwordChange_admin'),
  #path('passwordChange2_admin/', views.MyPasswordChange2View_admin.as_view(), name='passwordChange2_admin'),

  path('<int:user_id>/mypage_seller/', views.MyPageView_seller.as_view(), name='mypage_seller'),
  path('mypage_seller/', views.MyPageView_seller.as_view(), name='mypage_seller'),

  path('<int:user_id>/mypage_buyer/', views.MyPageView_buyer.as_view(), name='mypage_buyer'),
  path('mypage_buyer/', views.MyPageView_buyer.as_view(), name='mypage_buyer'),

  # 25/04/27 <int:user_id>は要否検討
  # path('<int:user_id>/mypage_admin/', views.MyPageView_admin.as_view(), name='mypage_admin'),
  path('<int:user_id>/mypage_admin/', views.MyPageView_admin.as_view(), name='mypage_admin'),
  path('mypage_admin/', views.MyPageView_admin.as_view(), name='mypage_admin'),


  path('contact_buyer/', views.ContactView_buyer.as_view(), name='contact_buyer'),  # 24/06/30追加
  path('contact_seller/', views.ContactView_seller.as_view(), name='contact_seller'),  # 24/06/30追加

  # ★★ 260502 使っているのか確認して削除
  #path('<int:user_id>/infoEdit_buyer/', views.InfoEditView_buyer.as_view(), name='infoEdit_buyer'),  # 24/08/21追加
  path('infoEdit_buyer/', views.InfoEditView_buyer.as_view(), name='infoEdit_buyer'),  # 24/08/21追加

  #path('<int:user_id>/infoEdit_seller/', views.InfoEditView_seller.as_view(), name='infoEdit_seller'),  # 24/08/21追加
  path('infoEdit_seller/', views.InfoEditView_seller.as_view(), name='infoEdit_seller'),  # 24/08/21追加

  #path('<int:user_id>/infoEdit_admin/', views.InfoEditView_admin.as_view(), name='infoEdit_admin'),  # 24/08/21追加
  path('infoEdit_admin/', views.InfoEditView_admin.as_view(), name='infoEdit_admin'),  # 26/2/20追加

  #path('<int:user_id>/<int:entity_id>/infoEdit_buyer/', views.InfoEditView_buyer.as_view(), name='info_buyer_seller'),  # 25/05/15追加
  #path('infoEdit_buyer/', views.InfoEditView_seller.as_view(), name='infoEdit_buyer'),  # 25/05/15追加

  path('bankAccountCreate_before/<token>', views.BankAccountCreateView_before.as_view(), name='bankAccountCreate_before'),  # 24/07/14追加
  ## <int:entity_id>だけでよくないか、BankAccountCreateView_beforeでtx_idからentityを抽出している 24/07/21
  path('bankAccountCreate/', views.BankAccountCreateView.as_view(), name='bankAccountCreate'),  # 24/07/14追加
  #path('<int:entity_id>/bankAccountCreate/', views.BankAccountCreateView.as_view(), name='bankAccountCreate'),  # 24/07/14追加
  path('<int:tx_id>/bankAccountCreate/', views.BankAccountCreateView.as_view(), name='bankAccountCreate'),  # 24/07/14追加

  path('passwordReset_buyer/', views.MyPasswordResetView_buyer.as_view(), name='passwordReset_buyer'),
  path('accounts/passwordResetDone_buyer/', views.MyPasswordResetDoneView_buyer.as_view(), name='passwordResetDone_buyer'),
  path('passwordReset_buyer/<uidb64>/<token>/', views.MyPasswordResetConfirmView_buyer.as_view(), name='passwordResetConfirm_buyer'),

  path('passwordReset_seller/', views.MyPasswordResetView_seller.as_view(), name='passwordReset_seller'),
  path('accounts/passwordResetDone_seller/', views.MyPasswordResetDoneView_seller.as_view(), name='passwordResetDone_seller'),
  path('passwordReset_seller/<uidb64>/<token>/', views.MyPasswordResetConfirmView_seller.as_view(), name='passwordResetConfirm_seller'),

  path('passwordReset_admin/', views.MyPasswordResetView_admin.as_view(), name='passwordReset_admin'),
  path('accounts/passwordResetDone_admin/', views.MyPasswordResetDoneView_admin.as_view(), name='passwordResetDone_admin'),
  path('passwordReset_admin/<uidb64>/<token>/', views.MyPasswordResetConfirmView_admin.as_view(), name='passwordResetConfirm_admin'),

  path('profileEdit_buyer/', views.ProfileEditView_buyer.as_view(), name='profileEdit_buyer'),  # 24/08/21追加
  path('profileEdit_seller/', views.ProfileEditView_seller.as_view(), name='profileEdit_seller'),  # 24/08/21追加

]