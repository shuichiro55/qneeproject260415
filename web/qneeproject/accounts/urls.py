#from accounts.form import EmailAuthenticationForm  #INSTALLED_APPSに登録済み
from django.urls import path
from . import views
#from .form import SignupForm

app_name = 'accounts'   #23/12/29 動かないので加えてみた

urlpatterns = [

    path('login_buyer/', views.MyLoginView_buyer.as_view(), name='login_buyer'),
    path('login_buyer/<token>/', views.MyLoginView_buyer.as_view(), name='login_buyer'),

    path('login_seller/', views.MyLoginView_seller.as_view(), name='login_seller'),
    path('login_seller/<token>/', views.MyLoginView_seller.as_view(), name='login_seller'),

    path('login_redirect/', views.MyLoginRedirect, name='login_redirect'),

    path('logout_buyer/', views.MyLogoutView_buyer, name='logout_buyer'),
    path('logout_seller/', views.MyLogoutView_seller, name='logout_seller'),


    path('user_create_buyer/', views.UserCreateView_buyer.as_view(), name='user_create_buyer'),
    path('user_create_seller/', views.UserCreateView_seller.as_view(), name='user_create_seller'),

    path('user_create_done_buyer', views.UserCreateDone_buyer.as_view(), name='user_create_done_buyer'),
    path('user_create_done_seller', views.UserCreateDone_seller.as_view(), name='user_create_done_seller'),
    # path('user_create/complete/<token>/', views.UserCreateComplete.as_view(), name='user_create_complete'),

    path('entity_create_seller/<token>/', views.EntityCreateView_seller.as_view(), name='entity_create_seller'),   
    path('entity_create_buyer/<token>/', views.EntityCreateView_buyer.as_view(), name='entity_create_buyer'),

    path('<int:user_id>/entity_create_seller/', views.EntityCreateView_seller.as_view(), name='entity_create_seller'),
    path('<int:user_id>/entity_create_buyer/', views.EntityCreateView_buyer.as_view(), name='entity_create_buyer'),

    #開発用
    path('<int:user_id>/<int:entity_id>/agreement_confirm_buyer/', views.AgreementConfirmView_buyer.as_view(), name='agreement_confirm_buyer'),
    path('<int:user_id>/<int:entity_id>/agreement_confirm_seller/', views.AgreementConfirmView_seller.as_view(), name='agreement_confirm_seller'),

    path('<int:user_id>/mypage_seller/', views.MyPageView_seller.as_view(), name='mypage_seller'),
    path('mypage_seller/', views.MyPageView_seller.as_view(), name='mypage_seller'),

    path('<int:user_id>/mypage_buyer/', views.MyPageView_buyer.as_view(), name='mypage_buyer'),
    path('mypage_buyer/', views.MyPageView_buyer.as_view(), name='mypage_buyer'),

    path('contact_buyer/', views.ContactView_buyer.as_view(), name='contact_buyer'),  # 24/06/30追加
    path('contact_seller/', views.ContactView_seller.as_view(), name='contact_seller'),  # 24/06/30追加

    path('<int:user_id>/<int:entity_id>/info_edit_seller/', views.InfoEditView_seller.as_view(), name='info_edit_seller'),  # 24/08/21追加
    path('info_edit_seller/', views.InfoEditView_seller.as_view(), name='info_edit_seller'),  # 24/08/21追加

    path('bankaccount_create_before/<token>', views.BankAccountCreateView_before.as_view(), name='bankaccount_create_before'),  # 24/07/14追加
    ## <int:entity_id>だけでよくないか、BankAccountCreateView_beforeでtx_idからentityを抽出している 24/07/21
    path('<int:entity_id>/bankaccount_create/', views.BankAccountCreateView.as_view(), name='bankaccount_create'),  # 24/07/14追加
    path('<int:tx_id>/<int:entity_id>/bankaccount_create/', views.BankAccountCreateView.as_view(), name='bankaccount_create'),  # 24/07/14追加

]