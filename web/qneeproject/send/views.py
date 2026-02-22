import csv
import io
from django.shortcuts import redirect, render
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render
from django.contrib.auth import get_user_model
from django.views import generic
from qpay.models import QpayTx
from accounts.models import LegalEntity
from send.models import ServInfoMailSets, ServInfoMailLog, AddrProfile

from django.urls import reverse, reverse_lazy
from django.http import HttpResponse, HttpResponseBadRequest #, HttpResponseRedirect
from django.template.response import TemplateResponse

from .form import AddrFileUpForm
import openpyxl

#from django.utils import timezone
#import calendar
#import datetime
#from dateutil.relativedelta import relativedelta
import json

from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.core.mail import EmailMessage

#from django.contrib import messages
#from django.core.paginator import Paginator
#from django.core.mail import EmailMessage

from .form import RepeatSetForm, UserEntryForm, ServInfoMailForm
from .form import CSVUploadForm, ImportExportForm #小原さん作成
import datetime
import calendar

UserModel = get_user_model()


class ServInfoMailSetsView(LoginRequiredMixin, generic.UpdateView):

  #buyUser_id = -1  おそらく変更できない（get内で変更したが、post内で変更されていない）
  #buyEntity_id = -1

  #" 定期配信の設定値 "
  #repeatOnOff = 'on'
  #interval = 2 # 初期値は2か月おき
  #dayOfMonth = 1 # 初期値は10日

  def get(self, request, *args, **kwargs):

    #buyUser = UserModel.objects.get(email=self.request.user)
    #buyEntity = LegalEntity.objects.get(pk=buyUser.entity_id)

    buyEntity_id = self.request.session.get('buyEntity_id', None)
    buyEntity = LegalEntity.objects.get(pk=buyEntity_id)

    sellEntitys_pkList = QpayTx.objects.select_related('buyEntity').filter(buyEntity=buyEntity).order_by('-created_at').values_list('sellEntity')
    # 関係しているゲスト
    # values_list("name", "team", flat=False) ⇒nameとteamの複数指定は「flag=False」
    # <QuerySet [('山下', 'ファルコンズ'), ('瀬戸', 'タイガース'), ]
    # values("team")は、辞書型で取得{'team', 'ファルコンズ'}

    sellEntitysUsers = UserModel.objects.select_related('entity').filter(entity__pk__in=sellEntitys_pkList).values('userName','email','entity__entityName')
    # 関係しているゲストのユーザー（複数）を取得

    # 上記のクエリーのアウトプットを確認したうえで項目を絞る
    # .values('id','customuser_id','customuser__userName','customuser__email')
    # https://yk5656.hatenablog.com/entry/20210410/1617980400
    # 「yuki5656 diary Djangoでデータを取得してみる(外部キー) Authorモデル側」を参考
    # 【コメント：prefetch_relatedは、多モデル側（customuser）側から隠せ巣親モデル（Foreignkeyの参照先モデル）から取得する場合のコードを参考】

    # SQL確認用コード
    print(f'sql1={sellEntitys_pkList.query}')
    print(f'sql2={sellEntitysUsers.query}')
    print(f'sellEntitysUsers={sellEntitysUsers}')

    mailSets, created = ServInfoMailSets.objects.get_or_create(buyEntity=buyEntity)
    " フォームの「startDate」の初期値セット（保存しない） "
    if mailSets.startDate is not None:
      str_startDate = mailSets.startDate.strftime('%Y/%m/%d')
    else:
      str_startDate = self.nearStartDate()

    print(f'pass0-1 mailSets={mailSets} def get in SevInfoMailSetsView')

    init_data = {
      'startDate':str_startDate,
      'interval':mailSets.interval,
      'dayOfMonth':mailSets.dayOfMonth
    }
    print(f'init_data={init_data}')

    context = {
      'addrFileUpForm': AddrFileUpForm(),
      'mailForm': ServInfoMailForm(),
      'repeatOnOff': mailSets.repeatOnOff,
      'RepeatSetForm': RepeatSetForm(initial=init_data),
    }
    return TemplateResponse(request, 'send/servInfoMailSets.html', context)

  def nearStartDate():
    today = datetime.date.today()
    if today.day < 10:
      str_startDate = datetime.date(today.year, today.month, 10).strftime('%Y/%m/%d')
    elif today.day <20:
      str_startDate = datetime.date(today.year, today.month, 20).strftime('%Y/%m/%d')
    elif today.day < calendar.monthrange(today.year, today.month)[1]:
      str_startDate = calendar.monthrange(today.year, today.month)[1]
    else:
      str_startDate = datetime.date(today.year, today.month+1 , 10).strftime('%Y/%m/%d')       

    return str_startDate

  def post(self, request, *args):

    buyEntity_id = self.request.session.get('buyEntity_id', None)
    print(f'buyEntity_id={buyEntity_id}')

    buyEntity = LegalEntity.objects.get(pk=buyEntity_id)
    buyUser = UserModel.objects.get(entity=buyEntity)

    sellEntitys_pkList = QpayTx.objects.select_related('buyEntity').filter(buyEntity=buyEntity).order_by('-created_at').values_list('sellEntity')
    sellEntitysUsers = UserModel.objects.select_related('entity').filter(entity__pk__in=sellEntitys_pkList).values('userName','email','entity__entityName')

    mailSets = ServInfoMailSets.objects.get(buyEntity=buyEntity)

    next2 = self.request.POST.get('next2', None)

    if next2 != None:

      if next2.find("ToSendNow") >= 0:

        print(f'pass1 def post if "ToSendNow" in SevInfoMailSetsView')

        current_site = get_current_site(self.request)
        domain = current_site.domain

        for sellUser in sellEntitysUsers:

          #★★ 251214 除外リストに該当するものは外す
          #★★ 251214 未登録ユーザー or 登録済みユーザーのどちらに送るか
          #★★ 251214 送信日について休日調整するか選択する機能を入れるか

          context1 = {
            'protocol': self.request.scheme,
            'domain': domain,
            'buUser_id': json.dumps(buyUser.pk),      # 処理者のuser.pkを維持する
            'buyEntity_id': json.dumps(buyEntity.pk), # 処理者のentity.pkを維持する
          }
          print(f'buyUser.pk={buyUser.pk}, buyEntity.pk={buyEntity.pk}')
          subject = render_to_string('send/mail/servInfoMail_subject.txt', context1)
          message = render_to_string('send/mail/servInfoMail_message.txt', context1)

          from_email = 'shuichiro.tomihari.201604@gmail.com'
          recipient_list = [sellUser.email]
          #bcc =  ["toritoritorina@gmail.com"]  # BCCリスト
          email = EmailMessage(subject, message, from_email, recipient_list)
          email.send()
  
          print(f'pass1 sellUser.email={sellUser.email}（ServInfoMailSetsView, post)')

          context = {}
          return TemplateResponse(self.request, 'accounts/buyer/mypage.html', context)


      if next2.find("ToSaveSendSets") >= 0:

        print(f'pass2 def post if "ToSaveSendSets" in SevInfoMailSetsView')

        """  定期配信の設定を更新（EntityCreateViewで初期設定済み） """
        #mailSets = ServInfoMailSets.objects.create(
        #  startDate=startDate, interval=interval, dayOfMonth=dayOfMonth)

        repeatOnOff = self.request.POST.get("name_RepeatOnOff", None)

        if repeatOnOff == 'on':
          
          #mailSets.buyEntity = buyEntity
          mailSets.repeatOnOff = repeatOnOff

          str_startDate = self.request.POST.get("startDate", None)
          interval = int(self.request.POST.get("interval", None))
          dayOfMonth = int(self.request.POST.get("dayOfMonth", None))

          print(f'str_startDate={str_startDate}, interval={interval} def post repeatOnOff="on" in ServInfoMailSetView')

          mailSets.startDate = datetime.date(
            int(str_startDate.split('/')[0]),
            int(str_startDate.split('/')[1]),
            int(str_startDate.split('/')[2]))
          mailSets.interval = interval
          mailSets.dayOfMonth = dayOfMonth

          month_startDate = int(str_startDate.split('/')[1])
          month_min = month_startDate % interval

          print(f'month_startDate={month_startDate}, month_min={month_min} in ServInfoMailSetView')

          x = 1
          while x <= 12:
            if x >= month_min and ((x - month_min) % interval) == 0:
              mailSets.json_sendMonth[str(x)] = '1'
            else:
              mailSets.json_sendMonth[str(x)] = '0'
              
            print(f'x={x}, mailSets.json_sendMonth[x]={mailSets.json_sendMonth[str(x)]}')

            x += 1

          #★★ 260213 修正が必要　jsonfieldのアップデートを確認する
          x = 1       
          while x <= 3:
            if x == month_startDate: mailSets.json_sendDay[str(x)] = '1'
            else: mailSets.json_sendDay[str(x)] = '0'
            x += 1

          print(f'mailSets.json_sendMonth={mailSets.json_sendMonth}, mailSets.json_sendDay={mailSets.json_sendDay} in ServInfoMailSetView')

          mailSets.save()

          context = {}
          return TemplateResponse(self.request, 'accounts/buyer/mypage.html', context)


        if repeatOnOff == 'off':

          #mailSets.buyEntity = buyEntity
          mailSets.repeatOnOff = repeatOnOff
          mailSets.startDate = None
   
          mailSets.save()

          init_data = {
            'startDate':self.nearStartDate(),
            'interval':2,
            'dayOfMonth':1,
          }
          print(f'pass3-1 init_data={init_data} mailSets.startDate={mailSets.startDate}')

          context = {
            'sellEntitysUsers': sellEntitysUsers,
            'addrFileUpForm': AddrFileUpForm(),            
            'mailForm1': ServInfoMailForm(), 

            'repeatOnOff': repeatOnOff,
            'RepeatSetForm': RepeatSetForm(initial=init_data),
          }
          return TemplateResponse(self.request, 'send/servInfoMailSets.html', context)
        

    """ 個別入力されたアドレスについてメール送信し、ログを取る """
    btnValue = self.request.POST.get('name_fixAddrBtn', None)

    if btnValue != None:

      print(f'pass3 btnValue={btnValue} def post in SevInfoMailSetsView')


      # ★★ 260222 mailListがセットされてない場合はエラーを出す
      log = ServInfoMailLog.objects.create(buyEntity=buyEntity, sendUser=buyUser)
      log.save()

      # 送付先のログ作成
      i = 1
      while True:
        address = self.request.POST.get("name_ItemInput_" + str(i), None)
        print(f'pass4 name={"name_ItemInput_"+ str(i)} def post in SevInfoMailSetsView')
        print(f'pass4 addresss={address} def post in SevInfoMailSetsView')

        if address != None:
          # ★★ 260222 JSON形式での保存方法を確認する
          # {{code:'1', address:'', name:''},{code:'2', address:'', name:''}}の形式で保存
          data = {"address":address, "name":""}
          profile = AddrProfile.objects.create(addr_id=str(i), data=data)
          profile.logLink = log
          profile.save()

        else:
          break
        i += 1

      print(f'pass5 log.smailingList={log.mailingList}def post in SevInfoMailSetsView')

      log.save()

      context = {}
      return TemplateResponse(self.request, 'accounts/buyer/mypage.html', context)


    next1 = self.request.POST.get('next1', None)

    if next1 != None:

      print(f'pass-6-1 ファイル読み込みプロセス')
      if next1.find("ToUploadAddrFile") >= 0:

        mailLog = ServInfoMailLog.objects.filter(buyEntity=buyEntity, sent_at__isnull=True).order_by('-created_at').first()

        if mailLog is None: mailLog = ServInfoMailLog.objects.create(buyEntity=buyEntity)
        " select_relatedは、ForeignKey（外部キー）やOneToOneFieldの順方向参照 "
        " prefetch_relatedは、ManyToManyField、または逆方向のForeignKey "

        print(f'pass-6-2 ファイル読み込みプロセス')
        form = AddrFileUpForm(request.POST, request.FILES)
       
        fileType = request.POST.get("fileType", None)
        print(f'fileType={fileType} in ServInfoMailSetsView')

        if form.is_valid():

          fileType = form.cleaned_data['fileType']  
          addrFile = form.cleaned_data['addrFile'] # アップロードされたファイルをメモリ内で読み込む

          log = ServInfoMailLog.objects.create(buyEntity=buyEntity, sendUser=buyUser)
          log.save()

          print(f'pass-6-4 ファイル読み込みプロセス')

          if fileType == "excel":

            wb = openpyxl.load_workbook(addrFile)
            sheet = wb.active # アクティブなシートを選択

            # 2行目から1行ずつループ（1行目がヘッダーと想定）
            # min_row=2 で開始行、max_col=2 で2項目目までを指定
            i = 1
            for row in sheet.iter_rows(min_row=2, max_col=2, values_only=True):
              address, name = row # 1行から2つの項目を取り出す

              data = {"address":address, "name":name}
              profile = AddrProfile.objects.create(addr_id=str(i), data=data)
              profile.logLink = log
              profile.save()

              i += 1

              # ★★ 260222 JSON形式での保存方法を確認する
              # ★★ 260223 前回の送信以降に作成したデータが消す（ウォーニングも出す）
              # ★★ 260223 csvからも読み込むようにする
              # ★★ 260223 読込用ファイルをダウンロードできるようにする

              # addr_id = "1" ,{"address":"-@-", "name":"富張"}の形式で保存              

              # ここでデータベースへの保存などの処理を行う
              # 例: MyModel.objects.create(name=item1, value=item2)
            
            profiles = AddrProfile.objects.filter(logLink=log)
            for each in profiles:
              print(each.data["address"], each.data["name"])  # 辞書としてアクセス

        else:
          print(form.errors)  # エラー内容を確認
        

        if mailSets.startDate is not None:
          str_startDate = mailSets.startDate.strftime('%Y/%m/%d')
        else:
          str_startDate =self.nearStartDate()

        print(f'pass 6-6 mailSets.startDate={mailSets.startDate}, mailSets.interval={mailSets.interval} mailSets.dayOfMonth={mailSets.dayOfMonth} def get in SevInfoMailSetsView')

        init_data = {
          'startDate':str_startDate,
          'interval':mailSets.interval,
          'dayOfMonth':mailSets.dayOfMonth}
        print(f'init_data={init_data}')

        context = {
          'addrFileUpForm': AddrFileUpForm(),
          'mailForm': ServInfoMailForm(),  # 
          'repeatOnOff': mailSets.repeatOnOff,
          'RepeatSetForm': RepeatSetForm(initial=init_data),
        }

        return TemplateResponse(request, 'send/servInfoMailSets.html', context)


    return TemplateResponse(request, 'send/servInfoMailSets.html', {'addrFileUpForm': AddrFileUpForm()})

  def form_invalid(self, form):
    print(f'ここまで来てる4（form_invalid in class SerInfoMailSetsView）')
    print(form.errors)
    return super().form_invalid(form)

      #if next1.find('ToExportCSV') >=0 :
      #
      #  response = HttpResponse(content_type='text/csv')
      #  response['Content-Disposition'] = 'attachment; filename="users.csv"'
      #  writer = csv.writer(response)
      #  writer.writerow(['名前', 'メールアドレス'])
      #
      #  entity = LegalEntity.objects.get(email=request.user)
      #  entityUsers = entity.entity_users.all()
      #
      #  for user in entityUsers():
      #    writer.writerow([user.userName, user.email])
      #
      #  return response
      #
      #if next1.find('ToImportCSV') >= 0:
      #
      #  form = CSVUploadForm(request.POST, request.FILES)
      #  if form.is_valid():
      #
      #    data = request.FILES['file'].read().decode('utf-8')
      #    reader = csv.reader(io.StringIO(data))
      #    preview_data = [row for row in reader if row]
      #    request.session['csv_data'] = preview_data
      #    return TemplateResponse(request, 'send/import_preview.html', {'rows': preview_data})
      #  
      #  return TemplateResponse(request, 'send/import_csv.html', {'form': form})
      #
      #return HttpResponseBadRequest()  # 基本的にはここには来ない


