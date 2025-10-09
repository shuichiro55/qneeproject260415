from django import forms
from django.db import models
from django.contrib.auth.forms import \
  AuthenticationForm, UserCreationForm, PasswordChangeForm
from .models import CustomUser, LegalEntity, BankAccount 
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

#from .models import LegalEntity, UserEntityRelation

import unicodedata, re
from django.core.validators import RegexValidator
from django.contrib.auth.validators import UnicodeUsernameValidator

UserModel = get_user_model()

name_validator = UnicodeUsernameValidator()
tel_regex = RegexValidator(regex=r'^[0-9０-９ー―－‐₋⁻-]+$', message = ("ハイフン「-」なしで数字のみご入力下さい（最大15桁）　例：09012345678."))
zip_regex = RegexValidator(regex=r'^[0-9０-９]{7}+$', message = ("7桁の数字のみご入力ください　例: '1234567'"))

tran_zen_han = str.maketrans('―－‐ー₋—⁻０１２３４５６７８９', '-------0123456789')

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
    fields = ('email', 'type2',)

  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    for field in self.fields.values():
      field.widget.attrs['class'] = 'form-control'
      field.widget.attrs['placeholder'] = field.label
    
  def clean_email(self):
    email = self.cleaned_data['email']
    UserModel.objects.filter(email=email, is_active=False).delete()
    # ★★★ 25/01/01、25/04/11
    # おそらく仮登録だけされて、ゴースト化したインスタンスを消すためのもの
    # 問題なさそうだが、本当に問題ないか確認が必要ではないか
    return email


class MyPageForm_admin(forms.ModelForm):
  class Meta:
    model = CustomUser
    fields = ('userName', )

class MyPageForm_buyer(forms.ModelForm):
  class Meta:
    model = CustomUser
    fields = ('userName', )

class MyPageForm_seller(forms.ModelForm):
  class Meta:
    model = CustomUser
    fields = ('userName', )

#ログインフォーム
#class MyLoginForm(AuthenticationForm):
#
#  class Meta:
#    model = UserModel
#    fields = ('email', 'password')
#
#  def __init__(self, *args, **kwargs):
#    super().__init__(*args, **kwargs)
#    for field in self.fields.values():
#      field.widget.attrs['class'] = 'form-control'
#      field.widget.attrs['placeholder'] = field.label


"""パスワード変更フォーム"""
class MyPasswordChangeForm(PasswordChangeForm):

  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    for field in self.fields.values():
      field.widget.attrs['class'] = 'form-control'


class EntitySetForm_buyer(forms.Form):

  """ ユーザー（担当者）情報 """
  entityName = forms.CharField(label='取引主体名', max_length=100)
  userName = forms.CharField(label='あなたのお名前', max_length=100)
  tel_user = forms.CharField(label='電話番号（直通）', max_length=30)
  department = forms.CharField(label='所属部署', max_length=100)
  title = forms.CharField(label='役職', max_length=100)

  #class Meta:
  #  model = UserEntityRelation
  #  fields = ('userName', 'tel_user', )
  #  labels = {
  #    'userName': 'お名前（個人名）',
  #    'tel_direct': '電話番号（直通）',
  #  }

  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)

    for field in self.fields.values():
      field.widget.attrs['class'] = 'form-control'

    self.fields['userName'].widget.attrs['placeholder'] = '記入例：山田 太郎'
    self.fields['tel_user'].widget.attrs['placeholder'] = '数字のみご記載ください'

  def clean_entityName(self):
    entityName = self.cleaned_data.get('entityName', None)
    print(f'self.cleaned_data[entityName]={entityName} (in EntitySetForm_buyer)')
    if entityName is None:
      raise forms.ValidationError('データが選択されていません。')
    if entityName is not None :
      if LegalEntity.objects.filter(entityName=entityName).exists() == False:
        raise forms.ValidationError('登録された以外のデータが選択されています。')
      return unicodedata.normalize('NFKC', entityName)

    return entityName
    
  def clean_userName(self):
    userName =self.cleaned_data.get('userName', None)
    print(f'self.cleaned_data[userName]={userName} (in EntitySetForm_buyer)')
    return unicodedata.normalize('NFKC', self.cleaned_data['userName'])

  def clean_tel_user(self):
    tel1 = self.cleaned_data['tel_user'].translate(tran_zen_han)
    tel2 = unicodedata.normalize('NFKC', ''.join(re.findall('[0-9０-９]+', tel1)))
    print(f'tel2:{tel2}（clean_tel_user. in class EntitySetForm_buyer）')
    return tel2

  def clean_department(self):
    department =self.cleaned_data.get('department', None)
    print(f'self.cleaned_data[department]={department} (in EntitySetForm_buyer)')
    return unicodedata.normalize('NFKC', self.cleaned_data['department'])

  def clean_title(self):
    title =self.cleaned_data.get('title', None)
    print(f'self.cleaned_data[title]={title} (in EntitySetForm_buyer)')
    return unicodedata.normalize('NFKC', self.cleaned_data['title'])


