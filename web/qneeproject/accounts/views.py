from django.contrib.auth import logout, get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required

from django.contrib.auth.views import \
  LoginView, PasswordChangeView, \
  PasswordResetView, PasswordResetDoneView, PasswordResetConfirmView

from .models import CustomUser, LegalEntity, BankAccount, CorpInfo
from qpay.models import QpayTx
from send.models import InvitationSets

from django.template.response import TemplateResponse
from django.urls import reverse, reverse_lazy

from django.conf import settings

from django.views import generic
from .form import \
  MyLoginForm, \
  UserCreateForm_buyer, UserCreateForm_seller, UserCreateForm_admin, \
  EntitySetForm_buyer, EntityCreateForm_buyer, PermissionUpdateForm_buyer,\
  EntitySetForm_seller, EntityCreateForm_seller, PermissionUpdateForm_seller,\
  PermissionUpdateForm_admin, \
  MyPageForm_buyer, MyPageForm_seller, \
  ContactForm, BankSelectForm, BankAccountForm, \
  AgreementConfirmForm_buyer, AgreementConfirmForm_seller, \
  MyPasswordChangeForm, ProfileEditForm_buyer, ProfileEditForm_seller, \
  InfoEvidenceForm, FeedbackForm

from qpay.form import TxCreateForm, TxApproveForm_buyer

from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.core.signing import dumps, loads, BadSignature, SignatureExpired
from django.http import HttpResponseBadRequest, HttpResponseRedirect, HttpResponseNotAllowed

from django.shortcuts import render

from django.contrib import messages
from django.core.mail import EmailMessage

import datetime
from datetime import date

from dateutil.relativedelta import relativedelta
from django.utils import timezone
from django.db.models import Sum

from zengin_code import Bank
from django.db.models import Q
import unicodedata, re
import json

from django.core.paginator import Paginator

# 以下は2025/02/14時点で参照されていない
#from django.test import TestCase
#from django.core.paginator import Paginator
#from django.core.exceptions import ValidationError
#from django.core.exceptions import PermissionDenied
#from django.contrib.auth.views import LogoutView
#from django.core.mail import send_mail # 使っている？
#from django import forms
#from django.shortcuts import redirect

UserModel = get_user_model()  #get_user_model は、settings.py で AUTH_USER_MODEL に指定されているモデルを取得する関数

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
    print(f'self.kwargs={self.kwargs} in get_context_data')
    if 'afterLogin' in self.kwargs: context['afterLogin'] = self.kwargs['afterLogin']
    if 'token' in self.kwargs: context['token'] = self.kwargs['token']
    return context

  def get_success_url(self):

    print(f'通過1 self.request.user={self.request.user} get_success_url in MyLoginView_buyer')

    buyUser = UserModel.objects.get(email=self.request.user)
    buyEntity = LegalEntity.objects.get(pk=buyUser.entity_id)

    self.request.session['buyUser_id'] = buyUser.id
    self.request.session['buyEntity_id'] = buyEntity.id

    if buyUser.type1 != 1:
      if buyUser.type1 == 1: type1_name = "パートナー"
      if buyUser.type1 == 2: type1_name = "ゲスト"
      if buyUser.type1 == 3: type1_name = "スタッフ"

      message = type1_name + "での登録です。" + type1_name + "でログインしてください。"
      messages.add_message(self.request, messages.WARNING, message) 
      logout(self.request)

      if buyUser.type1 == 1: return reverse_lazy('accounts:login_buyer')
      if buyUser.type1 == 2: return reverse_lazy('accounts:login_seller')
      if buyUser.type1 == 3: return reverse_lazy('accounts:login_admin')


    # メールからのログイン後に画面の指定がある場合の処理
    # メールURLで指定され、login.htmlで維持した変数から値を取り出す
    afterLogin = self.request.POST.get('afterLogin', None)
    if afterLogin is not None and afterLogin != '':

      if self.request.POST['afterLogin'] == 'qpayApproveApply':
        return reverse_lazy(
          'qpay:txApproveDetailPre_buyer',
          kwargs={'token': self.request.POST['token']})

      if self.request.POST['afterLogin'] == 'userAddApply':

        return reverse_lazy(
          'accounts:userAddPre_buyer',
          kwargs={'token':self.request.POST['token']})
    else:

      return reverse_lazy('accounts:mypage_buyer')


class MyLoginView_seller(LoginView):

  #redirect_authenticated_user=True,  "Trueの場合、ログイン済みユーザーはトップページ等にリダイレクト
  model = CustomUser
  form_class = MyLoginForm
  template_name='accounts/seller/login.html'

  def get_context_data(self, **kwargs):
    context = super().get_context_data(**kwargs)
    print(f'self.kwargs={self.kwargs} in get_context_data')
    if 'afterLogin' in self.kwargs: context['afterLogin'] = self.kwargs['afterLogin']
    if 'token' in self.kwargs: context['token'] = self.kwargs['token']

    return context

  
  def get_success_url(self):

    print(f'通過1 get_success_url in MyLoginView_seller')

    sellUser = UserModel.objects.get(email=self.request.user)
    sellEntity = LegalEntity.objects.get(pk=sellUser.entity_id)

    self.request.session['sellUser_id'] = sellUser.id
    self.request.session['sellEntity_id'] = sellEntity.id

    if sellUser.type1 != 2:
      if sellUser.type1 == 1: type1_name = "パートナー"
      if sellUser.type1 == 2: type1_name = "ゲスト"
      if sellUser.type1 == 3: type1_name = "スタッフ"

      message = type1_name + "での登録です。" + type1_name + "でログインしてください。"
      messages.add_message(self.request, messages.INFO, message) 
      logout(self.request)
      print(f'user.type1={sellUser.type1} in get_success_url in MyLoginView_seller')

      if sellUser.type1 == 1: return reverse_lazy('accounts:login_buyer')
      if sellUser.type1 == 2: return reverse_lazy('accounts:login_seller')
      if sellUser.type1 == 3: return reverse_lazy('accounts:login_admin')


    # メールからのログイン後に画面の指定がある場合の処理
    # メールURLで指定され、login.htmlで維持した変数から値を取り出す
    afterLogin = self.request.POST.get('afterLogin', None)
    if afterLogin is not None and afterLogin != '':

      #if self.request.POST['afterLogin'] == 'qpayApproveApply':
      #  return reverse_lazy(
      #    'qpay:txApproveDetailPre_seller',
      #    kwargs={'token': self.request.POST['token']})

      if self.request.POST['afterLogin'] == 'userAddApply':
        return reverse_lazy(
          'accounts:userAddPre_seller',
          kwargs={'token':self.request.POST['token']})
    else:

      return reverse_lazy('accounts:mypage_seller')


class MyLoginView_admin(LoginView):

  #redirect_authenticated_user=True,  "Trueの場合、ログイン済みユーザーはトップページ等にリダイレクト
  model = CustomUser
  form_class = MyLoginForm
  template_name='accounts/admin/login.html'

  def get_context_data(self, **kwargs):
    context = super().get_context_data(**kwargs)

    if 'afterLogin' in self.kwargs: context['afterLogin'] = self.kwargs['afterLogin']
    if 'token' in self.kwargs: context['token'] = self.kwargs['token']
    return context

  def get_success_url(self):

    adminUser = UserModel.objects.get(email=self.request.user)
    adminEntity = LegalEntity.objects.get(pk=adminUser.entity_id,)
    self.request.session['adminUser_id'] = adminUser.id
    self.request.session['adminbuyEntity_id'] = adminEntity.id

    if adminUser.type1 != 3:
      if adminUser.type1 == 1: type1_name = "パートナー"
      if adminUser.type1 == 2: type1_name = "ゲスト"

      message = type1_name + "での登録です。" + type1_name + "でログインしてください。"
      messages.add_message(self.request, messages.INFO, message) 
      logout(self.request)
      print(f'user.type1={adminUser.type1} in get_success_url in MyLoginView_admin')

      if adminUser.type1 == 1: return reverse_lazy('accounts:login_buyer')
      if adminUser.type1 == 2: return reverse_lazy('accounts:login_seller')

    # メールからのログイン後に画面の指定がある場合の処理
    # メールURLで指定され、login.htmlで維持した変数から値を取り出す
    afterLogin = self.request.POST.get('afterLogin', None)
    if afterLogin is not None and afterLogin != '':

      if self.request.POST['afterLogin'] == 'userAddApply':

        return reverse_lazy(
          'accounts:buyUserAddPre_admin',
          kwargs={'token':self.request.POST['token']})
        """「token」にはdumps(user.pk)の値を確報 """
      
      if self.request.POST['afterLogin'] == 'corpInfoApply':

        return reverse_lazy(
          'accounts:corpInfoUpdatePre_admin',
          kwargs={'token':self.request.POST['token']})
        """「token」にはdumps(user.pk)の値を確報 """

    else:

      return reverse_lazy('accounts:mypage_admin')


def MyLogoutView_buyer(request, **kwargs):
  request.session.flush()
  logout(request)
  #return redirect('login_buyer')
  return HttpResponseRedirect(reverse('accounts:login_buyer'))

def MyLogoutView_seller(request, **kwargs):
  request.session.flush()
  logout(request)
  return HttpResponseRedirect(reverse('accounts:login_seller'))

def MyLogoutView_admin(request, **kwargs):
  request.session.flush()
  logout(request)
  return HttpResponseRedirect(reverse('accounts:login_admin'))


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


class MyPasswordResetConfirmView_buyer(LoginRequiredMixin, PasswordResetConfirmView):

  login_url = '/accounts/login_buyer/'
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


class MyPasswordResetConfirmView_seller(LoginRequiredMixin, PasswordResetConfirmView):

  login_url = '/accounts/login_seller/'
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


class MyPasswordResetConfirmView_admin(LoginRequiredMixin, PasswordResetConfirmView):

  login_url = '/accounts/login_admin/'
  template_name = 'accounts/admin/passwordResetConfirm.html'

  def get_success_url(self):
    print(f'通過1 get_success_url in MyPasswordResetConfirm_admin')   
    messages.add_message(self.request, messages.INFO, "パスワードの再設定が完了しました。") 
    return reverse_lazy('accounts:login_admin')


# 25/05/17に追加
class MyPasswordChangeView_buyer(PasswordChangeView):

  """パスワード変更ビュー"""
  form_class = MyPasswordChangeForm
  template_name = 'accounts/buyer/passwordChange.html'

  def get_context_data(self, **kwargs):
    context = super().get_context_data(**kwargs)
    user = UserModel.objects.get(email=self.request.user)
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
  template_name = 'accounts/seller/passwordChange.html'

  def get_context_data(self, **kwargs):
    context = super().get_context_data(**kwargs)
    user = UserModel.objects.get(email=self.request.user)
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
  template_name = 'accounts/admin/passwordChange.html'

  def get_context_data(self, **kwargs):
    context = super().get_context_data(**kwargs)
    user = UserModel.objects.get(email=self.request.user)
    context['user_id'] = user.id
    user_id = context['user_id'] 
    print(f'user_id = {user_id} get_context_data in MyPasswordChangeView_admin')
    return context

  def get_success_url(self):
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

      user.is_active = False
      """ 参加承認が必要な場合は、承認された時点でアクティブに """
      """ 参加承認が不要な場合は、利用規約に同意した時点でアクティブに """
      """ アクティブにならないとログインができない """

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

      subject = render_to_string('accounts/buyer/mail/userTempRegister_subject.txt', context1)
      message = render_to_string('accounts/buyer/mail/userTempRegister_message.txt', context1)

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
      """ 参加承認が必要な場合は、承認された時点でアクティブに """
      """ 参加承認が不要な場合は、利用規約に同意した時点でアクティブに """
      """ アクティブにならないとログインができない """

      #user.email = self.request.user
      user.type1 = 2  # パートナー：1、ゲスト：2、Qnee：3で登録 25/04/27

      user.save()

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
  
      print(f'ここ来てる2（def post if form.is_valid=FALSE in class UserCreateView_seller）')
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
      # adminの場合は、パスワードの設定時点でユーザー名を制定

      user.type1 = 3  # パートナー：1、ゲスト：2、Qnee：3で登録 25/04/27
      user.type2 = 2  # Qnee（法人）として登録

      user.canApproveAll = True
      user.canApproveQpay = True
      user.canApproveChg = True

      """ ★★ 260314 Qneeが承認したときに「is_active=True」とするように変える """
      user.is_active = True
      user.joined_at = timezone.now()

      entity, created = LegalEntity.objects.get_or_create(
        entityName='株式会社Qnee',
        type1=3, type2=2,)
      
      user.entity = entity

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
  
      print(f'ここ来てる2（def post if form.is_valid=FALSE in class UserCreateView_admin）')
      print(form.errors)

      context2 = {
        'flag_step': 1,
        'form' : form,
      }
      return render(request, 'accounts/admin/userCreate.html', context2)  #ここでgetとするのは、おそらく親クラスでtemplate_nameを表示するように規定されている


"""25/01/01 メールで受領したURLがクリックされると本登録画面を表示"""

