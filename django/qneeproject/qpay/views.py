from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render
from django.contrib.auth import get_user_model
from django.views import generic
from .models import QpayTx
from accounts.models import LegalEntity
from qpay.form import TxCreateForm, \
      TxListForm_buyer_approve, TxListForm_buyer_history, \
      TxListForm_seller #, TxDetailForm

from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.http import HttpResponseBadRequest, HttpResponseRedirect
from django.template.response import TemplateResponse

from accounts.models import CustomUser
from django.db import models
from django.contrib import messages
from django.core.paginator import Paginator
from django.core.mail import EmailMessage

from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.core.signing import dumps, loads, BadSignature, SignatureExpired
from django.conf import settings

from django.core.mail import EmailMessage

usermodel = get_user_model()

def top(request):
  return render(request, 'qpay/top.html')

#受注者が前払い申請する際に利用するビュー（工事中）
class TxCreateView(generic.CreateView):

  model = QpayTx
  template_name = 'qpay/tx_create.html'
  form_class = TxCreateForm

  def get(self, request, *args, **kwargs):

    seller_user = usermodel.objects.get(pk=self.kwargs['user_id'])
  
    init_dict = {
      'seller_email': seller_user.email,
      'seller_personname': seller_user.personname,
      'seller_entityname': seller_user.entityname,
    }
    #print(f'seller_email={seller_user.email}')
    #print(f'seller_personname={seller_user.personname}')
    #print(f'seller_entityname={seller_user.entityname}')

    form = self.form_class(initial=init_dict)

    return render(request, 'qpay/tx_create.html', {'form': form})

  
  def post(self, request, *args, **kwargs):

    #seller_user = usermodel.objects.get(pk=self.kwargs['user_id'])
    #buyer_entity = LegalEntity.objects.get(entityname = buyer_entityname)

    #form.buyer_entity = buyer_entity          # これは有効ではない？
    #form.buyer_entityname = buyer_entityname  # これは有効ではない？

    # user = usermodel.objects.get(pk=self.kwargs['user_id'])
    # usermodelだと、エラーとして「functionがobjectsを持ってない」と出る
    # get_user_modelの仕様を確認しよう！

    form = self.form_class(request.POST, request.FILES)
    next = self.request.POST.get('next', '')   # POST.getはミドルウェア機能

    print(f'next={next}')
    print(f'ファイル名={request.FILES}')

    if form.is_valid():
      # 「.is_valid()」の後、フォームでのclean、clean_<field>が実行され、
      # form.cleaned_data[]にデータが入る

      if next == 'confirm':
        tx = form.save(commit=True) # 確認画面の後に保存した方がよいか？
        entityname_list = list(LegalEntity.objects.filter(type1=1).values_list('entityname', flat=True))
        buyer_entityname = entityname_list[int(request.POST['buyer_entity_choice']) - 1]

        tx.buyer_entityname = buyer_entityname
        buyer_entity = LegalEntity.objects.get(entityname = buyer_entityname)
        tx.buyer_entity = buyer_entity
        tx.buyer_email = buyer_entity.email
        tx.buyer_personname = buyer_entity.personname

        seller_user = usermodel.objects.get(personname = request.POST['seller_personname'], entityname = request.POST['seller_entityname'])
        seller_user = usermodel.objects.get(personname = request.POST['seller_personname'], entityname = request.POST['seller_entityname'])

        seller_entity = LegalEntity.objects.get(entityname = request.POST['seller_entityname'])

        ##tx.seller_user = seller_user
        tx.seller_entity = seller_entity
        
        # 各種金額を計算
        tx.advance_amount = tx.requested_amount
        tx.advance_fee = (tx.requested_amount * buyer_entity.advance_fee_rate) //1
        tx.referral_fee = (tx.requested_amount * buyer_entity.referral_fee_rate) //1
        tx.transfer_fee = 110
        tx.to_seller_amount = tx.advance_amount - tx.advance_fee - tx.transfer_fee

        print(f'メールアドレス：{tx.buyer_email} next==confirm in TxCreateView')
        tx.save()

        return render(
          self.request,
          'qpay/tx_create_confirm.html',
          { 'form':form,
            'buyer_entityname': buyer_entityname,
            'user_id': self.kwargs['user_id'],
            'tx': tx
          }
        )

    if next == 'back':
      print(f'ここまで来てる4（def post after form.is_valid in class TxCreateView）')
      return render(self.request, 'qpay/tx_create.html', {'form':form})

    if next == 'create':
      tx = QpayTx.objects.get(pk=self.kwargs['tx_id'])
      tx.requested_at = timezone.now()
      tx.save()
      print(f'ここまで来てる5（def post if next==create after form.is_valid in class TxCreateView）')
      
      ## 前払いの申請後、buyerに申請があったことを通知し、承認を依頼する
      current_site = get_current_site(self.request)
      domain = current_site.domain
      context = {
        'protocol': self.request.scheme,
        'domain': domain,
        'token': dumps(tx.pk),
        'tx': tx,
      }
      subject = render_to_string('qpay/mail/mail1_subject_applied.txt', context)
      message = render_to_string('qpay/mail/mail1_message_applied.txt', context)

      from_email = 'shuichiro.tomihari.201604@gmail.com'
      recipient_list = [tx.buyer_email]
      #bcc =  ["toritoritorina@gmail.com"]  # BCCリスト
      email = EmailMessage(subject, message, from_email, recipient_list)
      email.send()
  
      print(f'ここまで来てる6（def post if next==create after form.is_valid in class TxCreateView）')
    
      return TemplateResponse(request, "accounts/mypage_seller.html", {'entity': tx.seller_entity},)
      #return reverse_lazy('accounts:bankaccount_create', kwargs={'tx_id': tx_id})
  
    else:
      print(form.errors)
      print(f'通過してる？7（post⇒form.is_valid後の例外処理 in class TxCreateView）')

      #return TemplateResponse(self.request, 'qpay/tx_create.html', {'form':form, 'user_id':request.user.id, 'user':request.user},)
      return TemplateResponse(self.request, 'qpay/tx_create.html', {'form':form},)      #contextを見直しが必要（基本的にはあまり通らないところだが）

  ## ★★★工事中
  #def get_context_data(self, *args, **kwargs):  #テンプレートに渡すcontextを取得する
  #  context = super().get_context_data(self, **kwargs)
  #  form = TxCreateForm()
  #  #一番新しいデータを引っ張ってこれればtransactionのデータもとれるか？
  #  return {'form': form}

  def form_valid(self, form):
    return super().form_valid(form)
  
  # 申請後のViewを表示する。★★mypageに行くとき何かメッセージを出せないか
  def get_success_url(self):
    return reverse('accounts:mypage_seller')

  #def form_invalid(self, form):
  #  return super().form_invalid(form)

  
