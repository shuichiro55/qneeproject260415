from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth import get_user_model
from django.contrib.auth.views import LoginView, LogoutView
from .models import LegalEntity, CustomUser, BankAccount

from django.template.response import TemplateResponse
from django.urls import reverse, reverse_lazy
from django.shortcuts import redirect
from django.conf import settings

from django.views import generic
from .form import \
  MyLoginForm, UserCreateForm, \
  EntityCreateForm, EntityConfirmForm, \
  MyPageForm_seller, MyPageForm_buyer, \
  ContactForm, BankAccountForm, InfoEditForm_seller

from qpay.models import QpayTx
from qpay.form import TxCreateForm, TxListForm_buyer_approve

from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.core.signing import dumps, loads, BadSignature, SignatureExpired
from django.http import HttpResponseBadRequest, HttpResponseRedirect, HttpResponseNotAllowed

from django.shortcuts import render
from django.core.mail import send_mail

from django.contrib import messages
from django.core.mail import EmailMessage

from django.test import TestCase
from django.core.exceptions import ValidationError
from django.core.exceptions import PermissionDenied

from datetime import date
from dateutil.relativedelta import relativedelta
from django.db.models import Sum

import re
from zengin_code import Bank

usermodel = get_user_model()  #get_user_model は、settings.py で AUTH_USER_MODEL に指定されているモデルを取得する関数

# MyLoginView_sellerでログインした場合に通る想定
# MyLoginView_buyerでログインしたListViewに遷移される
def MyLoginRedirect(request):
  print(f'request.user={request.user} in MyLoginRedirect') #これは表示されない
  print(f'ここ通っている in MyLoginRedirect')               #これは表示されない

  #http_method_names = ['get']
  #email = request.user.username

  #return reverse('accounts:mypage_seller', kwargs={'user_id':request.user.id})  
  return HttpResponseRedirect(reverse('accounts:mypage_seller'))
  #return HttpResponseRedirect(reverse('accounts:login_seller'))

#class MyLoginRedirect(generic.View):
#  #http_method_names = ['get']
#
#  def get(self, request, *args, **kwargs):
#    print(f'ここ通る？ def get in MyLoginRedirect')
#    return HttpResponseRedirect(reverse('accounts:mypage', kwargs={'user_id': request.user.id}))

class MyLoginView_buyer(LoginView):
  #redirect_authenticated_user=True,  "Trueの場合、ログイン済みユーザーはトップページ等にリダイレクト
  model = CustomUser
  form_class = MyLoginForm
  template_name='accounts/login_buyer.html'

  def get_success_url(self):
    print(f'通過1 get_success_url in MyLoginView_buyer')
    try:
      ## tx_idをtokenに変えた方がよいか 24/07/20
      token =self.kwargs['token']
      return reverse_lazy('qpay:txdetail_buyer_approve_before', kwargs={'token': token})
    except:
      print(f'通過2 get_success_url in MyLoginView_buyer')
      return reverse_lazy('accounts:mypage_buyer')


class MyLoginView_seller(LoginView):

  model = CustomUser
  form_class = MyLoginForm
  template_name = 'accounts/login_seller.html'
  #http_method_names = ['get']

  #def get_object(self, queryset=None):
  #  obj = super().get_object(queryset)
  #  return obj

  def get_success_url(self):

    print(f'通過1 get_success_url in MyLoginView_seller')
    try:
      ## tx_idをtokenに変えた方がよいか 24/07/20
      token =self.kwargs['token']
      return reverse_lazy('accounts:bankaccount_create_before', kwargs={'token': token})
    except:
      print(f'通過2 get_success_url in MyLoginView_seller')
      return reverse_lazy('accounts:mypage_seller')
  
  #def get_context_data(self, **kwargs):  #テンプレートに渡すcontextを取得する
  #  context = super().get_context_data(**kwargs)
  #  user = self.get_object()
  #  context['user'] = usermodel.objects.get(id=user.id)   #user_create.htmlで「user」でユーザーインスタンスをを扱える
  #  return context
  

class MyLogoutView(LogoutView):
    """ログアウトページ"""
    template_name = 'qpay/top.html'