class EntityCreateView_buyer(generic.CreateView):

  #login_url = '/accounts/login_buyer/'
  form_class = EntityCreateForm_buyer
  timeout_seconds = getattr(settings, 'ACTIVATION_TIMEOUT_SECONDS', 60*60*24)
  #dict_buyEntityName = dict((f, f) for idx, f in enumerate(LegalEntity.objects.filter(type1=1).values_list('entityName', flat=True), 1))
  

  def dispatch(self, request, *args, **kwargs):
  
    self.request.session['dict_buyEntityname'] = \
      dict((f, f) for idx, f in enumerate(LegalEntity.objects.filter(type1=1).values_list('entityName', flat=True), 1))
  
    """ 初回のマイグレーションの時のみ下記を採用する """
    #dict_buyEntityName = {'Qnee','Qnee'}
    # 「flat=True」はリスト、「flat=False」はタプル
  
    return super().dispatch(request, *args, **kwargs)
  

  def get(self, request, **kwargs):  #selfはメソッドを呼んだインスタンス自体
  
    """（ビューにおいて）GETリクエストを受け取ったときに呼び出される（実践Django P121）"""
    """ 処理：パートナーに送られたメールのURLをクリックされた時点で呼ばれる """

    """ def getでは、メールから本登録に進む場合に呼ばれ、
      ①新規パートナー登録か、②既存パートナーにユーザー追加を選択するテンプレートを送る """

    try:
      # メール内のURLから<token>（暗号化されたuser_id）を取り出す（kwargsはdict型）
      token = self.kwargs.get('token', None)
      user_pk = loads(token, max_age=self.timeout_seconds)
      print(f'token = {token}, user_pk = {user_pk} in def get of EntitySetView_buyer')
      user = UserModel.objects.get(pk=user_pk)

    except UserModel.DoesNotExist:
      message = "ユーザー情報がございません。ユーザー登録をお願いいたします。"
      messages.add_message(self.request, messages.WARNING, message) 
      return TemplateResponse(request,'accounts/buyer/login.html', {'form':MyLoginForm}) 

    except SignatureExpired:  # 時間切れ

      # ★★ 250824 テスト未了。メルアド重複で登録不可にならないようUserオブジェクトを削除
      UserModel.objects.get(email=self.request.user).delete()
      message = "規定の時間を超えたため、再度、お手続きをお願いいたします"
      messages.add_message(self.request, messages.WARNING, message)

      return TemplateResponse(request,'accounts/buyer/login.html', {'form':MyLoginForm}) 

    except BadSignature:      # tokenが間違っている
      return HttpResponseBadRequest()


    # 仮登録が完了し、メールからのリンクにより本登録を開始した時点
    #user.is_active = True #Trueにしないとログインできない

    user.save()
    self.user_id = user.id
    print(f'self.user_id = {self.user_id}')

    dict_buyEntityName = self.request.session.get('dict_buyEntityname')
    #print(f'dict_buyEntityName={dict_buyEntityName} def get in EntityCreateView_buyer')

    init_dict = {
      #'userName': '',
      #'email': user.email,
      #'tel_user': "",
    }
    context = {
      'flag_step': 1,
      'user': user,
      'form': EntitySetForm_buyer(initial=init_dict),
      'temporal_buyEntityName': "",
      # コメント(25/06/08)：Selectボックスで未選択であることを示す。選択後はページ移動でデータ保持するために使う
      'dict_buyEntityName': dict_buyEntityName,
      'json_buyEntityName': json.dumps(dict_buyEntityName),
    }

    print(f'ここ来てる1 request.user={request.user} email={user.email} type2={user.type2}（get in class EntityCreateView_buyer）')
        
    return TemplateResponse(request, 'accounts/buyer/entitySet.html', context)


  def post(self, request, *args, **kwargs):

    next1 = self.request.POST.get('next1', None)
    next2 = self.request.POST.get('next2', None)
    # next1は、新規entityを登録する際の処理種別
    # next2は、既存entityにuser追加する際の処理種別

    print(f'pass-1 self.request.POST.get(next2)={next2} in def post next1 EntityCreateView_buyer')
    """ 新規のパートナー登録をする処理 """
    if next1 != None:

      if next1.find('ToCreateEntity') >= 0:

        user = UserModel.objects.get(pk=next1.split('_')[1]) 

        context = {
          'flag_step': 1,
          'user': user,
          'form': self.form_class,
        }
        # ★★ Entityは郵便番号、代表者の他、住所を登録するようにする 25/08/01
        return TemplateResponse(self.request, 'accounts/buyer/entityCreate.html', context)


      """ 入力内容を確認する画面 """
      if next1.find('ToConfirm') >= 0:

        user = UserModel.objects.get(pk=next1.split('_')[1]) 
        form = self.form_class(request.POST)
        # 260103 nextCaseを追加（①パートナー追加と②ユーザー追加に分ける）
        # 260301 ユーザー追加の場合はEntitySetform_buyerを利用（nextCaseをなくした）

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

        user = UserModel.objects.get(pk=next1.split('_')[1]) 

        context = {
          'user': user,
          'flag_step': 1,
          'form': form,
        }
        return TemplateResponse(self.request, 'accounts/buyer/.html', context)


      if next1.find('ToSave') >= 0: # 確認した内容をデータベースに登録

        # 250802 フォームをモデルフォームから通常フォームに変更したことに伴い変更
        user = UserModel.objects.get(pk=next1.split('_')[1]) 

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

        # 251221 定期配信の初期設定（sendのInvitationSets（in models.py）生成、関連付け）
        mailSets = InvitationSets.objects.create()
        mailSets.buyEntity = entity
        mailSets.save()

        entity.save()
       
        user.userName = \
          self.request.POST.get('lastName') + ' ' + self.request.POST.get('firstName')
        user.userName_kana = \
          self.request.POST.get('lastName_kana') + ' ' + self.request.POST.get('firstName_kana')

        # アプリで使うのはuseNameだが、名前を変更する場合があるので保存しておく
        user.lastName = self.request.POST.get('lastName')
        user.firstName = self.request.POST.get('firstName')
        user.lastName_kana = self.request.POST.get('lastName_kana')
        user.firstName_kana = self.request.POST.get('firstName_kana')

        user.tel_user = self.request.POST.get('tel_user', None)
        user.department = self.request.POST.get('department', None)
        user.title = self.request.POST.get('title', None)

        user.entity = entity

        user.canApproveAll = False
        user.canApproveChg = False
        user.canApproveQpay = False
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

        user = UserModel.objects.get(pk=next2.split('_')[1]) 
        form = EntitySetForm_buyer(request.POST)

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
          return TemplateResponse(self.request, 'accounts/buyer/entitySet.html', context)  # 確認画面に行く
        else:
          return TemplateResponse(self.request, 'accounts/buyer/entitySet.html', context)  # 確認画面に行く


      if next2.find('BackToInput') >= 0:

        form = EntitySetForm_buyer(request.POST)  # form_class=EntityCreateForm_buyer

        user = UserModel.objects.get(pk=next2.split('_')[1]) 
        entity = LegalEntity.objects.get(pk=next2.split('_')[2])

        dict_buyEntityName = self.request.session.get('dict_buyEntityname')

        context = {
          'user': user,
          'entity': entity,
          'flag_step': 1,
          'form': form,
          'temporal_buyEntityName': entity.entityName,
          # Note(25/06/08)：選択済み内容をページ移動後も維持するために使う（初期は空欄）
          'dict_buyEntityName': dict_buyEntityName,
          'json_buyEntityName': json.dumps(dict_buyEntityName),
        }
        return TemplateResponse(request, 'accounts/buyer/entitySet.html', context)


      if next2.find('ToSave&Apply') >= 0: # entitySet.htmlの「flag_step==2」の後（登録データ確認後）

        form = EntitySetForm_buyer(request.POST)  # form_class=EntityCreateForm_buyer

        user = UserModel.objects.get(pk=next2.split('_')[1]) 
        entity = LegalEntity.objects.get(pk=next2.split('_')[2])

        #temporal_buyEntityName = self.request.POST.get('temporal_buyEntityName', "")
        #entity = LegalEntity.objects.get(entityName=temporal_buyEntityName)

        user.entity = entity
        user.userName = \
          self.request.POST.get('lastName') + ' ' + self.request.POST.get('firstName')
        user.userName_kana = \
          self.request.POST.get('lastName_kana') + ' ' + self.request.POST.get('firstName_kana')

        # アプリで使うのはuseNameだが、名前を変更する場合があるので保存しておく
        user.lastName = self.request.POST.get('lastName')
        user.firstName = self.request.POST.get('firstName')
        user.lastName_kana = self.request.POST.get('lastName_kana')
        user.firstName_kana = self.request.POST.get('firstName_kana')

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



class AgreementConfirmView_buyer(generic.CreateView):

  " 25/01/08 利用規約に同意するためのビュー  "

  model = LegalEntity
  form_class = AgreementConfirmForm_buyer
  template_name = 'accounts/buyer/agreementConfirm.html'

  ## このgetメソッドは開発時に利用するためのもの　24/01/08
  ## 通常時は、EntityCreateViewのpostメソッド内から呼び出される
  def get(self, request, **kwargs):  #selfはメソッドを呼んだインスタンス自体
  
    try:
      user = UserModel.objects.get(pk=self.kwargs['user_id'])
      entity = LegalEntity.objects.get(pk=self.kwargs['entity_id'])

    except UserModel.DoesNotExist:
      messages.add_message(self.request,
        messages.INFO, "ユーザー情報がありません。ユーザー登録をお願いいたします。")
      return TemplateResponse(request,'accounts/buyer/login.html', {'form':MyLoginForm}) 

    """ エンティティの一人目か。一人目はQneenに申請、以降はパートナーに申請 """
    flag_firstPerson = 0
    if UserModel.objects.filter(
      ~Q(pk=user.id)
      & Q(entity=entity)
      & Q(canApproveAll=True)).exists():
      
      flag_firstPerson = 1

    context = {
      'flag_step': 1,
      'flag_firstPerson': flag_firstPerson,
      'user': user,
      'entity': entity,
    }
    return TemplateResponse(request, 'accounts/buyer/agreementConfirm.html', context) 


  def post(self, request, *args, **kwargs):
  
    checkValue = self.request.POST.get('checkConsent', None)  
    buttonValue = self.request.POST.get('next', None) 

    print(f'checkValue={checkValue}')
    print(f'buttonValue={buttonValue}')

    if buttonValue.find('ToAgree') >= 0:

      applyUser = UserModel.objects.get(pk=buttonValue.split('_')[1]) 
      buyEntity = LegalEntity.objects.get(pk=buttonValue.split('_')[2])
      print(f'applyUser.email={applyUser.email}')
      print(f'applyUser.userName={applyUser.userName}')
      print(f'applyUser.tel_user={applyUser.tel_user}')
      print(f'applyUser.department={applyUser.department}')
      print(f'applyUser.title={applyUser.title}')

      if checkValue == 'ToAgree': # 規約同意にチェックされた場合

        buyEntity.membershipConsent_boolean = True
        buyEntity.membershipConsent_at = timezone.now()
        buyEntity.sourcingConsent_boolean = True
        buyEntity.sourcingConsent_at = timezone.now()

        buyEntity.joined_at = timezone.now()
        buyEntity.save()

        applyUser.addStatus = 1
        applyUser.addStatus_char = '承認待ち'
        applyUser.save()

        """ ★★ 25/02/19編集（テストは未済み）""" 
        """ 「canApproveAll=True」「canApproveChg=True」の人に承認依頼する """
        """ ただし、一人目の場合はQneeが承認するようにする """

        buyApprovers = UserModel.objects.filter(
          ~Q(pk=applyUser.id) & Q(entity_id=buyEntity.id) & (Q(canApproveAll=True) | Q(canApproveChg=True)))

        #queryset_users = UserModel.objects.prefetch_related('entitys').filter(entitys=entity.id, is_buyUser_ApproveAll=True)

        # データ取得参考（https://noauto-nolife.com/post/django-foreignkey-related-name/）

        # 一人目のユーザーの場合（参加を承認するユーザーがいない場合）⇒Qneeが承認する
        if buyApprovers.first() is None: 

          adminApprovers = UserModel.objects.filter(
            Q(type1=3) & (Q(canApproveAll=True) | Q(canApproveChg=True)))

          for approver in adminApprovers:

            context1 = {
              'afterLogin': 'userAddApply',
              'approver': approver,
              'token': dumps(applyUser.pk), } # 申請者のuser.pkを維持する
            utils.sendEmail_common('accounts/buyer/mail/userAddApplyToAdmin', '', [approver.email], context1)

          #messages.add_message(request, messages.SUCCESS,
          #  "キユーニーにパートナー登録の申請をしました。")

          context = {'flag_step': 2,}
          return TemplateResponse(self.request,
            'accounts/buyer/agreementConfirm.html', context)


        else:   # パートナー内の権限者に参加申請する

          print(f'pass2 approvers.first() != None in def post AgreementConfirmView_buyer')
          print(f'pass2 approvers[0].email={buyApprovers[0].email}')

          for approver in buyApprovers:

            context1 = {
              'afterLogin': 'userAddApply',
              'approver': approver,
              'token': dumps(applyUser.pk), } # 申請者のuser.pkを維持する
            utils.sendEmail_common('accounts/buyer/mail/userAddApply', '', [approver.email], context1)
 
            print(f'pass1 approver.email={approver.email}（EntityCreateView_buyer, post, checkbox==agree)')

            context2 = {'flag_step': 3,}
            return TemplateResponse(self.request, 'accounts/buyer/agreementConfirm.html', context2)
      
      else:  # 同意チェックがされていない場合（チェックしていない場合はボタンが押せない）

        messages.error(request, 
          "「利用規約に同意します。」のチェックボックスにチェックがありません。", extra_tags='no check')

        context = {
          'flag_step': 1,
          'applyUser': applyUser,
          'buyEntity': buyEntity,
        }
        return render(self.request, 'accounts/buyer/agreementConfirm.html', context)


    if buttonValue.find('ToDisagree') >= 0:

      messages.error(request, "手続きを終了しました。またの機会によろしくお願いいたします。", extra_tags='no check')

      if UserModel.objects.filter(pk=buttonValue.split('_')[1]).exists():
        UserModel.objects.get(pk=buttonValue.split('_')[1]).delete()
      if LegalEntity.objects.filter(pk=buttonValue.split('_')[2]).exists():
        LegalEntity.objects.get(pk=buttonValue.split('_')[2]).delete()

      return TemplateResponse(request,'accounts/buyer/login.html', {'form':MyLoginForm}) 

    return HttpResponseBadRequest()  # 基本的にはここには来ない


