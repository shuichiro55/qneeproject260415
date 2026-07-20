import csv
import io
from django.db.models import Q
from django.shortcuts import redirect, render
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render
from django.contrib.auth import get_user_model
from django.views import generic
from qpay.models import QpayTx
from accounts.models import LegalEntity
from send.models import InvitationSets, AddList, IndvAdd, InvitationLog

from django.urls import reverse, reverse_lazy
from django.http import HttpResponse, HttpResponseBadRequest #, HttpResponseRedirect
from django.template.response import TemplateResponse

from .form import AddFileUpForm, AddListNameForm
import openpyxl
from openpyxl.utils.exceptions import InvalidFileException

from django.contrib import messages
import json

from .form import AddListSelectForm, UserEntryForm, InvitationForm, RepeatSetForm
#from .form import CSVUploadForm, ImportExportForm #小原さん作成
#from django.http import JsonResponse

#from django.utils import timezone
#import calendar
#import datetime

#from dateutil.relativedelta import relativedelta
#from django.contrib import messages
#from django.core.paginator import Paginator
#from django.core.mail import EmailMessage

import datetime
import calendar

UserModel = get_user_model()


class InvitationSetsView(generic.UpdateView):

  # buyEntity_id = -1  get内で変更後、post内で値変わらず
   
  def get(self, request, *args, **kwargs):

    buyEntity_id = request.session.get('buyEntity_id', None)
    buyEntity = LegalEntity.objects.get(pk=buyEntity_id)

    " 適用中のアドレスリストがあるかを判定。判断結果によりパートナー側の処理フローが変わる"
    mailSets, created = InvitationSets.objects.select_related('appliedList').get_or_create(buyEntity=buyEntity)   
    mailSets.save()

    if mailSets.appliedList is not None:
      request.session['flag_appliedList'] = 1
      appliedList = AddList.objects.get(pk=mailSets.appliedList_id)
      request.session['nameOfAppliedList'] = appliedList.listName
    else:
      request.session['flag_appliedList'] = 0


    " 関係しているゲスト抽出（テンプレートに渡すため） "
    sellEntitys_pkList = QpayTx.objects.select_related('buyEntity').filter(buyEntity=buyEntity).order_by('-created_at').values_list('sellEntity')
    # 関係しているゲスト
    # values_list("name", "team", flat=False) ⇒nameとteamの複数指定は「flag=False」
    # <QuerySet [('山下', 'ファルコンズ'), ('瀬戸', 'タイガース'), ]
    # values("team")は、辞書型で取得{'team', 'ファルコンズ'}

    sellEntitysUsers = UserModel.objects.select_related('entity').filter(
      entity__pk__in=sellEntitys_pkList).values('personname','email','entity__entityname')
    # 関係しているゲストのユーザー（複数）を取得

    # 上記のクエリーのアウトプットを確認したうえで項目を絞る
    # .values('id','customuser_id','customuser__personname','customuser__email')
    # https://yk5656.hatenablog.com/entry/20210410/1617980400
    # 「yuki5656 diary Djangoでデータを取得してみる(外部キー) Authorモデル側」を参考
    # 【コメント：prefetch_relatedは、多モデル側（customuser）側から隠せ巣親モデル（Foreignkeyの参照先モデル）から取得する場合のコードを参考】

    # SQL確認用コード
    print(f'sql1={sellEntitys_pkList.query}')
    print(f'sql2={sellEntitysUsers.query}')
    print(f'sellEntitysUsers={sellEntitysUsers}')

    """ 260311 テンプレートで表示するためのデータ作成・セッションに保存 """
    self.makeListsData(buyEntity_id) # 260308に追加
    
    " フォームの「startDate」の初期値セット（保存しない） "
    if mailSets.startDate is not None:
      str_startDate = mailSets.startDate.strftime('%Y/%m/%d')
    else:
      str_startDate = self.nearStartDate()
    print(f'str_startDate={str_startDate} def get of InvitationSetsView')
    print(f'pass0-1 mailSets={mailSets} def get in SevInfoMailSetsView')

    request.session['flag_manualInput'] = 1 # テンプレートで入力画面を表示するフラグ
    
    init_data = {
      'startDate':str_startDate,
      'interval':mailSets.interval,
      'dayOfMonth':mailSets.dayOfMonth
    }
    print(f'init_data={init_data} def get of InvitationSetsView')

    context = {
      'addListSelectForm': AddListSelectForm(buyEntity_id=buyEntity_id),
      'step_fileUp': 1,
      'addFileUpForm': AddFileUpForm(),
      'addListNameForm1': AddListNameForm(),

      'flag_manualInput': 1,
      'addListNameForm2': AddListNameForm(),
      'mailForm': InvitationForm(),
      'repeatOnOff': mailSets.repeatOnOff,
      'RepeatSetForm': RepeatSetForm(initial=init_data),
    }
    return TemplateResponse(request, 'send/buyer/invitationSets.html', context)


  def nearStartDate(self):
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

  """ 260311 テンプレートで表示するためのデータ作成・セッションに保存 """
  def makeListsData(self, buyEntity_id):

    addLists = AddList.objects.select_related('buyEntity').filter(
      buyEntity__pk=buyEntity_id).order_by('-created_at')
    #request.session['addListNames'] = list(addLists.values_list('listName', flat=True))   
    #addListNames = request.session.get('addListNames')
    #print(f'addListNames={addListNames}')
    
    listsData = {} # 辞書型に設定
    for addList in addLists:
      indvAdds = IndvAdd.objects.filter(addList=addList) #.values_list('address', 'name')
    
      listsData[addList.listName] = [] # 辞書型の要素にリストを設定
      for indvAdd in indvAdds:
        listsData[addList.listName].append({'address':indvAdd.address, 'name': indvAdd.name})
    
      #print(f'listsData={listsData}')
    
    self.request.session['listsData'] = listsData
    self.request.session['json_listsData'] = json.dumps(listsData)


  def post(self, request, *args):

    buyUser_id = request.session.get('buyUser_id', None)
    buyEntity_id = request.session.get('buyEntity_id', None)
    print(f'buyEntity_id from session={buyEntity_id}')

    buyUser = UserModel.objects.get(pk=buyUser_id)
    buyEntity = LegalEntity.objects.get(pk=buyEntity_id)

    sellEntitys_pkList = QpayTx.objects.select_related('buyEntity').filter(
      buyEntity=buyEntity).order_by('-created_at').values_list('sellEntity')

    sellEntitysUsers = UserModel.objects.select_related('entity').filter(
      entity__pk__in=sellEntitys_pkList).values('personname','email','entity__entityname')

    mailSets = InvitationSets.objects.get(buyEntity=buyEntity)

    print(f'pass post1')
    nextWho_fileInput = self.request.POST.get('nextWho_fileInput', None) # 誰に送るかの対応
    nextWho_manualInput = self.request.POST.get('nextWho_manualInput', None) # 誰に送るかの対応
    nextWho_listApply = self.request.POST.get('nextWho_listApply', None) # 誰に送るかの対応

    nextWhen = self.request.POST.get('nextWhen', None) # 送信タイミングに係る対応
    nextWhat = self.request.POST.get('nextWhat', None) # 何を送るかの対応

    nextWho_MakeOrSelect = self.request.POST.get('nextWho_MakeOrSelect', None)

    if nextWho_MakeOrSelect != None:

      if nextWho_MakeOrSelect.find("make") >= 0:
        mailSets, created = InvitationSets.objects.select_related('appliedList').get_or_create(buyEntity=buyEntity)   
        mailSets.save()

        " フォームの「startDate」の初期値セット（保存しない） "
        if mailSets.startDate is not None:
          str_startDate = mailSets.startDate.strftime('%Y/%m/%d')
        else:
          str_startDate = self.nearStartDate()

        init_data = {
          'startDate':str_startDate,
          'interval':mailSets.interval,
          'dayOfMonth':mailSets.dayOfMonth
        }
        print(f'init_data={init_data} def get of InvitationSetsView')

        context = {
          'WhoWhenWhat':'who',
          'MakeOrSelect': 'make',          
          'FileOrManual':'',
          'FileType': '',

          'addListSelectForm': AddListSelectForm(buyEntity_id=buyEntity_id),
          'step_fileUp': 1,
          'addFileUpForm': AddFileUpForm(),
          'addListNameForm1': AddListNameForm(),

          'flag_manualInput': 1,
          'addListNameForm2': AddListNameForm(),
          'mailForm': InvitationForm(),
          'repeatOnOff': mailSets.repeatOnOff,
          'RepeatSetForm': RepeatSetForm(initial=init_data),
        }
        return TemplateResponse(request, 'send/buyer/invitationSets.html', context)


    if nextWho_fileInput != None:

      if nextWho_fileInput.find("ToUploadAddFile") >= 0:

        addList = AddList.objects.create(buyEntity=buyEntity)

        # 下記のコメントは、select_relatedを利用しているところに移す
        " select_relatedは、ForeignKey（外部キー）やOneToOneFieldの順方向参照 "
        " prefetch_relatedは、ManyToManyField、または逆方向のForeignKey "

        form = AddFileUpForm(request.POST, request.FILES)

        if form.is_valid():

          fileType = form.cleaned_data['fileType']
          addFile = form.cleaned_data['addFile'] # アップロードされたファイルをメモリ内で読み込む

          print(f'pass-6-4 ファイル読み込みプロセス')

          if fileType == "excel":

            # ★★ 260227 ファイルタイプが違う時のエラー処理を追加する！
            try:
              wb = openpyxl.load_workbook(addFile)
              sheet = wb.active # アクティブなシートを選択

              # 2行目から1行ずつループ（1行目がヘッダーと想定）
              # min_row=2 で開始行、max_col=2 で2項目目までを指定
              i = 0
              for row in sheet.iter_rows(min_row=2, max_col=2, values_only=True):
                i += 1
                address, name = row # 1行から2つの項目を取り出す
                print(f'add_id={str(i)}, address={address}, name={name}') 
                indvAdd = IndvAdd.objects.create(
                add_id=str(i), address=address, name=name)
                indvAdd.addList = addList
                indvAdd.save()

                " テンプレートに渡すためのデータ作成 "
                adds = IndvAdd.objects.filter(addList=addList)

              # ★★ 260223 前回の送信以降に作成したデータが消す（ウォーニングも出す）
              # ★★ 260223 読込用ファイルをダウンロードできるようにする

            except InvalidFileException:
              # ファイル形式が不正な場合の処理
              messages.add_message(request, messages.INFO,
                '対応していないファイル形式です。.xlsxまたは.xlsmファイルを指定してください。')


          elif fileType == "csv":

            # 260305に追加してエラー処理
            if not addFile.name.endswith('.csv') and addFile.content_type != 'text/csv':
              messages.error(request, 'CSVファイルのみアップロード可能です。')            

            try:
              data = addFile.read().decode('utf-8')
              # （補足）addFile.read(): バイナリデータ（bytes型）を読み込み
              # （補足）decode('utf-8')：読み込んだバイナリデータをUTF-8形式の文字列（str型）に変換

              reader = csv.reader(io.StringIO(data))
              #（補足） Pythonでメモリ上の文字列（CSV形式）をファイルのように扱い、csvモジュールで読み込む

              rows = [row for row in reader if row]
              #（補足）空行を除外し、全データをリストの変数に格納する

              print(f'rows={rows} def post if csv in InvitationSetsView')
              #request.session['rows_data'] = rows

            except csv.Error as e:
              # CSVのパースエラー
              messages.error(request, f"CSVファイルの読み込み中にエラーが発生しました: {e}")
            except Exception as e:
              messages.error(request, f"予期しないエラーが発生しました: {e}")

            i = 0
            for address, name in rows:
              if address.find('@') >= 0:
                i += 1
                indvAdd = IndvAdd.objects.create(
                  add_id=str(i), address=address, name= name)
                indvAdd.addList = addList
                indvAdd.save()

          else: # ファイルタイプの指定が正しくない場合
            messages.add_message(request, messages.WARNING, 'ファイルタイプを認識できません.')

        else:
          print(form.errors)  #「form.in_valid()==False」の場合

        """ 260311 テンプレートで表示するためのデータ作成・セッションに保存 """
        adds = IndvAdd.objects.filter(addList=addList)
        self.makeListsData(buyEntity_id) # 260308に追加
        print(f'adds={adds}')
        
        if mailSets.startDate is not None:
          str_startDate = mailSets.startDate.strftime('%Y/%m/%d')
        else:
          str_startDate =self.nearStartDate()

        print(f'pass 6-6 str_startDate={str_startDate}, mailSets.interval={mailSets.interval} mailSets.dayOfMonth={mailSets.dayOfMonth} def post in SevInfoMailSetsView')

        init_data = {
          'startDate':str_startDate,
          'interval':mailSets.interval,
          'dayOfMonth':mailSets.dayOfMonth}
        print(f'init_data2={init_data}')

        context = {
          'WhoWhenWhat':'who',
          'MakeOrSelect': 'make',          
          #'InputOrSelect':'input',
          'FileOrManual':'file',
          'FileType':fileType,

          'addListSelectForm': AddListSelectForm(buyEntity_id=buyEntity_id),
          'step_fileUp': 2,
          'adds':adds,
          'addFileUpForm': form,
          'addListNameForm1': AddListNameForm(
            initial={
              'listName':'addList_file_' + datetime.datetime.now().strftime('%y%m%d%H%M%S'),},),

          'flag_manualInput': 1,
          'addListNameForm2': AddListNameForm(),
          'mailForm': InvitationForm(),
          'repeatOnOff': mailSets.repeatOnOff,
          'RepeatSetForm': RepeatSetForm(initial=init_data),
        }
        return TemplateResponse(request, 'send/buyer/invitationSets.html', context)


      " ファイル入力で作成したアドレスリストを保存 "
      if nextWho_fileInput.find("ToSaveAddList") >= 0:

        form = AddListNameForm(self.request.POST, buyEntity_id=buyEntity_id)
        addList = AddList.objects.filter(
          buyEntity=buyEntity).order_by('-created_at').first()
        
        if form.is_valid():
          formError = 0
          listName = form.cleaned_data['listName']
          addList.listName = listName
          addList.save()

          # ★★ 260313 リストを適用するかは選べるようにし、選択肢によりメッセージを変える          
          # request.session['flag_appliedList'] = 1
          #messages.add_message(request, messages.SUCCESS,
          #  "リストが保存されました。作成したリストが選べるようになりました。")
        else:
          formError = 1

        """ 260311 テンプレートで表示するためのデータ作成・セッションに保存 """
        adds = IndvAdd.objects.filter(addList=addList)
        self.makeListsData(buyEntity_id) # 260308に追加

        if mailSets.startDate is not None:
          str_startDate = mailSets.startDate.strftime('%Y/%m/%d')
        else:
          str_startDate =self.nearStartDate()

        init_data = {
          'startDate':str_startDate,
          'interval':mailSets.interval,
          'dayOfMonth':mailSets.dayOfMonth}

        context = {
          'step_fileUp': 1 if formError==0 else 2,
          'WhoWhenWhat': 'who',
          'MakeOrSelect': 'make' if formError==0 else 'make',
          #'InputOrSelect':'' if formError==0 else 'input',
          'FileOrManual':'file' if formError==0 else 'file',
          'FileType':'' if formError==0 else self.request.POST.get('fileType'),
          'addListNameForm1': AddListNameForm() if formError==0 else form,
          'adds': '' if formError==0 else adds,

          'step_fileUp': 3,
          'addFileUpForm': AddFileUpForm(),
          'addListSelectForm': AddListSelectForm(buyEntity_id=buyEntity_id),
          'flag_manualInput': 1,
          'addListNameForm2': AddListNameForm(),
          'mailForm': InvitationForm(),
          'repeatOnOff': mailSets.repeatOnOff,
          'RepeatSetForm': RepeatSetForm(initial=init_data),
        }
        return TemplateResponse(request, 'send/buyer/invitationSets.html', context)


      print(f'pass fileup0 nextWho_fileInput={nextWho_fileInput}')
      if nextWho_fileInput.find("ToUploadAddListAgain") >= 0:
        print(f'pass fileup1')

        AddList.objects.filter(
          buyEntity=buyEntity).order_by('-created_at').first().delete()
        # models.pyで「on_delete = CASCADE」と設定してInvitationLogを削除する選択も

        if mailSets.startDate is not None:
          str_startDate = mailSets.startDate.strftime('%Y/%m/%d')
        else:
          str_startDate =self.nearStartDate()

        init_data = {
          'startDate':str_startDate,
          'interval':mailSets.interval,
          'dayOfMonth':mailSets.dayOfMonth}
        print(f'init_data={init_data}')

        context = {
          'step_fileUp': 1,
          'WhoWhenWhat':'who',
          'MakeOrSelect': 'make',
          #'InputOrSelect':'input',
          'FileOrManual':'file',
          'FileType':self.request.POST.get('fileType'),

          'addListSelectForm': AddListSelectForm(buyEntity_id=buyEntity_id),
          'addFileUpForm': AddFileUpForm(),
          'addListNameForm1': AddListNameForm(),

          'flag_manualInput': 1,
          'addListNameForm2': AddListNameForm(),
          'mailForm': InvitationForm(),
          'repeatOnOff': mailSets.repeatOnOff,
          'RepeatSetForm': RepeatSetForm(initial=init_data),
        }
        return TemplateResponse(request, 'send/buyer/invitationSets.html', context)


    """ 個別入力されたアドレスについてアドレスリストを作成する """
    # ★★ 260313 リストを保存する際に使用するリストとするか確認する
    if nextWho_manualInput != None:

      " 入力データを読み込んでアドレスリストを仮で保存 "
      if nextWho_manualInput.find("ToReadAddList") >= 0:

        addList = AddList.objects.create(buyEntity=buyEntity)
        addList.save()

        # 送付先のログ作成
        i = 0
        while True:
          i += 1
          address = self.request.POST.get("name_ItemInput_" + str(i), None)
          if address != None:

            # リスト名を指定できるようにする
            # {{add_id:'1', address:'富張', name:''},{add_id:'2', address:'安西', name:''}}の形式で保存
            indvAdd = IndvAdd.objects.create(
              add_id=str(i), address=address, name='')
            indvAdd.addList = addList
            indvAdd.save()

          else:
            break

        " テンプレートに渡すための処理 "
        adds = IndvAdd.objects.filter(addList=addList)

        for add in adds:
          print(f'add={add.address, add.name}')

        if mailSets.startDate is not None:
          str_startDate = mailSets.startDate.strftime('%Y/%m/%d')
        else:
          str_startDate =self.nearStartDate()

        init_data = {
          'startDate':str_startDate,
          'interval':mailSets.interval,
          'dayOfMonth':mailSets.dayOfMonth}
        print(f'init_data={init_data}')

        context = {
          'WhoWhenWhat':'who',
          'MakeOrSelect': 'make',
          #'InputOrSelect':'input',
          'FileOrManual': 'manual',

          'addListSelectForm': AddListSelectForm(buyEntity_id=buyEntity_id),
          'step_fileUp': 1,
          'addFileUpForm': AddFileUpForm(),
          'addListNameForm1': AddListNameForm(),

          'flag_manualInput': 2,
          'addListNameForm2': AddListNameForm(
            initial={
              'listName':'addList_manual_' + datetime.datetime.now().strftime('%y%m%d%H%M%S'),}),
          'adds': adds,
          'mailForm': InvitationForm(),
          'repeatOnOff': mailSets.repeatOnOff,
          'RepeatSetForm': RepeatSetForm(initial=init_data),
        }
        return TemplateResponse(request, 'send/buyer/invitationSets.html', context)


      " 手入力で作成したアドレスリストを保存 "
      " 仮で保存しているリストに、リスト名を加えて保存"

      print(f'nextWho_manuInput={nextWho_manualInput}')
      if nextWho_manualInput.find("ToSaveAddList") >= 0:
        print(f'pass manuInput saveList1')
        print(f'buyEntity_id={buyEntity_id}')
        
        form = AddListNameForm(self.request.POST, buyEntity_id=buyEntity_id)
        addList = AddList.objects.filter(
          buyEntity=buyEntity).order_by('-created_at').first()
        adds = IndvAdd.objects.filter(addList=addList) # テンプレートに渡すデータ

        if form.is_valid():
          formError = 0
          listName = form.cleaned_data['listName']
          addList.listName = listName
          addList.save()

          # ★★ 260313 リストを適用するかは選べるようにし、選択肢によりメッセージを変える          
          # request.session['flag_appliedList'] = 1
          #messages.add_message(request, messages.SUCCESS,
          #  "リストが保存されました。作成したリストが選べるようになりました。")
        else:
          formError = 1

        """ テンプレートで表示するためのデータ作成・セッションに保存 """
        adds = IndvAdd.objects.filter(addList=addList)
        self.makeListsData(buyEntity_id) # 260308に追加

        if mailSets.startDate is not None:
          str_startDate = mailSets.startDate.strftime('%Y/%m/%d')
        else:
          str_startDate =self.nearStartDate()
     
        init_data = {
          'startDate':str_startDate,
          'interval':mailSets.interval,
          'dayOfMonth':mailSets.dayOfMonth}
        
        context = {
          'WhoWhenWhat':'who',
          'MakeOrSelect': '' if formError==0 else 'make',
          #'InputOrSelect': '' if formError==0 else 'input',
          'FileOrManual': '' if formError==0 else 'manual', 
          'flag_manualInput': 1 if formError==0 else 2,
          'addListNameForm2': AddListNameForm()  if formError==0 else form,
          'adds': '' if formError==0 else adds,

          'FileType':'',
          'addListSelectForm': AddListSelectForm(buyEntity_id=buyEntity_id),
          'step_fileUp': 1,
          'addFileUpForm': AddFileUpForm(),
          'addListNameForm1': AddListNameForm(),

          'mailForm': InvitationForm(),
          'repeatOnOff': mailSets.repeatOnOff,
          'RepeatSetForm': RepeatSetForm(initial=init_data),
        }
        return TemplateResponse(request, 'send/buyer/invitationSets.html', context)


      if nextWho_manualInput.find("ToInputAddListAgain") >= 0:

        if AddList.objects.filter(buyEntity=buyEntity, listName=None).exists():
          AddList.objects.filter(
            buyEntity=buyEntity, listName=None).delete()
        # models.pyで「on_delete = CASCADE」と設定してInvitationLogを削除する選択も

        if mailSets.startDate is not None:
          str_startDate = mailSets.startDate.strftime('%Y/%m/%d')
        else:
          str_startDate =self.nearStartDate()

        init_data = {
          'startDate':str_startDate,
          'interval':mailSets.interval,
          'dayOfMonth':mailSets.dayOfMonth}
        print(f'init_data={init_data}')

        context = {
          'WhoWhenWhat':'who',
          'MakeOrSelect': 'make',
          #'InputOrSelect':'input',
          'FileOrManual':'manual',
          'FileType':'',

          'addListSelectForm': AddListSelectForm(buyEntity_id=buyEntity_id),
          'step_fileUp': 1,
          'addFileUpForm': AddFileUpForm(),
          'addListNameForm1': AddListNameForm(),

          'flag_manualInput': 1,
          'addListNameForm2': AddListNameForm(),
          'mailForm': InvitationForm(),
          'repeatOnOff': mailSets.repeatOnOff,
          'RepeatSetForm': RepeatSetForm(initial=init_data),
        }
        return TemplateResponse(request, 'send/buyer/invitationSets.html', context)


    if nextWhen != None:

      # ★★ 260410 適用中のリストのアドレスで送るように調整が必要
      # 今はDBに登録されているゲスト宛に送るだけ
      if nextWhen.find("ToSendToListMembersNow") >= 0:

        print(f'pass1 def post if "ToSendToListMembersNow" in SevInfoMailSetsView')

        InvitationAgtView.sendNow()
        return TemplateResponse(self.request, 'accounts/buyer/mypage.html', {})


      if nextWhen.find("ToSendToGuestsNow") >= 0:

        for sellUser in sellEntitysUsers:

          context = {
            'sellUser': sellUser,
            'buyEntity': buyEntity,
          }
          utils.sendEmail_common(
            'send/buyer/mail/invitation', '', [sellUser['email']], context)
  
          email = sellUser['email']
          print(f'pass1 sellUser.email={email}（InvitationSetsView, post)')

          return TemplateResponse(self.request, 'accounts/buyer/mypage.html', {})


      if nextWhen.find("ToSaveSendSets") >= 0:

        print(f'pass2 def post if "ToSaveSendSets" in SevInfoMailSetsView')

        """  定期配信の設定を更新（EntityCreateViewで初期設定済み） """
        #mailSets = InvitationSets.objects.create(
        #  startDate=startDate, interval=interval, dayOfMonth=dayOfMonth)

        repeatOnOff = self.request.POST.get("name_RepeatOnOff", None)

        if repeatOnOff == 'on':
          
          #mailSets.buyEntity = buyEntity
          mailSets.repeatOnOff = repeatOnOff

          str_startDate = self.request.POST.get("startDate", None)
          interval = int(self.request.POST.get("interval", None))
          dayOfMonth = int(self.request.POST.get("dayOfMonth", None))

          print(f'str_startDate={str_startDate}, interval={interval} def post repeatOnOff="on" in InvitationSetView')

          mailSets.startDate = datetime.date(
            int(str_startDate.split('/')[0]),
            int(str_startDate.split('/')[1]),
            int(str_startDate.split('/')[2]))
          mailSets.interval = interval
          mailSets.dayOfMonth = dayOfMonth

          month_startDate = int(str_startDate.split('/')[1])
          month_min = month_startDate % interval

          print(f'month_startDate={month_startDate}, month_min={month_min} in InvitationSetView')

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

          print(f'mailSets.json_sendMonth={mailSets.json_sendMonth}, mailSets.json_sendDay={mailSets.json_sendDay} in InvitationSetView')

          mailSets.save()

          messages.add_message(request,
            messages.SUCCESS, "QPAYご案内メールの送信設定を変更しました。")

          init_data = {
            'startDate': str_startDate,
            'interval': interval,
            'dayOfMonth': dayOfMonth,
          }

          context = {
            'WhoWhenWhat':'when',

            'sellEntitysUsers': sellEntitysUsers,

            'addListSelectForm': AddListSelectForm(buyEntity_id=buyEntity_id),
            'step_fileUp': 1,   
            'addFileUpForm': AddFileUpForm(),
            'addListNameForm1': AddListNameForm(),

            'flag_manualInput': 1,
            'addListNameForm2': AddListNameForm(),
            'mailForm': InvitationForm(), 

            'repeatOnOff': repeatOnOff,
            'RepeatSetForm': RepeatSetForm(initial=init_data),
          }
          return render(self.request, 'send/buyer/invitationSets.html', context)


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

            'addListSelectForm': AddListSelectForm(buyEntity_id=buyEntity_id),
            'step_fileUp': 1,   
            'addFileUpForm': AddFileUpForm(),
            'addListNameForm1': AddListNameForm(),

            'flag_manualInput': 1,
            'addListNameForm2': AddListNameForm(),
            'mailForm': InvitationForm(), 

            'repeatOnOff': repeatOnOff,
            'RepeatSetForm': RepeatSetForm(initial=init_data),
          }
          return TemplateResponse(self.request, 'send/buyer/invitationSets.html', context)
        
    """
    if nextWhen != None:

      if nextWhen.find("ToSendNow") >= 0:

        print(f'pass1 def post if "ToSendNow" in SevInfoMailSetsView')

        # ★★ 260305 選択されているアドレスリストのアドレスに送るようにする
        for sellUser in sellEntitysUsers:

          #★★ 251214 除外リストに該当するものは外す
          #★★ 251214 未登録ユーザー or 登録済みユーザーのどちらに送るか
          #★★ 251214 送信日について休日調整するか選択する機能を入れるか

          utils.sendEmail_common(
            'send/buyer/invitation', '', [sellUser.email], {})

          context = {}
          return TemplateResponse(self.request, 'accounts/buyer/mypage.html', context)
    """

    if nextWho_listApply != None:

      # ★★ 260305 指定されたリストを適用する
      if nextWho_listApply.find("ToApplyList") >= 0:

        #addListSelectForm = AddListSelectForm(self.request.POST, buyEntity_id=buyEntity_id)
        nameOfSelectedList = self.request.POST.get('name_ListOfListName')
        print(f'nameOfSelectedList={nameOfSelectedList}')
        if nameOfSelectedList == '適用なし':
          mailSets.appliedList = None
          request.session['nameOfAppliedList'] = None


        else:
          selectedList = AddList.objects.get(listName=nameOfSelectedList)
          mailSets.appliedList = selectedList
          print(f'nameofSelectedList={nameOfSelectedList}')
          print(f'selectedList.listNmae={selectedList.listName}')
          request.session['nameOfAppliedList'] = selectedList.listName

        mailSets.save()

        test = request.session.get('nameOfAppliedList')
        print(f'session.get(nameOfAppliedList)={test}')
        # ★★　260305 アドレスリストを作成するとき名前の重複を避ける

        if mailSets.startDate is not None:
          str_startDate = mailSets.startDate.strftime('%Y/%m/%d')
        else:
          str_startDate =self.nearStartDate()

        init_data = {
          'startDate':str_startDate,
          'interval':mailSets.interval,
          'dayOfMonth':mailSets.dayOfMonth}
        print(f'init_data={init_data}')

        context = {
          'WhoWhenWhat':'who',
          'MakeOrSelect':'select',

          'addListSelectForm': AddListSelectForm(
            buyEntity_id=buyEntity_id),
          'step_fileUp': 1,
          'addFileUpForm': AddFileUpForm(),
          'addListNameForm1': AddListNameForm(),

          'flag_manualInput': 1,
          'addListNameForm2': AddListNameForm(),
          'mailForm': InvitationForm(),
          'repeatOnOff': mailSets.repeatOnOff,
          'RepeatSetForm': RepeatSetForm(initial=init_data),
        }
        return TemplateResponse(request, 'send/buyer/invitationSets.html', context)


      # ★★ 260305 指定されたリストを適用する
      if nextWho_listApply.find("ToDeleteList") >= 0:

        #addListSelectForm = AddListSelectForm(self.request.POST, buyEntity_id=buyEntity_id)
        nameOfSelectedList = self.request.POST.get('name_ListOfListName')
        print(f'nameOfSelectedList={nameOfSelectedList}')

        if nameOfSelectedList != '適用なし':
          AddList.objects.filter(Q(listName=nameOfSelectedList) | Q(listName__isnull=True)).delete()

        """ 260311 テンプレートで表示するためのデータ作成・セッションに保存 """
        self.makeListsData(buyEntity_id) # 260308に追加
        
        # ★★　260305 アドレスリストを作成するとき名前の重複を避ける

        if mailSets.startDate is not None:
          str_startDate = mailSets.startDate.strftime('%Y/%m/%d')
        else:
          str_startDate =self.nearStartDate()

        init_data = {
          'startDate':str_startDate,
          'interval':mailSets.interval,
          'dayOfMonth':mailSets.dayOfMonth}
        print(f'init_data={init_data}')

        context = {
          'WhoWhenWhat':'who',
          'MakeOrSelect':'select',

          'addListSelectForm': AddListSelectForm(buyEntity_id=buyEntity_id),
          'step_fileUp': 1,
          'addFileUpForm': AddFileUpForm(),
          'addListNameForm1': AddListNameForm(),

          'flag_manualInput': 1,
          'addListNameForm2': AddListNameForm(),
          'mailForm': InvitationForm(),
          'repeatOnOff': mailSets.repeatOnOff,
          'RepeatSetForm': RepeatSetForm(initial=init_data),
        }
        return TemplateResponse(request, 'send/buyer/invitationSets.html', context)


    return TemplateResponse(request, 'send/buyer/invitationSets.html', {'addFileUpForm': AddFileUpForm()})



  
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
      #    writer.writerow([user.personname, user.email])
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
      return redirect('send/buyer/invitationSets.html')
  else:
    form = UserEntryForm()
  return TemplateResponse(request, 'send/buyer/register.html', {'form': form})


