from django.contrib.auth import get_user_model
from django.db import models
from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.contrib.auth.models import PermissionsMixin, UserManager
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.core.validators import RegexValidator
from django.core.mail import send_mail

#from django.contrib.auth.models import AbstractUser
#from django.contrib.auth.validators import ASCIIUsernameValidator

name_validator = UnicodeUsernameValidator()
tel_regex = RegexValidator(regex=r'^[0-9０-９ー―－‐₋⁻-]+$', message = ("数字のみご入力下さい（最大15桁）　例：09012345678."))
zip_regex = RegexValidator(regex=r'^[0-9０-９]{7}+$', message = ("7桁の数字のみご入力ください　例: '1234567'"))
  #「 \d → 任意の数字	[0-9]」 「 ^ → 文字列の先頭」、「 $ → 文字列の末尾」
  #取引主体が個人の場合に住所を入れるか検討（選択肢は①入力しない、②郵便番号まで、③全部入力）

class BankAccount(models.Model):

  holderName =  models.CharField(
    '口座名義', max_length=100,
    unique=False, null=False, blank=False, default="",
  )

  entity_id = models.IntegerField('エンティティID', null=False, blank=True, default=0)

  bankCode =  models.CharField('金融機関コード', max_length=4, null=False, blank=False)
  bankName =  models.CharField('金融機関名', max_length=25, null=False, blank=False, default="")

  branchCode = models.CharField('支店コード', max_length=3, null=False, blank=False, default="")
  branchName = models.CharField('支店名', max_length=25, null=False, blank=False, default="")

  accountNumber_regex = RegexValidator(regex=r'^[0-9]+$', message = _("口座番号は数字でご入力ください。ex '1234567'"))
  accountNumber = models.CharField('口座番号', max_length=10, null=False, blank=False, default="", validators=[accountNumber_regex])

  temporal_tx_id = models.IntegerField(_('取引ID'), null=False, blank=True, default=0)
  # 取引口座を設定していない取引がある場合に使う一時的な要素（ユーザーには見せない）


class LegalEntity(models.Model):

  choices1 = ((1, 'パートナー'), (2, 'ゲスト'))
  type1 = models.IntegerField(default=1, null=False, blank=True, choices=choices1) #ユーザーが入力しない想定

  choices2 = ((1, '個人（法人組織でない）'), (2, '法人'))
  type2 = models.IntegerField(default=1, null=False, blank=True, choices=choices2)

  #企業の場合の入力値、個人の場合はuser.nameが入る
  entityName = models.CharField(
    '取引主体名', max_length=100,
    unique=False, null=False, blank=False, default="",
    validators=[name_validator],)
    #error_messages={'unique':_("ご入力の名前は既に存在します。次のリストからお選び下さい。")},)

  representitive = models.CharField(
    '代表者名', max_length=100,
    unique=False, null=True, blank=True,
    validators=[name_validator],
    # error_messages={'unique': _("ご記載の名前は既に使われています")},
  )

  #######################################
  ##  以下は、個人も企業も入力必要な項目  ##
  #######################################

  tel_entity = models.CharField(_('電話番号'), max_length=30,
    null=False, blank=False, default="", validators=[tel_regex])

  #企業の場合、住所は全部入力する
  zip_entity = models.CharField(_('郵便番号'), max_length=15,
    null=False, blank=False, default="",validators=[zip_regex])

  address1 = models.CharField(_('都道府県・区市町村'),
    max_length=30,
    null=True)

  address2 = models.CharField(_('〇丁目〇番〇号'),
    max_length=20,
    null=True)

  address3 = models.CharField(_('建物・マンション名・部屋番号'),
    max_length=30,
    null=True)

  # 手数料は加盟企業（発注者）ごとに設定できるようにする
  advance_fee_rate = models.DecimalField(max_digits=11, decimal_places=10, default=0.06) # 立替手数料（Seller⇒Qnee）
  referral_fee_rate = models.DecimalField(max_digits=11, decimal_places=10, default=0.015) # 紹介手数料（Qnee⇒Buyer）

  # 前払い申請者の受領口座
  bankAccount = models.OneToOneField(BankAccount,
    null=True, verbose_name='振込口座', on_delete=models.PROTECT)
  bankAccount_flag = models.IntegerField(_('口座設定フラグ'), null=False, blank=False, default=0)
  # 0：設定なし、1：設定済み

  # パートナー規約、ゲスト規約の同意状況、同意日時
  membershipConsent_boolean = models.BooleanField(_('規約同意'),default=False)  
  membershipConsent_at = models.DateTimeField(
    _('規約同意の日時'), null=True, blank=True,)

  # 業務委託契約の同意状況、同意日時
  sourcingConsent_boolean = models.BooleanField(_('契約合意'),default=False)  
  sourcingConsent_at = models.DateTimeField(
    _('契約合意の日時'), null=True, blank=True,)

  # 会員登録した日時
  #joined_at = models.DateTimeField(_('登録日'), null=True, blank=True)

  def __str__(self):
    return f'{self.entityName}'

