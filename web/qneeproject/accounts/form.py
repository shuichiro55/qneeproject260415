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
    fields = ('email',)

  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    for field in self.fields.values():
      field.widget.attrs['class'] = 'form-control'
      field.widget.attrs['placeholder'] = field.label
    
  def clean_email(self):
    email = self.cleaned_data['email']
    UserModel.objects.filter(email=email, is_active=False).delete()
    return email


class MyPageForm_buyer(forms.ModelForm):

  class Meta:
    model = LegalEntity
    fields = ('personname', 'tel', 'entityname', 'department', 'title', 'postal_code')

class MyPageForm_seller(forms.ModelForm):

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


class UserCreateForm_buyer(UserCreationForm):

    class Meta:
      model = UserModel
      fields = ('email',)

    def __init__(self, *args, **kwargs):
      super().__init__(*args, **kwargs)
      for field in self.fields.values():
        field.widget.attrs['class'] = 'form-control'
        field.widget.attrs['placeholder'] = field.label
    
    def clean_email(self):
      email = self.cleaned_data['email']
      UserModel.objects.filter(email=email, is_active=False).delete()
      # ★★ 25/0101 これ、既に登録されているユーザーを削除してしまうではないか、、、
      return email

tran_zen_han = str.maketrans('―－‐ー₋—⁻０１２３４５６７８９', '-------0123456789')

class UserCreateForm_seller(UserCreationForm):

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
      # ★★ 25/0101 これ、既に登録されているユーザーを削除してしまうではないか、、、
      return email


class EntityCreateForm_buyer(forms.ModelForm):

    class Meta:
      model = LegalEntity
      fields = ('personname', 'tel', 'entityname', 'postal_code', 'department', 'title')
      labels = {
        "personname": "お名前（個人名）",
        "tel": "電話番号",
        "entityname": "企業名",
        "postal_code": "郵便番号",
        "department": "部署名",
        "title": "役職",
    }

    def __init__(self, *args, **kwargs):
      super().__init__(*args, **kwargs)
      
      for field in self.fields.values():
        field.widget.attrs['class'] = 'form-control'

      self.fields['personname'].widget.attrs['placeholder'] = '記入例：山田 太郎'
      self.fields['tel'].widget.attrs['placeholder'] = '数字のみ、ご記載ください'
      self.fields['postal_code'].widget.attrs['placeholder'] = '数字のみ、ご記載ください'

    def clean_personname(self):
      print(self.cleaned_data['personname'])
      personname =self.cleaned_data.get('personname')
      personname 
      print(f'self.cleaned_data[personname]={personname} (in EntityCreateForm_buyer)')

      return unicodedata.normalize('NFKC', self.cleaned_data['personname'])
        
    def clean_entityname(self):
      entityname = self.cleaned_data.get('entityname')
      print(f'self.cleaned_data[entityname]={entityname} (in EntityCreateForm_buyer)')
      if entityname is not None :
        return unicodedata.normalize('NFKC', entityname)   
      return entityname

    def clean_department(self):
      department = self.cleaned_data['department']
      print(f'self.cleaned_data[department]={department} (clean_department in EntityCreateForm_buyer)')
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
      print(f'tel2:{tel2}（clean_tel. in class EntityCreateform_buyer）')
      return tel2
    
    def clean_postal_code(self):
      postal_code1 = self.cleaned_data['postal_code'].translate(tran_zen_han)
      postal_code2 = unicodedata.normalize('NFKC', ''.join(re.findall('[0-9０-９]+', postal_code1)))
      return postal_code2

class EntityCreateForm_seller(forms.ModelForm):

  class Meta:
    model = LegalEntity
    fields = ('personname', 'tel', 'entityname',  'postal_code', 'department', 'title')
    labels = {
      "personname": "お名前（個人名）",
      "tel": "電話番号",
      "entityname": "企業名",
      "postal_code": "郵便番号",
      "department": "部署名",
      "title": "役職",
  }


  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
      
    for field in self.fields.values():
      field.widget.attrs['class'] = 'form-control'
      field.widget.attrs['placeholder'] = field.label

    self.fields['personname'].widget.attrs['placeholder'] = '記入例：山田 太郎'
    self.fields['tel'].widget.attrs['placeholder'] = '数字のみ、ご記載ください'
    self.fields['postal_code'].widget.attrs['placeholder'] = '数字のみ、ご記載ください'

  def clean_personname(self):
    print(self.cleaned_data['personname'])
    personname =self.cleaned_data.get('personname')
    print(f'self.cleaned_data[personname]={personname} (in EntityCreateForm_seller)')
    return unicodedata.normalize('NFKC', self.cleaned_data['personname'])
        
  def clean_entityname(self):
    entityname = self.cleaned_data.get('entityname')
    print(f'self.cleaned_data[entityname]={entityname} (in EntityCreateForm_seller)')
    if entityname is not None :
      return unicodedata.normalize('NFKC', entityname)   
    return entityname

  def clean_department(self):
    department = self.cleaned_data['department']
    print(f'self.cleaned_data[department]={department} (clean_department in EntityCreateForm_seller)')
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
    print(f'tel2:{tel2}（clean_te. in class EntityCreateform_seller）')
    return tel2
    
  def clean_postal_code(self):
    postal_code1 = self.cleaned_data['postal_code'].translate(tran_zen_han)
    postal_code2 = unicodedata.normalize('NFKC', ''.join(re.findall('[0-9０-９]+', postal_code1)))
    return postal_code2


class EntityConfirmForm_buyer(forms.Form):

  class Meta:
    model = LegalEntity

class EntityConfirmForm_seller(forms.Form):

  class Meta:
    model = LegalEntity


class AgreementConfirmForm_buyer(forms.Form):

  class Meta:
    model = LegalEntity
    fields = ('is_consent_membership')

class AgreementConfirmForm_seller(forms.Form):

  class Meta:
    model = LegalEntity
    fields = ('is_consent_membership')


class MyPageForm_buyer(forms.ModelForm):

  class Meta:
    model = LegalEntity
    fields = ('personname', 'tel', 'entityname', 'department', 'title', 'postal_code')

class MyPageForm_seller(forms.ModelForm):

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
      'temporal_tx_id', # 取引と紐づいて受取口座を設定する際に利用 25/02/01
      'entity_id',
      'bank_code',
      'bank_name',
      'branch_code',
      'branch_name',
      'holdername',
      'accountNumber',
    ) 

  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)

    for field in self.fields.values():
      field.widget.attrs['class'] = 'form-control'

#  def clean_holdername(self):
#    holdername = self.cleaned_data.get('holdername')
#    print(f'pass1 self.cleaned_data[accountNumber]={holdername} (blank in BankAccountForm)')
#    if holdername is None or "None" or "" :
#      print(f'pass2 self.cleaned_data[accountNumber]={holdername} (hodername is None or blank in BankAccountForm)')
#      raise forms.ValidationError('口座名義を入力してください')
#
#    return unicodedata.normalize('NFKC', holdername)

#  def clean_accountNumber(self):
#    accountNumber = self.cleaned_data.get('accountNumber')
#    print(f'pass3 self.cleaned_data[accountNumber]={accountNumber} (in BankAccountForm)')
#    if accountNumber is None or "None" or "" :
#      print(f'pass4 self.cleaned_data[accountNumber]={accountNumber} (in BankAccountForm)')
#      raise forms.ValidationError('口座番号を入力してください')
#
#    return accountNumber


class InfoEditForm_seller(forms.ModelForm):

  class Meta:
    model = LegalEntity
    fields = ('personname', 'tel', 'entityname', 'department', 'title', 'postal_code')  