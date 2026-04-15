from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render
from django.contrib.auth import get_user_model
from django.views import generic
from .models import QpayTx
from accounts.models import LegalEntity, BankAccount
from qpay.form import TxCreateForm, TxEvidenceForm, \
      TxApproveForm_buyer, TxListForm_buyer, \
      TxListForm_seller

from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.http import HttpResponseBadRequest, HttpResponseRedirect
from django.template.response import TemplateResponse


from django.contrib import messages
from django.core.paginator import Paginator
from django.core.mail import EmailMessage
from django.db.models import Q

from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.core.signing import dumps, loads, BadSignature, SignatureExpired
from django.conf import settings

#from datetime import date
import datetime

# 以下は2025/02/14時点で使われていない参照
# from accounts.models import CustomUser
# from django.db import models

UserModel = get_user_model()

#def top(request):
#  return render(request, 'qpay/top.html')

# ★★ 受注者が前払い申請する際に利用するビュー（工事中）
class TxCreateView(generic.CreateView):

  model = QpayTx
  template_name = 'qpay/seller/txCreate.html'
  form_class = TxCreateForm

  def dispatch(self, request, *args, **kwargs):
  
    self.request.session['dict_buyEntityname'] = \
      dict((f, f) for idx, f in enumerate(LegalEntity.objects.filter(type1=1).values_list('entityName', flat=True), 1))
  
    """ 初回のマイグレーションの時のみ下記を採用する """
    #dict_buyEntityName = {'Qnee','Qnee'}
    # 「flat=True」はリスト、「flat=False」はタプル
  
    return super().dispatch(request, *args, **kwargs)
  

  def get(self, request, *args, **kwargs):

    #sellUser = UserModel.objects.get(email=self.request.user)
    #sellEntity = LegalEntity.objects.get(pk=sellUser.entity_id)

    sellUser_id = self.request.session.get('sellUser_id')
    sellUser = UserModel.objects.get(pk=sellUser_id)
    sellEntity = LegalEntity.objects.get(pk=sellUser.entity_id)

    dict_buyEntityName = self.request.session.get('dict_buyEntityname')

    init_dict = {
      'buyEntityName': "",
      'sellUser_email': sellUser.email,
      'sellUser_userName': sellUser.userName,
      'sellEntityName': sellEntity.entityName,
    }
    form = self.form_class(initial=init_dict)

    context = {
      'flag_step': 1,
      'sellUser': sellUser,
      'sellEntity': sellEntity,
      'form': form,
      'temporal_buyEntityName': "",
      'dict_buyEntityName': dict_buyEntityName,
      #'temporal_sellEntityName': sellEntity.entityName, # 250608 Selectボックス未選択を示す
      #'dict_sellEntityName': dict_sellEntityName,

    }
    return render(request, 'qpay/seller/txCreate.html', context)

  
  def post(self, request, *args, **kwargs):

    next = self.request.POST.get('next', '')   # POST.getはミドルウェア機能

    print(f'next={next}')
    print(f'ファイル名={request.FILES}')

    if next.find('ToConfirm') >= 0:

      # ★TxCreateFormとTxEvidenceFormを使い分ける
      # ★postのすぐ下にあったものをここにもってきた 2026/02/14
      form = self.form_class(request.POST)

      if form.is_valid():
      # 「.is_valid()」の後、フォームでのclean、clean_<field>が実行され、
      # form.cleaned_data[]にデータが入る
 
        sellUser_id = self.request.session.get('sellUser_id')
        sellUser = UserModel.objects.get(pk=sellUser_id)
        sellEntity = LegalEntity.objects.get(pk=sellUser.entity_id)
        
        # もし、同じユーザーで作成途中のデーターがあれば削除
        QpayTx.objects.filter(sellUser=sellUser, evidence=None).delete()

        tx = form.save(commit=False)
        tx.sellUser = sellUser
        tx.sellEntity = sellEntity
        
        buyEntityName = self.request.POST['buyEntityName']
        tx.buyEntityName = buyEntityName

        buyEntity = LegalEntity.objects.get(entityName=buyEntityName)
        tx.buyEntity = buyEntity
        # tx.buyUser_email = buyEntity.email  ★★　buyerのuserを複数にしたときに修正　25/05/31
        # tx.buyUser_userName = buyEntity.userName buyerエンティティにはuserNameは設けない

        # 各種金額を計算       
        tx.advance_amount = tx.requested_amount
        tx.advance_fee = (tx.requested_amount * buyEntity.advance_fee_rate) //1
        tx.referral_fee = (tx.requested_amount * buyEntity.referral_fee_rate) //1
        tx.transfer_fee = 110
        tx.transfer_amount = tx.advance_amount - tx.advance_fee - tx.transfer_fee

        tx.save()
        self.request.session['tx_id'] = tx.id

        # print(f'メールアドレス：{tx.buyUser_email} next==confirm in TxCreateView')
        print(f'pass4 tx.buyEntityName={tx.buyEntityName} TxCreateViewV, post, next==ToConfirm')
        print(f'pass4 tx.sellUser_userName={tx.sellUser_userName} TxCreateViewV, post, next==ToConfirm')

        context = {
          'flag_step': 2,
          'sellUser': sellUser,
          'sellEntity': sellEntity,
          'tx': tx,
          'form':form,
          #'buyEntityName': buyEntityName,
        }
        return render(self.request, 'qpay/seller/txCreate.html', context)

      else: # 「if form.is_valid() == False」の場合

        sellUser_id = self.request.session.get('sellUser_id')
        sellUser = UserModel.objects.get(pk=sellUser_id)
        sellEntity = LegalEntity.objects.get(pk=sellUser.entity_id)

        dict_buyEntityName = self.request.session.get('dict_buyEntityname')

        context = {
          'flag_step': 1,
          'sellUser': sellUser,
          'sellEntity': sellEntity,
          'form':form,
          'temporal_sellEntityName': self.request.POST['sellEntityName'],
          'temporal_buyEntityName': self.request.POST['buyEntityName'],
          'dict_sellEntityName': dict_buyEntityName,
          'dict_buyEntityName': dict_buyEntityName,
        }
        return render(self.request, 'qpay/seller/txCreate.html', context)


    # データ確認画面から入力画面に戻る時の処理 2025/02/14
    if next.find('BackToInput') >= 0:

      sellUser_id = self.request.session.get('sellUser_id')
      sellUser = UserModel.objects.get(pk=sellUser_id)
      sellEntity = LegalEntity.objects.get(pk=sellUser.entity_id)

      tx_id = self.request.session.get('tx_id')
      tx = QpayTx.objects.get(pk=tx_id)

      form = self.form_class(request.POST)

      temporal_sellEntityName = sellEntity.entityName
      temporal_buyEntityName = self.request.POST['buyEntityName']
      print(f'pass4 temporal_sellEntityName={temporal_sellEntityName} in TxCreateV, post, next==BackToInput')
      print(f'pass4 temporal_buyEntityName={temporal_buyEntityName} in TxCreateV, post, next==BackToInput')

      dict_buyEntityName = self.request.session.get('dict_buyEntityname')

      context = {
        'flag_step': 1,
        'sellUser': sellUser,
        'sellEntity': sellEntity,
        'tx': tx,
         'form': form,
        'temporal_buyEntityName': temporal_buyEntityName,
        'dict_buyEntityName': dict_buyEntityName,
        #'temporal_sellEntityName': temporal_sellEntityName,
        #'dict_sellEntityName': dict_sellEntityName,

      }
      return render(self.request, 'qpay/seller/txCreate.html', context)


    # エビデンスをアップロードするための処理
    # TxCreateFormで必要項目を入力後、データベースに入力値を保存したうえでの処理
    if next.find('ToEvidenceSelect') >= 0:

      sellUser_id = self.request.session.get('sellUser_id')
      sellUser = UserModel.objects.get(pk=sellUser_id)
      sellEntity = LegalEntity.objects.get(pk=sellUser.entity_id)

      tx_id = self.request.session.get('tx_id')
      tx = QpayTx.objects.get(pk=tx_id)

      context = {
        'flag_step': 1,
        'sellUser': sellUser,
        'sellEntity': sellEntity,
        'tx': tx,
        'form': TxEvidenceForm(),
      }
      return TemplateResponse(request, "qpay/seller/txCreate_evidence.html", context)


    if next.find('ToEvidenceConfirm') >= 0:

      sellUser_id = self.request.session.get('sellUser_id')
      sellUser = UserModel.objects.get(pk=sellUser_id)
      sellEntity = LegalEntity.objects.get(pk=sellUser.entity_id)

      tx_id = self.request.session.get('tx_id')
      tx = QpayTx.objects.get(pk=tx_id)

      form = TxEvidenceForm(request.POST, request.FILES)
      if form.is_valid():
        print(f'pass3 next={next} after form.is_valide()')
        tx_tmp = form.save(commit=False)

        tx.evidence = tx_tmp.evidence
        tx.save()

        context = {
          'flag_step': 2,
          'sellUser': sellUser,
          'sellEntity': sellEntity,
          'tx': tx,
        }
        return TemplateResponse(request, "qpay/seller/txCreate_evidence.html", context)
      
      else:
  
        context = {
          'flag_step': 1,
          'sellUser': sellUser,
          'sellEntity': sellEntity,
          'tx': tx,
          'form': form,
        }
        return TemplateResponse(request, "qpay/seller/txCreate_evidence.html", context)
    

    # 申請手続きを終えてパートナー宛にメールで承認依頼
    if next.find('Complete') >= 0:

      tx_id = next.split('_')[3]
      tx = QpayTx.objects.get(pk=tx_id)
      tx.requested_at = timezone.now()  # 申請した時点を記録する

      tx.save()

      QpayTx.objects.filter(pk__lt=tx_id, requested_at=None).delete()
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

      buyEntity = LegalEntity.objects.get(pk=tx.buyEntity_id)
      buyEntityUsers = buyEntity.entity_users.all()

      for eachUser in buyEntityUsers:
  
        if eachUser.canApproveAll == True or eachUser.canApproveQpay:
          context = {
            'protocol': self.request.scheme,
            'domain': domain,
            'afterLogin': 'qpayApproveApply',
            'token': dumps(tx.pk),
            'tx': tx,
            'buyEntityApprover': eachUser,
          }
          subject = render_to_string('qpay/seller/mail/qpayApproveApply_subject.txt', context)
          message = render_to_string('qpay/seller/mail/qpayApproveApply_message.txt', context)

          from_email = 'shuichiro.tomihari.201604@gmail.com'

          recipient_list = [eachUser.email]
          #bcc =  ["toritoritorina@gmail.com"]  # BCCリスト
          email = EmailMessage(subject, message, from_email, recipient_list)
          email.send()
  
          print(f'pass6 buyEntityのapprover.email={eachUser.email}（TxCreateV, post, next==TxSave)')

      messages.add_message(request, messages.SUCCESS, 'パートナー企業に前払いの申請を行いました.')

      return TemplateResponse(request, "accounts/seller/mypage.html", {'entity': tx.sellEntity},)
          #return reverse_lazy('accounts:bankaccount_create', kwargs={'tx_id': tx_id})
  
    # self.request.POST.get('next', '')が何にも該当しない場合
    messages.add_message(request, messages.WARNING, 'システムエラーが発生しました。お手数ですがお問い合わせ頂けると有難いです。')
    print(f'pass7 nextがどれにも該当せず（エラー）（TxCreateView, post）')

    return TemplateResponse(self.request, 'qpay/seller/txCreate.html', {'form':form},)      #contextを見直しが必要（基本的にはあまり通らないところだが）


  #def form_valid(self, form):
  #  return super().form_valid(form)
  
  # 申請後のViewを表示する。★★mypageに行くとき何かメッセージを出せないか
  #def get_success_url(self):
  #  return reverse('accounts:mypage_seller')

  #def form_invalid(self, form):
  #  return super().form_invalid(form)