# email＋パスワードでログインするためにカスタマイズ
class CustomUserManager(UserManager):
  use_in_migrations = True

  def _create_user(self, email, password, **extra_fields):
  
    if not email:
      raise ValueError('The given email must be set')

    email = self.normalize_email(email)
    user = self.model(email=email, **extra_fields)
    user.set_password(password)
    user.save(using=self._db)
    return user

  def create_user(self, email, password=None, **extra_fields):
    extra_fields.setdefault('is_staff', False)
    extra_fields.setdefault('is_superuser', False)
    return self._create_user(email, password, **extra_fields)

  def create_superuser(self, email, password, **extra_fields):
    extra_fields.setdefault('is_staff', True)
    extra_fields.setdefault('is_active', True)
    extra_fields.setdefault('is_superuser', True)

    if extra_fields.get('is_staff') is not True:
      raise ValueError('Superuser must have is_staff=True.')

    if extra_fields.get('is_superuser') is not True:
      raise ValueError('Superuser must have is_superuser=True.')

    return self._create_user(email, password, **extra_fields)

""" パートナー、ゲストにおいて一人目の承認はエンティティの承認も含む """
class ApprovedStatus(models.IntegerChoices):
  """ 承認された参加者かを判定するフラグ """
  UNPROCCESSED = 1  # 未処理
  APPROVED = 2      # 承認済み
  DISAPPROVED = 3   # 否認済み