# ユーザーを作成し、メールアドレス・パスワードを登録（発注者側）
class UserCreateView_buyer(generic.CreateView):
  model = CustomUser
  template_name = 'accounts/user_create.html'
  form_class = UserCreateForm

  # CreateView（親クラス）で自動バリデーションが通ったときに実行される
  # 発注者のフラグ立て、ユーザーインスタンス組成、本登録用メールの発行を行う
  def form_valid(self, form):

    user = form.save(commit=False)
    user.is_active = False  #仮登録と本登録の切り替えフラグ（退会後はFalse）
    user.type1 = 1          #発注者として登録 24/04/27
    user.type2 = self.request.POST['type2']
    user.save()
    
    print(f'ここまで来てる1 email={user.email} type2={user.type2}（form_valid in class UserCreateView_buyer）')
    #アクティベーションURLの送付
    ### あとでsend_mailに切り替える？
    current_site = get_current_site(self.request)
    domain = current_site.domain
    context = {
      'protocol': self.request.scheme,
      'domain': domain,
      'token': dumps(user.pk),
      'user': user,
    }

    subject = render_to_string('accounts/mail/subject.txt', context)
    message = render_to_string('accounts/mail/message.txt', context)

    print(f'メールアドレス：{user.email}')
    user.email_user(subject, message)
        
    return redirect('accounts:user_create_done')

  def form_invalid(self, form):

    print(f'ここ来てる2（form_invalid in class UserCreateVier_buyer）')
    print(form.errors)
    form.instance.user = self.request.user
    return super().form_invalid(form)


# ユーザーを作成し、メールアドレス・パスワードを登録（受注者側）
class UserCreateView_seller(generic.CreateView):
  model = CustomUser
  template_name = 'accounts/user_create.html'
  form_class = UserCreateForm

  # CreateView（親クラス）で自動バリデーションが通ったときに実行される
  # 発注者のフラグ立て、ユーザーインスタンス組成、本登録用メールの発行を行う
  def form_valid(self, form):

    user = form.save(commit=False)
    user.is_active = False
    user.type1 = 2          #受注者として登録 24/04/27
    user.type2 = self.request.POST['type2']
    user.save()
    print(f'ここまで来てる1 email={user.email} type2={user.type2}（form_valid in class UserCreateView_seller）')

    #アクティベーションURLの送付
    ### あとでsend_mailに切り替える？
    current_site = get_current_site(self.request)
    domain = current_site.domain
    context = {
      'protocol': self.request.scheme,
      'domain': domain,
      'token': dumps(user.pk),
      'user': user,
    }

    subject = render_to_string('accounts/mail/subject.txt', context)
    message = render_to_string('accounts/mail/message.txt', context)

    print(f'メールアドレス：{user.email}')
    user.email_user(subject, message)
     
    return redirect('accounts:user_create_done')

  def form_invalid(self, form):

    print(f'ここ来てる2（form_invalid in class UserCreateView_seller）')
    print(form.errors)
    #form.instance.user = self.request.user
    return super().form_invalid(form)


"""ユーザー仮登録が完了し、メール送付したと伝えるテンプレート"""
class UserCreateDone(generic.TemplateView):
  template_name = 'accounts/user_create_done.html'

"""24/04/05 メールで受領したURLがクリックされると本登録画面を表示"""
class UserCreateComplete(generic.TemplateView):

  template_name = 'accounts/user_create_complete.html'
  timeout_seconds = getattr(settings,  'ACTIVATION_TIMEOUT_SECONDS', 60*60*24)

  #（ビューにおいて）GETリクエストを受け取ったときに呼び出される（実践Django P121）
  #具体的には、受注者に送られたメールのURLをクリックされた時点で呼ばれる
  def get(self, request, **kwargs):  #selfはメソッドを呼んだインスタンス自体
  
    #tokenが但しければ本登録
    token = kwargs.get('token')  #kwargsはdict型
    try:
      user_pk = loads(token, max_age=self.timeout_seconds)

    #期限切れ
    except SignatureExpired:
      return HttpResponseBadRequest()

    #tokenが間違っている
    except BadSignature:
      return HttpResponseBadRequest()

    else:
      try:
        user = usermodel.objects.get(pk=user_pk)
      except usermodel.DoesNotExist:
        return HttpResponseBadRequest()

      else:
        if not user.is_active:
          user.is_active = True
          user.save()

          print(f'ここまで来てる2 email={user.email} type2={user.type2}（get in class UserCreateComplete）')

          # この下の２行はいらないでしょ 24/06/01
          context = super().get_context_data(**kwargs)
          context['user'] = user
                    
          print(f'ここまで来てる3 email={user.email} type2={user.type2}（get in class UserCreateComplete）')
          print(f'ここまで来てる3 request.user={request.user} type2={user.type2}（get in class UserCreateComplete）')
        
          return TemplateResponse(request, 'accounts/user_create_complete.html', {'user':user})  #ここでgetとするのは、おそらく親クラスでtemplate_nameを表示するように規定されている
                
    return HttpResponseBadRequest() 

  #def get_context_data(self, **kwargs):  #
  #    context = super().get_context_data(**kwargs)
  #    context['user'] = usermodel.objects.all()
  #    return context

