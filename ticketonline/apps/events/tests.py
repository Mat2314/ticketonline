from django.test import TestCase
from rest_framework.test import APIClient
from .models import Event, Reservation
import datetime
import pytz
from datetime import timedelta
from ticketonline.apps.tickets.models import TicketType, OrderedTicket


class EventTestCase(TestCase):
    """ Test case for events/event endpoint"""

    def setUp(self):
        self.client = APIClient()
        # Create a set of N events
        events_amount = 30

        for i in range(events_amount):
            event_date = datetime.datetime.utcnow().replace(tzinfo=pytz.utc) + timedelta(days=i)
            new_event = Event(name=f"Generated_event_{i}", date=event_date)
            new_event.save()

    def test_event_list(self):
        """Test checks if endpoint returns proper list of events"""
        # Test connection with the endpoint
        response = self.client.get('/events/event/', {'current_page': 1, 'page_size': 20}, format='json')
        self.assertEqual(response.status_code, 200)

        # Check if the amount of events is ok
        self.assertEqual(response.json()['last_page'], 2)
        self.assertEqual(len(response.json()['events']), 20)

    def test_event_details(self):
        """
        Test checks if event detailed data returned by the server is valid.
        Test checks:
            - response code
            - event information
            - amounts of tickets
        """
        # Create a proper event
        event_date = datetime.datetime.utcnow().replace(tzinfo=pytz.utc) + timedelta(days=3)
        new_event = Event(name=f"Concert", date=event_date)
        new_event.save()

        # Define tocket types for an event
        ticket_types = [
            {"type": "VIP", "price": 100, "amount": 50, "amount_created": 30},
            {"type": "Gold", "price": 80, "amount": 150, "amount_created": 100},
            {"type": "Silver", "price": 50, "amount": 300, "amount_created": 200},
        ]

        # Create tickets in the database
        for ticket in ticket_types:
            TicketType(type=ticket['type'], event=new_event, price=ticket['price'], amount=ticket['amount']).save()

        # Create some ordered tickets
        for ticket_type in ticket_types:
            reservation = Reservation(event=new_event, status='COMPLETED', pending_until=event_date)
            reservation.save()

            # Create proper amount of tickets of each type
            for i in range(ticket_type['amount_created']):
                new_ticket = OrderedTicket(reservation=reservation, event=new_event, price=ticket_type['price'],
                                           type=ticket_type['type'])
                new_ticket.save()

        # Also create some tickets with cancelled reservation
        for ticket_type in ticket_types:
            reservation = Reservation(event=new_event, status='CANCELLED', pending_until=event_date)
            reservation.save()

            # Create 5 tickets in each cancelled reservation
            for i in range(5):
                new_ticket = OrderedTicket(reservation=reservation, event=new_event, price=ticket_type['price'],
                                           type=ticket_type['type'])
                new_ticket.save()

        # Check server response
        response = self.client.post('/events/event/', {'event_id': str(new_event.id)}, format='json')
        self.assertEqual(response.status_code, 200)

        for ticket_type in response.json()['ticket_types']:
            expected_amount = 0
            for ticket in ticket_types:
                if ticket['type'] == ticket_type['type']:
                    expected_amount = ticket['amount'] - ticket['amount_created']

            self.assertEqual(ticket_type['tickets_left'], expected_amount)


class ReservationTestCase(TestCase):
    """Test case for events/reservation/ endpoint"""

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

    def test_cancel_reservation(self):
        """Test checks cancel reservation process"""
        # Create a reservation by using the endpoint
        response = self.client.post('/events/reservation/',
                                    {'tickets': [
                                        {"type": "VIP", "amount": 3},
                                        {"type": "Gold", "amount": 1}
                                    ], 'event_id': str(self.event.id)},
                                    format='json')

        # Check if the response returned reservation_id and sessionid
        self.assertEqual(response.status_code, 200)
        self.assertTrue('reservation_id' in response.json())
        self.assertFalse(response.cookies is None)

        # Save returned reservation_id
        reservation_id = response.json()['reservation_id']

        # Try to cancel the reservation
        response = self.client.delete('/events/reservation/', {'reservation_id': str(reservation_id)}, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertTrue('ok' in response.json())

    def test_reservation_details(self):
        """Test checks reservation details validity"""
        # Create a reservation
        reservation = Reservation(event=self.event,
                                  pending_until=datetime.datetime.utcnow().replace(tzinfo=pytz.utc) + timedelta(
                                      minutes=15))
        reservation.save()

        # Assign some tickets to this reservation
        tickets_amount = 3
        for i in range(tickets_amount):
            ticket = OrderedTicket(type="VIP", price=100, event=self.event, reservation=reservation)
            ticket.save()

        # Check server response
        response = self.client.get('/events/reservation/', {'reservation_id': str(reservation.id)}, format='json')
        self.assertEqual(response.status_code, 200)

        # Check if the response is complete
        self.assertTrue('reservation' in response.json())
        self.assertTrue('tickets' in response.json())
        self.assertTrue('event' in response.json())

        self.assertEqual(len(response.json()['tickets']), 3)


class StatisticsTestCase(TestCase):
    """Test case for events/stats/ endpoint"""

    def setUp(self):
        self.client = APIClient()

    def test_statistics(self):
        """Test checks stats reliability"""
        # Create event
        event_date = datetime.datetime.utcnow().replace(tzinfo=pytz.utc) - timedelta(days=7)
        new_event = Event(name=f"Concert", date=event_date)
        new_event.save()

        # Create ticket types
        ticket_types = [
            {"type": "VIP", "price": 100, "amount": 50, 'amount_created': 32},
            {"type": "Gold", "price": 80, "amount": 150, 'amount_created': 78},
            {"type": "Silver", "price": 50, "amount": 300, 'amount_created': 250},
        ]

        # Create tickets in the database
        for ticket in ticket_types:
            TicketType(type=ticket['type'], event=new_event, price=ticket['price'], amount=ticket['amount']).save()

        # Create reservations of all types PENDING, COMPLETED, CANCELLED
        # Create ordered tickets
        for ticket_type in ticket_types:
            reservation = Reservation(event=new_event, status='COMPLETED', pending_until=event_date)
            reservation.save()

            # Create proper amount of tickets of each type
            for i in range(ticket_type['amount_created']):
                new_ticket = OrderedTicket(reservation=reservation, event=new_event, price=ticket_type['price'],
                                           type=ticket_type['type'])
                new_ticket.save()

        # Also create some tickets with cancelled reservation
        for ticket_type in ticket_types:
            reservation = Reservation(event=new_event, status='CANCELLED', pending_until=event_date)
            reservation.save()

            # Create 5 tickets in each cancelled reservation
            for i in range(5):
                new_ticket = OrderedTicket(reservation=reservation, event=new_event, price=ticket_type['price'],
                                           type=ticket_type['type'])
                new_ticket.save()

        # Call stats endpoint
        # Verify it's reliability
        response = self.client.get('/events/stats/', {'event_id': str(new_event.id)}, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertTrue('event' in response.json())

        # Check stats values
        self.assertEqual(response.json()['ticket_counters']['all_tickets_sold'], 360)
        for ticket in ticket_types:
            self.assertEqual(response.json()['ticket_counters']['ticket_types'][ticket['type']],
                             ticket['amount_created'])
