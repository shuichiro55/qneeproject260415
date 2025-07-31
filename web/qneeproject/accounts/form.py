from django import forms
from django.db import models
from django.contrib.auth.forms import \
  AuthenticationForm, UserCreationForm, PasswordChangeForm
from .models import CustomUser, BankAccount 
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

from .models import LegalEntity, UserEntityRelation

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
    fields = ('personname', )

class MyPageForm_buyer(forms.ModelForm):
  class Meta:
    model = CustomUser
    fields = ('personname', )

class MyPageForm_seller(forms.ModelForm):
  class Meta:
    model = CustomUser
    fields = ('personname', )

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


"""パスワード変更フォーム"""
class MyPasswordChangeForm(PasswordChangeForm):

  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    for field in self.fields.values():
      field.widget.attrs['class'] = 'form-control'


class EntitySetForm_buyer(forms.Form):

  class Meta:
    model = UserEntityRelation
    fields = ('personname', 'tel_direct', )
    labels = {
      'personname': 'お名前（個人名）',
      'tel_direct': '電話番号（直通）',

    }

  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
      
    for field in self.fields.values():
      field.widget.attrs['class'] = 'form-control'

    #self.fields['personname'].widget.attrs['placeholder'] = '記入例：山田 太郎'
    #self.fields['tel_direct'].widget.attrs['placeholder'] = '数字のみ、ご記載ください'

  def clean_personname(self):
    personname =self.cleaned_data.get('personname')
    print(f'self.cleaned_data[personname]={personname} (in EntitySetForm_buyer)')

    return unicodedata.normalize('NFKC', self.cleaned_data['personname'])

  def clean_tel_direct(self):
    tel1 = self.cleaned_data['tel_direct'].translate(tran_zen_han)
    tel2 = unicodedata.normalize('NFKC', ''.join(re.findall('[0-9０-９]+', tel1)))
    print(f'tel2:{tel2}（clean_tel_direct. in class EntitySetForm_seller）')
    return tel2


from django.core.validators import RegexValidator
from django.contrib.auth.validators import UnicodeUsernameValidator

name_validator = UnicodeUsernameValidator()
tel_regex = RegexValidator(regex=r'^[0-9０-９ー―－‐₋⁻-]+$', message = ("ハイフン「-」なしで数字のみご入力下さい（最大15桁）　例：09012345678."))


class EntityCreateForm_buyer(forms.ModelForm):

  #企業の場合の入力値、個人の場合はpersonnameが入る
  entityname = models.CharField('取引主体名', max_length=150, unique=False, default="", null=True, blank=True, validators=[name_validator],)
  representitive = models.CharField('代表者名', max_length=150, unique=False, default="", null=True, validators=[name_validator],)
  tel_main = models.CharField(_('電話番号（代表）'), max_length=30, default="", null=False, validators=[tel_regex])

  #企業の場合、住所は全部入力する
  postal_code_regex = RegexValidator(regex=r'^[0-9]+$', message = _("Postal Code must be entered in the format: '1234567'. Up to 7 digits allowed."))
  postal_code = models.CharField(_('郵便番号'), max_length=7, default="", null=False, blank=True, validators=[postal_code_regex])

  personname = models.CharField('お名前（個人）', blank=False, max_length=150, unique=False, null=True,)
  tel_direct = models.CharField(_('電話番号（直通）'), max_length=30, default="", null=False, validators=[tel_regex])

  department = models.CharField(_('部署名'), max_length=150, default="", blank=True, null=True)   # Entityが法人の場合
  title = models.CharField(_('役職名'), max_length=150, default="", blank=True, null=True)        # Entityが法人の場合

  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
      
    for field in self.fields.values():
      field.widget.attrs['class'] = 'form-control'

    self.fields['personname'].widget.attrs['placeholder'] = '記入例：山田 太郎'
    self.fields['tel_main'].widget.attrs['placeholder'] = '数字のみ、ご記載ください'
    self.fields['postal_code'].widget.attrs['placeholder'] = '数字のみ、ご記載ください'
    self.fields['tel_direct'].widget.attrs['placeholder'] = '数字のみ、ご記載ください'

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

  def clean_tel_main(self):
    tel1 = self.cleaned_data['tel_main'].translate(tran_zen_han)
    tel2 = unicodedata.normalize('NFKC', ''.join(re.findall('[0-9０-９]+', tel1)))
    print(f'tel2:{tel2}（clean_tel_main. in class EntityCreateform_buyer）')
    return tel2
    
  def clean_postal_code(self):
    postal_code1 = self.cleaned_data['postal_code'].translate(tran_zen_han)
    postal_code2 = unicodedata.normalize('NFKC', ''.join(re.findall('[0-9０-９]+', postal_code1)))
    return postal_code2

  def clean_tel_direct(self):
    tel1 = self.cleaned_data['tel_direct'].translate(tran_zen_han)
    tel2 = unicodedata.normalize('NFKC', ''.join(re.findall('[0-9０-９]+', tel1)))
    print(f'tel2:{tel2}（clean_tel_direct. in class EntityCreateform_buyer）')
    return tel2


tran_zen_han = str.maketrans('―－‐ー₋—⁻０１２３４５６７８９', '-------0123456789')


# ★★★ 25/06/17 
class UserAddForm_buyer(UserCreationForm):

  class Meta:
    model = UserModel
    fields = ('is_approver_buyer_all', 'is_approver_buyer_add', 'is_approver_buyer_qpay', )

  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    for field in self.fields.values():
      field.widget.attrs['class'] = 'form-check form-switch'

    self.fields['is_approver_buyer_all'].widget.attrs['label'] = "すべて"
    self.fields['is_approver_buyer_add'].widget.attrs['label'] = "ユーザー追加"
    self.fields['is_approver_buyer_qpay'].widget.attrs['label'] = "前払いの承認"