"""24/04/05 メールで受領したURLがクリックされると本登録画面を表示"""
class EntityCreateView(generic.CreateView):

  model = LegalEntity
  form_class = EntityCreateForm
  template_name = 'accounts/entity_create.html'

#  def get(self, request, *args, **kwargs):
#
#    user = usermodel.objects.get(pk=self.kwargs['user_id']) 
#    form = self.form_class()
#    return render(request, 'accounts/entity_create.html', {'form': form})

  def get_context_data(self, **kwargs):  #テンプレートに渡すcontextを取得する
      context = super().get_context_data(**kwargs)
      context['user'] = usermodel.objects.get(pk=self.kwargs['user_id'])   #user_create.htmlで「user」でユーザーインスタンスをを扱える
      context['form'] = self.form_class()
      return context
  
  def post(self, request, *args, **kwargs):
    form = self.form_class(request.POST)
    user = usermodel.objects.get(pk=self.kwargs['user_id'])
    # print(f'ここまで来てる2（post in class EntityCreateView）')

    if form.is_valid():
    # 「.is_valid()」の後、フォームでのclean、clean_<field>が実行され、
    # form.cleaned_data[]にデータが入る

      #user.personname = form.cleaned_data['personname']
      next = self.request.POST.get('next', '') 
   
      if next == 'confirm':
        print(f'self.request.POST.get={next}（post==confirm after form.is_valid in class EntityCreateView）')
        print(f'user.email={user.email}（def post==confirm after form.is_valid in class EntityCreateView）')
        print(f'user.personname={user.personname}（def post==confirm after form.is_valid in class EntityCreateView）')
        print(f'user.entityname={user.entityname}（def post==confirm after form.is_valid in class EntityCreateView）')

        return render(self.request, 'accounts/entity_confirm.html', {'form':form, 'user':user})

      if next == 'back':
        print(f'ここまで来てる4（def post after form.is_valid in class EntityCreateView）')
        return render(self.request, 'accounts/entity_create.html', {'form':form, 'user':user})
  
      if next == 'create':
        entity = form.save(commit=False)
        entity.type1 = user.type1  # CustomUserとLegalEntityでいずれもtype1（発注者 or 受注者）、type2（個人 or 法人）を管理
        entity.type2 = user.type2  # CustomUserとLegalEntityでいずれもtype1（発注者 or 受注者）、type2（個人 or 法人）を管理
        entity.save()  # このタイミング保存するかは要検討、間違って修正すると既に登録されていると出てします。
        user.personname = entity.personname
        user.entity = entity

        # 個人（type2==1）の場合、entitynameに直接入力しない為、personnameを代入
        if user.type2 == 1: entity.entityname = entity.personname
        user.entityname = entity.entityname

        user.save()
        entity.save()

        print(f'self.request.POST.get={next}（post ==confirm after form.is_valid in class EntityCreateView）')
        print(f'user.personname={user.personname}（def post ==confirm after form.is_valid in class EntityCreateView）')
        print(f'user.entityname={user.entityname}（def post ==confirm after form.is_valid in class EntityCreateView）')
        print(f'email={user.email} type2={user.type2}（def post ==confirm after form.is_valid in class EntityCreateView）')
        print(f'request.user={request.user} type2={user.type2}（def post ==confirm after form.is_valid in class EntityCreateView）')
        print(f'request.user.get_username={request.user.get_username} type2={user.type2}（def post ==confirm after form.is_valid in class EntityCreateView）')

        if entity.type1 == 1: return HttpResponseRedirect(reverse('accounts:login_buyer'))
        if entity.type1 == 2: return HttpResponseRedirect(reverse('accounts:login_seller'))

    else:
      print(form.errors)
      print(f'ここまで来てる6 例外（post in class EntityCreateView）')
    return TemplateResponse(self.request, 'accounts/entity_create.html', {'form':form, 'user_id':user.id, 'user':user},)
    #contextを見直しが必要（基本的にはあまり通らないところだが）

  def form_valid(self, form):
    return super().form_valid(form)

  def get_success_url(self):
    user = usermodel.objects.get(pk=self.kwargs['user_id'])
    if user.is_authenticated:
      print(f'user.is_authenticated（get_success_url in class EntityCreateView）')
      return reverse('accounts:mypage_seller', kwargs={'user_id': user.id})
      #return reverse('accounts:mypage_seller')
    
    print(f'user.is_not_authenticated（get_success_url in class EntityCreateView）')

    if user.type1 == 1: return reverse('accounts:mylogin_buyer')
    if user.type2 == 2: return reverse('accounts:mylogin_seller')
    
    #return reverse('accounts:mypage_seller', kwargs={'user_id':user.id, })
    #return reverse('accounts:entity_confirm', kwargs={'user_id':user.id, 'entity_id':self.object.id})

  def form_invalid(self, form):
    print(f'ここまで来てる4（form_invalid in class EntityCreateView）')
    print(form.errors)
    #form.instance.user = self.request.user
    return super().form_invalid(form)

