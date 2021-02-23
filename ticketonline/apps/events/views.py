from rest_framework import viewsets
from .serializers import EventSerializer, ReservationSerializer
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.http import JsonResponse, HttpResponse
from django.core.paginator import Paginator
from ticketonline.decorators import log_exceptions
from .models import Event, Reservation
from ticketonline.apps.tickets.serializers import TicketTypeSerializer, OrderedTicketSerializer
from django.db.models import Q
from ticketonline.apps.tickets.models import TicketType, OrderedTicket
import datetime
from datetime import timedelta
from django.core.paginator import Paginator
from ticketonline.apps.payments.tasks import process_reservation_payment
from ticketonline.apps.payments.models import Transaction


# Create your views here.
class EventViewSet(viewsets.ModelViewSet):
    queryset = Event.objects.all()
    serializer_class = EventSerializer
    permission_classes = (AllowAny,)

    @log_exceptions("Error - could not get list of all events")
    def list(self, request):
        """
        Endpoint returns paginated list of all events available in the database.
        Required params:
        - current_page: number (starting from 1)
        - page_size: number
        :param request:
        :return:
            - events: list - list of events
            - last_page: number
        """
        # Read the params
        current_page = int(self.request.query_params.get('current_page'))
        page_size = int(self.request.query_params.get('page_size'))

        # Get all the events which will happen sorted from the earliest
        now = datetime.datetime.now()
        events = Event.objects.filter(date__gte=now).order_by('date')
        events_serializer = EventSerializer(events, many=True)

        # Setup paginator and get current page
        paginator = Paginator(events_serializer.data, page_size)
        page = paginator.get_page(current_page)

        # Gather all the information and return
        return_data = dict()
        return_data['events'] = page.object_list
        return_data['last_page'] = paginator.num_pages

        return JsonResponse(return_data)

    @log_exceptions("Error - could not get info about the event")
    def create(self, request):
        """
        Endpoint returns detailed info about particular event based on given event id.
        Required params:
            - event_id: string
        :param request:
        :return: Event data, types of tickets, amount of tickets available
        """
        # Read event id and try to get particular event
        event = Event.objects.get(id=request.data['event_id'])

        # Serialize event data
        event_serializer = EventSerializer(event)
        # Get all types of tickets and amount of available tickets
        ticket_types = event.ticket_types.all()
        ticket_type_serializer = TicketTypeSerializer(ticket_types, many=True)

        # Get all the ticket types
        serialized_ticket_types = ticket_type_serializer.data

        # Initialize reserved tickets counters
        ticket_counters = dict()
        # Initialize counters for all ticket types
        for ticket in serialized_ticket_types:
            ticket_counters[ticket['type']] = event.tickets_ordered.filter(
                Q(type=ticket['type'], reservation__status='PENDING') |
                Q(type=ticket['type'], reservation__status='COMPLETED'), ).count()

        # Calculate final amount of tickets left for each ticket category
        for ticket in serialized_ticket_types:
            ticket['tickets_left'] = ticket['amount'] - ticket_counters[ticket['type']]

        # Assign all the returned data to a variable
        return_data = dict()
        return_data['event'] = event_serializer.data
        return_data['ticket_types'] = ticket_type_serializer.data

        return JsonResponse(return_data)


