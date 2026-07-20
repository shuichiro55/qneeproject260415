from django import forms
import datetime
#from django.db import models
#from accounts.models import CustomUser, LegalEntity

from .models import QpayTx
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

import unicodedata, re

UserModel = get_user_model()


period_CHOICES = [
  ("0", "－"),
  ("2W", "2週間内の申請"),
  ("1M", "1ヶ月内の申請"), ("3M", "3ヶ月内の申請"),
  ("6M", "6ヶ月内の申請"), ("1Y", "1年内の申請"),
]
from django.forms import Select, SelectMultiple

class TxPeriodSetForm(forms.Form):
   
  applyPeriod = forms.ChoiceField(label="申請時点",
    choices=period_CHOICES,
    required=False,
    widget=forms.Select)
  
  applyPeriod_start = forms.DateField(label="開始日", required=False)
  applyPeriod_end = forms.DateField(label="終了日", required=False)

  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)

    # フィールドの属性をループで一括設定
    for field_name, field in self.fields.items():
      # ウィジェットのインスタンス判定
      widget_type = field.widget
            
      # セレクトボックス(1つ選択)と複数選択セレクトボックスの判定
      if isinstance(widget_type, (Select, SelectMultiple)):
        field.widget.attrs['class'] = 'custom-select-center'
      else:
        # テキストエリア、Input、Dateなどその他
        field.widget.attrs['class'] = 'form-control form-control-sm'

        #for field in self.fields.values():
        #    field.widget.attrs['class'] = 'form-select form-select-sm'

class TxCreateForm(forms.ModelForm):

  class Meta:
    model = QpayTx
    fields = (
      'sellEntityname',
      'sellUser_personname',
      'buyEntityname',
      'requested_amount',
      'exPayment_date',
      #'sellUser_email',
    )
#    widgets = {
#      'exPayment_date': forms.SelectDateWidget
#    }
#    widgets= {'sellUser_personname':forms.HiddenInput(), 'sellEntityname':forms.HiddenInput()}
    
  def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control form-control-sm'
            field.widget.attrs['placeholder'] = field.label        


  def clean_requested_amount(self):
      requested_amount = self.cleaned_data.get('requested_amount')
      print(f'self.cleaned_data[entityname]={requested_amount} (in TxCreateForm)')
      if requested_amount is None:
        raise forms.ValidationError("申請金額をご入力ください.")
      return requested_amount
  
  def clean_exPayment_date(self):
      exPayment_date = self.cleaned_data.get('exPayment_date')
      print(f'self.cleaned_data[exPayment_date]={exPayment_date} (in TxCreateForm)')
      print(f'datetime.date.today()={datetime.date.today()}')
      
      if exPayment_date is None:
        raise forms.ValidationError('「当初報酬日」にもともとの報酬の支払日を入力してください.')
      if exPayment_date <= datetime.date.today():
        raise forms.ValidationError("入力された「当初報酬日」が本日以前になっています.")
      return exPayment_date


class TxReapplyForm(forms.ModelForm):

  class Meta:
    model = QpayTx
    fields = (
      #'id',
      'sellEntityname',
      'sellUser_personname',
      'buyEntityname',
      'requested_amount',
      'exPayment_date',
      'evidence',
    )
    
  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)

    for field in self.fields.values():
      field.widget.attrs['class'] = 'form-control form-control-sm'
      field.widget.attrs['placeholder'] = field.label

  #def clean(self):
  #  cleaned_data = super().clean()
  #  print(f'pass1 in clean of TxReapplyForm')   
  #  # cleanのタイミングでは、正しくインスタンスとPKが紐付いています
  #  if self.instance and self.instance.pk:
  #   print(f"バリデーション時のPK: {self.instance.pk}")
  #   # PKに応じたバリデーションロジックをここに書く
  #          
  #  return cleaned_data

  def clean_buyEntityname(self):
    return self.cleaned_data.get('buyEntityname')
  
  def clean_requested_amount(self):
    requested_amount = self.cleaned_data.get('requested_amount')
    if requested_amount is not None:
        print(f'self.cleaned_data[request_amount]={requested_amount} (in TxReapplyForm)')
    return requested_amount

  def clean_exPayment_date(self):
    exPayment_date = self.cleaned_data.get('exPayment_date')
    print(f'self.cleaned_data[exPayment_date]={exPayment_date} (in TxReapplyForm)')
    if exPayment_date <= datetime.date.today():
      raise forms.ValidationError("入力された「当初報酬日」が本日以前になっています.")

    print(f'datetime.date.today()={datetime.date.today()}')
    return exPayment_date

  # modelsのvalidatorが優先されるので下記は通過しない
  # modelsのvalidatorではファイル拡張子もチェックする
  def clean_evidence(self):
      evidence = self.cleaned_data.get('evidence')
      print(f'self.cleaned_data[evidence]={evidence} (in TxReapplyForm)')
      if not evidence: #if evidence is None or "" :
        raise forms.ValidationError('証明書類のファイルを選択してください')   
      return evidence


