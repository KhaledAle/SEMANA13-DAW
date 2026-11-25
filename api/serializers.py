from django.utils import timezone
from rest_framework import serializers
from rest_framework.reverse import reverse
from drf_spectacular.utils import extend_schema_field

from .models import Resource


class ResourceSerializer(serializers.HyperlinkedModelSerializer):
    owner_username = serializers.ReadOnlyField(source="owner.username")
    _links = serializers.SerializerMethodField()

    class Meta:
        model = Resource
        fields = (
            "id",
            "url",
            "name",
            "description",
            "category",
            "status",
            "owner_username",
            "created_at",
            "updated_at",
            "_links",
        )
        read_only_fields = ("id", "owner_username", "created_at", "updated_at")
        extra_kwargs = {
            "url": {"view_name": "api:recurso-detail"},
        }

    def validate_name(self, value):
        name = value.strip()
        if not name:
            raise serializers.ValidationError("El nombre no puede estar vacío.")
        return name

    def validate(self, attrs):
        name = attrs.get("name", getattr(self.instance, "name", ""))
        category = attrs.get("category", getattr(self.instance, "category", ""))
        duplicates = Resource.objects.filter(
            name__iexact=name,
            category__iexact=category,
        )
        if self.instance:
            duplicates = duplicates.exclude(pk=self.instance.pk)
        if duplicates.exists():
            raise serializers.ValidationError(
                {"name": "Ya existe un recurso con ese nombre en esta categoría."}
            )
        return attrs

    @extend_schema_field(serializers.DictField(child=serializers.CharField()))
    def get__links(self, obj):
        request = self.context.get("request")
        return {
            "self": reverse("api:recurso-detail", args=[obj.pk], request=request),
            "collection": reverse("api:recurso-list", request=request),
            "activar": reverse("api:recurso-activar", args=[obj.pk], request=request),
        }


class ApiStatusSerializer(serializers.Serializer):
    service = serializers.CharField(read_only=True)
    status = serializers.CharField(read_only=True)
    total_records = serializers.IntegerField(read_only=True)
    timestamp = serializers.DateTimeField(read_only=True)

    @classmethod
    def current(cls):
        return {
            "service": "API RESTful - Laboratorio 13",
            "status": "ok",
            "total_records": Resource.objects.count(),
            "timestamp": timezone.now(),
        }
