from django.contrib.auth import logout, get_user_model
from django.contrib.auth.views import \
  LoginView, PasswordChangeView, PasswordChangeDoneView
from .models import CustomUser, BankAccount, UserEntityRelation
from .models import LegalEntity

from django.template.response import TemplateResponse
from django.urls import reverse, reverse_lazy

from django.shortcuts import redirect
from django.conf import settings

from django.views import generic
from .form import \
  MyLoginForm, UserCreateForm, UserAddForm_buyer, \
  EntitySetForm_buyer, EntityCreateForm_buyer, EntityCreateForm_seller, \
  MyPageForm_buyer, MyPageForm_seller, \
  ContactForm, BankAccountForm, InfoEditForm_seller, \
  AgreementConfirmForm_buyer, AgreementConfirmForm_seller, \
  MyPasswordChangeForm

from qpay.models import QpayTx
from qpay.form import TxCreateForm, TxListForm_buyer_approve

from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.core.signing import dumps, loads, BadSignature, SignatureExpired
from django.http import HttpResponseBadRequest, HttpResponseRedirect, HttpResponseNotAllowed

from django.shortcuts import render
from django.core.mail import send_mail # 使っている？

from django.contrib import messages
from django.core.mail import EmailMessage

from datetime import date
from dateutil.relativedelta import relativedelta
from django.db.models import Sum

import re
from django.utils import timezone
from zengin_code import Bank

import json

# 以下は2025/02/14時点で参照されていない
from django.test import TestCase
from django.core.exceptions import ValidationError
from django.core.exceptions import PermissionDenied
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LogoutView

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


class MyLoginView_buyer(LoginView):

  #redirect_authenticated_user=True,  "Trueの場合、ログイン済みユーザーはトップページ等にリダイレクト
  model = CustomUser
  form_class = MyLoginForm
  template_name='accounts/login_buyer.html'

  def get_context_data(self, **kwargs):
    context = super().get_context_data(**kwargs)
    return context

  def get_success_url(self):

    print(f'通過1 get_success_url in MyLoginView_buyer')

    try:
      token =self.kwargs['token']
      return reverse_lazy('qpay:txdetail_buyer_approve_before', kwargs={'token': token})

    except:
      self.object = usermodel.objects.get(email=self.request.user)

      if self.object.type1 != 1:
        if self.object.type1 == 1: type1_name = "パートナー"
        if self.object.type1 == 2: type1_name = "ゲスト"
        if self.object.type1 == 3: type1_name = "スタッフ"

        message = type1_name + "での登録です。" + type1_name + "でログインしてください。"
        messages.add_message(self.request, messages.INFO, message) 
        logout(self.request)
        print(f'self.object.type1={self.object.type1} in get_success_url in MyLoginView_buyer')

        if self.object.type1 == 1: reverse_lazy('accounts:login_buyer')
        if self.object.type1 == 2: reverse_lazy('accounts:login_seller')
        if self.object.type1 == 3: reverse_lazy('accounts:login_admin')

      return reverse_lazy('accounts:mypage_buyer')


class MyLoginView_seller(LoginView):

  #redirect_authenticated_user=True,  "Trueの場合、ログイン済みユーザーはトップページ等にリダイレクト
  model = CustomUser
  form_class = MyLoginForm
  template_name='accounts/login_seller.html'

  def get_context_data(self, **kwargs):
    context = super().get_context_data(**kwargs)
    return context

  def get_success_url(self):

    print(f'通過1 get_success_url in MyLoginView_seller')

    self.object = usermodel.objects.get(email=self.request.user)

    if self.object.type1 != 2:
      if self.object.type1 == 1: type1_name = "パートナー"
      if self.object.type1 == 2: type1_name = "ゲスト"
      if self.object.type1 == 3: type1_name = "スタッフ"

      message = type1_name + "での登録です。" + type1_name + "でログインしてください。"
      messages.add_message(self.request, messages.INFO, message) 
      logout(self.request)
      print(f'self.object.type1={self.object.type1} in get_success_url in MyLoginView_seller')

      if self.object.type1 == 1: reverse_lazy('accounts:login_buyer')
      if self.object.type1 == 2: reverse_lazy('accounts:login_seller')
      if self.object.type1 == 3: reverse_lazy('accounts:login_admin')

    return reverse_lazy('accounts:mypage_seller')


class MyLoginView_admin(LoginView):

  #redirect_authenticated_user=True,  "Trueの場合、ログイン済みユーザーはトップページ等にリダイレクト
  model = CustomUser
  form_class = MyLoginForm
  template_name='accounts/login_admin.html'

  def get_context_data(self, **kwargs):
    context = super().get_context_data(**kwargs)
    return context

  def get_success_url(self):

    print(f'通過1 get_success_url in MyLoginView_admin')

    self.object = usermodel.objects.get(email=self.request.user)

    if self.object.type1 != 3:
      if self.object.type1 == 1: type1_name = "パートナー"
      if self.object.type1 == 2: type1_name = "ゲスト"
      if self.object.type1 == 3: type1_name = "スタッフ"

      message = type1_name + "での登録です。" + type1_name + "でログインしてください。"
      messages.add_message(self.request, messages.INFO, message) 
      logout(self.request)
      print(f'self.object.type1={self.object.type1} in get_success_url in MyLoginView_admin')

      if self.object.type1 == 1: reverse_lazy('accounts:login_buyer')
      if self.object.type1 == 2: reverse_lazy('accounts:login_seller')
      if self.object.type1 == 3: reverse_lazy('accounts:login_admin')

    return reverse_lazy('accounts:mypage_admin')


def MyLogoutView_buyer(request, **kwargs):
  logout(request)
  return redirect('index_qconnect_buyer')

def MyLogoutView_seller(request, **kwargs):
  logout(request)
  return redirect('index_qconnect_seller')

def MyLogoutView_admin(request, **kwargs):
  logout(request)
  return redirect('index_qconnect_admin')


# 25/05/17に追加
class MyPasswordChangeView_buyer(PasswordChangeView):

  """パスワード変更ビュー"""
  form_class = MyPasswordChangeForm
  success_url = reverse_lazy('accounts:passwordChange2_buyer')
  template_name = 'accounts/passwordChange_buyer.html'

  def get_context_data(self, **kwargs):
    context = super().get_context_data(**kwargs)
    context['user_id'] = self.kwargs['user_id']
    user_id = context['user_id'] 
    print(f'user_id = {user_id} get_context_data in MyPasswordChange_buyer')
    return context


  def get_success_url(self):

    print(f'通過1 get_success_url in MyPasswordChange_buyer')
    
    self.object = usermodel.objects.get(email=self.request.user)

    if self.object.type1 != 1:
      if self.object.type1 == 1: type1_name = "パートナー"
      if self.object.type1 == 2: type1_name = "ゲスト"
      if self.object.type1 == 3: type1_name = "スタッフ"

      message = type1_name + "での登録です。" + type1_name + "でログインしてください。"
      messages.add_message(self.request, messages.INFO, message) 
      logout(self.request)
      print(f'self.object.type1={self.object.type1} in get_success_url in MyPasswordChangeView_buyer')

      return reverse_lazy('accounts:MyPasswordChange_buyer')

    return reverse_lazy('accounts:mypage_buyer')
  

