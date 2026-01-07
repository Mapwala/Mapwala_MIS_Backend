from django.db import models
from django.contrib.auth.models import User


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    accepted_terms = models.BooleanField(default=False)
    accepted_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.user.username


class State(models.Model):
    STATUS_CHOICES = (
        ("active", "Active"),
        ("inactive", "Inactive"),
    )

    name = models.CharField(max_length=100, unique=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return self.name


class District(models.Model):
    STATUS_CHOICES = (
        ("active", "Active"),
        ("inactive", "Inactive"),
    )

    name = models.CharField(max_length=100)
    code = models.CharField(max_length=10)
    state = models.ForeignKey(State, on_delete=models.CASCADE, related_name="districts")
    status = models.CharField(max_length=10, choices=STATUS_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("code", "state")
        ordering = ["id"]

    def __str__(self):
        return self.name


class ParentCompany(models.Model):
    name = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=15)
    email = models.EmailField()
    address = models.TextField()

    state = models.ForeignKey(State, on_delete=models.PROTECT)
    district = models.ForeignKey(District, on_delete=models.PROTECT)

    bank_name = models.CharField(max_length=255)
    account_holder_name = models.CharField(max_length=255)
    account_number = models.CharField(max_length=50)
    ifsc_code = models.CharField(max_length=20)

    gst_number = models.CharField(max_length=20)
    gst_document = models.FileField(upload_to="documents/gst/")

    tan_number = models.CharField(max_length=20)
    tan_document = models.FileField(upload_to="documents/tan/")

    pan_number = models.CharField(max_length=20)
    pan_document = models.FileField(upload_to="documents/pan/")

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["gst_number"]),
            models.Index(fields=["pan_number"]),
        ]

    def __str__(self):
        return self.name


class Vendor(models.Model):
    name = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=15)
    email = models.EmailField()
    address = models.TextField()

    state = models.ForeignKey(State, on_delete=models.PROTECT)
    district = models.ForeignKey(District, on_delete=models.PROTECT)

    bank_name = models.CharField(max_length=255)
    account_holder_name = models.CharField(max_length=255)
    account_number = models.CharField(max_length=50)
    ifsc_code = models.CharField(max_length=20)

    gst_number = models.CharField(max_length=20)
    gst_document = models.FileField(upload_to="documents/vendor/gst/")

    tan_number = models.CharField(max_length=20)
    tan_document = models.FileField(upload_to="documents/vendor/tan/")

    pan_number = models.CharField(max_length=20)
    pan_document = models.FileField(upload_to="documents/vendor/pan/")

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-id"]

    def __str__(self):
        return self.name


class B2CCustomer(models.Model):
    name = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=15)
    email = models.EmailField()
    address = models.TextField()

    state = models.ForeignKey(State, on_delete=models.PROTECT)
    district = models.ForeignKey(District, on_delete=models.PROTECT)

    bank_name = models.CharField(max_length=255)
    account_holder_name = models.CharField(max_length=255)
    account_number = models.CharField(max_length=50)
    ifsc_code = models.CharField(max_length=20)

    gst_number = models.CharField(max_length=20)
    gst_document = models.FileField(upload_to="documents/b2c/gst/")

    tan_number = models.CharField(max_length=20)
    tan_document = models.FileField(upload_to="documents/b2c/tan/")

    pan_number = models.CharField(max_length=20)
    pan_document = models.FileField(upload_to="documents/b2c/pan/")

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-id"]
        indexes = [
            models.Index(fields=["gst_number"]),
            models.Index(fields=["pan_number"]),
            models.Index(fields=["phone_number"]),
        ]

    def __str__(self):
        return f"{self.name} ({self.phone_number})"


class B2BPartner(models.Model):
    partner_name = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=15)
    email = models.EmailField()
    address = models.TextField()

    state = models.ForeignKey(State, on_delete=models.PROTECT)
    district = models.ForeignKey(District, on_delete=models.PROTECT)

    bank_name = models.CharField(max_length=255)
    account_holder_name = models.CharField(max_length=255)
    account_number = models.CharField(max_length=50)
    ifsc_code = models.CharField(max_length=20)

    gst_number = models.CharField(max_length=20)
    gst_document = models.FileField(upload_to="documents/b2b/gst/")

    tan_number = models.CharField(max_length=20)
    tan_document = models.FileField(upload_to="documents/b2b/tan/")

    pan_number = models.CharField(max_length=20)
    pan_document = models.FileField(upload_to="documents/b2b/pan/")

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-id"]
        indexes = [
            models.Index(fields=["gst_number"]),
            models.Index(fields=["pan_number"]),
            models.Index(fields=["phone_number"]),
        ]

    def __str__(self):
        return f"{self.partner_name} ({self.phone_number})"


