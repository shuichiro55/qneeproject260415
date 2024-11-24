from django import forms
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
      'buyer_entity_choice',
      'buyer_entityname',
      'requested_amount',
      'original_payment_date',
      'evidence',
      #'seller_user',
      'seller_email',
      'seller_personname',
      #'seller_entity',
      'seller_entityname'
    )
    #widgets= {'seller_personname':forms.HiddenInput(), 'seller_entityname':forms.HiddenInput()}

  def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'
            # field.widget.attrs['placeholder'] = field.label

#class TxCreateForm(forms.ModelForm):
#
#
#  class Meta:
#    model = QpayTx
#    fields = ('buyer_entity_choice', 'requested_amount', 'evidence')
#
#  def __init__(self, *args, **kwargs):
#    #print(f'ここまで来てる4 buyer_entity_chices={buyer_entity_choices} (in __init__ of TxCreateForm)')
#    #print(f'ここまで来てる5 {self.base_fields['buyer_entity']} (in __init__ of TxCreateForm)')
#    #self.base_fields['buyer_entity'].choices = buyer_entity_choices
#        super().__init__(*args, **kwargs)
#        for field in self.fields.values():
#            field.widget.attrs['class'] = 'form-control'
#            # field.widget.attrs['placeholder'] = field.label

class TxCreateConfirmForm(forms.ModelForm):

  class Meta:
    model = QpayTx
    fields = ('buyer_entity_choice', 'requested_amount', 'evidence')

# 24/7/9 発注者が承認するために表示する一覧表。表示項目は未精査
class TxListForm_buyer_approve(forms.ModelForm):

  class Meta:
    model = QpayTx
    fields = ('seller_entity', 'seller_user', 'requested_amount', 'evidence')
    ##fields = ('seller_entity',  'requested_amount', 'evidence')


# 24/7/9 発注者が書類を発行するために表示する取引履歴。表示項目は未精査
class TxListForm_buyer_history(forms.ModelForm):

  class Meta:
    model = QpayTx
    fields = ('seller_entity', 'seller_user', 'requested_amount', 'evidence')
    ##fields = ('seller_entity', 'requested_amount', 'evidence')

class TxListForm_seller(forms.ModelForm):

  class Meta:
    model = QpayTx
    fields = ('seller_entity', 'seller_user', 'requested_amount', 'evidence')
    ##fields = ('seller_entity', 'requested_amount', 'evidence')

#class TxDetailForm(forms.ModelForm):
#
#  class meta:
#    model = QpayTx
#    fields = ('seller_entity', 'seller_user', 'request_amount', 'evidennce')
#
#  def __init__(self, *args, **kwargs):
#    super().__init__(*args, **kwargs)
#    for field in self.fields.values():
#      field.widget.attrs['class'] = 'form-control'
#      field.widget.attrs['placeholder'] = field.label