class MyPasswordChangeView_seller(PasswordChangeView):

  """パスワード変更ビュー"""
  form_class = MyPasswordChangeForm
  success_url = reverse_lazy('accounts:passwordChange2_seller')
  template_name = 'accounts/passwordChange_seller.html'

  def get_context_data(self, **kwargs):
    context = super().get_context_data(**kwargs)
    context['user_id'] = self.kwargs['user_id']
    user_id = context['user_id'] 
    print(f'user_id = {user_id} get_context_data in MyPasswordChange_seller')
    return context


  def get_success_url(self):

    print(f'通過1 get_success_url in MyPasswordChange_seller')
    
    self.object = usermodel.objects.get(email=self.request.user)

    if self.object.type1 != 2:
      if self.object.type1 == 1: type1_name = "パートナー"
      if self.object.type1 == 2: type1_name = "ゲスト"
      if self.object.type1 == 3: type1_name = "スタッフ"

      message = type1_name + "での登録です。" + type1_name + "でログインしてください。"
      messages.add_message(self.request, messages.INFO, message) 
      logout(self.request)
      print(f'self.object.type1={self.object.type1} in get_success_url in MyPasswordChangeView_seller')

      return reverse_lazy('accounts:MyPasswordChange_seller')

    return reverse_lazy('accounts:mypage_seller')


class MyPasswordChangeView_admin(PasswordChangeView):

  """パスワード変更ビュー"""
  form_class = MyPasswordChangeForm
  success_url = reverse_lazy('accounts:passwordChange2_admin')
  template_name = 'accounts/passwordChange_admin.html'

  def get_context_data(self, **kwargs):
    context = super().get_context_data(**kwargs)
    context['user_id'] = self.kwargs['user_id']
    user_id = context['user_id'] 
    print(f'user_id = {user_id} get_context_data in MyPasswordChange_admin')
    return context


  def get_success_url(self):

    print(f'通過1 get_success_url in MyPasswordChange_admin')
    
    self.object = usermodel.objects.get(email=self.request.user)

    if self.object.type1 != 3:
      if self.object.type1 == 1: type1_name = "パートナー"
      if self.object.type1 == 2: type1_name = "ゲスト"
      if self.object.type1 == 3: type1_name = "スタッフ"

      message = type1_name + "での登録です。" + type1_name + "でログインしてください。"
      messages.add_message(self.request, messages.INFO, message) 
      logout(self.request)
      print(f'self.object.type1={self.object.type1} in get_success_url in MyPasswordChangeView_admin')

      return reverse_lazy('accounts:MyPasswordChange_admin')

    return reverse_lazy('accounts:mypage_admin')
  

# 25/05/17に追加
class MyPasswordChange2View_buyer(PasswordChangeDoneView):
    """パスワードを変更したことを表示"""
    template_name = 'accounts/passwordChange2_buyer.html'


class MyPasswordChange2View_seller(PasswordChangeDoneView):
    """パスワードを変更したことを表示"""
    template_name = 'accounts/passwordChange2_seller.html'


class MyPasswordChange2View_admin(PasswordChangeDoneView):
    """パスワードを変更したことを表示"""
    template_name = 'accounts/passwordChange2_admin.html'


class UserCreateView1_buyer(generic.CreateView):

  model = CustomUser
  template_name = 'accounts/userCreate1_buyer.html'
  form_class = UserCreateForm


  def get(self, request, **kwargs):  #selfはメソッドを呼んだインスタンス自体

    context = {
      'form' : self.form_class,
    }
    return TemplateResponse(request, 'accounts/userCreate1_buyer.html', context)  #ここでgetとするのは、おそらく親クラスでtemplate_nameを表示するように規定されている


  # CreateView（親クラス）で自動バリデーションが通ったときに実行される
  # ユーザーインスタンス生成・保存、type1,type2の登録、本登録用メールの発行を行う

  def post(self, request, **kwargs):  #selfはメソッドを呼んだインスタンス自体

    form = self.form_class(request.POST)

    if form.is_valid():

      user = form.save(commit=False)
      user.is_active = False

      user.type1 = 1  # パートナー：1、ゲスト：2、Qnee：3で登録 25/04/27

      user.save()
      print(f'ここまで来てる1 email={user.email} type2={user.type2} user.pk={user.pk} usr.passsword= {user.password}（def post if form.is_valid in class UserCreateView1_buyer）')

      ### あとでsend_mailに切り替えるか検討 2025/04/27
      current_site = get_current_site(self.request)
      domain = current_site.domain
      context = {
        'protocol': self.request.scheme,
        'domain': domain,
        'token': dumps(user.pk),
        'user': user,
      }

      subject = render_to_string('accounts/mail/buyUserTempRegister_subject.txt', context)
      message = render_to_string('accounts/mail/buyUserTempRegister_message.txt', context)

      print(context)
      print(f'メールアドレス：{user.email}')
      user.email_user(subject, message)
     
      return redirect('accounts:userCreate2_buyer')

    else:
  
      print(f'ここ来てる2（def post if form.is_valid=FALSE in class UserCreateView1_buyer）')
      print(form.errors)

      context = {
        'form' : form,
      }
      return render(request, 'accounts/userCreate1_buyer', context)
      #ここでgetとするのは、おそらく親クラスでtemplate_nameを表示するように規定されている

class UserAddView_buyer(generic.CreateView):

  model = CustomUser
  template_name = 'accounts/userAdd_buyer.html'
  form_class = UserAddForm_buyer

  def get(self, request, **kwargs):  #selfはメソッドを呼んだインスタンス自体
    
    try:
      # URLから<token>（暗号化されたuser_id）を取り出す（kwargsはdict型）
      token = kwargs.get('token')
      applyUser_pk = loads(token, max_age=self.timeout_seconds)
      applyUser = usermodel.objects.get(pk=applyUser_pk)
      print(f'token = {token}, applyUser_pk = {applyUser_pk} in def get of UserAdd_buyer')

    except usermodel.DoesNotExist:
      return HttpResponseBadRequest()

    # 期限切れ
    except SignatureExpired:
      # この段階でCustomUserインスタンスが生成されている。
      # 同じメールアドレスで登録できるように、オブジェクトを削除する。
      return HttpResponseBadRequest()

    # tokenが間違っている
    except BadSignature:
      return HttpResponseBadRequest()

    context = {
      'form': self.form_class,
      'applyUser': applyUser, 
    }

    return TemplateResponse(request, 'accounts/userAdd_buyer.html', context)
  
  def post(self, request, **kwargs):

    self.request.POST.get('next', '')

    if next == 'PermitSetComplete':
      form = self.form_class(request.POST)
      applyUser = form.save(commit=False)
      applyUser.is_active2 = True
      applyUser.save()

    return TemplateResponse(request, 'accounts/mypage_buyer.html')


class UserCreateView1_seller(generic.CreateView):

  model = CustomUser
  template_name = 'accounts/userCreate1_seller.html'
  form_class = UserCreateForm


  def get(self, request, **kwargs):  #selfはメソッドを呼んだインスタンス自体
  
    context = {
      'form' : self.form_class,
    }
    return TemplateResponse(request, 'accounts/userCreate1_seller.html', context)  #ここでgetとするのは、おそらく親クラスでtemplate_nameを表示するように規定されている


  # CreateView（親クラス）で自動バリデーションが通ったときに実行される
  # ユーザーインスタンス生成・保存、type1,type2の登録、本登録用メールの発行を行う

  def post(self, request, **kwargs):  #selfはメソッドを呼んだインスタンス自体

    form = self.form_class(request.POST)

    if form.is_valid():

      user = form.save(commit=False)
      user.is_active = False

      user.type1 = 2  # パートナー：1、ゲスト：2、Qnee：3で登録 25/04/27

      user.save()
      print(f'ここまで来てる1 email={user.email} type2={user.type2} user.pk={user.pk} usr.passsword= {user.password}（def post if form.is_valid in class UserCreateView1_seller）')

      ### あとでsend_mailに切り替えるか検討 2025/04/27
      current_site = get_current_site(self.request)
      domain = current_site.domain
      context = {
        'protocol': self.request.scheme,
        'domain': domain,
        'token': dumps(user.pk),
        'user': user,
      }

      subject = render_to_string('accounts/mail/sellUserTempRegister_subject.txt', context)
      message = render_to_string('accounts/mail/sellUserTempRegister_message.txt', context)

      print(context)
      print(f'メールアドレス：{user.email}')
      user.email_user(subject, message)
     
      return redirect('accounts:userCreate2_seller')

    else:
  
      print(f'ここ来てる2（def post if form.is_valid=FALSE in class UserCreateView1_seller）')
      print(form.errors)

      context = {
        'form' : form,
      }
      return render(request, 'accounts/userCreate1_seller.html', context)  #ここでgetとするのは、おそらく親クラスでtemplate_nameを表示するように規定されている


