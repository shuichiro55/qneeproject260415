from django.contrib import admin
from .models import ServInfoMailSets, ServInfoMailLog, AddList

class ServInfoMailSetsAdmin(admin.ModelAdmin):
  list_display = (
    'repeatOnOff',
    'startDate',
    'interval',
    'dayOfMonth',
  )


class ServInfoMailLogAdmin(admin.ModelAdmin):
  list_display = (
    'buyEntity',
    'sendUser',
  )

class AddListAdmin(admin.ModelAdmin):
  list_display = (
    'listName',
  )

admin.site.register(ServInfoMailSets, ServInfoMailSetsAdmin)
admin.site.register(ServInfoMailLog, ServInfoMailLogAdmin)
admin.site.register(AddList, AddListAdmin)