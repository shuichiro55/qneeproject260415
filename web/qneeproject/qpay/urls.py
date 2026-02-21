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

  path('txApprove_buyer/', views.TxApproveView_buyer.as_view(), name='txApprove_buyer'),
  path('<int:tx_id>/txApprove_buyer/', views.TxApproveView_buyer.as_view(), name='txApprove_buyer'),
  path('<int:tx_id>/<int:page_num>/txApprove_buyer/', views.TxApproveView_buyer.as_view(), name='txApprove_buyer'),

  path('txList_buyer/', views.TxListView_buyer.as_view(), name='txList_buyer'),
  path('<int:page_num>/txList_buyer/', views.TxListView_buyer.as_view(), name='txList_buyer'),
  path('<int:tx_id>/<int:page_num>/txList_buyer/', views.TxListView_buyer.as_view(), name='txList_buyer'),

  path('txList_seller/', views.TxListView_seller.as_view(), name='txList_seller'),
  path('<int:page_num>/txList_seller/', views.TxListView_seller.as_view(), name='txList_seller'),
  path('<int:tx_id>/<int:page_num>/txList_seller/', views.TxListView_seller.as_view(), name='txList_seller'),

  path('txApproveDetailPre_buyer/<token>/', views.TxApproveDetailPreView_buyer.as_view(), name='txApproveDetailPre_buyer'),

  path('<int:tx_id>/txApproveDetail_buyer/', views.TxApproveDetailView_buyer.as_view(), name='txApproveDetail_buyer'),
  path('<int:tx_id>/<int:page_num>/txApproveDetail_buyer/', views.TxApproveDetailView_buyer.as_view(), name='txApproveDetail_buyer'),
  # 「int:page_num」は承認後、TxListにおいて結果を確認するときに使う

  path('<int:tx_id>/txDetail_buyer/', views.TxDetailView_buyer.as_view(), name='txDetail_buyer'),
  path('<int:tx_id>/<int:page_num>/txDetail_buyer/', views.TxDetailView_buyer.as_view(), name='txDetail_buyer'),

  path('<int:tx_id>/<int:page_num>/txDetail_seller/', views.TxDetailView_seller.as_view(), name='txDetail_seller'),

]