# 発注者が申請状況を確認するためのView   
class TxListView_buyer_approve(generic.UpdateView):

  model = QpayTx
  template_name = "qpay/txlist_buyer_approve.html"
  form_class = TxListForm_buyer_approve
  context_object_name = 'qpaytxs'

  def get(self, request, *args, **kwargs):

    user =usermodel.objects.get(email=self.request.user)

    # 承認待ちの取引を抽出する
    object_list = QpayTx.objects.filter(buyer_entity = user.entity, tx_status_int=1).order_by('-requested_at')
    print(f'request.user={request.user} def get in TxListView_buyer_approve')

    # ログイン後にすぐに呼ばれることはなくなった中、必要か検討 24/07/02
    if user.type1 == 2:
    # 次のメッセージは確認できなかったので、要調整（トップページで出るようにする？）
      messages.add_message(request, messages.INFO, "発注者としてログインして下さい") 
      return HttpResponseRedirect(reverse('accounts:logout'))

    paginate_by = 4 # 4で仮置き

    paginator = Paginator(object_list, paginate_by)
 
    try:
      page_number = self.kwargs['page_num']
    except:
      page_number = request.GET.get('page', 1)

    page_obj = paginator.page(page_number)

    return render(request, 'qpay/txlist_buyer_approve.html', { 'object_list': object_list, 'page_obj': page_obj })

  # 「モデル名（qpaytx）_list」が使える（ツボコツP130）
  def get_context_data(self, **kwargs):  #テンプレートに特定entityの取引データを渡す
    context = super().get_context_data(**kwargs)
    return context

