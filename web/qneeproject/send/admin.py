from django.contrib import admin
from .models import ServInfoMailSets, ServInfoMailLog

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

admin.site.register(ServInfoMailSets, ServInfoMailSetsAdmin)
admin.site.register(ServInfoMailLog, ServInfoMailLogAdmin)