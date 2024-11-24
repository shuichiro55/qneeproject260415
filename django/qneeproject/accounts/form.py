from django import forms
from django.db import models
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser, BankAccount 
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

from django.contrib.auth.forms import AuthenticationForm
from .models import LegalEntity
import unicodedata, re

UserModel = get_user_model()

#ログインフォーム
class MyLoginForm(AuthenticationForm):

  class Meta:
    model = UserModel
    fields = ('email', 'password')

  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    for field in self.fields.values():
      field.widget.attrs['class'] = 'form-control'
      field.widget.attrs['placeholder'] = field.label

class UserCreateForm(UserCreationForm):

  class Meta:
    model = UserModel
    fields = ('email', 'type2')

  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    for field in self.fields.values():
      field.widget.attrs['class'] = 'form-control'
      field.widget.attrs['placeholder'] = field.label
    
  def clean_email(self):
    email = self.cleaned_data['email']
    UserModel.objects.filter(email=email, is_active=False).delete()
    return email

## 24/03/31 個人か法人かを確認し、それぞれのFormにつなげる
#class UserCreate2Form(forms.ModelForm):
#
#    def __init__(self, *args, **kwargs):
#        super().__init__(*args, **kwargs)
#        for field in self.fields.values():
#            field.widget.attrs['class'] = 'form-control'
#            field.widget.attrs['placeholder'] = field.label
#
#    def clean_type2(self):
#        return self.cleaned_date['type2']
#
#    class Meta:
#        model = UserModel
#        fields = ('type2',)


class MyPageForm_seller(forms.ModelForm):

  class Meta:
    model = LegalEntity
    fields = ('personname', 'tel', 'entityname', 'department', 'title', 'postal_code')

#class ConsentForm(forms.ModelForm):

#class EmailAuthenticationForm(forms.Form): #実践Djangoの「認証バックエンドによるログイン処理のカスタマイズ」P217
#    email = forms.EmailField(max_length=254, widget=forms.TextInput(attrs={'autofocus':True}))
#    password = forms.CharField(label=_("Password"), strip=False, widget=forms.PasswordInput)
#
#    error_messages = {
#        'invalid_login': "Eメールアドレスまたはパスワードに誤りがあります。", 'inactive':_("This account is inactive"),
#    }
#
#    def __init__(self, request=None, *args, **kwargs):
#        self.request = request
#        self.user_cashe = None
#        super().__init__(*args, **kwargs)
#        
#       #Set the label for the "email" field.
#        self.email_field = UserModel._meta.get_field("email")
#        if self.fields['email'].label is None:
#            self.fields['email'].label = capfirst(self.email_field.verbose_name) #capfirst 先頭の文字を大文字に
#    
#    def clean(self):
#        email = self.cleaned_data.get('email')
#        password = self.cleaned_data.get('password')
#
#        if email is not None and password:
#            self.user_cache = authenticate(self.request, email=email, password=password)
#            if self.user_cache is None:
#                raise forms.ValidationError(
#                    self.error_messages['invalid_login'],
#                    code = 'invalid_login',  #推奨コードにcodeの記載はあるがメリットは
#                    params = {'email': self.email_field.verbose_name})  #paramsはエラーメッセージに変数を使うときだが使われていない
#            else:
#                self.confirm_login_allowed(self.user_cache)
#        return self.cleaned_data
#
#    def confirm_login_allowed(self, user):
#        if not user.is_active:
#            raise forms.ValidationError(self.error_messages['inactive'], code='inactive')
#    
#    def get_user_id(self):
#        if self.user_cache:
#            return self.user_cache.id
#    
#    def get_user(self):
#        return self.user_cache

class MyPageForm_buyer(forms.ModelForm):

  class Meta:
    model = LegalEntity
    fields = ('personname', 'tel', 'entityname', 'department', 'title', 'postal_code')


#ログインフォーム
class MyLoginForm(AuthenticationForm):

    class Meta:
      model = UserModel
      fields = ('email', 'password')

    def __init__(self, *args, **kwargs):
      super().__init__(*args, **kwargs)
      for field in self.fields.values():
        field.widget.attrs['class'] = 'form-control'
        field.widget.attrs['placeholder'] = field.label

class UserCreateForm(UserCreationForm):

    class Meta:
      model = UserModel
      fields = ('email', 'type2')

    def __init__(self, *args, **kwargs):
      super().__init__(*args, **kwargs)
      for field in self.fields.values():
        field.widget.attrs['class'] = 'form-control'
        field.widget.attrs['placeholder'] = field.label
    
    def clean_email(self):
      email = self.cleaned_data['email']
      UserModel.objects.filter(email=email, is_active=False).delete()
      return email


tran_zen_han = str.maketrans('―－‐ー₋—⁻０１２３４５６７８９', '-------0123456789')

