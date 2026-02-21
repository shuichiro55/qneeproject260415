from django.contrib.auth import logout, get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin

from django.contrib.auth.views import \
  LoginView, PasswordChangeView, \
  PasswordResetView, PasswordResetDoneView, PasswordResetConfirmView
from .models import CustomUser, BankAccount
from .models import LegalEntity
from send.models import ServInfoMailSets

from django.template.response import TemplateResponse
from django.urls import reverse, reverse_lazy

from django.shortcuts import redirect
from django.conf import settings

from django.views import generic
from .form import \
  MyLoginForm, \
  UserCreateForm_buyer, UserCreateForm_seller, UserCreateForm_admin, \
  UserAddForm_buyer, EntitySetForm_buyer, EntityCreateForm_buyer, PermissionUpdateForm_buyer,\
  UserAddForm_seller, EntitySetForm_seller, EntityCreateForm_seller, PermissionUpdateForm_seller,\
  MyPageForm_buyer, MyPageForm_seller, \
  ContactForm, BankSelectForm, BankAccountForm, \
  AgreementConfirmForm_buyer, AgreementConfirmForm_seller, \
  MyPasswordChangeForm

from qpay.models import QpayTx
from qpay.form import TxCreateForm, TxApproveForm_buyer

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
from django.db.models import Q
import unicodedata, re
import json


# 以下は2025/02/14時点で参照されていない
from django.test import TestCase
from django.core.paginator import Paginator
#from django.core.exceptions import ValidationError
#from django.core.exceptions import PermissionDenied
#from django.contrib.auth.views import LogoutView

#from django import forms

usermodel = get_user_model()  #get_user_model は、settings.py で AUTH_USER_MODEL に指定されているモデルを取得する関数

# MyLoginView_sellerでロインした場合に通る想定
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
  template_name='accounts/buyer/login.html'

  def get_context_data(self, **kwargs):
    context = super().get_context_data(**kwargs)
    return context

  def get_success_url(self):

    print(f'通過1 get_success_url in MyLoginView_buyer')

    if 'token' in self.kwargs:
      token =self.kwargs['token']
      return reverse_lazy('qpay:txdetail_buyer_approve_before', kwargs={'token': token})

    else:

      if self.request.user.is_authenticated:

        user = usermodel.objects.get(email=self.request.user)
        entity = LegalEntity.objects.get(entity=user.entity)

        self.request.session['user_id'] = user.id
        self.request.session['entity_id'] = entity.id
        # ログイン後は下記で取得
        # request.session.get('user_id')、request.session.pop('user_id', None)

        print(f'user={user} in get_success_url in MyLoginView_buyer')

        if user.type1 != 1:
          if user.type1 == 1: type1_name = "パートナー"
          if user.type1 == 2: type1_name = "ゲスト"
          if user.type1 == 3: type1_name = "スタッフ"

          message = type1_name + "での登録です。" + type1_name + "でログインしてください。"
          messages.add_message(self.request, messages.WARNING, message) 
          logout(self.request)

          if user.type1 == 1: return reverse_lazy('accounts:login_buyer')
          if user.type1 == 2: return reverse_lazy('accounts:login_seller')
          if user.type1 == 3: return reverse_lazy('accounts:login_admin')

        return reverse_lazy('accounts:mypage_buyer')

      else:
        print(f'ログイン出来てません。 def get in MyLoginView_buyer')
        logout(self.request)


class MyLoginView_seller(LoginView):

  #redirect_authenticated_user=True,  "Trueの場合、ログイン済みユーザーはトップページ等にリダイレクト
  model = CustomUser
  form_class = MyLoginForm
  template_name='accounts/seller/login.html'

  def get_context_data(self, **kwargs):
    context = super().get_context_data(**kwargs)
    return context

  def get_success_url(self):

    print(f'通過1 get_success_url in MyLoginView_seller')

    user = usermodel.objects.get(email=self.request.user)

    if user.type1 != 2:
      if user.type1 == 1: type1_name = "パートナー"
      if user.type1 == 2: type1_name = "ゲスト"
      if user.type1 == 3: type1_name = "スタッフ"

      message = type1_name + "での登録です。" + type1_name + "でログインしてください。"
      messages.add_message(self.request, messages.INFO, message) 
      logout(self.request)
      print(f'user.type1={user.type1} in get_success_url in MyLoginView_seller')

      if user.type1 == 1: return reverse_lazy('accounts:login_buyer')
      if user.type1 == 2: return reverse_lazy('accounts:login_seller')
      if user.type1 == 3: return reverse_lazy('accounts:login_admin')

    return reverse_lazy('accounts:mypage_seller')


class MyLoginView_admin(LoginView):

  #redirect_authenticated_user=True,  "Trueの場合、ログイン済みユーザーはトップページ等にリダイレクト
  model = CustomUser
  form_class = MyLoginForm
  template_name='accounts/admin/login.html'

  def get_context_data(self, **kwargs):
    context = super().get_context_data(**kwargs)
    return context

  def get_success_url(self):

    print(f'通過1 get_success_url in MyLoginView_admin')
    user = usermodel.objects.get(email=self.request.user)

    if user.type1 != 3:
      if user.type1 == 1: type1_name = "パートナー"
      if user.type1 == 2: type1_name = "ゲスト"
      if user.type1 == 3: type1_name = "スタッフ"

      message = type1_name + "での登録です。" + type1_name + "でログインしてください。"
      messages.add_message(self.request, messages.INFO, message) 
      logout(self.request)
      print(f'user.type1={user.type1} in get_success_url in MyLoginView_admin')

      if user.type1 == 1: return reverse_lazy('accounts:login_buyer')
      if user.type1 == 2: return reverse_lazy('accounts:login_seller')
      if user.type1 == 3: return reverse_lazy('accounts:login_admin')

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


# 25/11/14 パスワードリセット用
class MyPasswordResetView_buyer(PasswordResetView):

  """パスワード変更用URLの送付ページ"""
  from_email='shuichiro.tomihari.201406@gmail.com'
  subject_template_name = 'accounts/buyer/mail/passwordReset_subject.txt'
  email_template_name = 'accounts/buyer/mail/passwordReset_message.txt'
  template_name = 'accounts/buyer/passwordReset.html'
  success_url = reverse_lazy('accounts:passwordResetDone_buyer')
  
  # PasswordResetFormでの項目はemail

class MyPasswordResetDoneView_buyer(PasswordResetDoneView):
    """パスワード変更用URLを送りましたページ"""
    template_name = 'accounts/buyer/passwordResetDone.html'

class MyPasswordResetConfirmView_buyer(PasswordResetConfirmView, LoginRequiredMixin):

  template_name = 'accounts/buyer/passwordResetConfirm.html'

  def get_success_url(self):
    print(f'通過1 get_success_url in MyPasswordResetConfirm_buyer')   
    messages.add_message(self.request, messages.INFO, "パスワードの再設定が完了しました。") 
    return reverse_lazy('accounts:login_buyer')
  
    # SetPasswordFormでのfield
    # new_password1, new_password2 = SetPasswordMixin.create_password_fields(
    #   label1=_("New password"), label2=_("New password confirmation"))


# 25/11/14 パスワードリセット用
class MyPasswordResetView_seller(PasswordResetView):

  """パスワード変更用URLの送付ページ"""
  from_email='shuichiro.tomihari.201406@gmail.com'
  subject_template_name = 'accounts/seller/mail/passwordReset_subject.txt'
  email_template_name = 'accounts/seller/mail/passwordReset_message.txt'
  template_name = 'accounts/seller/passwordReset.html'
  success_url = reverse_lazy('accounts:passwordResetDone_seller')
  
  # PasswordResetFormでの項目はemail

class MyPasswordResetDoneView_seller(PasswordResetDoneView):
    """パスワード変更用URLを送りましたページ"""
    template_name = 'accounts/seller/passwordResetDone.html'


class MyPasswordResetConfirmView_seller(PasswordResetConfirmView, LoginRequiredMixin):

  template_name = 'accounts/seller/passwordResetConfirm.html'

  def get_success_url(self):
    print(f'通過1 get_success_url in MyPasswordResetConfirm_seller')   
    messages.add_message(self.request, messages.INFO, "パスワードの再設定が完了しました。") 
    return reverse_lazy('accounts:login_seller')
  
    # SetPasswordFormでのfield
    # new_password1, new_password2 = SetPasswordMixin.create_password_fields(
    #   label1=_("New password"), label2=_("New password confirmation"))


# 25/11/14 パスワードリセット用
class MyPasswordResetView_admin(PasswordResetView):

  """パスワード変更用URLの送付ページ"""
  from_email='shuichiro.tomihari.201406@gmail.com'
  subject_template_name = 'accounts/admin/mail/passwordReset_subject.txt'
  email_template_name = 'accounts/admin/mail/passwordReset_message.txt'
  template_name = 'accounts/admin/passwordReset.html'
  success_url = reverse_lazy('accounts:passwordResetDone_admin')
 
  # PasswordResetFormでの項目はemail

class MyPasswordResetDoneView_admin(PasswordResetDoneView):
    """パスワード変更用URLを送りましたページ"""
    template_name = 'accounts/admin/passwordResetDone.html'


class MyPasswordResetConfirmView_admin(PasswordResetConfirmView, LoginRequiredMixin):

  template_name = 'accounts/admin/passwordResetConfirm.html'

  def get_success_url(self):
    print(f'通過1 get_success_url in MyPasswordResetConfirm_admin')   
    messages.add_message(self.request, messages.INFO, "パスワードの再設定が完了しました。") 
    return reverse_lazy('accounts:login_admin')
  
    # SetPasswordFormでのfield
    # new_password1, new_password2 = SetPasswordMixin.create_password_fields(
    #   label1=_("New password"), label2=_("New password confirmation"))


# 25/05/17に追加
class MyPasswordChangeView_buyer(PasswordChangeView):

  """パスワード変更ビュー"""
  form_class = MyPasswordChangeForm
  template_name = 'accounts/buyer/passwordChange_admin'

  def get_context_data(self, **kwargs):
    context = super().get_context_data(**kwargs)
    user = usermodel.objects.get(email=self.request.user)
    context['user_id'] = user.id
    user_id = context['user_id'] 
    print(f'user_id = {user_id} get_context_data in MyPasswordChangeView_buyer')
    return context

  def get_success_url(self):
    print(f'通過1 get_success_url in MyPasswordChangeView_buyer')   
    messages.add_message(self.request, messages.INFO, "パスワードが変更されました") 
    return reverse_lazy('accounts:mypage_buyer')


# 25/05/17に追加
class MyPasswordChangeView_seller(PasswordChangeView):

  """パスワード変更ビュー"""
  form_class = MyPasswordChangeForm
  template_name = 'accounts/seller/passwordChange_admin'

  def get_context_data(self, **kwargs):
    context = super().get_context_data(**kwargs)
    user = usermodel.objects.get(email=self.request.user)
    context['user_id'] = user.id
    user_id = context['user_id'] 
    print(f'user_id = {user_id} get_context_data in MyPasswordChangeView_seller')
    return context

  def get_success_url(self):
    print(f'通過1 get_success_url in MyPasswordChangeView_seller')   
    messages.add_message(self.request, messages.INFO, "パスワードが変更されました") 
    return reverse_lazy('accounts:mypage_seller')


# 25/05/17に追加
class MyPasswordChangeView_admin(PasswordChangeView):

  """パスワード変更ビュー"""
  form_class = MyPasswordChangeForm
  template_name = 'accounts/admin/passwordChange_admin'

  def get_context_data(self, **kwargs):
    context = super().get_context_data(**kwargs)
    user = usermodel.objects.get(email=self.request.user)
    context['user_id'] = user.id
    user_id = context['user_id'] 
    print(f'user_id = {user_id} get_context_data in MyPasswordChangeView_admin')
    return context

  def get_success_url(self):
    print(f'通過1 get_success_url in MyPasswordChangeView_admin')
    messages.add_message(self.request, messages.INFO, "パスワードが変更されました") 
    return reverse_lazy('accounts:mypage_admin')


class UserCreateView_buyer(generic.CreateView):

  model = CustomUser
  template_name = 'accounts/buyer/userCreate.html'
  form_class = UserCreateForm_buyer


  def get(self, request, **kwargs):  #selfはメソッドを呼んだインスタンス自体

    context = {
      'flag_step': 1,
      'form' : self.form_class,
    }
    return TemplateResponse(request, 'accounts/buyer/userCreate.html', context)  #ここでgetとするのは、おそらく親クラスでtemplate_nameを表示するように規定されている


  # CreateView（親クラス）で自動バリデーションが通ったときに実行される
  # ユーザーインスタンス生成・保存、type1,type2の登録、本登録用メールの発行を行う

  def post(self, request, **kwargs):  #selfはメソッドを呼んだインスタンス自体

    form = self.form_class(request.POST)

    if form.is_valid():

      user = form.save(commit=False)
      user.is_active = False  # メールからアクセスした時点でアクティブに

      #user.email = self.request.user
      user.type1 = 1  # パートナー：1、ゲスト：2、Qnee：3で登録 25/04/27
      user.type2 = 2  # 個人：1、法人：2 25/04/27追加

      user.save()
 
      print(f'ここまで来てる1 email={user.email} type2={user.type2} user.pk={user.pk} usr.passsword= {user.password}（def post if form.is_valid in class UserCreateView_buyer）')

    
      ### あとでsend_mailに切り替えるか検討 2025/04/27
      current_site = get_current_site(self.request)
      domain = current_site.domain
      context1 = {
        'protocol': self.request.scheme,
        'domain': domain,
        'token': dumps(user.pk),
        'user': user,
      }

      subject = render_to_string('accounts/buy/mail/userTempRegister_subject.txt', context1)
      message = render_to_string('accounts/buy/mail/userTempRegister_message.txt', context1)

      print(context1)
      print(f'メールアドレス：{user.email}')
      user.email_user(subject, message)

      context2 = {
        'flag_step': 2,
      }
      return TemplateResponse(request, 'accounts/buyer/userCreate.html', context2)

    else:
    
      print(f'ここ来てる2（def post if form.is_valid=FALSE in class UserCreateView_buyer）')
      messages.add_message(self.request, messages.INFO, form.errors) 
      context = {
        'form' : form,
        'flag_step': 1,
      }
      return TemplateResponse(request, 'accounts/buyer/userCreate.html', context)

  def form_invalid(self, form):
    print(f'ここまで来てる4（form_invalid in class UserCreateView_buyer）')
    print(form.errors)
    #form.instance.user = self.request.user
    return super().form_invalid(form)