class EntityCreateView_seller(generic.CreateView):

  """（ビューにおいて）GETリクエストを受け取ったときに呼び出される（実践Django P121）"""
  """ 処理：ゲストに送られたメールのURLをクリックされた時点で呼ばれる """

  """ def getでは、メールから本登録に進む場合に呼ばれ、
      ①新規ゲスト登録か、②既存ゲストにユーザー追加を選択するテンプレートを送る """

  form_class = EntityCreateForm_seller
  template_name = 'accounts/seller/entityCreate.html'
  timeout_seconds = getattr(settings, 'ACTIVATION_TIMEOUT_SECONDS', 60*60*72)

  #dict_sellEntityName = dict((f, f) for idx, f in enumerate(LegalEntity.objects.filter(type1=2,type2=2).values_list('entityName', flat=True), 1))
  #パートナー新規登録後に2人目のユーザーを追加しても反映されないため没

  def dispatch(self, request, *args, **kwargs):
  
    self.request.session['dict_sellEntityname'] = \
      dict((f, f) for idx, f in enumerate(LegalEntity.objects.filter(type1=2,type2=2).values_list('entityName', flat=True), 1))
  
    """ 初回のマイグレーションの時のみ下記を採用する """
    #dict_sellEntityName = {'Qnee','Qnee'}
    # 「flat=True」はリスト、「flat=False」はタプル
  
    return super().dispatch(request, *args, **kwargs)


  def get(self, request, **kwargs):  #selfはメソッドを呼んだインスタンス自体
  
    try:
      # メール内のURLから<token>（暗号化されたuser_id）を取り出す（kwargsはdict型）
      token = self.kwargs.get('token', None)
      user_pk = loads(token, max_age=self.timeout_seconds)
      user = UserModel.objects.get(pk=user_pk)
      print(f'token = {token}, user_pk = {user_pk} in def get of EntityCreateView_seller')

    except UserModel.DoesNotExist:
      
      UserModel.objects.get(email=self.request.user).delete()
      messages.add_message(self.request,
        messages.WARNING, "ユーザー情報がありません。ユーザー登録をお願いします。") 
      return TemplateResponse(request,'accounts/seller/login.html', {'form':MyLoginForm}) 

    except SignatureExpired:  # 時間切れ

      # ★★ 250824 テスト未了。メルアド重複で登録不可にならないようUserオブジェクトを削除
      UserModel.objects.get(email=self.request.user).delete()
      messages.add_message(self.request,
        messages.WARNING, "規定の時間を超えたため、再度、お手続きをお願いいたします")
      return TemplateResponse(request,'accounts/seller/login.html', {'form':MyLoginForm}) 

    except BadSignature:      # tokenが間違っている
      return HttpResponseBadRequest()
    

    # 仮登録が完了し、メールからのリンクにより本登録を開始した時点
    user.is_active = False # 参加承認が得られた時点でTrueにする
    user.save()

    dict_sellEntityName = self.request.session.get('dict_sellEntityname')

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
        'dict_sellEntityName': dict_sellEntityName,
        'json_sellEntityName': json.dumps(dict_sellEntityName),
      }
      print(f'ここ来てる2 self.request.user={self.request.user} email={user.email} type2={user.type2}（get in class EntityCreateView_seller）')
     
      return TemplateResponse(request, 'accounts/seller/entitySet.html', context)


  def post(self, request, *args, **kwargs):

    #user = UserModel.objects.get(email=self.request.user) 

    next1_indiv = self.request.POST.get('next1_indiv', None)

    next1_corp = self.request.POST.get('next1_corp', None)
    next2_corp = self.request.POST.get('next2_corp', None)
    # next1_corpは、新規entityを登録する際の処理種別
    # next2_corpは、既存entityにuser追加する際の処理種別


    """ 個人用の処理 """

    if next1_indiv != None:

      user = UserModel.objects.get(pk=next1_indiv.split('_')[1]) 
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

        # アプリで使うのはuseNameだが、名前を変更する場合があるので保存しておく
        user.lastName = self.request.POST.get('lastName')
        user.firstName = self.request.POST.get('firstName')
        user.lastName_kana = self.request.POST.get('lastName_kana')
        user.firstName_kana = self.request.POST.get('firstName_kana')

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

        user.canApproveAll = False
        user.canApproveChg = False
        user.canApproveQpay = False
        # 【留意】 「False」とし、AgreementConfirmView_sellerにおいて、
        # 利用規約に同意した時点（二人目以降は追加承認がなされた後）に
        # 各権限を「True」、addStatus=1（申請中）とする

        # ★★ 2500927 ゲストの場合はQneeの承認はなし（パートナーと異なる）

        user.is_active = False

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

      user = UserModel.objects.get(pk=next1_corp.split('_')[1]) 
      
      # ★★ 250930 これは新規ゲスト作成のときにいる？
      #form = self.form_class(request.POST)

      """ （法人用）新規のゲスト登録をする処理 """

      print(f'pass0 if ToCreateEntity')

      # 入力するための画面を表示する
      if next1_corp.find('ToCreateEntity') >= 0:
        
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

        user.entity = entity
        user.userName = \
          self.request.POST.get('lastName') + ' ' + self.request.POST.get('firstName')
        user.userName_kana = \
          self.request.POST.get('lastName_kana') + ' ' + self.request.POST.get('firstName_kana')

        # アプリで使うのはuseNameだが、名前を変更する場合があるので保存しておく
        user.lastName = self.request.POST.get('lastName')
        user.firstName = self.request.POST.get('firstName')
        user.lastName_kana = self.request.POST.get('lastName_kana')
        user.firstName_kana = self.request.POST.get('firstName_kana')

        user.tel_user = self.request.POST.get('tel_user')
        user.department = self.request.POST.get('department')
        user.title = self.request.POST.get('title')

        user.entity = entity

        user.canApproveAll = False
        user.canApproveChg = False
        user.canApproveQpay = False
        # 【留意】 「False」とし、AgreementConfirmView_sellerにおいて、
        # パートナ一１人目の場合は「True」、２人目以降は権限者が「True/False」を設定

        # ★★ 25009254 Qneeはゲストに対しては承認しない
        # ★★ この部分はパートナーと異なる

        user.is_active = False
        
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

        user = UserModel.objects.get(pk=next1_corp.split('_')[1])

        context = {
          'flag_step': 1,
          'user': user,
          'form': form,
        }
        return TemplateResponse(self.request, 'accounts/seller/entityCreate.html', context)


    """ （法人用）登録済みゲストに追加する処理 """

    if next2_corp != None:

      print(f'next2_corp={next2_corp} def post of EntityCreateView_seller')

      if next2_corp.find('ToStopProcess') >= 0: # プロセスと止める
        messages.error(self.request, "ユーザー登録の手続きを終了しました。")
        logout(request)
        return HttpResponseRedirect(reverse('accounts:login_seller'))
      

      if next2_corp.find('ToConfirm') >= 0:  # 登録済みパートナーにユーザー追加

        form = EntitySetForm_seller(request.POST) # form_class=EntityCreateForm_seller
        user = UserModel.objects.get(pk=next2_corp.split('_')[1])

        # ★★ 250914 バリデーション（エンティティが選ばれているかを含む）を対応
        if form.is_valid():
        # 下記①、②、③の順で実行
        # ①.is_valid()、②フォームでのclean、clean_<field>、③form.cleaned_data[]に格納

          #temporal_sellEntityName = self.request.POST.get('name_SellerSelect', None)
          #sellEntity = LegalEntity.objects.get(entityName=temporal_sellEntityName)
 
          cleaned_data = form.cleaned_data 
          entityName = cleaned_data['entityName']
  
          # 確認用
          entityName2 = self.request.POST.get('entityName', None)
          print(f'self.request.POST.get(entityName)={entityName2}')
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
          dict_sellEntityName = self.request.session.get('dict_sellEntityname')

          context = {
            'flag_step': 1,
            'selectedValue': 'AddToEntity',
            'user': user,
            'entity': entity,
            'form' : form,
            'temporal_sellEntityName': entity.entityName,
            # コメント(25/06/08)：Selectボックスで未選択であることを示す。選択後はページ移動でデータ保持するために使う
            'dict_sellEntityName': dict_sellEntityName,
            'json_sellEntityName': json.dumps(dict_sellEntityName),

          }
          return TemplateResponse(self.request, 'accounts/seller/entitySet.html', context)



      if next2_corp.find('BackToInput') >= 0:

        form = EntitySetForm_seller(request.POST)  # form_class=EntityCreateForm_seller

        user = UserModel.objects.get(pk=next2_corp.split('_')[1]) 
        entity = LegalEntity.objects.get(pk=next2_corp.split('_')[2])
        dict_sellEntityName = self.request.session.get('dict_sellEntityname')

        context = {
          'selectedValue': 'AddToEntity',
          'flag_step': 1,
          'user': user,
          'entity': entity,
          'form': form,
          'temporal_sellEntityName': entity.entityName,
          # Note(25/06/08)：選択済み内容をページ移動後も維持するために使う（初期は空欄）
          'dict_sellEntityName': dict_sellEntityName,
          'json_sellEntityName': json.dumps(dict_sellEntityName),
        }
        return TemplateResponse(request, 'accounts/seller/entitySet.html', context)


      if next2_corp.find('ToSave&Apply') >= 0: 
      # entitySet.htmlの「flag_step==2」の後（登録データ確認後）

        form = EntitySetForm_seller(request.POST)  # form_class=EntityCreateForm_buyer

        user = UserModel.objects.get(pk=next2_corp.split('_')[1]) 
        entity = LegalEntity.objects.get(pk=next2_corp.split('_')[2])

        #user.userName = self.request.POST.get('userName', None)
        user.entity = entity
        user.userName = \
          self.request.POST.get('lastName') + ' ' + self.request.POST.get('firstName')
        user.userName_kana = \
          self.request.POST.get('lastName_kana') + ' ' + self.request.POST.get('firstName_kana')

        # 名前を変更する場合があるので保存しておく
        user.lastName = self.request.POST.get('lastName')
        user.firstName = self.request.POST.get('firstName')
        user.lastName_kana = self.request.POST.get('lastName_kana')
        user.firstName_kana = self.request.POST.get('firstName_kana')

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



