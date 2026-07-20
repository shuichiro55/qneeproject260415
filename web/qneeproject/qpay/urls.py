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

  path('txReapply_seller/', views.TxReapplyView_seller.as_view(), name='txReapply_seller'),

  #path('txlist_buyer_approve_before/<token>/', views.TxListView_buyer_approve_before.as_view(), name='txlist_buyer_approve_before'),

  path('txList_buyer/', views.TxListView_buyer.as_view(), name='txList_buyer'),
  path('<int:page_number>/txList_buyer/', views.TxListView_buyer.as_view(), name='txList_buyer'),
  path('<int:tx_id>/<int:page_number>/txList_buyer/', views.TxListView_buyer.as_view(), name='txList_buyer'),
  # 「int:page_number」は承認後、TxList（一覧）において結果を確認するときに使う

  path('txList_seller/', views.TxListView_seller.as_view(), name='txList_seller'),
  path('<int:page_number>/txList_seller/', views.TxListView_seller.as_view(), name='txList_seller'),
  path('<int:tx_id>/<int:page_number>/txList_seller/', views.TxListView_seller.as_view(), name='txList_seller'),

  path('txList_admin/', views.TxListView_admin.as_view(), name='txList_admin'),
  path('<int:page_number>/txList_admin/', views.TxListView_admin.as_view(), name='txList_admin'),
  path('<int:tx_id>/<int:page_number>/txList_admin/', views.TxListView_admin.as_view(), name='txList_admin'),

  path('txApprove_buyer/', views.TxApproveView_buyer.as_view(), name='txApprove_buyer'),
  path('<int:page_number>/txApprove_buyer/', views.TxApproveView_buyer.as_view(), name='txApprove_buyer'),
  path('<int:tx_id>/txApprove_buyer/', views.TxApproveView_buyer.as_view(), name='txApprove_buyer'),

  path('txApproveDetailPre_buyer/<token>/', views.TxApproveDetailPreView_buyer.as_view(), name='txApproveDetailPre_buyer'),
  path('<int:tx_id>/txApproveDetail_buyer/', views.TxApproveDetailView_buyer.as_view(), name='txApproveDetail_buyer'),

  path('<int:tx_id>/txListDetail_buyer/', views.TxListDetailView_buyer.as_view(), name='txListDetail_buyer'),
  path('<int:tx_id>/<int:page_number>/txListDetail_buyer/', views.TxListDetailView_buyer.as_view(), name='txListDetail_buyer'),

  path('<int:tx_id>/<int:page_number>/txListDetail_seller/', views.TxListDetailView_seller.as_view(), name='txListDetail_seller'),
  path('<int:tx_id>/<int:page_number>/txListDetail_admin/', views.TxListDetailView_admin.as_view(), name='txListDetail_admin'),

  path('txInbox/', views.TxInboxView_admin.as_view(), name='txInbox'),
  #path('<int:page_number>/txInbox/', views.TxInboxView.as_view(), name='txInbox'),

  path('txInboxDetailPre/<token>/', views.TxInboxDetailPreView_admin.as_view(), name='txInboxDetailPre'),

  # path('txInboxDetail/', views.TxInboxDetailView_admin.as_view(), name='txInboxDetail'),
  path('<int:tx_id>/txInboxDetail/', views.TxInboxDetailView_admin.as_view(), name='txInboxDetail'),
  path('<int:tx_id>/<int:page_number>/txInboxDetail/', views.TxInboxDetailView_admin.as_view(), name='txInboxDetail'),
  # 「int:page_number」は承認後、txInboxにおいて結果を確認するときに使う
]
