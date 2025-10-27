from django import forms
from accounts.models import LegalEntity


class MailForm(forms.Form):

  title = forms.CharField(label='メール件名', max_length=100)
  message = forms.CharField(
    label='メール本文',max_length=1000,
    widget=forms.Textarea(attrs={'rows': 5, 'cols': 80}))


class UserEntryForm(forms.Form):
  userName = forms.CharField(label='あなたのお名前', max_length=100)
  email = forms.CharField(label='メールアドレス', max_length=150)

class CSVUploadForm(forms.Form):
  file = forms.FileField()