# 確認画面のViewは全面的に使わない方針（全部切り替えた時点で削除） 24/05/15
class EntityConfirmView(generic.CreateView):

  template_name = 'accounts/entity_confirm.html'
  form_class = EntityConfirmForm

  def get_context_data(self, **kwargs):  #テンプレートに渡すcontextを取得する
    form = EntityConfirmForm
    user = usermodel.objects.get(pk=self.kwargs['user_id'])
    return {'form': form, 'user':user, 'entity': user.entity}


"""ログインした後に呼ばれるビュー"""
class MyPageView_buyer(generic.DetailView):

  model = CustomUser
  template_name = "accounts/mypage_buyer.html"
  form_class = MyPageForm_buyer
  
  def get(self, request, *args, **kwargs):
    if request.method != "GET":
      return HttpResponseNotAllowed("GET")

    # 「URLパラメーターがある場合」と「ない場合（ログインから）」に分ける   
    try:
      self.object = usermodel.objects.get(pk=self.kwargs['user_id'])
    except:
      self.object = usermodel.objects.get(email=self.request.user) 
      print(f'request.user={request.user} def get in MyPageView_buyer')

    if self.object.type1 == 2:
      # 次のメッセージは確認できなかったので、要調整（トップページで出るようにする？）
      messages.add_message(request, messages.INFO, "発注者としてログインして下さい") 
      return HttpResponseRedirect(reverse('accounts:logout'))

    print(f'self.object.entityname={self.object.entityname} def get in MyPageView_buyer')

    entity = LegalEntity.objects.get(entityname=self.object.entityname)
    
    today = date.today()
    year = today.year; month = today.month; day = today.day

    first_of_month = date(year, month, 1)
    first_of_next_month = first_of_month + relativedelta(months=+1)
    first_of_month_after_next = first_of_month + relativedelta(months=+2)

    queryset = QpayTx.objects.filter(
      buyer_entity=entity,
      tx_status_int = 2,
      original_payment_date__gte = first_of_next_month,
      original_payment_date__lt = first_of_month_after_next)
    
    payment_date = first_of_next_month
    payment_count = queryset.count
    payment_amount = queryset.aggregate(Sum('approved_amount'))

    return TemplateResponse(
      request, "accounts/mypage_buyer.html",
      { 
        "user": self.object,
        "entity": entity,
        "payment_date": payment_date,
        "payment_count": payment_count,
        "payment_amount": payment_amount
      }
    ) 


  def post(self, request, *args, **kwargs):

    # 「URLパラメーターがある場合」と「ない場合（ログインから）」に分ける   
    try:
      self.object = usermodel.objects.get(pk=self.kwargs['user_id'])
    except:
      self.object = usermodel.objects.get(email=self.request.user) 
      print(f'request.user={request.user} def get in MyPageView_buyer')
    
    next = self.request.POST.get('next', '')
    if next == 'approve_qpay':
      form = TxListForm_buyer_approve()

      # Buyerにメールを送信するようにする

      return super().form_valid(form)      

    # 以下、各プログラムを加えていく
    #if next == '':
    #  form = TxCreateForm(request.POST)
    #  return super().form_valid(form)    
    
    #if next == '':
    #  form = TxCreateForm(request.POST)
    #  return super().form_valid(form)

  def get_success_url(self):
    return reverse('qpay:txlist_buyer_approve', kwargs={'user_id': self.object.id})


