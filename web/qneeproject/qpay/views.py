from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render
from django.contrib.auth import get_user_model
from django.views import generic
from .models import QpayTx, SendbackInfo, ClearingInfo
from accounts.models import LegalEntity, BankAccount, CorpInfo
from qpay.form import TxCreateForm, TxEvidenceForm, \
      TxApproveForm_buyer, TxPeriodSetForm, \
      TxListForm_seller, TxReapplyForm, SendbackInfoForm_qpay

from django.urls import reverse, reverse_lazy
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
from django.utils import timezone
from dateutil.relativedelta import relativedelta
import calendar

#import calendar

#from dateutil.relativedelta import relativedelta
# 以下は2025/02/14時点で使われていない参照
# from accounts.models import CustomUser
# from django.db import models

UserModel = get_user_model()

#def top(request):
#  return render(request, 'qpay/top.html')
from django.db.models import Sum, Count
from django.db.models.functions import TruncMonth

class TxListView_buyer(LoginRequiredMixin, generic.UpdateView):

  login_url = '/accounts/login_buyer/'
  model = QpayTx
  template_name = "qpay/buyer/txList.html"

  paginate_by = 6 # 6で仮置き

  def get(self, request, *args, **kwargs):

    user = UserModel.objects.get(email=self.request.user)
    IndivOrAggreg = self.request.GET.get('name_IndivOrAggreg', None)

    # パラメーター確認用
    print(f'IndivOrAggreg={IndivOrAggreg} def get in TxListView_buyer')
    print(f'self.paginate_by={self.paginate_by}')

    if IndivOrAggreg == None or IndivOrAggreg == 'indiv':
      IndivOrAggreg = 'indiv'

      # 初回（設定値がない場合）は"2W"とする
      applyPeriod = self.request.GET.get('applyPeriod', '2W')

      today = datetime.date.today()
      if applyPeriod == '0': periodStart = datetime.date(2024, 8, 5)
      elif applyPeriod=='2W': periodStart = today + relativedelta(weeks=-2)
      elif applyPeriod=='1M': periodStart = today + relativedelta(months=-1)
      elif applyPeriod=='3M': periodStart = today + relativedelta(months=-3)
      elif applyPeriod=='6M': periodStart = today + relativedelta(months=-6)
      elif applyPeriod=='1Y': periodStart = today + relativedelta(years=-1)

      print(f'applyPerod_value={applyPeriod} def get of TxListView_buyer')
      print(f'periodStart={periodStart} def get of TxListView_buyer')

      object_list = QpayTx.objects.filter(
        buyEntity=user.entity, created_at__gte=periodStart).order_by('-created_at')

      paginator = Paginator(object_list, self.paginate_by)

      # URLからページネーション経由でページ番号を取得する場合
      page_number = self.request.GET.get('page_number', None)
      if page_number is None:
        # viewを呼ぶときにページ番号が指定されている場合  
        page_number = self.kwargs.get('page_number', 1)
        page_obj = paginator.page(page_number)

      context = {
        'form': TxPeriodSetForm(initial={
          'applyPeriod': applyPeriod,
          'applyPeriod_start': periodStart.strftime('%Y-%m-%d'),
          'applyPeriod_end': today.strftime('%Y-%m-%d'),}),
          
        'IndivOrAggreg': IndivOrAggreg,
        'object_list': object_list,
        'page_obj': page_obj,
      }
      return render(request, 'qpay/buyer/txList.html', context)


    elif IndivOrAggreg == 'aggreg':

      # ★★ 260426 advanced_atに値が入った段階で、approved_at ⇒ advanced_atに変換する
      object_list = QpayTx.objects.filter(
        buyEntity = user.entity, created_at__isnull = False).annotate(
        month=TruncMonth('created_at')).values('sellEntityname','month').annotate(
        total_advance_amount = Sum('advance_amount'),  # 前払い額合計
        total_advance_count = Count('advance_amount'),  # 件数
        total_advance_fee = Sum('advance_fee'),  # パートナー宛の手数料の合計
        ).order_by('-month')

      #print(f'object_list={object_list}')

      for each in object_list:
        print(f'each={each}')

      paginator = Paginator(object_list, self.paginate_by)

      # URLからページネーション経由でページ番号を取得する場合
      page_number = self.request.GET.get('page_number', None)
      if page_number is None:
        # viewを呼ぶときにページ番号が指定されている場合  
        page_number = self.kwargs.get('page_number', 1)
      print(f'pass1 page_number={page_number} in TxListView_buyer')

      page_obj = paginator.page(page_number)
      context = {
        'form': TxPeriodSetForm(),
        'IndivOrAggreg': IndivOrAggreg,
        'object_list': object_list,
        'page_obj': page_obj,
      }
      return render(request, 'qpay/buyer/txList.html', context)


# 発注者が申請状況を確認するためのView（一覧表から個別データのボタンを押した後）  
class TxListDetailView_buyer(generic.UpdateView):

  model = QpayTx
  template_name = "qpay/buyer/txListDetail.html"

  def get(self, request, *args, **kwargs):

    tx = QpayTx.objects.get(pk=self.kwargs['tx_id'])
    #vle = LegalEntity.objects.get(entityname=tx.buyEntityname)

    try:
      page_number = int(self.kwargs['page_number'])
    except:
      page_number = 1

    print(f'page_number={page_number} in TxHDetailView_buyer, get')
    context = {
      'tx': tx,
      'page_number': page_number
    }
    return TemplateResponse(request, "qpay/buyer/txListDetail.html", context) 


# ゲストが取引履歴を確認するためのView   
class TxListView_seller(LoginRequiredMixin, generic.UpdateView):

  login_url = '/accounts/login_seller/'
  model = QpayTx
  template_name = "qpay/seller/txList.html"
  form_class = TxListForm_seller
  context_object_name = 'qpaytxs'
  paginate_by = 6 # 6で仮置き

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


