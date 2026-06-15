from django.contrib import admin
from .models import CustomUser
from .models import LegalEntity
from .models import BankAccount
from .models import CorpInfo

class CustomerUserAdmin(admin.ModelAdmin):
  list_display = ('userName', 'type1', 'type2',)


class LegalEntityAdmin(admin.ModelAdmin):
  list_display = ('type1', 'type2', 'entityName', 'representitive', )

class UserEntityRelationAdmin(admin.ModelAdmin):
  list_display = ('userName', 'entityName', 'email')

class BankAccountAdmin(admin.ModelAdmin):
  list_display = ('entity_id', 'holderName', 'bankName', 'branchName')

class CorpInfoAdmin(admin.ModelAdmin):
  list_display = ('entityName', 'status', 'created_at',)

admin.site.register(CustomUser, CustomerUserAdmin)
admin.site.register(LegalEntity, LegalEntityAdmin)
admin.site.register(BankAccount, BankAccountAdmin)
admin.site.register(CorpInfo, CorpInfoAdmin)