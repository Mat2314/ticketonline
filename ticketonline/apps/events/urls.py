from django.urls import include
from django.conf.urls import url
from rest_framework import routers
from . import views

router = routers.DefaultRouter()
router.register('event', views.EventViewSet)
router.register('reservation', views.ReservationViewSet)
router.register('stats', views.EventStatisticsViewSet)

urlpatterns = [
    url('', include(router.urls)),
]
