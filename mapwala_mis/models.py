from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal


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


class Manufacturer(models.Model):
    name = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.name


class Distributor(models.Model):
    LINKED_TO_CHOICES = (
        ("manufacturer", "Manufacturer"),
    )
    # Basic details
    name = models.CharField(max_length=255,verbose_name="Distributor Name")
    phone_number = models.CharField(max_length=15,verbose_name="Phone Number")
    email = models.EmailField(verbose_name="Email Address")
    address = models.TextField(verbose_name="Address")
    # Physical location (single)
    state = models.ForeignKey(State,on_delete=models.PROTECT,related_name="distributors",verbose_name="Registered State",help_text="State where the distributor is officially registered.")
    district = models.ForeignKey(District,on_delete=models.PROTECT,related_name="distributors",verbose_name="Registered District",help_text="District where the distributor is officially registered.")
    # Bank details
    bank_name = models.CharField(max_length=255, verbose_name="Bank Name")
    account_holder_name = models.CharField(max_length=255, verbose_name="Account Holder Name")
    account_number = models.CharField(max_length=50, verbose_name="Bank Account Number")
    ifsc_code = models.CharField(max_length=20, verbose_name="IFSC Code")
    # Tax details
    gst_number = models.CharField(max_length=20,verbose_name="GST Number")
    gst_document = models.FileField(upload_to="documents/distributor/gst/",verbose_name="GST Document")
    tan_number = models.CharField(max_length=20,verbose_name="TAN Number")
    tan_document = models.FileField(upload_to="documents/distributor/tan/",verbose_name="TAN Document")
    pan_number = models.CharField(max_length=20,verbose_name="PAN Number")
    pan_document = models.FileField(upload_to="documents/distributor/pan/",verbose_name="PAN Document")
    # Business linking
    linked_to = models.CharField(max_length=50,choices=LINKED_TO_CHOICES,verbose_name="Linked To",help_text="Defines the entity this distributor is linked to.")
    manufacturer = models.ForeignKey(Manufacturer,on_delete=models.PROTECT,null=True,blank=True,related_name="distributors",verbose_name="Linked Manufacturer",help_text="Required when Linked To is Manufacturer.")
    # Authorised operating area (MULTI-SELECT)
    authorised_states = models.ManyToManyField(State,related_name="authorised_distributors",blank=True,verbose_name="Authorised Operating States",help_text="States where this distributor is allowed to operate.")
    authorised_districts = models.ManyToManyField(District,related_name="authorised_distributors",blank=True,verbose_name="Authorised Operating Districts",help_text=(
            "Districts where this distributor is allowed to operate. "
            "Each district must belong to one of the selected authorised states."
        ))
    # System info
    created_at = models.DateTimeField(auto_now_add=True,verbose_name="Created At")

    def __str__(self):
        return self.name


