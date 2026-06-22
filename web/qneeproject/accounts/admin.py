from django.contrib import admin
from .models import CustomUser
from .models import LegalEntity
from .models import BankAccount
from .models import CorpInfo

class CustomerUserAdmin(admin.ModelAdmin):
  #list_display = ('personname', 'type1', 'type2',)
  list_display = ('personname', 'type1', 'type2',)
  #pass

class LegalEntityAdmin(admin.ModelAdmin):
  list_display = ('type1', 'type2', 'entityname', 'representitive', )

class UserEntityRelationAdmin(admin.ModelAdmin):
  #list_display = ('personname', 'entityname', 'email')
  list_display = ('personname', 'entityname', 'email')

class BankAccountAdmin(admin.ModelAdmin):
  list_display = ('entity_id', 'holderName', 'bankName', 'branchName')

class CorpInfoAdmin(admin.ModelAdmin):
  list_display = ('entityname', 'status', 'created_at',)

admin.site.register(CustomUser, CustomerUserAdmin)
admin.site.register(LegalEntity, LegalEntityAdmin)
admin.site.register(BankAccount, BankAccountAdmin)
admin.site.register(CorpInfo, CorpInfoAdmin)