class UserCreateView1_admin(generic.CreateView):

  model = CustomUser
  template_name = 'accounts/userCreate1_admin.html'
  form_class = UserCreateForm

  def get(self, request, **kwargs):  #selfはメソッドを呼んだインスタンス自体

    context = {
      'form' : self.form_class,
    }
    return TemplateResponse(request, 'accounts/userCreate1_admin.html', context)  #ここでgetとするのは、おそらく親クラスでtemplate_nameを表示するように規定されている


  # CreateView（親クラス）で自動バリデーションが通ったときに実行される
  # ユーザーインスタンス生成・保存、type1,type2の登録、本登録用メールの発行を行う

  def post(self, request, **kwargs):  #selfはメソッドを呼んだインスタンス自体

    form = self.form_class(request.POST)

    if form.is_valid():

      user = form.save(commit=False)

      user.type1 = 3  # パートナー：1、ゲスト：2、Qnee：3で登録 25/04/27
      user.type2 = 1  # 個人として登録
      user.active = True  # adminの場合はここでアクティブ化
      user.save()

      print(f'ここまで来てる1 email={user.email} type2={user.type2} user.pk={user.pk} usr.passsword= {user.password}（def post if form.is_valid in class UserCreateView1_admin）')

      ### あとでsend_mailに切り替えるか検討 2025/04/27
      current_site = get_current_site(self.request)
      domain = current_site.domain
      context = {
        'protocol': self.request.scheme,
        'domain': domain,
        'token': dumps(user.pk),
        'user': user,
      }

      subject = render_to_string('accounts/mail/adminUserTempRegister_subject.txt', context)
      message = render_to_string('accounts/mail/adminUserTempRegister_message.txt', context)

      print(context)
      print(f'メールアドレス：{user.email}')
      user.email_user(subject, message)
     
      return redirect('accounts:userCreate2_admin')

    else:
  
      print(f'ここ来てる2（def post if form.is_valid=FALSE in class UserCreateView1_admin）')
      print(form.errors)

      context = {
        'form' : form,
      }
      return render(request, 'accounts/userCreate1_admin.html', context)  #ここでgetとするのは、おそらく親クラスでtemplate_nameを表示するように規定されている


"""ユーザー仮登録が完了し、メール送付したと伝えるテンプレート"""
class UserCreateView2_buyer(generic.TemplateView):
  template_name = 'accounts/userCreate2_buyer.html'

class UserCreateView2_seller(generic.TemplateView):
  template_name = 'accounts/userCreate2_seller.html'

class UserCreateView2_admin(generic.TemplateView):
  template_name = 'accounts/userCreate2_admin.html'


"""25/01/01 メールで受領したURLがクリックされると本登録画面を表示"""

