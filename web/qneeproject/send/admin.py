from django.contrib import admin
from .models import InvitationSets, InvitationLog, AddList

class InvitationSetsAdmin(admin.ModelAdmin):
  list_display = (
    'repeatOnOff',
    'startDate',
    'interval',
    'dayOfMonth',
  )


class InvitationLogAdmin(admin.ModelAdmin):
  list_display = (
    'buyEntity',
    'sendUser',
  )

class AddListAdmin(admin.ModelAdmin):
  list_display = (
    'listName',
  )

admin.site.register(InvitationSets, InvitationSetsAdmin)
admin.site.register(InvitationLog, InvitationLogAdmin)
admin.site.register(AddList, AddListAdmin)