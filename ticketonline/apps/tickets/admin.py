from django.contrib import admin
from .models import OrderedTicket, TicketType

# Register your models here.
admin.site.register(OrderedTicket)
admin.site.register(TicketType)