class TxListView_buyer_history(LoginRequiredMixin, generic.UpdateView):

  model = QpayTx
  template_name = "qpay/txlist_buyer_history.html"
  form_class = TxListForm_buyer_history
  context_object_name = 'qpaytxs'

  def get(self, request, *args, **kwargs):

    user =usermodel.objects.get(email=self.request.user)
    object_list = QpayTx.objects.filter(buyer_entity = user.entity).order_by('-created_at')
    print(f'request.user={request.user} def get in TxListView_buyer_history')

    # ログイン後にすぐに呼ばれることはなくなった中、必要か検討 24/07/02
    if user.type1 == 2:
    # 次のメッセージは確認できなかったので、要調整（トップページで出るようにする？）
      messages.add_message(request, messages.INFO, "発注者としてログインして下さい") 
      return HttpResponseRedirect(reverse('accounts:logout'))

    paginate_by = 4 # 4で仮置き

    paginator = Paginator(object_list, paginate_by)
 
    try:
      page_number = self.kwargs['page_num']
    except:
      page_number = request.GET.get('page', 1)

    page_obj = paginator.page(page_number)

    return render(request, 'qpay/txlist_buyer_history.html', { 'object_list': object_list, 'page_obj': page_obj })

  # 「モデル名（qpaytx）_list」が使える（ツボコツP130）
  def get_context_data(self, **kwargs):  #テンプレートに特定entityの取引データを渡す
    context = super().get_context_data(**kwargs)
    return context


# 受注者が取引履歴を確認するためのView   
class TxListView_seller(LoginRequiredMixin, generic.UpdateView):

  model = QpayTx
  template_name = "qpay/txlist_seller.html"
  form_class = TxListForm_seller
  context_object_name = 'qpaytxs'

  def get(self, request, *args, **kwargs):

    user =usermodel.objects.get(email=self.request.user)
    object_list = QpayTx.objects.filter(seller_entity = user.entity).order_by('-requested_at')
    print(f'request.user={request.user} def get in TxListView_seller')

    if user.type1 == 1:
    # 次のメッセージは確認できなかったので、要調整（トップページで出るようにする？）
      messages.add_message(request, messages.INFO, "受注者としてログインして下さい") 
      return HttpResponseRedirect(reverse('accounts:logout'))

    paginate_by = 4 # 4で仮置き

    paginator = Paginator(object_list, paginate_by)
 
    try:
      page_number = self.kwargs['page_num']
    except:
      page_number = request.GET.get('page', 1)

    page_obj = paginator.page(page_number)

    return render(request, 'qpay/txlist_seller.html', { 'object_list': object_list, 'page_obj': page_obj })


  # 「モデル名（qpaytx）_list」が使える（ツボコツP130）
  def get_context_data(self, **kwargs):  #テンプレートに特定entityの取引データを渡す
    context = super().get_context_data(**kwargs)
    return context

#　24/06/14 tokenをtx_idに変換して、TDetailView_buyer_approveを呼ぶ
class TxDetailView_buyer_approve_before(generic.TemplateView):

  template_name = 'qpay/txdetail_buyer_approve_before.html'
  timeout_seconds = getattr(settings,  'ACTIVATION_TIMEOUT_SECONDS', 60*60*24)

  def get(self, request, *args, **kwargs):
      
    token = self.kwargs.get('token')  #kwargsはdict型
    print(f'token={token} def get in class TxDetailView_buyer_approve_before')
    
    try:
      tx_id = loads(token, max_age=self.timeout_seconds)
      print(f'tx_id={tx_id} def get in class TxDetailView_buyer_approve_before')

    except SignatureExpired:
      return HttpResponseBadRequest()

    #tokenが間違っている
    except BadSignature:
      return HttpResponseBadRequest()

    return HttpResponseRedirect(reverse('qpay:txdetail_buyer_approve', kwargs={'tx_id': tx_id}))

  # POSTメソッドで口座登録する場合に備えて保持 24/07/21  POST関数がなくとも機能するか？
  def get_success_url(self):
    tx_id = self.kwargs['tx_id']  #kwargsはdict型
    return reverse_lazy('accounts:bankaccount_create', kwargs={'tx_id': tx_id})


