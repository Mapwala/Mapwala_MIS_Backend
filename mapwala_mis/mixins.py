# mapwala_mis/mixins.py
from rest_framework.response import Response
from rest_framework import status
from django.db.models import ProtectedError
from django.db import DatabaseError


class DeleteResponseMixin:

    delete_object_name = "object"
    delete_display_field = None

    def get_display_value(self, instance):

        if self.delete_display_field:
            return getattr(instance, self.delete_display_field, str(instance))

        for field in ["name", "username", "title"]:
            if hasattr(instance, field):
                return getattr(instance, field)

        return str(instance)

    def destroy(self, request, *args, **kwargs):

        instance = self.get_object()
        display_value = self.get_display_value(instance)
        instance_id = instance.id  # capture before deletion

        try:
            self.perform_destroy(instance)

        except ProtectedError:
            return Response(
                {
                    "success": False,
                    "message": f"{self.delete_object_name.capitalize()} '{display_value}' cannot be deleted because it is linked to other records.",
                },
                status=status.HTTP_409_CONFLICT,
            )

        except DatabaseError:
            return Response(
                {
                    "success": False,
                    "message": f"{self.delete_object_name.capitalize()} '{display_value}' could not be deleted due to a database error.",
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return Response(
            {
                "success": True,
                "message": f"{self.delete_object_name.capitalize()} '{display_value}' deleted successfully.",
                self.delete_object_name: {
                    "id": instance_id,
                    "name": display_value,
                },
            },
            status=status.HTTP_200_OK,
        )