class CustomUser(AbstractBaseUser, PermissionsMixin):

  email = models.EmailField('メールアドレス',
    unique=True, blank=False, null=False)

  #firstName = models.CharField('名（First Name）',                                                       
  #  max_length=50,
  #  unique=False,
  #  null=False,
  #  blank=True,
  #  default="",
  #)
  #lastName = models.CharField('姓（Last Name）',
  #  max_length=50,
  #  unique=False,
  #  null=False,
  #  blank=True,
  #  default="",
  #)
  #firstName_kana = models.CharField('名のカナ（First Name）',                                                       
  #  max_length=50,
  #  unique=False,
  #  null=False,
  #  blank=True,
  #  default="",
  #)
  #lastName_kana = models.CharField('姓のカナ（Last Name）',
  #  max_length=50,
  #  unique=False,
  #  null=False,
  #  blank=True,
  #  default="",
  #)

  userName = models.CharField(
    _('お名前'),max_length=100,
    unique=False, null=True, blank=True, default="",
  )
  userName_kana = models.CharField(
    _('お名前（カナ）'), max_length=50,
    unique=False, null=False, blank=True, default="",
  )

  choice1 = ((0, ''), (1, 'パートナー'), (2, 'ゲスト'), (3, 'Qnee')) #内部管理用

  type1 = models.IntegerField('属性1',
    null=True, blank=True, choices=choice1)

  choice2 = ((0, ''),(1, '個人で利用'), (2, '会社でご利用'))
  type2 = models.IntegerField('属性2',
    null=False, blank=True, default=0, choices=choice2)

  tel_user = models.CharField(_('電話番号'),
    max_length=30, null=False, blank=False, default="", validators=[tel_regex])
  
  zip_user = models.CharField(_('郵便番号'),
    max_length=15, null=True, blank=True, default="", validators=[zip_regex])

  entity = models.ForeignKey(LegalEntity,
    verbose_name='取引主体',
    # through="UserEntityRelation",
    null=True, blank=True, default=None,
    on_delete=models.CASCADE,
    related_name='entity_users')


  department = models.CharField(
    _('部署名'), max_length=100,
    null=False, blank=True,  default="")   # Entityが法人の場合

  title = models.CharField(
    _('役職名'), max_length=100,
    null=False, blank=True, default="")  

  is_active = models.BooleanField(_('アクティブ'), default=False)   # 利用規約に同意した時点

  approvedStatus_int = models.IntegerField(choices=ApprovedStatus.choices,
    default=1, verbose_name='承認状況 No')
  approvedStatus_char = models.CharField(max_length=20, null=False, blank=False, default="承認待ち", verbose_name='承認状況')

  # 登録の経過を確認するためのフラグ
  #is_active1 = models.BooleanField(_('アクティブ1'), default=False)  # ユーザー仮登録完了後、メールからのアクセスで本登録開始
  #is_active2 = models.BooleanField(_('アクティブ2'), default=False)  # エンティティ参加（ユーザー追加の場合と新規エンティティ登録の場合がある）

  is_staff = models.BooleanField(_('staff status'), default=False)
  is_admin = models.BooleanField(default=False)

  canApprove_all = models.BooleanField(_('承認権限（全部）'), null=True, default=False)
  canApprove_add = models.BooleanField(_('承認権限（参加）'), null=True, default=False)
  # 各パートナー内、各ゲスト内においてユーザーを追加する際の権限

  canApprove_qpay = models.BooleanField(_('承認権限（Qpay）'), null=True, default=False)
  # ゲストであればQpayを申請内容を最終確認する権限
  # パートナーであればゲストからのQpayの申請を承認する権限 

  canReceive = models.BooleanField(_('メール受信'), null=True, default=True)
  # Qneeからのサービスの案内を受信可能か

  joined_at = models.DateTimeField(_('登録日'), default=timezone.now,)

  objects = CustomUserManager()

  EMAIL_FIELD = 'email'
  USERNAME_FIELD = 'email'  # ログイン認証やメール送信などで利用
  REQUIRED_FIELDS = [ ]     # ユーザー作成時の必須項目を入れる　既に必須項目を入れるとエラーに

  def clean(self):
    super().clean()
    self.email = self.__class__.objects.normalize_email(self.email)

  def email_user(self, subject, message, from_email=None, **kwargs):
      send_mail(subject, message, from_email, [self.email], **kwargs)

  @property
  def username(self):
    """username属性のゲッター
    他アプリケーションが、username属性にアクセスした場合に備えて定義
    メールアドレスを返す
    """
    return self.email

  def __str__(self):
    return f'{self.email}'
  

""" CustomUserとLegalentityの中間テーブル 25/06/08に追加 """

""" CustomUserのManyToManyFieldのthrough引数で指定することで、
ORMで自動生成される中間テーブルの代わりに利用することができる。
情報を追加することができる（email、tel）。 """

#class UserEntityRelation(models.Model):
#
#  user = models.ForeignKey("CustomUser", on_delete=models.CASCADE)  
#  name = models.CharField(
#    'お名前（個人）',
#    blank=False,
#    max_length=150,
#    unique=False,
#    null=False, )
#
#  entity = models.ForeignKey("LegalEntity", on_delete=models.CASCADE)
#  entityName = models.CharField(
#    '取引主体名',
#    max_length=150,
#    unique=False,
#    default="",
#    null=False,
#    blank=True,
#    validators=[name_validator],)
#    #error_messages={'unique':_("ご入力の名前は既に存在します。次のリストからお選び下さい。")},)
#
#  email = models.EmailField('メールアドレス', unique=True, blank=False, null=False)
#  tel_direct = models.CharField(_('電話番号'), max_length=30, default="", null=False, validators=[tel_regex])
#  #「 \d → 任意の数字	[0-9]」 「 ^ → 文字列の先頭」、「 $ → 文字列の末尾」
#
#  #######################################
#  ##  取引主体が法人の場合に入力する項目 **
#  #######################################
#  department = models.CharField(_('部署名'), max_length=150, default="", blank=True, null=False)   # Entityが法人の場合
#  title = models.CharField(_('役職名'), max_length=150, default="", blank=True, null=False)        # Entityが法人の場合