class EntityCreateForm_buyer(forms.Form):

  """ パートナー情報 """
  entityName = forms.CharField(label='取引主体名', max_length=100)
  entityName_selected = forms.CharField(label='取引主体名', max_length=100)

  representitive = forms.CharField(label='代表者名', max_length=100)
  zip_entity = forms.CharField(label='郵便番号', max_length=15)
  # ★★ 240801 現状では郵便番号どまりだが、住所を入力するようにする
  tel_entity = forms.CharField(label='電話番号（代表）', max_length=30)


  """ ユーザー情報（個人のとき） """
  lastName = forms.CharField(label='お名前（個人）', max_length=50)
  firstName = forms.CharField(label='お名前（個人）', max_length=50)
  lastName_kana = forms.CharField(label='お名前（個人）', max_length=50)
  firstName_kana = forms.CharField(label='お名前（個人）', max_length=50)
  tel_user = forms.CharField(label='電話番号（直通）', max_length=30)
  department = forms.CharField(label='部署名', max_length=100)
  title = forms.CharField(label='役職名', max_length=100)

  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
      
    for field in self.fields.values():
      field.widget.attrs['class'] = 'form-control'

    # 注釈が必要な項目だけ
    self.fields['userName'].widget.attrs['placeholder'] = '記入例：窮仁 太郎'
    self.fields['tel_entity'].widget.attrs['placeholder'] = '数字のみご記載ください。'
    self.fields['zip_entity'].widget.attrs['placeholder'] = '数字のみご記載ください。'
    self.fields['tel_user'].widget.attrs['placeholder'] = '数字のみご記載ください。'
    self.fields['zip_user'].widget.attrs['placeholder'] = '数字のみご記載ください。'
  
        
  def clean_entityName(self):
    entityName = self.cleaned_data.get('entityName')
    print(f'self.cleaned_data[entityName]={entityName} (in EntityCreateForm_buyer)')
    if entityName is not None :
      return unicodedata.normalize('NFKC', entityName)   
    return entityName

  def clean_tel_entity(self):
    tel1 = self.cleaned_data['tel_entity'].translate(tran_zen_han)
    tel2 = unicodedata.normalize('NFKC', ''.join(re.findall('[0-9０-９]+', tel1)))
    print(f'tel2:{tel2}（clean_tel_entity. in class EntityCreateform_buyer）')
    return tel2
    
  def clean_zip_entity(self):
    zip1 = self.cleaned_data['zip_entity'].translate(tran_zen_han)
    zip2 = unicodedata.normalize('NFKC', ''.join(re.findall('[0-9０-９]+', zip1)))
    return zip2

  def clean_userName(self):
    return unicodedata.normalize('NFKC', self.cleaned_data['userName'])

  def clean_tel_user(self):
    tel1 = self.cleaned_data['tel_user'].translate(tran_zen_han)
    tel2 = unicodedata.normalize('NFKC', ''.join(re.findall('[0-9０-９]+', tel1)))
    print(f'tel2:{tel2}（clean_tel_user. in class EntityCreateform_buyer）')
    return tel2

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