class TxListView_buyer(LoginRequiredMixin, generic.UpdateView):

  login_url = '/accounts/login_buyer/'
  model = QpayTx
  template_name = "qpay/buyer/txList.html"
  form_class = TxListForm_buyer
  # context_object_name = 'qpaytxs'

  paginate_by = 5 # 5で仮置き

  def get(self, request, *args, **kwargs):

    user = UserModel.objects.get(email=self.request.user)
    object_list = QpayTx.objects.filter(buyEntity = user.entity).order_by('-created_at')
    print(f'request.user={request.user} def get in TxListView_buyer')

    # ログイン後にすぐに呼ばれることはなくなった中、必要か検討 24/07/02
    if user.type1 == 2:
    # 次のメッセージは確認できなかったので、要調整（トップページで出るようにする？）
      messages.add_message(request, messages.INFO, "発注者としてログインして下さい") 
      return HttpResponseRedirect(reverse('accounts:logout'))

    paginator = Paginator(object_list, self.paginate_by)

    # URLからページネーション経由でページ番号を取得する場合
    page_number = self.request.GET.get('page_number', None)
    if page_number is None:
      # viewを呼ぶときにページ番号が指定されている場合  
      page_number = self.kwargs.get('page_number', 1)
    print(f'pass1 page_number={page_number} in TxListView_buyer')

    page_obj = paginator.page(page_number)
    context = {
      'object_list': object_list,
      'page_obj': page_obj,
    }
    return render(request, 'qpay/buyer/txList.html', context)