class TxEvidenceForm(forms.ModelForm):

  class Meta:
    model = QpayTx
    fields = (
      'evidence',
    )
    #widgets= {'sellUser_personname':forms.HiddenInput(), 'sellEntityname':forms.HiddenInput()}

  # ★全部のフィールドに'form-control'をセットするべきか？ 2025/02/14
  def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'
            # field.widget.attrs['placeholder'] = field.label

  # modelsのvalidatorが優先されるので下記は通過しない
  # modelsのvalidatorではファイル拡張子もチェックする
  def clean_evidence(self):
      evidence = self.cleaned_data.get('evidence')
      print(f'self.cleaned_data[entityname]={evidence} (in TxEvidenceForm)')
      if not evidence: #if evidence is None or "" :
        raise forms.ValidationError('証明書類のファイルを選択してください')   
      return evidence


class TxCreateConfirmForm(forms.ModelForm):

  class Meta:
    model = QpayTx
    fields = ('requested_amount', 'evidence')

# 24/7/9 発注者が承認するために表示する一覧表。表示項目は未精査
class TxApproveForm_buyer(forms.ModelForm):

  class Meta:
    model = QpayTx
    fields = ('sellEntity', 'sellUser', 'requested_amount', 'evidence')
    ##fields = ('sellEntity',  'requested_amount', 'evidence')


# 24/7/9 発注者が書類を発行するために表示する取引履歴。表示項目は未精査
class TxListForm_buyer(forms.ModelForm):

  class Meta:
    model = QpayTx
    fields = ('sellEntity', 'sellUser', 'requested_amount', 'evidence')
    ##fields = ('sellEntity', 'requested_amount', 'evidence')

class TxListForm_seller(forms.ModelForm):

  class Meta:
    model = QpayTx
    fields = ('sellEntity', 'sellUser', 'requested_amount', 'evidence')
    ##fields = ('sellEntity', 'requested_amount', 'evidence')

CHOICES = [
    ('radio0', '当初報酬日が誤っている'),
    ('radio1', '金額が異なる'),
    ('radio2', '証明書類（画像）が違う'),
    ('radio3', '証明書類の画像が不鮮明'),
    ('radio4', 'その他'),
]

class SendbackInfoForm_qpay(forms.Form):

  reason_radio = forms.ChoiceField(
    label="差戻理由",
    choices=CHOICES,
    widget=forms.RadioSelect(attrs={'class': 'form-check-input'}), # 基本のBootstrapクラス
    required=False,
  )

  # その他理由の場合の記載
  reason_text = forms.CharField(
    label="その他理由", max_length=100,
    required=False, )
    
  # ゲストへのメッセージ
  message = forms.CharField(
    label="メッセージ", max_length=200, widget=forms.Textarea(),
    required=False,)

  def __init__(self, *args, **kwargs):
    self.radioValue = kwargs.pop('radioValue', None)
    super().__init__(*args, **kwargs)


  def clean_reason_radio(self):
    reason_radio = self.cleaned_data['reason_radio']
    print(f'self.cleaned_data[reason_radio={reason_radio} (clean_reason_radio in SendbackInfoForm_qpay)')
    if reason_radio is None or reason_radio == '':
      raise forms.ValidationError('必ず差戻の理由を選択してください。')
    return unicodedata.normalize('NFKC', reason_radio)

  def clean_reason_text(self):
    reason_text = self.cleaned_data['reason_text']
    print(f'self.cleaned_data[reason_text]={reason_text} (clean_reason_text in SendbackInfoForm_qpay)')
    if self.radioValue == 'radio4':
      if reason_text == '' or reason_text is None:
        raise forms.ValidationError('その他を選択した場合は理由をご記載ください。')
    
    return unicodedata.normalize('NFKC', reason_text)

  def clean_message(self):
    message = self.cleaned_data['message']
    print(f'self.cleaned_data[message]={message} (clean_message in SendbackInfoForm_qpay)')
    return unicodedata.normalize('NFKC', message)
  
#class TxDetailForm(forms.ModelForm):
#
#  class meta:
#    model = QpayTx
#    fields = ('sellEntity', 'sellUser', 'request_amount', 'evidennce')
#
#  def __init__(self, *args, **kwargs):
#    super().__init__(*args, **kwargs)
#    for field in self.fields.values():
#      field.widget.attrs['class'] = 'form-control'
#      field.widget.attrs['placeholder'] = field.label