from .models import OrderedTicket, TicketType
from rest_framework import serializers


class OrderedTicketSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderedTicket
        fields = '__all__'


class TicketTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = TicketType
        fields = '__all__'