# ゲストが取引履歴を確認するためのView   
class TxListView_seller(LoginRequiredMixin, generic.UpdateView):

  login_url = '/accounts/login_seller/'
  model = QpayTx
  template_name = "qpay/seller/txList.html"
  form_class = TxListForm_seller
  context_object_name = 'qpaytxs'
  paginate_by = 5 # 5で仮置き

  def get(self, request, *args, **kwargs):

    sellUser = UserModel.objects.get(email=self.request.user)
    object_list = QpayTx.objects.filter(
      sellEntity = sellUser.entity).order_by('-requested_at')

    if sellUser.type1 == 1:
    # 次のメッセージは確認できなかったので、要調整（トップページで出るようにする？）
      messages.add_message(request, messages.WARNING, "受注者としてログインして下さい") 
      return HttpResponseRedirect(reverse('accounts:logout'))

    paginator = Paginator(object_list, self.paginate_by)

    # URLからページネーション経由でページ番号を取得する場合
    page_number = self.request.GET.get('page_number', None)
    if page_number is None:
      # viewを呼ぶときにページ番号が指定されている場合  
      page_number = self.kwargs.get('page_number', 1)
    print(f'pass1 page_number={page_number} in TxListView_seller')

    page_obj = paginator.page(page_number)

    context = {
      'object_list': object_list,
      'page_obj': page_obj,
    }
    return render(request, 'qpay/seller/txList.html', context)


