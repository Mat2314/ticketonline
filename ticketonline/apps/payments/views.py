from rest_framework.permissions import IsAuthenticated, AllowAny
from .models import Transaction
from .serializers import TransactionSerializer
from ticketonline.decorators import log_exceptions
from rest_framework import viewsets
from django.http import JsonResponse


class TransactionViewSet(viewsets.ModelViewSet):
    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer
    permission_classes = (AllowAny,)

    @log_exceptions("Error - could not get a transaction info")
    def list(self, request):
        """
        Endpoint checks status of the transaction with given id.
        Required params:
        - transaction_id: strin
        :param request:
        :return: status: string
        """
        # Get transaction
        transaction_id = self.request.query_params.get('transaction_id')
        transaction = Transaction.objects.get(id=transaction_id)

        return JsonResponse({"status": transaction.status, "transaction_error": transaction.error_type})
