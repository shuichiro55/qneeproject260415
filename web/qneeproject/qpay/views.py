from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render
from django.contrib.auth import get_user_model
from django.views import generic
from .models import QpayTx
from accounts.models import LegalEntity
from qpay.form import TxCreateForm, TxEvidenceForm, \
      TxListForm_buyer_approve, TxListForm_buyer_history, \
      TxListForm_seller

from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.http import HttpResponseBadRequest, HttpResponseRedirect
from django.template.response import TemplateResponse


from django.contrib import messages
from django.core.paginator import Paginator
from django.core.mail import EmailMessage

from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.core.signing import dumps, loads, BadSignature, SignatureExpired
from django.conf import settings

from django.core.mail import EmailMessage

# 以下は2025/02/14時点で使われていない参照
from accounts.models import CustomUser
from django.db import models

usermodel = get_user_model()

def top(request):
  return render(request, 'qpay/top.html')

#受注者が前払い申請する際に利用するビュー（工事中）
class TxCreateView(generic.CreateView):

  model = QpayTx
  template_name = 'qpay/tx_create.html'
  form_class = TxCreateForm

  def get(self, request, *args, **kwargs):

    sellerUser = usermodel.objects.get(pk=self.kwargs['user_id'])

    buyerEntityname_dict =dict((str(idx), f) for idx, f in enumerate(LegalEntity.objects.filter(type1=1).values_list('entityname', flat=True), 1))
    print(f'buyerEntityname_dict={buyerEntityname_dict} def get in TxCreateView')
    print(f'sellerUser.personname={sellerUser.personname} def get in TxCreateView')

    init_dict = {
      'buyerEntity_entityname': "",
      'sellerUser_email': sellerUser.email,
      'sellerUser_personname': sellerUser.personname,
      'sellerEntity_entityname': sellerUser.entityname,
    }
    form = self.form_class(initial=init_dict)
    context = {
      'form': form,
      'flag_step': 1,
      'temporal_buyerEntityname': "",
      'buyerEntityname_dict': buyerEntityname_dict,
    }

    return render(request, 'qpay/tx_create.html', context)

  
  def post(self, request, *args, **kwargs):

    next = self.request.POST.get('next', '')   # POST.getはミドルウェア機能

    print(f'next={next}')
    print(f'ファイル名={request.FILES}')

    if next == 'ToConfirm':

      # ★TxCreateFormとTxEvidenceFormを使い分ける
      # ★postのすぐ下にあったものをここにもってきた 2026/02/14
      form = self.form_class(request.POST)

      if form.is_valid():
      # 「.is_valid()」の後、フォームでのclean、clean_<field>が実行され、
      # form.cleaned_data[]にデータが入る
 
        tx = form.save(commit=False)

        buyerEntity_entityname = self.request.POST['buyerEntity_entityname']
        tx.buyerEntity_entityname = buyerEntity_entityname
        print(f'tx.buyerEntity_entityname={tx.buyerEntity_entityname} TxCreateViewV, post, next==ToConfirm')
        print(f'tx.sellerUser_personname={tx.sellerUser_personname} TxCreateViewV, post, next==ToConfirm')

        buyerEntity = LegalEntity.objects.get(entityname=buyerEntity_entityname)
        tx.buyerEntity = buyerEntity
        tx.buyerUser_email = buyerEntity.email  #★★★　buyerのuserを複数にしたときに修正　25/05/31

        tx.buyerUser_personname = buyerEntity.personname

        tx.sellerUser = usermodel.objects.get(personname = request.POST['sellerUser_personname'], entityname = request.POST['sellerEntity_entityname'])
        #tx.sellerUser_personname = request.POST['sellerUser_personname']
        tx.sellerEntity = LegalEntity.objects.get(entityname = request.POST['sellerEntity_entityname'])
        
        # 各種金額を計算
        tx.advance_amount = tx.requested_amount
        tx.advance_fee = (tx.requested_amount * buyerEntity.advance_fee_rate) //1
        tx.referral_fee = (tx.requested_amount * buyerEntity.referral_fee_rate) //1
        tx.transfer_fee = 110
        tx.to_seller_amount = tx.advance_amount - tx.advance_fee - tx.transfer_fee

        tx.save()
        print(f'メールアドレス：{tx.buyerUser_email} next==confirm in TxCreateView')

        context = {
          'form':form,
          'flag_step': 2,
          #'buyerEntityname': buyerEntityname,
          'user_id': self.kwargs['user_id'],
          'tx': tx,
        }
        return render(self.request, 'qpay/tx_create.html', context)

      else: # 「if form.is_valid() == False」の場合

        buyerEntityname_dict =dict((str(idx), f) for idx, f in enumerate(LegalEntity.objects.filter(type1=1).values_list('entityname', flat=True), 1))
        print(f'buyerEntityname_dict={buyerEntityname_dict}')
        context = {
          'form':form,
          'flag_step': 1,
          'temporal_buyerEntityname': self.request.POST['buyerEntity_entityname'],
          'buyerEntityname_dict': buyerEntityname_dict,
        }
        return render(self.request, 'qpay/tx_create.html', context)


    # データ確認画面から入力画面に戻る時の処理 2025/02/14
    if next == 'BackToInput':

      form = self.form_class(request.POST)

      buyerEntityname_dict = \
        dict((str(idx), f) for idx, f in enumerate(LegalEntity.objects.filter(type1=1).values_list('entityname', flat=True), 1))
      print(f'buyerEntityname_dict={buyerEntityname_dict}')

      temporal_buyerEntityname = self.request.POST['buyerEntity_entityname']
      print(f'pass4 temporal_buyerEntityname={temporal_buyerEntityname} in TxCreateV, post, next==BackToInput')

      context = {
        'form': form,
        'flag_step': 1,
        'buyerEntityname_dict': buyerEntityname_dict,
        'temporal_buyerEntityname': temporal_buyerEntityname,
      }
      return render(self.request, 'qpay/tx_create.html', context)


    # エビデンスをアップロードするための処理
    # TxCreateFormで必要項目を入力後、データベースに入力値を保存したうえでの処理
    if next == 'ToEvidence':
      init_dict = {
        'id':self.kwargs['tx_id'],
        'evidence': "",
      }
      form = TxEvidenceForm(initial=init_dict)
      tx = QpayTx.objects.get(pk=self.kwargs['tx_id'])
      print(f'pass5（TxCreateV, post, next==ToEvidence')
  
      context = {
        'form': form,
        'flag_step': 1,

        'user_id': self.kwargs['user_id'],
        'tx_id': self.kwargs['tx_id'],
        #'tx': tx,
      }
      return TemplateResponse(request, "qpay/tx_evidence.html", context)


    if next == 'ToEvidenceConfirm':
      form = TxEvidenceForm(request.POST, request.FILES)
      tx_tmp = form.save(commit=False)

      tx = QpayTx.objects.get(pk=self.kwargs['tx_id'])
      tx.evidence = tx_tmp.evidence
      tx.save()

      tx_id = self.kwargs['tx_id']
      print(f'pass5 self.kwarts[tx_id]={tx_id} in TxCreateV, post, next==ToEvidenceConfirm')
      print(f'pass5 tx.buyerUer_email={tx.buyerUser_email} in TxCreateV, post, next==ToEvidenceConfirm')

      context = {
        'flag_step': 2,
        'user_id': self.kwargs['user_id'],
        'tx_id': self.kwargs['tx_id'],
        'tx': tx,
      }
      return TemplateResponse(request, "qpay/tx_evidence.html", context)
    

    # 申請手続きを終えてパートナー宛にメールで承認依頼
    if next == 'complete':

      # 申請した時点を記録する
      tx = QpayTx.objects.get(pk=self.kwargs['tx_id'])
      tx.requested_at = timezone.now()
      tx.save()

      QpayTx.objects.filter(pk__lt=self.kwargs['tx_id'], requested_at=None).delete()
      #「__lt=a」でaより小さい、[__lte=a]でa以下。AND条件は「,」でつなぐ

      # メール送付の処理
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
      recipient_list = [tx.buyerUser_email]
      #bcc =  ["toritoritorina@gmail.com"]  # BCCリスト
      email = EmailMessage(subject, message, from_email, recipient_list)
      email.send()
  
      messages.add_message(request, messages.SUCCESS, 'パートナー企業に前払いの申請を行いました.')
      print(f'pass6 tx.buyer_email={tx.buyerUser_email}（TxCreateV, post, next==TxSave)')
    
      return TemplateResponse(request, "accounts/mypage_seller.html", {'entity': tx.sellerEntity},)
      #return reverse_lazy('accounts:bankaccount_create', kwargs={'tx_id': tx_id})
  
    # self.request.POST.get('next', '')が何にも該当しない場合
    messages.add_message(request, messages.WARNING, 'システムエラーが発生しました。お手数ですがお問い合わせ頂けると有難いです。')
    print(f'pass7 nextがどれにも該当せず（エラー）（TxCreateView, post）')

    return TemplateResponse(self.request, 'qpay/tx_create.html', {'form':form},)      #contextを見直しが必要（基本的にはあまり通らないところだが）


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
  #context_object_name = 'qpaytxs'

  def get(self, request, *args, **kwargs):

    user =usermodel.objects.get(email=self.request.user)

    # 承認待ちの取引を抽出する
    object_list = QpayTx.objects.filter(buyerEntity = user.entity, tx_status_int=1).order_by('-requested_at')
    print(f'request.user={request.user} def get in TxListView_buyer_approve')

    # ログイン後にすぐに呼ばれることはなくなった中、必要か検討 24/07/02
    if user.type1 == 2:
    # 次のメッセージは確認できなかったので、要調整（トップページで出るようにする？）
      messages.add_message(request, messages.INFO, "発注者としてログインして下さい") 
      return HttpResponseRedirect(reverse('accounts:logout'))

    paginate_by = 4 # 4で仮置き

    paginator = Paginator(object_list, paginate_by)
 
    page_num = request.GET.get('page', 0)
    if page_num == 0:
      try:
        page_num = self.kwargs['page_num']
      except:
        page_num = 1

    page_obj = paginator.page(page_num)

    context = {
      'object_list': object_list,
       'page_obj': page_obj,
    }
    return render(request, 'qpay/txlist_buyer_approve.html', context)

  # 「モデル名（qpaytx）_list」が使える（ツボコツP130）
  def get_context_data(self, **kwargs):  #テンプレートに特定entityの取引データを渡す
    context = super().get_context_data(**kwargs)
    return context