class UserCreateView_seller(generic.CreateView):

  model = CustomUser
  template_name = 'accounts/seller/userCreate.html'
  form_class = UserCreateForm_seller


  def get(self, request, **kwargs):  #selfはメソッドを呼んだインスタンス自体
  
    context = {
      'flag_step': 1,
      'form' : self.form_class,
    }
    return TemplateResponse(request, 'accounts/seller/userCreate.html', context)  #ここでgetとするのは、おそらく親クラスでtemplate_nameを表示するように規定されている


  # CreateView（親クラス）で自動バリデーションが通ったときに実行される
  # ユーザーインスタンス生成・保存、type1,type2の登録、本登録用メールの発行を行う

  def post(self, request, **kwargs):  #selfはメソッドを呼んだインスタンス自体

    form = self.form_class(request.POST)

    if form.is_valid():

      user = form.save(commit=False)
      user.is_active = False
      """ メールからアクセス後、EntityCreateViewでアクティブ化 """
      """ is_active=Falseの場合はログインできない """

      #user.email = self.request.user
      user.type1 = 2  # パートナー：1、ゲスト：2、Qnee：3で登録 25/04/27

      user.save()
      print(f'ここまで来てる1 email={user.email} type2={user.type2} user.pk={user.pk} user.passsword= {user.password}（def post if form.is_valid in class UserCreateView1_seller）')

      ### あとでsend_mailに切り替えるか検討 2025/04/27
      current_site = get_current_site(self.request)
      domain = current_site.domain
      context1 = {
        'protocol': self.request.scheme,
        'domain': domain,
        'token': dumps(user.pk),
        'user': user,
      }

      subject = render_to_string('accounts/seller/mail/userTempRegister_subject.txt', context1)
      message = render_to_string('accounts/seller/mail/userTempRegister_message.txt', context1)

      print(context1)
      print(f'メールアドレス：{user.email}')
      user.email_user(subject, message)
     
      context2 = {
        'flag_step': 2,
      }
      return TemplateResponse(request, 'accounts/seller/userCreate.html', context2)

    else:
  
      print(f'ここ来てる2（def post if form.is_valid=FALSE in class UserCreateView1_seller）')
      messages.add_message(self.request, messages.INFO, form.errors) 

      context = {
        'flag_step': 1,
        'form' : form,
      }
      return render(request, 'accounts/seller/userCreate.html', context)  #ここでgetとするのは、おそらく親クラスでtemplate_nameを表示するように規定されている


class UserCreateView_admin(generic.CreateView):

  model = CustomUser
  template_name = 'accounts/admin/userCreate.html'
  form_class = UserCreateForm_admin

  def get(self, request, **kwargs):  #selfはメソッドを呼んだインスタンス自体

    context = {
      'flag_step': 1,
      'form' : self.form_class,
    }
    return TemplateResponse(request, 'accounts/admin/userCreate.html', context)  #ここでgetとするのは、おそらく親クラスでtemplate_nameを表示するように規定されている


  # CreateView（親クラス）で自動バリデーションが通ったときに実行される
  # ユーザーインスタンス生成・保存、type1,type2の登録、本登録用メールの発行を行う

  def post(self, request, **kwargs):  #selfはメソッドを呼んだインスタンス自体

    form = self.form_class(request.POST)

    if form.is_valid():

      user = form.save(commit=False)

      #user.email = self.request.user
      user.type1 = 3  # パートナー：1、ゲスト：2、Qnee：3で登録 25/04/27
      user.type2 = 1  # 個人として登録
      user.is_active = True
      """ is_active=Trueにしないとログインできない """
      """ パートナー、ゲストはEntityCreateViewでアクティブ化 """

      user.save()

      print(f'ここまで来てる1 email={user.email} type2={user.type2} user.pk={user.pk} usr.passsword= {user.password}（def post if form.is_valid in class UserCreateView1_admin）')

      ### あとでsend_mailに切り替えるか検討 2025/04/27
      current_site = get_current_site(self.request)
      domain = current_site.domain
      context1 = {
        'protocol': self.request.scheme,
        'domain': domain,
        'token': dumps(user.pk),
        'user': user,
      }

      subject = render_to_string('accounts/admin/mail/userTempRegister_subject.txt', context1)
      message = render_to_string('accounts/admin/mail/userTempRegister_message.txt', context1)

      print(context1)
      print(f'メールアドレス：{user.email}')
      user.email_user(subject, message)

      context2 = {
        'flag_step': 2,
      }
      return TemplateResponse(request, 'accounts/admin/userCreate.html', context2)

    else:
  
      print(f'ここ来てる2（def post if form.is_valid=FALSE in class UserCreateView1_admin）')
      print(form.errors)

      context2 = {
        'flag_step': 1,
        'form' : form,
      }
      return render(request, 'accounts/admin/userCreate.html', context2)  #ここでgetとするのは、おそらく親クラスでtemplate_nameを表示するように規定されている


"""25/01/01 メールで受領したURLがクリックされると本登録画面を表示"""

class EntityCreateView_buyer(generic.CreateView, LoginRequiredMixin):

  form_class = EntityCreateForm_buyer
  timeout_seconds = getattr(settings, 'ACTIVATION_TIMEOUT_SECONDS', 60*60*24)
  dict_buyEntityName = dict((f, f) for idx, f in enumerate(LegalEntity.objects.filter(type1=1).values_list('entityName', flat=True), 1))
  # 「flat=True」はリスト、「flat=False」はタプル

  """（ビューにおいて）GETリクエストを受け取ったときに呼び出される（実践Django P121）"""
  """ 処理：パートナーに送られたメールのURLをクリックされた時点で呼ばれる """

  """ def getでは、メールから本登録に進む場合に呼ばれ、
      ①新規パートナー登録か、②既存パートナーにユーザー追加を選択するテンプレートを送る """

  def get(self, request, **kwargs):  #selfはメソッドを呼んだインスタンス自体
  
    try:
      # メール内のURLから<token>（暗号化されたuser_id）を取り出す（kwargsはdict型）
      token = kwargs.get('token', None)
      user_pk = loads(token, max_age=self.timeout_seconds)
      print(f'token = {token}, user_pk = {user_pk} in def get of EntitySetView_buyer')
      user = usermodel.objects.get(pk=user_pk)

    except usermodel.DoesNotExist:
      message = "申し訳ありませんが、ユーザー情報が確認できません"
      messages.add_message(self.request, messages.WARNING, message) 
      return TemplateResponse(request,'accounts/buyer/login_admin', {'form':MyLoginForm}) 

    except SignatureExpired:  # 時間切れ
      # ★★ 250824 テスト未了。メルアド重複で登録不可にならないようUserオブジェクトを削除
      usermodel.objects.get(email=self.request.user).delete()
      message = "規定の時間を超えたため、再度、お手続きをお願いいたします"
      messages.add_message(self.request, messages.WARNING, message)

      return TemplateResponse(request,'accounts/buyer/login_admin', {'form':MyLoginForm}) 

    except BadSignature:      # tokenが間違っている
      return HttpResponseBadRequest()
    
    # 仮登録が完了し、メールからのリンクにより本登録を開始した時点
    user.is_active = True #Trueにしないとログインできない

    user.save()
    self.user_id = user.id
    print(f'self.user_id = {self.user_id}')

    ### ここからしたが工事中（25/06/08） ###
    ### dict_buyEntityNameのデータをselectに格納するようにする 

    #dict_buyEntityName = dict((str(idx), f) for idx, f in enumerate(LegalEntity.objects.filter(type1=1).values_list('entityName', flat=True), 1))
    #print(f'dict_buyEntityName={dict_buyEntityName} def get in EntityCreateView_buyer')

    init_dict = {
      'userName': '',
      'email': user.email,
      'tel_user': "",
    }
    context = {
      'flag_step': 1,
      'user': user,
      'form': EntitySetForm_buyer(initial=init_dict),
      'temporal_buyEntityName': "",
      # コメント(25/06/08)：Selectボックスで未選択であることを示す。選択後はページ移動でデータ保持するために使う
      'dict_buyEntityName': self.dict_buyEntityName,
      'json_buyEntityName': json.dumps(self.dict_buyEntityName),
    }

    print(f'ここ来てる1 request.user={request.user} email={user.email} type2={user.type2}（get in class EntityCreateView_buyer）')
        
    return TemplateResponse(request, 'accounts/buyer/entitySet.html', context)


  def post(self, request, *args, **kwargs):

    print(f'pass-1 self.request.user={self.request.user} in def post next1 EntityCreateView_buyer')

    next1 = self.request.POST.get('next1', None)
    next2 = self.request.POST.get('next2', None)
    # next1は、新規entityを登録する際の処理種別
    # next2は、既存entityにuser追加する際の処理種別

    """ 新規のパートナー登録をする処理 """
    if next1 != None:

      if next1.find('ToEntityCreate') >= 0:

        user = usermodel.objects.get(pk=next1.split('_')[1]) 

        context = {
          'flag_step': 1,
          'user': user,
          'form': self.form_class,
        }
        # ★★ Entityは郵便番号、代表者の他、住所を登録するようにする 25/08/01
        return TemplateResponse(self.request, 'accounts/buyer/entityCreate.html', context)


      """ 入力内容を確認する画面 """
      if next1.find('ToConfirm') >= 0:

        user = usermodel.objects.get(pk=next1.split('_')[1]) 
        form = self.form_class(request.POST, nextCase=1)
        # 260103 nextCaseを追加（①パートナー追加と②ユーザー追加に分ける）

        if form.is_valid():
        # 下記①、②、③の順で実行
        # ①.is_valid()、②フォームでのclean、clean_<field>、③form.cleaned_data[]に格納

          cleaned_data = form.cleaned_data

          init_dict = {
            'entityName' : cleaned_data['entityName'],
            'representitive' : cleaned_data['representitive'],
            'tel_entity' : cleaned_data['tel_entity'],
            
            'zip_entity' : cleaned_data['zip_entity'],
            'address1' : cleaned_data['address1'],
            'address2' : cleaned_data['address2'],
            'address3' : cleaned_data['address3'],

            'lastName' : cleaned_data['lastName'],
            'lastName_kana' : cleaned_data['lastName_kana'],
            'firstName' : cleaned_data['firstName'],
            'firstName_kana' : cleaned_data['firstName_kana'],
            'tel_user' : cleaned_data['tel_user'],
            'department' : cleaned_data['department'],
            'title' : cleaned_data['title'],
          }
          context = {
            'flag_step': 2,
            'user': user,
            'form' : self.form_class(initial=init_dict),
          }         
          return TemplateResponse(
            self.request, 'accounts/buyer/entityCreate.html', context)

        else: #バリデーションエラーの時に通る

          print(f'ここ来てる3（def post after if not form.is_valid in class EntityCreateView_buyer）')
          return TemplateResponse(self.request, 'accounts/buyer/entityCreate.html',
            {'flag_step': 1, 'user':user, 'form':form, })


      # データ確認画面から入力画面に戻る時の処理 2025/02/14
      if next1.find('BackToInput') >= 0:

        user = usermodel.objects.get(pk=next1.split('_')[1]) 

        context = {
          'user': user,
  
          'flag_step': 1,
          'form': form,
        }
        return TemplateResponse(self.request, 'accounts/buyer/.html', context)


      if next1.find('ToSave') >= 0: # 確認した内容をデータベースに登録

        # 250802 フォームをモデルフォームから通常フォームに変更したことに伴い変更
        user = usermodel.objects.get(pk=next1.split('_')[1]) 

        entity = LegalEntity.objects.create()
        entity.entityName = self.request.POST['entityName']
        #entity.entityName = form.entityName 
        # この式はエラー（'EntityCreateForm_buyer' object has no attribute 'entityName'）

        entity.representitive = self.request.POST['representitive']
        entity.tel_entity = self.request.POST['tel_entity']
        entity.zip_entity = self.request.POST['zip_entity']
        entity.address1 = self.request.POST['address1']
        entity.address2 = self.request.POST['address2']
        entity.address3 = self.request.POST['address3']

        # type1、type2はCustomUserとLegalEntityで双方で管理
        # type1；発注者／受注者、type2：個人／法人
        entity.type1 = user.type1  
        entity.type2 = user.type2

        # 251221 定期配信の初期設定（sendのServInfoMailSets（in models.py）生成、関連付け）
        mailSets = ServInfoMailSets.objects.create()
        mailSets.buyEntity = entity
        mailSets.save()

        entity.save()

        user.userName = \
          self.request.POST.get('lastName') + ' ' + self.request.POST.get('firstName')
        user.userName_kana = \
          self.request.POST.get('lastName_kana') + ' ' + self.request.POST.get('firstName_kana')

        user.tel_user = self.request.POST.get('tel_user', None)
        user.department = self.request.POST.get('department', None)
        user.title = self.request.POST.get('title', None)

        user.entity = entity

        user.canApprove_all = False
        user.canApprove_add = False
        user.canApprove_qpay = False
        # 【留意】 「False」とし、AgreementConfirmView_buyerにおいて、
        # パートナ一１人目の場合は「True」、２人目以降は権限者が「True/False」を設定

        # ★★ 250824 Qneeに登録を承認するプロセスを入れる（Qneeでis_active=Trueにする）
        # ★★ 250824 Qneeに申請が見れるようにする

        # user.is_active = True
        
        user.save()

        print(f'request.user.get_username={request.user.get_username} type2={user.type2}（def post ==confirm after form.is_valid in EntityCreateView_buyer）')
        print(f'entity.id = {entity.id}（post ==create after form.is_valid in EntityCreateView_buyer）')

        context = {
          'flag_step': 1, # agreementConfirmのflag
          'user': user,
          'entity': entity,
        }
        return TemplateResponse(self.request, 'accounts/buyer/agreementConfirm.html', context)
      

    """ 登録済みパートナーに追加する処理 """

    if next2 != None:

      if next2.find('ToConfirm') >= 0:  # 登録済みパートナーにユーザー追加

        user = usermodel.objects.get(pk=next2.split('_')[1]) 

        form = self.form_class(request.POST, nextCase=2)
        # form_class=EntityCreateForm_buyer
        # 260103 nextCaseを追加（①新規パートナーと②ユーザー追加を場合分け）

        # ★★ 250914 バリデーション（エンティティが選ばれているかを含む）を対応

        if form.is_valid():
        # 下記①、②、③の順で実行
        # ①.is_valid()、②フォームでのclean、clean_<field>、③form.cleaned_data[]に格納

          #temporal_buyEntityName = self.request.POST.get('entityName', None)
          #print(f'temporal_buyEntityName={temporal_buyEntityName} post if next2.find(ToConfirm)>=0: EntityCreateView_buyer')

          cleaned_data = form.cleaned_data 
          entityName = cleaned_data['entityName']
          print(f'cleaned_data[entityName]={entityName}')
          entity = LegalEntity.objects.get(entityName=cleaned_data['entityName'])


          init_dict = {
            #'entityName' : entity.entityName, テンプレートではentityで渡す
            'lastName' : cleaned_data['lastName'],
            'firstName' : cleaned_data['firstName'],
            'lastName_kana' : cleaned_data['lastName_kana'],
            'firstName_kana' : cleaned_data['firstName_kana'],
            'tel_user' : cleaned_data['tel_user'],
            'department' : cleaned_data['department'],
            'title' : cleaned_data['title'],
          }
          context = {
            'user': user,
            'entity': entity,
            'flag_step': 2,
            'form' : EntitySetForm_buyer(initial=init_dict),
          }
          return render(self.request, 'accounts/buyer/entitySet.html', context)  # 確認画面に行く


      if next2.find('BackToInput') >= 0:

        form = EntitySetForm_buyer(request.POST)  # form_class=EntityCreateForm_buyer

        user = usermodel.objects.get(pk=next2.split('_')[1]) 
        entity = LegalEntity.objects.get(pk=next2.split('_')[2])

        context = {
          'user': user,
          'entity': entity,
          'flag_step': 1,
          'form': form,
          'temporal_buyEntityName': entity.entityName,
          # Note(25/06/08)：選択済み内容をページ移動後も維持するために使う（初期は空欄）
          'dict_buyEntityName': self.dict_buyEntityName,
          'json_buyEntityName': json.dumps(self.dict_buyEntityName),
        }
        return TemplateResponse(request, 'accounts/buyer/entitySet.html', context)


      if next2.find('ToSave&Apply') >= 0: # entitySet.htmlの「flag_step==2」の後（登録データ確認後）

        form = EntitySetForm_buyer(request.POST)  # form_class=EntityCreateForm_buyer

        user = usermodel.objects.get(pk=next2.split('_')[1]) 
        entity = LegalEntity.objects.get(pk=next2.split('_')[2])
        print(f'user.id={user.id} entity.id={entity.id} if next2.find(ToSave&Apply) >=0 in EntityCreateView_buyer')

        #temporal_buyEntityName = self.request.POST.get('temporal_buyEntityName', "")
        #entity = LegalEntity.objects.get(entityName=temporal_buyEntityName)

        user.userName = \
          self.request.POST.get('lastName') + ' ' + self.request.POST.get('firstName')
        user.userName_kana = \
          self.request.POST.get('lastName_kana') + ' ' + self.request.POST.get('firstName_kana')

        user.tel_user = self.request.POST.get('tel_user', None)
        user.department = self.request.POST.get('department', None)
        user.title = self.request.POST.get('title', None)

        print(f'user.department={user.department}')
        print(f'user.title={user.title}')
        
        # user.entity = entity
        # ★★ 250824 ユーザー追加が承認された時点で対応

        user.save()

        context = {
          'flag_step': 1,
          'user': user,
          'entity': entity,
        }
        return render(self.request, 'accounts/buyer/agreementConfirm.html', context)

      print(form.errors)
      print(f'ここまで来てる6 例外（post in class EntityCreateView_buyer）')

  def form_valid(self, form):
    return super().form_valid(form)
  
  def form_invalid(self, form):
    print(f'ここまで来てる4（form_invalid in class EntityCreateView_buyer）')
    print(form.errors)
    #form.instance.user = self.request.user
    return super().form_invalid(form)