"""25/01/10 利用規約に同意するためのビュー"""
class AgreementConfirmView_seller(generic.UpdateView):

  model = LegalEntity
  form_class = AgreementConfirmForm_seller
  template_name = 'accounts/seller/agreementConfirm.html'

  ## このgetメソッドは開発時に利用するためのもの　24/01/08
  ## 通常時は、EntityCreateViewのpostメソッド内から呼び出される
  def get(self, request, **kwargs):  #selfはメソッドを呼んだインスタンス自体
  
    try:
      user = UserModel.objects.get(pk=self.kwargs['user_id'])
      entity = LegalEntity.objects.get(pk=self.kwargs['entity_id'])

    except UserModel.DoesNotExist:
      message = "申し訳ありませんが、ユーザー情報が確認できません。"
      messages.add_message(self.request, messages.INFO, message) 
      return TemplateResponse(request,'accounts/seller/login.html', {'form':MyLoginForm()}) 

    """ 法人の場合のエンティティの二人目以降はゲスト企業に申請 """
    flag_firstPerson = 0
    if UserModel.objects.filter(
      ~Q(pk=user.id)
      & Q(entity=entity)
      & Q(canApproveAll=True)).exists():
      
      flag_firstPerson = 1

    context = {
      'flag_step': 1,
      'flag_firstPerson': flag_firstPerson,
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
      applyUser = UserModel.objects.get(pk=buttonValue.split('_')[1]) 
      sellEntity = LegalEntity.objects.get(pk=buttonValue.split('_')[2])

      if checkValue == 'ToAgree':  # 規約同意にチェックされた場合

        sellEntity.membershipConsent_boolean = True
        sellEntity.membershipConsent_at = timezone.now()

        sellEntity.joined_at = timezone.now()
        #entity.email = user.email

        sellEntity.save()

        if applyUser.type2 == 1: # 個人ゲストの場合は承認受けず

          applyUser.canApproveAll = True
          applyUser.canApproveChg = True
          applyUser.canApproveQpay = True

          applyUser.addStatus = 2 # （承認不要なため、）承認済みにする
          applyUser.addStatus_char = '承認不要'

          applyUser.entity = sellEntity
          applyUser.save()

          return TemplateResponse(request,'accounts/seller/login.html', {'form':MyLoginForm()})


        if applyUser.type2 == 2: # 法人ゲストの場合

          """ ★★ 25/06/14追加（テストは未済み） 
             「canApproveAll=True」「canApproveChg=True」の人に承認依頼する """
          
          approvers = UserModel.objects.filter(
            ~Q(pk=applyUser.id) & Q(entity_id=sellEntity.id) & (Q(canApproveAll=True) | Q(canApproveChg=True)))
    
          if approvers.first() is None: # 一人目のユーザーの場合（参加を承認するユーザーがいない場合）
          
            applyUser.canApproveAll = True
            applyUser.canApproveChg = True
            applyUser.canApproveQpay = True

            applyUser.addStatus = 2 # 承認不要なので
            applyUser.addStatus_char = '承認不要'
            applyUser.is_active = True #ここでログインできるようになる

            applyUser.entity = sellEntity
            applyUser.save()

            context2 = {'flag_step': 2,}
            return TemplateResponse(self.request, 'accounts/seller/agreementConfirm.html', context2)
            #return TemplateResponse(request,'accounts/seller/login.html', {'form':MyLoginForm}) 


          else:   # ゲスト内の権限者に参加申請する

            current_site = get_current_site(self.request)
            domain = current_site.domain

            for approver in approvers:

              applyUser.addStatus = 1 # 申請済み・承認前のステータスに変更
              applyUser.addStatus_char = '承認待ち'
              applyUser.save()

              context1 = {
                'afterLogin': 'userAddApply',
                'approver': approver,
                'token': dumps(applyUser.pk),
              }
              utils.sendEmail_common(
                'accounts/seller/mail/userAddApply', '',  [approver.email], context1)

              #messages.add_message(request, messages.SUCCESS, 'ユーザーの追加登録の申請を行いました.')
              #テンプレート上にメッセージがでるので不要

              print(f'pass1 approver.email={approver.email}（EntityCreateView_seller, post, checkbox==agree)')

              context2 = {'flag_step': 3,}
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

      messages.error(request, "手続きを終了しました。またの機会によろしくお願いいたします。", extra_tags='no check')

      if UserModel.objects.filter(pk=buttonValue.split('_')[1]).exists():
        UserModel.objects.get(pk=buttonValue.split('_')[1]).delete()
      if LegalEntity.objects.filter(pk=buttonValue.split('_')[2]).exists():
        LegalEntity.objects.get(pk=buttonValue.split('_')[2]).delete()

      return TemplateResponse(request,'accounts/seller/login.html', {'form':MyLoginForm}) 


    return HttpResponseBadRequest()  # 基本的にはここには来ない


class UserAddPreView_buyer(LoginRequiredMixin, generic.TemplateView):

  " 案内されたメールからアプリに入ってユーザー追加の承認をする場合の入口 "
  " tokenをapplyUser_idに変換して、UserAddView_buyerを呼ぶ "

  login_url = '/accounts/login_buyer/'
  timeout_seconds = getattr(settings,  'ACTIVATION_TIMEOUT_SECONDS', 60*60*24)

  def get(self, request, *args, **kwargs):
  
    try:
      token_applyUserID = self.kwargs.get('token')    # URLから<token>（暗号化されたuser_id）を取り出す（kwargsはdict型）   
      applyUser_id = loads(token_applyUserID, max_age=self.timeout_seconds)
      #self.request.session['applyUser_id'] = applyUser_id

    except SignatureExpired:
      return HttpResponseBadRequest()

    #tokenが間違っている
    except BadSignature:
      return HttpResponseBadRequest()

    return HttpResponseRedirect(
      reverse_lazy('accounts:userAdd_buyer', kwargs={'applyUser_id': applyUser_id}))
  

class UserAddView_buyer(LoginRequiredMixin, generic.TemplateView):

  """ 承認者がユーザー参加を承認するためのビュー """
  """ ビューの呼ばれる方は２種類 """
  """ ①承認者が受領したメール内のリンクから②商人者のマイページから """
  """ ①申請者におけるAgreementConfirmView⇒②承認者へのメール⇒③メール内リンクから呼ばれる """
  """ 承認者（self.request.user）、申請者の二者のidを維持する必要あり """
  """ 最終編集 260320 """

  login_url = '/accounts/login_buyer/'
  model = CustomUser


  """ 承認者が受領したメール内のリンクから呼ばれる """
  def get(self, request, **kwargs):  #selfはメソッドを呼んだインスタンス自体

    loginUser = UserModel.objects.get(email=self.request.user)

    try: # applyUser_idの指定がある場合

      applyUser_id = self.kwargs.get('applyUser_id')
      applyUser = UserModel.objects.get(pk=applyUser_id)
      print(f'applyUser={applyUser} in UserAddView_buyer')
      self.request.session['flag_frWhere'] = 1
      context = {
        'loginUser': loginUser,
        'applyUser': applyUser,
      }
      return TemplateResponse(request, 'accounts/buyer/userAdd.html', context)
    
    except: # mypage経由で来る場合（applyUser_idの指定がない場合）

      self.request.session['flag_frWhere'] = 2

      applyUsers =UserModel.objects.filter(
        Q(entity=loginUser.entity) & (Q(addStatus=1) | Q(addStatus=3))
        ).order_by('-created_at')
      
      # 確認用
      cnt_applyUsers =UserModel.objects.filter(
        Q(entity=loginUser.entity) & (Q(addStatus=1) | Q(addStatus=3))
        ).count()
      print(f'cnt_applyUsers={cnt_applyUsers} in UserAddView_buyer')

      context = {
        'loginUser': loginUser,
        'applyUsers': applyUsers,
      }
      return TemplateResponse(request, 'accounts/buyer/userAdd.html', context)


  def post(self, request, **kwargs):

    next = self.request.POST.get('next', '')

    if next.find('ToEditPermission') >=0: # リストで選択されたユーザーの設定を表示する

      editedUser = UserModel.objects.get(pk=next.split('_')[1])

      context = {
        'flag_scene': 'whenJoining',
        # 権限設定側（PermissionSetsView、def post）でユーザー参加承認時と認識
        'editedUser': editedUser,
        'form': PermissionUpdateForm_buyer(),
      }
      return TemplateResponse(request, 'accounts/buyer/permissionUpdate.html', context)
    

    if next.find('ToApproveUser') >= 0:
      print(f'pass1 if ToApproveUser in UserAddView_buyer')

      loginUser = UserModel.objects.get(email=self.request.user)
      applyUser = UserModel.objects.get(pk=next.split('_')[1])
      #buyEntity = LegalEntity.objects.get(pk=applyUser.entity_id)

      if applyUser.addStatus == 1 or applyUser.addStatus == 3:

        applyUser.addStatus = 2
        applyUser.addStatus_char = '承認済み'

        applyUser.is_active = True #ここでログインできるようになる
        applyUser.joined_at = timezone.now()

        applyUser.save()

        # ここからは申請者に参加が認められたことを伝えるメール送信
        utils.sendEmail_common('accounts/buyer/mail/userAddReplyYes', '', [applyUser.email])

        messages.add_message(self.request,
          messages.SUCCESS, "あなたの承認で新しいユーザーが加わりました。") 


        # メールからアプリに入る場合、対象データだけの処理結果を表示
        if self.request.session.get('flag_frWhere') == 1:

          context = {
            'loginUser': loginUser,
            'applyUser': applyUser,
          }
          return TemplateResponse(request, 'accounts/buyer/userAdd.html', context)

        # mypageから処理する場合は、全ユーザーの状況を表示する
        if self.request.session.get('flag_frWhere') == 2:

          applyUsers =UserModel.objects.filter(
            Q(entity=loginUser.entity)
            & (Q(addStatus=1) | Q(addStatus=3))).order_by('-created_at')
          # 申請中＋否認済みのものが対象

          context = {
            'loginUser': loginUser,
            'applyUsers': applyUsers, }
          return TemplateResponse(request, 'accounts/buyer/userAdd.html', context)
        

      else: # ここは通らないはず

        messages.add_message(self.request,
          messages.WARNING, "システムエラー（想定外の処理となっています）。") 
        
        loginUser = UserModel.objects.get(email=self.request.user)

        # メールからアプリに入る場合、対象データだけの処理結果を表示
        if self.request.session.get('flag_frWhere') == 1:
          context = {
            'loginUser': loginUser,
            'applyUser': applyUser, }     
          return TemplateResponse(
            request, 'accounts/buyer/userAdd.html', context)

        # mypageから処理する場合は、全ユーザーの状況を表示する
        if self.request.session.get('flag_frWhere') == 2:

          applyUsers =UserModel.objects.filter(
            Q(entity=loginUser.entity)
            & (Q(addStatus=1) | Q(addStatus=3))).order_by('-created_at')
          # 申請中＋否認済みのものが対象

          context = {
            'loginUser': loginUser,
            'applyUsers': applyUsers,
          }
          return TemplateResponse(request, 'accounts/buyer/userAdd.html', context)


    if next.find('ToRefuseUser') >= 0:
      print(f'pass2 if ToRefuseUser in UserAddView_buyer')

      loginUser = UserModel.objects.get(email=self.request.user)
      applyUser = UserModel.objects.get(pk=next.split('_')[1])
      #buyEntity = LegalEntity.objects.get(pk=applyUser.entity_id)

      applyUser.addStatus = 3
      applyUser.addStatus_char = "否認済み"

      applyUser.save()

      # 否認されたことを通知する
      utils.sendEmail_common('accounts/buyer/mail/userAddReplyNo', '', [applyUser.email])

      # メールからアプリに入る場合、対象データだけの処理結果を表示
      if self.request.session.get('flag_frWhere') == 1:
        print(f'pass2-1 if ToRefuseUser & flag_frWhere==1, applyUser.in UserAddView_buyer')
        context = {
          'loginUser': loginUser,
          'applyUser': applyUser,
        }     
        return TemplateResponse(request, 'accounts/buyer/userAdd.html', context)


      # mypageから処理する場合は、全ユーザーの状況を表示する
      if self.request.session.get('flag_frWhere') == 2:
        loginUser = UserModel.objects.get(email=self.request.user)

        applyUsers =UserModel.objects.filter(
          Q(entity=loginUser.entity)
          & (Q(addStatus=1) | Q(addStatus=3))).order_by('-created_at')

        context = {
          'loginUser': loginUser,
          'applyUsers': applyUsers,
        }
        return TemplateResponse(request, 'accounts/buyer/userAdd.html', context)    
    
    print(f'pass2 本当はここは通らないんだけど！ in UserAddView_buyer')



" 案内されたメールからアプリに入ってユーザー追加の承認をする場合の入口 "
" tokenをapplyUser_idに変換して、UserAddView_sellerを呼ぶ "
class UserAddPreView_seller(LoginRequiredMixin, generic.TemplateView):

  login_url = '/accounts/login_seller/'
  timeout_seconds = getattr(settings,  'ACTIVATION_TIMEOUT_SECONDS', 60*60*24)

  def get(self, request, *args, **kwargs):

    try:
      token_applyUserID = self.kwargs.get('token')    # URLから<token>（暗号化されたuser_id）を取り出す（kwargsはdict型）   
      applyUser_id = loads(token_applyUserID, max_age=self.timeout_seconds)
      self.request.session['applyUser_id'] = applyUser_id
      
    except SignatureExpired:
      return HttpResponseBadRequest()

    #tokenが間違っている
    except BadSignature:
      return HttpResponseBadRequest()

    return HttpResponseRedirect(
      reverse_lazy('accounts:userAdd_seller', kwargs={'applyUser_id': applyUser_id}))


" ゲスト内でユーザーを追加する場合の処理 "
class UserAddView_seller(LoginRequiredMixin, generic.CreateView):

  """ 承認者がユーザー参加を承認するためのビュー """
  """ ビューの呼ばれる方は２種類 """
  """ ①承認者が受領したメール内のリンクから②商人者のマイページから """
  """ ①申請者におけるAgreementConfirmView⇒②承認者へのメール⇒③メール内リンクから呼ばれる """
  """ 承認者（self.request.user）、申請者の二者のidを維持する必要あり """
  """ 最終編集 260322 """

  login_url = '/accounts/login_seller/'
  model = CustomUser


  def get(self, request, **kwargs):  #selfはメソッドを呼んだインスタンス自体

    loginUser = UserModel.objects.get(email=self.request.user)

    try:
      applyUser_id = self.kwargs.get('applyUser_id')
      applyUser = UserModel.objects.select_related('entity').get(pk=applyUser_id)

      self.request.session['flag_frWhere'] = 1
      context = {
        'loginUser': loginUser,
        'applyUser': applyUser,
      }
      return TemplateResponse(request, 'accounts/seller/userAdd.html', context)

    except:

      self.request.session['flag_frWhere'] = 2

      #TwoWeeksAgo = datetime.datetime.now() - datetime.timedelta(days=14)

      applyUsers =UserModel.objects.filter(
        Q(entity=loginUser.entity)
        & (Q(addStatus=1) | Q(addStatus=3))).order_by('-created_at')


      context = {
        # 'flag_frWhere': 2,
        'loginUser': loginUser,
        'applyUsers': applyUsers,
      }
      return TemplateResponse(request, 'accounts/seller/userAdd.html', context)
     

  def post(self, request, **kwargs):

    next = self.request.POST.get('next', None)

    if next.find('ToEditPermission') >=0: # リストで選択されたユーザーの設定を表示する

      editedUser = UserModel.objects.get(pk=next.split('_')[1])

      context = {
        'flag_scene': 'whenJoining',
        'editedUser': editedUser,
        'form': PermissionUpdateForm_seller(),
      }
      return TemplateResponse(request, 'accounts/seller/permissionUpdate.html', context)
    

    if next.find('ToApproveUser') >= 0:

      loginUser = UserModel.objects.get(email=self.request.user)
      applyUser = UserModel.objects.get(pk=next.split('_')[1])

      #sellEntity = LegalEntity.objects.get(pk=applyUser.entity_id)

      if applyUser.addStatus == 1 or applyUser.addStatus == 3:

        applyUser.addStatus = 2    # パートナー内でユーザー追加が承認された時点
        applyUser.addStatus_char = '承認済み'
        applyUser.is_active = True #ここでログインできるようになる

        applyUser.save()

        utils.sendEmail_common('accounts/seller/mail/userAddReplyYes', '',  [applyUser.email])

        messages.add_message(self.request,
          messages.SUCCESS, "あなたの承認で新しいユーザーが加わりました。") 
        
        return TemplateResponse(request, 'accounts/seller/mypage.html')

      else: # ここは通らないはず

        messages.add_message(self.request,
          messages.WARNING, "既に否認がなされています。") 

        if self.request.session.get('flag_frWhere') == 1:
          context = {
            'loginUser': loginUser,
            'applyUser': applyUser,
          }     
          return TemplateResponse(request, 'accounts/seller/userAdd.html', context)

        if self.request.session.get('flag_frWhere') == 2:
          loginUser = UserModel.objects.get(email=self.request.user)

          applyUsers =UserModel.objects.filter(
            Q(entity=loginUser.entity)
            & (Q(addStatus=1) | Q(addStatus=3))).order_by('-created_at')

          context = {
            'loginUser': loginUser,
            'applyUsers': applyUsers,
          }
          return TemplateResponse(request, 'accounts/seller/userAdd.html', context)    
  

    if next.find('ToRefuseUser') >= 0:

      loginUser = UserModel.objects.get(email=self.request.user)
      applyUser = UserModel.objects.get(pk=next.split('_')[1])
      #sellEntity = LegalEntity.objects.get(pk=applyUser.entity_id)

      applyUser.addStatus = 3
      applyUser.addStatus_char = "否認済み"
      applyUser.save()

      # 否認されたことを通知する
      utils.sendEmail_common('accounts/seller/mail/userAddReplyNo', '', [applyUser.email])

      if self.request.session.get('flag_frWhere') == 1:
        context = {
          #'form': form,
          'loginUser': loginUser,
          'applyUser': applyUser,
        }     
        return TemplateResponse(request, 'accounts/seller/userAdd.html', context)


      if self.request.session.get('flag_frWhere') == 2:
        loginUser = UserModel.objects.get(email=self.request.user)

        applyUsers =UserModel.objects.filter(
          Q(entity=loginUser.entity)
          & (Q(addStatus=1) | Q(addStatus=3))).order_by('-created_at')

        context = {
          #'form': self.form_class(),
          'loginUser': loginUser,
          'applyUsers': applyUsers,
        }
        return TemplateResponse(request, 'accounts/seller/userAdd.html', context)    



class BuyUserAddPreView_admin(LoginRequiredMixin, generic.TemplateView):

  " 案内されたメールからアプリに入ってユーザー追加の承認をする場合の入口 "
  " tokenをapplyUser_idに変換して、UserAddView_buyerを呼ぶ "

  login_url = '/accounts/login_admin/'
  timeout_seconds = getattr(settings,  'ACTIVATION_TIMEOUT_SECONDS', 60*60*24)

  def get(self, request, *args, **kwargs):
  
    try:
      token_applyUserID = self.kwargs.get('token')    # URLから<token>（暗号化されたuser_id）を取り出す（kwargsはdict型）   
      applyUser_id = loads(token_applyUserID, max_age=self.timeout_seconds)
      self.request.session['applyUser_id'] = applyUser_id

    except SignatureExpired:
      return HttpResponseBadRequest()

    #tokenが間違っている
    except BadSignature:
      return HttpResponseBadRequest()

    return HttpResponseRedirect(
      reverse_lazy('accounts:buyUserAdd_admin', kwargs={'applyUser_id': applyUser_id}))
  

class BuyUserAddView_admin(LoginRequiredMixin, generic.TemplateView):

  """ パートナーの一人目の参加についてQneeが承認するためのビュー。"""
  """ ビューの呼ばれる方は２種類 """
  """ ①承認者が受領したメール内のリンクから②商人者のマイページから """
  """ ①申請者におけるAgreementConfirmView⇒②承認者へのメール⇒③メール内リンクから呼ばれる """
  """ 承認者（self.request.user）、申請者の二者のidを維持する必要あり """
  """ 最終編集 260501 """

  login_url = '/accounts/login_admin/'
  model = CustomUser


  """ 承認者が受領したメール内のリンクから呼ばれる """
  def get(self, request, **kwargs):  #selfはメソッドを呼んだインスタンス自体

    loginUser = UserModel.objects.get(email=self.request.user)

    try: # applyUser_idの指定がある場合

      applyUser_id = self.kwargs.get('applyUser_id')
      applyUser = UserModel.objects.select_related('entity').get(pk=applyUser_id)

      print(f'applyUser={applyUser} applyUser.addStatus={applyUser.addStatus} def get in BuyUserAddView_admin')

      self.request.session['flag_frWhere'] = 1
      context = {
        'loginUser': loginUser,
        'applyUser': applyUser,
      }
      return TemplateResponse(request, 'accounts/admin/buyUserAdd.html', context)
    
    except: # mypage経由で来る場合（applyUser_idの指定がない場合）

      self.request.session['flag_frWhere'] = 2

      applyUsers =UserModel.objects.select_related('entity').filter(
        Q(type1=1) & (Q(addStatus=1) | Q(addStatus=3))).order_by('-created_at')
      
      # 確認用
      cnt_applyUsers =UserModel.objects.filter(
        Q(type1=1) & (Q(addStatus=1) | Q(addStatus=3))).count()
      print(f'cnt_applyUsers={cnt_applyUsers} in BuyUserAddView_admin')
      print(f'applyUsers={applyUsers} in BuyUserAddView_admin')

      context = {
        'loginUser': loginUser,
        'applyUsers': applyUsers,
      }
      return TemplateResponse(request, 'accounts/admin/buyUserAdd.html', context)


  def post(self, request, **kwargs):

    next = self.request.POST.get('next', '')

    if next.find('ToEditPermission') >=0: # リストで選択されたユーザーの設定を表示する

      editedUser = UserModel.objects.get(pk=next.split('_')[1])
      print(f'editedUser={editedUser} in BuyUserAddView_admin')

      context = {
        'flag_scene': 'whenJoining',
        'editedUser': editedUser,
        'form': PermissionUpdateForm_admin(), 
      }
      return TemplateResponse(request, 'accounts/admin/permissionUpdate.html', context)
    

    if next.find('ToApproveUser') >= 0:
      print(f'pass1 ここ通っているのか in BuyUserAddView_admin')

      applyUser = UserModel.objects.get(pk=next.split('_')[1])
      #buyEntity = LegalEntity.objects.get(pk=applyUser.entity_id)

      if applyUser.addStatus == 1 or applyUser.addStatus == 3:

        applyUser.addStatus = 2
        applyUser.addStatus_char = '承認済み'

        applyUser.is_active = True #ここでログインできるようになる
        applyUser.joined_at = timezone.now()

        applyUser.save()

        # ここからは申請者に参加が認められたことを伝えるメール送信
        utils.sendEmail_common('accounts/admin/mail/buyUserAddReplyYes', '', [applyUser.email])

        messages.add_message(self.request,
          messages.SUCCESS, "新しいパートナーが加わりました。") 
        
        return TemplateResponse(request, 'accounts/admin/mypage.html')

      else: # ここは通らないはず

        messages.add_message(self.request,
          messages.WARNING, "システムエラー（想定外の処理になっています）。") 

        if self.request.session.get('flag_frWhere') == 1:
          context = {
            'applyUser': applyUser,
          }     
          return TemplateResponse(request, 'accounts/admin/buyUserAdd.html', context)


        if self.request.session.get('flag_frWhere') == 2:
          #loginUser = UserModel.objects.get(email=self.request.user)

          applyUsers =UserModel.objects.filter(
            Q(type1=1) & (Q(addStatus=1) | Q(addStatus=3))).order_by('-created_at')

          context = {
           'applyUsers': applyUsers,
          }
          return TemplateResponse(request, 'accounts/admin/buyUserAdd.html', context)    


    if next.find('ToRefuseUser') >= 0:

      print(f'pass1 nextValue={next} after if next=ToRefuseUser def post BuyUserAddView_admin')
      loginUser = UserModel.objects.get(email=self.request.user)
      applyUser = UserModel.objects.get(pk=next.split('_')[1])

      applyUser.addStatus = 3
      applyUser.addStatus_char = "否認済み"

      applyUser.save()

      # 否認されたことを通知する
      utils.sendEmail_common('accounts/admin/mail/buyUserAddReplyNo', '', [applyUser.email])

      # 承認者が申請メールからアプリに入る場合（個別申請データのみ表示）
      if self.request.session.get('flag_frWhere') == 1:
        context = {
          'loginUser': loginUser,
          'applyUser': applyUser,
        }     
        return TemplateResponse(request, 'accounts/admin/buyUserAdd.html', context)


      # マイページからアプリに入る場合（承認申請データをすべて表示）
      if self.request.session.get('flag_frWhere') == 2:
        #loginUser = UserModel.objects.get(email=self.request.user)

        applyUsers =UserModel.objects.filter(
          Q(type1=1) & (Q(addStatus=1) | Q(addStatus=3))).order_by('-created_at')

        context = {
          'loginUser': loginUser,
          'applyUsers': applyUsers,
        }
        return TemplateResponse(request, 'accounts/admin/buyUserAdd.html', context)    
    
    print(f'pass2 本当はここは通らないんだけど！ in BuyUserAddView_admin')



""" ① mypageから「ユーザーごとの権限」を確認・編集する """
""" ② ユーザー追加時の権限設定の対応（def postでの対応） """
class PermissionSetsView_buyer(generic.View):

  def get(self, request, **kwargs):  #selfはメソッドを呼んだインスタンス自体

    loginUser = UserModel.objects.get(email=self.request.user)
    entity = LegalEntity.objects.get(pk=loginUser.entity_id)
    print(f'loginUser.id={loginUser.id}')
    print(f'loginUser.entity_id={loginUser.entity_id}')

    #entityUsers = entity.entity_users.all()
    entityUsers = UserModel.objects.filter(
      Q(entity=entity) & (Q(addStatus=2) | Q(addStatus=3)))
    # 既にユーザー追加が承認・否認されたデータを抽出

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

        editedUser = UserModel.objects.get(pk=next1.split('_')[1])

        #char_canApproveAll = editedUser.canApproveAll
        #char_canApproveChg = editedUser.canApproveChg
        #char_canApproveQpay = editedUser.canApproveQpay

        init_dict = {
        } # テンプレートでは「editedUser」の情報を基にJavaScriptでトグルを操作
        context = {
          'editedUser': editedUser,
          'form': PermissionUpdateForm_buyer(initial=init_dict),
        }
        return TemplateResponse(request, 'accounts/buyer/permissionUpdate.html', context)


    next2 = self.request.POST.get('next2', None)

    if next2 != None:

      " 下記２パターンに対応 "
      " ① PermissionSet：マイページからの権限変更 "
      " ② PermissionSetWhenJoining：ユーザー追加時の権限設定 "

      if next2.find('PermissionSet') >= 0:

        editedUser = UserModel.objects.get(pk=next2.split('_')[1])

        char_canApproveAll = self.request.POST.get('canApproveAll', None)
        char_canApproveChg = self.request.POST.get('canApproveChg', None)
        char_canApproveQpay = self.request.POST.get('canApproveQpay', None)

        """ 「すべて」権限者を一人は残すようにする """
        cnt_canApproveAll = UserModel.objects.filter(
          entity=editedUser.entity, canApproveAll=True).count()

        if editedUser.canApproveAll == True and cnt_canApproveAll == 1:
          if char_canApproveAll != "True":
            messages.add_message(self.request,
              messages.WARNING, 'すべての権限を持つ管理者が一人は必要です。') 

            context = {
              'editedUser': editedUser,
              'form': PermissionUpdateForm_buyer(),
            }
            return TemplateResponse(request, 'accounts/seller/permissionUpdate.html', context)


        if char_canApproveAll == "True":
          editedUser.canApproveAll = True
        else: editedUser.canApproveAll = False

        if char_canApproveChg == "True":
          editedUser.canApproveChg = True
          print(f'pass1 canApproveChg={char_canApproveChg}')
        else:
          editedUser.canApproveChg = False
          print(f'pass2 canApproveChg={char_canApproveChg}')


        if char_canApproveQpay == "True":
          editedUser.canApproveQpay = True
        else: editedUser.canApproveQpay = False

        editedUser.save()

        loginUser = UserModel.objects.get(email=self.request.user)

        if next2.find('WhenJoining') == -1: # 通常の権限設定の場合

          entity = LegalEntity.objects.get(pk=editedUser.entity_id)
          entityUsers = entity.entity_users.all()

          context = {
            'loginUser': loginUser,  # 承認・変更の権限があるかを確認
            'entityUsers': entityUsers,
          }
          return TemplateResponse(request, 'accounts/admin/permissionList.html', context)

        else: # ユーザー参加承認時の権限設定の場合
    
          return HttpResponseRedirect(
            reverse_lazy('accounts:userAdd_buyer', kwargs={'applyUser_id': editedUser.id}))


""" mypageから「ユーザーごとの権限」を確認・編集する """
class PermissionSetsView_seller(generic.View):

  def get(self, request, **kwargs):  #selfはメソッドを呼んだインスタンス自体

    loginUser = UserModel.objects.get(email=self.request.user)
    entity = LegalEntity.objects.get(pk=loginUser.entity_id)
    print(f'loginUser.id={loginUser.id}')
    print(f'loginUser.entity_id={loginUser.entity_id}')
    #entityUsers = entity.entity_users.all()
    entityUsers = UserModel.objects.filter(
      Q(entity=entity) & (Q(addStatus=2) | Q(addStatus=3)))
    # 既にユーザー追加が承認・否認されたデータを抽出

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

        editedUser = UserModel.objects.get(pk=next1.split('_')[1])

        char_canApproveAll = editedUser.canApproveAll
        char_canApproveChg = editedUser.canApproveChg
        char_canApproveQpay = editedUser.canApproveQpay

        init_dict = {
        } # テンプレートでは「editedUser」の情報を基にJavaScriptでトグルを操作
        context = {
          'editedUser': editedUser,
          'form': PermissionUpdateForm_seller(initial=init_dict),
        }
        return TemplateResponse(request, 'accounts/seller/permissionUpdate.html', context)


    next2 = self.request.POST.get('next2', None)
    form = PermissionUpdateForm_seller(self.request.POST)
    form.is_valid() # canApproveAll=Trueの人が一人はいるかバリデーションする

    if next2 != None:

      if next2.find('PermissionSet') >= 0: # 選択されたユーザーの設定を更新

        editedUser = UserModel.objects.get(pk=next2.split('_')[1])

        char_canApproveAll = self.request.POST.get('canApproveAll', None)
        char_canApproveChg = self.request.POST.get('canApproveChg', None)
        char_canApproveQpay = self.request.POST.get('canApproveQpay', None)

        """ 「canApproveAll==True」の権限者を一人は残すようにする """
        cnt_canApproveAll = UserModel.objects.filter(entity=editedUser.entity, canApproveAll=True).count()

        if editedUser.canApproveAll == True and cnt_canApproveAll == 1:
          if char_canApproveAll != "True":
            messages.add_message(self.request,
              messages.WARNING, 'すべてに権限を持つ管理者が一人は必要です。') 

            context = {
              'editedUser': editedUser,
              'form': PermissionUpdateForm_seller(),
            }
            return TemplateResponse(request, 'accounts/seller/permissionUpdate.html', context)


        if char_canApproveAll == "True":
          editedUser.canApproveAll = True
        else: editedUser.canApproveAll = False

        if char_canApproveChg == "True":
          editedUser.canApproveChg = True
        else: editedUser.canApproveChg = False

        if char_canApproveQpay == "True":
          editedUser.canApproveQpay = True
        else: editedUser.canApproveQpay = False

        editedUser.save()

        loginUser = UserModel.objects.get(email=self.request.user)

        if next2.find('WhenJoining') == -1: # 通常の権限変更の場合
        
          entity = LegalEntity.objects.get(pk=editedUser.entity_id)
          entityUsers = entity.entity_users.all()

          context = {
            'loginUser': loginUser,
            'entityUsers': entityUsers,
          }
          return TemplateResponse(request, 'accounts/admin/permissionList.html', context)

        else:  # ユーザー参加承認時の権限設定の場合
    
          return HttpResponseRedirect(
            reverse_lazy('accounts:userAdd_seller', kwargs={'applyUser_id': editedUser.id}))



""" mypageから「ユーザーごとの権限」を確認・編集する """
class PermissionSetsView_admin(generic.View):
# ★★★ 2509025作成開始

  def get(self, request, **kwargs):  #selfはメソッドを呼んだインスタンス自体

    loginUser = UserModel.objects.get(email=self.request.user)
    entity = LegalEntity.objects.get(pk=loginUser.entity_id)
    print(f'loginUser.id={loginUser.id}')
    print(f'loginUser.entity_id={loginUser.entity_id}')

    #entityUsers = entity.entity_users.all()
    entityUsers = UserModel.objects.filter(
      Q(entity=entity), (Q(addStatus=2) | Q(addStatus=3)))
    # ユーザー追加のステータスが承認・否認のものを抽出

    context = {
      'loginUser': loginUser,
      'entity': entity,
      'entityUsers': entityUsers,
    }
    return TemplateResponse(request, 'accounts/admin/permissionList.html', context)


  def post(self, request):  #selfはメソッドを呼んだインスタンス自体

    next1 = self.request.POST.get('next1', None)

    if next1 != None:

      if next1.find('Edit') >=0: # リストで選択されたユーザーの設定を表示する

        editedUser = UserModel.objects.get(pk=next1.split('_')[1])

        char_canApproveAll = editedUser.canApproveAll
        char_canApproveChg = editedUser.canApproveChg
        char_canApproveQpay = editedUser.canApproveQpay

        init_dict = {
        }
        context = {
          'editedUser': editedUser,
          'form': PermissionUpdateForm_seller(initial=init_dict),
        }
        return TemplateResponse(request, 'accounts/admin/permissionUpdate.html', context)


    next2 = self.request.POST.get('next2', None)
    form = PermissionUpdateForm_seller(self.request.POST)
    form.is_valid() # canApproveAll=Trueの人が一人はいるかバリデーションする

    if next2 != None:

      if next2.find('PermissionSet') >= 0: # 選択されたユーザーの設定を更新
        print(f'pass1 next2={next2} if next2.find(PermissionSet) def post in PermissionSettinsView_admin')

        editedUser = UserModel.objects.get(pk=next2.split('_')[1])
        print(f'editedUser={editedUser} in PermissionSetsView_admin')

        char_canApproveAll = self.request.POST.get('canApproveAll', None)
        char_canApproveChg = self.request.POST.get('canApproveChg', None)
        char_canApproveQpay = self.request.POST.get('canApproveQpay', None)

        """ 「すべて」権限者を一人は残すようにする """
        cnt_canApproveAll = UserModel.objects.filter(
          entity=editedUser.entity, canApproveAll=True).count()

        if editedUser.canApproveAll == True and cnt_canApproveAll == 1:
          if char_canApproveAll != "True":
            message = "「すべて」の権限者が一人は必要です。"
            messages.add_message(self.request, messages.WARNING, message) 

            context = {
              'editedUser': editedUser,
              'form': PermissionUpdateForm_seller(),
            }
            return TemplateResponse(request, 'accounts/admin/permissionUpdate.html', context)


        if char_canApproveAll == "True":
          editedUser.canApproveAll = True
        else: editedUser.canApproveAll = False

        if char_canApproveChg == "True":
          editedUser.canApproveChg = True
          print(f'pass3 canApproveChg=True')
        else:
          editedUser.canApproveChg = False
          print(f'pass4 canApproveChg=False')


        if char_canApproveQpay == "True":
          editedUser.canApproveQpay = True
        else: editedUser.canApproveQpay = False

        editedUser.save()

        loginUser = UserModel.objects.get(email=self.request.user)
        if next2.find('WhenJoining') == -1: # 通常の権限変更の場合
    
          entity = LegalEntity.objects.get(pk=editedUser.entity_id)
          entityUsers = entity.entity_users.all()

          context = {
            'loginUser': loginUser,
            'entityUsers': entityUsers,
          }
          return TemplateResponse(request, 'accounts/admin/permissionList.html', context)


        else: # ユーザーの参加承認における権限設定

          return HttpResponseRedirect(
            reverse_lazy('accounts:buyUserAdd_admin', kwargs={'applyUser_id': editedUser.id}))



"""ログインした後に呼ばれるビュー"""
class MyPageView_admin(generic.DetailView):

  model = CustomUser
  template_name = "accounts/admin/mypage.html"

  
  def get(self, request, *args, **kwargs):
    if request.method != "GET":
      return HttpResponseNotAllowed("GET")

    adminUser_id = self.request.session['adminUser_id']  
    adminUser = UserModel.objects.get(pk= adminUser_id)

    # 「URLパラメーターがある場合」と「ない場合（ログインから）」に分ける   
    #try:
    #  user = UserModel.objects.get(pk=self.kwargs['user_id'])
    #except:
    #  print(f'request.user={request.user} def get in MyPageView_admin')
    #  user = UserModel.objects.get(email=self.request.user) 
  
    if adminUser.type1 != 3:

      if adminUser.type1 == 1:
        message = "パートナーで登録されています。パートナーでログインして下さい。"
        messages.add_message(request, messages.INFO, message) 
        logout(request)
        return HttpResponseRedirect(reverse('accounts:login', 1))

      if adminUser.type1 == 2:
        message = "ゲストで登録されています。ゲストでログインして下さい。"
        messages.add_message(request, messages.INFO, message) 
        logout(request)
        return HttpResponseRedirect(reverse('accounts:login', 2))

    TwoWeeksAgo = datetime.datetime.now() - datetime.timedelta(days=14)

    # ①前払い未処理（送金待ち）の件数を抽出
    if adminUser.canApproveAll == True or adminUser.canApproveQpay == True:
      cnt_toBePayed_qpay = QpayTx.objects.filter(
        (Q(txStatus_int=1) | Q(txStatus_int=2) | Q(txStatus_int=3))
        & Q(created_at__gte=TwoWeeksAgo)).count()
    else: cnt_toBePayed_qpay = 0

    print(f'cnt_toBePayed_qpay={cnt_toBePayed_qpay} in MyPageView_admin')
  
    
    # パートナーからのユーザー追加の承認依頼の件数を抽出
    if adminUser.canApproveAll == True or adminUser.canApproveChg == True:
      cnt_toBeApproved_add = UserModel.objects.filter(
        Q(type1=1) & (Q(addStatus=1) | Q(addStatus=3))).count()
    else: cnt_toBeApproved_add = 0
    print(f'cnt_toBeApproved_add={cnt_toBeApproved_add}')

    if adminUser.canApproveAll == True or adminUser.canApproveChg == True:
      cnt_toBeApproved_info = CorpInfo.objects.filter(status=2).count()
    else: cnt_toBeApproved_info = 0

    return TemplateResponse(
      request, "accounts/admin/mypage.html", 
      {
        "user": adminUser,
        "cnt_toBePayed_qpay": cnt_toBePayed_qpay,
        "cnt_toBeApproved_add": cnt_toBeApproved_add,
        "cnt_toBeApproved_info": cnt_toBeApproved_info,
      }) 



"""ログインした後に呼ばれるビュー"""
class MyPageView_buyer(generic.DetailView):

  model = CustomUser
  template_name = "accounts/buyer/mypage.html"
  form_class = MyPageForm_buyer
  
  def get(self, request, *args, **kwargs):

    if request.method != "GET":
      return HttpResponseNotAllowed("GET")

    # 「URLパラメーターがある場合」と「ない場合（ログインから）」に分ける   
    if 'user_id' in self.kwargs:
      loginUser = UserModel.objects.get(pk=self.kwargs['user_id'])
    else:
      if self.request.user.is_authenticated:
        loginUser = UserModel.objects.get(email=self.request.user) 
      else:
        print(f'ログイン出来てません。 def get in MyPageView_buyer')

    print(f'request.user={self.request.user} def get in MyPageView_buyer')
    if loginUser.type1 != 1:

      if loginUser.type1 == 2:
        message = "ゲストで登録されています。ゲストでログインして下さい。"
        messages.add_message(request, messages.INFO, message) 
        logout(request)
        return TemplateResponse(request, "accounts/seller/login.html", {'form':MyLoginForm})

      if loginUser.type1 == 3:
        message = "スタッフで登録されています。スタッフでログインして下さい。"
        messages.add_message(request, messages.INFO, message) 
        logout(request)
        return TemplateResponse(request, "accounts/admin/login.html", {'form':MyLoginForm})

    #TwoWeeksAgo = datetime.datetime.now() - datetime.timedelta(days=14)

    # 前払いの「承認待ち」「否認」のデータの件数を抽出
    if loginUser.canApproveAll == True or loginUser.canApproveQpay == True:

      cnt_toBeApproved_qpay = QpayTx.objects.filter(
        Q(buyEntity=loginUser.entity)
        & (Q(txStatus_int=1) | Q(txStatus_int=3))).count()
      
    else: cnt_toBeApproved_qpay = 0

    # ユーザー追加の「承認待ち」「否認」のデータの件数を抽出
    if loginUser.canApproveAll == True or loginUser.canApproveChg == True:
      cnt_toBeApproved_add = UserModel.objects.filter(
        Q(entity=loginUser.entity)
        & (Q(addStatus=1) | Q(addStatus=3))).count()
      
    else: cnt_toBeApproved_add = 0
    
    print(f'cnt_toBeApproved_qpay = {cnt_toBeApproved_qpay} in get of MypageView_buyer')
    print(f'cnt_toBeApproved_add = {cnt_toBeApproved_add} in get of MypageView_buyer')

    firstOfThisMonth = date.today().replace(day=1)
    firstOfNextMonth = firstOfThisMonth + relativedelta(months=+1)

    query_tx = QpayTx.objects.filter(
      buyEntity=loginUser.entity,
      txStatus_int = 2,
      advanced_at__gte = firstOfThisMonth,
      advanced_at__lt = firstOfNextMonth)

    cnt_advanced = query_tx.count
    paybacked_at = (date.today() + relativedelta(months=+1)).replace(day=7)
    totalAdvanceAmount = query_tx.aggregate(Sum('advance_amount'))

    return TemplateResponse(
      request, "accounts/buyer/mypage.html",
      {
        'loginUser': loginUser,
        #'buyEntity': buyEntity,
        'cnt_advanced': cnt_advanced, # 前払いされた件数
        'totalAdvancedAmount': totalAdvanceAmount,
        'paybacked_at': paybacked_at,
        'cnt_toBeApproved_qpay': cnt_toBeApproved_qpay, 
        'cnt_toBeApproved_add': cnt_toBeApproved_add,
      }
    ) 


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
      loginUser = UserModel.objects.get(pk=self.kwargs['user_id'])
    except:
      print(f'request.user={request.user} def get in MyPageView_seller')
      loginUser = UserModel.objects.get(email=self.request.user) 

    if loginUser.type1 != 2:

      if loginUser.type1 == 1:
        message = "パートナーで登録されています。パートナーでログインして下さい。"
        messages.add_message(request, messages.INFO, message) 
        logout(request)
        return TemplateResponse(request, "accounts/buyer/login.html", {'form':MyLoginForm})

      if loginUser.type1 == 3:
        message = "スタッフで登録されています。スタッフでログインして下さい。"
        messages.add_message(request, messages.INFO, message) 
        logout(request)
        return TemplateResponse(request, "accounts/admin/login.html", {'form':MyLoginForm})

    #TwoWeeksAgo = datetime.datetime.now() - datetime.timedelta(days=14)

    # ユーザー追加の未処理（承認待ち）データを抽出
    if loginUser.canApproveAll == True or loginUser.canApproveChg == True:
      cnt_toBeApproved_add = UserModel.objects.filter(
        Q(entity=loginUser.entity)
        & (Q(addStatus=1) | Q(addStatus=3))).count()
    else: cnt_toBeApproved_add = 0

    return TemplateResponse(
      request, "accounts/seller/mypage.html",
      {
        'loginUser': loginUser,
        #'sellEntity': sellEntity,
        'cnt_toBeApproved_add': cnt_toBeApproved_add,
      }
    ) 


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
class BankAccountCreateView_before(LoginRequiredMixin, generic.TemplateView):

  login_url = '/accounts/login_seller/'
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
  

class BankAccountCreateView(generic.CreateView):

  login_url = '/accounts/login_seller/'
  model = BankAccount
  form_class = BankAccountForm
  #template_name='accounts/seller/bankAccountCreate1.html'
  dict_banks = BankAccount.MakeBanksDict()
  dict_bankCode_branches = BankAccount.MakeBanksBranchesDict()

  def get(self, request, *args, **kwargs):

    print(f'self.request.user={self.request.user}')
    sellUser = UserModel.objects.get(email=self.request.user) 

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


    if sellEntity.bankAccount_flag == 1: # 受取口座が未設定の場合

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

    else:
    # entity.bankAccount_flag == 1のとき（受取口座が設定済み場合）
    # 既に口座設定がなされている場合は、表示するようフォームに初期値セット
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
      

  def post(self, request, *args, **kwargs):

    # 既に口座設定済みの方の処理
    WhichAccount = self.request.POST.get('WhichAccount', '')
    if WhichAccount:

      if WhichAccount.find('ThisAccount') >= 0:
        print(f'pass1 WhichAccount={WhichAccount}')
        return HttpResponseRedirect(reverse_lazy('accounts:mypage_seller'))
      

      if WhichAccount.find('NewAccount') >= 0:
      
        print(f'pass2 別の口座設定 WhichAccount={WhichAccount} post in BankAccountCreateView')
        sellUser = UserModel.objects.get(pk=WhichAccount.split('_')[1]) 
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

        sellUser = UserModel.objects.get(pk=search.split('_')[1]) 
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

        sellUser = UserModel.objects.get(pk=search.split('_')[1]) 
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

        sellUser = UserModel.objects.get(pk=next.split('_')[1]) 
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

        sellUser = UserModel.objects.get(pk=next.split('_')[1]) 
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

        sellUser = UserModel.objects.get(pk=next.split('_')[1]) 
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

        sellUser = UserModel.objects.get(pk=next.split('_')[1]) 
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

        sellUser = UserModel.objects.get(pk=next.split('_')[1]) 
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
class InfoEditView_buyer(generic.DetailView):

  def get(self, request, *args, **kwargs):

    try:    # 通常ケース（管理画面がログアウトされていないとワークせずエラーケースに）
      buyUser = UserModel.objects.get(email=self.request.user)

      # ユーザー追加の承認依頼の件数を抽出する 
      if buyUser.canApproveAll == True or buyUser.canApproveChg == True:
        cnt_toBeApproved_add = UserModel.objects.filter(
          Q(entity=buyUser.entity)
          & (Q(addStatus=1) | Q(addStatus=3))).count()
      else: cnt_toBeApproved_add = 0

    except UserModel.DoesNotExist:

      # データが存在しない場合の処理
      messages.add_message(request, messages.WARNING, "ユーザー（self.request.user）が認識されていません") 
      return HttpResponseRedirect(reverse('accounts:login_buyer'))
    

    context = {
      "cnt_toBeApproved_add": cnt_toBeApproved_add,
    }
    return TemplateResponse(request, "accounts/buyer/infoEdit.html", context) 


"""メインメニューから呼ばれる登録情報変更ビュー"""
class InfoEditView_seller(generic.DetailView):
  
  def get(self, request, *args, **kwargs):

    try:  # 通常ケース（管理画面がログアウトされていないとワークせずエラーケースに）
      sellUser = UserModel.objects.get(email=self.request.user)

      if sellUser.canApproveAll == True or sellUser.canApproveChg == True:

        #TwoWeeksAgo = datetime.datetime.now() - datetime.timedelta(days=14)
        cnt_toBeApproved_add = UserModel.objects.filter(
        Q(entity=sellUser.entity)
        & (Q(addStatus=1) | Q(addStatus=3))).count()

      else: cnt_toBeApproved_add = 0
      
    except UserModel.DoesNotExist:

      # データが存在しない場合の処理
      messages.add_message(request, messages.WARNING, "ユーザー（self.request.user）が認識されていません") 

    context = {
      'sellUser': sellUser,
      'cnt_toBeApproved_add': cnt_toBeApproved_add,
    }
    return TemplateResponse(request, "accounts/seller/infoEdit.html", context) 


"""メインメニューから呼ばれる登録情報変更ビュー"""
class InfoEditView_admin(generic.DetailView):
  
  def get(self, request, *args, **kwargs):

    try:  # 通常ケース（管理画面がログアウトされていないとワークせずエラーケースに）
      adminUser = UserModel.objects.get(email=self.request.user)
      print(f'request.user={request.user} def get in InfoEditView_admin')

      # パートナーからのユーザー追加の承認依頼の件数を抽出する 
      if adminUser.canApproveAll == True or adminUser.canApproveChg == True:
        cnt_toBeApproved_add = UserModel.objects.filter(
          Q(type1=1) & (Q(addStatus=1) | Q(addStatus=3))).count()
      else: cnt_toBeApproved_add = 0

      if adminUser.canApproveAll == True or adminUser.canApproveChg == True:
        cnt_toBeApproved_info = CorpInfo.objects.filter(status=2).count()
      else: cnt_toBeApproved_info = 0

    except UserModel.DoesNotExist:

      # データが存在しない場合の処理
      messages.add_message(request, messages.WARNING, "ユーザー（self.request.user）が認識されていません") 


    context = {
      'adminUser': adminUser,
      'cnt_toBeApproved_add': cnt_toBeApproved_add,
      'cnt_toBeApproved_info': cnt_toBeApproved_info,
    }
    return TemplateResponse(request, "accounts/admin/infoEdit.html", context)




# ★★ 2026/04/29編集開始 ユーザー・エンティティの内容を変更する場合のビュー

class ProfileEditView_buyer(generic.UpdateView):

  def get(self, request, **kwargs):  #selfはメソッドを呼んだインスタンス自体

    user = UserModel.objects.get(email=self.request.user)
    entity = LegalEntity.objects.get(pk=user.entity_id)

    """ 申請中・申請差戻データがない場合 """
    if CorpInfo.objects.filter(
      Q(applyEntity=entity) & (Q(status=2) | Q(status=3))).exists() == False:

      init_dict = {
        'entityName' : entity.entityName,
        'representitive' : entity.representitive,
        'tel_entity' : entity.tel_entity,
            
        'zip_entity' : entity.zip_entity,
        'address1' : entity.address1,
        'address2' : entity.address2,
        'address3' : entity.address3,

        'firstName' : user.firstName,
        'lastName' : user.lastName,
        'firstName_kana' : user.firstName_kana,
        'lastName_kana' : user.lastName_kana,

        'tel_user' : user.tel_user,
        'department' : user.department,
        'title' : user.title,
      }
      context = {
        'step_edit': 1,
        'flag_pending': 0,
        #'frWhere': '',
        'form': ProfileEditForm_buyer(initial=init_dict),
      }
      return TemplateResponse(self.request, 'accounts/buyer/profileEdit.html', context)


    """ 既に申請中の場合 """
    if CorpInfo.objects.filter(applyEntity=entity, status=2).exists():

      corpInfo = CorpInfo.objects.select_related(
        'applyUser','applyEntity').get(applyEntity=entity, status=2)

      init_dict = {
        'entityName' : entity.entityName,
        'representitive' : entity.representitive,
        'tel_entity' : entity.tel_entity,
            
        'zip_entity' : entity.zip_entity,
        'address1' : entity.address1,
        'address2' : entity.address2,
        'address3' : entity.address3,

        'firstName' : user.firstName,
        'lastName' : user.lastName,
        'firstName_kana' : user.firstName_kana,
        'lastName_kana' : user.lastName_kana,

        'tel_user' : user.tel_user,
        'department' : user.department,
        'title' : user.title,
      }

      context = {
        'step_edit': 1,
        'flag_pending': 1,
        'frWhere': '',
        'corpInfo': corpInfo,
        'user': user,
        'form': ProfileEditForm_buyer(initial=init_dict), 
        }
      return TemplateResponse(self.request, 'accounts/buyer/profileEdit.html', context)


    """ 申請差戻データがある場合 """
    if CorpInfo.objects.filter(applyEntity=entity, status=3).exists():

      corpInfo = CorpInfo.objects.select_related(
        'applyUser','applyEntity').get(applyEntity=entity, status=3)

      init_dict = {
        'entityName' : corpInfo.entityName,
        'representitive' : corpInfo.representitive,
        'tel_entity' : corpInfo.tel_entity,
            
        'zip_entity' : corpInfo.zip_entity,
        'address1' : corpInfo.address1,
        'address2' : corpInfo.address2,
        'address3' : corpInfo.address3,

        'firstName' : user.firstName,
        'lastName' : user.lastName,
        'firstName_kana' : user.firstName_kana,
        'lastName_kana' : user.lastName_kana,

        'tel_user' : user.tel_user,
        'department' : user.department,
        'title' : user.title,
      }
      context = {
        'step_edit': 1,
        'flag_pending': 2,
        #'frWhere': '',
        'corpInfo': corpInfo,
        'form': ProfileEditForm_buyer(initial=init_dict),
      }
      return TemplateResponse(self.request, 'accounts/buyer/profileEdit.html', context)



  def post(self, request, *args, **kwargs):

    user = UserModel.objects.get(email=self.request.user)
    entity = LegalEntity.objects.get(pk=user.entity_id)

    form = ProfileEditForm_buyer(request.POST)
    # 260103 nextCaseを追加（①パートナー追加と②ユーザー追加に分ける）
    # 260301 ユーザー追加の場合はEntitySetform_buyerを利用（nextCaseをなくした）

    btnAction = self.request.POST.get('btnAction', None)
    if btnAction != None:

      user = UserModel.objects.get(email=self.request.user)
      entity = LegalEntity.objects.get(pk=user.entity_id)


      """ 会社情報の更新内容を確認する画面 """
      if btnAction.find('ToConfirm_corp') >= 0:

        if form.is_valid():
        # 下記①、②、③の順で実行
        # ①.is_valid()、②フォームでのclean、clean_<field>、③form.cleaned_data[]に格納

          cleaned_data = form.cleaned_data

          """ 申請中のデータがあるがある場合は処理をストップする """
          """ 基本的にここは通らないようにする """

          if CorpInfo.objects.filter(
            Q(applyEntity=entity) & (Q(status=2) | Q(status=3))).exists():
          # 申請中、申請差戻のデータがある場合は、申請不可とする
    
            messages.add_message(request, messages.WARNING, "申請中、又は差戻のデータがあります。") 

            return TemplateResponse(self.request, 'accounts/buyer/profileEdit.html',
            {'step_edit': 1, 'whatUpdate': '', 'user':user, 'form':form, })


          else: # 申請中のデータがない場合

            """ エビデンスが必要な場合の処理 """
            """ 入力データをCorpInfoに保存、corpInfo_idをセッションに保存 """
            " corpInfo_idはビュー内の後続処理でのエビデンス保存時に取り出す "

            flag_needEvidence = 0

            if entity.entityName != cleaned_data['entityName'] or \
              entity.representitive != cleaned_data['representitive'] or \
              entity.zip_entity != cleaned_data['zip_entity'] or \
              entity.address1 != cleaned_data['address1'] or \
              entity.address2 != cleaned_data['address2'] or \
              entity.address3 != cleaned_data['address3']:

              print(f'pass1 コーポレート情報変更')
              flag_needEvidence = 1

              " Qnee承認まで変更内容をCorpInfoに保存 "
              corpInfo = CorpInfo.objects.create()

              corpInfo.entityName = cleaned_data['entityName']
              corpInfo.representitive =cleaned_data['representitive']
              corpInfo.tel_entity = cleaned_data['tel_entity']
              corpInfo.zip_entity = cleaned_data['zip_entity']
              corpInfo.address1 = cleaned_data['address1']
              corpInfo.address2 = cleaned_data['address2']
              corpInfo.address3 = cleaned_data['address3']

              corpInfo.applyUser = user
              corpInfo.applyEntity = entity

              # 後続でエビデンスをアップロードした後、申請中（corpInfo.status=2）に変更

              corpInfo.save()

              self.request.session['corpInfo_id'] = corpInfo.id
              # エビデンスをアップロードする際にセッション通じでidを渡す


            " 下記はエビデンス要否に拘わらず行う処理 "
            context = {
              'step_edit': 2,
              'flag_needEvidence': flag_needEvidence,
              'user': user,
              'form' : form,
            }
            return TemplateResponse(
              self.request, 'accounts/buyer/profileEdit.html', context)

        else:
        #「if form.is_valid()==False」の場合の処理
        # 入力値は既に「form」に保存済みのため、formをテンプレートに渡す

          print(f'ここ来てる3（def post after if form.is_valid==False in class ProfileEditView_buyer）')

          context = {
            'step_edit': 1,
            'flag_pending': 0,
            #'frWhere': '',
            'user': user,
            'form': form,
          }
          return TemplateResponse(self.request,
            'accounts/buyer/profileEdit.html', context)


      # データ確認画面から入力画面に戻る時の処理 2025/02/14
      if btnAction.find('BackToInput') >= 0:

        context = {
          'step_edit': 1,
          'user': user,
          'form': form,
        }
        return TemplateResponse(self.request, 'accounts/buyer/profileEdit.html', context)


      # 代表者、住所を変更した場合にはエビデンスをアップロード
      if btnAction.find('ToSelectEvidence_corp') >= 0:

        context = {
          'step_upEvidence': 1,
          'form': InfoEvidenceForm,
        }
        return TemplateResponse(request, "accounts/buyer/profileEdit_evidence.html", context)


      if btnAction.find('ToEvidenceConfirm_corp') >= 0:

        corpInfo_id = self.request.session.get('corpInfo_id', None)
        corpInfo = CorpInfo.objects.get(pk=corpInfo_id)

        form = InfoEvidenceForm(request.POST, request.FILES)
        if form.is_valid():

          print(f'pass4 btnAction={btnAction} after form.is_valid()')

          corpInfo.evidence = form.cleaned_data.get('evidence')
          " 【メモ】フォームからデータを取り出す場合の取り方 "

          corpInfo.save()

          context = {
            'step_upEvidence': 2,
            'corpInfo': corpInfo,
          }
          return TemplateResponse(request, "accounts/buyer/profileEdit_evidence.html", context)
      
        else:
  
          context = {
            'step_upEvidence': 1,
            'form': form,}
          return TemplateResponse(request, "accounts/buyer/profileEdit_evidence.html", context)
    

      # エビデンスをアップロードし、Qneeへ申請
      if btnAction.find('ToApplyToQnee_corp') >= 0:

        corpInfo_id = self.request.session.get('corpInfo_id', None)
        if corpInfo_id != None:

          corpInfo = CorpInfo.objects.select_related('applyUser','applyEntity').get(pk=corpInfo_id)
          corpInfo.status = 2 # 申請中のステータスに変更

          corpInfo.save()

          # メール送付の処理
          qneeUsers = UserModel.objects.filter(
            Q(type1=3) & (Q(canApproveAll=True) | Q(canApproveChg=True)))

          for eachUser in qneeUsers:

            context1 = {
              'afterLogin': 'corpInfoApply',
              'token': dumps(corpInfo.pk), 
              'qneeUser': eachUser,
              'applyEntityName': corpInfo.applyEntity.entityName,
              'afterLogin': 'corpInfoApply',}
            utils.sendEmail_common('accounts/buyer/mail/corpInfoApply', '', [eachUser.email], context1)
  
          messages.add_message(request, messages.SUCCESS,
            'キユーニーに会社情報更新の申請しました。')

          return TemplateResponse(request, "accounts/buyer/mypage.html", {},)

        else:

          messages.add_message(request, messages.DANGER, "エラー。該当データが見つかりません。") 

          return TemplateResponse(self.request, 'accounts/buyer/profileEdit.html',
          {'step_edit': 1, 'whatUpdate': '', 'user':user, 'form':form, })


      """ 会社情報の申請を取り下げる処理 """
      """ ①申請中の場合、②申請差戻の場合の2パターンに対応する """
      if btnAction.find('ToDropUpdate') >= 0:

        corpInfo_id = btnAction.split('_')[1]
        print(f'pass3 corpInfo_id={corpInfo_id} after ToDoropUpdate')

        corpInfo = CorpInfo.objects.get(pk=corpInfo_id)
        corpInfo.delete()
        #corpInfo.status = 1 # 未処理のステータスに変更
        #corpInfo.save()

        return HttpResponseRedirect(reverse_lazy('accounts:profileEdit_buyer'))


      """ ユーザー情報の変更内容を確認する画面 """
      if btnAction.find('ToConfirm_user') >= 0:

        if form.is_valid():

          # 下記①、②、③の順で実行
          # ①.is_valid()、②フォームでのclean、clean_<field>、③form.cleaned_data[]に格納

          context = {
            'step_edit': 2,
            'whatUpdate': 'userInfo',
            'flag_needEvidence': 0,
            'user': user,
            'form' : form,
          }         
          return TemplateResponse(
            self.request, 'accounts/buyer/profileEdit.html', context)

        else: #バリデーションエラーの時に通る

          print(f'ここ来てる3（def post after if not form.is_valid in class ProfileEditView_buyer）')
          return TemplateResponse(self.request, 'accounts/buyer/profileEdit.html',
            {'step_edit': 1, 'whatUpdate': 'userInfo', 'user':user, 'form':form, })


      # データ確認画面から入力画面に戻る時の処理 2025/02/14
      if btnAction.find('BackToInput') >= 0:

        context = {
          'step_edit': 1,
          'user': user,
          'form': form,
        }
        return TemplateResponse(self.request, 'accounts/buyer/profileEdit.html', context)


      " 会社情報もユーザー情報も同時に扱う "
      if btnAction.find('ToSave') >= 0: 

        entity.entityName = self.request.POST['entityName']
        entity.representitive = self.request.POST['representitive']
        entity.tel_entity = self.request.POST['tel_entity']
        entity.zip_entity = self.request.POST['zip_entity']
        entity.address1 = self.request.POST['address1']
        entity.address2 = self.request.POST['address2']
        entity.address3 = self.request.POST['address3']

        entity.save()

        user.userName = \
          self.request.POST.get('lastName') + ' ' + self.request.POST.get('firstName')
        user.userName_kana = \
          self.request.POST.get('lastName_kana') + ' ' + self.request.POST.get('firstName_kana')

        # アプリで使うのはuseNameだが、名前を変更する場合があるので保存しておく
        user.lastName = self.request.POST.get('lastName')
        user.firstName = self.request.POST.get('firstName')
        user.lastName_kana = self.request.POST.get('lastName_kana')
        user.firstName_kana = self.request.POST.get('firstName_kana')

        user.tel_user = self.request.POST.get('tel_user', None)
        user.department = self.request.POST.get('department', None)
        user.title = self.request.POST.get('title', None)
      
        user.save()

        print(f'request.user.get_username={request.user.get_username} type2={user.type2}（def post ==confirm after form.is_valid in ProfileEditView_buyer）')

        return TemplateResponse(self.request, 'accounts/buyer/mypage.html', {})


class ProfileEditView_seller(generic.UpdateView):

  def get(self, request, **kwargs):  #selfはメソッドを呼んだインスタンス自体
  
    user = UserModel.objects.get(email=self.request.user)
    entity = LegalEntity.objects.get(pk=user.entity_id)

    init_dict = {
      'userName': '',
      'email': user.email,
      'tel_user': "",

      'entityName' : entity.entityName,
      'representitive' : entity.representitive,
      'tel_entity' : entity.tel_entity,
            
      'zip_entity' : entity.zip_entity,
      'address1' : entity.address1,
      'address2' : entity.address2,
      'address3' : entity.address3,

      'lastName' : user.lastName,
      'firstName' : user.firstName,
      'lastName_kana' : user.lastName_kana,
      'firstName_kana' : user.firstName_kana,

      'tel_user' : user.tel_user,
      'department' : user.department,
      'title' : user.title,

    }
    context = {
      'step_edit': 1,
      'frWhere': '',
      'user': user,
      'form': ProfileEditForm_seller(initial=init_dict),
    }
    return TemplateResponse(self.request, 'accounts/seller/profileEdit.html', context)


  def post(self, request, *args, **kwargs):

    user = UserModel.objects.get(email=self.request.user) 
    form = ProfileEditForm_seller(request.POST)
    # 260103 nextCaseを追加（①パートナー追加と②ユーザー追加に分ける）
    # 260301 ユーザー追加の場合はEntitySetform_sellerを利用（nextCaseをなくした）

    btnAction = self.request.POST.get('btnAction', None)

    if btnAction != None:

      """ 入力内容を確認する画面 """
      if btnAction.find('ToConfirm_corp') >= 0:

        if form.is_valid():
        # 下記①、②、③の順で実行
        # ①.is_valid()、②フォームでのclean、clean_<field>、③form.cleaned_data[]に格納

          cleaned_data = form.cleaned_data

          #if CorpInfo.objects.filter(applyEntity=entity).exists():
          #  CorpInfo.objects.filter(applyEntity=entity).delete()
          # データクリエイトの前に、これまでの利用してデータは削除

          " エビデンスが必要かチェック "
          flag_needEvidence = 0

          if entity.entityName != cleaned_data['entityName'] or \
            entity.representitive != cleaned_data['representitive'] or \
            entity.zip_entity != cleaned_data['zip_entity'] or \
            entity.address1 != cleaned_data['address1'] or \
            entity.address2 != cleaned_data['address2'] or \
            entity.address3 != cleaned_data['address3']:

            print(f'pass1 コーポレート情報変更')
            flag_needEvidence = 1

            " パートナー承認まで変更内容をCorpInfoに保存 "
            corpInfo = CorpInfo.objects.create()
            corpInfo.entityName = cleaned_data['entityName']
            corpInfo.representitive =cleaned_data['representitive']
            corpInfo.tel_entity = cleaned_data['tel_entity']
            corpInfo.zip_entity = cleaned_data['zip_entity']
            corpInfo.address1 = cleaned_data['address1']
            corpInfo.address2 = cleaned_data['address2']
            corpInfo.address3 = cleaned_data['address3']

            corpInfo.applyUser = user
            corpInfo.applyEntity = entity

            # エビデンスをアップデートした後、申請中（corpInfo.status = 2）とする

            corpInfo.save()

          context = {
            'step_edit': 2,
            'flag_needEvidence': flag_needEvidence,
            'whatUpdate': 'corpInfo',
            'user': user,
            'form' : form,
          }
          return TemplateResponse(
            self.request, 'accounts/buyer/profileEdit.html', context)


        else: #バリデーションエラーの時に通る

          print(f'ここ来てる3（def post after if not form.is_valid in class ProfileEditView_seller）')
          return TemplateResponse(self.request, 'accounts/seller/profileEdit.html',
            {'step_edit': 1, 'frWhere': '', 'user':user, 'form':form, })


      """ 入力内容を確認する画面 """
      if btnAction.find('ToConfirm') >= 0:

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
            'firstName' : cleaned_data['firstName'],
            'lastName_kana' : cleaned_data['lastName_kana'],
            'firstName_kana' : cleaned_data['firstName_kana'],

            'tel_user' : cleaned_data['tel_user'],
            'department' : cleaned_data['department'],
            'title' : cleaned_data['title'],
          }
          context = {
            'step_edit': 2,
            'frWhere': 'userInfoUpdate',
            'user': user,
            'form' : ProfileEditForm_seller(initial=init_dict),
          }         
          return TemplateResponse(
            self.request, 'accounts/seller/profileEdit.html', context)

        else: #バリデーションエラーの時に通る

          print(f'ここ来てる3（def post after if not form.is_valid in class ProfileEditView_seller）')
          return TemplateResponse(self.request, 'accounts/seller/profileEdit.html',
            {'step_edit': 1, 'frWhere': '', 'user':user, 'form':form, })


      # データ確認画面から入力画面に戻る時の処理 2025/02/14
      if btnAction.find('BackToInput') >= 0:

        user = UserModel.objects.get(email=self.request.user) 

        context = {
          'step_edit': 1,
          'user': user,
          'form': form,
        }
        return TemplateResponse(self.request, 'accounts/seller/profileEdit.html', context)


      if btnAction.find('ToSave') >= 0: # 確認した内容をデータベースに登録

        # 250802 フォームをモデルフォームから通常フォームに変更したことに伴い変更
        user = UserModel.objects.get(email=self.request.user) 

        entity = LegalEntity.objects.get(pk=user.entity_id)
        entity.entityName = self.request.POST['entityName']
        #entity.entityName = form.entityName 
        # この式はエラー（'EntityCreateForm_seller' object has no attribute 'entityName'）

        entity.representitive = self.request.POST['representitive']
        entity.tel_entity = self.request.POST['tel_entity']
        entity.zip_entity = self.request.POST['zip_entity']
        entity.address1 = self.request.POST['address1']
        entity.address2 = self.request.POST['address2']
        entity.address3 = self.request.POST['address3']

        entity.save()

        user.userName = \
          self.request.POST.get('lastName') + ' ' + self.request.POST.get('firstName')
        user.userName_kana = \
          self.request.POST.get('lastName_kana') + ' ' + self.request.POST.get('firstName_kana')

        # アプリで使うのはuseNameだが、名前を変更する場合があるので保存しておく
        user.lastName = self.request.POST.get('lastName')
        user.firstName = self.request.POST.get('firstName')
        user.lastName_kana = self.request.POST.get('lastName_kana')
        user.firstName_kana = self.request.POST.get('firstName_kana')

        user.tel_user = self.request.POST.get('tel_user', None)
        user.department = self.request.POST.get('department', None)
        user.title = self.request.POST.get('title', None)

        # ★★ 250824 Qneeに登録を承認するプロセスを入れる（Qneeでis_active=Trueにする）
        # ★★ 250824 Qneeに申請が見れるようにする
        
        user.save()

        print(f'request.user.get_username={request.user.get_username} type2={user.type2}（def post ==confirm after form.is_valid in EntityCreateView_seller）')

        return TemplateResponse(self.request, 'accounts/seller/mypage.html', {})
      