# 発注者が前払いの申請をするためのView（一覧又はメール内URLから遷移）  
class TxDetailView_buyer_approve(generic.UpdateView):

  model = QpayTx
  template_name = "qpay/txdetail_buyer_approve.html"
  timeout_seconds = getattr(settings,  'ACTIVATION_TIMEOUT_SECONDS', 60*60*24)

  def get(self, request, *args, **kwargs):

    tx = QpayTx.objects.get(pk=self.kwargs['tx_id'])   
    #le = LegalEntity.objects.get(entityname=tx.buyer_entityname)

    try:
      page_num = int(self.kwargs['page_num'])
      print(f'page_num={page_num} in def get of TxDetailView_buyer')
    except:
      page_num = 1

    return TemplateResponse(request, "qpay/txdetail_buyer_approve.html", { "tx": tx, 'page_num': page_num }) 


  def post(self, request, *args, **kwargs):

    tx =QpayTx.objects.get(pk=self.kwargs['tx_id'])

    next = self.request.POST.get('next', '') 
    if next == "approve":

      print("「承認」が押下された post in TxDetailView_buyer_approve")
      # 承認された場合の処理（処理状況の更新、Qneeへの連絡等）を行う
      tx.tx_status_int = 2
      tx.tx_status_char = "承認済み\n（前払い前）" 
      tx.approved_at = timezone.now()
      
      ## 一旦、リスクエスト金額を承認された金額にする 24/07/25
      tx.approved_amount = tx.requested_amount
      tx.save()

      ## buyerが承諾した後、sellerに承諾したことをメールで伝える
      current_site = get_current_site(self.request)
      domain = current_site.domain
      context = {
        'protocol': self.request.scheme,
        'domain': domain,
        'token': dumps(tx.pk),
        'tx': tx,
      }

      subject = render_to_string('qpay/mail/mail2_subject_approved.txt', context)
      message = render_to_string('qpay/mail/mail2_message_approved.txt', context)

      from_email = 'shuichiro.tomihari.201604@gmail.com'
      recipient_list =[tx.seller_email]
      #bcc =  ["toritoritorina@gmail.com"]  # BCCリスト
      email = EmailMessage(subject, message, from_email, recipient_list)
      email.send()
    
      return TemplateResponse(request, "qpay/txdetail_buyer_approve.html",{ "tx":tx })
      #return HttpResponseRedirect(self.get_success_url())

    elif next == "reject1":

      # 否認された場合の処理（処理状況の更新、受注者への連絡等）を行う
      tx.status = 3
      tx.tx_status_char = "否認"
      tx.rejected_at = timezone.now()
      tx.save()

      return TemplateResponse(request, "qpay/txdetail_buyer_approve.html",{ "tx":tx })
      #return HttpResponseRedirect(self.get_success_url())

    elif next == "reject2":

      # 否認された場合の処理（処理状況の更新、受注者への連絡等）を行う
      tx.status = 3
      tx.tx_status_char = "否認"
      tx.rejected_at = timezone.now()
      tx.save()

      return TemplateResponse(request, "qpay/txdetail_buyer_approve.html",{ "tx":tx })
      #return HttpResponseRedirect(self.get_success_url())

    return HttpResponseBadRequest()

  def get_success_url(self):
    return reverse_lazy('qpay:txlist_buyer_approve')

  #def get_context_data(self, **kwargs):  #テンプレートに特定entityの取引データを渡す
  #  form = TxDetailForm
  #  tx = QpayTx.objects.get(id=self.kwargs['tx_id'])
  #  return {'form': form, 'tx': tx, }


# 発注者が申請状況を確認するためのView（一覧表から個別データのボタンを押した後）  
class TxDetailView_buyer_history(generic.UpdateView):

  model = QpayTx
  template_name = "qpay/txdetail_buyer_history.html"

  def get(self, request, *args, **kwargs):

    tx = QpayTx.objects.get(pk=self.kwargs['tx_id'])
    le = LegalEntity.objects.get(entityname=tx.buyer_entityname)

    try:
      page_num = int(self.kwargs['page_num'])
      print(f'page_num={page_num} in def get of TxDetailView_buyer_history')
    except:
      page_num = 1

    return TemplateResponse(request, "qpay/txdetail_buyer_history.html", { "tx": tx, 'page_num': page_num }) 