class TxListView_buyer_history(LoginRequiredMixin, generic.UpdateView):

  model = QpayTx
  template_name = "qpay/txlist_buyer_history.html"
  form_class = TxListForm_buyer_history
  # context_object_name = 'qpaytxs'

  def get(self, request, *args, **kwargs):

    user =usermodel.objects.get(email=self.request.user)
    object_list = QpayTx.objects.filter(buyerEntity = user.entity).order_by('-created_at')
    print(f'request.user={request.user} def get in TxListView_buyer_history')

    # ログイン後にすぐに呼ばれることはなくなった中、必要か検討 24/07/02
    if user.type1 == 2:
    # 次のメッセージは確認できなかったので、要調整（トップページで出るようにする？）
      messages.add_message(request, messages.INFO, "発注者としてログインして下さい") 
      return HttpResponseRedirect(reverse('accounts:logout'))

    paginate_by = 4 # 4で仮置き

    paginator = Paginator(object_list, paginate_by)

    page_num = request.GET.get('page', 0)
    if page_num == 0:
      try:
        page_num = self.kwargs['page_num']
      except:
        page_num = 1

    page_obj = paginator.page(page_num)
    context = {
      'object_list': object_list,
      'page_obj': page_obj,
    }
    return render(request, 'qpay/txlist_buyer_history.html', context)

  # 「モデル名（qpaytx）_list」が使える（ツボコツP130）
  #def get_context_data(self, **kwargs):  #テンプレートに特定entityの取引データを渡す
  #  context = super().get_context_data(**kwargs)
  #  return context


