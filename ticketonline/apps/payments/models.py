from django.db import models
import uuid
from ticketonline.apps.events.models import Reservation


# Create your models here.
class Transaction(models.Model):
    """
    Class stores the data related to transaction referring to particular reservation.
    Attributes:
        - status - transaction status
        - date - date of transaction initialization
        - amount - the total amount to pay for all the tickets made with one reservation
        - reservation - the reservation made by user
        - error_type - in case of Payment Gateway error, this is the description of an error
    """
    STATUS = (
        ('COMPLETED', 'COMPLETED'),
        ('PENDING', 'PENDING'),
        ('CANCELLED', 'CANCELLED'),
        ('ERROR', 'ERROR'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    status = models.CharField(max_length=32, default="PENDING")
    date = models.DateTimeField(auto_now_add=True)
    amount = models.FloatField()
    reservation = models.ForeignKey(Reservation, on_delete=models.CASCADE, related_name="transactions")
    error_type = models.CharField(max_length=256, null=True, blank=True)

    def __str__(self):
        return f"{self.date} ({self.amount}) - {self.reservation.event.name}"
