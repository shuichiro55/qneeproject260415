from django.contrib import admin
from .models import CustomUser
from .models import LegalEntity
from .models import BankAccount

class CustomerUserAdmin(admin.ModelAdmin):
  list_display = ('username', 'type1', 'type2', 'personname', 'entityname')


class LegalEntityAdmin(admin.ModelAdmin):
  list_display = ('entityname', 'type1', 'personname', 'tel', 'email')

class BankAccountAdmin(admin.ModelAdmin):
  list_display = ('entity_id', 'holdername', 'bank_name', 'branch_name')

admin.site.register(CustomUser, CustomerUserAdmin)
admin.site.register(LegalEntity, LegalEntityAdmin)
admin.site.register(BankAccount, BankAccountAdmin)
