from django.db import models
from accounts.models import CustomUser, LegalEntity
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class ServInfoMailList(models.Model):

  sndUser = models.ForeignKey(CustomUser,
    verbose_name='ユーザー（発信側）',
    null=True, blank=True, default=None,
    on_delete=models.CASCADE,
    related_name='list_sndUsers')

  rcvUser = models.ForeignKey(CustomUser,
    verbose_name='ユーザー（受信側）',
    null=True, blank=True, default=None,
    on_delete=models.CASCADE,    
    related_name='list_rcvUsers')

  sndEntity = models.ForeignKey(LegalEntity,
    verbose_name='取引主体（発信側）',
    null=True, blank=True, default=None,
    on_delete=models.CASCADE,
    related_name='list_sndEntitys')

  rcvEntity = models.ForeignKey(LegalEntity,
    verbose_name='取引主体（受信側）',
    null=True, blank=True, default=None,
    on_delete=models.CASCADE,
    related_name='list_rcvEntitys')

  sent_at = models.DateTimeField(_('送信日時'), default=timezone.now,)