"""ログインした後に呼ばれるビュー"""
class MyPageView_seller(generic.DetailView):

  model = CustomUser
  template_name = "accounts/mypage_seller.html"
  form_class = MyPageForm_seller
  
  def get(self, request, *args, **kwargs):

    if request.method != "GET":
      return HttpResponseNotAllowed("GET")

    # 後者の場合は、request.userがAdminから切り替わっていない場合がある！
    # 前のページの情報は認識できないのか？  

    # 「URLパラメーターがある場合」と「ない場合（ログインから）」に分ける   
    try:
      self.object = usermodel.objects.get(pk=self.kwargs['user_id'])
    except:
      self.object = usermodel.objects.get(email=self.request.user) 
      print(f'request.user={request.user} def get in MyPageView_seller')

    if self.object.type1 == 1:
      # 次のメッセージは確認できなかったので、要調整（トップページで出るようにする？）
      messages.add_message(request, messages.INFO, "発注者としてログインして下さい") 
      return HttpResponseRedirect(reverse('accounts:logout'))

    print(f'self.object.entityname={self.object.entityname} def get in MyPageView_seller')
  
    entity = LegalEntity.objects.get(entityname=self.object.entityname)
    return TemplateResponse(request, "accounts/mypage_seller.html", { "user": self.object, "entity": entity }) 


  def post(self, request, *args, **kwargs):

    print(f'ここに来てる1（def post in class MyPageView_seller）')
    self.object = usermodel.objects.get(pk=self.kwargs['user_id'])
  
    next = self.request.POST.get('next', '')
    if next == 'apply_qpay':
      form = TxCreateForm(request.POST)

      # Buyerにメールを送信するようにする

      return super().form_valid(form)      

    #if next == 'history':
    #  form = TxCreateForm(request.POST)
    #  return super().form_valid(form)    

    # 以下、各プログラムを加えていく
    #if next == 'myinfo':
    #  form = TxCreateForm(request.POST)
    #  return super().form_valid(form)

  def get_success_url(self):
    return reverse('qpay:tx_create', kwargs={'user_id': self.object.id})


class ContactView(generic.FormView):

  template_name = 'accounts/contact.html'
  form_class = ContactForm
  success_url = reverse_lazy('accounts:contact')

  def form_valid(self, form):

    name = form.cleaned_data['name']
    email = form.cleaned_data['email']
    title = form.cleaned_data['title']
    message = form.cleaned_data['message']

    subject = 'お問い合わせ：{}'.format(title)
    message = \
      '送信者名：{0}\nメールアドレス：{1}\nタイトル：{2}\nメッセージ：{3}\n' \
      .format(name, email, title, message)
    
    from_email = 'shuichiro4@gmail.com'
    to_list = [email]

    message = EmailMessage(
      subject=subject,
      body=message,
      from_email=from_email,
      to=to_list
    )

    message.send()

    messages.success(
        self.request, 'お問い合わせは正常に送信されました。')
    
    return super().form_valid(form)

class BankAccountCreateView_before(generic.TemplateView):

  timeout_seconds = getattr(settings,  'ACTIVATION_TIMEOUT_SECONDS', 60*60*24)

  def get(self, request, *args, **kwargs):
      
    token = self.kwargs.get('token')  #kwargsはdict型
    print(f'token={token} def get in class BankAccountCreateView_before')
    
    try:
      tx_id = loads(token, max_age=self.timeout_seconds)
      tx = QpayTx.objects.get(pk=tx_id)
      ### ここは修正を要する
      le = LegalEntity.objects.get(email=tx.seller_email)
      print(f'tx_id={tx_id}, entity_id={le.id} def get in class BankAccountCreateView_before')

    except SignatureExpired:
      return HttpResponseBadRequest()

    #tokenが間違っている
    except BadSignature:
      return HttpResponseBadRequest()

    return HttpResponseRedirect(reverse('accounts:bankaccount_create', kwargs={'tx_id': tx_id, 'entity_id': le.id}))
  
  # POSTメソッドで口座登録する場合に備えて保持 24/07/21 POST関数がなくとも機能するか？
  def get_success_url(self):
    entity_id = self.kwargs['entity_id']  #kwargsはdict型
    return reverse_lazy('accounts:bankaccount_create', kwargs={'entity_id': entity_id})


