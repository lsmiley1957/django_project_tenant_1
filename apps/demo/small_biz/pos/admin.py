from django.contrib import admin
from .models import POSSession, POSTransaction, POSItem


admin.site.register(POSSession)

admin.site.register(POSTransaction)

admin.site.register(POSItem)