class CorpInfoUpdatePreView_admin(LoginRequiredMixin, generic.TemplateView):

  " 案内されたメールからアプリに入ってユーザー追加の承認をする場合の入口 "
  " tokenをapplyUser_idに変換して、CorpInfoUpdateView_buyerを呼ぶ "

  login_url = '/accounts/login_admin/'
  timeout_seconds = getattr(settings,  'ACTIVATION_TIMEOUT_SECONDS', 60*60*72)

  def get(self, request, *args, **kwargs):
  
    try:
      token_corpInfoID = self.kwargs.get('token')    # URLから<token>（暗号化されたuser_id）を取り出す（kwargsはdict型）   
      corpInfo_id = loads(token_corpInfoID, max_age=self.timeout_seconds)
      corpInfo = CorpInfo.objects.get(pk=corpInfo_id)

    except SignatureExpired:
      return HttpResponseBadRequest()

    #tokenが間違っている
    except BadSignature:
      return HttpResponseBadRequest()

    return HttpResponseRedirect(
      reverse_lazy('accounts:corpInfoUpdate_admin', kwargs={'corpInfo_id': corpInfo.id}))
  

class CorpInfoUpdateView_admin(LoginRequiredMixin, generic.TemplateView):

  """ パートナーの会社情報の更新を、Qneeが承認するためのビュー。"""
  """ ビューの呼ばれる方は２種類 """
  """ ①Qnee承認者が受領したメール内のリンクから②Qnee承認者のマイページから """
  """ ①申請者におけるAgreementConfirmView⇒②承認者へのメール⇒③メール内リンクから呼ばれる """
  """ Qnee承認者（self.request.user）と申請者の二者のユーザーidを維持が必要 """
  """ 最終編集 260516 """

  login_url = '/accounts/login_admin/'
  model = CustomUser

  """ Qneeの承認者が受領するメール内のリンクから呼ばれる """
  def get(self, request, **kwargs):  #selfはメソッドを呼んだインスタンス自体

    #loginUser = UserModel.objects.get(email=self.request.user)

    try: # CorpInfoUpdatePreView_admin経由（corpInfo_idの指定がある場合）

      corpInfo_id = self.kwargs.get('corpInfo_id')
      corpInfo = CorpInfo.objects.select_related(
        'applyUser', 'applyEntity').get(pk=corpInfo_id)

      # 「flag_frWhere」を不要にするように変更
      #self.request.session['flag_frWhere'] = 1
      # テンプレート側で「corpInfo_id指定あり」と認識するためセッションに保存
      # この場合は、該当データのみ表示する

      object_list = CorpInfo.objects.select_related(
        'applyUser', 'applyEntity').filter(status=2).order_by('-created_at')

      paginator = Paginator(object_list, 1)

      i = 1
      page_obj = paginator.page(i)
      for item in page_obj:
        if item.id != corpInfo.id:
          if page_obj.has_next:
            i = i + 1
            page_obj = paginator.page(i)
          print(f'合致するidがありました。id={corpInfo.id}')

          break


    except: # mypage経由で来る場合（corpInfo_idの指定がない場合）

      #self.request.session['flag_frWhere'] = 2
      # テンプレート側で「corpInfo_id指定なし」と認識するためセッションに保存
      # この場合は、該当データのみ表示する

      object_list = CorpInfo.objects.select_related(
        'applyUser', 'applyEntity').filter(status=2).order_by('-created_at')
      #self.request.session['corpInfo_id'] = None

      paginator = Paginator(object_list, 1)

      # URLからページネーション経由でページ番号を取得する場合
      page_number = self.request.GET.get('page_number', None)
      if page_number is None:
        # viewを呼ぶときにページ番号が指定されている場合  
        page_number = self.kwargs.get('page_number', 1)
        page_obj = paginator.page(page_number)

    context = {
      'step_process': 1,
      'corpInfo': object_list,
      'page_obj': page_obj,
      'last_page': paginator.num_pages
    }
    return TemplateResponse(request, 'accounts/admin/corpInfoUpdate.html', context)
      
 
  def post(self, request, **kwargs):

    #flag_frWhere = self.request.session.get('flag_frWhere', None)

    btnAction = self.request.POST.get('btnAction', None)
    if btnAction.find('ToApproveUpdate') >= 0:

      corpInfo_id = btnAction.split('_')[1]
      print(f'corpInfo_id={corpInfo_id}')
      corpInfo = CorpInfo.objects.select_related('applyUser', 'applyEntity').get(pk=corpInfo_id)
      
      if corpInfo.status == 2: # 申請中の場合

        applyEntity = LegalEntity.objects.get(pk=corpInfo.applyEntity_id)

        applyEntity.entityName = corpInfo.entityName
        applyEntity.representitive = corpInfo.representitive

        applyEntity.zip_entity = corpInfo.zip_entity
        applyEntity.address1 = corpInfo.address1
        applyEntity.address2 = corpInfo.address2
        applyEntity.address3 = corpInfo.address3

        applyEntity.save()

        corpInfo.status = 4 # 承認のステータスに変更
        corpInfo.save()

        context = {
          'applyUser': corpInfo.applyUser,
          'applyEntity': corpInfo.applyEntity,
        }
        # 会社情報が更新されたことを申請者（パートナー）に伝える
        utils.sendEmail_common('accounts/admin/mail/corpInfoUpdateYes', '', [corpInfo.applyUser.email], context)

        messages.add_message(self.request,
          messages.SUCCESS, "申請がキユーニーに承認され、会社情報が更新されました。")

        return HttpResponseRedirect(
          reverse_lazy('accounts:corpInfoUpdate_admin', kwargs={'corpInfo_id': corpInfo.id}))


      else: # corpInfo.status != 2の場合（ここは通らないはず）

        messages.add_message(self.request,
          messages.DANGER, "申請中のステータスのデータが見つかりません。") 

        return HttpResponseRedirect(
          reverse_lazy('accounts:corpInfoUpdate_admin', kwargs={}))


    ## ★★ 262528 以下工事中
    ## ToSendBack1で差戻理由を入力、ToSendBack2で差戻実行

    if btnAction.find('ToSendback1') >= 0:
      
      print(f'btnAction={btnAction}')
      corpInfo_id = btnAction.split('_')[1]
      #corpInfo = CorpInfo.objects.select_related('applyUser', 'applyEntity').get(pk=corpInfo_id)
      
      context = {
        'step_process': 2,
        'corpInfo_id': corpInfo_id,
        'FeedbackForm': FeedbackForm(), }
      return TemplateResponse(request, 'accounts/admin/corpInfoUpdate.html', context)


    if btnAction.find('ToSendback2') >= 0:

      corpInfo_id = btnAction.split('_')[1]
      print(f'corpInfo_id={corpInfo_id}')
      corpInfo = CorpInfo.objects.select_related('applyUser', 'applyEntity').get(pk=corpInfo_id)

      # 確認用
      sendbackReason_radio = self.request.POST.get('sendbackReason_radio')
      print(f'sendbackReason_radio={sendbackReason_radio}')

      form = FeedbackForm(self.request.POST)
      if form.is_valid(): 

        print(f'pass1 after if form.is_valid==True in CorpInfoUpdateView_admin')

        radioValue = self.request.POST.get('sendbackReason_radio', None)
        sendbackMessage = form.cleaned_data['sendbackMessage']

        if radioValue == 'option4':
          print(f'pass2 after if form.is_valid==True in CorpInfoUpdateView_admin')
          sendbackReason = form.cleaned_data['sendbackReason_text']
        else:
          print(f'pass3 after if form.is_valid==True in CorpInfoUpdateView_admin')
          if radioValue == 'option1': sendbackReason = '入力に誤りがある'
          if radioValue == 'option2': sendbackReason = '証明書類が適切でない'
          if radioValue == 'option3': sendbackReason = '画像の写りが不十分'

        corpInfo.status = 3 # 差戻のステータスに変更
        corpInfo.status_char = "差戻"
        corpInfo.sendbackReason = sendbackReason
        corpInfo.sendbackMessage = sendbackMessage

        corpInfo.save()
        print(f'corpInfo.status={corpInfo.status}')
        # 差戻されたことを通知する
        context = {
          'sendbackReasonText': sendbackReason,
          'sendbackMessage': sendbackMessage,
        }
        utils.sendEmail_common(
          'accounts/admin/mail/corpInfoSendback', '', [corpInfo.applyUser.email], context)

        messages.add_message(self.request,
          messages.SUCCESS, "差戻の処理が完了しました。") 

        return HttpResponseRedirect(
          reverse_lazy('accounts:corpInfoUpdate_admin', kwargs={}))

      else:
        print(f'pass2 after if form.is_valid==False in CorpInfoUpdateView_admin')


    
    print(f'pass2 本当はここは通らないんだけど！ in BuyUserAddView_admin')
    return HttpResponseRedirect(
      reverse_lazy('accounts:corpInfoUpdate_admin', kwargs={}))


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