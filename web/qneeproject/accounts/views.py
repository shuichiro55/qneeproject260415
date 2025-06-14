from django.contrib.auth import logout, get_user_model
from django.contrib.auth.views import \
  LoginView, PasswordChangeView, PasswordChangeDoneView
from .models import CustomUser, BankAccount
from .models import LegalEntity

from django.template.response import TemplateResponse
from django.urls import reverse, reverse_lazy

from django.shortcuts import redirect
from django.conf import settings

from django.views import generic
from .form import \
  MyLoginForm, UserCreateForm, \
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
from django.core.mail import send_mail

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
  success_url = reverse_lazy('accounts:password_change2_buyer')
  template_name = 'accounts/password_change_buyer.html'

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
  success_url = reverse_lazy('accounts:password_change2_seller')
  template_name = 'accounts/password_change_seller.html'

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
  success_url = reverse_lazy('accounts:password_change2_admin')
  template_name = 'accounts/password_change_admin.html'

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
    template_name = 'accounts/password_change2_buyer.html'


class MyPasswordChange2View_seller(PasswordChangeDoneView):
    """パスワードを変更したことを表示"""
    template_name = 'accounts/password_change2_seller.html'


class MyPasswordChange2View_admin(PasswordChangeDoneView):
    """パスワードを変更したことを表示"""
    template_name = 'accounts/password_change2_admin.html'


class UserCreateView_buyer(generic.CreateView):

  model = CustomUser
  template_name = 'accounts/user_create_buyer.html'
  form_class = UserCreateForm


  def get(self, request, **kwargs):  #selfはメソッドを呼んだインスタンス自体

    context = {
      'form' : self.form_class,
    }
    return TemplateResponse(request, 'accounts/user_create_buyer.html', context)  #ここでgetとするのは、おそらく親クラスでtemplate_nameを表示するように規定されている


  # CreateView（親クラス）で自動バリデーションが通ったときに実行される
  # ユーザーインスタンス生成・保存、type1,type2の登録、本登録用メールの発行を行う

  def post(self, request, **kwargs):  #selfはメソッドを呼んだインスタンス自体

    form = self.form_class(request.POST)

    if form.is_valid():

      user = form.save(commit=False)
      user.is_active = False

      user.type1 = 1  # パートナー：1、ゲスト：2、Qnee：3で登録 25/04/27

      user.save()
      print(f'ここまで来てる1 email={user.email} type2={user.type2} user.pk={user.pk} usr.passsword= {user.password}（def post if form.is_valid in class UserCreateView_buyer）')

      ### あとでsend_mailに切り替えるか検討 2025/04/27
      current_site = get_current_site(self.request)
      domain = current_site.domain
      context = {
        'protocol': self.request.scheme,
        'domain': domain,
        'token': dumps(user.pk),
        'user': user,
      }

      subject = render_to_string('accounts/mail/subject_buyer.txt', context)
      message = render_to_string('accounts/mail/message_buyer.txt', context)

      print(context)
      print(f'メールアドレス：{user.email}')
      user.email_user(subject, message)
     
      return redirect('accounts:user_create2_buyer')

    else:
  
      print(f'ここ来てる2（def post if form.is_valid=FALSE in class UserCreateView_buyer）')
      print(form.errors)

      context = {
        'form' : form,
      }
      return render(request, 'accounts/user_create_buyer', context)  #ここでgetとするのは、おそらく親クラスでtemplate_nameを表示するように規定されている


