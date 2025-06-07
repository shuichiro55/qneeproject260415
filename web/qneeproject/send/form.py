from django import forms
import datetime
#from django.db import models
#from accounts.models import CustomUser, LegalEntity

from .models import QpayInfoSend
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

import unicodedata, re

UserModel = get_user_model()

class QpayInfoSendForm(forms.ModelForm):

  class Meta:
    model = QpayInfoSend
    fields = (

    )

#    widgets = {   ??widgetsってなんだっけ？？
#      'original_payment_date': forms.SelectDateWidget
#    }
#    widgets= {'sellerUser_personname':forms.HiddenInput(), 'sellerEntity_entityname':forms.HiddenInput()}
    
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