def register(request):

  if request.method == 'POST':
    form = UserEntryForm(request.POST)
    if form.is_valid():
      form.save()
      return redirect('send/servInfoMailSets.html')
  else:
    form = UserEntryForm()
  return TemplateResponse(request, 'send/register.html', {'form': form})


def import_csv(request):
  if request.method == 'POST':
    form = CSVUploadForm(request.POST, request.FILES)
    if form.is_valid():
      data = request.FILES['file'].read().decode('utf-8')
      reader = csv.reader(io.StringIO(data))
      preview_data = [row for row in reader if row]
      request.session['csv_data'] = preview_data
      return TemplateResponse(request, 'send/import_preview.html', {'rows': preview_data})
  else:
      form = CSVUploadForm()
  return TemplateResponse(request, 'send/import_csv.html', {'form': form})

def finalize_import(request):
  csv_data = request.session.pop('csv_data', [])
  for name, email in csv_data:
    LegalEntity.objects.get_or_create(personname=name, email=email)
  return redirect(reverse('send:servInfoMailSets.html'))

def export_csv(self, request):
  response = HttpResponse(content_type='text/csv')
  response['Content-Disposition'] = 'attachment; filename="users.csv"'
  writer = csv.writer(response)
  writer.writerow(['名前', 'メールアドレス'])

  for user in LegalEntity.objects.all():
    writer.writerow([user.personname, user.email])
  return response