#  def get_form_kwargs(self):
#    print(f'self.user_id={self.user_id} def get_form_kwargs in EntityCreateView_buyer')
#    kwargs =super(EntityCreateView_buyer, self).get_form_kwargs()
#    user = usermodel.objects.gets(email=self.user.request_id)
#    kwargs['user'] = usermodel.objects.gets(pk=self.user_id)
#
#   return kwargs

"""25/01/08 利用規約に同意するためのビュー"""
class AgreementConfirmView_buyer(generic.CreateView):

  model = LegalEntity
  form_class = AgreementConfirmForm_buyer
  template_name = 'accounts/buyer/agreementConfirm.html'

  ## このgetメソッドは開発時に利用するためのもの　24/01/08
  ## 通常時は、EntityCreateViewのpostメソッド内から呼び出される
  def get(self, request, **kwargs):  #selfはメソッドを呼んだインスタンス自体
  
    try:
      user = usermodel.objects.get(pk=self.kwargs['user_id'])
      entity = LegalEntity.objects.get(pk=self.kwargs['entity_id'])

    except usermodel.DoesNotExist:
      message = "申し訳ありませんが、ユーザー情報が確認できません。"
      messages.add_message(self.request, messages.INFO, message)
      return TemplateResponse(request,'accounts/buyer/login.html', {'form':MyLoginForm}) 
     
    context = {
      'flag_step': 1,
      'user': user,
      'entity': entity,
    }
    return TemplateResponse(request, 'accounts/buyer/agreementConfirm.html', context) 


  def post(self, request, *args, **kwargs):
  
    checkValue = request.POST.get('checkConsent', None)  
    buttonValue = self.request.POST.get('next', None) 

    print(f'checkValue={checkValue}')
    print(f'buttonValue={buttonValue}')

    if buttonValue.find('ToAgree') >= 0:

      applyUser = usermodel.objects.get(pk=buttonValue.split('_')[1]) 
      buyEntity = LegalEntity.objects.get(pk=buttonValue.split('_')[2])
      print(f'applyUser.email={applyUser.email}')
      print(f'applyUser.userName={applyUser.userName}')
      print(f'applyUser.tel_user={applyUser.tel_user}')
      print(f'applyUser.department={applyUser.department}')
      print(f'applyUser.title={applyUser.title}')

      if checkValue == 'ToAgree': # 規約同意にチェックされた場合

        buyEntity.membershipConsent_boolean = True
        buyEntity.membershipConsent_at = timezone.now()
        buyEntity.joined_at = timezone.now()
        buyEntity.save()

        """ ★★ 25/02/19編集（テストは未済み）""" 
        """ 「canApprove_all=True」「canApprove_add=True」の人に承認依頼する """
        """ ただし、一人目の場合はQneeが承認するようにする """

        approvers = usermodel.objects.filter(
          Q(entity_id=buyEntity.id) & (Q(canApprove_all=True) | Q(canApprove_add=True)))
        #queryset_users = usermodel.objects.prefetch_related('entitys').filter(entitys=entity.id, is_buyUser_ApproveAll=True)

        # データ取得参考（https://noauto-nolife.com/post/django-foreignkey-related-name/）
    
        if approvers.first() is None: # 参加を承認するユーザーがいない場合（一人目のユーザーの場合）

          print(f'pass1 approvers.first() is None in def post AgreementConfirmView_buyer')
          applyUser.canApprove_all = True
          applyUser.canApprove_add = True
          applyUser.canApprove_qpay = True

          # ★★ 250906 一人目のユーザーはQnee承認後に「approvalStatus=2」とする
          # ★★ 250906 Qneeが承認してから「is_active2=True」とする

          applyUser.approvedStatus_int = 2

          applyUser.entity = buyEntity
          applyUser.save()

          return TemplateResponse(request,'accounts/buyer/login.html', {'form':MyLoginForm}) 

        else:   # パートナー内の権限者に参加申請する

          print(f'pass2 approvers.first() != None in def post AgreementConfirmView_buyer')
          print(f'pass2 approvers[0].email={approvers[0].email}')

          current_site = get_current_site(self.request)
          domain = current_site.domain

          for approver in approvers:

            context1 = {
              'protocol': self.request.scheme,
              'domain': domain,
              'applyuser_id': dumps(applyUser.pk),  # 申請者のuser.pkを維持する
              'buyentity_id': dumps(buyEntity.pk),  # 申請者のentity.pkを維持する
            }
            print(f'applyuser.pk={applyUser.pk}, buyentity.pk={buyEntity.pk}')
            subject = render_to_string('accounts/mail/buyUserAddApply_subject.txt', context1)
            message = render_to_string('accounts/mail/buyUserAddApply_message.txt', context1)

            from_email = 'shuichiro.tomihari.201604@gmail.com'
            recipient_list = [approver['email']]
            #bcc =  ["toritoritorina@gmail.com"]  # BCCリスト
            email = EmailMessage(subject, message, from_email, recipient_list)
            email.send()
  
            print(f'pass1 approver.email={approver.email}（EntityCreateView_buyer, post, checkbox==agree)')

            context2 = {'flag_step': 2,}
            return TemplateResponse(self.request, 'accounts/buyer/agreementConfirm.html', context2)
      
      else:  # 同意チェックがされていない場合（チェックしていない場合はボタンが押せない）

        messages.error(request, "「利用規約に同意します。」のチェックボックスにチェックがありません。", extra_tags='no check')

        context = {
          'flag_step': 1,
          'applyUser': applyUser,
          'buyEntity': buyEntity,
        }
        return render(self.request, 'accounts/buyer/agreementConfirm.html', context)


    if buttonValue.find('ToDisagree') >= 0:

      messages.error(request, "「同意しない」のボタンが押されました。", extra_tags='no check')

      user = usermodel.objects.get(pk=buttonValue.split('_')[1]) 
      entity = LegalEntity.objects.get(pk=buttonValue.split('_')[2])

      context = {
        'flag_step': 1,
        'user': user,
        'entity': entity,
        }
      return render(self.request, 'accounts/buyer/agreementConfirm.html', context)
    return HttpResponseBadRequest()  # 基本的にはここには来ない