class Dealer(models.Model):
    LINKED_TO_CHOICES = (
        ("manufacturer", "Manufacturer"),
        ("distributor", "Distributor"),
    )
    # Basic details
    name = models.CharField(max_length=255,verbose_name="Dealer Name")
    phone_number = models.CharField(max_length=15,verbose_name="Phone Number")
    email = models.EmailField(verbose_name="Email Address")
    address = models.TextField(verbose_name="Address")
    # Physical location (single)
    state = models.ForeignKey(State,on_delete=models.PROTECT,related_name="dealers",verbose_name="Registered State",help_text="State where the dealer is officially registered.")
    district = models.ForeignKey(District,on_delete=models.PROTECT,related_name="dealers",verbose_name="Registered District",help_text="District where the dealer is officially registered.")
    # Bank details
    bank_name = models.CharField(max_length=255,verbose_name="Bank Name")
    account_holder_name = models.CharField(max_length=255,verbose_name="Account Holder Name")
    account_number = models.CharField(max_length=50,verbose_name="Bank Account Number")
    ifsc_code = models.CharField(max_length=20,verbose_name="IFSC Code")
    # Tax details
    gst_number = models.CharField(max_length=20,verbose_name="GST Number")
    gst_document = models.FileField(upload_to="documents/dealer/gst/",verbose_name="GST Document")
    tan_number = models.CharField(max_length=20,verbose_name="TAN Number")
    tan_document = models.FileField(upload_to="documents/dealer/tan/",verbose_name="TAN Document")
    pan_number = models.CharField(max_length=20,verbose_name="PAN Number")
    pan_document = models.FileField(upload_to="documents/dealer/pan/",verbose_name="PAN Document")
    # Business linking
    linked_to = models.CharField(max_length=20,choices=LINKED_TO_CHOICES,verbose_name="Linked To",help_text="Choose whether this dealer is linked to a Manufacturer or Distributor.")
    manufacturer = models.ForeignKey(Manufacturer,on_delete=models.PROTECT,null=True,blank=True,related_name="dealers",verbose_name="Linked Manufacturer",help_text="Required when Linked To is Manufacturer.")
    distributor = models.ForeignKey(Distributor,on_delete=models.PROTECT,null=True,blank=True,related_name="dealers",verbose_name="Linked Distributor",help_text="Required when Linked To is Distributor.")
    # Authorised operating area (MULTI)
    authorised_states = models.ManyToManyField(State,related_name="authorised_dealers",blank=True,verbose_name="Authorised Operating States",help_text="States where this dealer is allowed to operate.")
    authorised_districts = models.ManyToManyField(District,related_name="authorised_dealers",blank=True,verbose_name="Authorised Operating Districts",
        help_text=(
            "Districts where this dealer is allowed to operate. "
            "Each district must belong to one of the selected authorised states."
        ))
    # System info
    created_at = models.DateTimeField(auto_now_add=True,verbose_name="Created At")
    class Meta:
        ordering = ["-id"]
        verbose_name = "Dealer"
        verbose_name_plural = "Dealers"

    def __str__(self):
        return self.name


class Product(models.Model):
    # product_id = models.PositiveIntegerField(unique=True,verbose_name="Product ID",help_text="Numeric Product ID shown in PI screen (e.g. 101, 102)")
    product_id = models.CharField(max_length=20,unique=True,verbose_name="Product ID",help_text="Numeric Product ID shown in PI screen (e.g. 101, 102)")
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        ordering = ["product_id"]
        verbose_name = "Product"
        verbose_name_plural = "Products"

    def __str__(self):
        # EXACT match with UI dropdown
        return f"Product {self.product_id}"