class UserCreateView_seller(generic.CreateView):

  model = CustomUser
  template_name = 'accounts/user_create_seller.html'
  form_class = UserCreateForm


  def get(self, request, **kwargs):  #selfはメソッドを呼んだインスタンス自体
  
    context = {
      'form' : self.form_class,
    }
    return TemplateResponse(request, 'accounts/user_create_seller.html', context)  #ここでgetとするのは、おそらく親クラスでtemplate_nameを表示するように規定されている


  # CreateView（親クラス）で自動バリデーションが通ったときに実行される
  # ユーザーインスタンス生成・保存、type1,type2の登録、本登録用メールの発行を行う

  def post(self, request, **kwargs):  #selfはメソッドを呼んだインスタンス自体

    form = self.form_class(request.POST)

    if form.is_valid():

      user = form.save(commit=False)
      user.is_active = False

      user.type1 = 2  # パートナー：1、ゲスト：2、Qnee：3で登録 25/04/27

      user.save()
      print(f'ここまで来てる1 email={user.email} type2={user.type2} user.pk={user.pk} usr.passsword= {user.password}（def post if form.is_valid in class UserCreateView_seller）')

      ### あとでsend_mailに切り替えるか検討 2025/04/27
      current_site = get_current_site(self.request)
      domain = current_site.domain
      context = {
        'protocol': self.request.scheme,
        'domain': domain,
        'token': dumps(user.pk),
        'user': user,
      }

      subject = render_to_string('accounts/mail/subject_seller.txt', context)
      message = render_to_string('accounts/mail/message_seller.txt', context)

      print(context)
      print(f'メールアドレス：{user.email}')
      user.email_user(subject, message)
     
      return redirect('accounts:user_create2_seller')

    else:
  
      print(f'ここ来てる2（def post if form.is_valid=FALSE in class UserCreateView_seller）')
      print(form.errors)

      context = {
        'form' : form,
      }
      return render(request, 'accounts/user_create_seller.html', context)  #ここでgetとするのは、おそらく親クラスでtemplate_nameを表示するように規定されている


class UserCreateView_admin(generic.CreateView):

  model = CustomUser
  template_name = 'accounts/user_create_admin.html'
  form_class = UserCreateForm

  def get(self, request, **kwargs):  #selfはメソッドを呼んだインスタンス自体

    context = {
      'form' : self.form_class,
    }
    return TemplateResponse(request, 'accounts/user_create_admin.html', context)  #ここでgetとするのは、おそらく親クラスでtemplate_nameを表示するように規定されている


  # CreateView（親クラス）で自動バリデーションが通ったときに実行される
  # ユーザーインスタンス生成・保存、type1,type2の登録、本登録用メールの発行を行う

  def post(self, request, **kwargs):  #selfはメソッドを呼んだインスタンス自体

    form = self.form_class(request.POST)

    if form.is_valid():

      user = form.save(commit=False)
      user.is_active = False

      user.type1 = 3  # パートナー：1、ゲスト：2、Qnee：3で登録 25/04/27
      user.type2 = 1  # 個人として登録
      user.is_active = True

      user.save()
      print(f'ここまで来てる1 email={user.email} type2={user.type2} user.pk={user.pk} usr.passsword= {user.password}（def post if form.is_valid in class UserCreateView_admin）')

      ### あとでsend_mailに切り替えるか検討 2025/04/27
      current_site = get_current_site(self.request)
      domain = current_site.domain
      context = {
        'protocol': self.request.scheme,
        'domain': domain,
        'token': dumps(user.pk),
        'user': user,
      }

      subject = render_to_string('accounts/mail/subject_admin.txt', context)
      message = render_to_string('accounts/mail/message_admin.txt', context)

      print(context)
      print(f'メールアドレス：{user.email}')
      user.email_user(subject, message)
     
      return redirect('accounts:user_create2_admin')

    else:
  
      print(f'ここ来てる2（def post if form.is_valid=FALSE in class UserCreateView_admin）')
      print(form.errors)

      context = {
        'form' : form,
      }
      return render(request, 'accounts/user_create_admin.html', context)  #ここでgetとするのは、おそらく親クラスでtemplate_nameを表示するように規定されている


"""ユーザー仮登録が完了し、メール送付したと伝えるテンプレート"""
class UserCreateView2_buyer(generic.TemplateView):
  template_name = 'accounts/user_create2_buyer.html'

class UserCreateView2_seller(generic.TemplateView):
  template_name = 'accounts/user_create2_seller.html'

class UserCreateView2_admin(generic.TemplateView):
  template_name = 'accounts/user_create2_admin.html'



""" 25/06/02（コーディング開始） ①パートナー登録するか、②既存パートナーにユーザー追加を選択 """
""" 上記①の場合はEntityCreateViewへ、上②の場合は既存パートナーのスーパーユーザーに登録申請 """