# ★★ 受注者が前払い申請する際に利用するビュー（工事中）
class TxCreateView(generic.CreateView):

  model = QpayTx
  template_name = 'qpay/seller/txCreate.html'
  form_class = TxCreateForm

  def dispatch(self, request, *args, **kwargs):
  
    self.request.session['dict_buyEntityname'] = \
      dict((f, f) for idx, f in enumerate(LegalEntity.objects.filter(type1=1).values_list('entityname', flat=True), 1))
  
    """ 初回のマイグレーションの時のみ下記を採用する """
    #dict_buyEntityname = {'Qnee','Qnee'}
    # 「flat=True」はリスト、「flat=False」はタプル
  
    return super().dispatch(request, *args, **kwargs)
  

  def get(self, request, *args, **kwargs):

    #sellUser = UserModel.objects.get(email=self.request.user)
    #sellEntity = LegalEntity.objects.get(pk=sellUser.entity_id)

    sellUser_id = self.request.session.get('sellUser_id')
    sellUser = UserModel.objects.get(pk=sellUser_id)
    sellEntity = LegalEntity.objects.get(pk=sellUser.entity_id)

    dict_buyEntityname = self.request.session.get('dict_buyEntityname')

    init_dict = {
      'buyEntityname': "",
      'sellUser_email': sellUser.email,
      'sellUser_personname': sellUser.personname,
      'sellEntityname': sellEntity.entityname,
    }
    form = self.form_class(initial=init_dict)

    context = {
      'flag_step': 1,
      'sellUser': sellUser,
      'sellEntity': sellEntity,
      'form': form,
      'temporal_buyEntityname': "",
      'dict_buyEntityname': dict_buyEntityname,
      #'temporal_sellEntityname': sellEntity.entityname, # 250608 Selectボックス未選択を示す
      #'dict_sellEntityname': dict_sellEntityname,

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
        tx.sellUser_personname = sellUser.personname
        tx.sellEntity = sellEntity
        tx.sellEntiyname = sellEntity.entityname
        
        buyEntityname = self.request.POST['buyEntityname']
        tx.buyEntityname = buyEntityname

        buyEntity = LegalEntity.objects.get(entityname=buyEntityname)
        tx.buyEntity = buyEntity

        # tx.buyUser, tx.buyUser_personnameは承認時に入力する 260515

        # 各種金額を計算       
        tx.advance_amount = tx.requested_amount
        tx.advance_fee = (tx.requested_amount * buyEntity.advance_fee_rate) //1
        tx.referral_fee = (tx.requested_amount * buyEntity.referral_fee_rate) //1
        tx.transfer_fee = 110
        tx.transfer_amount = tx.advance_amount - tx.advance_fee - tx.transfer_fee

        tx.save()
        print(f'tx.transfer_amount={tx.transfer_amount} def post in TxCreateView  ')

        self.request.session['tx_id'] = tx.id

        # print(f'メールアドレス：{tx.buyUser_email} next==confirm in TxCreateView')
        print(f'pass4 tx.buyEntityname={tx.buyEntityname} TxCreateViewV, post, next==ToConfirm')
        print(f'pass4 tx.sellUser_personname={tx.sellUser_personname} TxCreateViewV, post, next==ToConfirm')

        context = {
          'flag_step': 2,
          'sellUser': sellUser,
          'sellEntity': sellEntity,
          'tx': tx,
          'form':form,
          #'buyEntityname': buyEntityname,
        }
        return render(self.request, 'qpay/seller/txCreate.html', context)

      else: # 「if form.is_valid() == False」の場合

        sellUser_id = self.request.session.get('sellUser_id')
        sellUser = UserModel.objects.get(pk=sellUser_id)
        sellEntity = LegalEntity.objects.get(pk=sellUser.entity_id)

        dict_buyEntityname = self.request.session.get('dict_buyEntityname')

        context = {
          'flag_step': 1,
          'sellUser': sellUser,
          'sellEntity': sellEntity,
          'form':form,
          'temporal_sellEntityname': self.request.POST['sellEntityname'],
          'temporal_buyEntityname': self.request.POST['buyEntityname'],
          'dict_sellEntityname': dict_buyEntityname,
          'dict_buyEntityname': dict_buyEntityname,
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

      temporal_sellEntityname = sellEntity.entityname
      temporal_buyEntityname = self.request.POST['buyEntityname']
      print(f'pass4 temporal_sellEntityname={temporal_sellEntityname} in TxCreateV, post, next==BackToInput')
      print(f'pass4 temporal_buyEntityname={temporal_buyEntityname} in TxCreateV, post, next==BackToInput')

      dict_buyEntityname = self.request.session.get('dict_buyEntityname')

      context = {
        'flag_step': 1,
        'sellUser': sellUser,
        'sellEntity': sellEntity,
        'tx': tx,
        'form': form,
        'temporal_buyEntityname': temporal_buyEntityname,
        'dict_buyEntityname': dict_buyEntityname,
        #'temporal_sellEntityname': temporal_sellEntityname,
        #'dict_sellEntityname': dict_sellEntityname,

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
        tx.requested_at = timezone.now()
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
      tx.txStatus = 1
      tx.txStatus_char = 'ゲスト申請済・パートナー承認前'
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
            'afterLogin': 'qpayApprove',
            'token': dumps(tx.pk),
            'tx': tx,
            'buyEntityApprover': eachUser,
          }
          subject = render_to_string('qpay/seller/mail/qpayApply_subject.txt', context)
          message = render_to_string('qpay/seller/mail/qpayApply_message.txt', context)

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


# ★★ 20260629 受注者が前払い申請する際に利用するビュー（工事中）

from django.forms import modelformset_factory

class TxReapplyView_seller(generic.UpdateView):

  model = QpayTx
  template_name = 'qpay/seller/txCreate.html'
  form_class = TxReapplyForm

  def dispatch(self, request, *args, **kwargs):
  
    self.request.session['dict_buyEntityname'] = \
      dict((f, f) for idx, f in enumerate(LegalEntity.objects.filter(type1=1).values_list('entityname', flat=True), 1))
  
    """ 初回のマイグレーションの時のみ下記を採用する """
    #dict_buyEntityname = {'Qnee','Qnee'}
    # 「flat=True」はリスト、「flat=False」はタプル
  
    return super().dispatch(request, *args, **kwargs)
  

  def get(self, request, *args, **kwargs):

    sellUser_id = self.request.session.get('sellUser_id')
    sellUser = UserModel.objects.get(pk=sellUser_id)
    sellEntity = LegalEntity.objects.get(pk=sellUser.entity_id)
    txQueryset = QpayTx.objects.select_related('sendbackInfo_buyer').filter(
      Q(sellEntity=sellEntity) & Q(txStatus=2))
    print(f'txQueryset.count={txQueryset.count()}')

    TxReapplyFormSet = modelformset_factory(
        QpayTx,
        form = TxReapplyForm, 
        extra = 0
    )   
    formset = TxReapplyFormSet(queryset=txQueryset)
    print(f"Formset total forms: {formset.total_form_count()}") 

    dict_buyEntityname = self.request.session.get('dict_buyEntityname')

    context = {
      'step_reapply': 1,
      'flag_formset': 1,
      'formset': formset,
      'dict_buyEntityname': dict_buyEntityname,
    }
    return render(request, 'qpay/seller/txReapply.html', context)

  
  def post(self, request, *args, **kwargs):

    actionBtn = self.request.POST.get('actionBtn', '')   # POST.getはミドルウェア機能
    #actionBtn2 = self.request.POST.get('actionBtn2', '')   # POST.getはミドルウェア機能

    print(f'actionBtn={actionBtn}')
    print(f'ファイル名={request.FILES}')

    # formsetを使うパターンにおいて
    # <input type="hidden" name="tx_id" value="{{ form.instance.id }}">から取得する
    # 但し、単独フォームの時はテンプレート上にのtx（QpayTxインスタンス）

    if actionBtn.find('ToConfirm') >= 0:

      print(self.request.POST)

      tx_id = actionBtn.split('_')[1]
      form_index = actionBtn.split('_')[2]
      
      tx = QpayTx.objects.get(pk=tx_id)
      user = UserModel.objects.get(email=self.request.user)
      print(f'self.request.user={self.request.user} in def post of TxReapplyView_seller')
      print(f'user.personname={user.personname} in def post of TxReapplyView_seller')

      # 2. FormSetではなく、通常の単一フォーム「TxReapplyForm」を使用する
      # 【重要】HTML側のプレフィックス（form-0-など）を prefix 引数で指定する
      form = TxReapplyForm(
          self.request.POST, 
          self.request.FILES, 
          instance=tx,
          prefix=f'form-{int(form_index)}'
      )
      """ この時点で「tx.sellUser_personname=None」の為、request.POSTを上書き """
      """ なお、request.POSTを上書きするため設定を変更 """
      if hasattr(form.data, '_mutable'):
        form.data._mutable = True
      form.data[f'form-{int(form_index)}-sellUser_personname'] = user.personname          
   
      if form.is_valid():
        # 「.is_valid()」の後、フォームでのclean、clean_<field>が実行され、

        # tx.buyUser, tx.buyUser_personnameは承認時に入力する 260629

        # 各種金額を計算
        tx.advance_amount = tx.requested_amount
        tx.advance_fee = (tx.requested_amount * tx.buyEntity.advance_fee_rate) //1
        tx.referral_fee = (tx.requested_amount * tx.buyEntity.referral_fee_rate) //1
        tx.transfer_fee = 110
        tx.transfer_amount = tx.advance_amount - tx.advance_fee - tx.transfer_fee

        tx.save()

        # print(f'メールアドレス：{tx.buyUser_email} actionBtn1==confirm in TxReapplyView')
        print(f'tx.transfer_amount={tx.transfer_amount} def post in TxReapplyView_seller')
        print(f'pass4 tx.buyEntityname={tx.buyEntityname} TxReapplyViewView_seller, post, next==ToConfirm')

        context = {
          'step_reapply': 2,
          'form':form,
          'tx': tx,
          'sellUser_personname': user.personname,
          #'buyEntityname': buyEntityname,
        }
        return render(self.request, 'qpay/seller/txReapply.html', context)

      else: # 「if form.is_valid() == False」の場合

        print(f'form.errors={form.errors}')
        TxReapplyFormSet = modelformset_factory(
          QpayTx,
          form = TxReapplyForm, 
          extra = 0
        )
        formset = TxReapplyFormSet(self.request.POST, self.request.FILES )

        dict_buyEntityname = self.request.session.get('dict_buyEntityname')
        buyEntityname = self.request.POST.get(f'form-{form_index}-buyEntityname')
        exPayment_date = self.request.POST.get(f'form-{form_index}-exPayment_date')
        print(f'buyEntityname={buyEntityname}')
        print(f'exPayment_data={exPayment_date}')

        #print(f"--- デバッグ開始 ---")
        #print(f"抽出した form_index: {form_index}")
        #print(f"届いているPOSTデータの全キー: {list(request.POST.keys())}")
        #print(f"--- デバッグ終了 ---")
        #print(f'form.errors={form.errors}') 

        context = {
          'step_reapply': 1,
          'flag_formset': 1,
          'formset': formset,
          'tx': tx,
          'temporal_buyEntityname': self.request.POST.get(f'form-{form_index}-buyEntityname'),
          'dict_buyEntityname': dict_buyEntityname,
          #'exPayment_date': exPayment_date,
          # exPayment_dateは検証中。入力した画面に戻ると、値が「年/月/日」の表示になる（日付にならない）
          #'buyEntityname': buyEntityname,
        }
        return render(self.request, 'qpay/seller/txReapply.html', context)       
        #return HttpResponseRedirect(reverse_lazy('qpay:txReaaply_seller'))

    # 申請データの編集を終え、再申請する
    if actionBtn.find('ToReapplyQpay') >= 0:

      tx_id = actionBtn.split('_')[1]
      tx = QpayTx.objects.select_related('buyEntity').get(pk=tx_id)

      tx.txStatus = 1
      tx.txStatus_char = "ゲスト再申請済・パートナー再承認前"
      tx.requested_at = timezone.now()  # 申請した時点を記録する

      #tx.sendbackInfo = None

      tx.save()

      QpayTx.objects.filter(pk__lt=tx.id, requested_at=None).delete()
      #「__lt=a」でaより小さい、[__lte=a]でa以下。AND条件は「,」でつなぐ

      # メール送付の処理
      """ 260629 「canApproveAll=True」「canApproveQpay=True」のユーザーに
          差し戻された申請が再申請されたことを伝える """
      sellEntityUsers = UserModel.objects.select_related('entity').filter(
        Q(entity=tx.sellEntity)
        & (Q(canApproveAll=True) | Q(canApproveQpay=True)))

      for sellUser in sellEntityUsers:

        context1 = {
          'token': dumps(tx.pk), # tx.pkを維持する必要ないので不要か
          'tx': tx,
          'afterLogin': 'qpayApprove',
        }
        utils.sendEmail_common(
          'qpay/seller/mail/qpayReapply', '', [sellUser.email], context1)

      messages.add_message(request, messages.SUCCESS,
        '差戻された前払い申請についてパートナー企業に再申請しました。')

      context = { 'step_reapply': 3, 'tx': tx, }
      return TemplateResponse(request, "qpay/seller/txReapply.html", context)


    # データ確認画面から入力画面に戻る時の処理 2025/02/14
    if actionBtn.find('BackToInput') >= 0:

      return HttpResponseRedirect(reverse_lazy('qpay:txReapply_seller'))
      #form = TxReapplyForm(self.request.POST, request.FILES)

      #tx = QpayTx.objects.get(pk=tx_id)
      #temporal_buyEntityname = self.request.POST['buyEntityname']
      #dict_buyEntityname = self.request.session.get('dict_buyEntityname')

      # ★★　20260709 初期値を設定する必要があるかは要検証
      #context = {
      #  'step_reapply': 1,
      #  'flag_formset': 0,
      #  'form': form,
      #   'tx': tx,
      #  'temporal_buyEntityname': temporal_buyEntityname,
      #  'dict_buyEntityname': dict_buyEntityname,
      #  #'temporal_sellEntityname': temporal_sellEntityname,
      #  #'dict_sellEntityname': dict_sellEntityname,
      #
      #}
      #return render(self.request, 'qpay/seller/txReapply.html', context)

    # ★★　申請を取り下げる
    if actionBtn.find('ToDropApply') >= 0:

      tx.txStatus = -1;
      tx.txStatus_char = 'ゲスト取下'
      tx.save()
      return HttpResponseRedirect(reverse_lazy('qpay:txReapply_seller'))


    else: # 想定してないケースが発生
  
      # self.request.POST.get('actionBtn', '')が何にも該当しない場合
      messages.add_message(request, messages.WARNING, '想定してないケースが発生しました。お手数ですがお問い合わせ頂けると有難いです。')
      print(f'pass7 actionBtnがどれにも該当せず（エラー）（TxReapplyView_seller, post）')

      return TemplateResponse(self.request, 'qpay/seller/txReapply.html', {'form':form},)      #contextを見直しが必要（基本的にはあまり通らないところだが）



# 発注者が申請状況を確認するためのView   
class TxApproveView_buyer(LoginRequiredMixin, generic.UpdateView):

  login_url = '/accounts/login_buyer/'
  model = QpayTx
  form_class = TxApproveForm_buyer
  paginate_by = 5 # 4で仮置き
  #template_name = "qpay/buyer/txApprove.html"
  #context_object_name = 'qpaytxs'

  def get(self, request, *args, **kwargs):

    loginUser = UserModel.objects.get(email=self.request.user)

    TwoWeeksAgo = datetime.datetime.now() - relativedelta(weeks=2)

    # 承認待ちの取引を抽出する   
    object_list = QpayTx.objects.select_related(
      'buyUser', 'sendbackInfo_admin', 'sendbackInfo_buyer'
      ).filter(
        Q(buyEntity=loginUser.entity)
        & (Q(txStatus=1) | Q(txStatus=-3) | Q(txStatus=4))
        ).order_by('-requested_at')

    # 確認用
    cnt = QpayTx.objects.select_related('buyUser').filter(
      Q(buyEntity=loginUser.entity)
      & (Q(txStatus=1) | Q(txStatus=-3) | Q(txStatus=4))
      ).order_by('txStatus', '-requested_at').count()
    print(f'cnt_qpaytx={cnt}')
    
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

    tx = QpayTx.objects.select_related(
      'sendbackInfo_admin','sendbackInfo_buyer').get(pk=self.kwargs['tx_id'])

    self.request.session['tx_id'] = tx.pk
    tx_id = self.request.session.get('tx_id')
    print(f'tx_id = {tx_id} in get of TxApproveDetailView_buyer')

    context = { 'step_process': 1, 'tx': tx, }
    return TemplateResponse(request,
      "qpay/buyer/txApproveDetail.html", context) 


  def post(self, request, *args, **kwargs):

    print(f'before ToRejectQpay in post of TxApproceDetailView_buyer')

    tx_id = self.kwargs['tx_id']
    tx =QpayTx.objects.select_related('sellEntity', 'buyEntity').get(pk=tx_id)
    buyUser = UserModel.objects.get(email=self.request.user)
    # 承認・否認したユーザーを登録するために抽出しておく

    actionBtn = self.request.POST.get('actionBtn', None) 
    print(f'pass0 actionBtn=={actionBtn} def post of TxApproDetailView_buyer')

    if actionBtn.find('ToApproveQpay') >= 0:
 
      # 承認された場合の処理
      tx.txStatus = 3
      if tx.sendbackInfo_buyer is None:
        tx.txStatus_char = "ゲスト申請・パートナー承認済"
      else:
        tx.txStatus_char = "ゲスト再申請・パートナー再承認済"

      ## 一旦、リスクエスト金額を承認された金額にする 24/07/25
      tx.approved_amount = tx.requested_amount
      tx.approved_at = timezone.now()

      tx.buyUser = buyUser
      tx.buyUser_personname = buyUser.personname

      tx.save()

      ## buyer承諾後に、sellerに承諾したことをメールで伝える

      """ 260620 「canApproveAll=True」「canApproveQpay=True」のユーザーに
          承認されたことを伝える """
      sellEntityUsers = UserModel.objects.select_related('entity').filter(
        Q(entity=tx.sellEntity)
        & (Q(canApproveAll=True) | Q(canApproveQpay=True))).values('personname','email','entity__entityname')
      # valuesは辞書型、value_listはタプルで戻る
      # （ご参考）https://se-memorandum.com/django-values-values_list/

      for eachUser in sellEntityUsers:

        context1 = {
          #'type1': 2,  # 承認された後、sellerがログインする場合の種別
          'token': dumps(tx.pk), # tx.pkを維持する必要ないので不要か
          'tx': tx,
          'flag_bankAccountUnset':
            0 if tx.sellEntity.bankAccount is None else 1,
          'afterLogin': '' if tx.sellEntity.bankAccount is None else 'bankAccountSet',
          # 口座未設定の場合は、ログイン後、設定画面に行くようにする
        }
        utils.sendEmail_common(
          'qpay/buyer/mail/approveToSeller', '', [eachUser['email']], context1)

        # 確認用
        flag_bankAccountUnset = 1 if tx.sellEntity.bankAccount is not None else 0
        print(f'flag_bankAccountUnset={flag_bankAccountUnset} in TxApproveDetailView_buyer')

      #del self.request.session['tx_id']
      context = { 'step_process': 1, 'tx': tx,}
      return TemplateResponse(request, "qpay/buyer/txApproveDetail.html", context)


    # 差戻しした場合の処理
    elif actionBtn.find('ToSendbackQpay1') >= 0:

      context = {
        'step_process': 2,
        'tx': tx,
        'form': SendbackInfoForm_qpay(),}
      return TemplateResponse(request, "qpay/buyer/txApproveDetail.html", context)


    elif actionBtn.find('ToSendbackQpay2') >= 0:

      reason_radio = self.request.POST.get('reason_radio')
      print(f'reason_radio={reason_radio}')
      
      form = SendbackInfoForm_qpay(request.POST)
      print("=== request.POST の全中身 ===")
      print(request.POST)
      print("=============================")

      if form.is_valid(): 

        print(f'pass1 after if form.is_valid==True in TxApproveDetailView_buyer')

        #message = form.cleaned_data['message']
        selectedValue = form.cleaned_data.get('reason_radio')
        reason = dict(form.fields['reason_radio'].choices).get(selectedValue)
        print(f'reason={reason}')

        if selectedValue == 'radio4':
          print(f'pass2 after if form.is_valid==True in TxApproveDetailView_buyer')
          reason = form.cleaned_data['reason_text']
        
        message = form.cleaned_data['message']
        print(f'message={message} if actionBtn.find(ToSendbackQpay2) of TxApproveDetailView_buyer')
        sb = SendbackInfo.objects.create(
          qpaytx=tx, type1_frWho=1,
          reason=reason, message=message,
          created_at=timezone.now())

        sb.save()

        tx.txStatus = 2
        tx.txStatus_char = "ゲスト申請差戻・パートナー差戻済"
        tx.sendbackInfo_buyer = sb
      
        tx.buyUser = buyUser
        tx.buyUser_personname = buyUser.personname

        #tx.sendbackReason = reason_radio
        #tx.sendbackMessage = message

        tx.save()

        print(f'tx.txStatus={tx.txStatus}')


        """ 260620 「canApproveAll=True」「canApproveQpay=True」のユーザーに
            差し戻されたことを伝える """
        sellEntityUsers = UserModel.objects.select_related('entity').filter(
          Q(entity=tx.sellEntity)
          & (Q(canApproveAll=True) | Q(canApproveQpay=True))
          ).values('personname','email','entity__entityname')
        # valuesは辞書型、value_listはタプルで戻る
        # （ご参考）https://se-memorandum.com/django-values-values_list/

        for sellUser in sellEntityUsers:

          context1 = {
            'token': dumps(tx.pk), # tx.pkを維持する必要ないので不要か
            'tx': tx,
            'sendbackReason': reason,
            'sendbackMessage': message,
            'afterLogin': 'qpaySendback',
          }
          utils.sendEmail_common(
            'qpay/buyer/mail/sendbackToSeller', '', [sellUser['email']], context1)


        """ 260620 「canApproveAll=True」「canApproveQpay=True」のユーザーに
            差し戻したことをパートナーの権限者に共有する """
        buyEntityUsers = UserModel.objects.select_related('entity').filter(
          Q(entity=tx.buyEntity) & (Q(canApproveAll=True) | Q(canApproveQpay=True))).values('personname','email','entity__entityname')
        # valuesは辞書型、value_listはタプルで戻る
        # （ご参考）https://se-memorandum.com/django-values-values_list/

        for buyUser in buyEntityUsers:

          context2 = {
            'tx': tx,
            'sendbackReason': reason,
            'sendbackMessage': message,
          }
          utils.sendEmail_common(
            'qpay/buyer/mail/sendbackShareWithQ', '', [buyUser['email']], context2)

        messages.add_message(self.request,
          messages.SUCCESS, "差戻の処理が完了しました。") 

        context = { 'step_process': 3, 'tx': tx, }
        return TemplateResponse(request, "qpay/buyer/txApproveDetail.html", context)

      else:

        context = {
          'step_process': 2,
          'tx': tx,
          'form': form, }
        return TemplateResponse(request, 'qpay/buyer/txApproveDetail.html', context)


    elif actionBtn.find('ToRejectQpay') >= 0:

      print(f'after ToRejectQpay in post of TxApproceDetailView_buyer')

      # 否認された場合の処理（処理状況の更新、受注者への連絡等）を行う
      tx.txStatus = -3
      tx.txStatus_char = "ゲスト申請否認・パートナー否認済"
      tx.rejected_at = timezone.now()

      tx.buyUser = buyUser
      tx.buyUser_personname = buyUser.personname

      tx.save()

      context = {'step_process': 1, 'tx': tx,}
      return TemplateResponse(request, "qpay/buyer/txApproveDetail.html", context)

    print(f'pass3 other')
    
    return HttpResponseBadRequest()


# 発注者が申請状況を確認するためのView（一覧表から個別データのボタンを押した後）  
class TxListDetailView_seller(generic.UpdateView):

  model = QpayTx
  template_name = "qpay/seller/txListDetail.html"

  def get(self, request, *args, **kwargs):

    tx = QpayTx.objects.get(pk=self.kwargs['tx_id'])
    le = LegalEntity.objects.get(entityname=tx.buyEntityname)

    try:
      page_number = int(self.kwargs['page_number'])
      print(f'page_number={page_number} in TxListDetailV, get')
    except:
      page_number = 1

    print(f'page_number={page_number} def get in TxListDetailView_seller')
    return TemplateResponse(request, "qpay/seller/txListDetail.html", { "tx": tx, 'page_number': page_number }) 

  def post(self, request, *args, **kwargs):
    tx =QpayTx.objects.get(pk=self.kwargs['tx_id'])
    return TemplateResponse(request, "qpay/seller/txListDetail.html",{ "tx":tx })

  def get_success_url(self):
    return reverse_lazy('qpay:txList_seller')


class TxListView_admin(LoginRequiredMixin, generic.UpdateView):

  login_url = '/accounts/login_admin/'
  model = QpayTx
  template_name = "qpay/admin/txList.html"
  # context_object_name = 'qpaytxs'

  paginate_by = 5 # 5で仮置き

  def get(self, request, *args, **kwargs):

    searchInput = self.request.GET.get('searchInput', None)
    print(f'searchInput={searchInput}')
    if searchInput != None and searchInput != '':
      searchInput = searchInput.strip()
      listCnt = len(searchInput.split())

    if searchInput is None or searchInput == '':
      object_list = QpayTx.objects.all().order_by('-created_at')

    elif listCnt == 1:

      object_list = QpayTx.objects.filter(
        Q(sellEntityname__icontains=searchInput.split()[0]) | Q(buyEntityname__icontains=searchInput.split()[0])
        ).order_by('-created_at')

    elif listCnt >= 2:
      object_list = QpayTx.objects.filter(
        (Q(sellEntityname__icontains=searchInput.split()[0]) & Q(sellEntityname__icontains=searchInput.split()[0]))
        | (Q(buyEntityname__icontains=searchInput.split()[1]) & Q(buyEntityname__icontains=searchInput.split()[1]))
        ).order_by('-created_at')

    paginator = Paginator(object_list, self.paginate_by)
    page_obj = None # データが存在しない場合の対応
    if object_list.exists():
      paginator = Paginator(object_list, self.paginate_by)

      # URLからページネーション経由でページ番号を取得する場合
      page_number = self.request.GET.get('page_number', None)
      if page_number is None:
        # 自分でviewを呼ぶときにページ番号を指定する場合  
        page_number = self.kwargs.get('page_number', 1)
        print(f'pass1 page_number={page_number}')

      page_obj = paginator.page(page_number)

    context = {
      'searchInput': searchInput,
      'object_list': object_list,
      'page_obj': page_obj,
    }
    return render(request, 'qpay/admin/txList.html', context)
  

# 発注者が申請状況を確認するためのView（一覧表から個別データのボタンを押した後）  
class TxListDetailView_admin(generic.UpdateView):

  model = QpayTx
  template_name = "qpay/admin/txListDetail.html"

  def get(self, request, *args, **kwargs):

    tx = QpayTx.objects.get(pk=self.kwargs['tx_id'])
    le = LegalEntity.objects.get(entityname=tx.buyEntityname)

    try:
      page_number = int(self.kwargs['page_number'])
      print(f'page_number={page_number} in TxListDetailView_admin, get')
    except:
      page_number = 1

    print(f'page_number={page_number} def get in TxListDetailView_admin')
    return TemplateResponse(request, "qpay/admin/txListDetail.html", { "tx": tx, 'page_number': page_number }) 

  def post(self, request, *args, **kwargs):
    tx =QpayTx.objects.get(pk=self.kwargs['tx_id'])
    return TemplateResponse(request, "qpay/admin/txListDetail.html",{ "tx":tx })

  def get_success_url(self):
    return reverse_lazy('qpay:txList_admin')
  

# 発注者が申請状況を確認するためのView   
class TxInboxView_admin(generic.UpdateView):

  model = QpayTx
  template_name = "qpay/admin/txInbox.html"
  paginate_by = 5 # 5で仮置き

  def get(self, request, *args, **kwargs):

    # パートナー承認が済み、Qneeが振込を行うデータ
    object_list = QpayTx.objects.select_related('sellEntity', 'sendbackInfo_admin').filter(
      Q(txStatus=3) | Q(txStatus=4)).order_by('-requested_at')
    
    # 確認用
    cnt = QpayTx.objects.select_related('sellEntity').filter(
      Q(txStatus=3) | Q(txStatus=4)).order_by('-requested_at').count()

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
class TxInboxDetailPreView_admin(LoginRequiredMixin, generic.TemplateView):

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


""" 発注者が前払いの承認するためのView（一覧又はメール内URLから遷移）"""
""" 承認時、パートナーの月集計の支払情報（ClearingInfo）を紐づけする """

class TxInboxDetailView_admin(LoginRequiredMixin, generic.UpdateView):

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
        "qpay/admin/txInboxDetail.html", {'step_process': 1, 'tx': tx, 'ba': bankAccount,}) 

    else:
      messages.add_message(request, messages.WARNING, "ゲストの受取口座が未設定です。「口座設定依頼」をお願いします。") 
     
      return TemplateResponse(request,
        "qpay/admin/txInboxDetail.html",  {'step_process': 1, 'tx': tx }) 


  def post(self, request, *args, **kwargs):

    tx =QpayTx.objects.select_related('buyEntity').get(pk=self.kwargs['tx_id'])

    # 口座設定がある場合とない場合に分けて処理をする
    ba = None
    if BankAccount.objects.filter(entity=tx.sellEntity).exists():
        ba = BankAccount.objects.get(entity=tx.sellEntity).exists()

    actionBtn = self.request.POST.get('actionBtn', None) 
    if actionBtn.find('ToTransferMoney') >= 0:

      print("「振込処理する」が押下された post in TxInboxDetailView")

      if ba is not None:

        tx.txStatus = 5
        tx.txStatus_char = "Qnee前払済"
        tx.advanced_at = timezone.now()

        # Qnee支払後に差戻し情報への参照をリセット
        tx.sendbackInfo_admin = None
        tx.sendbackInfo_buyer = None

        advancedTerm_YYYYMM = timezone.now().strftime('%Y%m')

        clrdInfo, created = ClearingInfo.objects.get_or_create(
          buyEntity=tx.buyEntity, advancedTerm_YYYYMM=advancedTerm_YYYYMM)
      
        if not created:
          amount_toBeCleared = QpayTx.objects.filter(
            buyEntity=tx.buyEntity, advancedTerm_YYYYMM=advancedTerm_YYYYMM).aggregate(sum('requested_amount'))
        
          clrdInfo.amount_toBeCleared = amount_toBeCleared

        clrdInfo.updated_at = timezone.now()
        tx.ClearingInfo = clrdInfo

        tx.save(); clrdInfo.save()


        ## buyer承諾後に、sellerに承諾したことをメールで伝える

        """ 251103 「canApproveAll=True」「canApproveQpay=True」のユーザーに
            承認されたことを伝える """
        sellEntityUsers = UserModel.objects.select_related('entity').filter(
          Q(entity=tx.sellEntity)
          & (Q(canApproveAll=True) | Q(canApproveQpay=True))).values('personname','email','entity__entityname')
        # valuesは辞書型、value_listはタプルで戻る
        # （ご参考）https://se-memorandum.com/django-values-values_list/

        # 口座設定がある場合とない場合に分けて処理をする
        if ba is not None:

          for sellUser in sellEntityUsers:

            context1 = {
              'tx': tx,
              'ba': ba,
              'token': dumps(tx.pk),
              'sellUser': sellUser, }
            utils.sendEmail_common('qpay/admin/mail/adminPayed', '', [sellUser.email], context1)
    
          return TemplateResponse(request,
            "qpay/admin/txInboxDetail.html", {'step_process': 1,  'tx': tx, })
          #return HttpResponseRedirect(self.get_success_url())
      
      else:

        messages.add_message(request, messages.WARNING,
          '口座未設定のため振込ができません。「設定依頼」のボタンを押下してください。')

        return TemplateResponse(request,
          "qpay/admin/txInboxDetail.html", {'step_process': 1,  'tx': tx, })


    elif actionBtn.find('ToRejectTransfer') >= 0:

      # 振込処理を謝絶の場合の処理
      tx.txStatus = -5
      tx.txStatus_char = "Qnee前払謝絶"
      tx.sendbackInfo_admin = None
      tx.sendbackInfo_buyer = None 
      tx.rejected_at = timezone.now()
      tx.save()

      context = {
        'step_process': 1, 
        'tx': tx,
        'ba': ba, }  
      return TemplateResponse(request, "qpay/admin/txInboxDetail.html", context)


    # ゲストが口座未設定の場合に依頼のメールをする
    elif actionBtn.find('ToRequestAcctSet') >= 0:

      sellEntityUsers = UserModel.objects.filter(
        Q(entity=tx.sellEntity) & (Q(canApproveAll=True) | Q(canApproveQpay=True)))

      for sellUser in sellEntityUsers:
        context1 = {
          'tx': tx,
          'token': dumps(tx.pk),
          'sellUser': sellUser,
          'afterLogin': 'bankAccountSet',}
      utils.sendEmail_common('qpay/admin/mail/bankAccountUnset', '', [sellUser.email], context1)
  
      messages.add_message(request, messages.SUCCESS,
        'ゲストユーザーに口座設定の依頼メールを送信しました。')

      return TemplateResponse(request,
        "qpay/admin/txInboxDetail.html",  {'step_process': 1, 'tx': tx, 'ba': ba, })


    ## ★★ 260619 工事開始
    ## ToSendBack1で差戻理由を入力、ToSendBack2で差戻実行

    if actionBtn.find('ToSendbackQpay1') >= 0:

      print(f'pass ToSendbackQpay1')
      context = {
        'step_process': 2,
        'tx': tx,
        'form': SendbackInfoForm_qpay(), }
      return TemplateResponse(request, 'qpay/admin/txInboxDetail.html', context)


    if actionBtn.find('ToSendbackQpay2') >= 0:

      # 確認用
      radioValue = self.request.POST.get('reason_radio')
      print(f'radioValue={radioValue}')
      
      form = SendbackInfoForm_qpay(self.request.POST, radioValue)

      if form.is_valid(): 

        print(f'pass1 after if form.is_valid==True in TxInboxDetailView_admin')

        selectedValue = form.cleaned_data.get('reason_radio')
        reason = dict(form.fields['reason_radio'].choices).get(selectedValue)
        message = form.cleaned_data['message']

        if radioValue == 'radio4':
          print(f'pass2 after if form.is_valid==True in TxInboxDetailView_admin')
          reason = form.cleaned_data['reason_text']

        tx.txStatus = 4
        tx.txStatus_char = 'パートナー承認差戻・Qnee差戻済'

        tx.approved_at = None
        tx.approved_amount = None

        sb = SendbackInfo.objects.create(
         qpaytx=tx, type1_frWho=3,
         reason=reason, message=message,
         created_at=timezone.now())

        tx.sendbackInfo_admin = sb

        tx.save(); sb.save()

        buyEntityUsers = UserModel.objects.filter(Q(entity=tx.buyEntity)
          & (Q(canApproveAll=True) | Q(canApproveQpay=True)))

        context = {
          'tx': tx,
          'token': dumps(tx.id),
          'afterLogin': 'qpaySendback',
          'sendbackReason': reason,
          'sendbackMessage': message,}

        for eachUser in buyEntityUsers:
          # 差戻されたことを通知する
        
          context['buyUser'] = eachUser
          context['token'] = dumps(tx.id)

          utils.sendEmail_common(
            'qpay/admin/mail/qpaySendback', '', [eachUser.email], context)

        messages.add_message(self.request,
          messages.SUCCESS, tx.buyEntityname + "への差戻の処理が完了しました。") 

        context = {
          'step_process': 3,
          'tx': tx,
          'form': form, }
        return TemplateResponse(request, 'qpay/admin/txInboxDetail.html', context)

      else:
        print(f'pass2 after if form.is_valid==False in TxInboxDetailVeiw_admin')
        context = {
          'step_process': 2,
          'tx': tx,
          'form': form, }
        return TemplateResponse(request, 'qpay/admin/txInboxDetail.html', context)

    return HttpResponseBadRequest()


# ★★　開発開始 20260624 パートナーの支払状況を更新するクラス


class ClearingListView_buyer(LoginRequiredMixin, generic.UpdateView):

  login_url = '/accounts/login_buyer/'
  model = QpayTx
  #template_name = "qpay/admin/txInboxDetail.html"

  def get(self, request, *args, **kwargs):

    # ★★　全てのbuyerに対して処理する
    tx = QpayTx.objects.get(pk=self.kwargs['tx_id'])
    buyEntity = LegalEntity.objects.get(pk=tx.buyEntity_id)
    sellEntity = LegalEntity.objects.get(pk=tx.sellEntity_id)

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

    actionBtn = self.request.POST.get('actionBtn', None) 
    if actionBtn.find('') >= 0:

      today = datetime.date.today()
      after1M = today + relativedelta(months=1)
      after2M = today + relativedelta(months=2)
      after3M = today + relativedelta(months=3)

      lastDay_thisMonth = calendar.monthrange(today.year, today.month)[1]
      lastDay_after1M = calendar.monthrange(after1M.year, after1M.month)[1]
      lastDay_after2M = calendar.monthrange(after2M.year, after2M.month)[1]
      lastDay_after3M = calendar.monthrange(after3M.year, after3M.month)[1]

      return TemplateResponse(request,
        "qpay/admin/txInboxDetail.html", { 'tx': tx, })
      #return HttpResponseRedirect(self.get_success_url())

    elif actionBtn.find('RejectRemittance') >= 0:

      context = {
        'tx': tx,
      }  
      return TemplateResponse(request, "qpay/admin/txInboxDetail.html", context)


    if actionBtn.find('ToSendback1') >= 0:
      
      
      context = {
        'step_process': 2,
        'SendbackInfoForm': SendbackInfoForm_qpay(), }
      return TemplateResponse(request, 'qpay/admin/corpInfoUpdate.html', context)

    return HttpResponseBadRequest()
  


class utils:
    
  def sendEmail_common(path, from_email, addList, context=None):

    if context == None: context ={}
    context['protocol'] = settings.PROTOCOL
    context['domain'] = settings.DOMAIN

    subject = render_to_string(path + '_subject.txt', context)
    message = render_to_string(path + '_message.txt', context)

    # .email_user(subject, message)
    if from_email is None or from_email == '':
      from_email = settings.DEFAULT_FROM_EMAIL

    recipient_list = addList
    #bcc =  ["toritoritorina@gmail.com"]  # BCCリスト
    email = EmailMessage(subject, message, from_email, recipient_list)
    email.send()

    return True