from django import forms
import datetime
#from django.db import models
#from accounts.models import CustomUser, LegalEntity

from .models import QpayTx
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

import unicodedata, re

UserModel = get_user_model()

class TxCreateForm(forms.ModelForm):

  class Meta:
    model = QpayTx
    fields = (
      'id',
      'buyEntityname',
      'requested_amount',
      'original_payment_date',
      'sellUser_email',
      'sellUser_personname',
      'sellEntityname'
    )
#    widgets = {
#      'original_payment_date': forms.SelectDateWidget
#    }
#    widgets= {'sellUser_personname':forms.HiddenInput(), 'sellEntityname':forms.HiddenInput()}
    
  def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'
            field.widget.attrs['placeholder'] = field.label        


  def clean_requested_amount(self):
      requested_amount = self.cleaned_data.get('requested_amount')
      print(f'self.cleaned_data[entityname]={requested_amount} (in TxCreateForm)')
      if requested_amount is None or "" :
        raise forms.ValidationError("申請金額をご入力ください.")
      return requested_amount
  
  def clean_original_payment_date(self):
      original_payment_date = self.cleaned_data.get('original_payment_date')
      print(f'self.cleaned_data[original_payment_date]={original_payment_date} (in TxCreateForm)')
      print(f'datetime.date.today()={datetime.date.today()}')
      
      if original_payment_date is None or "" :
        raise forms.ValidationError('「当初報酬日」にもともとの報酬の支払日を入力してください.')
      if original_payment_date <= datetime.date.today():
        raise forms.ValidationError("入力された「当初報酬日」が本日以前になっています.")
      return original_payment_date


class TxEvidenceForm(forms.ModelForm):

  class Meta:
    model = QpayTx
    fields = (
      'id',
      'evidence',
    )
    #widgets= {'sellUser_personname':forms.HiddenInput(), 'sellEntityname':forms.HiddenInput()}

  # ★全部のフィールドに'form-control'をセットするべきか？ 2025/02/14
  def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'
            # field.widget.attrs['placeholder'] = field.label

  def clean_evidence(self):
      evidence = self.cleaned_data.get('evidence')
      print(f'self.cleaned_data[entityname]={evidence} (in TxEvidenceForm)')
      if evidence is None or "" :
        raise forms.ValidationError('証明書ファイルを選択してください')   
      return evidence


class TxCreateConfirmForm(forms.ModelForm):

  class Meta:
    model = QpayTx
    fields = ('requested_amount', 'evidence')

# 24/7/9 発注者が承認するために表示する一覧表。表示項目は未精査
class TxListForm_buyer_approve(forms.ModelForm):

  class Meta:
    model = QpayTx
    fields = ('sellEntity', 'sellUser', 'requested_amount', 'evidence')
    ##fields = ('sellEntity',  'requested_amount', 'evidence')


# 24/7/9 発注者が書類を発行するために表示する取引履歴。表示項目は未精査
class TxListForm_buyer_history(forms.ModelForm):

  class Meta:
    model = QpayTx
    fields = ('sellEntity', 'sellUser', 'requested_amount', 'evidence')
    ##fields = ('sellEntity', 'requested_amount', 'evidence')

class TxListForm_seller(forms.ModelForm):

  class Meta:
    model = QpayTx
    fields = ('sellEntity', 'sellUser', 'requested_amount', 'evidence')
    ##fields = ('sellEntity', 'requested_amount', 'evidence')

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