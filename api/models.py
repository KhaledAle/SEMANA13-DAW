from django.conf import settings
from django.db import models
from django.db.models.functions import Lower


class Resource(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "active", "Activo"
        INACTIVE = "inactive", "Inactivo"

    name = models.CharField("nombre", max_length=120)
    description = models.TextField("descripción")
    category = models.CharField("categoría", max_length=80, db_index=True)
    status = models.CharField(
        "estado",
        max_length=8,
        choices=Status.choices,
        default=Status.ACTIVE,
        db_index=True,
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="resources",
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField("creado", auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField("actualizado", auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                Lower("name"),
                Lower("category"),
                name="unique_resource_name_per_category_ci",
            ),
        ]
        verbose_name = "recurso"
        verbose_name_plural = "recursos"

    def __str__(self):
        return self.name
