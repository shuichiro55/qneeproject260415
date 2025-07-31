from django.contrib import admin
from .models import QpayTx

class QpayTxAdmin(admin.ModelAdmin):
  list_display = ('sellEntityname', 'buyEntityname', 'requested_amount', 'requested_at', 'approved_at')

admin.site.register(QpayTx, QpayTxAdmin)