class EntityCreateView_buyer(generic.CreateView):

  model = LegalEntity
  form_class = EntityCreateForm_buyer
  template_name = 'accounts/entityCreate_buyer.html'

  timeout_seconds = getattr(settings,  'ACTIVATION_TIMEOUT_SECONDS', 60*60*24)


  """（ビューにおいて）GETリクエストを受け取ったときに呼び出される（実践Django P121）"""
  """ 処理：ゲストに送られたメールのURLをクリックされた時点で呼ばれる """

  """ def getでは、メールから本登録に進む場合に呼ばれ、
      ①新規パートナー登録か、②既存パートナーにユーザー追加を選択するテンプレートを送る """

  def get(self, request, **kwargs):  #selfはメソッドを呼んだインスタンス自体
  
    try:
      ### 開発時だけのコード（時間制限なくレイアウトを整えられるように）25/06/08
      user = usermodel.objects.get(pk=self.kwargs['user_id'])
    except:

      try:
        # URLから<token>（暗号化されたuser_id）を取り出す（kwargsはdict型）
        token = kwargs.get('token')
        user_pk = loads(token, max_age=self.timeout_seconds)
        user = usermodel.objects.get(pk=user_pk)
        print(f'token = {token}, user_pk = {user_pk} in def get of EntitySetView_buyer')

      except usermodel.DoesNotExist:
        return HttpResponseBadRequest()

      # 期限切れ
      except SignatureExpired:
        # この段階でCustomUserインスタンスが生成されている。
        # 同じメールアドレスで登録できるように、オブジェクトを削除する。
        return HttpResponseBadRequest()

      # tokenが間違っている
      except BadSignature:
        return HttpResponseBadRequest()
    
    # 仮登録が完了し、メールからのリンクにより本登録を開始した時点
    if not user.is_active1:
      user.is_active1 = True
      user.save()

    ### ここからしたが工事中（25/06/08） ###
    ### dict_buyEntitynameのデータをselectに格納するようにする 

    dict_buyEntityname = dict((str(idx), f) for idx, f in enumerate(LegalEntity.objects.filter(type1=1).values_list('entityname', flat=True), 1))
    print(f'dict_buyEntityname={dict_buyEntityname} def get in EntitySetView_buyer')

    init_dict = {
      'personname': '',
      'email': user.email,
      'tel': "",
    }

    context = {
      'flag_step': 1,
      'user': user,
      'form': EntitySetForm_buyer(initial=init_dict),
      'temporal_buyEntityname': "",
      # コメント(25/06/08)：Selectボックスで未選択であることを示す。選択後はページ移動でデータ保持するために使う
      'dict_buyEntityname': dict_buyEntityname,
      'json_buyEntityname': json.dumps(dict_buyEntityname),
    }

    print(f'ここ来てる1 request.user={request.user} email={user.email} type2={user.type2}（get in class EntitySetView_buyer）')
        
    return TemplateResponse(request, 'accounts/entitySet_buyer.html', context)


  def post(self, request, *args, **kwargs):

    user = usermodel.objects.get(email=self.request.user) 
    next1 = self.request.POST.get('next1', '')
    next2 = self.request.POST.get('next2', '')


    """ 新規のパートナー登録をする処理 """

    if next1 == 'ToEntityCreate':

      # ★★★ Entityでは郵便番号、住所、代表者を登録するようにする 25/06/08 23:46

      context = {
        'user': user,
        'form': EntityCreateForm_buyer,
      }
      return render(self.request, 'accounts/entityCreate_buyer.html', context)

    # データ確認画面から入力画面に戻る時の処理 2025/02/14
    if next1 == 'BackToInput':

      print(f'ここ来てる4（in class EntityCreateView_buyer）')

      """
      dict_buyEntityname = dict((str(idx), f) for idx, f in enumerate(LegalEntity.objects.filter(type1=1).values_list('entityname', flat=True), 1))
      print(f'dict_buyEntityname={dict_buyEntityname} def get in EntitySetView_buyer')

      context = {
        'flag_step': 1,
        'form': self.form_class(request.POST),
        'temporal_buyEntityname': self.request.POST['temporal_buerEntityname'],
        # コメント(25/06/08)：Selectボックスで未選択であることを示す。選択後はページ移動でデータ保持するために使う
        'dict_buyEntityname': dict_buyEntityname,
      }
      return TemplateResponse(request, 'accounts/entity_set_buyer.html', context)
      """
      return render(self.request, 'accounts/entityCreate_buyer.html', {'form':form, 'user':user})

    if next1 == 'ToConfirm1':  
    
      if form.is_valid():
      # 「.is_valid()」の後、フォームでのclean、clean_<field>が実行され、
      # form.cleaned_data[]にデータが入る

        context = {
          'form': form,
          'user': user,
        }
        return render(self.request, 'accounts/entityConfirm_buyer.html', context)

      else: #バリデーションエラーの時に通る
        print(f'ここ来てる3（def post after if not form.is_valid in class EntityCreateView_buyer）')
        return TemplateResponse(self.request, 'accounts/entityCreate_buyer.html', {'form':form, 'user_id':user.id, 'user':user},)
    
    else: # next1 != "ToConfirm1"の場合（confirm画面からの処理を想定）

      form = self.form_class(request.POST)
        
      if next1 == 'Save': # 確認した内容をデータベースに登録

        entity = form.save(commit=False)
        entity.type1 = user.type1  # CustomUserとLegalEntityでいずれもtype1（発注者 or 受注者）、type2（個人 or 法人）を管理
        entity.type2 = user.type2  # CustomUserとLegalEntityでいずれもtype1（発注者 or 受注者）、type2（個人 or 法人）を管理

        count = LegalEntity.objects.filter(email=user.email).count()
        if count >= 1:
          messages.add_message(request, messages.INFO, '既に同じメールアドレスでの登録があります。')
       
        # 個人（type2==1）の場合、entitynameに直接入力しない為、personnameを代入
        if user.type2 == 1:
          #entity.email = user.email
          # 25/07/19 entity.personname ⇒ self.request.post['personname']に要修正
          entity.entityname = self.request.post['personname']

        entity.save()

        # 25/07/19 entity.personname ⇒ self.request.post['personname']に要修正
        user.personname = self.request.post['personname']
        #user.entityname = entity.entityname

        #user.entity = entity
        user.entities.add(entity)

        if not user.is_active2: user.is_active2 = True

        user.save()

        print(f'request.user.get_username={request.user.get_username} type2={user.type2}（def post ==confirm after form.is_valid in EntityCreateView_buyer）')
        print(f'entity.id = {entity.id}（post ==create after form.is_valid in EntityCreateView_buyer）')

        return render(self.request, 'accounts/agreement_confirm_buyer.html', {'user':user, 'entity':entity})
        # return HttpResponseRedirect(reverse('accounts:login_buyer'))
      

    """ 登録済みパートナーに追加する処理 """

    if next2 == 'ToConfirm2':  # 登録済みパートナーにユーザー追加

      form = EntitySetForm_buyer(request.POST)

      temporal_buyEntityname = self.request.POST.get('name_BuyerSelect', "")
      buyEntity = LegalEntity.objects.get(entityname=temporal_buyEntityname)
 
      print(f'temporal_buyEntityname={temporal_buyEntityname} form.personname={form.personname} (def post of EntityCreateView_buyer)')

      context = {
        'flag_step': 2,
        'form': form,     # personname, email, telの値が入っている
        'buyEntity': buyEntity,
        'temporal_buyEntityname': temporal_buyEntityname,
      }
      return render(self.request, 'accounts/entityCreate_buyer.html', context)

    if next2 == 'BackToInput':

      dict_buyEntityname = dict((str(idx), f) for idx, f in enumerate(LegalEntity.objects.filter(type1=1).values_list('entityname', flat=True), 1))
      print(f'dict_buyEntityname={dict_buyEntityname} def get in EntityCreateView_buyer')

      context = {
        'flag_step': 1,
        'form': EntitySetForm_buyer(request.POST),
        'temporal_buyEntityname': self.request.POST['temporal_buerEntityname'],
        # コメント(25/06/08)：Selectボックスで未選択であることを示す。選択後はページ移動でデータ保持するために使う
        'dict_buyEntityname': dict_buyEntityname,
        'json_buyEntityname': json.dumps(dict_buyEntityname),
      }
      return TemplateResponse(request, 'accounts/entitySet_buyer.html', context)


    if next2 == 'ToSave&Apply': # flag_stepが2の後（登録データ確認後）、データ保存＆パートナーに参加申請

      form = EntitySetForm_buyer(request.POST)
      temporal_buyEntityname = self.request.POST.get('temporal_buyEntityname', "")
      entity = LegalEntity.objects.get(entityname=temporal_buyEntityname)

      user.personname = form.personname
      user.entities.add(entity)
      user.save()

      UER = form.save(commit=False)
      UER.user = user
      UER.entity = entity  # ★★★ この「entity」は中身は入っている？ 25/07/19
      UER.entityname = temporal_buyEntityname
      UER.save()

      """ ★★★ 25/06/14追加（テストは未済み）  既に「is_buerUser_ApproveAll=True」の人がいるかで処理を分ける """

      approvers = usermodel.objects.filter(entities=entity.id, is_approver_buyer_all=True)
      #queryset_users = usermodel.objects.prefetch_related('entities').filter(entities=entity.id, is_buyUser_ApproveAll=True)

      # データ取得参考（https://noauto-nolife.com/post/django-foreignkey-related-name/）
    
      if approvers.first() is None: # 参加を承認するユーザーがいない場合（一人目のユーザーの場合）
        
        user.is_approver_buyer_all = True
        user.is_approver_buyer_add = True
        user.is_approver_buyer_qpay = True

        if not user.is_active2: user.is_active2 = True
        user.save()

        return render(self.request, 'accounts/mypage_buyer.html')

      else:   # 権限者に参加申請する

        current_site = get_current_site(self.request)
        domain = current_site.domain

        for approver in approvers:

          context = {
            'protocol': self.request.scheme,
            'domain': domain,
            'token': dumps(user.pk),
            'approver': approver,
          }
          subject = render_to_string('accounts/mail/buyerApplyAdd_subject.txt', context)
          message = render_to_string('accounts/mail/buyerApplyAdd_message.txt', context)

          from_email = 'shuichiro.tomihari.201604@gmail.com'
          recipient_list = [approver.email]
          #bcc =  ["toritoritorina@gmail.com"]  # BCCリスト
          email = EmailMessage(subject, message, from_email, recipient_list)
          email.send()
  
          messages.add_message(request, messages.SUCCESS, 'ユーザーの追加登録の申請を行いました.')
          print(f'pass1 approver.email={approver.email}（EntityCreateView_buyer, post, next==save1)')
    
        return redirect('logout_buyer')

    print(form.errors)
    print(f'ここまで来てる6 例外（post in class EntityCreateView_buyer）')

  def form_valid(self, form):
    return super().form_valid(form)
  
  def form_invalid(self, form):
    print(f'ここまで来てる4（form_invalid in class EntityCreateView_buyer）')
    print(form.errors)
    #form.instance.user = self.request.user
    return super().form_invalid(form)