#  # 「モデル名（qpaytx）_list」が使える（ツボコツP130）
#  def get_context_data(self, **kwargs):  #テンプレートに特定entityの取引データを渡す
#    context = super().get_context_data(**kwargs)
#    return context

# 発注者が申請状況を確認するためのView   
class TxApproveView_buyer(LoginRequiredMixin, generic.UpdateView):

  login_url = '/accounts/login_buyer/'
  model = QpayTx
  form_class = TxApproveForm_buyer
  paginate_by = 4 # 4で仮置き
  #template_name = "qpay/buyer/txApprove.html"
  #context_object_name = 'qpaytxs'

  def get(self, request, *args, **kwargs):

    loginUser = UserModel.objects.get(email=self.request.user)

    OneWeekAgo = datetime.datetime.now() - datetime.timedelta(days=7)

    # 承認待ちの取引を抽出する   
    object_list = QpayTx.objects.select_related('buyUser').filter(
      Q(buyEntity=loginUser.entity)
      & (Q(txStatus_int=1) | Q(txStatus_int=3))
      & Q(created_at__gte=OneWeekAgo)).order_by('-requested_at')

    # 確認用
    cnt = QpayTx.objects.select_related('buyUser').filter(
      Q(buyEntity=loginUser.entity)
      & Q(txStatus_int__lte=3)
      & Q(created_at__gte=OneWeekAgo)).order_by('txStatus_int', '-requested_at').count()
    
    paginator = Paginator(object_list, self.paginate_by)

    # URLからページネーション経由でページ番号を取得する場合
    page_number = self.request.GET.get('page_number', None)
    if page_number is None:
      # viewを呼ぶときにページ番号が指定されている場合  
      page_number = self.kwargs.get('page_number', 1)
    print(f'pass1 page_number={page_number} in TxApproveView_buyer')

    page_obj = paginator.page(page_number)

    context = {
      'loginUser': loginUser,
      'object_list': object_list,
      'page_obj': page_obj,
    }
    return render(request, 'qpay/buyer/txApprove.html', context)