def import_csv(request):
  if request.method == 'POST':
    form = CSVUploadForm(request.POST, request.FILES)
    if form.is_valid():
      data = request.FILES['file'].read().decode('utf-8')
      reader = csv.reader(io.StringIO(data))
      preview_data = [row for row in reader if row]
      request.session['csv_data'] = preview_data
      return TemplateResponse(request, 'send/buyer/import_preview.html', {'rows': preview_data})
  else:
      form = CSVUploadForm()
  return TemplateResponse(request, 'send/buyer/import_csv.html', {'form': form})

def finalize_import(request):
  csv_data = request.session.pop('csv_data', [])
  for name, email in csv_data:
    LegalEntity.objects.get_or_create(personname=name, email=email)
  return redirect(reverse('send:invitationSets'))

def export_csv(self, request):
  response = HttpResponse(content_type='text/csv')
  response['Content-Disposition'] = 'attachment; filename="users.csv"'
  writer = csv.writer(response)
  writer.writerow(['名前', 'メールアドレス'])

  for user in LegalEntity.objects.all():
    writer.writerow([user.personname, user.email])
  return response


#from django.utils import timezone
from datetime import date

"""  """
class InvitationAgtView(LoginRequiredMixin, generic.UpdateView):

  login_url = '/accounts/login_admin/'
  def get(self, request, *args, **kwargs):
    context = {}
    return render(request, 'send/admin/invitationAgt.html', context)

  def applicableSendDate(self):
    return True

  def sendNow(request=None):
    " 260402 今日、いまから送る場合に呼ばれるメソッド "
    " 260402 このメソッドを呼ぶ時間を別の場所で管理する "

    invitationSets = InvitationSets.objects.select_related('appliedList').all()

    today = date.today
    addList  = []

    for eachSets in invitationSets:
      if today >= eachSets.startDate:

        if eachSets.json_sendMonth[today.month] == 1 and \
          eachSets.json_sendDay[today.day] == 1:

          # ★★　下記はまだテストが終わっていない
          addList = list(IndvAdd.objects.filter(addList=eachSets.appliedList).values_list('email', flat=True))
          utils.sendEmail_common('send/admin/mail/servInfo', '', addList, {})
    
    messages.add_message(request,
      messages.SUCCESS, "ゲストにサービス内容を案内するメールを送信しました。")
  

  def post(self, request, *args, **kwargs):

    next = self.request.POST.get('next', None)


    if next.find("ToExecuteForToday") >= 0:
      
      context2 = {}
      return render(request, 'send/admin/invitationAgt.html', context2)


    if next.find("ToStopAgent") >= 0:

      context = {}
      return render(request, 'accounts/admin/mypage.html', context)  

    context = {}
    return render(request, 'send/invitationAgt.html', context)  


from django.conf import settings
from django.template.loader import render_to_string
from django.core.mail import EmailMessage

class utils:

  def sendEmail_common(path, from_email, addList, context=None):

    #辞書型のデータにprotorolとdomainの情報を加える
    if context == None: context={}
    context['protocol'] = settings.PROTOCOL
    context['domain'] = settings.DOMAIN

    print(f'path={path}')
    subject = render_to_string(path + '_subject.txt', context)
    message = render_to_string(path + '_message.txt', context)

    # .email_user(subject, message)
    if from_email is None or from_email == '':
      from_email = settings.DEFAULT_FROM_EMAIL

    recipient_list = addList
    #bcc =  ["toritoritorina@gmail.com"]  # BCCリスト
    email = EmailMessage(subject, message, from_email, recipient_list)
    email.send()

    return True