class UserAddView_buyer(generic.TemplateView, LoginRequiredMixin):

  """ 承認者がユーザー参加を承認するためビュー、ビューの呼び出しは２種類 """
  """ ①承認者が受領したメール内のリンクから②商人者のマイページから """
  """ ①申請者におけるAgreementConfirmView⇒②承認者へのメール⇒③メール内リンクから呼ばれる """
  """ 承認者はself.request.userとなる為、申請者のuser.idで管理する """
  """ 最終編集 250927 """

  model = CustomUser
  template_name = 'accounts/buyer/userAdd.html'
  form_class = UserAddForm_buyer
  #timeout_seconds = getattr(settings, 'ACTIVATION_TIMEOUT_SECONDS', 60*60*24)
  timeout_seconds = getattr(settings, 'ACTIVATION_TIMEOUT_SECONDS', 60*60*72)


  """ 承認者が受領したメール内のリンクから呼ばれる """
  def get(self, request, **kwargs):  #selfはメソッドを呼んだインスタンス自体

    try:
      token_applyUserID = kwargs.get('applyuser_id')    # URLから<token>（暗号化されたuser_id）を取り出す（kwargsはdict型）   
      applyUserID = loads(token_applyUserID, max_age=self.timeout_seconds)
      print(f'applyUserID={applyUserID} in def get in UserAddView_buyer')
      applyUser = usermodel.objects.get(pk=applyUserID)

      token_buyEntityID = kwargs.get('buyentity_id')    # URLから<token>（暗号化されたuser_id）を取り出す（kwargsはdict型）   
      buyEntityID = loads(token_buyEntityID, max_age=self.timeout_seconds)
      print(f'buyEntityID={buyEntityID} in def get in UserAddView_buyer')
      buyEntity = LegalEntity.objects.get(pk=buyEntityID)

      messages.add_message(request, messages.SUCCESS, 'あなたにユーザー追加の申請が行われました.')
 
      context = {
        'form': self.form_class(),
        'buyEntity': buyEntity,
        'applyUsers': applyUser,
      }
      return TemplateResponse(request, 'accounts/buyer/userAdd.html', context)

    except usermodel.DoesNotExist:
      message = "申し訳ありませんが、申請者の情報が確認できません。"
      messages.add_message(self.request, messages.WARNING, message) 
      return TemplateResponse(request,'accounts/buyer/login.html', {'form':MyLoginForm}) 

    except SignatureExpired:  # 期限切れ
      # この段階でCustomUserインスタンスが生成されている。
      # ★★ 250824 時間内に承認されない場合の対応追加（権限者、申請者に未処理であることをメール通知）
      return TemplateResponse(request,'accounts/buyer/login.html', {'form':MyLoginForm}) 

    except BadSignature:      # tokenが間違っている
      return HttpResponseBadRequest() 

    except: # マイページの設定画面から呼ばれる場合

      buyUser = usermodel.objects.select_related('entity').get(email=self.request.user)
      applyUsers = usermodel.objects.filter(entity=buyUser.entity, approvedStatus_int=1)

      print(f'buyEntity={buyUser.entity} in UserAddView_buyer')
      context = {
        'form': self.form_class(),
        'buyEntity': buyUser.entity,
        'applyUsers': applyUsers,
      }
      return TemplateResponse(request, 'accounts/buyer/userAdd.html', context)


  def post(self, request, **kwargs):

    form = self.form_class(request.POST)
    next = self.request.POST.get('next', '')

    print(f'next={next}')

    if next.find('ApproveUser') >= 0:
      print(f'pass1 ここ通っているかな in UserAddView_buyer')

      applyUser = usermodel.objects.get(pk=next.split('_')[1])
      buyEntity = LegalEntity.objects.get(pk=next.split('_')[2])

      char_CanApproveAll = self.request.POST.get('canApprove_all', None)
      char_CanApproveAdd = self.request.POST.get('canApprove_add', None)
      char_CanApproveQpay = self.request.POST.get('canApprove_qpay', None)

      if char_CanApproveAll == "True":
        applyUser.canApprove_all = True
        print(f'pass1 canApprove_all = True at def post, class UserAddView_buyer')
      else: applyUser.canApprove_all = False

      if char_CanApproveAdd == "True":
        applyUser.canApprove_add = True
        print(f'pass2 canApprove_add = True at def post, class UserAddView_buyer')
      else: applyUser.canApprove_add = False

      if char_CanApproveQpay == "True":
        applyUser.canApprove_qpay = True
        print(f'pass3 canApprove_qpay = True at def post, class UserAddView_buyer')
      else: applyUser.canApprove_qpay = False

      applyUser.entity = buyEntity
      applyUser.approvedStatus_int = 2

      applyUser.save()

      # ここからは申請者に参加が認められたことを伝えるメール送信
      current_site = get_current_site(self.request)
      domain = current_site.domain

      context = {
        'protocol': self.request.scheme,
        'domain': domain,
        #'applyuser_id': dumps(applyUser.pk),  # 申請者のuser.pkを維持する
        #'buyentity_id': dumps(buyEntity.pk),  # 申請者のentity.pkを維持する
      }
      subject = render_to_string('accounts/mail/buyUserAddReplyYes_subject.txt', context)
      message = render_to_string('accounts/mail/buyUserAddReplyYes_message.txt', context)

      from_email = 'shuichiro.tomihari.201604@gmail.com'
      recipient_list = [applyUser.email]
      #bcc =  ["toritoritorina@gmail.com"]  # BCCリスト
      email = EmailMessage(subject, message, from_email, recipient_list)
      email.send()

      return TemplateResponse(request, 'accounts/buyer/mypage.html')


    if next.find('RefuseUser') >= 0:

      # ★★ 250917 申請者に理由があり追加できないことを伝える
      # ★★ 250917時点で工事中

      applyUser = usermodel.objects.get(pk=next.split('_')[1])
      buyEntity = LegalEntity.objects.get(pk=next.split('_')[2])

      applyUser.approvedSatus_int = 3

      # 否認されたことを通知する
      current_site = get_current_site(self.request)
      domain = current_site.domain

      context = {
        'protocol': self.request.scheme,
        'domain': domain,
        #'applyuser_id': dumps(applyUser.pk),  # 申請者のuser.pkを維持する
        #'buyentity_id': dumps(buyEntity.pk),  # 申請者のentity.pkを維持する
      }
      subject = render_to_string('accounts/mail/buyUserAddReplyNo_subject.txt', context)
      message = render_to_string('accounts/mail/buyUserAddReplyNo_message.txt', context)

      from_email = 'shuichiro.tomihari.201604@gmail.com'
      recipient_list = [applyUser.email]
      #bcc =  ["toritoritorina@gmail.com"]  # BCCリスト
      email = EmailMessage(subject, message, from_email, recipient_list)
      email.send()

      return render(request, 'accounts/buyer/login.html', {'form':MyLoginForm})

    print(f'pass2 本当はここは通らないんだけど！ in UserAddView_buyer')


""" mypageから「ユーザーごとの権限」を確認・編集する """
class PermissionSetsView_buyer(generic.View):
# ★★★ 250828作成開始

  def get(self, request, **kwargs):  #selfはメソッドを呼んだインスタンス自体

    loginUser = usermodel.objects.get(email=self.request.user)
    entity = LegalEntity.objects.get(pk=loginUser.entity_id)
    print(f'loginUser.id={loginUser.id}')
    print(f'loginUser.entity_id={loginUser.entity_id}')
    entityUsers = entity.entity_users.all()

    context = {
      'loginUser': loginUser,
      'entity': entity,
      'entityUsers': entityUsers,
    }
    return TemplateResponse(request, 'accounts/buyer/permissionList.html', context)


  def post(self, request, **kwargs):  #selfはメソッドを呼んだインスタンス自体

    next1 = self.request.POST.get('next1', None)

    if next1 != None:

      if next1.find('Edit') >=0: # リストで選択されたユーザーの設定を表示する

        editedUser = usermodel.objects.get(pk=next1.split('_')[1])

        char_CanApproveAll = editedUser.canApprove_all
        char_CanApproveAdd = editedUser.canApprove_add
        char_CanApproveQpay = editedUser.canApprove_qpay

        print(f'char_CanApproveAll={char_CanApproveAll} after next1.find(Edit) in PermissionSetsView_buyer')
        print(f'char_CanApproveAdd={char_CanApproveAdd} after next1.find(Edit) in PermissionSetsView_buyer')
        print(f'char_CanApproveQpay={char_CanApproveQpay} after next1.find(Edit) in PermissionSetsView_buyer')
        print(f'editedUser.id={editedUser.id} after next1.find(Edit) in PermissionSetsView_buyer')

        init_dict = {
        }
        context = {
          'editedUser': editedUser,
          'form': PermissionUpdateForm_buyer(initial=init_dict),
        }
        return TemplateResponse(request, 'accounts/buyer/permissionUpdate.html', context)


    next2 = self.request.POST.get('next2', None)

    if next2 != None:

      if next2.find('PermissionSet') >= 0: # 選択されたユーザーの設定を更新
        print(f'pass1 if next2.find(PermissionSet) def post in PermissionSettinsView_buyer')

        editedUser = usermodel.objects.get(pk=next2.split('_')[1])

        char_CanApproveAll = self.request.POST.get('canApprove_all', None)
        char_CanApproveAdd = self.request.POST.get('canApprove_add', None)
        char_CanApproveQpay = self.request.POST.get('canApprove_qpay', None)

        """ 「すべて」権限者を一人は残すようにする """
        cnt_canApprove_all = usermodel.objects.filter(entity=editedUser.entity, canApprove_all=True).count()

        if editedUser.canApprove == True and cnt_canApprove_all == 1:
          if char_CanApproveAll != "True":
            message = "「すべて」の権限者が一人は必要です。"
            messages.add_message(self.request, messages.WARNING, message) 

            context = {
              'editedUser': editedUser,
              'form': PermissionUpdateForm_seller(),
            }
            return TemplateResponse(request, 'accounts/seller/permissionUpdate.html', context)


        if char_CanApproveAll == "True":
          editedUser.canApprove_all = True
          print(f'pass1 canApprove_all = True')
        else: editedUser.canApprove_all = False

        if char_CanApproveAdd == "True":
          editedUser.canApprove_add = True
          print(f'pass2 canApprove_add = True')
        else: editedUser.canApprove_add = False

        if char_CanApproveQpay == "True":
          editedUser.canApprove_qpay = True
          print(f'pass3 canApprove_qpay = True')
        else: editedUser.canApprove_qpay = False

        editedUser.save()

        print(f'char_CanApproveAll={char_CanApproveAll} after next2.find(PermissionSet) in PermissionSetsView_buyer')
        print(f'char_CanApproveAdd={char_CanApproveAdd} after next2.find(PermissionSet) in PermissionSetsView_buyer')
        print(f'char_CanApproveQpay={char_CanApproveQpay} after next2.find(PermissionSet) in PermissionSetsView_buyer')
        print(f'editedUser.id={editedUser.id} after next2.find(PermissionSet)')

        loginUser = usermodel.objects.get(email=self.request.user)
        entity = LegalEntity.objects.get(pk=loginUser.entity_id)
        entityUsers = entity.entity_users.all()

        context = {
          'loginUser': loginUser,
          'entityUsers': entityUsers,
        }
        return TemplateResponse(request, 'accounts/buyer/permissionList.html', context)


""" mypageから「ユーザーごとの権限」を確認・編集する """
class PermissionSetsView_seller(generic.View):
# ★★★ 2509025作成開始

  def get(self, request, **kwargs):  #selfはメソッドを呼んだインスタンス自体

    loginUser = usermodel.objects.get(email=self.request.user)
    entity = LegalEntity.objects.get(pk=loginUser.entity_id)
    print(f'loginUser.id={loginUser.id}')
    print(f'loginUser.entity_id={loginUser.entity_id}')
    entityUsers = entity.entity_users.all()

    context = {
      'loginUser': loginUser,
      'entity': entity,
      'entityUsers': entityUsers,
    }
    return TemplateResponse(request, 'accounts/seller/permissionList.html', context)


  def post(self, request):  #selfはメソッドを呼んだインスタンス自体

    next1 = self.request.POST.get('next1', None)

    if next1 != None:

      if next1.find('Edit') >=0: # リストで選択されたユーザーの設定を表示する

        editedUser = usermodel.objects.get(pk=next1.split('_')[1])

        char_CanApproveAll = editedUser.canApprove_all
        char_CanApproveAdd = editedUser.canApprove_add
        char_CanApproveQpay = editedUser.canApprove_qpay

        print(f'char_CanApproveAll={char_CanApproveAll} after next1.find(Edit) in PermissionSetsView_seller')
        print(f'char_CanApproveAdd={char_CanApproveAdd} after next1.find(Edit) in PermissionSetsView_seller')
        print(f'char_CanApproveQpay={char_CanApproveQpay} after next1.find(Edit) in PermissionSetsView_seller')
        print(f'editedUser.id={editedUser.id} after next1.find(Edit) in PermissionSetsView_seller')

        init_dict = {
        }
        context = {
          'editedUser': editedUser,
          'form': PermissionUpdateForm_seller(initial=init_dict),
        }
        return TemplateResponse(request, 'accounts/seller/permissionUpdate.html', context)


    next2 = self.request.POST.get('next2', None)
    form = PermissionUpdateForm_seller(self.request.POST)
    form.is_valid() # canApprove_all=Trueの人が一人はいるかバリデーションする

    if next2 != None:

      if next2.find('PermissionSet') >= 0: # 選択されたユーザーの設定を更新
        print(f'pass1 if next2.find(PermissionSet) def post in PermissionSettinsView_seller')

        char_CanApproveAll = self.request.POST.get('canApprove_all', None)
        char_CanApproveAdd = self.request.POST.get('canApprove_add', None)
        char_CanApproveQpay = self.request.POST.get('canApprove_qpay', None)

        """ 「すべて」権限者を一人は残すようにする """
        cnt_canApprove_all = usermodel.objects.filter(entity=editedUser.entity, canApprove_all=True).count()

        if editedUser.canApprove == True and cnt_canApprove_all == 1:
          if char_CanApproveAll != "True":
            message = "「すべて」の権限者が一人は必要です。"
            messages.add_message(self.request, messages.WARNING, message) 

            context = {
              'editedUser': editedUser,
              'form': PermissionUpdateForm_seller(),
            }
            return TemplateResponse(request, 'accounts/seller/permissionUpdate.html', context)


        if char_CanApproveAll == "True":
          editedUser.canApprove_all = True
          print(f'pass1 canApprove_all = True')
        else: editedUser.canApprove_all = False

        if char_CanApproveAdd == "True":
          editedUser.canApprove_add = True
          print(f'pass2 canApprove_add = True')
        else: editedUser.canApprove_add = False

        if char_CanApproveQpay == "True":
          editedUser.canApprove_qpay = True
          print(f'pass3 canApprove_qpay = True')
        else: editedUser.canApprove_qpay = False

        editedUser.save()

        print(f'char_CanApproveAll={char_CanApproveAll} after next2.find(PermissionSet) in PermissionSetsView_seller')
        print(f'char_CanApproveAdd={char_CanApproveAdd} after next2.find(PermissionSet) in PermissionSetsView_seller')
        print(f'char_CanApproveQpay={char_CanApproveQpay} after next2.find(PermissionSet) in PermissionSetsView_seller')
        print(f'editedUser.id={editedUser.id} after next2.find(PermissionSet)')

        loginUser = usermodel.objects.get(email=self.request.user)
        entity = LegalEntity.objects.get(pk=loginUser.entity_id)
        entityUsers = entity.entity_users.all()

        context = {
          'loginUser': loginUser,
          'entityUsers': entityUsers,
        }
        return TemplateResponse(request, 'accounts/seller/permissionList.html', context)