" 案内されたメールから前払いの承認をするためにQneePayに入る入口"
" tokenをtx_idに変換して、TxApproveDetailView_buyerを呼ぶ "
class TxApproveDetailPreView_buyer(LoginRequiredMixin, generic.TemplateView):

  login_url = '/accounts/login_buyer/'
  timeout_seconds = getattr(settings,  'ACTIVATION_TIMEOUT_SECONDS', 60*60*24)

  def get(self, request, *args, **kwargs):
      
    token = self.kwargs.get('token')  #kwargsはdict型 
    try:
      print(f'token={token} def get in class TxApproveDetailPreView_buyer')
      tx_id = loads(token, max_age=self.timeout_seconds)
      print(f'tx_id={tx_id} def get in class TxApproveDetailPreView_buyer')

    except SignatureExpired:
      return HttpResponseBadRequest()

    #tokenが間違っている
    except BadSignature:
      return HttpResponseBadRequest()

    return HttpResponseRedirect(reverse('qpay:txApproveDetail_buyer', kwargs={'tx_id': tx_id}))


# 発注者が前払いの承認するためのView（一覧又はメール内URLから遷移）  
class TxApproveDetailView_buyer(LoginRequiredMixin, generic.UpdateView):

  login_url = '/accounts/login_buyer/'
  model = QpayTx
  paginate_by = 5 # 5で仮置き

  def get(self, request, *args, **kwargs):

    tx = QpayTx.objects.get(pk=self.kwargs['tx_id'])
    self.request.session['tx_id'] = tx.pk
    tx_id = self.request.session.get('tx_id')
    print(f'tx_id = {tx_id} in get of TxApproveDetailView_buyer')

    return TemplateResponse(request,
      "qpay/buyer/txApproveDetail.html", {'tx': tx,}) 


  def post(self, request, *args, **kwargs):

    print(f'before ToRejectQpay in post of TxApproceDetailView_buyer')

    tx_id = self.kwargs['tx_id']
    tx =QpayTx.objects.select_related('sellEntity').get(pk=tx_id)

    next = self.request.POST.get('next', None) 
    print(f'pass0 next=={next} def post of TxApproDetailView_buyer')

    if next == "ToApproveQpay":
 
      # 承認された場合の処理（処理状況の更新、Qneeへの連絡等）を行う
      tx.txStatus_int = 2
      tx.txStatus_char = "承認済・前払い前"
      tx.approved_at = timezone.now()

      ## 一旦、リスクエスト金額を承認された金額にする 24/07/25
      tx.approved_amount = tx.requested_amount

      buyUser = UserModel.objects.get(email=self.request.user)
      tx.buyUser_userName = buyUser.userName

      tx.save()

      ## buyer承諾後に、sellerに承諾したことをメールで伝える

      """ 251103 「canApproveAll=True」「canApproveQpay=True」のユーザーに
          承認されたことを伝える """
      sellEntityUsers = UserModel.objects.select_related('entity').filter(
        Q(entity=tx.sellEntity) & (Q(canApproveAll=True) | Q(canApproveQpay=True))).values('userName','email','entity__entityName')
      # valuesは辞書型、value_listはタプルで戻る
      # （ご参考）https://se-memorandum.com/django-values-values_list/

      for eachUser in sellEntityUsers:

        current_site = get_current_site(self.request)
        domain = current_site.domain
        context1 = {
          'protocol': self.request.scheme,
          'domain': domain,
          'type1': 2,  # 承認された後、sellerがログインする場合の種別
          'token': dumps(tx.pk), # tx.pkを維持する必要ないので不要か
          'tx': tx,
          'flag_bankAccountUnset':
            1 if tx.sellEntity.bankAccount is not None else 0,
          'sellEntityUser': eachUser,
        }
        subject = render_to_string('qpay/buyer/mail/buyerApproved_subject.txt', context1)
        message = render_to_string('qpay/buyer/mail/buyerApproved_message.txt', context1)

        from_email = 'shuichiro.tomihari.201604@gmail.com'
        recipient_list =[eachUser['email']]
        #bcc =  ["toritoritorina@gmail.com"]  # BCCリスト
        email = EmailMessage(subject, message, from_email, recipient_list)
        email.send()

        flag_bankAccountUnset = 1 if tx.sellEntity.bankAccount is not None else 0
        print(f'flag_bankAccountUnset={flag_bankAccountUnset} in TxApproveDetailView_buyer')

      #del self.request.session['tx_id']
      return TemplateResponse(request, "qpay/buyer/txApproveDetail.html", {'tx': tx,})
    

    elif next == "ToRejectQpay":

      print(f'after ToRejectQpay in post of TxApproceDetailView_buyer')
      # 否認された場合の処理（処理状況の更新、受注者への連絡等）を行う
      tx.txStatus_int = 3
      tx.txStatus_char = "否認済み"
      tx.rejected_at = timezone.now()
      tx.save()

      context = {'tx': tx,}
      return TemplateResponse(request, "qpay/buyer/txApproveDetail.html", context)

    # これ使ってないのでは？（一覧に戻るときはGETで行くようにしている）
    # elif next == "ToBackToList":

      #buyEntity_id = self.request.session.get('buyEntity_id')
      #
      #buyEntity = LegalEntity.objects.get(pk=buyEntity_id)
      #object_list = QpayTx.objects.filter(
      #  buyEntity=buyEntity, txStatus_int=1).order_by('-requested_at')
      #
      #paginator = Paginator(object_list, self.paginate_by)
      #
      #context = {
      #  'tx_id': tx_id,
      #  'object_list': object_list,
      #  'page_obj': paginator.page(1),
      #}
      #del self.request.session['tx_id']
      #return TemplateResponse(request, "qpay/buyer/txApprove.html", context)
      return HttpResponseRedirect(
        reverse('qpay:txApprove_buyer', kwargs={'tx_id': tx_id}))

    print(f'pass3 other')
    
    return HttpResponseBadRequest()