"""25/01/01 メールで受領したURLがクリックされると本登録画面を表示"""
class EntityCreateView_seller(generic.CreateView):

  model = LegalEntity
  form_class = EntityCreateForm_seller
  template_name = 'accounts/entityCreate_seller.html'

  timeout_seconds = getattr(settings,  'ACTIVATION_TIMEOUT_SECONDS', 60*60*24)

  #（ビューにおいて）GETリクエストを受け取ったときに呼び出される（実践Django P121）
  # 具体的には、受注者に送られたメールのURLをクリックされた時点で呼ばれる
  def get(self, request, **kwargs):  #selfはメソッドを呼んだインスタンス自体
  
    try: # 開発時に使う（時間制限なく使えるように）24/01/02
      user = usermodel.objects.get(pk=self.kwargs['user_id'])

    except: # 通常ケース（メールからアクセスする場合）
      try:
        token = kwargs.get('token')
        # URLから<token>（暗号化されたuser_id）を取り出す（kwargsはdict型）

        user_pk = loads(token, max_age=self.timeout_seconds)
        user = usermodel.objects.get(pk=user_pk)
        print(f'token = {token} in def get of EntityCreateView_seller')
        print(f'user_pk = {user_pk} in def get of EntityCreateView_seller')

      except usermodel.DoesNotExist:
        return HttpResponseBadRequest()

      # 期限切れ
      except SignatureExpired:
        # この段階でCustomUserインスタンスが生成されている。
        # 同じメールアドレスで登録できるように、オブジェクトを削除する。
        return HttpResponseBadRequest()

      # tokenが間違っている
      except BadSignature:
        return HttpResponseBadRequest()
            
    if not user.is_active1:
      user.is_active1 = True
      user.save()

    context = {
      'user': user,
      'form': self.form_class,
    }

    print(f'ここ来てる1 email={user.email} type2={user.type2}（get in class EntityCreateView_seller）')
    print(f'ここ来てる1 request.user={request.user} type2={user.type2}（get in class EntityCreateView_seller）')
        
    return TemplateResponse(request, 'accounts/entityCreate_seller.html', context)  #ここでgetとするのは、おそらく親クラスでtemplate_nameを表示するように規定されている

  
  def post(self, request, *args, **kwargs):
     
    form = self.form_class(request.POST)
    next = self.request.POST.get('next', '') 

    if next == 'ToConfirm':  
    
      try: # 通常はここを通る
        user = usermodel.objects.get(pk=self.kwargs['user_id'])

      except:
        try:
          timeout_seconds = getattr(settings,  'ACTIVATION_TIMEOUT_SECONDS', 60*60*24)
          token = kwargs.get('token')  #kwargsはdict型

          user_pk = loads(token, max_age=timeout_seconds)
          user = usermodel.objects.get(pk=user_pk)

          print(f'token = {token} in def post of EntityCreateView_seller')
          print(f'user_pk = {user_pk} in def post of EntityCreateView_seller')
    
        # 期限切れ
        except SignatureExpired:
          # この段階でCustomUserインスタンスが生成されている。
          # 同じメールアドレスで登録できるように、オブジェクトを削除する。
          return HttpResponseBadRequest()

        # tokenが間違っている
        except BadSignature:
          return HttpResponseBadRequest()

        except usermodel.DoesNotExist:
          return HttpResponseBadRequest()

      if form.is_valid():
      # 「.is_valid()」の後、フォームでのclean、clean_<field>が実行され、
      # form.cleaned_data[]にデータが入る
        return render(self.request, 'accounts/entityConfirm_seller.html', {'form':form, 'user':user})

      else:
        return TemplateResponse(self.request, 'accounts/entityCreate_seller.html', {'form':form, 'user_id':user.id, 'user':user},)
        #contextを見直しが必要（基本的にはあまり通らないところだが）
    
    else:

      user = usermodel.objects.get(pk=self.kwargs['user_id'])
      form = self.form_class(request.POST)

      if next == 'back':
        print(f'ここまで来てる4（def post after 「try-except:」 in class EntityCreateView_seller）')
        return render(self.request, 'accounts/entityCreate_seller.html', {'form':form, 'user':user})
        
      if next == 'create': # 確認した内容をデータベースに登録

        entity = form.save(commit=False)
        entity.type1 = user.type1  # CustomUserとLegalEntityでいずれもtype1（発注者 or 受注者）、type2（個人 or 法人）を管理
        entity.type2 = user.type2  # CustomUserとLegalEntityでいずれもtype1（発注者 or 受注者）、type2（個人 or 法人）を管理
        entity.email = user.email

        count = LegalEntity.objects.filter(email=user.email).count()
        if count >= 1:
          messages.add_message(request, messages.INFO, '既に同じメールアドレスでの登録があります。')
       
        # 個人（type2==1）の場合、entitynameに直接入力しない為、personnameを代入
        if user.type2 == 1:
          entity.entityname = entity.personname

        entity.save()

        user.personname = entity.personname
        user.entityname = entity.entityname
        user.entity = entity
        user.save()
        
        print(f'self.request.POST.get={next}')
        print(f'user.entity={user.entity}')
        print(f'request.user.get_username={request.user.get_username} type2={user.type2}')
        print(f'user.id={user.id}  entity.id={entity.id} def post ==create after form.is_valid in class EntityCreateView_seller）')

        return render(self.request, 'accounts/agreement_confirm_seller.html', {'user':user, 'entity':entity})
        # return HttpResponseRedirect(reverse('accounts:login_seller'))

      print(form.errors)
      print(f'ここまで来てる6 例外（post in class EntityCreateView_seller）')

  def form_valid(self, form):
    return super().form_valid(form)

  def form_invalid(self, form):
    print(f'ここまで来てる4（form_invalid in class EntityCreateView_seller）')
    print(form.errors)
    #form.instance.user = self.request.user
    return super().form_invalid(form)


"""25/01/08 利用規約に同意するためのビュー"""
class AgreementConfirmView_buyer(generic.CreateView):

  model = LegalEntity
  form_class = AgreementConfirmForm_buyer
  template_name = 'accounts/agreement_confirm_buyer.html'

  ## このgetメソッドは開発時に利用するためのもの　24/01/08
  ## 通常時は、EntityCreateViewのpostメソッド内から呼び出される
  def get(self, request, **kwargs):  #selfはメソッドを呼んだインスタンス自体
  
    try:
      user = usermodel.objects.get(pk=self.kwargs['user_id'])
      entity = LegalEntity.objects.get(pk=self.kwargs['entity_id'])

    except usermodel.DoesNotExist:
        return HttpResponseBadRequest()
            
    if not user.is_active3:
      user.is_active3 = True
      if user.is_active1 and user.is_active2:
        user.is_active = True

      user.save()

    context = {
      'user': user,
      'entity': entity,
    }

    return TemplateResponse(request, 'accounts/agreement_confirm_buyer.html', context) 


  def post(self, request, *args, **kwargs):
  
    button_value = self.request.POST.get('next', '') 
    checkbox_value = request.POST.get('check_consent', '')  
    print(f'entity.is_consent_membership={checkbox_value}')

    if button_value == 'agree':  

      user = usermodel.objects.get(pk=self.kwargs['user_id'])
      entity = LegalEntity.objects.get(pk=self.kwargs['entity_id'])

      if checkbox_value == 'agree': # 規約同意にチェックされた場合

        entity.is_consent_membership = True
        entity.date_consent_membership = timezone.now()
        entity.date_joined = timezone.now()
        entity.save()

        return redirect('accounts:login', 1)
      
      else:
        messages.error(request, "「利用規約に同意します。」のチェックボックスにチェックがありません。", extra_tags='no check')

        context = {
          'user': user,
          'entity': entity,
        }
        return render(self.request, 'accounts/agreement_confirm_buyer.html', context)
    
    if button_value == 'disagree':

      # パートナー企業の情報を削除（個人の情報は残す）、ユーザー情報は残す
      messages.error(request, "利用規約には同意せず、パートナー企業の情報を削除しました。", extra_tags='no check')
      entity.delete()

      return redirect('index_qconnect_buyer')

    return HttpResponseBadRequest()  # 基本的にはここには来ない


