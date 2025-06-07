from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render
from django.contrib.auth import get_user_model
from django.views import generic

#from qpay.models import QpayTx
from accounts.models import LegalEntity
from send.form import QpayInfoSend \

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


class QpayInfoSendView(generic.CreateView):

  model = QpayInfoSend
  template_name = 'send/qpayinfo_send.html'
  form_class = QpayinfoSendForm

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
