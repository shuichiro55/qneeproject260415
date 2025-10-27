import csv
import io
from django.shortcuts import redirect, render
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render
from django.contrib.auth import get_user_model
from django.views import generic
from qpay.models import QpayTx
from accounts.models import LegalEntity

from django.urls import reverse, reverse_lazy
#from django.utils import timezone
from django.http import HttpResponse, HttpResponseBadRequest #, HttpResponseRedirect
from django.template.response import TemplateResponse


#from django.contrib import messages
#from django.core.paginator import Paginator
#from django.core.mail import EmailMessage

#from .forms import CSVUploadForm, UserEntryForm #edited by s.tomihari 251010
from .form import MailForm, CSVUploadForm, UserEntryForm

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
    sellEntitysUsers = UserModel.objects.select_related('entity').filter(entity__pk__in=sellEntitys_pkList).values('userName','email','entity__entityName')

    # 上記のクエリーのアウトプットを確認したうえで項目を絞る
    # .values('id','customuser_id','customuser__userName','customuser__email')
    # https://yk5656.hatenablog.com/entry/20210410/1617980400
    # 「yuki5656 diary Djangoでデータを取得してみる(外部キー) Authorモデル側」を参考
    # 【コメント：prefetch_relatedは、「」多モデル側（customuser）側から隠せ巣親モデル（Foreignkeyの参照先モデル）から取得する場合のコードを参考】

    # SQL確認用コード
    print(f'sql1={sellEntitys_pkList.query}')
    print(f'sql2={sellEntitysUsers.query}')
    print(f'sellEntitysUsers={sellEntitysUsers}')

    context = {
      'buyUser': buyUser,
      'buyEntity': buyEntity,
      'sellEntitysUsers': sellEntitysUsers,
      'mailForm1': MailForm(),
      'mailForm2': MailForm(),
    }
    return TemplateResponse(request, 'send/servInfoMailSets.html', context)


  def post(self, request, *args):

    next1 = self.request.POST.get('next1', None)

    if next1 != None:

      print(f'self.buyUser_id={self.buyUser_id}')

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