class ReservationViewSet(viewsets.ModelViewSet):
    queryset = Reservation.objects.all()
    serializer_class = ReservationSerializer
    permission_classes = (AllowAny,)

    @log_exceptions("Error - could not get reservation data")
    def list(self, request):
        """
        Endpoint returns detailed info about the reservation.
        Required payload:
            - reservation_id: string
        :param request:
        :return: Reservation data and ticket data
        """
        # Get reservation and serialize it
        reservation_id = self.request.query_params.get('reservation_id')
        reservation = Reservation.objects.get(id=reservation_id)
        reservation_serializer = ReservationSerializer(reservation)

        # Get tickets related to this reservation
        tickets = reservation.tickets.all()
        tickets_serializer = OrderedTicketSerializer(tickets, many=True)

        # Get event info
        event = reservation.event
        event_serializer = EventSerializer(event)

        # Gather all the data and return
        return_data = dict()
        return_data['reservation'] = reservation_serializer.data
        return_data['tickets'] = tickets_serializer.data
        return_data['event'] = event_serializer.data

        return JsonResponse(return_data)

    @log_exceptions("Error - could not create a reservation for this event")
    def create(self, request):
        """
        Endpoint handles creating a reservation of N tickets for particular event.
        Application assumes maximum 5 tickets of each type.
        Required payload:
            - tickets: Array with ticket types and the amount for each ticket
            (example: [{"type":"VIP", "amount":3},{"type":"Basic", "amount": 1}])

            - event_id: string
        :param request:
        :return:
            - ok / error string info
            - reservation_id (in case of successfull reservation)
        """
        # Find event and collect tickets ordered by user
        event = Event.objects.get(id=request.data['event_id'])
        ordered_tickets = request.data['tickets']

        # Gather ticket types assigned to this event
        event_tickets = event.ticket_types.all()
        # And save their types in a list
        ticket_types = [t.type for t in event_tickets]

        # Check if the ticket types are exactly as the ones defined by the event host
        for ticket in ordered_tickets:
            if not ticket['type'] in ticket_types:
                return JsonResponse({"error": "Requested ticket type is not present in event ticket types",
                                     "message": "This event does not distribute tickets of this type"})

        # Check if the ticket amounts are not bigger than amount of available tickets
        for ticket in ordered_tickets:
            # If there are more than 5 tickets of any type
            # Return error message
            if ticket['amount'] > 5:
                return JsonResponse({"error": "Ordering more tickets than allowed!",
                                     "message": "Can not order more than 5 tickets of each type"})

            for event_ticket in event_tickets:
                if event_ticket.type == ticket['type']:
                    # Calculate tickets already bought and reserved
                    tickets_already_ordered = event.tickets_ordered.filter(
                        Q(type=ticket['type'], reservation__status='PENDING') |
                        Q(type=ticket['type'], reservation__status='COMPLETED')).count()

                    # If there's not enough tickets of certain type return error message
                    if event_ticket.amount - tickets_already_ordered < ticket['amount']:
                        return JsonResponse({"error": "Requested more tickets than available",
                                             "message": f"This event does not have sufficient quantity of {ticket['type']} tickets"})

        # Ticket types are correct
        # There are enough tickets to buy
        # Create reservation and ordered tickets to database
        reservation_start = datetime.datetime.now()
        reservation_end = reservation_start + timedelta(minutes=15)

        # Create new reservation with PENDING status
        new_reservation = Reservation(event=event, reservation_date=reservation_start, pending_until=reservation_end)
        new_reservation.save()

        for ticket in ordered_tickets:
            # Get the price for current ticket
            ticket_price = event.ticket_types.filter(type=ticket['type'])[0].price
            for i in range(ticket['amount']):
                new_ticket = OrderedTicket(type=ticket['type'], event=event, reservation=new_reservation,
                                           price=ticket_price)
                new_ticket.save()

        # Setup session for 15 minutes
        request.session['reservation_id'] = str(new_reservation.id)
        request.session.set_expiry(900)

        return JsonResponse({"ok": "Reservation made successfully", "reservation_id": str(new_reservation.id),
                             "message": "Reservation made successfully! Remember to finalize the payment within 15 miuntes from now"})

    @log_exceptions("Error - could not initialize the payment for the reservation")
    def put(self, request):
        """
        Endpoint handles payment simulation for given reservation.
        Required params:
            - reservation_id: string
        :param request:
        :return:
        """
        # Get the reservation and its tickets
        reservation = Reservation.objects.get(id=request.data['reservation_id'])

        # Check reservation status
        if reservation.status != "PENDING":
            return JsonResponse({"error": "Reservation status is different than PENDING",
                                 "message": "Status of this reservation does not allow to process a payment for it"})

        # Calculate total price for all the tickets
        tickets = reservation.tickets.all()
        total_amount = 0
        for ticket in tickets:
            total_amount += ticket.price

        # Initiate a new transaction
        new_transaction = Transaction(amount=total_amount, reservation=reservation)
        new_transaction.save()

        # Setup worker to handle payment
        process_reservation_payment.delay(reservation.id, new_transaction.id)

        return JsonResponse(
            {"ok": "Transaction started", "reservation_id": reservation.id, 'transaction_id': str(new_transaction.id),
             "message": "Transaction started successfully. Now wait for payment confirmation"})

    @log_exceptions("Error - could not remove the reservation")
    def delete(self, request):
        """
        Endpoint enables cancelling the reservation initiated by user.
        :param request:
        :return:
        """
        # Check if user session contains proper reservation_id
        reservation_id = request.session.pop('reservation_id', None)

        # Cancel reservation
        reservation = Reservation.objects.get(id=reservation_id)
        reservation.status = 'CANCELLED'
        reservation.save()

        return JsonResponse(
            {"ok": "Reservation cancelled", "message": "Reservation for the event was cancelled successfully"})


class EventStatisticsViewSet(viewsets.ModelViewSet):
    queryset = Event.objects.all()
    serializer_class = EventSerializer
    permission_classes = (AllowAny,)

    @log_exceptions("Error - could not get statistics for this event")
    def list(self, request):
        """
        Endpoint returns statistics for given event.
        Statistics present how many tickets were sold in total and how many tickets each type were sold.
        Required params:
            - event_id: string
        :param request:
        :return: dictionary with data regarding tickets sold and the event
        """
        # Get event and serialize it
        event_id = self.request.query_params.get('event_id')
        event = Event.objects.get(id=event_id)
        event_serializer = EventSerializer(event)

        # Get all possible ticket types
        ticket_types = TicketType.objects.filter(event=event)
        ticket_types_list = [ticket.type for ticket in ticket_types]

        # Setup counters
        ticket_counters = {
            "all_tickets_sold": event.tickets_ordered.filter(Q(reservation__status="COMPLETED")).count(),
            "ticket_types": {}
        }

        # Count all sold tickets of each type
        for ticket_type in ticket_types_list:
            ticket_counters["ticket_types"][ticket_type] = event.tickets_ordered.filter(
                Q(reservation__status="COMPLETED", type=ticket_type)).count()

        # Collect all the data and return it
        return_data = dict()
        return_data['ticket_counters'] = ticket_counters
        return_data['event'] = event_serializer.data

        return JsonResponse(return_data)