class EntityCreateForm(forms.ModelForm):

    class Meta:
      model = LegalEntity
      fields = ('personname', 'tel', 'entityname', 'department', 'title', 'postal_code')

    def __init__(self, *args, **kwargs):
      super().__init__(*args, **kwargs)
      for field in self.fields.values():
        field.widget.attrs['class'] = 'form-control'
        #    field.widget.attrs['placeholder'] = field.label

    def clean_personname(self):
      print(self.cleaned_data['personname'])
      personname =self.cleaned_data.get('personname')
      print(f'self.cleaned_data[personname]={personname} (in EntityCreateForm)')
      return unicodedata.normalize('NFKC', self.cleaned_data['personname'])
        
    def clean_entityname(self):
      entityname = self.cleaned_data.get('entityname')
      print(f'self.cleaned_data[entityname]={entityname} (in EntityCreateForm)')
      if entityname is not None :
        return unicodedata.normalize('NFKC', entityname)   
      return entityname

    def clean_department(self):
      department = self.cleaned_data['department']
      print(f'self.cleaned_data[department]={department} (clean_department in EntityCreateForm)')
      if department is not None:
         return unicodedata.normalize('NFKC', department)
      return department

    def clean_title(self):
      title = self.cleaned_data['title']
      if title is not None:
        return unicodedata.normalize('NFKC', title)
      return title

    def clean_tel(self):
      tel1 = self.cleaned_data['tel'].translate(tran_zen_han)
      tel2 = unicodedata.normalize('NFKC', ''.join(re.findall('[0-9０-９]+', tel1)))
      print(f'tel2:{tel2}（clean_te. in class EntityCreateform）')
      return tel2
    
    def clean_postal_code(self):
      postal_code1 = self.cleaned_data['postal_code'].translate(tran_zen_han)
      postal_code2 = unicodedata.normalize('NFKC', ''.join(re.findall('[0-9０-９]+', postal_code1)))
      return postal_code2


class EntityConfirmForm(forms.Form):

    #is_consent = forms.BooleanField(label='同意する', required=True, widget=forms.CheckboxInput(attrs={'class': 'check'}),)

    class Meta:
      model = LegalEntity
      fields = ('is_consent')


class MyPageForm_seller(forms.ModelForm):

    class Meta:
      model = LegalEntity
      fields = ('personname', 'tel', 'entityname', 'department', 'title', 'postal_code')

#class ConsentForm(forms.ModelForm):

#class EmailAuthenticationForm(forms.Form): #実践Djangoの「認証バックエンドによるログイン処理のカスタマイズ」P217
#    email = forms.EmailField(max_length=254, widget=forms.TextInput(attrs={'autofocus':True}))
#    password = forms.CharField(label=_("Password"), strip=False, widget=forms.PasswordInput)
#
#    error_messages = {
#        'invalid_login': "Eメールアドレスまたはパスワードに誤りがあります。", 'inactive':_("This account is inactive"),
#    }
#
#    def __init__(self, request=None, *args, **kwargs):
#        self.request = request
#        self.user_cashe = None
#        super().__init__(*args, **kwargs)
#        
#       #Set the label for the "email" field.
#        self.email_field = UserModel._meta.get_field("email")
#        if self.fields['email'].label is None:
#            self.fields['email'].label = capfirst(self.email_field.verbose_name) #capfirst 先頭の文字を大文字に
#    
#    def clean(self):
#        email = self.cleaned_data.get('email')
#        password = self.cleaned_data.get('password')
#
#        if email is not None and password:
#            self.user_cache = authenticate(self.request, email=email, password=password)
#            if self.user_cache is None:
#                raise forms.ValidationError(
#                    self.error_messages['invalid_login'],
#                    code = 'invalid_login',  #推奨コードにcodeの記載はあるがメリットは
#                    params = {'email': self.email_field.verbose_name})  #paramsはエラーメッセージに変数を使うときだが使われていない
#            else:
#                self.confirm_login_allowed(self.user_cache)
#        return self.cleaned_data
#
#    def confirm_login_allowed(self, user):
#        if not user.is_active:
#            raise forms.ValidationError(self.error_messages['inactive'], code='inactive')
#    
#    def get_user_id(self):
#        if self.user_cache:
#            return self.user_cache.id
#    
#    def get_user(self):
#        return self.user_cache

class MyPageForm_buyer(forms.ModelForm):

  class Meta:
    model = LegalEntity
    fields = ('personname', 'tel', 'entityname', 'department', 'title', 'postal_code')

# 24/06/30作成
class ContactForm(forms.Form):

  name = forms.CharField(label='お名前')
  email = forms.EmailField(label='メールアドレス')
  title = forms.CharField(label='件名')
  message = forms.CharField(label='メッセージ', widget=forms.Textarea)

  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    #self.fields['name'].widget.attrs['placeholder'] = 'お名前をご入力してください。'
    self.fields['name'].widget.attrs['class'] = 'form-control'

    #self.fields['email'].widget.attrs['placeholder'] = 'メールアドレスをご入力してください。'
    self.fields['email'].widget.attrs['class'] = 'form-control'

    #self.fields['title'].widget.attrs['placeholder'] = 'タイトルをご入力してください。'
    self.fields['title'].widget.attrs['class'] = 'form-control'

    #self.fields['message'].widget.attrs['placeholder'] = 'メッセージををご入力してください。'
    self.fields['message'].widget.attrs['class'] = 'form-control'

# 24/07/14作成
class BankAccountForm(forms.ModelForm):

  class Meta:
    model = BankAccount
    fields = (
      'entity_id',
      'bank_code',
      'bank_name',
      'branch_code',
      'branch_name',
      'account_number',
    #  'holdername'
    ) 
    
  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)

    for field in self.fields.values():
      field.widget.attrs['class'] = 'form-control'

class InfoEditForm_seller(forms.ModelForm):

  class Meta:
    model = LegalEntity
    fields = ('personname', 'tel', 'entityname', 'department', 'title', 'postal_code')  