class BankAccountCreateView(generic.CreateView):
  
  model = BankAccount
  form_class = BankAccountForm
  template_name='accounts/bankaccount_create.html'

  def get(self, request, *args, **kwargs):

    ## 銀行口座は、設定されてない場合（初回）と、既に設定されているときの２パターン必要
  
    init_dict = {
      'entity_id': kwargs.get('entity_id'),
    }
    form = self.form_class(initial=init_dict)

    return render(request, 'accounts/bankaccount_create.html', {'form': form})

  def post(self, request, *args, **kwargs):

    form = self.form_class(request.POST)

    # 検索ボタンが押されたときは、条件にマッチするデータ（辞書型）を返す
    search = self.request.POST.get('search', '')
  
    if search:
      print(f'ここ来る２')

      if search == 'search_bank':
      
        keyword_bank = self.request.POST['keyword_bank']
        print(f'ここ来る３ keyword_bank={keyword_bank}')
        match_bank_dict = BankAccount.BankSearch(keyword_bank)

      #if search == 'search_branch':
      #  match_branch_dict =  

        return  TemplateResponse(request, "accounts/bankaccount_create.html", {"form":form, "match_bank_dict": match_bank_dict})

      if search == 'search_branch':
      
        keyword_bank = self.request.POST['keyword_bank']
        print(f'ここ来る３ keyword_bank={keyword_bank}')
        match_bank_dict = BankAccount.BankSearch(keyword_bank)

        bank_code = self.request.POST['select_bank']
        keyword_branch = self.request.POST['keyword_branch']
        print(f'ここ来る４ self.request.POST[select_bank]={bank_code} keyword_branch={keyword_branch}')
        match_branch_dict = BankAccount.BranchSearch(bank_code, keyword_branch)

      #if search == 'search_branch':
      #  match_branch_dict =  

        return  TemplateResponse(request, "accounts/bankaccount_create.html", {"form":form, "match_bank_dict": match_bank_dict, "bank_code":bank_code, "match_branch_dict": match_branch_dict})

    next = self.request.POST.get('next', '')   # POST.getはミドルウェア機能 
    print(f'next={next}')


    form = self.form_class(request.POST)
    if form.is_valid():

      # 「.is_valid()」の後、フォームでのclean、clean_<field>が実行され、
      # form.cleaned_data[]にデータが入る

      if next == 'confirm':

        print(f'ここ通る？ after def post form.is_valid in BankAccountcreateView')

        #le = LegalEntity.objects.get(pk=self.kwargs['entity_id'])
        ba = BankAccount()
        ba.entity_id = self.request.POST['entity_id']   
        ba.bank_code = self.request.POST['select_bank']
        ba.branch_code = self.request.POST['select_branch']
        ba.account_number = self.request.POST['account_number']

        ba.bank_name = BankAccount.BankCodeSearch(ba.bank_code)
        ba.branch_name = BankAccount.BranchCodeSearch(ba.bank_code, ba.branch_code)

        init_dict = {
          'entity_id': ba.entity_id,
          'bank_code': ba.bank_code,
          'branch_code': ba.branch_code,
          'account_number': ba.account_number,
          'bank_name': ba.bank_name,
          'branch_name': ba.branch_name,
        }

        form = self.form_class(initial=init_dict)

        print(f'entity_id={ba.entity_id}')
        print(f'bank_code={ba.bank_code}')
        print(f'branch_code={ba.branch_code}')
        print(f'account_number={ba.account_number}')
        print(f'bank_name={ba.bank_name}')
        print(f'branch_name={ba.branch_name}')

        return render(request, "accounts/bankaccount_create_confirm.html", {"form": form, "entity_id": ba.entity_id })

      if next == 'register':
        ba = form.save(commit=True)
        le = LegalEntity.objects.get(pk=ba.entity_id)

        le.bank_account = ba.save()
        le.save()
        
        return super().form_valid(form)    

      if next == 'back':
        print(f'ここまで来てる（def post after form.is_valid in class BankAccountCreateView）')
        return render(self.request, 'accounts/bankaccount_create.html', {'form':form})
  
    return HttpResponseBadRequest()

  def form_invalid(self, form):

    print(f'ここ来てる2（form_invalid in class BankAccountCreateView）')
    print(form.errors)
    form.instance.user = self.request.user
    return super().form_invalid(form)

  def get_success_url(self):
    return reverse('accounts:mypage_seller')

  def get_context_data(self, **kwargs):
    context = super().get_context_data(**kwargs)
    context['bank_object_list'] = Bank.objects.all() 
    return context