# 発注者が申請状況を確認するためのView（一覧表から個別データのボタンを押した後）  
class TxDetailView_buyer(generic.UpdateView):

  model = QpayTx
  template_name = "qpay/buyer/txDetail.html"

  def get(self, request, *args, **kwargs):

    tx = QpayTx.objects.get(pk=self.kwargs['tx_id'])
    #vle = LegalEntity.objects.get(entityName=tx.buyEntityName)

    try:
      page_number = int(self.kwargs['page_number'])
    except:
      page_number = 1

    print(f'page_number={page_number} in TxHDetailView_buyer, get')
    context = {
      'tx': tx,
      'page_number': page_number
    }
    return TemplateResponse(request, "qpay/buyer/txDetail.html", context) 


# 発注者が申請状況を確認するためのView（一覧表から個別データのボタンを押した後）  
class TxDetailView_seller(generic.UpdateView):

  model = QpayTx
  template_name = "qpay/seller/txDetail.html"

  def get(self, request, *args, **kwargs):

    tx = QpayTx.objects.get(pk=self.kwargs['tx_id'])
    le = LegalEntity.objects.get(entityName=tx.buyEntityName)

    try:
      page_number = int(self.kwargs['page_number'])
      print(f'page_number={page_number} in TxDetailV, get')
    except:
      page_number = 1

    print(f'page_number={page_number} def get in TxDetailView_seller')
    return TemplateResponse(request, "qpay/seller/txDetail.html", { "tx": tx, 'page_number': page_number }) 

  def post(self, request, *args, **kwargs):
    tx =QpayTx.objects.get(pk=self.kwargs['tx_id'])
    return TemplateResponse(request, "qpay/seller/txDetail.html",{ "tx":tx })

  def get_success_url(self):
    return reverse_lazy('qpay:txList_seller')


class TxListView_admin(LoginRequiredMixin, generic.UpdateView):

  login_url = '/accounts/login_admin/'
  model = QpayTx
  template_name = "qpay/admin/txList.html"
  # context_object_name = 'qpaytxs'

  paginate_by = 5 # 5で仮置き

  def get(self, request, *args, **kwargs):

    user = UserModel.objects.get(email=self.request.user)
    object_list = QpayTx.objects.all().order_by('-created_at')
    print(f'request.user={request.user} def get in TxListView_admin')

    paginator = Paginator(object_list, self.paginate_by)

    # URLからページネーション経由でページ番号を取得する場合
    page_number = self.request.GET.get('page_number', None)
    if page_number is None:
      # viewを呼ぶときにページ番号が指定されている場合  
      page_number = self.kwargs.get('page_number', 1)
    print(f'pass1 page_number={page_number} in TxListView_admin')

    page_obj = paginator.page(page_number)
    context = {
      'object_list': object_list,
      'page_obj': page_obj,
    }
    return render(request, 'qpay/admin/txList.html', context)


