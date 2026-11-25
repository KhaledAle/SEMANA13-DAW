from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import ResourceViewSet, csrf_cookie

app_name = "api"

router = DefaultRouter()
router.register("recursos", ResourceViewSet, basename="recurso")

urlpatterns = [
    path("csrf/", csrf_cookie, name="csrf"),
    path("", include(router.urls)),
]
