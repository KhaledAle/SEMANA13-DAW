from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase, override_settings
from rest_framework import status
from rest_framework.test import APIClient, APITestCase
from rest_framework.throttling import AnonRateThrottle

from .models import Resource
from .views import ResourceViewSet

User = get_user_model()


class ResourceApiTests(APITestCase):
    def setUp(self):
        self.owner = User.objects.create_user(username="owner", password="test-pass-123")
        self.other_user = User.objects.create_user(
            username="other", password="test-pass-123"
        )
        self.resource = Resource.objects.create(
            name="Equipo de prueba",
            description="Recurso de prueba para la API.",
            category="equipos",
            status=Resource.Status.INACTIVE,
            owner=self.owner,
        )

    def test_list_is_paginated_and_includes_hateoas_links(self):
        response = self.client.get("/api/recursos/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        item = response.data["results"][0]
        self.assertIn("url", item)
        self.assertEqual(item["_links"]["self"], item["url"])
        self.assertTrue(item["_links"]["collection"].endswith("/api/recursos/"))
        self.assertNotIn("owner", item)

    def test_filter_search_ordering_and_page_size_limit(self):
        Resource.objects.create(
            name="Equipo auxiliar",
            description="Segundo recurso de prueba.",
            category="equipos",
            status=Resource.Status.ACTIVE,
            owner=self.owner,
        )
        response = self.client.get(
            "/api/recursos/?status=active&search=auxiliar&ordering=name&page_size=100"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["name"], "Equipo auxiliar")

    def test_page_size_is_capped_at_fifty(self):
        Resource.objects.bulk_create(
            [
                Resource(
                    name=f"Recurso {index}",
                    description="Recurso de prueba para paginación.",
                    category="paginacion",
                    owner=self.owner,
                )
                for index in range(51)
            ]
        )
        response = self.client.get("/api/recursos/?page_size=100")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 52)
        self.assertEqual(len(response.data["results"]), 50)

    def test_anonymous_user_cannot_create_resource(self):
        response = self.client.post(
            "/api/recursos/",
            {
                "name": "Nuevo",
                "description": "Recurso válido para crear.",
                "category": "equipos",
                "status": "active",
            },
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_authenticated_create_and_duplicate_validation(self):
        self.client.force_authenticate(self.owner)
        data = {
            "name": "  Nuevo recurso  ",
            "description": "Descripción válida del recurso.",
            "category": "equipos",
            "status": "active",
        }
        response = self.client.post("/api/recursos/", data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["name"], "Nuevo recurso")
        self.assertEqual(response.data["owner_username"], "owner")

        duplicate = dict(data, name="nuevo recurso")
        duplicate_response = self.client.post("/api/recursos/", duplicate)
        self.assertEqual(duplicate_response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("name", duplicate_response.data)

    def test_only_owner_can_modify_and_activate(self):
        self.client.force_authenticate(self.other_user)
        denied = self.client.patch(
            f"/api/recursos/{self.resource.pk}/",
            {"name": "Cambio no autorizado"},
        )
        self.assertEqual(denied.status_code, status.HTTP_403_FORBIDDEN)

        self.client.force_authenticate(self.owner)
        activated = self.client.post(f"/api/recursos/{self.resource.pk}/activar/")
        self.assertEqual(activated.status_code, status.HTTP_200_OK)
        self.assertEqual(activated.data["status"], Resource.Status.ACTIVE)

    def test_owner_can_update_and_delete_resource(self):
        self.client.force_authenticate(self.owner)
        updated = self.client.patch(
            f"/api/recursos/{self.resource.pk}/",
            {"name": "Equipo actualizado"},
        )
        self.assertEqual(updated.status_code, status.HTTP_200_OK)
        self.assertEqual(updated.data["name"], "Equipo actualizado")

        deleted = self.client.delete(f"/api/recursos/{self.resource.pk}/")
        self.assertEqual(deleted.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Resource.objects.filter(pk=self.resource.pk).exists())

    def test_summary_serializes_non_model_data_and_schema_is_available(self):
        summary = self.client.get("/api/recursos/resumen/")
        schema = self.client.get("/api/schema/")
        docs = self.client.get("/api/docs/")

        self.assertEqual(summary.status_code, status.HTTP_200_OK)
        self.assertEqual(summary.data["total_records"], 1)
        self.assertEqual(summary.data["status"], "ok")
        self.assertEqual(schema.status_code, status.HTTP_200_OK)
        self.assertIn("/api/recursos/", schema.data["paths"])
        self.assertEqual(docs.status_code, status.HTTP_200_OK)

    def test_cors_preflight_allows_only_configured_origin(self):
        with override_settings(CORS_ALLOWED_ORIGINS=["http://localhost:3000"]):
            allowed = self.client.options(
                "/api/recursos/",
                HTTP_ORIGIN="http://localhost:3000",
                HTTP_ACCESS_CONTROL_REQUEST_METHOD="POST",
                HTTP_ACCESS_CONTROL_REQUEST_HEADERS="content-type,x-csrftoken",
            )
            denied = self.client.options(
                "/api/recursos/",
                HTTP_ORIGIN="http://untrusted.example",
                HTTP_ACCESS_CONTROL_REQUEST_METHOD="POST",
            )

        self.assertEqual(
            allowed.headers.get("Access-Control-Allow-Origin"),
            "http://localhost:3000",
        )
        self.assertIn(
            "POST",
            allowed.headers.get("Access-Control-Allow-Methods", ""),
        )
        self.assertIn(
            "x-csrftoken",
            allowed.headers.get("Access-Control-Allow-Headers", "").lower(),
        )
        self.assertIsNone(denied.headers.get("Access-Control-Allow-Origin"))

    def test_session_authentication_requires_csrf_token(self):
        client = APIClient(enforce_csrf_checks=True)
        client.force_login(self.owner)
        client.get("/api/csrf/")
        data = {
            "name": "CSRF recurso",
            "description": "Descripción válida para comprobar CSRF.",
            "category": "pruebas",
            "status": "active",
        }

        without_token = client.post("/api/recursos/", data)
        self.assertEqual(without_token.status_code, status.HTTP_403_FORBIDDEN)

        token = client.cookies["csrftoken"].value
        with_token = client.post(
            "/api/recursos/",
            data,
            format="json",
            HTTP_X_CSRFTOKEN=token,
        )
        self.assertEqual(with_token.status_code, status.HTTP_201_CREATED)


class ThrottleTests(TestCase):
    def test_anonymous_requests_are_throttled(self):
        class TwoPerMinuteAnonThrottle(AnonRateThrottle):
            THROTTLE_RATES = {"anon": "2/minute"}

        cache.clear()
        with patch.object(ResourceViewSet, "throttle_classes", [TwoPerMinuteAnonThrottle]):
            client = APIClient()
            self.assertEqual(client.get("/api/recursos/").status_code, 200)
            self.assertEqual(client.get("/api/recursos/").status_code, 200)
            limited = client.get("/api/recursos/")

        self.assertEqual(limited.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
        self.assertIn("Retry-After", limited.headers)
