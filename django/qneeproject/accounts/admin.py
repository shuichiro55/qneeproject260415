from django.contrib import admin
from .models import CustomUser, LegalEntity

class CustomerUserAdmin(admin.ModelAdmin):
  list_display = ('username', 'type1', 'type2', 'personname', 'entityname')


class LegalEntityAdmin(admin.ModelAdmin):
  list_display = ('entityname', 'type1', 'personname', 'tel', 'email')

admin.site.register(CustomUser, CustomerUserAdmin)
admin.site.register(LegalEntity, LegalEntityAdmin)
