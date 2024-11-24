#from accounts.form import EmailAuthenticationForm  #INSTALLED_APPSに登録済み
from django.urls import path, re_path
from . import views

app_name = 'qpay'

urlpatterns = [

    path('<int:user_id>/tx_create/', views.TxCreateView.as_view(), name='tx_create'),
    path('<int:user_id>/<int:tx_id>/tx_create/', views.TxCreateView.as_view(), name='tx_create'),

    #path('txlist_buyer_approve_before/<token>/', views.TxListView_buyer_approve_before.as_view(), name='txlist_buyer_approve_before'),

    path('txlist_buyer_approve/', views.TxListView_buyer_approve.as_view(), name='txlist_buyer_approve'),

    path('<int:page_num>/txlist_buyer_approve/', views.TxListView_buyer_approve.as_view(), name='txlist_buyer_approve'),

    path('txlist_buyer_history/', views.TxListView_buyer_history.as_view(), name='txlist_buyer_history'),
    path('<int:page_num>/txlist_buyer_history/', views.TxListView_buyer_history.as_view(), name='txlist_buyer_history'),

    path('txlist_seller/', views.TxListView_seller.as_view(), name='txlist_seller'),

    path('txdetail_buyer_approve_before/<token>/', views.TxDetailView_buyer_approve_before.as_view(), name='txdetail_buyer_approve_before'),

    path('<int:tx_id>/txdetail_buyer_approve/', views.TxDetailView_buyer_approve.as_view(), name='txdetail_buyer_approve'),
    path('<int:tx_id>/<int:page_num>/txdetail_buyer_approve/', views.TxDetailView_buyer_approve.as_view(), name='txdetail_buyer_approve'),

    path('<int:tx_id>/txdetail_buyer_history/', views.TxDetailView_buyer_history.as_view(), name='txdetail_buyer_history'),
    path('<int:tx_id>/<int:page_num>/txdetail_buyer_history/', views.TxDetailView_buyer_history.as_view(), name='txdetail_buyer_history'),

    path('<int:tx_id>/txdetail_seller/', views.TxDetailView_seller.as_view(), name='txdetail_seller'),

]