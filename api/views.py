from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_GET
from drf_spectacular.utils import extend_schema
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Resource
from .serializers import ApiStatusSerializer, ResourceSerializer


class ResourceViewSet(viewsets.ModelViewSet):
    queryset = Resource.objects.select_related("owner").all()
    serializer_class = ResourceSerializer
    filterset_fields = ("status", "category")
    search_fields = ("name", "description", "category")
    ordering_fields = ("created_at", "name", "id")
    ordering = ("-created_at",)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    @extend_schema(
        responses=ApiStatusSerializer,
        description="Resumen del servicio y cantidad total de recursos.",
    )
    @action(detail=False, methods=["get"], url_path="resumen")
    def resumen(self, request):
        return Response(ApiStatusSerializer(ApiStatusSerializer.current()).data)

    @extend_schema(
        request=None,
        responses=ResourceSerializer,
        description="Cambia el estado del recurso a activo.",
    )
    @action(detail=True, methods=["post"], url_path="activar")
    def activar(self, request, pk=None):
        resource = self.get_object()
        resource.status = Resource.Status.ACTIVE
        resource.save(update_fields=("status", "updated_at"))
        return Response(self.get_serializer(resource).data, status=status.HTTP_200_OK)


@require_GET
@ensure_csrf_cookie
def csrf_cookie(request):
    return JsonResponse({"detail": "Cookie CSRF lista."})