#  TxListView_buyer_historyから表示するだけなのでpostは基本は不要 24/7/11
#  将来、個別取引の証明書発行などで機能追加をする場合にこの部分を加工する
#  
#  def post(self, request, *args, **kwargs):
#
#    tx =QpayTx.objects.get(pk=self.kwargs['tx_id'])
#
#    next = self.request.POST.get('next', '') 
#    if next == "approve":#
#
#      print("「承認」が押下された in TxDetailView_buyer_history")
#      # 承認された場合の処理（処理状況の更新、Qneeへの連絡等）を行う
#      tx.tx_status_int = 2
#      tx.tx_status_char = "承認済み（前払い前）" 
#      tx.approved_at = timezone.now()
#      tx.save()
#    
#      return TemplateResponse(request, "qpay/txdetail_buyer_history.html",{ "tx":tx })
#      #return HttpResponseRedirect(self.get_success_url())
#
#    elif next == "reject1":
#
#      # 否認された場合の処理（処理状況の更新、受注者への連絡等）を行う
#      tx.status = 3
#      tx.tx_status_char = "否認"
#      tx.rejected_at = timezone.now()
#      tx.save()
#
#      return TemplateResponse(request, "qpay/txdetail_buyer_history.html",{ "tx":tx })
#      #return HttpResponseRedirect(self.get_success_url())
#
#    elif next == "reject2":
#
#      # 否認された場合の処理（処理状況の更新、受注者への連絡等）を行う
#      tx.status = 3
#      tx.tx_status_char = "否認"
#      tx.rejected_at = timezone.now()
#      tx.save()
#
#      return TemplateResponse(request, "qpay/txdetail_buyer.html",{ "tx":tx })
#      #return HttpResponseRedirect(self.get_success_url())
#
#    return HttpResponseBadRequest()
#
#  def get_success_url(self):
#    return reverse_lazy('qpay:txlist_buyer_approve')
#
#  #def get_context_data(self, **kwargs):  #テンプレートに特定entityの取引データを渡す
#  #  form = TxDetailForm
#  #  tx = QpayTx.objects.get(id=self.kwargs['tx_id'])
#  #  return {'form': form, 'tx': tx, }


# 発注者が申請状況を確認するためのView（一覧表から個別データのボタンを押した後）  
class TxDetailView_seller(generic.UpdateView):

  model = QpayTx
  template_name = "qpay/txdetail_seller.html"

  def get(self, request, *args, **kwargs):

    tx = QpayTx.objects.get(pk=self.kwargs['tx_id'])
    le = LegalEntity.objects.get(entityname=tx.buyer_entityname)

    try:
      page_num = int(self.kwargs['page_num'])
      print(f'page_num={page_num} in def get of TxDetailView_seller')
    except:
      page_num = 1

    # 各種金額を計算
    #tx.advance_amount = tx.requested_amount
    #tx.advance_fee = (tx.requested_amount * le.advance_fee_rate) //1
    #tx.referral_fee = (tx.requested_amount * le.referral_fee_rate) //1
    #tx.to_seller_amount = tx.advance_amount - tx.advance_fee - tx.transfer_fee
    #tx.save()

    return TemplateResponse(request, "qpay/txdetail_seller.html", { "tx": tx, 'page_num': page_num }) 

  def post(self, request, *args, **kwargs):
    tx =QpayTx.objects.get(pk=self.kwargs['tx_id'])
    return TemplateResponse(request, "qpay/txdetail_seller.html",{ "tx":tx })

  def get_success_url(self):
    return reverse_lazy('qpay:txlist_seller')

  #def get_context_data(self, **kwargs):  #テンプレートに特定entityの取引データを渡す
  #  form = TxDetailForm
  #  tx = QpayTx.objects.get(id=self.kwargs['tx_id'])
  #  return {'form': form, 'tx': tx, }

#
class TxConfirm(generic.UpdateView):

  model = QpayTx
  template_name = "qpay/txdetail_buyer.html"

