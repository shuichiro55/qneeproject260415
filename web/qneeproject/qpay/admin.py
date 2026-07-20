from django.contrib import admin
from .models import QpayTx, SendbackInfo

class QpayTxAdmin(admin.ModelAdmin):
  list_display = (
    'sellEntityname',
    'buyEntityname',
    'requested_amount',
    'requested_at',
    'approved_at'
  )

class SendbackInfoAdmin(admin.ModelAdmin):
  list_display = (
    'qpaytx',
    'created_at',
    'type1_frWho',
    'reason',
    'message'
  )

admin.site.register(QpayTx, QpayTxAdmin)
admin.site.register(SendbackInfo, SendbackInfoAdmin)