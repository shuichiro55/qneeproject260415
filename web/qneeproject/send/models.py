from django.db import models
from accounts.models import CustomUser, LegalEntity
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class ServInfoMailLog(models.Model):

  buyEntity = models.ForeignKey(LegalEntity,
    verbose_name='パートナー',
    null=True, blank=True, default=None,
    on_delete=models.CASCADE,
    related_name='list_sndEntitys')
  
  sendUser = models.ForeignKey(CustomUser,
    verbose_name='作成者',
    null=True, blank=True, default=None,
    on_delete=models.CASCADE,
    related_name='list_sndUsers')

  mailingList = models.JSONField(_('送信先'), null=True)
  #「 番号」「メールアドレス」「名前」の3つを保存する（3つ目はなくてもよい）
  # 送信する際に「null」の場合は、宛先を設定する必要があることをメッセージ

  created_at = models.DateTimeField(_('モデル生成日時'), default=timezone.now,)
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

class ServInfoMailSets(models.Model):

  buyEntity = models.OneToOneField(LegalEntity, 
    verbose_name='ゲスト・ユーザー',
    null=True,
    related_name='buyentity_users', on_delete=models.CASCADE)
  
  repeatOnOff = models.CharField(_("する・しない"), max_length=5, default='on')

  startDate = models.DateField(_("開始日"), null=True) # 定期配信の初回送信日
  interval  = models.IntegerField(_("間隔"), null=True, default=2) # 定期配信のインターバル
  dayOfMonth = models.IntegerField(_("月の〇日"), null=True, default=1) # 配信日を該当月の〇日とする

  json_sendMonth  = models.JSONField(verbose_name="配信月", null=True, default=getInitDict_sendMonth)
  # 1月に送る場合は「1:1」
  
  json_sendDay  = models.JSONField(verbose_name="配信日", null=True, default=getInitDict_sendDay)
  # 10日の場合は1:1、20日の場合は2:1、月末の場合は3:1
  
  exclusions = models.JSONField(verbose_name="除外アドレス", default=dict, null=True)

  #「登録済アドレス」を対象とする場合の除外するアドレスリスト

  # 更新された日
  updated_at = models.DateTimeField(_('更新日'), null=True, blank=True)