# 発注者が申請状況を確認するためのView   
class TxInboxView(generic.UpdateView):

  model = QpayTx
  template_name = "qpay/admin/txInbox.html"
  paginate_by = 5 # 5で仮置き

  def get(self, request, *args, **kwargs):

    # パートナーに承認されたデータを抽出する
    object_list = QpayTx.objects.select_related('sellEntity').filter(
      Q(txStatus_int=1) | Q(txStatus_int=2)).order_by('-requested_at')
    
    # 確認用
    cnt = QpayTx.objects.select_related('sellEntity').filter(
      Q(txStatus_int=1) | Q(txStatus_int=2)).order_by('-requested_at').count()
    print(f'cnt={cnt} in def get of TxInboxView')

    paginator = Paginator(object_list, self.paginate_by)

    # URLからページネーション経由でページ番号を取得する場合
    page_number = self.request.GET.get('page_number', None)
    if page_number is None:
      # viewを呼ぶときにページ番号が指定されている場合  
      page_number = self.kwargs.get('page_number', 1)
    print(f'pass1 page_number={page_number} in TxInboxView')

    print(f'page_numnber={page_number} in TxInboxView')
    page_obj = paginator.page(page_number)

    context = {
      'object_list': object_list,
      'page_obj': page_obj,
    }
    return render(request, 'qpay/admin/txInbox.html', context)


" 案内されたメールからアプリに入って振り込みを行う場合の処理 "
" tokenをtx_idに変換して、TxInboxDetailView_buyerを呼ぶ "
class TxInboxDetailPreView(LoginRequiredMixin, generic.TemplateView):

  login_url = '/accounts/login_buyer/'
  template_name = 'qpay/admin/TxInboxDetailPreView.html'
  timeout_seconds = getattr(settings,  'ACTIVATION_TIMEOUT_SECONDS', 60*60*24)

  def get(self, request, *args, **kwargs):
      
    token = self.kwargs.get('token')  #kwargsはdict型
    print(f'token={token} def get in class TxInboxDetailPreView')
    
    try:
      tx_id = loads(token, max_age=self.timeout_seconds)
      print(f'tx_id={tx_id} def get in class TxInboxDetailPreView')

    except SignatureExpired:
      return HttpResponseBadRequest()

    #tokenが間違っている
    except BadSignature:
      return HttpResponseBadRequest()

    return HttpResponseRedirect(reverse('qpay:txInboxDetail', kwargs={'tx_id': tx_id}))