class EntityCreateView_seller(generic.CreateView):

  """（ビューにおいて）GETリクエストを受け取ったときに呼び出される（実践Django P121）"""
  """ 処理：ゲストに送られたメールのURLをクリックされた時点で呼ばれる """

  """ def getでは、メールから本登録に進む場合に呼ばれ、
      ①新規ゲスト登録か、②既存ゲストにユーザー追加を選択するテンプレートを送る """

  form_class = EntityCreateForm_seller
  template_name = 'accounts/seller/entityCreate.html'
  timeout_seconds = getattr(settings, 'ACTIVATION_TIMEOUT_SECONDS', 60*60*72)

  dict_sellEntityName = dict((f, f) for idx, f in enumerate(LegalEntity.objects.filter(type1=2,type2=2).values_list('entityName', flat=True), 1))
  # ゲストの場合は、個人と法人があるため抽出条件に「type2=2」とする


  def get(self, request, **kwargs):  #selfはメソッドを呼んだインスタンス自体
  
    try:
      # メール内のURLから<token>（暗号化されたuser_id）を取り出す（kwargsはdict型）
      token = kwargs.get('token', None)
      user_pk = loads(token, max_age=self.timeout_seconds)
      user = usermodel.objects.get(pk=user_pk)
      print(f'token = {token}, user_pk = {user_pk} in def get of EntityCreateView_seller')

    except usermodel.DoesNotExist:
      
      usermodel.objects.get(email=self.request.user).delete()
      message = "申し訳ありませんが、ユーザー情報が確認できません"
      messages.add_message(self.request, messages.WARNING, message) 
      return TemplateResponse(request,'accounts/seller/login.html', {'form':MyLoginForm}) 

    except SignatureExpired:  # 時間切れ
      # ★★ 250824 テスト未了。メルアド重複で登録不可にならないようUserオブジェクトを削除
      usermodel.objects.get(email=self.request.user).delete()
      message = "規定の時間を超えたため、再度、お手続きをお願いいたします"
      messages.add_message(self.request, messages.WARNING, message)
      return TemplateResponse(request,'accounts/seller/login.html', {'form':MyLoginForm}) 

    except BadSignature:      # tokenが間違っている
      return HttpResponseBadRequest()
    

    # 仮登録が完了し、メールからのリンクにより本登録を開始した時点
    user.is_active = True
    user.save()

    print(f'ここ来てる1 self.request.user={self.request.user} email={user.email} type2={user.type2}（get in class EntityCreateView_seller）')

    if user.type2 == 1: # 個人の場合

      context = {
        'flag_step': 1,
        'user': user,
        'form': self.form_class(),
      }
      # ★★ userの住所を登録するようにする 25/09/23

      return TemplateResponse(self.request, 'accounts/seller/entityCreate.html', context)


    if user.type2 == 2: # 法人の場合

      init_dict = {
        'email': user.email,
        #'userName': '',
        'tel_user': "",
      }
      context = {
        'flag_step': 1,
        'user': user,
        'form': EntitySetForm_seller(initial=init_dict),
        'temporal_sellEntityName': "",
        # コメント(25/06/08)：Selectボックスで未選択であることを示す。選択後はページ移動でデータ保持するために使う
        'dict_sellEntityName': self.dict_sellEntityName,
        'json_sellEntityName': json.dumps(self.dict_sellEntityName),
      }
      print(f'ここ来てる2 self.request.user={self.request.user} email={user.email} type2={user.type2}（get in class EntityCreateView_seller）')
     
      return TemplateResponse(request, 'accounts/seller/entitySet.html', context)


  def post(self, request, *args, **kwargs):

    #user = usermodel.objects.get(email=self.request.user) 

    next1_indiv = self.request.POST.get('next1_indiv', None)

    next1_corp = self.request.POST.get('next1_corp', None)
    next2_corp = self.request.POST.get('next2_corp', None)
    # next1_corpは、新規entityを登録する際の処理種別
    # next2_corpは、既存entityにuser追加する際の処理種別


    """ 個人用の処理 """

    if next1_indiv != None:

      user = usermodel.objects.get(pk=next1_indiv.split('_')[1]) 
      form = self.form_class(request.POST)
      
      if next1_indiv.find('ToConfirm') >= 0:

        if form.is_valid():
        # 下記①、②、③の順で実行
        # ①.is_valid()、②フォームでのclean、clean_<field>、③form.cleaned_data[]に格納

          cleaned_data = form.cleaned_data 
    
          init_dict = {
            'lastName' : cleaned_data['lastName'],
            'firstName' : cleaned_data['firstName'],
            'lastName_kana' : cleaned_data['lastName_kana'],
            'firstName_kana' : cleaned_data['firstName_kana'],

            'tel_user' : cleaned_data['tel_user'],
            'zip_user' : cleaned_data['zip_user'],
          }
          context = {
            'flag_step': 2,
            'user': user,
            'form' : self.form_class(initial=init_dict),
          }
          return TemplateResponse(
            self.request, 'accounts/seller/entityCreate.html', context)
        

        else: #バリデーションエラーの時に通る

          print(f'ここ来てる3（def post after if not form.is_valid in class EntityCreateView_seller）')
          return TemplateResponse(self.request, 'accounts/seller/entityCreate.html',
            {'flag_step': 1, 'user':user, 'form':form})


      if next1_indiv.find('ToSave') >= 0: # 確認した内容をデータベースに登録

        user.userName = \
          self.request.POST.get('lastName') + ' ' + self.request.POST.get('firstName')
        user.userName_kana = \
          self.request.POST.get('lastName_kana') + ' ' + self.request.POST.get('firstName_kana')

        user.tel_user = self.request.POST.get('tel_user')
        user.zip_user = self.request.POST.get('zip_user')

        entity = LegalEntity.objects.create()

        entity.entityName = \
          self.request.POST.get('lastName') + ' ' + self.request.POST.get('firstName')
        #　entity.entityName = form.entityName 
        # 上式はエラー（'EntityCreateForm_buyer' object has no attribute 'entityName'）

        entity.tel_entity = self.request.POST.get('tel_user')
        entity.zip_entity = self.request.POST.get('zip_user')

        # type1、type2はCustomUserとLegalEntityで双方で管理
        # type1；発注者／受注者、type2：個人／法人
        entity.type1 = user.type1  
        entity.type2 = user.type2

        entity.save()

        user.entity = entity

        user.canApprove_all = False
        user.canApprove_add = False
        user.canApprove_qpay = False
        # 【留意】 「False」とし、AgreementConfirmView_sellerにおいて、
        # 利用規約に同意した時点（二人目以降は追加承認がなされた後）に
        # 各権限を「True」、approvedStatus_int=2とする

        # ★★ 2500927 ゲストの場合はQneeの承認はなし（パートナーと異なる）

        user.is_active = True

        user.save()

        print(f'request.user.get_username={request.user.get_username} type2={user.type2}（def post ==confirm after form.is_valid in EntityCreateView_seller）')
        print(f'entity.id = {entity.id}（post ==create after form.is_valid in EntityCreateView_seller）')

        context = {
          'flag_step': 1, # agreementConfirm.htmlのflag
          'user': user,
          'entity': entity,
        }
        return render(self.request, 'accounts/seller/agreementConfirm.html', context)


      # データ確認画面から入力画面に戻る時の処理 2025/02/14
      if next1_indiv.find('BackToInput') >= 0:

        context = {
          'flag_step': 1,
          'user': user,
          'form': form,
        }
        return TemplateResponse(self.request, 'accounts/seller/entityCreate.html', context)


    """ 法人用の処理 """
    if next1_corp != None:

      user = usermodel.objects.get(pk=next1_corp.split('_')[1]) 
      
      # ★★ 250930 これは新規ゲスト作成のときにいる？
      #form = self.form_class(request.POST)

      """ （法人用）新規のゲスト登録をする処理 """
      if next1_corp.find('ToEntityCreate') >= 0:

        init_dict = {}
        context = {
          'flag_step': 1,
          'user': user,
          'form': self.form_class(initial=init_dict),
        }
        # ★★ Entityの住所を登録するようにする 25/09/23

        return render(self.request, 'accounts/seller/entityCreate.html', context)


      form = self.form_class(request.POST, userType2=user.type2)

      if next1_corp.find('ToConfirm') >= 0:

        if form.is_valid():
        # 下記①、②、③の順で実行
        # ①.is_valid()、②フォームでのclean、clean_<field>、③form.cleaned_data[]に格納

          cleaned_data = form.cleaned_data 
          init_dict = {
            'entityName' : cleaned_data['entityName'],
            'representitive' : cleaned_data['representitive'],
            'tel_entity' : cleaned_data['tel_entity'],
            'zip_entity' : cleaned_data['zip_entity'],
            'address1' : cleaned_data['address1'],
            'address2' : cleaned_data['address2'],
            'address3' : cleaned_data['address3'],

            'lastName' : cleaned_data['lastName'],
            'lastName_kana' : cleaned_data['lastName_kana'],
            'firstName' : cleaned_data['firstName'],
            'firstName_kana' : cleaned_data['firstName_kana'],
            'tel_user' : cleaned_data['tel_user'],
            'department' : cleaned_data['department'],
            'title' : cleaned_data['title'],
          }
          context = {
            'flag_step': 2,
            'user': user,
            'form' : self.form_class(initial=init_dict),
          }         
          return TemplateResponse(
            self.request, 'accounts/seller/entityCreate.html', context)
        

        else: #バリデーションエラーの時に通る

          print(f'pass3 form.errors={form.errors}（def post if not form.is_valid in class EntityCreateView_seller）')
          return TemplateResponse(self.request, 'accounts/seller/entityCreate.html',
            {'flag_step': 1, 'user':user, 'form':form})


      if next1_corp.find('ToSave') >= 0: # 確認した内容をデータベースに登録

        entity = LegalEntity.objects.create()

        # ★★ 250923 法人の処理として記載。このうえに個人の処理を入れる
        entity.entityName = self.request.POST['entityName']
        #　entity.entityName = form.entityName 
        # 上式はエラー（'EntityCreateForm_buyer' object has no attribute 'entityName'）

        entity.representitive = self.request.POST.get('representitive')
        entity.tel_entity = self.request.POST.get('tel_entity')
        entity.zip_entity = self.request.POST.get('zip_entity')
        entity.address1 = self.request.POST.get('address1')
        entity.address2 = self.request.POST.get('address2')
        entity.address3 = self.request.POST.get('address3')
        
        # type1、type2はCustomUserとLegalEntityで双方で管理
        # type1；発注者／受注者、type2：個人／法人
        entity.type1 = user.type1  
        entity.type2 = user.type2

        entity.save()

        user.userName = \
          self.request.POST.get('lastName') + ' ' + self.request.POST.get('firstName')
        user.userName_kana = \
          self.request.POST.get('lastName_kana') + ' ' + self.request.POST.get('firstName_kana')

        user.tel_user = self.request.POST.get('tel_user')
        user.department = self.request.POST.get('department')
        user.title = self.request.POST.get('title')

        user.entity = entity

        user.canApprove_all = False
        user.canApprove_add = False
        user.canApprove_qpay = False
        # 【留意】 「False」とし、AgreementConfirmView_sellerにおいて、
        # パートナ一１人目の場合は「True」、２人目以降は権限者が「True/False」を設定

        # ★★ 25009254 Qneeはゲストに対しては承認しない
        # ★★ この部分はパートナーと異なる

        user.is_active = True
        
        user.save()

        print(f'request.user.get_username={request.user.get_username} type2={user.type2}（def post ==confirm after form.is_valid in EntityCreateView_seller）')
        print(f'entity.id = {entity.id}（post ==create after form.is_valid in EntityCreateView_seller）')

        context = {
          'flag_step': 1, # agreementConfirm.htmlのflag
          'user': user,
          'entity': entity,
        }
        return render(self.request, 'accounts/seller/agreementConfirm.html', context)


      # データ確認画面から入力画面に戻る時の処理 2025/02/14
      if next1_corp.find('BackToInput') >= 0:

        user = usermodel.objects.get(pk=next1_corp.split('_')[1])

        context = {
          'flag_step': 1,
          'user': user,
          'form': form,
        }
        return TemplateResponse(self.request, 'accounts/seller/entityCreate.html', context)


    """ （法人用）登録済みゲストに追加する処理 """

    if next2_corp != None:

      if next2_corp.find('ToConfirm') >= 0:  # 登録済みパートナーにユーザー追加

        form = EntitySetForm_seller(request.POST) # form_class=EntityCreateForm_seller
        user = usermodel.objects.get(pk=next2_corp.split('_')[1])

        # ★★ 250914 バリデーション（エンティティが選ばれているかを含む）を対応
        if form.is_valid():
        # 下記①、②、③の順で実行
        # ①.is_valid()、②フォームでのclean、clean_<field>、③form.cleaned_data[]に格納

          #temporal_sellEntityName = self.request.POST.get('name_SellerSelect', None)
          #sellEntity = LegalEntity.objects.get(entityName=temporal_sellEntityName)
 
          cleaned_data = form.cleaned_data 
          entityName = cleaned_data['entityName']
          print(f'cleaned_data[entityName]={entityName}')
          entity = LegalEntity.objects.get(entityName=cleaned_data['entityName'])

          init_dict = {
            #'entityName' : entity.entityName,　テンプレートにはentityで渡す
            'lastName' : cleaned_data['lastName'],
            'lastName_kana' : cleaned_data['lastName_kana'],
            'firstName' : cleaned_data['firstName'],
            'firstName_kana' : cleaned_data['firstName_kana'],
            'tel_user' : cleaned_data['tel_user'],
            'department' : cleaned_data['department'],
            'title' : cleaned_data['title'],
          }
          context = {
            'flag_step': 2,
            'user': user,
            'entity': entity,
            'form' : EntitySetForm_seller(initial=init_dict),
          }
          return render(self.request, 'accounts/seller/entitySet.html', context)  # 確認画面に行く

        else: #バリデーションエラーの時に通る

          print(f'ここ来てる4（def post after if not form.is_valid in class EntityCreateView_seller）')
          entityName = self.request.POST.get('entityName')
          entity = LegalEntity.objects.get(entityName=entityName)


          context = {
            'flag_step': 1,
            'selectedValue': 'AddToEntity',
            'user': user,
            'entity': entity,
            'form' : form,
            'temporal_sellEntityName': entity.entityName,
            # コメント(25/06/08)：Selectボックスで未選択であることを示す。選択後はページ移動でデータ保持するために使う
            'dict_sellEntityName': self.dict_sellEntityName,
            'json_sellEntityName': json.dumps(self.dict_sellEntityName),

          }
          return TemplateResponse(self.request, 'accounts/seller/entitySet.html', context)



      if next2_corp.find('BackToInput') >= 0:

        form = EntitySetForm_seller(request.POST)  # form_class=EntityCreateForm_seller

        user = usermodel.objects.get(pk=next2_corp.split('_')[1]) 
        entity = LegalEntity.objects.get(pk=next2_corp.split('_')[2])

        context = {
          'flag_step': 1,
          'user': user,
          'entity': entity,
          'form': form,
          'temporal_sellEntityName': entity.entityName,
          # Note(25/06/08)：選択済み内容をページ移動後も維持するために使う（初期は空欄）
          'dict_sellEntityName': self.dict_sellEntityName,
          'json_sellEntityName': json.dumps(self.dict_sellEntityName),
        }
        return TemplateResponse(request, 'accounts/seller/entitySet.html', context)


      if next2_corp.find('ToSave&Apply') >= 0: # entitySet.htmlの「flag_step==2」の後（登録データ確認後）

        form = EntitySetForm_seller(request.POST)  # form_class=EntityCreateForm_buyer

        user = usermodel.objects.get(pk=next2_corp.split('_')[1]) 
        entity = LegalEntity.objects.get(pk=next2_corp.split('_')[2])

        #user.userName = self.request.POST.get('userName', None)
        user.userName = \
          self.request.POST.get('lastName') + ' ' + self.request.POST.get('firstName')
        user.userName_kana = \
          self.request.POST.get('lastName_kana') + ' ' + self.request.POST.get('firstName_kana')

        user.tel_user = self.request.POST.get('tel_user')
        user.department = self.request.POST.get('department')
        user.title = self.request.POST.get('title')

        print(f'user.department={user.department}')
        print(f'user.title={user.title}')

        # user.entity = entity # ★★ 250824 ユーザー追加が承認された時点で対応

        user.save()

        context = {
          'flag_step': 1,
          'user': user,
          'entity': entity,
        }
        return render(self.request, 'accounts/seller/agreementConfirm.html', context)

      print(form.errors)
      print(f'ここまで来てる6 例外（post in class EntityCreateView_seller）')

  #def form_valid(self, form):
  #  return super().form_valid(form)
  #
  #def form_invalid(self, form):
  #  print(f'ここまで来てる4（form_invalid in class EntityCreateView_seller）')
  #  print(form.errors)
  #  #form.instance.user = self.request.user
  #  return super().form_invalid(form)

  #def get_form_kwargs(self):
  #  print(f'pass4 def get_form_kwargs in EntityCreateView_seller')
  #  kwargs = super(EntityCreateView_seller, self).get_form_kwargs()
  #  user = usermodel.objects.get(email=self.request.user)
  #  userType2 = 2
  #  print(f'userType2={userType2} def get_form_kwargs in EntityCreateView_seller')
  #  kwargs.update({'userType2': userType2})
  #
  #
  # return kwargs