class EntityCreateForm_seller(forms.ModelForm):

  #企業の場合の入力値、個人の場合はpersonnameが入る
  entityname = models.CharField('取引主体名', max_length=150, unique=False, default="", null=True, blank=True, validators=[name_validator],)
  representitive = models.CharField('代表者名', max_length=150, unique=False, default="", null=True, validators=[name_validator],)
  tel_main = models.CharField(_('電話番号（代表）'), max_length=30, default="", null=False, validators=[tel_regex])

  #企業の場合、住所は全部入力する
  postal_code_regex = RegexValidator(regex=r'^[0-9]+$', message = _("Postal Code must be entered in the format: '1234567'. Up to 7 digits allowed."))
  postal_code = models.CharField(_('郵便番号'), max_length=7, default="", null=False, blank=True, validators=[postal_code_regex])

  personname = models.CharField('お名前（個人）', blank=False, max_length=150, unique=False, null=True,)
  tel_direct = models.CharField(_('電話番号（直通）'), max_length=30, default="", null=False, validators=[tel_regex])

  department = models.CharField(_('部署名'), max_length=150, default="", blank=True, null=True)   # Entityが法人の場合
  title = models.CharField(_('役職名'), max_length=150, default="", blank=True, null=True)        # Entityが法人の場合


  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
      
    for field in self.fields.values():
      field.widget.attrs['class'] = 'form-control'
      field.widget.attrs['placeholder'] = field.label

    self.fields['personname'].widget.attrs['placeholder'] = '記入例：山田 太郎'
    self.fields['tel_main'].widget.attrs['placeholder'] = '数字のみ、ご記載ください'
    self.fields['postal_code'].widget.attrs['placeholder'] = '数字のみ、ご記載ください'
    self.fields['tel_direct'].widget.attrs['placeholder'] = '数字のみ、ご記載ください'

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

  def clean_tel_main(self):
    tel1 = self.cleaned_data['tel_main'].translate(tran_zen_han)
    tel2 = unicodedata.normalize('NFKC', ''.join(re.findall('[0-9０-９]+', tel1)))
    print(f'tel2:{tel2}（clean_tel_main. in class EntityCreateform_seller）')
    return tel2
    
  def clean_postal_code(self):
    postal_code1 = self.cleaned_data['postal_code'].translate(tran_zen_han)
    postal_code2 = unicodedata.normalize('NFKC', ''.join(re.findall('[0-9０-９]+', postal_code1)))
    return postal_code2

  def clean_tel_direct(self):
    tel1 = self.cleaned_data['tel_direct'].translate(tran_zen_han)
    tel2 = unicodedata.normalize('NFKC', ''.join(re.findall('[0-9０-９]+', tel1)))
    print(f'tel2:{tel2}（clean_tel_direct. in class EntityCreateform_seller）')
    return tel2

# 使っていないから削除予定
class EntityConfirmForm_buyer(forms.Form):

  class Meta:
    model = LegalEntity

# 使っていないから削除予定
class EntityConfirmForm_seller(forms.Form):

  class Meta:
    model = LegalEntity


## Metaを使う時には、forms.ModelFormを継承するべき 25/06/02
class AgreementConfirmForm_buyer(forms.Form):

  class Meta:
    model = LegalEntity
    fields = ('is_consent_membership')

class AgreementConfirmForm_seller(forms.Form):

  class Meta:
    model = LegalEntity
    fields = ('is_consent_membership')


#class MyPageForm_buyer(forms.ModelForm):
#
#  class Meta:
#    model = LegalEntity
#    fields = ('personname', 'tel', 'entityname', 'department', 'title', 'postal_code')
#
#class MyPageForm_seller(forms.ModelForm):
#
#  class Meta:
#    model = LegalEntity
#    fields = ('personname', 'tel', 'entityname', 'department', 'title', 'postal_code')


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
      'BankCode',
      'BankName',
      'BranchCode',
      'BranchName',
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

  #企業の場合の入力値、個人の場合はpersonnameが入る
  entityname = models.CharField('取引主体名', max_length=150, unique=False, default="", null=True, blank=True, validators=[name_validator],)
  representitive = models.CharField('代表者名', max_length=150, unique=False, default="", null=True, validators=[name_validator],)
  tel_main = models.CharField(_('電話番号（代表）'), max_length=30, default="", null=False, validators=[tel_regex])

  #企業の場合、住所は全部入力する
  postal_code_regex = RegexValidator(regex=r'^[0-9]+$', message = _("Postal Code must be entered in the format: '1234567'. Up to 7 digits allowed."))
  postal_code = models.CharField(_('郵便番号'), max_length=7, default="", null=False, blank=True, validators=[postal_code_regex])

  personname = models.CharField('お名前（個人）', blank=False, max_length=150, unique=False, null=True,)
  tel_direct = models.CharField(_('電話番号（直通）'), max_length=30, default="", null=False, validators=[tel_regex])

  department = models.CharField(_('部署名'), max_length=150, default="", blank=True, null=True)   # Entityが法人の場合
  title = models.CharField(_('役職名'), max_length=150, default="", blank=True, null=True)        # Entityが法人の場合


# 25/05/17 パスワード変更用意追加
class MyPasswordChangeForm(PasswordChangeForm):
    """パスワード変更フォーム"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            print(f'field.label={field.label}')


            field.widget.attrs['class'] = 'form-control'