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

class BankAccount(models.Model):

  holdername =  models.CharField(
    '口座名義',
    max_length=150,
    unique=False,
    default="",
    null=True,
  )

  entity_id = models.IntegerField('エンティティID', default=0, null=True, blank=True)

  bank_code =  models.CharField('金融機関コード', max_length=4, null=True, blank=True)
  bank_name =  models.CharField('金融機関名', max_length=25, default=0, null=True, blank=True)

  branch_code = models.CharField('支店コード', max_length=3, null=True, blank=True)
  branch_name = models.CharField('支店名', max_length=25, default=0, null=True, blank=True)

  accountNumber_regex = RegexValidator(regex=r'^[0-9]+$', message = _("口座番号は数字でご入力ください。ex '1234567'"))
  accountNumber = models.CharField('口座番号', max_length=10, default=None, null=True, validators=[accountNumber_regex])

  temporal_tx_id = models.IntegerField(_('取引ID'), default=0, null=True, blank=True)
  # 取引口座を設定していない取引がある場合に使う一時的な要素（ユーザーには見せない）

class LegalEntity(models.Model):

  choices1 = ((1, 'パートナー'), (2, 'ゲスト'))
  type1 = models.IntegerField(default=1, null=False, blank=False, choices=choices1) #ユーザーが入力しない想定

  choices2 = ((1, '個人（法人組織でない）'), (2, '法人'))
  type2 = models.IntegerField(default=1, null=True, blank=True, choices=choices2)

  ################################
  ##  個人も企業も入力必要な項目  ##
  ################################
  personname_validator = UnicodeUsernameValidator()
  personname = models.CharField(
    '個人名', # 25/01/04 FirstNameとLastNameに分けるかは課題
    max_length=150,
    unique=False,
    default="",
    null=True,
    validators=[personname_validator],
    error_messages={'unique': _("A user with that username already exists")},
  )
  email = models.EmailField('メールアドレス', unique=True, blank=False, null=True)
  
  tel_regex = RegexValidator(regex=r'^[0-9０-９ー―－‐₋⁻-]+$', message = ("ハイフン「-」なしで数字のみご入力下さい（最大15桁）　例：09012345678."))
  tel = models.CharField(_('電話番号'), max_length=30, default="", null=False, validators=[tel_regex])
  #「 \d → 任意の数字	[0-9]」 「 ^ → 文字列の先頭」、「 $ → 文字列の末尾」

  #取引主体が個人の場合に住所を入れるか検討（選択肢は①入力しない、②郵便番号まで、③全部入力）
  postal_code_regex = RegexValidator(regex=r'^[0-9]+$', message = ("Postal Code must be entered in the format: '1234567'. Up to 7 digits allowed."))
  postal_code = models.CharField(_('郵便番号'), validators=[postal_code_regex], max_length=7)  

  #######################################
  ##  取引主体が法人の場合に入力する項目 **
  #######################################
  department = models.CharField(_('部署名'), max_length=150, default="", blank=True, null=True)  # CustomUserが企業の担当のとき
  title = models.CharField(_('役職名'), max_length=150, default="", blank=True, null=True)            # CustomUserが企業の担当のとき

  #企業の場合の入力値、個人の場合はpersonnameが入る
  entityname_validator = UnicodeUsernameValidator()
  entityname = models.CharField(
    '取引主体名',
    max_length=150,
    unique=False,
    default="",
    null=True,
    blank=True,
    validators=[entityname_validator],)
    #error_messages={'unique':_("ご入力の取引者は既に存在します。次のリストからお選び下さい。")},)

  #企業の場合、住所は全部入力する
  postal_code_regex = RegexValidator(regex=r'^[0-9]+$', message = _("Postal Code must be entered in the format: '1234567'. Up to 7 digits allowed."))
  postal_code = models.CharField(_('郵便番号'), max_length=7, default="", null=False, blank=True, validators=[postal_code_regex])

  # 手数料は加盟企業（発注者）ごとに設定できるようにする
  advance_fee_rate = models.DecimalField(max_digits=11, decimal_places=10, default=0.06) # 立替手数料（Seller⇒Qnee）
  referral_fee_rate = models.DecimalField(max_digits=11, decimal_places=10, default=0.015) # 紹介手数料（Qnee⇒Buyer）

  # 前払い申請者の受領口座
  bank_account = models.OneToOneField(BankAccount, verbose_name='振込口座', null=True, related_name='BankAccount_tx', on_delete=models.PROTECT)
  bank_account_flag = models.IntegerField(_('口座設定フラグ'), null=True, blank=True, default=0)
  # 0：設定なし、1：設定済み

  # パートナー規約、ゲスト規約の同意状況、同意日時
  is_consent_membership = models.BooleanField(_('規約同意'),default=False)  
  date_consent_membership = models.DateTimeField(_('規約同意の日時'), null=True, blank=True,)

  # 業務委託契約の同意状況、同意日時
  is_consent_outsource = models.BooleanField(_('契約合意'),default=False)  
  date_consent_outsource = models.DateTimeField(_('契約合意の日時'), null=True, blank=True,)

  # 会員登録した日時
  date_joined = models.DateTimeField(_('登録日'), null=True, blank=True, )

  def __str__(self):
    return f'{self.entityname}'

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


class CustomUser(AbstractBaseUser, PermissionsMixin):

  email = models.EmailField('メールアドレス', unique=True, blank=False, null=False)

  firstname = models.CharField(
    '名（First Name）',
    blank=False,
    max_length=150,
    unique=False,
    null=True,
  )
  lastname = models.CharField(
    '姓（Last Name）',
    blank=False,
    max_length=150,
    unique=False,
    null=True,
  )

  personname = models.CharField(
    'お名前（個人）',
    blank=False,
    max_length=150,
    unique=False,
    null=True,
  )

  choice1 = ((1, 'パートナー'), (2, 'ゲスト'), (3, 'Qnee')) #内部管理用
  type1 = models.IntegerField('属性1', default=1, null=True, blank=True, choices=choice1)

  choice2 = ((1, '個人（法人組織でない）'), (2, '法人'))
  type2 = models.IntegerField('属性2', null=True, blank=True, choices=choice2)

  entity = models.ForeignKey(LegalEntity, verbose_name='取引主体', null=True, related_name='user_entity', on_delete=models.CASCADE)
  # related_nameは、参照しているentity（親モデル）を参照するuser（子モデル）を抽出する場合に使う

  entityname = models.CharField(
    '取引主体',
    max_length=150,
    unique=False,
    null=True,
    blank=True,
  )
  # buyer_entity = models.ForeignKey(LegalEntity, verbose_name='発注者', null=True, related_name='user_buyerentity', on_delete=models.CASCADE)
  #（CustomUserが受注者の場合に）発注者を保存。受注者への案内時に発注者の情報を持たせるようにする
  # 発注者の情報は、①QRコードに発注者の情報を持たせる、②前払い申請の時に選択するようにした方がよいか、
  # なぜなら特定の受注者は、複数の発注先を持つ可能性がある。

  is_active = models.BooleanField(_('active'), default=False)
  is_staff = models.BooleanField(_('staff status'), default=False)
  is_admin = models.BooleanField(default=False)
  is_company = models.BooleanField(_('company'), default=False)

  date_joined = models.DateTimeField(_('登録日'), default=timezone.now,)

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