# 発注者が前払いの承認するためのView（一覧又はメール内URLから遷移）  
class TxInboxDetailView(LoginRequiredMixin, generic.UpdateView):

  login_url = '/accounts/login_admin/'
  model = QpayTx
  #template_name = "qpay/admin/txInboxDetail.html"

  def get(self, request, *args, **kwargs):

    tx = QpayTx.objects.get(pk=self.kwargs['tx_id'])
    buyEntity = LegalEntity.objects.get(pk=tx.buyEntity_id)
    sellEntity = LegalEntity.objects.get(pk=tx.sellEntity_id)

    print(f'buyEntity.id={buyEntity.id} in get of TxInboxDetailView')
    print(f'sellEntity.bankAccount={sellEntity.bankAccount} in get of TxInboxDetailView')
    print(f'sellEntity.bankAccount_id={sellEntity.bankAccount_id} in get of TxInboxDetailView')

    if BankAccount.objects.filter(pk=sellEntity.bankAccount_id).exists():

      bankAccount = BankAccount.objects.get(pk=sellEntity.bankAccount_id)
      return TemplateResponse(request,
        "qpay/admin/txInboxDetail.html", {'tx': tx, 'ba': bankAccount,}) 

    else:
      messages.add_message(request, messages.WARNING, "ゲスト側で受取口座が未設定です。メールにて設定依頼をしました") 

      sellUser = UserModel.objects.get(pk=tx.sellUser_id)
      sellEntity = LegalEntity.objects.get(pk=tx.sellEntity_id)

      current_site = get_current_site(self.request)
      domain = current_site.domain
      context = {
        'protocol': self.request.scheme,
        'domain': domain,
        'type1': 2,  # 承認された後、sellerがログインする場合の種別
        'token': dumps(tx.pk), # tx.pkを維持する必要ないので不要か
        'tx': tx,}

      subject = render_to_string('qpay/admin/mail/bankAccountUnset_subject.txt', context)
      message = render_to_string('qpay/admin/mail/bankAccountUnset_message.txt', context)

      from_email = 'shuichiro.tomihari.201604@gmail.com'
      recipient_list =[sellUser.email]
      #bcc =  ["toritoritorina@gmail.com"]  # BCCリスト
      email = EmailMessage(subject, message, from_email, recipient_list)
      email.send()
      
      return TemplateResponse(request,
        "qpay/admin/txInboxDetail.html",  {'tx': tx }) 


  def post(self, request, *args, **kwargs):

    tx =QpayTx.objects.get(pk=self.kwargs['tx_id'])

    next = self.request.POST.get('next', None) 
    if next == "ToTransferMoney":

      print("「振込処理する」が押下された post in TxInboxDetailView")
      # 承認された場合の処理（処理状況の更新、Qneeへの連絡等）を行う
      tx.txStatus_int = 4
      tx.txStatus_char = "承認済み・前払い済み" 
      tx.payed_at = timezone.now()
      
      ## 一旦、リスクエスト金額を承認された金額にする 24/07/25
      tx.approved_amount = tx.requested_amount
      tx.save()

      ## buyer承諾後に、sellerに承諾したことをメールで伝える

      """ 251103 「canApproveAll=True」「canApproveQpay=True」のユーザーに
          承認されたことを伝える """
      sellEntityUsers = UserModel.objects.select_related('entity').filter(
        Q(entity=tx.sellEntity) & (Q(canApproveAll=True) | Q(canApproveQpay=True))).values('userName','email','entity__entityName')
      # valuesは辞書型、value_listはタプルで戻る
      # （ご参考）https://se-memorandum.com/django-values-values_list/

      for eachUser in sellEntityUsers:

        current_site = get_current_site(self.request)
        domain = current_site.domain
        context1 = {
          'protocol': self.request.scheme,
          'domain': domain,
          'type1': 2,  # 承認された後、sellerがログインする場合の種別
          'token': dumps(tx.pk), # tx.pkを維持する必要ないので不要か
          'tx': tx,
          'sellEntityUser': eachUser,
        }

        subject = render_to_string('qpay/admin/mail/adminPayed_subject.txt', context1)
        message = render_to_string('qpay/admin/mail/adminPayed_message.txt', context1)

        from_email = 'shuichiro.tomihari.201604@gmail.com'
        recipient_list =[eachUser['email']]
        #bcc =  ["toritoritorina@gmail.com"]  # BCCリスト
        email = EmailMessage(subject, message, from_email, recipient_list)
        email.send()

      return TemplateResponse(request,
        "qpay/admin/txInboxDetail.html", { 'tx': tx, })
      #return HttpResponseRedirect(self.get_success_url())

    elif next == "RejectRemittance":

      # 否認された場合の処理（処理状況の更新、受注者への連絡等）を行う
      tx.txStatus_int = 5
      tx.txStatus_char = "承認済み・支払い保留"
      tx.rejected_at = timezone.now()
      tx.save()

      context = {
        'tx': tx,
      }  
      return TemplateResponse(request, "qpay/admin/txInboxDetail.html", context)


    #elif next == "BackToList":
    #
    #  object_list = QpayTx.objects.filter(
    #    txStatus_int=2).order_by('-requested_at')
    #
    #  paginator = Paginator(object_list, self.paginate_by)
    #
    #  context = {
    #    'object_list': object_list,
    #    'page_obj': paginator.page(1),
    #  }
    #  return TemplateResponse(request, "qpay/admin/txInbox.html", context)

    return HttpResponseBadRequest()


" 案内されたメールから遷移して振り込みをする場合"
" tokenをtx_idに変換して、TxApproveDetailView_buyerを呼ぶ "
class TxInboxDetailPreView(generic.TemplateView):

  #template_name = 'qpay/admin/txInboxDetailPre.html'
  timeout_seconds = getattr(settings,  'ACTIVATION_TIMEOUT_SECONDS', 60*60*24)

  def get(self, request, *args, **kwargs):
      
    token = self.kwargs.get('token')  #kwargsはdict型
    print(f'token={token} def get in class TxInboxDetailPreView')
    
    try:
      tx_id = loads(token, max_age=self.timeout_seconds)
      print(f'tx_id={tx_id} def get in class TxInboxDetailPreView')

    except SignatureExpired:
      return HttpResponseBadRequest()

    #tokenが間違っている
    except BadSignature:
      return HttpResponseBadRequest()

    return HttpResponseRedirect(reverse('qpay:txInboxDetail', kwargs={'tx_id': tx_id}))