"""25/01/10 利用規約に同意するためのビュー"""
class AgreementConfirmView_seller(generic.UpdateView):

  model = LegalEntity
  form_class = AgreementConfirmForm_seller
  template_name = 'accounts/seller/agreementConfirm.html'

  ## このgetメソッドは開発時に利用するためのもの　24/01/08
  ## 通常時は、EntityCreateViewのpostメソッド内から呼び出される
  def get(self, request, **kwargs):  #selfはメソッドを呼んだインスタンス自体
  
    try:
      user = usermodel.objects.get(pk=self.kwargs['user_id'])
      entity = LegalEntity.objects.get(pk=self.kwargs['entity_id'])

    except usermodel.DoesNotExist:
      message = "申し訳ありませんが、ユーザー情報が確認できません。"
      messages.add_message(self.request, messages.INFO, message) 
      return redirect('accounts: login_seller') 

    context = {
      'flag_step': 1,
      'user': user,
      'entity': entity,
    }
    return TemplateResponse(request, 'accounts/seller/agreementConfirm.html', context) 


  def post(self, request, *args, **kwargs):

    checkValue = request.POST.get('checkConsent', None)  
    buttonValue = self.request.POST.get('next', None) 
    print(f'entity.membershipConsent_boolean={checkValue}')

    if buttonValue.find('ToAgree') >= 0:

      print(f'buttonValue={buttonValue}')
      applyUser = usermodel.objects.get(pk=buttonValue.split('_')[1]) 
      sellEntity = LegalEntity.objects.get(pk=buttonValue.split('_')[2])

      if checkValue == 'ToAgree':  # 規約同意にチェックされた場合

        sellEntity.membershipConsent_boolean = True
        sellEntity.membershipConsent_at = timezone.now()
        sellEntity.joined_at = timezone.now()
        #entity.email = user.email

        sellEntity.save()

        if applyUser.type2 == 1: # 個人ゲストの場合は承認受けず

          applyUser.canApprove_all = True
          applyUser.canApprove_add = True
          applyUser.canApprove_qpay = True

          applyUser.approvedStatus_int = 2

          applyUser.entity = sellEntity
          applyUser.save()

          return TemplateResponse(request,'accounts/seller/login.html', {'form':MyLoginForm}) 


        if applyUser.type2 == 2:

          """ ★★ 25/06/14追加（テストは未済み） 
             「canApprove_all=True」「canApprove_add=True」の人に承認依頼する """
          approvers = usermodel.objects.filter(
            Q(entity_id=sellEntity.id) & (Q(canApprove_all=True) | Q(canApprove_add=True)))
    
          if approvers.first() is None: # 参加を承認するユーザーがいない場合（一人目のユーザーの場合）
          
            applyUser.canApprove_all = True
            applyUser.canApprove_add = True
            applyUser.canApprove_qpay = True

            applyUser.approvedStatus_int = 2

            applyUser.entity = sellEntity
            applyUser.save()

            return TemplateResponse(request,'accounts/seller/login.html', {'form':MyLoginForm}) 


          else:   # ゲスト内の権限者に参加申請する

            current_site = get_current_site(self.request)
            domain = current_site.domain

            for approver in approvers:

              context1 = {
                'protocol':  self.request.scheme,
                'domain': domain,
                'token1': dumps(applyUser.pk),
                'token2': dumps(sellEntity.pk),
                'user': approver,
              }
              subject = render_to_string('accounts/mail/sellUserAddApply_subject.txt', context1)
              message = render_to_string('accounts/mail/sellUserAddApply_message.txt', context1)

              #approver.email_user(subject, message)

              from_email = 'shuichiro.tomihari.201604@gmail.com'
              recipient_list = [approver['email']]
              #bcc =  ["toritoritorina@gmail.com"]  # BCCリスト
              email = EmailMessage(subject, message, from_email, recipient_list)
              email.send()

              #messages.add_message(request, messages.SUCCESS, 'ユーザーの追加登録の申請を行いました.')
              #テンプレート上にメッセージがでるので不要

              print(f'pass1 approver.email={approver.email}（EntityCreateView_seller, post, checkbox==agree)')

              context2 = {'flag_step': 2,}
              return TemplateResponse(self.request, 'accounts/seller/agreementConfirm.html', context2)

        else:  # 同意チェックがされていない場合（チェックしていない場合はボタンが押せない）

          messages.error(request, "「利用規約に同意します」のチェックボックスにチェックがありません。", extra_tags='no check')

          context = {
            'flag_step': 1,
            'applyUser': applyUser,
            'sellEntity': sellEntity,
          }
          return render(self.request, 'accounts/seller/agreementConfirm.html', context)


    if buttonValue.find('ToDisagree') >= 0:

      messages.error(request, "「同意しない」のボタンが押されました。", extra_tags='no check')

      applyUser = usermodel.objects.get(pk=buttonValue.split('_')[1]) 
      sellEntity = LegalEntity.objects.get(pk=buttonValue.split('_')[2])

      context = {
        'flag_step': 1,
        'applyUser': applyUser,
        'sellEntity': sellEntity,
        }
      return render(self.request, 'accounts/seller/agreementConfirm.html', context)

    return HttpResponseBadRequest()  # 基本的にはここには来ない


class UserAddView_seller(generic.CreateView, LoginRequiredMixin):
# パートナー内でユーザーを追加するときの承認処理を行う

  model = CustomUser
  template_name = 'accounts/seller/userAdd.html'
  form_class = UserAddForm_seller
  #timeout_seconds = getattr(settings, 'ACTIVATION_TIMEOUT_SECONDS', 60*60*24)
  timeout_seconds = getattr(settings, 'ACTIVATION_TIMEOUT_SECONDS', 60*60*72)

  # 250824作成 承認者が受領したメール内のリンクからアクセスされる
  # ①申請者におけるAgreementConfirmView⇒②承認者へのメール⇒③メール内リンクから呼ばれる
  # self.request.userが承認者となるため、申請者のuser.idを維持する
  def get(self, request, **kwargs):  #selfはメソッドを呼んだインスタンス自体
    
    try:
      token1 = kwargs.get('token1', None)   # URLから<token>（暗号化されたuser_id）を取り出す（kwargsはdict型）
      token2 = kwargs.get('token2', None)

      applyUser_id = loads(token1, max_age=self.timeout_seconds)
      sellEntity_id = loads(token2, max_age=self.timeout_seconds)

      applyUser = usermodel.objects.get(pk=applyUser_id)
      sellEntity = LegalEntity.objects.get(pk=sellEntity_id)

    except usermodel.DoesNotExist:
      message = "申し訳ありませんが、申請者の情報が確認できません。"
      messages.add_message(self.request, messages.INFO, message) 
      return redirect('accounts: login_seller') 

    except SignatureExpired:  # 期限切れ
      # この段階でCustomUserインスタンスが生成されている。
      # ★★ 250824 時間内に承認されない場合の対応追加（権限者、申請者に未処理であることをメール通知）
      return redirect('account:login_seller')

    except BadSignature:      # tokenが間違っている
      return HttpResponseBadRequest() 

    context = {
      'form': self.form_class(),
      'applyUser': applyUser,
      'sellEntity': sellEntity,
    }
    return TemplateResponse(request, 'accounts/seller/userAdd.html', context)


  def post(self, request, **kwargs):

    next = self.request.POST.get('next', None)
    if next.find('ApproveUser') >= 0:

      applyUser = usermodel.objects.get(pk=next.split('_')[1])
      sellEntity = LegalEntity.objects.get(pk=next.split('_')[2])

      applyUser.canApprove_all = self.request.POST.get('canApprove_all', None)
      applyUser.canApprove_add = self.request.POST.get('canApprove_add', None)
      applyUser.canApprove_qpay = self.request.POST.get('canApprove_qpay', None)
      applyUser.entity = sellEntity
      applyUser.approvedStatus_int = 2    # パートナー内でユーザー追加が承認された時点

      applyUser.save()
      
      return TemplateResponse(request, 'accounts/seller/mypage.html')


    if next.find('RefuseUser') >= 0:

      applyUser = usermodel.objects.get(pk=next.split('_')[1])
      sellEntity = LegalEntity.objects.get(pk=next.split('_')[2])

      applyUser.entity = sellEntity
      applyUser.approvedStatus_int = 3

      applyUser.save()

      init_dict = {
        'canApprove_all': self.request.POST.get('canApprove_all', None),
        'canApprove_add': self.request.POST.get('canApprove_add', None),
        'canApprove_qpay': self.request.POST.get('canApprove_qpay', None),
      }
      form = self.form_class(initial=init_dict) 

      context = {
        'form': form,
        'applyUser': applyUser,
        'sellEntity': sellEntity,
      }     
      return TemplateResponse(request, 'accounts/seller/userAdd.html', context)


