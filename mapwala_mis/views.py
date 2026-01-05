from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.tokens import AccessToken
from django.utils import timezone
from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter


from .serializers import (LoginSerializer, StateSerializer, DistrictSerializer)
from .models import (UserProfile, State, District)


class LoginAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data["user"]

        # Save terms acceptance
        profile, _ = UserProfile.objects.get_or_create(user=user)
        profile.accepted_terms = True
        profile.accepted_at = timezone.now()
        profile.save()

        # Generate JWT tokens
        access_token = AccessToken.for_user(user)

        return Response(
            {
                "message": "Login successful",
                "access_token": str(access_token),
                "expires_in_hours": 24,
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "is_staff": user.is_staff,
                    "is_superuser": user.is_superuser,
                },
            },
            status=status.HTTP_200_OK,
        )


class StateViewSet(ModelViewSet):
    queryset = State.objects.all()
    serializer_class = StateSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [SearchFilter]
    search_fields = ["name"]

    @action(detail=False, methods=["get"])
    def active(self, request):
        queryset = self.get_queryset().filter(status="active")
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class DistrictViewSet(ModelViewSet):
    queryset = District.objects.select_related("state").all()
    serializer_class = DistrictSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [SearchFilter]
    search_fields = ["name", "code"]

    def get_queryset(self):
        queryset = super().get_queryset()
        state_id = self.request.query_params.get("state")
        if state_id:
            queryset = queryset.filter(state_id=state_id)
        return queryset
