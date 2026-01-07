from django.contrib.auth import authenticate
from rest_framework import serializers
from .models import State, District, UserProfile, ParentCompany, Vendor, B2CCustomer, B2BPartner


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
        fields = ["id", "name", "code", "state", "state_name", "status"]


class ParentCompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = ParentCompany
        fields = "__all__"

    def validate(self, data):
        if data["district"].state_id != data["state"].id:
            raise serializers.ValidationError(
                "Selected district does not belong to selected state."
            )
        return data


class VendorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vendor
        fields = "__all__"

    def validate(self, data):
        if data["district"].state_id != data["state"].id:
            raise serializers.ValidationError(
                "Selected district does not belong to the selected state."
            )
        return data


class B2CCustomerRegistrationSerializer(serializers.ModelSerializer):
    class Meta:
        model = B2CCustomer
        fields = ["name","phone_number","email","address","state","district","bank_name","account_holder_name","account_number","ifsc_code","gst_number","gst_document","tan_number","tan_document","pan_number","pan_document",]

    def validate(self, data):
        state = data.get("state")
        district = data.get("district")

        if district.state_id != state.id:
            raise serializers.ValidationError(
                {"district": "Selected district does not belong to selected state."}
            )

        return data


class B2BPartnerRegistrationSerializer(serializers.ModelSerializer):
    class Meta:
        model = B2BPartner
        fields = ["partner_name","phone_number","email","address","state","district","bank_name","account_holder_name","account_number","ifsc_code","gst_number","gst_document","tan_number","tan_document","pan_number","pan_document",]

    def validate(self, data):
        state = data.get("state")
        district = data.get("district")

        if district.state_id != state.id:
            raise serializers.ValidationError({
                "district": "Selected district does not belong to selected state."
            })

        return data



