from ticketonline.celery import app
from .utils.payment_gateway import PaymentGateway
from ticketonline.apps.events.models import Reservation
import random
from .utils.payment_gateway import CurrencyError, PaymentError, CardError
from .models import Transaction


@app.task
def process_reservation_payment(reservation_id, transaction_id):
    """
    Task is using the payment gateway to process the payment.
    :param reservation_id: id of the reservation object
    :param transaction_id: id of the transaction
    :return:
    """

    # Define gateway
    gateway = PaymentGateway()

    # Get reservation
    reservation = Reservation.objects.get(id=reservation_id)

    # generate a random token to simulate different cases
    tokens = ['card_error', 'payment_error', 'transaction_ok']
    random_token = tokens[random.randint(0, len(tokens))]

    # Initiate the new transaction
    new_transaction = Transaction.objects.get(id=transaction_id)

    # Pass amount to the gateway along with random token
    # Handle any possible exception
    try:
        # Process the payment
        gateway.charge(new_transaction.amount, random_token)
    except (CurrencyError, PaymentError, CardError) as e:
        # Add transaction error
        new_transaction.status = 'ERROR'
        new_transaction.error_type = e.args[0]
        new_transaction.save()

    else:
        # Add successfull transaction
        # And change reservation status
        new_transaction.status = 'COMPLETED'
        new_transaction.save()

        reservation.status = 'COMPLETED'
        reservation.save()