"""25/01/10 利用規約に同意するためのビュー"""
class AgreementConfirmView_seller(generic.UpdateView):

  model = LegalEntity
  form_class = AgreementConfirmForm_seller
  template_name = 'accounts/agreement_confirm_seller.html'

  ## このgetメソッドは開発時に利用するためのもの　24/01/08
  ## 通常時は、EntityCreateViewのpostメソッド内から呼び出される
  def get(self, request, **kwargs):  #selfはメソッドを呼んだインスタンス自体
  
    try:
      user = usermodel.objects.get(pk=self.kwargs['user_id'])
      entity = LegalEntity.objects.get(pk=self.kwargs['entity_id'])

    except usermodel.DoesNotExist:
        return HttpResponseBadRequest()
            
    if not user.is_active3:
      user.is_active3 = True
      if user.is_active1 and user.is_active2:
        user.is_active = True

      user.save()

    context = {
      'user': user,
      'entity': entity,
    }

    return TemplateResponse(request, 'accounts/agreement_confirm_seller.html', context) 


  def post(self, request, *args, **kwargs):

    button_value = self.request.POST.get('next', '') 
    checkbox_value = request.POST.get('check_consent', '')  
    print(f'entity.is_consent_membership={checkbox_value}')
 
    if button_value == 'agree':  

      user = usermodel.objects.get(pk=self.kwargs['user_id'])
      entity = LegalEntity.objects.get(pk=self.kwargs['entity_id'])

      if checkbox_value == 'agree':

        entity.is_consent_membership = True
        entity.date_consent_membership = timezone.now()
        entity.date_joined = timezone.now()
        entity.email = user.email

        entity.save()
        print(f'pass after if next==agree')
        return redirect('accounts:login', 2)

      else:
        messages.error(request, "「利用規約に同意します。」のチェックボックスにチェックがありません。", extra_tags='no check')

        context = {
          'user': user,
          'entity': entity,
        }
        return render(self.request, 'accounts/agreement_confirm_seller.html', context)
    
    if button_value == 'disagree':

      # パートナー企業の情報を削除（個人の情報は残す）、ユーザー情報は残す
      messages.error(request, "利用規約には同意せず、ゲスト企業としての情報を削除しました。", extra_tags='no check')
      entity.delete()

      return redirect('logout_seller')

    return HttpResponseBadRequest()  # 基本的にはここには来ない

