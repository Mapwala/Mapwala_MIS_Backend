from django.contrib.auth import authenticate
from rest_framework import serializers
from .models import State, District, UserProfile


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)
    accepted_terms = serializers.BooleanField()

    def validate(self, data):
        if not data.get("accepted_terms"):
            raise serializers.ValidationError(
                {"accepted_terms": "Please accept the terms and conditions to continue"}
            )

        user = authenticate(
            username=data["username"],
            password=data["password"],
        )

        if user is None:
            raise serializers.ValidationError(
                {"credentials": "Invalid username or password"}
            )

        data["user"] = user
        return data


class StateSerializer(serializers.ModelSerializer):
    class Meta:
        model = State
        fields = ["id", "name", "status"]


class DistrictSerializer(serializers.ModelSerializer):
    state_name = serializers.CharField(source="state.name", read_only=True)

    class Meta:
        model = District
        fields = [
            "id",
            "name",
            "code",
            "state",
            "state_name",
            "status",
        ]
