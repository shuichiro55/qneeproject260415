from django import forms
#from accounts.models import LegalEntity

interval_CHOICES = [
  ("1", "1カ月おき"),("2", "2カ月おき"), ("3", "3カ月おき"),("4", "4カ月おき"),
]

dayOfMonth_CHOICES = [("1", "10日"),("2", "20日"), ("3", "月末"),]


#from django.utils import timezone
import calendar
import datetime
from dateutil.relativedelta import relativedelta

class RepeatSetForm(forms.Form):
  
  startDate = forms.ChoiceField(label="開始日", required=False,)
  interval = forms.ChoiceField(label="間隔", choices=interval_CHOICES, required=False)
  dayOfMonth = forms.ChoiceField(label="月の◯日", choices=dayOfMonth_CHOICES, required=False)

  #holidayAdjust = forms.ChoiceField(label="休日調整", choices=choices_holidayAdjust, initial="before")

  def __init__(self, *args, **kwargs):    
    super().__init__(*args, **kwargs)

    #print(f'startDate={startDate} interval={interval} dayOfMonth={dayOfMonth}')

    today = datetime.date.today()
    after1M = today + relativedelta(months=1)
    after2M = today + relativedelta(months=2)
    after3M = today + relativedelta(months=3)

    lastDay_thisMonth = calendar.monthrange(today.year, today.month)[1]
    lastDay_after1M = calendar.monthrange(after1M.year, after1M.month)[1]
    lastDay_after2M = calendar.monthrange(after2M.year, after2M.month)[1]
    lastDay_after3M = calendar.monthrange(after3M.year, after3M.month)[1]

    list_startDate = []  # 日付を8個まで追加する
    listCnt = 0

    #if startDate != "":
    #  list_startDate.append((startDate.strftime('%Y/%m/%d'), startDate.strftime('%Y/%m/%d')))


    # 開始日の同月は、月内での日付を見て追加する
    if listCnt < 9 and today.day < 10:
      listCnt += 1; date = datetime.date(today.year, today.month, 10)
      list_startDate.append((date.strftime('%Y/%m/%d'), date.strftime('%Y/%m/%d')))

    if listCnt < 9 and today.day < 20:
      listCnt += 1; date = datetime.date(today.year, today.month, 20)
      list_startDate.append((date.strftime('%Y/%m/%d'), date.strftime('%Y/%m/%d')))

    if listCnt < 9 and today.day < lastDay_thisMonth:
      listCnt += 1; date = datetime.date(today.year, today.month, lastDay_thisMonth)
      list_startDate.append((date.strftime('%Y/%m/%d'), date.strftime('%Y/%m/%d')))


    # 開始日の翌月以降は、10日、20日、月末のすべてを加える
    if listCnt < 9:
      listCnt+=1; date = datetime.date(after1M.year, after1M.month, 10)
      list_startDate.append((date.strftime('%Y/%m/%d'), date.strftime('%Y/%m/%d')))
    if listCnt < 9:
      listCnt+=1; date = datetime.date(after1M.year, after1M.month, 20)
      list_startDate.append((date.strftime('%Y/%m/%d'), date.strftime('%Y/%m/%d')))
    if listCnt < 9:
      listCnt+=1; date = datetime.date(after1M.year, after1M.month, lastDay_after1M)
      list_startDate.append((date.strftime('%Y/%m/%d'), date.strftime('%Y/%m/%d')))

    if listCnt < 9:
      listCnt+=1; date = datetime.date(after2M.year, after2M.month, 10)
      list_startDate.append((date.strftime('%Y/%m/%d'), date.strftime('%Y/%m/%d')))
    if listCnt < 9:
      listCnt+=1; date = datetime.date(after2M.year, after2M.month, 20)
      list_startDate.append((date.strftime('%Y/%m/%d'), date.strftime('%Y/%m/%d')))
    if listCnt < 9:
      listCnt+=1; date = datetime.date(after2M.year, after2M.month, lastDay_after2M)
      list_startDate.append((date.strftime('%Y/%m/%d'), date.strftime('%Y/%m/%d')))

    if listCnt < 9:
      listCnt+=1; date = datetime.date(after3M.year, after3M.month, 10)
      list_startDate.append((date.strftime('%Y/%m/%d'), date.strftime('%Y/%m/%d')))
    if listCnt < 9:
      listCnt+=1; date = datetime.date(after3M.year, after3M.month, 20)
      list_startDate.append((date.strftime('%Y/%m/%d'), date.strftime('%Y/%m/%d')))
    if listCnt < 9:
      listCnt+=1; date = datetime.date(after3M.year, after3M.month, lastDay_after3M)
      list_startDate.append((date.strftime('%Y/%m/%d'), date.strftime('%Y/%m/%d')))

    print(f'list_startDate={list_startDate}')
    self.fields['startDate'].choices = list_startDate


class ServInfoMailContentForm(forms.Form):

  title = forms.CharField(label='メール件名', max_length=100)
  message = forms.CharField(
    label='メール本文',max_length=1000,
    widget=forms.Textarea(attrs={'rows': 5, 'cols': 80}))


class UserEntryForm(forms.Form):
  userName = forms.CharField(label='あなたのお名前', max_length=100)
  email = forms.CharField(label='メールアドレス', max_length=150)

class EmailAddrFileUploadForm(forms.Form):
  fileType = forms.ChoiceField(
    label='', choices=[("1", "エクセルファイル"),("2", "CSVファイル"),])
  # ★★ 260220 googleスプレッドシートを加えるか
 
  emailAddrFile = forms.FileField()


## 以下、小原さんのコードからコピペ


class CSVUploadForm(forms.Form):
  file = forms.FileField()

class ImportExportForm(forms.Form):
  import_file = forms.FileField(label="取り込み（Excel/CSV）", required=False)
  export_format = forms.ChoiceField(
    label="出力形式", choices=[("xlsx", "EXCEL"), ("csv", "CSV")], initial="xlsx"
  )