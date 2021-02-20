from django.db import models
import uuid


# Create your models here.
class Event(models.Model):
    """
    Class stores the data related to single event.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=512)
    date = models.DateTimeField(auto_now=False, auto_now_add=False)

    def __str__(self):
        return f"{self.name} - {self.date}"


class Reservation(models.Model):
    """
    Class stores the data related to made tickets reservation.
    There are 3 different statuses of a reservation:
    - CANCELLED - Something went wrong with the payment process or the payment was not handled within 15 minutes and
    the reservation is being cancelled
    - PENDING - User did select some tickets and this is the 15 minutes time period between making an order and
    handling payment
    - COMPLETED - Everything went fine and the tickets were purchased successfully by the user

    Other attributes:
    - pending_until - the exact date and time when the 15 minutes buffer will be finished
    - reservation_date - the moment the User initiated a reservation process
    - event - the particular event this reservation is related to
    """
    STATUS_SELECT = (
        ('CANCELLED', 'CANCELLED'),
        ('PENDING', 'PENDING'),
        ('COMPLETED', 'COMPLETED')
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    status = models.CharField(max_length=32, choices=STATUS_SELECT, default='PENDING')
    pending_until = models.DateTimeField(auto_now=False, auto_now_add=False)
    reservation_date = models.DateTimeField(auto_now=False, auto_now_add=True)
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="reservations")

    def __str__(self):
        return f"Event: {self.event.name}. Status: {self.status}. ({self.reservation_date})"
