from django.db import models
import uuid
from ticketonline.apps.events.models import Event, Reservation


# Create your models here.
class TicketModel(models.Model):
    """
    An abstract class which holds ticket-related data.
    Class attributes:
    - type - ticket type which might be customized for each type of event. (example: VIP, Gold, Silver, ...)
    - price - price for a single ticket of current type
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    type = models.CharField(max_length=32)
    price = models.FloatField()

    class Meta:
        abstract = True


class TicketType(TicketModel):
    """
    Class stores the data related to ticket type assigned to particular event.
    Class atrributes:
    - amount - the amount of tickets of current type released for particular event
    - event - the event to which tickets refer to
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    amount = models.IntegerField()
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="ticket_types")

    def __str__(self):
        return f"${self.event.name} - {self.type} (${self.price} EUR). Amount released: {self.amount}"

    class Meta:
        verbose_name = "Ticket type"
        verbose_name_plural = "Ticket types"


class OrderedTicket(TicketModel):
    """
    Class stores the data related to ticket ordered by the User.
    Class attributes:
    - reservation - the reservation made by user for particular event. The ticket is assigned to one reservation.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    reservation = models.ForeignKey(Reservation, on_delete=models.CASCADE, related_name="tickets")

    def __str__(self):
        return f"${self.type} ${self.price} EUR. Status: ${self.reservation.status}. " \
               f"Event: {self.reservation.event.name}."

    class Meta:
        verbose_name = "Ordered ticket"
        verbose_name_plural = "Ordered tickets"