## Metaを使う時には、forms.ModelFormを継承するべき 25/06/02
class AgreementConfirmForm_buyer(forms.Form):

  class Meta:
    model = LegalEntity
    fields = ('membershipConsent_boolean')


# 25/08/24 設定したモデルは6/17 
class UserAddForm_buyer(forms.Form):

  canApprove_all = forms.BooleanField(label='承認権限（全部）')
  canApprove_add = forms.BooleanField(label='承認権限（参加）')
  canApprove_qpay = forms.BooleanField(label='承認権限（Qpay）')

  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    #for field in self.fields.values():
    #  field.widget.attrs['class'] = 'form-check form-switch'

# 25/08/30追加 
class PermissionUpdateForm_buyer(forms.Form):
 
  canApprove_all = forms.BooleanField(label='承認権限（全部）')
  canApprove_add = forms.BooleanField(label='承認権限（参加）')
  canApprove_qpay = forms.BooleanField(label='承認権限（Qpay）')

  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    #for field in self.fields.values():
    #  field.widget.attrs['class'] = 'form-check form-switch'

# ★★ 250929 エンティティを選択するケースがカバーされていない
class EntitySetForm_seller(forms.Form):

  entityName = forms.CharField(label='取引主体名', max_length=100)
  userName = forms.CharField(label='あなたのお名前', max_length=100)
  tel_user = forms.CharField(label='電話番号（直通）', max_length=30)
  department = forms.CharField(label='所属部署', max_length=100)
  title = forms.CharField(label='役職', max_length=100)
  

  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)

    for field in self.fields.values():
      field.widget.attrs['class'] = 'form-control'

    self.fields['userName'].widget.attrs['placeholder'] = '例：山田 太郎'
    self.fields['tel_user'].widget.attrs['placeholder'] = '数字のみご記載ください'

  def clean_entityName(self):
    entityName = self.cleaned_data.get('entityName', None)
    print(f'self.cleaned_data[entityName]={entityName} (in EntitySetForm_seller)')
    if entityName is None:
      raise forms.ValidationError('データが選択されていません。')
    if entityName is not None :
      if LegalEntity.objects.filter(entityName=entityName).exists() == False:
        raise forms.ValidationError('登録された以外のデータが選択されています。')
      return unicodedata.normalize('NFKC', entityName)

  def clean_userName(self):
    return unicodedata.normalize('NFKC', self.cleaned_data['userName'])

  def clean_tel_user(self):
    tel1 = self.cleaned_data['tel_user'].translate(tran_zen_han)
    tel2 = unicodedata.normalize('NFKC', ''.join(re.findall('[0-9０-９]+', tel1)))
    print(f'tel2:{tel2}（clean_tel_user. in class EntitySetForm_seller）')
    return tel2