"""ログインした後に呼ばれるビュー"""
class MyPageView_admin(generic.DetailView):

  model = CustomUser
  template_name = "accounts/mypage_admin.html"

  
  def get(self, request, *args, **kwargs):
    if request.method != "GET":
      return HttpResponseNotAllowed("GET")

  
    # 「URLパラメーターがある場合」と「ない場合（ログインから）」に分ける   
    try:
      self.object = usermodel.objects.get(pk=self.kwargs['user_id'])
    except:
      print(f'request.user={request.user} def get in MyPageView_admin')
      self.object = usermodel.objects.get(email=self.request.user) 
  
    if self.object.type1 != 3:

      if self.object.type1 == 1:
        message = "パートナーで登録されています。パートナーでログインして下さい。"
        messages.add_message(request, messages.INFO, message) 
        logout(request)
        return HttpResponseRedirect(reverse('accounts:login', 1))

      if self.object.type1 == 2:
        message = "ゲストで登録されています。ゲストでログインして下さい。"
        messages.add_message(request, messages.INFO, message) 
        logout(request)
        return HttpResponseRedirect(reverse('accounts:login', 2))

    print(f'self.object.entityname={self.object.entityname} def get in MyPageView_admin')

    return TemplateResponse(
      request, "accounts/mypage_admin.html",
      { 
        "user": self.object,
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

    if self.object.type1 != 1:

      if self.object.type1 == 2:
        message = "ゲストで登録されています。ゲストでログインして下さい。"
        messages.add_message(request, messages.INFO, message) 
        logout(request)
        return TemplateResponse(request, "accounts/login.html", {"type1":2})

      if self.object.type1 == 3:
        message = "スタッフで登録されています。スタッフでログインして下さい。"
        messages.add_message(request, messages.INFO, message) 
        logout(request)
        return TemplateResponse(request, "accounts/login.html", {"type1":3})

    print(f'self.object.entityname={self.object.entityname} def get in MyPageView_buyer')

    entity = LegalEntity.objects.get(entityname=self.object.entityname)
    
    today = date.today()
    year = today.year; month = today.month; day = today.day

    first_of_month = date(year, month, 1)
    first_of_next_month = first_of_month + relativedelta(months=+1)
    first_of_month_after_next = first_of_month + relativedelta(months=+2)

    query_tx = QpayTx.objects.filter(
      buyEntity=entity,
      tx_status_int = 2,
      original_payment_date__gte = first_of_next_month,
      original_payment_date__lt = first_of_month_after_next)
    
    payment_date = first_of_next_month
    payment_count = query_tx.count
    payment_amount = query_tx.aggregate(Sum('approved_amount'))

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
      return reverse('qpay:txlist_buyer_approve', kwargs={'user_id': self.object.id})
      

    # 以下、各プログラムを加えていく
    #if next == '':
    #  form = TxCreateForm(request.POST)
    #  return super().form_valid(form)    
    
    #if next == '':
    #  form = TxCreateForm(request.POST)
    #  return super().form_valid(form)

  # form_validを使わなくなった時点で不要ではないか
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

    if self.object.type1 != 2:

      if self.object.type1 == 1:
        message = "パートナーで登録されています。パートナーでログインして下さい。"
        messages.add_message(request, messages.INFO, message) 
        logout(request)
        return TemplateResponse(request, "accounts/login.html", {"type1":1})

      if self.object.type1 == 3:
        message = "スタッフで登録されています。スタッフでログインして下さい。"
        messages.add_message(request, messages.INFO, message) 
        logout(request)
        return TemplateResponse(request, "accounts/login.html", {"type1":3})


    # ★error 個人で登録している人にエンティティが登録されていない 25/01/14
    # ★task ①複数のパートナーと仕事をするとき、②個人で仮登録しか終わってないとき 25/01/14

    # print(f'self.object.entityname={self.object.entityname} def get in MyPageView_seller')
    # entity = LegalEntity.objects.get(email=self.request.user, entityname=self.object.entityname)

    return TemplateResponse(request, "accounts/mypage_seller.html", { "user": self.object }) 


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

    #if next == 'myinfo':
    #  form = TxCreateForm(request.POST)
    #  return super().form_valid(form)

  def get_success_url(self):
    return reverse('qpay:tx_create', kwargs={'user_id': self.object.id})


class ContactView_buyer(generic.FormView):

  template_name = 'accounts/contact_buyer.html'
  form_class = ContactForm
  success_url = reverse_lazy('accounts:contact_buyer')

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

class ContactView_seller(generic.FormView):

  template_name = 'accounts/contact_seller.html'
  form_class = ContactForm
  success_url = reverse_lazy('accounts:contact_seller')

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
  

""" ゲストがメールにあるリンクから口座登録する場合に利用するビュー """
class BankAccountCreateView_before(generic.TemplateView):

  timeout_seconds = getattr(settings,  'ACTIVATION_TIMEOUT_SECONDS', 60*60*24)

  def get(self, request, *args, **kwargs):
      
    token = self.kwargs.get('token')  #kwargsはdict型
    print(f'token={token} def get in class BankAccountCreateView_before')
    
    try:
      tx_id = loads(token, max_age=self.timeout_seconds)
      print(f'tx_id={tx_id}, def get in class BankAccountCreateView_before')

    except SignatureExpired:
      return HttpResponseBadRequest()

    except BadSignature:  # tokenが間違っている場合
      return HttpResponseBadRequest()

    return HttpResponseRedirect(reverse('accounts:bankAccountCreate', kwargs={'tx_id': tx_id}))
  
  # POSTメソッドで口座登録する場合に備えて保持 24/07/21 POST関数がなくとも機能するか？
  #def get_success_url(self):
  #  entity_id = self.kwargs['entity_id']  #kwargsはdict型
  #  return reverse_lazy('accounts:bankAccountCreate', kwargs={'entity_id': entity_id})


class BankAccountCreateView(generic.CreateView):
  
  model = BankAccount
  form_class = BankAccountForm
  template_name='accounts/bankAccountCreate1.html'

  def get(self, request, *args, **kwargs):

    user = usermodel.objects.get(email=self.request.user) 
    init_dict = {}

    # ★★★ 250721 MyPageから設定するときはエンティティを選べるようにする
    # infoEdit_sellerから呼ばれた後の対応ができていない

    # tx_idが指定されているかで処理を分ける
    # tx_idの指定があるときはパートナーが前払いの承認時に口座未設定の場合
    try:
      tx_id = self.kwargs.get('tx_id')
      tx = QpayTx.objects.get(tx_id=tx_id)
      sellEntity = tx.sellEntity()
    
      if sellEntity.BankAccount_flag == 0: # 受取口座が未設定の場合
        form = self.form_class(initial=init_dict)
        context = {
          "form" : form,
          "temporal_tx_id" : tx_id,
        }
        # 新しい口座設定の画面をレンダリングする
        return render(request, 'accounts/bankAccountCreate2.html', context)   

      else:

        # 受取口座が設定済み場合sellEntity.BankAccount_flag == 1）
        # 既に口座設定がなされている場合は、表示できるように初期値に入力

        #try:
        #  entity_id = self.kwargs.get('entity_id')
        #  init_dict.update(entity_id=entity_id)
        #except:
        #  tmp_le = query_le.first()
        #  entity_id = tmp_le.id

        ba = sellEntity.bankAccount()
        print(f'ba.BankName={ba.BankName}')
        print(f'ba.BranchName={ba.BranchName}')
        init_dict.update(BankCode=ba.BankCode)
        init_dict.update(BandnchName=ba.BankName)
        init_dict.update(BranchCode=ba.BranchCode)
        init_dict.update(BranchName=ba.BranchName)
        init_dict.update(holdername=ba.holdername)
        init_dict.update(accountNumber=ba.accountNumber)

        form = self.form_class(initial=init_dict)

        dict_Banks = {} 
        dict_BankCode_Branches = {} 

        for BankCode in Bank.all:
          dict_Banks.update({BankCode : Bank[BankCode].name})
          dict_BankCode_Branches.update({BankCode : Bank[BankCode]})
          if BankCode == '0001': print(dict_BankCode_Branches)

        context = {
          "form" : form,
          "dict_Banks": dict_Banks,
          "json_Banks": json.dumps(dict_Banks),
          "dict_BankCode_Branches": dict_BankCode_Branches,
          "json_BankCode_Branches": json.dumps(dict_BankCode_Branches),
        }
        # 既存口座を表示のうえ、新しい口座を設定を選択する画面をレンダリング
        return render(request, 'accounts/bankAccountCreate1.html', context)

    except: 

      tx_id = 0  # 前払い取引の指定がない場合 （infoEdit.htmlからのアクセス）
      query_le = user.entities.select_related('BankAccount')
      init_dict.update(temporal_tx_id=tx_id)
      return render(request, 'accounts/bankAccountCreate1.html', context)


      

  def post(self, request, *args, **kwargs):

    form = self.form_class(request.POST)

    # 既に口座設定済みの方の処理
    WhichAccount = self.request.POST.get('WhichAccount', '')
    if WhichAccount:

      if WhichAccount == 'ThisAccount':
        print(f'pass1 WhichAccount={WhichAccount}')
        return HttpResponseRedirect(reverse_lazy('accounts:mypage_seller'))
      
      if WhichAccount == 'NewAccount':
        context = { "form" : form, }
        return render(request, "accounts/bankAccountCreate2.html", context)


    # 検索ボタン（金融機関 or 支店）を押したときの処理。条件にマッチするデータ（辞書型）を返す
    BankSearchBtn = self.request.POST.get('name_BankSearchBtn', '')
    BranchSearchBtn = self.request.POST.get('name_BranchSearchBtn', '')

    if BankSearchBtn:

      BankSearchInput = self.request.POST['name_BankSearchInput']
      print(f'ここ来る３ name_BankSearchInput={BankSearchInput}')
      dict_MatchedBank = BankAccount.BankSearch(BankSearchInput)

      dict_BankCode_Branches = {}

      for BankCode in Bank.all:

        # この下の部分が機能していないと判明
        dict_Branches = {} 
        for BranchCode in Bank[BankCode].branches:
          dict_Branches.update({BranchCode : Bank[BankCode].branches[BranchCode].name})

        dict_BankCode_Branches.update({BankCode : dict_Branches})
        if BankCode  == '0002': print(dict_BankCode_Branches)

      context = {
        "form" : form,
        "dict_MatchedBank": dict_MatchedBank,
        "dict_BankCode_Branches": dict_BankCode_Branches,
        "json_BankCode_Branches": json.dumps(dict_BankCode_Branches),
      }

      return render(request, "accounts/bankAccountCreate2.html", context)


    if BranchSearchBtn:
      
      BankSearchInput = self.request.POST['name_BankSearchInput']
      dict_MatchedBank = BankAccount.BankSearch(BankSearchInput)

      BankCode = self.request.POST['name_BankSelect']
      BranchSearchInput = self.request.POST['name_BranchSearchInput']
      print(f'ここ来る４ POST[name_BankSelect]={BankCode} POST[name_BranchSearchInput]={BranchSearchInput}')
      dict_MatchedBranch = BankAccount.BranchSearch(BankCode, BranchSearchInput)

      context = {
        "form" : form,
        "dict_MatchedBank": dict_MatchedBank,
        "dict_MatchedBranch": dict_MatchedBranch,
        "BankCode": BankCode,
      }

      return  TemplateResponse(request, "accounts/bankAccountCreate2.html", context)


    next = self.request.POST.get('next', '')   # POST.getはミドルウェア機能 
    print(f'next={next}')


    if next:

      if next == 'ToInput': # 口座名義・番号を入力する処理

        print(f'ここ通る？ if next==ToInput after def post form.is_valid in BankAccountCreateView')

        temporal_tx_id = self.request.POST['temporal_tx_id']
        # 取引承認が下りてから口座設定する場合（取引番号をキープ）
   
        entity_id = self.request.POST['entity_id']   
        BankCode = self.request.POST['name_BankSelect']
        BranchCode = self.request.POST['name_BranchSelect']

        BankName = BankAccount.BankCodeSearch(BankCode)
        BranchName = BankAccount.BranchCodeSearch(BankCode, BranchCode)

        print(f'temporal_tx_id={temporal_tx_id} BankAccountCreateV, post, next==ToInput')
        print(f'entity_id={entity_id} BankAccountCreateV, post, next==ToInput')
        print(f'BankCode={BankCode} BankAccountCreateV, post, next==ToInput')
        print(f'BranchCode={BranchCode} BankAccountCreateV, post, next==ToInput')
        print(f'BankName={BankName} BankAccountCreateV, post, next==ToInput')
        print(f'BranchName={BranchName} BankAccountCreateV, post, next==ToInput')

        init_dict = {
          'temporal_tx_id': temporal_tx_id,
          'entity_id': entity_id,
          'BankCode': BankCode,
          'BranchCode': BranchCode,
          'BankName': BankName,
          'BranchName': BranchName,
        }

        form = self.form_class(initial=init_dict)

        return render(request, "accounts/bankAccountCreate3.html", { "form": form })


      if next == 'ToDone':

        if form.is_valid():
          return render(request, "accounts/bankAccountCreate_done.html", { "form": form, "entity_id": self.request.POST['entity_id']})
          # ★★★ 250721 bankAccountCreate_done.htmlは使ってない
        else:
          entity_id =self.request.POST['entity_id']
          return render(request, "accounts/bankAccountCreate3.html", { "form": form, "entity_id": self.request.POST['entity_id']})


      if next == 'register': # 口座名義・番号を登録する処理

        if form.is_valid():

          ba_tmp = BankAccount()
          ba_tmp = form.save(commit=False)
          ba_tmp.temporal_tx_id = 0

          try:

            # 既存口座データがある場合の処理
            ba = self.model.objects.get(entity_id=ba_tmp.entity_id)
            ba.entity_id = ba_tmp.entity_id
            ba.BankCode = ba_tmp.BankCode
            ba.BankName = ba_tmp.BankName
            ba.BranchCode = ba_tmp.BranchCode
            ba.BranchName = ba_tmp.BranchName
            ba.holdername = ba_tmp.holdername
            ba.accountNumber = ba_tmp.accountNumber
            ba.temporal_tx_id = 0

            ba.save()

            le = LegalEntity.objects.get(pk=ba.entity_id)
            le.BankAccount_flag = 1
            le.BankAccount = ba
            le.save()

            print(f'ba.entity_id={ba.entity_id} BankAccountCreateV, post, next==register')
            print(f'ba.BankCode={ba.BankCode} BankAccountCreateV, post, next==register')

          except:

            # 既存口座データがない場合の処理
            # ＝（ba = self.model.objects.get(entity_id=ba_tmp.entity_id)がデータ取得できない場合）
            ba_tmp.save()
            le = LegalEntity.objects.get(pk=ba_tmp.entity_id)
            le.BankAccount_flag = 1
            le.BankAccount = ba_tmp
            le.save()

            messages.add_message(request, messages.INFO, "受け取り口座は設定されました。") 

            print(f'ba.entity_id={ba.entity_id} BankAccountCreateV, post, next==register')
            print(f'ba.BankCode={ba.BankCode} BankAccountCreateV, post, next==register')

          return TemplateResponse(reverse_lazy('mypage_seller'))

        else:
          messages.add_message(request, messages.INFO, "口座情報の入力にエラーがあります。") 
          return render(self.request, 'accounts/bankAccountCreate1.html', {'form':form})


      if next == 'back':
        print(f'ここまで来てる（def post if next==back after form.is_valid in class BankAccountCreateView）')
        return render(self.request, 'accounts/bankAccountCreate3.html', {'form':form})
  
    return HttpResponseBadRequest()

  def form_invalid(self, form):

    print(f'ここ来てる2（form_invalid in class BankAccountCreateView）')
    print(form.errors)
    form.instance.user = self.request.user
    return super().form_invalid(form)

  def get_success_url(self):
    return reverse('accounts:mypage_seller')

#  def get_context_data(self, **kwargs):
#    context = super().get_context_data(**kwargs)
#    context['bank_object_list'] = Bank.objects.all() 
#    print(f'これ使ってない!!!! get_context_data in BankAccountCreateView')
#    return context


class BankAccount:

  def BankSearch(keyword):
    
    dict_MatchedBank = {}
    
    for code in Bank.all:
      #bank = Bank[code]
      bank = Bank[code]

      if re.match(keyword, code) or \
        bank.name.find(keyword) >= 0 or \
        bank.kana.find(keyword) >= 0 or \
        bank.hira.find(keyword) >= 0 or \
        bank.roma.find(keyword) >= 0: 

        dict_MatchedBank.update({ code: bank.name })

        # reはimportしている機能（自作インスタンスではない）

        #銀行コードと銀行名を出力
        #print({
        #  "code": code,
        #  "name": bank.name,
        #})

    return dict_MatchedBank
  

  def BranchSearch(BankCode, keyword):
    
    dict_MatchedBranch = {}
    
    branches = Bank[BankCode].branches
  
    for code in branches:
      #bank = Bank[code]
      branch = branches[code]

      if re.match(keyword, code) or\
        branch.name.find(keyword) >= 0 or\
        branch.kana.find(keyword) >= 0 or\
        branch.hira.find(keyword) >= 0 or\
        branch.roma.find(keyword) >= 0: 
        
        dict_MatchedBranch.update({ code: branch.name })

        #銀行コードと銀行名を出力
        #print({
        #  "code": code,
        #  "name": branch.name,
        #})

    return dict_MatchedBranch

  def BankCodeSearch(BankCode):
    
    for code in Bank.all:
      #bank = Bank[code]
      bank = Bank[code]

      if re.match(BankCode, code): return bank.name
      
    return '該当データなし'

  def BranchCodeSearch(BankCode, BranchCode):
    
    branches = Bank[BankCode].branches
  
    for code in branches:
      #bank = Bank[code]
      branch = branches[code]

      if re.match(BranchCode, code): return branch.name

    return '該当データなし'
  
"""メインメニューから呼ばれる登録情報変更ビュー"""
class InfoEditView_seller(generic.DetailView):

  model = CustomUser
  template_name = "accounts/infoEdit_seller.html"
  form_class = InfoEditForm_seller
  
  def get(self, request, *args, **kwargs):

    if request.method != "GET":
      return HttpResponseNotAllowed("GET")

    # 後者の場合は、request.userがAdminから切り替わっていない場合がある！
    # 前のページの情報は認識できないのか？  

    try:
      user = usermodel.objects.get(email=self.request.user) 
      print(f'request.user={request.user} def get in InfoEditView_seller')

    except usermodel.DoesNotExist:

      # データが存在しない場合の処理
      messages.add_message(request, messages.INFO, "ログインID、またはパスワードが一致しません") 
      return HttpResponseRedirect(reverse('accounts:login_seller'))

    if user.type1 == 1:

      # 次のメッセージは確認できなかったので、要調整（トップページで出るようにする？）
      messages.add_message(request, messages.INFO, "発注者としてログインして下さい") 
      return HttpResponseRedirect(reverse('accounts:logout'))

    return TemplateResponse(request, "accounts/infoEdit_seller.html", { "user": user, }) 


  def post(self, request, *args, **kwargs):
    # ここは通らないと思う。BankAccountViewのGETに行くのでは
    print(f'ここに来てる1（def post in class InfoEditView_seller）')
    self.object = LegalEntity.objects.get(pk=self.kwargs['entity_id'])
  
    next = self.request.POST.get('next', '')
    if next == 'edit_bankAccount':
      ba = BankAccount.objects.get(entity_id = self.kwargs['entity_id'])

      form = BankAccountForm(instance=ba)

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
    return reverse('accounts:bankAccountCreate1', kwargs={'entity_id': self.object.id})
