from django.urls import include
from django.conf.urls import url
from rest_framework import routers
from . import views

router = routers.DefaultRouter()
router.register('list', views.TransactionViewSet)

urlpatterns = [
    url('', include(router.urls)),
]
