import csv
import io
from django.shortcuts import redirect, render
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render
from django.contrib.auth import get_user_model
from django.views import generic
from qpay.models import QpayTx
from accounts.models import LegalEntity
from send.models import ServInfoMailSets, ServInfoMailLog

from django.urls import reverse, reverse_lazy
from .form import RepeatSetForm 
from django.http import HttpResponse, HttpResponseBadRequest #, HttpResponseRedirect
from django.template.response import TemplateResponse

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

#from .forms import CSVUploadForm, UserEntryForm #edited by s.tomihari 251010
from .form import ServInfoMailContentForm, CSVUploadForm, UserEntryForm, ImportExportForm
import datetime
import calendar

UserModel = get_user_model()


class ServInfoMailSetsView(LoginRequiredMixin, generic.UpdateView):

  buyUser_id = -1
  buyEntity_id = -1

  def get(self, request, *args, **kwargs):

    buyUser = UserModel.objects.get(email=self.request.user)
    buyEntity = LegalEntity.objects.get(pk=buyUser.entity_id)

    self.buyUser_id = buyUser.pk
    self.buyEntity_id = buyEntity.pk

    sellEntitys_pkList = QpayTx.objects.select_related('buyEntity').filter(buyEntity=buyEntity).order_by('-created_at').values_list('sellEntity')
    # 関係しているゲストのpk（複数）を取得
    
    sellEntitysUsers = UserModel.objects.select_related('entity').filter(entity__pk__in=sellEntitys_pkList).values('userName','email','entity__entityName')
    # 関係しているゲストのユーザー（複数）を取得

    # 上記のクエリーのアウトプットを確認したうえで項目を絞る
    # .values('id','customuser_id','customuser__userName','customuser__email')
    # https://yk5656.hatenablog.com/entry/20210410/1617980400
    # 「yuki5656 diary Djangoでデータを取得してみる(外部キー) Authorモデル側」を参考
    # 【コメント：prefetch_relatedは、「」多モデル側（customuser）側から隠せ巣親モデル（Foreignkeyの参照先モデル）から取得する場合のコードを参考】

    # SQL確認用コード
    print(f'sql1={sellEntitys_pkList.query}')
    print(f'sql2={sellEntitysUsers.query}')
    print(f'sellEntitysUsers={sellEntitysUsers}')

    exists = ServInfoMailSets.objects.filter(buyEntity=buyEntity).exists()
    if exists:
      mailSets =ServInfoMailSets.objects.get(buyEntity=buyEntity)
      repeatOnOff = mailSets.repeatOnOff
    
    if exists == True and repeatOnOff == 'on':
      startDate = mailSets.startDate
      interval = mailSets.interval
      dayOfMonth = mailSets.dayOfMonth
      print(f'pass0-1 interval={interval} def get in SevInfoMailSetsView')

    else:

      """ ①モデル未設定、または②「repaeaOnOff=='off'」の場合 """

      today = datetime.date.today()
      if today.day < 10:
        startDate = datetime.date(today.year, today.month, 10).strftime('%Y/%m/%d')
      elif today.day <20:
        startDate = datetime.date(today.year, today.month, 20).strftime('%Y/%m/%d')
      elif today.day < calendar.monthrange(today.year, today.month)[1]:
        startDate = calendar.monthrange(today.year, today.month)[1]
      else:
        startDate = datetime.date(today.year, today.month+1 , 10).strftime('%Y/%m/%d')       

      interval = 2; dayOfMonth = 1

      print(f'pass0-2 buyEntity.id={buyEntity.id} interval={interval} def get in SevInfoMailSetsView')

    init_data = {
      'startDate':startDate,
      'interval':interval,
      'dayOfMonth':dayOfMonth}
    print(f'init_data={init_data}')

    context = {
      'buyUser': buyUser,
      'buyEntity': buyEntity,
      'sellEntitysUsers': sellEntitysUsers,
      'mailForm1': ServInfoMailContentForm(),  # 
      'mailForm2': ServInfoMailContentForm(),  # 使っていない

      'repeatOnOff': repeatOnOff,
      'RepeatSetForm': RepeatSetForm(initial=init_data),
    }
    return TemplateResponse(request, 'send/servInfoMailSets.html', context)


  def post(self, request, *args):

    next2 = self.request.POST.get('next2', None)

    if next2 != None:

      if next2.find("ToSendNow") >= 0:

        print(f'pass1 def post if "ToSendNow" in SevInfoMailSetsView')

        buyUser = UserModel.objects.get(pk=next2.split('_')[1])
        buyEntity = LegalEntity.objects.get(pk=next2.split('_')[2])

        sellEntitys_pkList = QpayTx.objects.select_related('buyEntity').filter(buyEntity=buyEntity).order_by('-created_at').values_list('sellEntity')
        sellEntitysUsers = UserModel.objects.select_related('entity').filter(entity__pk__in=sellEntitys_pkList).values('userName','email','entity__entityName')

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
        buyUser = UserModel.objects.get(pk=next2.split('_')[1])
        buyEntity = LegalEntity.objects.get(pk=next2.split('_')[2])

        """  定期配信の設定を更新（EntityCreateViewで初期設定済み） """
        #mailSets = ServInfoMailSets.objects.create(
        #  startDate=startDate, interval=interval, dayOfMonth=dayOfMonth)

        print(f'buyUser={buyUser.id} buyEntity={buyEntity.id} def post if "ToSaveSendSets" in SevInfoMailSetsView')

        print(f'pass2-0 def post if "ToSaveSendSets" in SevInfoMailSetsView')          
        repeatOnOff= self.request.POST.get("name_RepeatOnOff", None)
        print(f'pass2-1 repeatOnOff={repeatOnOff} def post if "ToSaveSendSets" in SevInfoMailSetsView')


        if repeatOnOff == 'on':

          print(f'pass2-3 def post if "ToSaveSendSets" in SevInfoMailSetsView')

          # 初回設定（既存データなし）と設定更新（既存データあり）に分ける
          try:
            mailSets =ServInfoMailSets.objects.get(buyEntity=buyEntity)
          except:
            # EntityCreateView_sellerでモデル生成しているので基本ここは通らない
            mailSets =ServInfoMailSets.objects.create()
            mailSets.buyEntity = buyEntity

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

          self.buyUser_id = buyUser.pk
          self.buyEntity_id = buyEntity.pk

          sellEntitys_pkList = QpayTx.objects.select_related('buyEntity').filter(buyEntity=buyEntity).order_by('-created_at').values_list('sellEntity')
          # 関係しているゲストのpk（複数）を取得
    
          sellEntitysUsers = UserModel.objects.select_related('entity').filter(entity__pk__in=sellEntitys_pkList).values('userName','email','entity__entityName')
          # 関係しているゲストのユーザー（複数）を取得

          try:
            mailSets =ServInfoMailSets.objects.get(buyEntity=buyEntity)
          except:
            # EntityCreateView_sellerでモデル生成しているので基本ここは通らない
            mailSets =ServInfoMailSets.objects.create()
            mailSets.buyEntity = buyEntity

          mailSets.repeatOnOff = repeatOnOff
          
          today = datetime.date.today()
          if today.day < 10:
            startDate = datetime.date(today.year, today.month, 10).strftime('%Y/%m/%d')
          elif today.day <20:
            startDate = datetime.date(today.year, today.month, 20).strftime('%Y/%m/%d')
          elif today.day < calendar.monthrange(today.year, today.month)[1]:
            startDate = calendar.monthrange(today.year, today.month)[1]
          else:
            startDate = datetime.date(today.year, today.month+1 , 10).strftime('%Y/%m/%d')       

          #interval = 2; dayOfMonth = 1 #デフォルトで設定しているので不要
    
          mailSets.save()

          init_data = {
            'startDate':startDate,
            'interval':2,
            'dayOfMonth':1,
          }
          print(f'pass3-1 init_data={init_data} startDate={startDate}')

          context = {
            'buyUser': buyUser,
            'buyEntity': buyEntity,
            'sellEntitysUsers': sellEntitysUsers,
            'mailForm1': ServInfoMailContentForm(),  # 
            'mailForm2': ServInfoMailContentForm(),  # 使っていない

            'repeatOnOff': repeatOnOff,
            'RepeatSetForm': RepeatSetForm(initial=init_data),
          }
        
          print(f'pass3-3')

          return TemplateResponse(self.request, 'send/servInfoMailSets.html', context)
        

    """ 個別入力されたアドレスについてメール送信し、ログを取る """
    btnValue = self.request.POST.get('name_fixAddrBtn', None)

    if btnValue != None:

      print(f'pass3 btnValue={btnValue} def post in SevInfoMailSetsView')

      buyUser = UserModel.objects.get(pk=btnValue.split('_')[0])
      buyEntity = LegalEntity.objects.get(pk=btnValue.split('_')[1])

      print(f'buyUser={buyUser.id} buyEntity={buyEntity.id} def post in SevInfoMailSetsView')

      log = ServInfoMailLog.objects.create()
      log.buyEntity = buyEntity
      log.sendUser = buyUser
      log.sendList.clear()

       # 入力されたアドレスに送付

      # 送付先のログ作成
      i = 1
      while True:
        address = self.request.POST.get("name_ItemInput_" + str(i), None)
        print(f'pass4 name={"name_ItemInput_"+ str(i)} def post in SevInfoMailSetsView')
        print(f'pass4 addresss={address} def post in SevInfoMailSetsView')

        if address != None:
          log.sendList[str(i)] = address
        else:
          break
        i += 1

      print(f'pass5 log.sendList={log.sendList}def post in SevInfoMailSetsView')

      log.save()

      context = {}
      return TemplateResponse(self.request, 'accounts/buyer/mypage.html', context)


    next1 = self.request.POST.get('next1', None)

    if next1 != None:

      if next1.find('ToExportCSV') >=0 :

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="users.csv"'
        writer = csv.writer(response)
        writer.writerow(['名前', 'メールアドレス'])

        entity = LegalEntity.objects.get(email=request.user)
        entityUsers = entity.entity_users.all()

        for user in entityUsers():
          writer.writerow([user.userName, user.email])
        
        return response

      if next1.find('ToImportCSV') >= 0:

        form = CSVUploadForm(request.POST, request.FILES)
        if form.is_valid():

          data = request.FILES['file'].read().decode('utf-8')
          reader = csv.reader(io.StringIO(data))
          preview_data = [row for row in reader if row]
          request.session['csv_data'] = preview_data
          return TemplateResponse(request, 'send/import_preview.html', {'rows': preview_data})
        
        return TemplateResponse(request, 'send/import_csv.html', {'form': form})

      return HttpResponseBadRequest()  # 基本的にはここには来ない


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