"""ログインした後に呼ばれるビュー"""
class MyPageView_admin(generic.DetailView):

  model = CustomUser
  template_name = "accounts/admin/mypage.html"

  
  def get(self, request, *args, **kwargs):
    if request.method != "GET":
      return HttpResponseNotAllowed("GET")

  
    # 「URLパラメーターがある場合」と「ない場合（ログインから）」に分ける   
    try:
      user = usermodel.objects.get(pk=self.kwargs['user_id'])
    except:
      print(f'request.user={request.user} def get in MyPageView_admin')
      user = usermodel.objects.get(email=self.request.user) 
  
    if user.type1 != 3:

      if user.type1 == 1:
        message = "パートナーで登録されています。パートナーでログインして下さい。"
        messages.add_message(request, messages.INFO, message) 
        logout(request)
        return HttpResponseRedirect(reverse('accounts:login', 1))

      if user.type1 == 2:
        message = "ゲストで登録されています。ゲストでログインして下さい。"
        messages.add_message(request, messages.INFO, message) 
        logout(request)
        return HttpResponseRedirect(reverse('accounts:login', 2))

    return TemplateResponse(
      request, "accounts/admin/mypage.html", { "user": user, }) 


  def post(self, request, *args, **kwargs):

    # 「URLパラメーターがある場合」と「ない場合（ログインから）」に分ける   
    try:
      self.object = usermodel.objects.get(pk=self.kwargs['user_id'])
    except:
      self.object = usermodel.objects.get(email=self.request.user) 
      print(f'request.user={request.user} def get in MyPageView_buyer')
    
    next = self.request.POST.get('next', '')
    if next == 'approve_qpay':
      form = TxApproveForm_buyer()

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
class MyPageView_buyer(generic.DetailView, LoginRequiredMixin):

  model = CustomUser
  template_name = "accounts/buyer/mypage.html"
  form_class = MyPageForm_buyer
  
  def get(self, request, *args, **kwargs):

    if request.method != "GET":
      return HttpResponseNotAllowed("GET")

    # 「URLパラメーターがある場合」と「ない場合（ログインから）」に分ける   
    if 'user_id' in self.kwargs:
      user = usermodel.objects.get(pk=self.kwargs['user_id'])
    else:
      if self.request.user.is_authenticated:
        print(f'request.user={self.request.user} def get in MyPageView_buyer')
        user = usermodel.objects.get(email=self.request.user) 
      else:
        print(f'ログイン出来てません。 def get in MyPageView_buyer')

    if user.type1 != 1:

      if user.type1 == 2:
        message = "ゲストで登録されています。ゲストでログインして下さい。"
        messages.add_message(request, messages.INFO, message) 
        logout(request)
        return TemplateResponse(request, "accounts/seller/login.html", {'form':MyLoginForm})

      if user.type1 == 3:
        message = "スタッフで登録されています。スタッフでログインして下さい。"
        messages.add_message(request, messages.INFO, message) 
        logout(request)
        return TemplateResponse(request, "accounts/admin/login.html", {'form':MyLoginForm})

    print(f'user.entity_id={user.entity_id} def get in MyPageView_buyer')

    
    print(f'request.user={request.user} def get in TxApproveView_buyer')
    entity = LegalEntity.objects.get(pk=user.entity_id)
    
    # 前払い、ユーザー追加の未処理（承認待ち）データを抽出
    cnt_toBeApproved_qpay = QpayTx.objects.filter(buyEntity=user.entity, txStatus_int=1).count()
    cnt_toBeApproved_add = usermodel.objects.select_related('entity').filter(
      entity=user.entity, approvedStatus_int=1).count()
    print(f'cnt_toBeApproved_qpay={cnt_toBeApproved_qpay}')

    today = date.today()
    year = today.year; month = today.month #; day = today.day

    first_of_month = date(year, month, 1)
    first_of_next_month = first_of_month + relativedelta(months=+1)
    first_of_month_after_next = first_of_month + relativedelta(months=+2)

    query_tx = QpayTx.objects.filter(
      buyEntity=entity,
      txStatus_int = 2,
      exPayment_date__gte = first_of_next_month,
      exPayment_date__lt = first_of_month_after_next)
    
    payment_date = first_of_next_month
    payment_count = query_tx.count
    payment_amount = query_tx.aggregate(Sum('approved_amount'))

    return TemplateResponse(
      request, "accounts/buyer/mypage.html",
      { 
        "user": user,
        "entity": entity,
        "payment_date": payment_date,
        "payment_count": payment_count,
        "payment_amount": payment_amount,
        "cnt_toBeApproved_qpay": cnt_toBeApproved_qpay, 
        "cnt_toBeApproved_add": cnt_toBeApproved_add,
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
      form = TxApproveForm_buyer()

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
  template_name = "accounts/seller/mypage.html"
  form_class = MyPageForm_seller
  
  def get(self, request, *args, **kwargs):

    if request.method != "GET":
      return HttpResponseNotAllowed("GET")

    # 後者の場合は、request.userがAdminから切り替わっていない場合がある！
    # 前のページの情報は認識できないのか？  

    # 「URLパラメーターがある場合」と「ない場合（ログインから）」に分ける   
    try:
      user = usermodel.objects.get(pk=self.kwargs['user_id'])
    except:
      print(f'request.user={request.user} def get in MyPageView_seller')
      user = usermodel.objects.get(email=self.request.user) 

    if user.type1 != 2:

      if user.type1 == 1:
        message = "パートナーで登録されています。パートナーでログインして下さい。"
        messages.add_message(request, messages.INFO, message) 
        logout(request)
        return TemplateResponse(request, "accounts/buyer/login.html", {'form':MyLoginForm})

      if user.type1 == 3:
        message = "スタッフで登録されています。スタッフでログインして下さい。"
        messages.add_message(request, messages.INFO, message) 
        logout(request)
        return TemplateResponse(request, "accounts/admin/login.html", {'form':MyLoginForm})


    # ★error 個人で登録している人にエンティティが登録されていない 25/01/14
    # ★task ①複数のパートナーと仕事をするとき、②個人で仮登録しか終わってないとき 25/01/14

    # print(f'self.object.entityName={self.object.entityName} def get in MyPageView_seller')
    # entity = LegalEntity.objects.get(email=self.request.user, entityName=self.object.entityName)

    return TemplateResponse(request, "accounts/seller/mypage.html", { "user": user }) 


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

  template_name = 'accounts/buyer/contact.html'
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

  template_name = 'accounts/seller/contact.html'
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
  
class BankAccount:

  def MakeBanksBranchesDict():

    dict_banks = {} 
    dict_bankCode_branches = {} 

    for bankCode in Bank.all:
      dict_banks.update({bankCode : Bank[bankCode].name})

      dict_branches = {} 
      for branchCode in Bank[bankCode].branches:
        dict_element = {
        'name': Bank[bankCode].branches[branchCode].name,
        'kana': Bank[bankCode].branches[branchCode].kana,
        'hira': Bank[bankCode].branches[branchCode].hira,
        'roma': Bank[bankCode].branches[branchCode].roma,
        }
        dict_branches.update({branchCode : dict_element})

      dict_bankCode_branches.update({bankCode : dict_branches})

    return dict_bankCode_branches


  def MakeBanksDict():

    dict_banks = {} 

    for bankCode in Bank.all:
      dict_element = {
        'name': Bank[bankCode].name,
        'kana': Bank[bankCode].kana,
        'hira': Bank[bankCode].hira,
        'roma': Bank[bankCode].roma,
      }
      dict_banks.update({bankCode : dict_element})

      #dict_banks = sorted(dict_banks.items)
    if bankCode == '0001':
      print(f'dict_banks={dict_banks}')

    return dict_banks
  

  def BankSearch(keyword):
  
    keyword = unicodedata.normalize('NFKC', keyword)

    dict_MatchedBank = {}
    
    for bankCode in Bank.all:
      #bank = Bank[code]
      bank = Bank[bankCode]

      if re.match(keyword, bankCode) or \
        bank.name.find(keyword) >= 0 or \
        bank.kana.find(keyword) >= 0 or \
        bank.hira.find(keyword) >= 0 or \
        bank.roma.find(keyword) >= 0: 

        dict_MatchedBank.update({ bankCode: bank.name })

    return dict_MatchedBank
  

  def BranchSearch(bankCode, keyword):
    
    keyword = unicodedata.normalize('NFKC', keyword)
    dict_MatchedBranch = {}
    
    branches = Bank[bankCode].branches

    for code in branches:
      #bank = Bank[code]
      branch = branches[code]

      if re.match(keyword, code) or\
        branch.name.find(keyword) >= 0 or\
        branch.kana.find(keyword) >= 0 or\
        branch.hira.find(keyword) >= 0 or\
        branch.roma.find(keyword) >= 0: 
        
        dict_MatchedBranch.update({ code: branch.name })

    return dict_MatchedBranch


  def BankCodeSearch(bankCode):
    
    for eachCode in Bank.all:
      #bank = Bank[code]
      bank = Bank[eachCode]

      if re.match(bankCode, eachCode): return bank.name
      
    return '該当データなし'

  def BranchCodeSearch(bankCode, branchCode):
    
    branches = Bank[bankCode].branches
  
    for eachCode in branches:
      #bank = Bank[code]
      branch = branches[eachCode]

      if re.match(branchCode, eachCode): return branch.name

    return '該当データなし'


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
  template_name='accounts/seller/bankAccountCreate1.html'
  dict_banks = BankAccount.MakeBanksDict()
  dict_bankCode_branches = BankAccount.MakeBanksBranchesDict()

  def get(self, request, *args, **kwargs):

    sellUser = usermodel.objects.get(email=self.request.user) 

    init_dict = {}

    # ★★ 250721 MyPageから設定するときはエンティティを選べるようにする
    # infoEdit_sellerから呼ばれた後の対応ができていない

    # tx_idが指定されているかで処理を分ける
    # tx_idを指定する意味は下記2つ
    # ①パートナーが前払いの承認時に口座未設定のことを認識すること
    # ②ユーザーが複数ゲストに参加可能とした場合にゲストを特定しなくて済む

    try:
      tx_id = self.kwargs.get('tx_id')
      tx = QpayTx.objects.get(pk=tx_id)
      init_dict.update(temporal_tx_id=tx_id)

      sellEntity = tx.sellEntity
    
    except:
      sellEntity = LegalEntity.objects.get(pk=sellUser.entity_id)

    if sellEntity.bankAccount_flag == 0: # 受取口座が未設定の場合

      form = self.form_class(initial=init_dict)

      context = {
        'flag_step': 1,
        'sellUser': sellUser,
        'sellEntity': sellEntity,

        'form' : form,
        'json_banks': json.dumps(self.dict_banks),
        'json_bankCode_branches': json.dumps(self.dict_bankCode_branches),
      }
      # bankAccountCreate1.htmlは（あれば）既設定口座を表示し、①登録済み口座を利用、②新規口座の設定か選択
      # bankAccountCreate2.htmlは、新規口座を登録
      return render(request, 'accounts/seller/bankAccountCreate2.html', context)   

    else:
    # entity.bankAccount_flag == 1のとき（受取口座が設定済み場合）
    # 既に口座設定がなされている場合は、表示するようフォームに初期値セット

      ba = sellEntity.bankAccount
      print(f'ba.bankName={ba.bankName}')
      print(f'ba.branchName={ba.branchName}')
      init_dict.update(bankCode=ba.bankCode)
      init_dict.update(bankName=ba.bankName)
      init_dict.update(branchCode=ba.branchCode)
      init_dict.update(branchName=ba.branchName)
      init_dict.update(holderName=ba.holderName)
      init_dict.update(accountNumber=ba.accountNumber)

      form = self.form_class(initial=init_dict)

      context = {
        'sellUser': sellUser,
        'sellEntity': sellEntity,
        'form' : form,
      }
      # 既存口座を表示のうえ、新しい口座を設定を選択する画面をレンダリング
      return render(request, 'accounts/seller/bankAccountCreate1.html', context)
      

  def post(self, request, *args, **kwargs):

    # 既に口座設定済みの方の処理
    WhichAccount = self.request.POST.get('WhichAccount', '')
    if WhichAccount:

      if WhichAccount.find('ThisAccount') >= 0:
        print(f'pass1 WhichAccount={WhichAccount}')
        return HttpResponseRedirect(reverse_lazy('accounts:mypage_seller'))
      

      if WhichAccount.find('NewAccount') >= 0:
      
        print(f'pass2 別の口座設定 WhichAccount={WhichAccount} post in BankAccountCreateView')
        sellUser = usermodel.objects.get(pk=WhichAccount.split('_')[1]) 
        sellEntity = LegalEntity.objects.get(pk=WhichAccount.split('_')[2])

        context = {
          'flag_step': 1,
          'sellUser': sellUser,
          'sellEntity': sellEntity,

          'form' : BankSelectForm(),
          'json_banks': json.dumps(self.dict_banks),
          'json_bankCode_branches': json.dumps(self.dict_bankCode_branches),
        }
        return render(request, "accounts/seller/bankAccountCreate2.html", context)


    # 検索ボタン（金融機関 or 支店）を押したときの処理。条件にマッチするデータ（辞書型）を返す
    search = self.request.POST.get('name_Search', '')
    print(f'search={search}')
  
    if search != None:

      if search.find('BankSearch') >= 0:

        sellUser = usermodel.objects.get(pk=search.split('_')[1]) 
        sellEntity = LegalEntity.objects.get(pk=search.split('_')[2])

        bankSearchInput = self.request.POST['name_bankSearchInput']
        print(f'ここ来る３ name_bankSearchInput={bankSearchInput}')
        dict_MatchedBank = BankAccount.BankSearch(bankSearchInput)

        init_dict = {
          'bankCode': self.request.POST.get('bankCode', None),
          'branchCode': self.request.POST.get('branchCode', None),
        }
        context = {
          'flag_step': 1,
          'sellUser': sellUser,
          'sellEntity': sellEntity,

          'form' : BankSelectForm(initial=init_dict),
          'bankCode': self.request.POST.get('bankCode', None),
          'bankSearchInput': bankSearchInput,
          'dict_MatchedBank': dict_MatchedBank,
          'json_banks': json.dumps(self.dict_banks),
          'json_bankCode_branches': json.dumps(self.dict_bankCode_branches),
        }
        return render(request, "accounts/seller/bankAccountCreate2.html", context)


      if search.find('BranchSearch') >= 0:

        sellUser = usermodel.objects.get(pk=search.split('_')[1]) 
        sellEntity = LegalEntity.objects.get(pk=search.split('_')[2])
      
        bankCode = self.request.POST.get('bankCode', None)
        print(f'bankCode={bankCode}')

        bankSearchInput = self.request.POST.get('name_bankSearchInput', None)
        branchSearchInput = self.request.POST.get('name_branchSearchInput', None)

        if bankCode is None or bankCode == "":
          dict_MatchedBranch = ""
          messages.info(request, '金融機関を選択してください')
        else:
          # 金融機関が選択され、支店の検索文字が入力されて初めて検索できる
          dict_MatchedBranch = BankAccount.BranchSearch(bankCode, branchSearchInput)

        # テンプレートで表示されているものを再現するため
        dict_MatchedBank = BankAccount.BankSearch(bankSearchInput)

        init_dict = {
          'bankCode': bankCode,
          'branchCode': self.request.POST.get('branchCode', None),
        }
        context = {
          "flag_step": 1,
          'sellUser': sellUser,
          'sellEntity': sellEntity,

          'form' : BankSelectForm(initial=init_dict),
          'bankCode': bankCode,
          'bankSearchInput': bankSearchInput,
          'branchSearchInput': branchSearchInput,
          'dict_MatchedBank': dict_MatchedBank,
          'dict_MatchedBranch': dict_MatchedBranch,
          'bankCode': self.request.POST.get('bankCode', None),
          'json_banks': json.dumps(self.dict_banks),
          'json_bankCode_branches': json.dumps(self.dict_bankCode_branches),
        }
        return  TemplateResponse(request, "accounts/seller/bankAccountCreate2.html", context)


    next = self.request.POST.get('next', '')   # POST.getはミドルウェア機能 
    if next:

      if next.find('ToInput') >= 0: # 口座名義・番号を入力する処理

        sellUser = usermodel.objects.get(pk=next.split('_')[1]) 
        sellEntity = LegalEntity.objects.get(pk=next.split('_')[2])

        print(f'pass1 if next==ToInput post/form.is_valid in BankAccountCreateView')

        form = BankSelectForm(self.request.POST)
        if form.is_valid():
          
          cleaned_data = form.cleaned_data
          bankCode = cleaned_data['bankCode']
          branchCode = cleaned_data['branchCode']

          print(f'pass2 bankCode={bankCode}, branchCode={branchCode} if next==ToInput post/form.is_valid in BankAccountCreateView')

          #bankCode = self.request.POST['name_bankSelect']
          #branchCode = self.request.POST['name_branchSelect']

          bankName = BankAccount.BankCodeSearch(bankCode)
          branchName = BankAccount.BranchCodeSearch(bankCode, branchCode)

          print(f'bankCode={bankCode} BankAccountCreateV, post, next==ToInput')
          print(f'branchCode={branchCode} BankAccountCreateV, post, next==ToInput')
          print(f'bankName={bankName} BankAccountCreateV, post, next==ToInput')
          print(f'branchName={branchName} BankAccountCreateV, post, next==ToInput')

          init_dict = {         
            'bankCode': bankCode,
            'branchCode': branchCode,
            'bankName': bankName,
            'branchName': branchName,
          }
          form = self.form_class(initial=init_dict)

          context = {
            'flag_step': 2,
            'sellUser': sellUser,
            'sellEntity': sellEntity,
            'form': form,
          }
          return render(request, "accounts/seller/bankAccountCreate2.html", context)
        
        else:  # 「form.is_valid() == False」のとき

          bankCode = self.request.POST.get('bankCode', None)
          branchCode = self.request.POST.get('branchCode', None)

          bankSearchInput = self.request.POST.get('name_bankSearchInput', None)
          branchSearchInput = self.request.POST.get('name_branchSearchInput', None)

          dict_MatchedBank = BankAccount.BankSearch(bankSearchInput)
          dict_MatchedBranch = BankAccount.BranchSearch(bankCode, branchSearchInput)

          init_dict = {
            'bankCode': bankCode,
            'branchCode': branchCode,
          }
          context = {
            'flag_step': 1,
            'sellUser': sellUser,
            'sellEntity': sellEntity,

            'form' : BankSelectForm(initial=init_dict),
            'bankSearchInput': bankSearchInput,
            'branchSearchInput': branchSearchInput,
            'dict_MatchedBank': dict_MatchedBank,
          }
          return render(request, "accounts/seller/bankAccountCreate2.html", context)


      if next.find('ToConfirm') >= 0:

        sellUser = usermodel.objects.get(pk=next.split('_')[1]) 
        sellEntity = LegalEntity.objects.get(pk=next.split('_')[2])
        print(f'next={next}')

        form = self.form_class(self.request.POST)

        if form.is_valid():

          context = {
            'flag_step': 3,
            'sellUser': sellUser,
            'sellEntity': sellEntity,
            'form': form,
          }
          return TemplateResponse(request, "accounts/seller/bankAccountCreate2.html", context)

        else:

          context = {
            'flag_step': 2,
            'sellUser': sellUser,
            'sellEntity': sellEntity,
            'form': form,
          }
          return render(request, "accounts/seller/bankAccountCreate2.html", context)


      if next.find('BackToSelect') >= 0:

        sellUser = usermodel.objects.get(pk=next.split('_')[1]) 
        sellEntity = LegalEntity.objects.get(pk=next.split('_')[2])

        form = self.form_class(self.request.POST)

        bankCode = self.request.POST.get('bankCode', None)
        branchCode = self.request.POST.get('branchCode', None)
        dict_MatchedBank = BankAccount.BankSearch(bankCode)
        dict_MatchedBranch = BankAccount.BranchSearch(bankCode, branchCode)

        context = {
          'flag_step': 1,
          'sellUser': sellUser,
          'sellEntity': sellEntity,

          'form' : form,
          'bankCode': bankCode,
          'branchCode': branchCode,
          'dict_MatchedBank': dict_MatchedBank,
          'dict_MatchedBranch': dict_MatchedBranch,
          'json_banks': json.dumps(self.dict_banks),
          'json_bankCode_branches': json.dumps(self.dict_bankCode_branches),
        }
        return render(request, 'accounts/seller/bankAccountCreate2.html', context)   


      if next.find('Register') >= 0: # 口座名義・番号を登録する処理

        sellUser = usermodel.objects.get(pk=next.split('_')[1]) 
        sellEntity = LegalEntity.objects.get(pk=next.split('_')[2])

        form = self.form_class(self.request.POST)

        if form.is_valid():

          ba_tmp = BankAccount()
          ba_tmp = form.save(commit=False)
          ba_tmp.temporal_tx_id = 0

          try:

            # 既存口座データがある場合の処理
            ba = self.model.objects.get(pk=sellEntity.bankAccount_id)
            ba.bankCode = ba_tmp.bankCode
            ba.bankName = ba_tmp.bankName
            ba.branchCode = ba_tmp.branchCode
            ba.branchName = ba_tmp.branchName
            ba.holderName = ba_tmp.holderName
            ba.accountNumber = ba_tmp.accountNumber
            ba.temporal_tx_id = 0

            ba.save()

            sellEntity.bankAccount_flag = 1
            sellEntity.bankAccount = ba
            sellEntity.save()

            print(f'ba.bankCode={ba.bankCode} BankAccountCreateV, post, next==register')

          except:

            # 既存口座データがない場合の処理
            # ＝（ba = self.model.objects.get(entity_id=ba_tmp.entity_id)がデータ取得できない場合）
            ba_tmp.save()
            sellEntity.bankAccount_flag = 1
            sellEntity.bankAccount = ba_tmp
            sellEntity.save()

            messages.add_message(request, messages.INFO, "受け取り口座は設定されました。") 


          return TemplateResponse(request, 'accounts/seller/mypage.html')

        else: #「if form.is_valid() == False」のとき
          
          messages.add_message(request, messages.WARING, "口座情報の入力にエラーがあります。")
          context = {
            'flag_step': 1,
            'form': form,
          } 
          return render(self.request, 'accounts/seller/bankAccountCreate2.html', context)


      if next.find('BackToInput') >= 0:

        sellUser = usermodel.objects.get(pk=next.split('_')[1]) 
        sellEntity = LegalEntity.objects.get(pk=next.split('_')[2])

        form = self.form_class(self.request.POST)

        print(f'ここまで来てる（def post if next==back after form.is_valid in class BankAccountCreateView）')
        context = {
          'flag_step': 2,  
          'sellUser': sellUser,
          'sellEntity': sellEntity,
          'form': form,
          'json_banks': json.dumps(self.dict_banks),
          'json_bankCode_branches': json.dumps(self.dict_bankCode_branches),
        }
        return render(self.request, 'accounts/seller/bankAccountCreate2.html', context)
  
    return HttpResponseBadRequest()

  def form_invalid(self, form):

    print(f'ここ来てる2（form_invalid in class BankAccountCreateView）')
    print(form.errors)
    form.instance.user = self.request.user
    return super().form_invalid(form)

  def get_success_url(self):
    return reverse('accounts:mypage_seller')



"""メインメニューから呼ばれる登録情報変更ビュー"""
class InfoEditView_buyer(generic.DetailView, LoginRequiredMixin):

  #template_name = "accounts/buyer/InfoEdit.html"

  def get(self, request, *args, **kwargs):

    print(f'request.user={request.user} def get in InfoEditView_buyer')
    try:    # 通常ケース（管理画面がログアウトされていないとワークせずエラーケースに）
      user = usermodel.objects.get(email=self.request.user)

      # ユーザー追加の承認依頼の件数を抽出する 
      cnt_toBeApproved_add = usermodel.objects.select_related('entity').filter(
      entity=user.entity, approvedStatus_int=1).count()

    except usermodel.DoesNotExist:

      # データが存在しない場合の処理
      messages.add_message(request, messages.WARNING, "ユーザー（self.request.user）が認識されていません") 
      return HttpResponseRedirect(reverse('accounts:login_buyer'))

    if user.type1 == 2:

      # 次のメッセージは確認できなかったので、要調整（トップページで出るようにする？）
      messages.add_message(request, messages.WARNING, "パートナーとしてログインして下さい") 
      return HttpResponseRedirect(reverse('accounts:logout'))

    context = {
      "user": user,
      "cnt_toBeApproved_add": cnt_toBeApproved_add,
    }
    return TemplateResponse(request, "accounts/buyer/infoEdit.html", context) 


"""メインメニューから呼ばれる登録情報変更ビュー"""
class InfoEditView_seller(generic.DetailView):
  
  def get(self, request, *args, **kwargs):

    try:  # 通常ケース（管理画面がログアウトされていないとワークせずエラーケースに）
      sellUser = usermodel.objects.get(email=self.request.user)
      sellEntity = LegalEntity.objects.get(pk=sellUser.entity_id)
      print(f'request.user={request.user} def get in InfoEditView_seller')

    except usermodel.DoesNotExist:

      # データが存在しない場合の処理
      messages.add_message(request, messages.WARNING, "ユーザー（self.request.user）が認識されていません") 

    if sellUser.type1 == 1:

      # 次のメッセージは確認できなかったので、要調整（トップページで出るようにする？）
      messages.add_message(request, messages.WARNING, "ゲストとしてログインして下さい") 
      return HttpResponseRedirect(reverse('accounts:logout'))

    context = {
      'sellUser': sellUser,
      'sellEntity': sellEntity,
    }
    return TemplateResponse(request, "accounts/seller/infoEdit.html", context) 
