from django.db import models
from accounts.models import CustomUser, LegalEntity
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class AddList(models.Model):

  listName = models.CharField(_('メルアドリスト名'),
    max_length=50, null=True, unique=True)
  
  buyEntity = models.ForeignKey(LegalEntity,
    verbose_name='パートナー',
    null=True, blank=True, default=None,
    on_delete=models.CASCADE)
  
  createUser = models.ForeignKey(CustomUser,
    verbose_name='作成者',
    null=True, blank=True, default=None,
    on_delete=models.CASCADE)

  created_at = models.DateTimeField(_('作成日時'), default=timezone.now)


" アドレスリストの個別アドレス情報を格納 "
class IndvAdd(models.Model):

  add_id = models.CharField(max_length=6) # リスト内での付番（pkと異なる）
  address = models.CharField(max_length=100, blank=True)
  name = models.CharField(max_length=50, blank=True)
  #repeat = models.BooleanField(default=True)
  #sent_at = models.DateTimeField(_('送信日時'), null=True)

  addList = models.ForeignKey(AddList, on_delete=models.CASCADE, null=True)


class InvitationLog(models.Model):

  buyEntity = models.ForeignKey(LegalEntity,
    verbose_name='パートナー',
    null=True, blank=True, default=None,
    on_delete=models.CASCADE)
  
  sendUser = models.ForeignKey(CustomUser,
    verbose_name='作成者',
    null=True, blank=True, default=None,
    on_delete=models.CASCADE)

  addList = models.ForeignKey(AddList,
    verbose_name='適用アドレスリスト',
    null=False, default=None,
    on_delete=models.CASCADE)
  
  created_at = models.DateTimeField(_('作成日時'), default=timezone.now)

  #mailingList = models.OneToOneField(_('送信先'), null=True)
  #「 番号」「メールアドレス」「名前」の3つを保存する（3つ目はなくてもよい）
  # 送信する際に「null」の場合は、宛先を設定する必要があることをメッセージ

  created_at = models.DateTimeField(_('モデル生成日時'), default=timezone.now, null=True)
  sent_at = models.DateTimeField(_('送信日時'), null=True)

  #recvEntity = models.ForeignKey(LegalEntity,
  #  verbose_name='取引主体（受信側）',
  #  null=True, blank=True, default=None,
  #  on_delete=models.CASCADE,
  #  related_name='list_rcvEntitys')

def getInitDict_sendMonth():
  return {'1':'1','2':'0',3:'1','4':'0','5':'1','6':'0','7':'1','8':'0','9':'1','10':'0','11':'1','12':'0'}
def getInitDict_sendDay():
  return {'1':'1','2':'0','3':'0'}

class InvitationSets(models.Model):

  buyEntity = models.OneToOneField(LegalEntity, 
    verbose_name='ゲスト・ユーザー',
    null=True,
    related_name='buyentity_users', on_delete=models.CASCADE)
  
  repeatOnOff = models.CharField(_("する・しない"), max_length=5, default='on')

  startDate = models.DateField(_("開始日"), null=True) # 定期配信の初回送信日
  interval  = models.IntegerField(_("間隔"), null=True, default=2) # 定期配信のインターバル
  dayOfMonth = models.IntegerField(_("月の〇日"), null=True, default=1) # 配信日を該当月の〇日とする

  json_sendMonth = models.JSONField(verbose_name="配信月", 
    default=getInitDict_sendMonth,
    null=True)
    # 1月に送る場合は「1:1」
  
  json_sendDay = models.JSONField(verbose_name="配信日",
    default= getInitDict_sendDay,
    null=True)
    # 10日の場合は1:1、20日の場合は2:1、月末の場合は3:1
  
  appliedList = models.ForeignKey(AddList, on_delete=models.SET_NULL, null=True)
  #exclusions = models.JSONField(verbose_name="除外アドレス", default=dict, null=True)

  #「登録済アドレス」を対象とする場合の除外するアドレスリスト

  # 作成日時
  created_at = models.DateTimeField(_('作成日時'), default=timezone.now)
  
  # 更新日時
  updated_at = models.DateTimeField(_('更新日'), 
    null=True, auto_now=True)
