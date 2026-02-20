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
      'buyEntityName',
      'requested_amount',
      'exPayment_date',
      'sellUser_userName',
      'sellEntityName'
      #'sellUser_email',
    )
#    widgets = {
#      'exPayment_date': forms.SelectDateWidget
#    }
#    widgets= {'sellUser_userName':forms.HiddenInput(), 'sellEntityName':forms.HiddenInput()}
    
  def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'
            field.widget.attrs['placeholder'] = field.label        


  def clean_requested_amount(self):
      requested_amount = self.cleaned_data.get('requested_amount')
      print(f'self.cleaned_data[entityName]={requested_amount} (in TxCreateForm)')
      if requested_amount is None or "" :
        raise forms.ValidationError("申請金額をご入力ください.")
      return requested_amount
  
  def clean_exPayment_date(self):
      exPayment_date = self.cleaned_data.get('exPayment_date')
      print(f'self.cleaned_data[exPayment_date]={exPayment_date} (in TxCreateForm)')
      print(f'datetime.date.today()={datetime.date.today()}')
      
      if exPayment_date is None or "" :
        raise forms.ValidationError('「当初報酬日」にもともとの報酬の支払日を入力してください.')
      if exPayment_date <= datetime.date.today():
        raise forms.ValidationError("入力された「当初報酬日」が本日以前になっています.")
      return exPayment_date


class TxEvidenceForm(forms.ModelForm):

  class Meta:
    model = QpayTx
    fields = (
      'evidence',
    )
    #widgets= {'sellUser_userName':forms.HiddenInput(), 'sellEntityName':forms.HiddenInput()}

  # ★全部のフィールドに'form-control'をセットするべきか？ 2025/02/14
  def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'
            # field.widget.attrs['placeholder'] = field.label

  def clean_evidence(self):
      evidence = self.cleaned_data.get('evidence')
      print(f'self.cleaned_data[entityName]={evidence} (in TxEvidenceForm)')
      if evidence is None or "" :
        raise forms.ValidationError('証明書ファイルを選択してください')   
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