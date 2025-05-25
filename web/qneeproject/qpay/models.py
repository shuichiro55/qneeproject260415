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
  date_time = datetime.datetime.now()  # 現在の時刻を取得
  date_dir = date_time.strftime('%Y%m%d_%H-%M-%S')  # 年/月/日のフォーマットの作成
  time_stamp = date_time.strftime('%H-%M-%S')  # 時-分-秒のフォーマットを作成
  new_filename = time_stamp + filename  # 実際のファイル名と結合
  user_directory = os.path.join(date_dir, new_filename)  # 階層構造にする
  #le = LegalEntity.objects.get(pk=instance.seller_entity_id)
  print(f'instance.seller_entity_id={instance.seller_entity_id} in qpay, models.py, user_directory_path')
  return "upload/entity{0}_tx{1}/{2}".format(instance.seller_entity_id, instance.id, user_directory)

class TxStatus(models.IntegerChoices):
  """ 状態 """
  UNPROCESSED = 1 # 未処理
  APPROVED = 2    # 承認済み（前払い未了）
  DISAPPROVED = 3 # 否認済み
  QNEE_PAYED = 4  # 前払い完了（Qnee⇒Seller）
  BUYER_PAYED = 5 # Qnee受領（Buyer⇒Qnee）
  
class QpayTx(models.Model):

  # seller_personnameは、ユーザー名は表示する機会が多い中、seller_userからデータを取り出さなくてすむよう設定
  seller_user = models.ForeignKey(CustomUser, verbose_name='ゲスト・ユーザー', null=True, related_name='tx_sellerUser', on_delete=models.CASCADE)
  # seller_user_id = models.IntegerField('ゲストID', null=False, blank=False, )
  seller_user_email = models.EmailField('ゲスト・メールアドレス', unique=False, null=True, blank=False,)
  seller_user_personname =models.CharField('ゲスト・ユーザー名', max_length=150, unique=False, null=True,)

  seller_entity = models.ForeignKey(LegalEntity, verbose_name='ゲスト・エンティティ', null=True, related_name='tx_sellerEntity', on_delete=models.CASCADE)
  # seller_entity_id = models.IntegerField('ゲスト・エンティティID', null=False, blank=False, )
  seller_entityname = models.CharField('ゲスト・エンティティ名', max_length=150, unique=False, null=True, blank=True)
 
  # TxCreateFormで選択された後に入力される 
  buyer_user = models.ForeignKey(CustomUser, verbose_name='パートナー・ユーザー', null=True, related_name='tx_buyerUser', on_delete=models.CASCADE)

  ## 24/07/16
  ## 発注者のemail,personnameを固定しないように要修正か
  ## 処理しているユーザー及びそのアドレスを取得するためのメソッドを追加した方が
  buyer_email = models.EmailField('パートナー・メールアドレス', unique=False, blank=False, null=True)
  buyer_personname =models.CharField('パートナー・ユーザー名', max_length=150, unique=False, null=True,)

  buyer_entity = models.ForeignKey(LegalEntity, verbose_name='パートナー・エンティティ', default="", null=True, related_name='buyer_tx', on_delete=models.CASCADE)
  # !! 初期値は「""」とし、値がセットされているかを判定できるようにする.
  buyer_entityname = models.CharField('パートナー・エンティティ名', max_length=150, unique=False, default="", null=True, blank=True)
  #buyer_entity_choice = models.IntegerField(_('パートナー・エンティティ（選択リスト）'), choices=[(idx, f) for idx, f in enumerate(LegalEntity.objects.filter(type1=1).values_list('entityname', flat=True), 1)], default=1)
  buyer_entity_choice = models.IntegerField(_('お支払者'), default=1)

  requested_at = models.DateTimeField(_('ご申請時点'), default=None, null=True)
  requested_amount = models.IntegerField(_('ご申請金額（円）'), default=None, null=True)
  approved_amount = models.IntegerField(_('承認金額（円）'), default=None, null=True)
  original_payment_date = models.DateField(_('報酬日'), default=None, null=True)
  advanced_payment_date = models.DateField(_('前払日'), default=None, null=True)

  evidence = models.FileField(
    _('ご報酬の証明（請求書など）'),
    upload_to = user_directory_path , 
    validators=[FileExtensionValidator(['jpg', 'png', 'jpeg', 'pdf', ])], default=None, null=True) 

  tx_status_int = models.IntegerField(choices=TxStatus.choices, default=1, verbose_name='処理状況 No')
  tx_status_char = models.CharField(max_length=20, null=False, blank=False, default="承認待ち", verbose_name='処理状況')
  
  # 1: UNPROCESSED 承認待ち
  # 2: APPROVED 承認済み（前払い未了）
  # 3: DISAPPROVED 否認済み
  # 4: QNEE_PAYED 前払い完了（Qnee⇒Seller）
  # 5: BUYER_PAYED Qnee受領（Buyer⇒Qnee）

  created_at = models.DateTimeField(_('データ作成時点'), auto_now_add=True, blank=True, null=True)
  approved_at = models.DateTimeField(_('承認時点'), default=None, blank=True, null=True)
  rejected_at = models.DateTimeField(_('否認時点'), default=None, blank=True, null=True)
  updated_at = models.DateTimeField(_('更新時点'), auto_now=True)

  advance_amount = models.IntegerField(_('立替金額'), default=0)
  advance_fee =  models.IntegerField(_('立替手数料'), default=0)
  referral_fee =  models.IntegerField(_('ご報酬（紹介料）'), default=0)
  transfer_fee = models.IntegerField(_('振込手数料'), default=0)
  total_fee = models.IntegerField(_('合計手数料'), default=0)

  to_seller_amount =  models.IntegerField(_('振込金額'), default=0)


  def save(self, *args, **kwargs):

    if self.id is None:
      uploaded_file = self.evidence # アップロードされたファイルを変数に代入しておく
      self.evidence = None          # 一旦fileフィールドがNullの状態で保存(→インスタンスIDが割り当てられる)
      super().save(*args, **kwargs)
      print(f'ここ通る？self.evidence={self.evidence} in models.py, class QpayTx, save()')

      self.evidence = uploaded_file # fileフィールドに値をセット

      if "force_insert" in kwargs:
        kwargs.pop("force_insert")

    super().save(*args, **kwargs)
    # この段階ではインスタンスIDが存在するので、user_directory_path関数でinstance.idが使える

  def __str__(self):
    return f'{self.buyer_entity}-{self.seller_entity}'