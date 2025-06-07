from django.contrib import admin
from .models import QpayTx

class QpayTxAdmin(admin.ModelAdmin):
  list_display = ('sellerEntity_entityname', 'buyerEntity_entityname', 'requested_amount', 'requested_at', 'approved_at')

admin.site.register(QpayTx, QpayTxAdmin)