class EntityCreateForm_seller(forms.Form):

  # ★★ 250927 個人（type2=1）に対するの対応を追加

  """ 個人・法人の共通項目 """
  lastName = forms.CharField(label='姓（last name）', max_length=50)
  firstName = forms.CharField(label='名（first name）', max_length=50)
  lastName_kana = forms.CharField(label='姓（フリガナ）', max_length=50)
  firstName_kana = forms.CharField(label='名（フリガナ）', max_length=50)

  tel_user = forms.CharField(label='電話番号（直通）', max_length=30)

  """ 個人のときだけ（type2=1）の項目 """
  # ★★ 250927 住所を入力するようにする
  zip_user = forms.CharField(label='郵便番号', max_length=15, required=False)

  """ 法人だけの項目 """
  entityName = forms.CharField(label='取引主体名', max_length=100, required=False)  # 個人の場合はuserNameと同じ情報となる
  representitive = forms.CharField(label='代表者名', max_length=100, required=False)
  zip_entity = forms.CharField(label='郵便番号', max_length=15, required=False)

  # ★★ 260927 住所を入力するようにする
  tel_entity = forms.CharField(label='電話番号（代表）', max_length=30, required=False)

  """ 法人だけにある担当者情報 """
  department = forms.CharField(label='部署名', max_length=100, required=False)
  title = forms.CharField(label='役職名', max_length=100, required=False)


  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
      
    for field in self.fields.values():
      field.widget.attrs['class'] = 'form-control'

    self.fields['lastName'].widget.attrs['placeholder'] = '例：山田'
    self.fields['firstName'].widget.attrs['placeholder'] = '例：太郎'
    self.fields['lastName_kana'].widget.attrs['placeholder'] = '例：ヤマダ'
    self.fields['firstName_kana'].widget.attrs['placeholder'] = '例：タロウ'
    self.fields['tel_entity'].widget.attrs['placeholder'] = '数字のみ、ご記載ください'
    self.fields['zip_entity'].widget.attrs['placeholder'] = '数字のみ、ご記載ください'
    self.fields['tel_user'].widget.attrs['placeholder'] = '数字のみ、ご記載ください'


  def clean_lastName(self):
    lastName = re.sub("[\u3000 \t]", "", self.cleaned_data['lastName'])
    return unicodedata.normalize('NFKC', lastName)
    # unicodedaata.normalize('NFKC',)で「unicodeの正規化」
    # カタカナは半角を全角に、数字は全角を半角にする

  def clean_lastName_kana(self):
    lastName_kana = re.sub("[\u3000 \t]", "", self.cleaned_data['lastName_kana']) # スペースとタブを削除
    lastName_kana = unicodedata.normalize('NFKC', lastName_kana)
    print(f'lastName_kana={lastName_kana} in def clean_lastName_kana in EntityCreateForm_seller')
    if bool(re.search(r'[ァ-ヶ]', lastName_kana)) == False:
      raise forms.ValidationError('カナ以外の文字が入力されています')
    return lastName_kana
  
    
  def clean_firstName(self):
    firstName = re.sub("[\u3000 \t]", "", self.cleaned_data['firstName'])
    return unicodedata.normalize('NFKC', firstName)
    # unicodedaata.normalize('NFKC',)で「unicodeの正規化」
    # カタカナは半角を全角に、数字は全角を半角にする

  def clean_firstName_kana(self):
    firstName_kana = re.sub("[\u3000 \t]", "", self.cleaned_data['firstName_kana'])
    firstName_kana = unicodedata.normalize('NFKC', firstName_kana)
    if bool(re.search(r'[ァ-ヶ]', firstName_kana)) == False:
      raise forms.ValidationError('カナ以外の文字が入力されています')
    return firstName_kana

  def clean_tel_user(self):
    tel_user = self.cleaned_data['tel_user'].translate(tran_zen_han)
    tel_user = unicodedata.normalize('NFKC', ''.join(re.findall(r'\d+', tel_user)))
    print(f'tel_user:{tel_user}（clean_tel_user. in class EntityCreateform_seller）')
    return tel_user

  def clean_zip_user(self):
    zip_user = self.cleaned_data['zip_user'].translate(tran_zen_han)
    zip_user = unicodedata.normalize('NFKC', ''.join(re.findall(r'\d+', zip_user)))
    print(f'self.cleaned_data[zip_user]={zip_user} (clean_zip_user in EntityCreateForm_seller)')
    return zip_user

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


  def clean_entityName(self):
    entityName = self.cleaned_data.get('entityName')
    print(f'self.cleaned_data[entityName]={entityName} (in EntityCreateForm_seller)')
    if entityName is None :
      raise forms.ValidationError('この項目は必須となります。ご入力お願いたします。')
    return entityName

  def clean_tel_entity(self):
    tel1 = self.cleaned_data['tel_entity'].translate(tran_zen_han)
    tel2 = unicodedata.normalize('NFKC', ''.join(re.findall('[0-9０-９]+', tel1)))
    print(f'tel2:{tel2}（clean_tel_entity. in class EntityCreateform_seller）')
    return tel2
    
  def clean_zip_entity(self):
    zip1 = self.cleaned_data['zip_entity'].translate(tran_zen_han)
    zip2 = unicodedata.normalize('NFKC', ''.join(re.findall('[0-9０-９]+', zip1)))
    return zip2


