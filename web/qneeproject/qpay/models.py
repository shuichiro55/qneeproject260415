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
  SELLER_DROPPED = -1     # 取下げ

  UNPROCESSED = 0         # 未処理
  UNDER_APPLICATION = 1   # 申請中
  BUYER_PENDING = 2       # 申請差戻
  BUYER_APPROVED = 3      # 承認
  QNEE_PENDING = 4        # 申請差戻
  QNEE_PAYED = 5          # 前払済（Qnee⇒Seller）
  BUYER_PAYED = 6         # 取引完了：パートナーからQneeに送金済み

  BUYER_DISAPPROVED = -3  # 否認
  QNEE_DISAPPROVED = -5   # 前払謝絶
  

class QpayTx(models.Model):

  sellEntity = models.ForeignKey(LegalEntity, verbose_name='ゲスト・エンティティ',
    null=False,
    related_name='sellEntity_txs',
    on_delete=models.CASCADE)

  sellEntityname = models.CharField('ゲスト・エンティティ名',
    max_length=150, unique=False, null=False, blank=True)

  sellUser = models.ForeignKey(CustomUser, verbose_name='ゲスト・ユーザー',
    null=False,
    related_name='sellUser_txs', on_delete=models.CASCADE)

  sellUser_personname = models.CharField('ゲスト・ユーザー名',
    max_length=150, unique=False, null=True, blank=True)

  buyEntity = models.ForeignKey(LegalEntity, verbose_name='パートナー・エンティティ',
    null=False,
    related_name='buyEntity_txs',
    on_delete=models.CASCADE)

  # !! 初期値は「""」とし、値がセットされているかを判定できるようにする.
  buyEntityname = models.CharField('パートナー・エンティティ名', max_length=150,
    unique=False,
    null=False,
    blank=True,
    default="")

  """ buyUserは、最後に承認・否認した人を登録するようにする """
  buyUser = models.ForeignKey(CustomUser, verbose_name='パートナー・ユーザー',
    null=True,
    related_name='buyUser_txs',
    on_delete=models.CASCADE)

  buyUser_personname =models.CharField('ゲスト・ユーザー名', max_length=150, unique=False, null=True,)

  created_at = models.DateTimeField(_('データ作成時点'), default=timezone.now)
  requested_at = models.DateTimeField(_('ご申請時点'), null=True)
  requested_amount = models.DecimalField(_('ご申請金額（円）'), max_digits=8, decimal_places=0, null=False)
  exPayment_date = models.DateField(_('当初報酬日'), null=True)


  evidence = models.FileField(
    _('ご報酬の証明（請求書など）'),
    upload_to = user_directory_path , 
    validators=[FileExtensionValidator(['jpg', 'png', 'jpeg', 'pdf', ])], null=True, default=None) 

  txStatus = models.IntegerField(choices=TxStatus.choices, default=0, verbose_name='処理状況 No')
  txStatus_char = models.CharField(max_length=20, null=False, blank=False, default="未処理", verbose_name='処理状況')
  
  #applied_at = models.DateTimeField(_('申請時点'), null=True, blank=True)
  approved_at = models.DateTimeField(_('承認時点'), null=True, blank=True)
  approved_amount = models.DecimalField(_('承認金額（円）'), max_digits=8, decimal_places=0, null=True, blank=True)
  #advancePayment_date = models.DateField(_('前払日'), null=True)
  # advanced_atがあるの不要
 
  rejected_at = models.DateTimeField(_('否認時点'), null=True, blank=True)
  #updated_at = models.DateTimeField(_('更新時点'), auto_now_add=True)

  """ 前払い決済に係る項目 """
  advanced_at = models.DateTimeField(_('前払い時点'), null=True, blank=True)
  advance_amount = models.DecimalField(_('前払い予定額'), max_digits=8, decimal_places=0, null=False, default=0)
  advance_fee =  models.DecimalField(_('前払い手数料'), max_digits=8, decimal_places=0, null=False, default=0)

  referral_fee =  models.DecimalField(_('ご報酬（紹介料）'), max_digits=8, decimal_places=0, null=False, default=0)
  transfer_fee = models.DecimalField(_('振込手数料'), max_digits=8, decimal_places=0, null=False, default=0)
  total_fee = models.DecimalField(_('合計手数料'), max_digits=8, decimal_places=0, null=False, default=0)

  transfer_amount =  models.DecimalField(_('送金額'), max_digits=8, decimal_places=0, null=False, default=0)

  # 最新の差戻情報へのリンク。
  # sendbackInfoからForeignkeyでの参照がある為、文字列で参照（循環回避）
  sendbackInfo_admin = models.OneToOneField('SendbackInfo',
    verbose_name='差戻情報（Qnee）',
    null=True, blank=True, on_delete=models.SET_NULL,
    related_name='adminSendbackInfo_qpaytx')

  sendbackInfo_buyer = models.OneToOneField('SendbackInfo',
    verbose_name='差戻情報（パートナー）',
    null=True, blank=True, on_delete=models.SET_NULL,
    related_name='buyerSendbackInfo_qpaytx')
  
  # 最新の会社情報更新の申請情報へのリンク。
  #   # sendbackInfoからForeignkeyでの参照がある為、文字列で参照（循環回避）
  clearingInfo = models.ForeignKey('ClearingInfo', verbose_name='最新清算リンク',
    null=True, blank=True, on_delete=models.SET_NULL, related_name='clearingInfo_qpaytx')
  

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
  

#class SendbackStatus(models.IntegerChoices):
#  " 状態 "
#  HISTORY = -1
#  AFTER_SENDBACK = 1  # 差戻中
#  AFTER_RESPONSE = 2  # 再申請後


class SendbackInfo(models.Model):

  qpaytx = models.ForeignKey(QpayTx, verbose_name='QPAY取引',
    null=True, blank=True, on_delete=models.CASCADE)
  
  created_at = models.DateTimeField(_('差戻時点'), null=True, blank=True)
  
  CHOICES = ((1, 'パートナー'), (3, 'Qnee'))
  type1_frWho = models.IntegerField(default=None, null=True, blank=True, choices=CHOICES)

  #status = models.IntegerField(
  #  choices=SendbackStatus.choices, default=1, verbose_name='処理状況 No')

  reason = models.CharField(
    '差戻理由', max_length=100,
    unique=False, null=True, blank=True,)

  message = models.TextField(
    'メッセージ', max_length=200,
    unique=False, null=True, blank=True,)  


class ClrStatus(models.IntegerChoices):
  """ 状態 """
  TBD = 1     # 未清算
  PENDING = 2 # 保留
  DONE = 3    # 清算済み

""" パートナーにおける前払い（Qnee立替分）の清算状況を管理 """
class ClearingInfo(models.Model):

  buyEntity = models.ForeignKey(LegalEntity,
    verbose_name='パートナー',
    null=True, blank=True, default=None,
    on_delete=models.CASCADE)

  advancedTerm_YYYYMM = models.CharField(
    '前払い年月', max_length=6, unique=False, null=True, blank=True,)
  
  status = models.IntegerField(
    '清算状況', choices=TxStatus.choices, default=1,)
  
  amount_toBeCleared = models.DecimalField(_('清算必要額（円）'), max_digits=8, decimal_places=0, null=True, default=0)
  # 清算必要額を格納する

  updated_at = models.DateTimeField(_('更新日'), null=True, default=None)
  cleared_at = models.DateTimeField(_('清算日'), null=True, default=None)
  # 清算（パートナー⇒Qnee）がなされた日を保存