class EntitySetView_buyer(generic.TemplateView):

  model = UserEntityRelation
  form_class = EntitySetForm_buyer
  template_name = 'accounts/entity_set_buyer.html'
  timeout_seconds = getattr(settings,  'ACTIVATION_TIMEOUT_SECONDS', 60*60*24)

  """（ビューにおいて）GETリクエストを受け取ったときに呼び出される（実践Django P121）"""
  """ 処理：ゲストに送られたメールのURLをクリックされた時点で呼ばれる """
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
            
    if not user.is_active:
      user.is_active = True
      user.save()

    ###  ここからしたが工事中（25/06/08） ###

    buyerEntityname_dict =dict((str(idx), f) for idx, f in enumerate(LegalEntity.objects.filter(type1=1).values_list('entityname', flat=True), 1))
    print(f'buyerEntityname_dict={buyerEntityname_dict} def get in EntitySetView_buyer')

    init_dict = {
      'personname': "",
      'email': user.email,
      'tel': "",
    }

    form = self.form_class(initial=init_dict)
    context = {
      'form': form,
      'temporal_buyerEntityname': "",
      # コメント(25/06/08)：Selectボックスで未選択であることを示す。選択後はページ移動でデータ保持するために使う
      'buyerEntityname_dict': buyerEntityname_dict,
    }

    print(f'ここ来てる1 request.user={request.user} email={user.email} type2={user.type2}（get in class EntitySetView_buyer）')
        
    return TemplateResponse(request, 'accounts/entity_set_buyer.html', context)


  def post(self, request, *args, **kwargs):

    user = usermodel.objects.get(email=self.request.user) 

    form = self.form_class(request.POST)
    next = self.request.POST.get('next', '')

    if form.is_valid():
    # 「.is_valid()」の後、フォームでのclean、clean_<field>が実行され、
    # form.cleaned_data[]にデータが入る

      if next == 'ToEntityCreate': # 新規のパートナー登録へ

        # ★★★ Entityでは郵便番号、住所、代表者を登録するようにする 25/06/08 23:46
        # ★★★ ここで

        context = {
          'user': user,
          'form': EntityCreateForm_buyer,
        }
        return render(self.request, 'accounts/entity_create_buyer.html', context)

      if next == 'ToConfirm':  # 登録済みパートナーにユーザー追加

        tmp_entityname = self.request.POST.get('buyerSelect', "")
        entity = LegalEntity.objects.get(entityname=tmp_entityname)
        print(f'tmp_entityname={tmp_entityname} (def post of EntitySetView_buyer)')
        user.personname = form.personname
        user.save()

        UserEntityRelation = form.save(commit=False)
        UserEntityRelation.user = user
        UserEntityRelation.entity = entity 
        UserEntityRelation.save()

        if not user.is_active:
          user.is_active = True
          user.save()

        context = {
          'user': user,
          'entity': entity,
        }
        return render(self.request, 'accounts/entity_confirm_buyer.html', context)


    if next == 'back':
      print(f'ここ来てる4（def post after 「try-except:」 in class EntityCreateView_buyer）')
      return render(self.request, 'accounts/entity_create_buyer.html', {'form':form, 'user':user})
        
    if next == 'create': # 確認した内容をデータベースに登録

      entity = form.save(commit=False)
      entity.type1 = user.type1  # CustomUserとLegalEntityでいずれもtype1（発注者 or 受注者）、type2（個人 or 法人）を管理
      entity.type2 = user.type2  # CustomUserとLegalEntityでいずれもtype1（発注者 or 受注者）、type2（個人 or 法人）を管理
      entity.email = user.email

      count = LegalEntity.objects.filter(email=user.email).count()
      if count >= 1:
        messages.add_message(request, messages.INFO, '既に同じメールアドレスでの登録があります。')

      print(f'entity.id = {entity.id}（post ==create after form.is_valid in class EntityCreateView_buyer）')
        
      # 個人（type2==1）の場合、entitynameに直接入力しない為、personnameを代入
      if user.type2 == 1: entity.entityname = entity.personname

      entity.save()

      user.personname = entity.personname
      user.entityname = entity.entityname
      user.entity = entity

      user.save()
        
      print(f'self.request.POST.get={next}')
      print(f'user.entityname={user.entityname}')
      print(f'request.user.get_username={request.user.get_username} type2={user.type2}（def post ==confirm after form.is_valid in class EntityCreateView_buyer）')

      return render(self.request, 'accounts/agreement_confirm_buyer.html', {'user':user, 'entity':entity})
      # return HttpResponseRedirect(reverse('accounts:login_buyer'))
        
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
class EntityCreateView_buyer(generic.CreateView):

  model = LegalEntity
  form_class = EntityCreateForm_buyer
  template_name = 'accounts/entity_create_buyer.html'

  timeout_seconds = getattr(settings,  'ACTIVATION_TIMEOUT_SECONDS', 60*60*24)


  """（ビューにおいて）GETリクエストを受け取ったときに呼び出される（実践Django P121）"""
  """ 処理：ゲストに送られたメールのURLをクリックされた時点で呼ばれる """

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
    
    # メールを受領し、リンクからアクセスできたタイミングでアクティブ化
    if not user.is_active:
      user.is_active = True
      user.save()

    ### ここからしたが工事中（25/06/08） ###
    ### buyerEntityname_dictのデータをselectに格納するようにする 

    buyerEntityname_dict = dict((str(idx), f) for idx, f in enumerate(LegalEntity.objects.filter(type1=1).values_list('entityname', flat=True), 1))
    print(f'buyerEntityname_dict={buyerEntityname_dict} def get in EntitySetView_buyer')

    init_dict = {
      'personname': "",
      'email': user.email,
      'tel': "",
    }

    context = {
      'flag_step': 1,
      'form': EntitySetForm_buyer(initial=init_dict),
      'temporal_buyerEntityname': "",
      # コメント(25/06/08)：Selectボックスで未選択であることを示す。選択後はページ移動でデータ保持するために使う
      'buyerEntityname_dict': buyerEntityname_dict,
    }

    print(f'ここ来てる1 request.user={request.user} email={user.email} type2={user.type2}（get in class EntitySetView_buyer）')
        
    return TemplateResponse(request, 'accounts/entity_set_buyer.html', context)


  def post(self, request, *args, **kwargs):

    user = usermodel.objects.get(email=self.request.user) 
    next = self.request.POST.get('next', '')

    if next == 'ToEntityCreate': # 新規のパートナー登録へ

      # ★★★ Entityでは郵便番号、住所、代表者を登録するようにする 25/06/08 23:46

      context = {
        'user': user,
        'form': EntityCreateForm_buyer,
        }
      return render(self.request, 'accounts/entity_create_buyer.html', context)


    if next == 'ToConfirm1':  # 登録済みパートナーにユーザー追加

      form = EntitySetForm_buyer(request.POST)

      temporal_buyerEntityname = self.request.POST.get('buyerSelect', "")
      entity = LegalEntity.objects.get(entityname=temporal_buyerEntityname)
 
      print(f'temporal_buyerEntityname={temporal_buyerEntityname} form.personname={form.personname} (def post of EntityCreateView_buyer)')

      context = {
        'flag_step': 2,
        'form': form,     # personname, email, telの値が入っている
        'entity': entity,
        'temporal_buyerEntityname': temporal_buyerEntityname,
      }
      return render(self.request, 'accounts/entity_create_buyer.html', context)


    if next == 'save1':

      form = EntitySetForm_buyer(request.POST)
      temporal_buyerEntityname = self.request.POST.get('temporal_buyerEntityname', "")

      user.personname = form.personname
      user.save()

      UserEntityRelation = form.save(commit=False)
      UserEntityRelation.user = user
      UserEntityRelation.entity = entity
      UserEntityRelation.entityname = temporal_buyerEntityname
      UserEntityRelation.save()

      # 確認が終わった後にフラグを変える（場所を移す）
      if not user.is_active2:
        user.is_active2 = True
        user.save()

      return render(self.request, 'accounts/mypage_buyer.html')


    # データ確認画面から入力画面に戻る時の処理 2025/02/14
    if next == 'BackToInput':

      buyerEntityname_dict = dict((str(idx), f) for idx, f in enumerate(LegalEntity.objects.filter(type1=1).values_list('entityname', flat=True), 1))
      print(f'buyerEntityname_dict={buyerEntityname_dict} def get in EntitySetView_buyer')

      context = {
        'flag_step': 1,
        'form': self.form_class(request.POST),
        'temporal_buyerEntityname': self.request.POST['temporal_buerEntityname'],
        # コメント(25/06/08)：Selectボックスで未選択であることを示す。選択後はページ移動でデータ保持するために使う
        'buyerEntityname_dict': buyerEntityname_dict,
      }
      return TemplateResponse(request, 'accounts/entity_set_buyer.html', context)


    if next == 'ToConfirm2':  
    
      if form.is_valid():
      # 「.is_valid()」の後、フォームでのclean、clean_<field>が実行され、
      # form.cleaned_data[]にデータが入る

        context = {
          'form': form,
          'user': user,
        }
        return render(self.request, 'accounts/entity_confirm_buyer.html', context)

      else: #バリデーションエラーの時に通る
        print(f'ここ来てる3（def post after if not form.is_valid in class EntityCreateView_buyer）')
        return TemplateResponse(self.request, 'accounts/entity_create_buyer.html', {'form':form, 'user_id':user.id, 'user':user},)
    
    else: # next != "ToConfirm"の場合（confirm画面からの処理を想定）

      form = self.form_class(request.POST)

      if next == 'back':
        print(f'ここ来てる4（def post after 「try-except:」 in class EntityCreateView_buyer）')
        return render(self.request, 'accounts/entity_create_buyer.html', {'form':form, 'user':user})
        
      if next == 'save': # 確認した内容をデータベースに登録

        entity = form.save(commit=False)
        entity.type1 = user.type1  # CustomUserとLegalEntityでいずれもtype1（発注者 or 受注者）、type2（個人 or 法人）を管理
        entity.type2 = user.type2  # CustomUserとLegalEntityでいずれもtype1（発注者 or 受注者）、type2（個人 or 法人）を管理
        entity.email = user.email

        count = LegalEntity.objects.filter(email=user.email).count()
        if count >= 1:
          messages.add_message(request, messages.INFO, '既に同じメールアドレスでの登録があります。')

        print(f'entity.id = {entity.id}（post ==create after form.is_valid in class EntityCreateView_buyer）')
        
        # 個人（type2==1）の場合、entitynameに直接入力しない為、personnameを代入
        if user.type2 == 1: entity.entityname = entity.personname

        entity.save()

        user.personname = entity.personname
        user.entityname = entity.entityname
        user.entity = entity

        user.save()

        
        print(f'self.request.POST.get={next}')
        print(f'user.entityname={user.entityname}')
        print(f'request.user.get_username={request.user.get_username} type2={user.type2}（def post ==confirm after form.is_valid in class EntityCreateView_buyer）')

        return render(self.request, 'accounts/agreement_confirm_buyer.html', {'user':user, 'entity':entity})
        # return HttpResponseRedirect(reverse('accounts:login_buyer'))
        
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
  template_name = 'accounts/entity_create_seller.html'

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
            
    if not user.is_active:
      user.is_active = True
      user.save()

    context = {
      'user': user,
      'form': self.form_class,
    }

    print(f'ここ来てる1 email={user.email} type2={user.type2}（get in class EntityCreateView_seller）')
    print(f'ここ来てる1 request.user={request.user} type2={user.type2}（get in class EntityCreateView_seller）')
        
    return TemplateResponse(request, 'accounts/entity_create_seller.html', context)  #ここでgetとするのは、おそらく親クラスでtemplate_nameを表示するように規定されている

  
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
        return render(self.request, 'accounts/entity_confirm_seller.html', {'form':form, 'user':user})

      else:
        return TemplateResponse(self.request, 'accounts/entity_create_seller.html', {'form':form, 'user_id':user.id, 'user':user},)
        #contextを見直しが必要（基本的にはあまり通らないところだが）
    
    else:

      user = usermodel.objects.get(pk=self.kwargs['user_id'])
      form = self.form_class(request.POST)

      if next == 'back':
        print(f'ここまで来てる4（def post after 「try-except:」 in class EntityCreateView_seller）')
        return render(self.request, 'accounts/entity_create_seller.html', {'form':form, 'user':user})
        
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
            
    if not user.is_active:
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
            
    if not user.is_active:
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

    queryset = QpayTx.objects.filter(
      buyerEntity=entity,
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

    print(f'self.object.entityname={self.object.entityname} def get in MyPageView_seller')
  
    entity = LegalEntity.objects.get(email=self.request.user, entityname=self.object.entityname)
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
  

# ゲストがメールにあるリンクから口座登録する場合に利用するビュー
class BankAccountCreateView_before(generic.TemplateView):

  timeout_seconds = getattr(settings,  'ACTIVATION_TIMEOUT_SECONDS', 60*60*24)

  def get(self, request, *args, **kwargs):
      
    token = self.kwargs.get('token')  #kwargsはdict型
    print(f'token={token} def get in class BankAccountCreateView_before')
    
    try:
      tx_id = loads(token, max_age=self.timeout_seconds)
      tx = QpayTx.objects.get(pk=tx_id)
      ### ここは修正を要する
      le = LegalEntity.objects.get(email=tx.sellerUser_email)
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
  template_name='accounts/bankaccount_create1.html'

  def get(self, request, *args, **kwargs):

    entity_id = self.kwargs.get('entity_id')
    print(f'pass0 entity_id={entity_id} BankAccountCreateV, get')

    init_dict = {
        'temporal_tx_id': 0, # 初期値として入力
        'entity_id': entity_id,
    }

    tx_id = self.kwargs.get('tx_id')  
    if tx_id != None:
      print(f'pass1 tx_id={tx_id}')
      init_dict.update(temporal_tx_id=tx_id)

    else: # マイページ経由の口座設定（取引と紐づかない）
      print(f'pass2 取引と紐づきなしの口座設定')


    print(f'entity_id={entity_id}')

    le = LegalEntity.objects.get(pk=entity_id)
    if le.bank_account_flag == 0: # 受取口座が未設定の場合
      form = self.form_class(initial=init_dict)
      context = { "form" : form, }
      return render(request, 'accounts/bankaccount_create2.html', context)   
    else:
      # 受取口座が設定済み場合（le.bank_account_flag == 1）
      # 既に口座設定がなされている場合は、表示できるように初期値に入力

      try:

        ba = self.model.objects.get(entity_id=entity_id)
        print(f'ba.bank_name={ba.bank_name}')
        print(f'ba.branch_name={ba.branch_name}')
        init_dict.update(bank_code=ba.bank_code)
        init_dict.update(bank_name=ba.bank_name)
        init_dict.update(branch_code=ba.branch_code)
        init_dict.update(branch_name=ba.branch_name)
        init_dict.update(holdername=ba.holdername)
        init_dict.update(accountNumber=ba.accountNumber)

      except:
        print('pass4 既存の口座設定なし（想定外）')
        messages.add_message(request, messages.INFO, "口座設定済みフラグありで口座情報取得できない") 

      form = self.form_class(initial=init_dict)
      context = { "form" : form, }

      return render(request, 'accounts/bankaccount_create1.html', context)
      

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
        return render(request, "accounts/bankaccount_create2.html", context)


    # 検索ボタン（金融機関 or 支店）を押したときの処理。条件にマッチするデータ（辞書型）を返す
    search = self.request.POST.get('search', '')
    if search:
      print(f'pass2 BankAccountCreateV, post, if search:')

      if search == 'search_bank':
      
        keyword_bank = self.request.POST['keyword_bank']
        print(f'ここ来る３ keyword_bank={keyword_bank}')
        match_bank_dict = BankAccount.BankSearch(keyword_bank)

        bank_branches_dict = {}

        for bank_code in Bank.all:
          # この下の部分が機能していないと判明
          branches_dict = {} 

          for branch_code in Bank[bank_code].branches:
            branches_dict.update({branch_code : Bank[bank_code].branches[branch_code].name})

          bank_branches_dict.update({bank_code : branches_dict})
          if bank_code  == '0001': print(bank_branches_dict)

        context = {
          "form" : form,
          "match_bank_dict": match_bank_dict,
          "bank_branches_dict": json.dumps(bank_branches_dict),
        }

        return render(request, "accounts/bankaccount_create2.html", context)


      if search == 'search_branch':
      
        keyword_bank = self.request.POST['keyword_bank']
        match_bank_dict = BankAccount.BankSearch(keyword_bank)

        bank_code = self.request.POST['select_bank']
        keyword_branch = self.request.POST['keyword_branch']
        print(f'ここ来る４ self.request.POST[select_bank]={bank_code} keyword_branch={keyword_branch}')
        match_branch_dict = BankAccount.BranchSearch(bank_code, keyword_branch)

        context = {
          "form" : form,
          "match_bank_dict": match_bank_dict,
          "match_branch_dict": match_branch_dict,
          "bank_code": bank_code,
        }

        return  TemplateResponse(request, "accounts/bankaccount_create2.html", context)


    next = self.request.POST.get('next', '')   # POST.getはミドルウェア機能 
    print(f'next={next}')
    if next:

      if next == 'ToInput': # 口座名義・番号を入力する処理

        print(f'ここ通る？ if next==ToInput after def post form.is_valid in BankAccountcreateView')

        temporal_tx_id = self.request.POST['temporal_tx_id']
        # 取引承認が下りてから口座設定する場合（取引番号をキープ）
   
        entity_id = self.request.POST['entity_id']   
        bank_code = self.request.POST['select_bank']
        branch_code = self.request.POST['select_branch']

        bank_name = BankAccount.BankCodeSearch(bank_code)
        branch_name = BankAccount.BranchCodeSearch(bank_code, branch_code)

        print(f'temporal_tx_id={temporal_tx_id} BankAccountCreateV, post, next==ToInput')
        print(f'entity_id={entity_id} BankAccountCreateV, post, next==ToInput')
        print(f'bank_code={bank_code} BankAccountCreateV, post, next==ToInput')
        print(f'branch_code={branch_code} BankAccountCreateV, post, next==ToInput')
        print(f'bank_name={bank_name} BankAccountCreateV, post, next==ToInput')
        print(f'branch_name={branch_name} BankAccountCreateV, post, next==ToInput')

        init_dict = {
          'temporal_tx_id': temporal_tx_id,
          'entity_id': entity_id,
          'bank_code': bank_code,
          'branch_code': branch_code,
          'bank_name': bank_name,
          'branch_name': branch_name,
        }

        form = self.form_class(initial=init_dict)

        return render(request, "accounts/bankaccount_create3.html", { "form": form })


      if next == 'ToDone':

        if form.is_valid():
          return render(request, "accounts/bankaccount_create_done.html", { "form": form, "entity_id": self.request.POST['entity_id']})
        else:
          entity_id =self.request.POST['entity_id']
          return render(request, "accounts/bankaccount_create3.html", { "form": form, "entity_id": self.request.POST['entity_id']})


      if next == 'register': # 口座名義・番号を登録する処理

        if form.is_valid():

          ba_tmp = BankAccount()
          ba_tmp = form.save(commit=False)
          ba_tmp.temporal_tx_id = 0

          try:

            # 既存口座データがある場合の処理
            ba = self.model.objects.get(entity_id=ba_tmp.entity_id)
            ba.entity_id = ba_tmp.entity_id
            ba.bank_code = ba_tmp.bank_code
            ba.bank_name = ba_tmp.bank_name
            ba.branch_code = ba_tmp.branch_code
            ba.branch_name = ba_tmp.branch_name
            ba.holdername = ba_tmp.holdername
            ba.accountNumber = ba_tmp.accountNumber
            ba.temporal_tx_id = 0

            ba.save()

            le = LegalEntity.objects.get(pk=ba.entity_id)
            le.bank_account_flag = 1
            le.bank_account = ba
            le.save()

            print(f'ba.entity_id={ba.entity_id} BankAccountCreateV, post, next==register')
            print(f'ba.bank_code={ba.bank_code} BankAccountCreateV, post, next==register')

          except:

            # 既存口座データがない場合の処理
            # ＝（ba = self.model.objects.get(entity_id=ba_tmp.entity_id)がデータ取得できない場合）
            ba_tmp.save()
            le = LegalEntity.objects.get(pk=ba_tmp.entity_id)
            le.bank_account_flag = 1
            le.bank_account = ba_tmp
            le.save()

            messages.add_message(request, messages.INFO, "受け取り口座は設定されました。") 

            print(f'ba.entity_id={ba.entity_id} BankAccountCreateV, post, next==register')
            print(f'ba.bank_code={ba.bank_code} BankAccountCreateV, post, next==register')

          return TemplateResponse(reverse_lazy('mypage_seller'))

        else:
          messages.add_message(request, messages.INFO, "口座情報の入力にエラーがあります。") 
          return render(self.request, 'accounts/bankaccount_create1.html', {'form':form})


      if next == 'back':
        print(f'ここまで来てる（def post if next==back after form.is_valid in class BankAccountCreateView）')
        return render(self.request, 'accounts/bankaccount_create3.html', {'form':form})
  
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
    
    match_bank_dict = {}
    
    for code in Bank.all:
      #bank = Bank[code]
      bank = Bank[code]

      if re.match(keyword, code) or \
        bank.name.find(keyword) >= 0 or \
        bank.kana.find(keyword) >= 0 or \
        bank.hira.find(keyword) >= 0 or \
        bank.roma.find(keyword) >= 0: 

        match_bank_dict.update({ code: bank.name })

        # reはimportしている機能（自作インスタンスではない）

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
    # ここは通らないと思う。BankAccountViewのGETに行くのでは
    print(f'ここに来てる1（def post in class InfoEditView_seller）')
    self.object = LegalEntity.objects.get(pk=self.kwargs['entity_id'])
  
    next = self.request.POST.get('next', '')
    if next == 'edit_bankaccount':
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
    return reverse('accounts:bankaccount_create', kwargs={'entity_id': self.object.id})