class BankAccount:

  def BankSearch(keyword):
    
    match_bank_dict = {}
    
    for code in Bank.all:
      #bank = Bank[code]
      bank = Bank[code]

      if re.match(keyword, code) or\
        bank.name.find(keyword) >= 0 or\
        bank.kana.find(keyword) >= 0 or\
        bank.hira.find(keyword) >= 0 or\
        bank.roma.find(keyword) >= 0: 
        
        match_bank_dict.update({ code: bank.name })

        #銀行コードと銀行名を出力
        #print({
        #  "code": code,
        #  "name": bank.name,
        #})

    return match_bank_dict
  

  def BranchSearch(bank_code, keyword):
    
    match_branch_dict = {}
    
    branches = Bank[bank_code].branches
  
    for code in branches:
      #bank = Bank[code]
      branch = branches[code]

      if re.match(keyword, code) or\
        branch.name.find(keyword) >= 0 or\
        branch.kana.find(keyword) >= 0 or\
        branch.hira.find(keyword) >= 0 or\
        branch.roma.find(keyword) >= 0: 
        
        match_branch_dict.update({ code: branch.name })

        #銀行コードと銀行名を出力
        #print({
        #  "code": code,
        #  "name": branch.name,
        #})

    return match_branch_dict

  def BankCodeSearch(bank_code):
    
    for code in Bank.all:
      #bank = Bank[code]
      bank = Bank[code]

      if re.match(bank_code, code): return bank.name
      
    return '該当データなし'

  def BranchCodeSearch(bank_code, branch_code):
    
    branches = Bank[bank_code].branches
  
    for code in branches:
      #bank = Bank[code]
      branch = branches[code]

      if re.match(branch_code, code): return branch.name

    return '該当データなし'
  
"""メインメニューから呼ばれる登録情報変更ビュー"""
class InfoEditView_seller(generic.DetailView):

  model = CustomUser
  template_name = "accounts/info_edit_seller.html"
  form_class = InfoEditForm_seller
  
  def get(self, request, *args, **kwargs):

    if request.method != "GET":
      return HttpResponseNotAllowed("GET")

    # 後者の場合は、request.userがAdminから切り替わっていない場合がある！
    # 前のページの情報は認識できないのか？  

    # 「URLパラメーターがある場合」と「ない場合（ログインから）」に分ける   
    try:
      self.object = usermodel.objects.get(pk=self.kwargs['user_id'])
    except:
      self.object = usermodel.objects.get(email=self.request.user) 
      print(f'request.user={request.user} def get in InfoEditView_seller')

    if self.object.type1 == 1:
      # 次のメッセージは確認できなかったので、要調整（トップページで出るようにする？）
      messages.add_message(request, messages.INFO, "発注者としてログインして下さい") 
      return HttpResponseRedirect(reverse('accounts:logout'))

    print(f'self.object.entityname={self.object.entityname} def get in InfoEditView_seller')
  
    entity = LegalEntity.objects.get(entityname=self.object.entityname)
    return TemplateResponse(request, "accounts/info_edit_seller.html", { "user": self.object, "entity": entity }) 


  def post(self, request, *args, **kwargs):

    print(f'ここに来てる1（def post in class InfoEditView_seller）')
    self.object = LegalEntity.objects.get(pk=self.kwargs['entity_id'])
  
    next = self.request.POST.get('next', '')
    if next == 'edit_bankaccount':
      form = TxCreateForm(request.POST)

      # Buyerにメールを送信するようにする

      return super().form_valid(form)      

    #if next == 'history':
    #  form = TxCreateForm(request.POST)
    #  return super().form_valid(form)    

    # 以下、各プログラムを加えていく
    #if next == 'myinfo':
    #  form = TxCreateForm(request.POST)
    #  return super().form_valid(form)

  def get_success_url(self):
    return reverse('accounts:bankaccount_create', kwargs={'entity_id': self.object.id})