class AgreementConfirmForm_seller(forms.Form):

  class Meta:
    model = LegalEntity
    fields = ('membershipConsent_boolean')


class UserAddForm_seller(forms.Form):

  #applyUser_id = forms.IntegerField(label='申請者ユーザーID')
  canApprove_all = forms.BooleanField(label='承認権限（全部）')
  canApprove_add = forms.BooleanField(label='承認権限（参加）')
  canApprove_qpay = forms.BooleanField(label='承認権限（Qpay）')

  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    #for field in self.fields.values():
    #  field.widget.attrs['class'] = 'form-check form-switch'


# 25/08/30追加 
class PermissionUpdateForm_seller(forms.Form):

  canApprove_all = forms.BooleanField(label='承認権限（全部）')
  canApprove_add = forms.BooleanField(label='承認権限（参加）')
  canApprove_qpay = forms.BooleanField(label='承認権限（Qpay）')

  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    #for field in self.fields.values():
    #  field.widget.attrs['class'] = 'form-check form-switch'

# 24/06/30作成
class ContactForm(forms.Form):

  userName = forms.CharField(label='お名前')
  email = forms.EmailField(label='メールアドレス')
  title = forms.CharField(label='件名')
  message = forms.CharField(label='メッセージ', widget=forms.Textarea)

  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    #self.fields['userName'].widget.attrs['placeholder'] = 'お名前をご入力してください。'
    self.fields['userName'].widget.attrs['class'] = 'form-control'

    #self.fields['email'].widget.attrs['placeholder'] = 'メールアドレスをご入力してください。'
    self.fields['email'].widget.attrs['class'] = 'form-control'

    #self.fields['title'].widget.attrs['placeholder'] = 'タイトルをご入力してください。'
    self.fields['title'].widget.attrs['class'] = 'form-control'

    #self.fields['message'].widget.attrs['placeholder'] = 'メッセージををご入力してください。'
    self.fields['message'].widget.attrs['class'] = 'form-control'

class BankSelectForm(forms.ModelForm):

  class Meta:
    model = BankAccount
    fields = (
      'bankCode',
      'branchCode',
    ) 

  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)

    for field in self.fields.values():
      field.widget.attrs['class'] = 'form-control'

  def clean_bankCode(self):
    bankCode = self.cleaned_data.get('bankCode')
    bankCode = unicodedata.normalize('NFKC', bankCode)
    print(f'pass1 self.cleaned_data[bankCode]={bankCode} (in BankSelectForm)')
    if re.match(r"^\d{4}$", bankCode) is None:
      print(f'pass2 self.cleaned_data[bankCode]={bankCode} (bankCode is None or blank in BankSelectForm)')
      raise forms.ValidationError('銀行が選択されていません') 
    return bankCode
  
  def clean_branchCode(self):
    branchCode = self.cleaned_data.get('branchCode')
    branchCode = unicodedata.normalize('NFKC', branchCode)
    print(f'pass1 self.cleaned_data[branchCode]={branchCode} (in BankSelectForm)')
    if re.match(r"^\d{3}$", branchCode) is None:
      print(f'pass2 self.cleaned_data[branchCode]={branchCode} (branchCode is None or blank inBankSelectForm)')
      raise forms.ValidationError('支店が選択されていません')
    return branchCode

# 24/07/14作成
class BankAccountForm(forms.ModelForm):

  class Meta:
    model = BankAccount
    fields = (
      'bankCode',
      'bankName',
      'branchCode',
      'branchName',
      'holderName',
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



# 25/05/17 パスワード変更用意追加
class MyPasswordChangeForm(PasswordChangeForm):
    """パスワード変更フォーム"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            print(f'field.label={field.label}')


            field.widget.attrs['class'] = 'form-control'