"""  """
class TaskAgentView(LoginRequiredMixin, generic.UpdateView):
  
  def get(self, request, *args, **kwargs):

    next = self.request.POST.get('next', None)

    if next.find("ToUploadFile") >= 0:

      context = {}
      return render(request, 'send/admin/servInfoMailSets.html', context)  

    context = {}
    return render(request, 'send/admin/servInfoMailSets.html', context)  


  def post(self, request, *args, **kwargs):
    context = {}
    return render(request, 'accounts/admin/mypage.html', context)  
  

"""  """
class TaskAgentView(LoginRequiredMixin, generic.UpdateView):
  
  def get(self, request, *args, **kwargs):

    next = self.request.POST.get('next', None)

    if next.find("ToStartTask") >= 0:

      context = {}
      return render(request, 'accounts/admin/mypage.html', context)  

    if next.find("ToStopTask") >= 0:

      context = {}
      return render(request, 'accounts/admin/mypage.html', context)  

    context = {}
    return render(request, 'send/taskAgent.html', context)  


  def post(self, request, *args, **kwargs):
    context = {}
    return render(request, 'accounts/admin/SendAgent.html', context)  
  

"""
class TxListView_buyer_settings(LoginRequiredMixin, generic.UpdateView):

  def get(self, request, *args, **kwargs):

    user =usermodel.objects.get(email=self.request.user)
    object_list = QpayTx.objects.filter(buyEntity = user.entity).order_by('-created_at')

    if user.type1 == 2:
      messages.add_message(request, messages.INFO, "発注者としてログインして下さい") 
      return HttpResponseRedirect(reverse('accounts:logout'))

    paginate_by = 4 # 4で仮置き

    paginator = Paginator(object_list, paginate_by)

    page_num = request.GET.get('page', 0)
    if page_num == 0:
      try:
        page_num = self.kwargs['page_num']
      except:
        page_num = 1

    page_obj = paginator.page(page_num)
    context = {
      'object_list': object_list,
      'page_obj': page_obj,
    }
    return TemplateResponse(request, 'send/txlist_buyer_settings.html', context)
"""