# ゲストが取引履歴を確認するためのView   
class TxListView_seller(LoginRequiredMixin, generic.UpdateView):

  model = QpayTx
  template_name = "qpay/txlist_seller.html"
  form_class = TxListForm_seller
  context_object_name = 'qpaytxs'

  def get(self, request, *args, **kwargs):

    user =usermodel.objects.get(email=self.request.user)
    object_list = QpayTx.objects.filter(sellerEntity = user.entity).order_by('-requested_at')
    print(f'request.user={request.user} def get in TxListView_seller')

    if user.type1 == 1:
    # 次のメッセージは確認できなかったので、要調整（トップページで出るようにする？）
      messages.add_message(request, messages.INFO, "受注者としてログインして下さい") 
      return HttpResponseRedirect(reverse('accounts:logout'))

    paginate_by = 4 # 4で仮置き

    paginator = Paginator(object_list, paginate_by)

    # ページネーションから受け取る「page」をセット
    page_num = self.request.GET.get('page', 0)

    # ページネーションから「page」を受け取らず、
    # 「page_num」を指定する場合
    if page_num == 0:
      try:
        page_num = self.kwargs['page_num']
        # 該当値がない場合は1を返す
      except:
        page_num = 1

    page_obj = paginator.page(page_num)
    page1 = request.GET.get('page', 0)
    print(f'self.kwargs[page_num]={page_num} TxListV, get')
    print(f'page_obj.number={page_obj.number} TxListV, get')
    print(f'request.GET.get(page)={page1} TxListV, get')

    context = {
      'object_list': object_list,
      'page_obj': page_obj,
    }
    return render(request, 'qpay/txlist_seller.html', context)


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
    #le = LegalEntity.objects.get(entityname=tx.buyerEntity_entityname)

    # ページネーションから受け取る「page」をセット
    page_num = self.request.GET.get('page', 0)

    # ページネーションから「page」を受け取らず、
    # 「page_num」を指定する場合
    if page_num == 0:
      try:
        page_num = self.kwargs['page_num']
        # 該当値がない場合は1を返す
      except:
        page_num = 1
      
    print(f'page_num={page_num} in TxDetailV, get')

    context = {
      'tx': tx,
      'page_num': page_num,
    }
    return TemplateResponse(request, "qpay/txdetail_buyer_approve.html", context) 


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
      context1 = {
        'protocol': self.request.scheme,
        'domain': domain,
        'type1': 2,  # 承認された後、sellerがログインする場合の種別
        'token': dumps(tx.pk),
        'tx': tx,
      }

      subject = render_to_string('qpay/mail/mail2_subject_approved.txt', context1)
      message = render_to_string('qpay/mail/mail2_message_approved.txt', context1)

      from_email = 'shuichiro.tomihari.201604@gmail.com'
      recipient_list =[tx.sellerUser_email]
      #bcc =  ["toritoritorina@gmail.com"]  # BCCリスト
      email = EmailMessage(subject, message, from_email, recipient_list)
      email.send()

      context2 = {
        'tx': tx,
        'page_num': self.kwargs['page_num']
      }    
      return TemplateResponse(request, "qpay/txdetail_buyer_approve.html", context2)
      #return HttpResponseRedirect(self.get_success_url())

    elif next == "reject":

      # 否認された場合の処理（処理状況の更新、受注者への連絡等）を行う
      tx.status = 3
      tx.tx_status_char = "否認"
      tx.rejected_at = timezone.now()
      tx.save()

      context = {
        'tx': tx,
        'page_num': self.kwargs['page_num']
      }  
      return TemplateResponse(request, "qpay/txdetail_buyer_approve.html", context)
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
    #vle = LegalEntity.objects.get(entityname=tx.buyerEntity_entityname)

    try:
      page_num = int(self.kwargs['page_num'])
    except:
      page_num = 1

    print(f'page_num={page_num} in TxDetailView_buyer_history, get')
    context = {
      'tx': tx,
      'page_num': page_num
    }
    return TemplateResponse(request, "qpay/txdetail_buyer_history.html", context) 


# 発注者が申請状況を確認するためのView（一覧表から個別データのボタンを押した後）  
class TxDetailView_seller(generic.UpdateView):

  model = QpayTx
  template_name = "qpay/txdetail_seller.html"

  def get(self, request, *args, **kwargs):

    tx = QpayTx.objects.get(pk=self.kwargs['tx_id'])
    le = LegalEntity.objects.get(entityname=tx.buyerEntity_entityname)

    try:
      page_num = int(self.kwargs['page_num'])
      print(f'page_num={page_num} in TxDetailV, get')
    except:
      page_num = 1

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

