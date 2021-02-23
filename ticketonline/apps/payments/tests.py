from django.test import TestCase
from rest_framework.test import APIClient
from .models import Transaction
from ticketonline.apps.events.models import Event, Reservation
import datetime
import pytz
from datetime import timedelta
from ticketonline.apps.tickets.models import TicketType, OrderedTicket


class TransactionTestCase(TestCase):
    """ Test case for transactions/list endpoint"""

    def setUp(self):
        self.client = APIClient()

        # Create an event
        event_date = datetime.datetime.utcnow().replace(tzinfo=pytz.utc) + timedelta(days=60)
        new_event = Event(name=f"Concert", date=event_date)
        new_event.save()
        self.event = new_event

        # Create some ticket types
        ticket_types = [
            {"type": "VIP", "price": 100, "amount": 50},
            {"type": "Gold", "price": 80, "amount": 150},
            {"type": "Silver", "price": 50, "amount": 300},
        ]

        # Create tickets in the database
        for ticket in ticket_types:
            TicketType(type=ticket['type'], event=new_event, price=ticket['price'], amount=ticket['amount']).save()

    def test_transaction_info(self):
        """Test checks if the transaction changes its status after simulated payment"""
        # Create reservation with some tickets
        response = self.client.post('/events/reservation/',
                                    {'tickets': [
                                        {"type": "VIP", "amount": 3},
                                        {"type": "Gold", "amount": 1}
                                    ], 'event_id': str(self.event.id)},
                                    format='json')

        # Save returned reservation_id
        reservation_id = response.json()['reservation_id']

        # Call endpoint to pay for the tickets
        response = self.client.put('/events/reservation/', {'reservation_id': reservation_id}, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertTrue('transaction_id' in response.json())

        transaction_id = response.json()['transaction_id']

        # Test if the transaction status changes
        response = self.client.get('/transactions/list/', {'transaction_id': transaction_id}, format='json')
        self.assertEqual(response.status_code, 200)

        # Define possible status values and check if status matches any of those
        possible_status_values = ['COMPLETED', 'ERROR']
        print(response.json())
        self.assertTrue(response.json()['status'] in possible_status_values)
