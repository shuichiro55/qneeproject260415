from django.contrib import admin
from .models import CustomUser
from .models import LegalEntity
from .models import BankAccount

class CustomerUserAdmin(admin.ModelAdmin):
  list_display = ('personname', 'type1', 'type2',)


class LegalEntityAdmin(admin.ModelAdmin):
  list_display = ('type1', 'type2', 'entityname', 'representitive', )

class UserEntityRelationAdmin(admin.ModelAdmin):
  list_display = ('personname', 'entityname', 'email')

class BankAccountAdmin(admin.ModelAdmin):
  list_display = ('entity_id', 'holdername', 'BankName', 'BranchName')

admin.site.register(CustomUser, CustomerUserAdmin)
admin.site.register(LegalEntity, LegalEntityAdmin)
admin.site.register(BankAccount, BankAccountAdmin)