class Device(models.Model):
    STATUS_CHOICES = (
        ("draft", "Draft"),
        ("completed", "Completed"),
    )

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="draft")
    created_by = models.ForeignKey(User, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Device-{self.id}"


class DeviceInformation(models.Model):
    device = models.OneToOneField(Device, on_delete=models.CASCADE, related_name="info")

    make = models.CharField(max_length=255)
    model = models.CharField(max_length=255)
    mrp = models.DecimalField(max_digits=10, decimal_places=2)

    unit_of_measure = models.CharField(max_length=50)
    version = models.CharField(max_length=50)
    variant = models.CharField(max_length=50)
    state_of_supply = models.CharField(max_length=100)


class BOM(models.Model):
    UPLOAD_TYPE_CHOICES = (
        ("individual", "Individual Entry"),
        ("bulk", "Bulk Upload"),
    )

    device = models.OneToOneField(Device, on_delete=models.CASCADE, related_name="bom")

    upload_type = models.CharField(max_length=20, choices=UPLOAD_TYPE_CHOICES)

    bom_file = models.FileField(
        upload_to="bom/excel/",
        null=True,
        blank=True
    )

    created_at = models.DateTimeField(auto_now_add=True)


class BOMComponent(models.Model):
    bom = models.ForeignKey(BOM, on_delete=models.CASCADE, related_name="components")

    identification_mark = models.CharField(max_length=100)
    description = models.CharField(max_length=255)
    designator = models.CharField(max_length=255)
    footprint = models.CharField(max_length=50)
    volt = models.CharField(max_length=50)
    part_no = models.CharField(max_length=100)
    part_make = models.CharField(max_length=100)
    per_device_quantity = models.PositiveIntegerField()
    remarks = models.CharField(max_length=255, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)


class Enclosure(models.Model):
    device = models.OneToOneField(Device, on_delete=models.CASCADE)

    length = models.DecimalField(max_digits=8, decimal_places=2)
    breadth = models.DecimalField(max_digits=8, decimal_places=2)
    height = models.DecimalField(max_digits=8, decimal_places=2)

    color = models.CharField(max_length=100)
    material = models.CharField(max_length=100)
    quantity = models.PositiveIntegerField()
    make = models.CharField(max_length=100)
    part_number = models.CharField(max_length=100)


class WireHarness(models.Model):
    device = models.OneToOneField(Device, on_delete=models.CASCADE)

    number_of_wires = models.PositiveIntegerField()
    specification = models.CharField(max_length=255)
    make = models.CharField(max_length=100)
    part_number = models.CharField(max_length=100)


class WireConnector(models.Model):
    wire_harness = models.ForeignKey(
        WireHarness,
        on_delete=models.CASCADE,
        related_name="connectors"
    )

    connector_name = models.CharField(max_length=100)
    number_of_pins = models.PositiveIntegerField()
    wire_colors = models.CharField(max_length=255)


class Battery(models.Model):
    device = models.OneToOneField(Device, on_delete=models.CASCADE)

    capacity = models.CharField(max_length=100)
    length = models.DecimalField(max_digits=8, decimal_places=2)
    breadth = models.DecimalField(max_digits=8, decimal_places=2)
    height = models.DecimalField(max_digits=8, decimal_places=2)
    make = models.CharField(max_length=100)
    part_number = models.CharField(max_length=100)


class SOSButton(models.Model):
    device = models.OneToOneField(Device, on_delete=models.CASCADE)

    total_length = models.DecimalField(max_digits=8, decimal_places=2)
    quantity_per_set = models.PositiveIntegerField()
    make = models.CharField(max_length=100)
    part_number = models.CharField(max_length=100)


class Sticker(models.Model):
    device = models.ForeignKey(Device, on_delete=models.CASCADE)

    name = models.CharField(max_length=255)
    length = models.DecimalField(max_digits=8, decimal_places=2)
    breadth = models.DecimalField(max_digits=8, decimal_places=2)
    quantity = models.PositiveIntegerField()
    file = models.FileField(upload_to="documents/device/stickers/")
    make = models.CharField(max_length=100)
    part_number = models.CharField(max_length=100)


class UserManual(models.Model):
    device = models.OneToOneField(Device, on_delete=models.CASCADE)
    file = models.FileField(upload_to="documents/device/manuals/")


class Accessory(models.Model):
    device = models.ForeignKey(Device, on_delete=models.CASCADE, related_name="accessories")

    name = models.CharField(max_length=255)
    quantity = models.PositiveIntegerField()
    specifications = models.CharField(max_length=255)
    description = models.TextField()


class ProformaInvoice(models.Model):
    PARTY_TYPE_CHOICES = (
        ("b2b", "B2B Partner"),
        ("b2c", "B2C Customer"),
        ("dealer", "Dealer"),
        ("distributor", "Distributor"),
    )

    PAYMENT_TERMS_CHOICES = (
        ("advance", "Advance"),
        ("on_delivery", "On Delivery"),
        ("full", "Full Payment"),
        ("partial", "Partial Payment"),
    )

    # Party selection
    party_type = models.CharField(max_length=20, choices=PARTY_TYPE_CHOICES)
    b2b_partner = models.ForeignKey("B2BPartner",on_delete=models.PROTECT,null=True,blank=True)
    b2c_customer = models.ForeignKey("B2CCustomer",on_delete=models.PROTECT,null=True,blank=True)
    dealer = models.ForeignKey("Dealer",on_delete=models.PROTECT,null=True,blank=True)
    distributor = models.ForeignKey("Distributor",on_delete=models.PROTECT,null=True,blank=True)
    # Product
    product = models.ForeignKey("Product",on_delete=models.PROTECT)
    selling_price = models.DecimalField(max_digits=10,decimal_places=2)
    discount_percent = models.DecimalField(max_digits=5,decimal_places=2,validators=[MinValueValidator(0), MaxValueValidator(100)],default=0)
    quantity = models.PositiveIntegerField()
    shipping_charges = models.DecimalField(max_digits=10,decimal_places=2,default=0)
    grand_total = models.DecimalField(max_digits=12,decimal_places=2)
    # Delivery & payment
    payment_terms = models.CharField(max_length=20,choices=PAYMENT_TERMS_CHOICES)
    delivery_date = models.DateField()
    delivery_address = models.TextField()
    state = models.ForeignKey(State, on_delete=models.PROTECT)
    # Contact
    contact_person_name = models.CharField(max_length=255)
    mobile_no = models.CharField(max_length=15)
    gstn = models.CharField(max_length=20, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        ordering = ["-id"]

    def __str__(self):
        return f"PI-{self.id}"


# ---------------- Order Entry ----------------
class OrderProduct(models.Model):
    """
    Product / Device Model shown in UI
    Example: GPS Tracker Pro, GPS Tracker Standard
    """
    name = models.CharField(
        max_length=100,
        unique=True,
        verbose_name="Product / Device Model"
    )

    class Meta:
        ordering = ["name"]
        verbose_name = "Order Product"
        verbose_name_plural = "Order Products"

    def __str__(self):
        return self.name


class OrderBatch(models.Model):
    """
    Each product can have MULTIPLE batches.
    Each batch maintains ITS OWN stock.
    """
    product = models.ForeignKey(
        OrderProduct,
        on_delete=models.PROTECT,
        related_name="batches"
    )
    batch_number = models.CharField(max_length=50)
    available_stock = models.PositiveIntegerField()

    class Meta:
        unique_together = ("product", "batch_number")
        ordering = ["batch_number"]
        verbose_name = "Order Batch"
        verbose_name_plural = "Order Batches"

    def __str__(self):
        return f"{self.product.name} | {self.batch_number}"


class SalesOrder(models.Model):
    CUSTOMER_TYPE_CHOICES = (
        ("b2c", "B2C Customer"),
        ("distributor", "Distributor"),
        ("dealer", "Dealer"),
    )

    PAYMENT_MODE_CHOICES = (
        ("cash", "Cash"),
        ("bank_transfer", "Bank Transfer"),
        ("cheque", "Cheque"),
        ("credit_card", "Credit Card"),
        ("upi", "UPI"),
        ("credit_terms", "Credit Terms"),
    )

    PAYMENT_STATUS_CHOICES = (
        ("paid", "Paid"),
        ("partially_paid", "Partially Paid"),
        ("pending", "Pending"),
        ("on_credit", "On Credit"),
    )

    # Customer
    customer_name = models.CharField(max_length=255)
    customer_type = models.CharField(max_length=20, choices=CUSTOMER_TYPE_CHOICES)
    contact_person = models.CharField(max_length=255)
    mobile_no = models.CharField(max_length=15)

    # Product + Batch (IMPORTANT)
    product = models.ForeignKey(OrderProduct, on_delete=models.PROTECT)
    batch = models.ForeignKey(OrderBatch, on_delete=models.PROTECT)

    quantity = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)

    discount_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        default=0
    )

    gst_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )

    shipping_charges = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    grand_total = models.DecimalField(max_digits=12, decimal_places=2)

    delivery_date = models.DateField()
    delivery_address = models.TextField()

    payment_mode = models.CharField(max_length=20, choices=PAYMENT_MODE_CHOICES)
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES)

    invoice_number = models.CharField(max_length=100, blank=True)
    remarks = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def calculate_grand_total(self):
        base = Decimal(self.quantity) * self.unit_price
        discount = (base * self.discount_percent) / Decimal("100")
        taxable = base - discount
        gst = (taxable * self.gst_percent) / Decimal("100")
        return taxable + gst + self.shipping_charges

    def __str__(self):
        return f"SalesOrder-{self.id}"


