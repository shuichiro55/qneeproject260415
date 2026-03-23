#from accounts.form import EmailAuthenticationForm  #INSTALLED_APPSに登録済み
from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

# 2025/02/15時点で参照せず
from django.urls import re_path

app_name = 'qpay'

urlpatterns = [

  path('txCreate/', views.TxCreateView.as_view(), name='txCreate'),
  path('<int:user_id>/txCreate/', views.TxCreateView.as_view(), name='txCreate'), # テスト用
  #path('<int:user_id>/<int:tx_id>/txCreate/', views.TxCreateView.as_view(), name='txCreate'),

  #path('txlist_buyer_approve_before/<token>/', views.TxListView_buyer_approve_before.as_view(), name='txlist_buyer_approve_before'),

  path('txList_buyer/', views.TxListView_buyer.as_view(), name='txList_buyer'),
  path('<int:pageNum>/txList_buyer/', views.TxListView_buyer.as_view(), name='txList_buyer'),
  path('<int:tx_id>/<int:pageNum>/txList_buyer/', views.TxListView_buyer.as_view(), name='txList_buyer'),
  # 「int:pageNum」は承認後、TxList（一覧）において結果を確認するときに使う

  path('txList_seller/', views.TxListView_seller.as_view(), name='txList_seller'),
  path('<int:pageNum>/txList_seller/', views.TxListView_seller.as_view(), name='txList_seller'),
  path('<int:tx_id>/<int:pageNum>/txList_seller/', views.TxListView_seller.as_view(), name='txList_seller'),

  path('txApprove_buyer/', views.TxApproveView_buyer.as_view(), name='txApprove_buyer'),
  path('<int:page_number>/txApprove_buyer/', views.TxApproveView_buyer.as_view(), name='txApprove_buyer'),
  path('<int:tx_id>/txApprove_buyer/', views.TxApproveView_buyer.as_view(), name='txApprove_buyer'),

  path('txApproveDetailPre_buyer/<token>/', views.TxApproveDetailPreView_buyer.as_view(), name='txApproveDetailPre_buyer'),
  path('<int:tx_id>/txApproveDetail_buyer/', views.TxApproveDetailView_buyer.as_view(), name='txApproveDetail_buyer'),

  path('<int:tx_id>/txDetail_buyer/', views.TxDetailView_buyer.as_view(), name='txDetail_buyer'),
  path('<int:tx_id>/<int:pageNum>/txDetail_buyer/', views.TxDetailView_buyer.as_view(), name='txDetail_buyer'),

  path('<int:tx_id>/<int:pageNum>/txDetail_seller/', views.TxDetailView_seller.as_view(), name='txDetail_seller'),

  path('adminInbox/', views.AdminInboxView.as_view(), name='adminInbox'),
  path('<int:tx_id>/adminInboxDetail/', views.AdminInboxDetailView.as_view(), name='adminInboxDetail'),
  path('<int:tx_id>/<int:pageNum>/adminInboxDetail/', views.AdminInboxDetailView.as_view(), name='adminInboxDetail'),
  # 「int:pageNum」は承認後、adminInboxにおいて結果を確認するときに使う

  path('adminInboxDetailPre/<token>/', views.AdminInboxDetailPreView.as_view(), name='adminInboxDetailPre'),

]
