from django.contrib.auth import get_user_model
from django.db import models
from accounts.models import CustomUser, LegalEntity
##from accounts.models import LegalEntity
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.core.validators import FileExtensionValidator
import os
import datetime

usermodel = get_user_model()
  
def user_directory_path(instance, filename):
  dateTime = datetime.datetime.now()  # 現在の時刻を取得
  date_dir = datetime.datetime.now().strftime('%Y%m%d_%H-%M-%S')  # 年/月/日のフォーマットの作成
  time_stamp = datetime.datetime.now().strftime('%H-%M-%S_')  # 時-分-秒のフォーマットを作成
  new_filename = time_stamp + filename  # 実際のファイル名と結合
  user_directory = os.path.join(date_dir, new_filename)  # 階層構造にする
  #le = LegalEntity.objects.get(pk=instance.sellerEntity_id)
  print(f'instance.sellerEntity_id={instance.sellEntity_id} in qpay, models.py, user_directory_path')
  return "upload/entity{0}_tx{1}/{2}".format(instance.sellEntity_id, instance.id, user_directory)

class TxStatus(models.IntegerChoices):
  """ 状態 """
  UNPROCESSED = 1 # 未処理
  BUYER_PENDING = 2 # 申請差戻
  BUYER_APPROVED = 3    # 承認
  QNEE_PENDING = 4 # 申請差戻
  QNEE_PAYED = 5  # 前払済（Qnee⇒Seller）
  BUYER_PAYED = 6 # 取引完了：パートナーからQneeに送金済み

  BUYER_DISAPPROVED = -3 # 否認
  QNEE_DISAPPROVED = -5  # 前払謝絶

  
class QpayTx(models.Model):

  sellEntity = models.ForeignKey(LegalEntity, verbose_name='ゲスト・エンティティ',
    null=False,
    related_name='sellEntity_txs',
    on_delete=models.CASCADE)

  sellEntityName = models.CharField('ゲスト・エンティティ名', max_length=150, unique=False, null=False, blank=True)
  # sellerEntity_id = models.IntegerField('ゲスト・エンティティID', null=False, blank=False, )

  sellUser = models.ForeignKey(CustomUser, verbose_name='ゲスト・ユーザー',
    null=False,
    related_name='sellUser_txs', on_delete=models.CASCADE)

  sellUser_userName =models.CharField('ゲスト・ユーザー名', max_length=150, unique=False, null=False,)
  # sellerUser_id = models.IntegerField('ゲストID', null=False, blank=False, )
  # sellUser_email = models.EmailField('ゲスト・メールアドレス', unique=False, null=False, blank=False,)

  buyEntity = models.ForeignKey(LegalEntity, verbose_name='パートナー・エンティティ',
    null=False,
    related_name='buyEntity_txs',
    on_delete=models.CASCADE)

  # !! 初期値は「""」とし、値がセットされているかを判定できるようにする.
  buyEntityName = models.CharField('パートナー・エンティティ名', max_length=150,
    unique=False,
    null=False,
    blank=True,
    default="")
  #buyer_entity_choice = models.IntegerField(_('パートナー・エンティティ（選択リスト）'), choices=[(idx, f) for idx, f in enumerate(LegalEntity.objects.filter(type1=1).values_list('entityName', flat=True), 1)], default=1)
  #buyEntity_choice = models.IntegerField(_('お支払者'), default=1)

  """ buyUserは、最後に承認・否認した人を登録するようにする """
  buyUser = models.ForeignKey(CustomUser, verbose_name='パートナー・ユーザー',
    null=True,
    related_name='buyUser_txs',
    on_delete=models.CASCADE)

  buyUser_userName =models.CharField('ゲスト・ユーザー名', max_length=150, unique=False, null=True,)

  created_at = models.DateTimeField(_('データ作成時点'), default=timezone.now)
  requested_at = models.DateTimeField(_('ご申請時点'), null=True)
  requested_amount = models.IntegerField(_('ご申請金額（円）'), null=False)
  exPayment_date = models.DateField(_('当初報酬日'), null=True)


  evidence = models.FileField(
    _('ご報酬の証明（請求書など）'),
    upload_to = user_directory_path , 
    validators=[FileExtensionValidator(['jpg', 'png', 'jpeg', 'pdf', ])], null=True, default=None) 

  txStatus_int = models.IntegerField(choices=TxStatus.choices, default=1, verbose_name='処理状況 No')
  txStatus_char = models.CharField(max_length=20, null=False, blank=False, default="未処理", verbose_name='処理状況')
  
  # 1: UNPROCESSED 承認待ち
  # 2: APPROVED 承認済み（前払い未了）
  # 3: DISAPPROVED 否認済み
  # 4: QNEE_PAYED 前払い完了（Qnee⇒Seller）
  # 5: BUYER_PAYED Qnee受領（Buyer⇒Qnee）

  #applied_at = models.DateTimeField(_('申請時点'), null=True, blank=True)
  approved_at = models.DateTimeField(_('承認時点'), null=True, blank=True)
  approved_amount = models.IntegerField(_('承認金額（円）'), null=True)
  #advancePayment_date = models.DateField(_('前払日'), null=True)
  # advanced_atがあるの不要

  sendbacked_at = models.DateTimeField(_('差戻時点'), null=True, blank=True)
  rejected_at = models.DateTimeField(_('否認時点'), null=True, blank=True)
  #updated_at = models.DateTimeField(_('更新時点'), auto_now_add=True)

  """ 前払いに係る項目 """
  advanced_at = models.DateTimeField(_('前払い時点'), null=True, blank=True)
  advance_amount = models.IntegerField(_('前払い予定額'), null=False, default=0)
  advance_fee =  models.IntegerField(_('前払い手数料'), null=False, default=0)

  referral_fee =  models.IntegerField(_('ご報酬（紹介料）'), null=False, default=0)
  transfer_fee = models.IntegerField(_('振込手数料'), null=False, default=0)
  total_fee = models.IntegerField(_('合計手数料'), null=False, default=0)

  # transfer_amount =  models.IntegerField(_('送金額'), null=False, default=0)


  def save(self, *args, **kwargs):

    # !! コードが分かりずらいの出実際には使わない
    # ファイルパスにID（self.id）を含めるとき、
    # 初回モデル保存時にはIDが存在しないため、
    # モデルを一度保存した後に、データにファイルを格納して再度保存

    if self.id is None:
      uploaded_file = self.evidence # アップロードされたファイルを変数に代入しておく
      self.evidence = None          # 初回データ保存時はfileフィールドがnull（フォルダに保存せず）
      super().save(*args, **kwargs)
      print(f'pass1 self.evidence={self.evidence} in qpay.models.py, class QpayTx, save()')

      self.evidence = uploaded_file # fileフィールドに値をセット

      if "force_insert" in kwargs:
        kwargs.pop("force_insert")

    super().save(*args, **kwargs)
    # この段階ではインスタンスIDが存在するので、user_directory_path関数でinstance.idが使える

  def __str__(self):
    return f'{self.buyEntity}-{self.sellEntity}'