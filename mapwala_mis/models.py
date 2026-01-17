from django.db import models
# from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal
from django.contrib.auth import get_user_model

User = get_user_model()


# ---------------- User Profile ----------------
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    accepted_terms = models.BooleanField(default=False)
    accepted_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.user.username


# ---------------- State ----------------
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


# ---------------- District ----------------
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


# ---------------- Parent Company ----------------
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


# ---------------- Vendor ----------------
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


# ---------------- B2C Customer ----------------
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


# ---------------- B2B Partner ----------------
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


# ---------------- Manufacturer ----------------
class Manufacturer(models.Model):
    name = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.name


# ---------------- Distributor ----------------
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


# ---------------- Dealer ----------------
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


# ---------------- Product ----------------
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


# ---------------- Device ----------------
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


# ---------------- Device Information ----------------
class DeviceInformation(models.Model):
    device = models.OneToOneField(Device, on_delete=models.CASCADE, related_name="info")
    make = models.CharField(max_length=255)
    model = models.CharField(max_length=255)
    mrp = models.DecimalField(max_digits=10, decimal_places=2)
    unit_of_measure = models.CharField(max_length=50)
    version = models.CharField(max_length=50)
    variant = models.CharField(max_length=50)
    state_of_supply = models.CharField(max_length=100)


# ---------------- BOM ----------------
class BOM(models.Model):
    UPLOAD_TYPE_CHOICES = (
        ("individual", "Individual Entry"),
        ("bulk", "Bulk Upload"),
    )
    device = models.OneToOneField(Device, on_delete=models.CASCADE, related_name="bom")
    upload_type = models.CharField(max_length=20, choices=UPLOAD_TYPE_CHOICES)
    bom_file = models.FileField(upload_to="bom/excel/",null=True,blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


# ---------------- BOM Component ----------------
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


# ---------------- Enclosure ----------------
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


# ---------------- Wire Harness ----------------
class WireHarness(models.Model):
    device = models.OneToOneField(Device, on_delete=models.CASCADE)
    number_of_wires = models.PositiveIntegerField()
    specification = models.CharField(max_length=255)
    make = models.CharField(max_length=100)
    part_number = models.CharField(max_length=100)


# ---------------- Wire Connector ----------------
class WireConnector(models.Model):
    wire_harness = models.ForeignKey(WireHarness,on_delete=models.CASCADE,related_name="connectors")
    connector_name = models.CharField(max_length=100)
    number_of_pins = models.PositiveIntegerField()
    wire_colors = models.CharField(max_length=255)


# ------------------ Battery ----------------
class Battery(models.Model):
    device = models.OneToOneField(Device, on_delete=models.CASCADE)
    capacity = models.CharField(max_length=100)
    length = models.DecimalField(max_digits=8, decimal_places=2)
    breadth = models.DecimalField(max_digits=8, decimal_places=2)
    height = models.DecimalField(max_digits=8, decimal_places=2)
    make = models.CharField(max_length=100)
    part_number = models.CharField(max_length=100)

# ---------------- SOS Button ----------------
class SOSButton(models.Model):
    device = models.OneToOneField(Device, on_delete=models.CASCADE)
    total_length = models.DecimalField(max_digits=8, decimal_places=2)
    quantity_per_set = models.PositiveIntegerField()
    make = models.CharField(max_length=100)
    part_number = models.CharField(max_length=100)


# ---------------- Sticker ----------------
class Sticker(models.Model):
    device = models.ForeignKey(Device, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    length = models.DecimalField(max_digits=8, decimal_places=2)
    breadth = models.DecimalField(max_digits=8, decimal_places=2)
    quantity = models.PositiveIntegerField()
    file = models.FileField(upload_to="documents/device/stickers/")
    make = models.CharField(max_length=100)
    part_number = models.CharField(max_length=100)


# ---------------- User Manual ----------------
class UserManual(models.Model):
    device = models.OneToOneField(Device, on_delete=models.CASCADE)
    file = models.FileField(upload_to="documents/device/manuals/")


# ---------------- Accessories ----------------
class Accessory(models.Model):
    device = models.ForeignKey(Device, on_delete=models.CASCADE, related_name="accessories")
    name = models.CharField(max_length=255)
    quantity = models.PositiveIntegerField()
    specifications = models.CharField(max_length=255)
    description = models.TextField()


# ---------------- Proforma Invoice ----------------
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
class OrderEntry(models.Model):
    ORDER_TYPE_CHOICES = (
        ("production", "Production Order"),
        ("sales", "Sales Order"),
    )

    PRODUCTION_TYPE_CHOICES = (
        ("add_to_stock", "Add to Stock"),
        ("make_to_order", "Make to Order"),
    )

    ASSEMBLY_TYPE_CHOICES = (
        ("fully_outsourced", "Fully Outsourced"),
        ("pcb_device", "PCB + Device"),
        ("pcb_outside_device_inside", "PCB Outside, Device Inside"),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    order_type = models.CharField(max_length=20, choices=ORDER_TYPE_CHOICES)
    production_type = models.CharField(max_length=20, choices=PRODUCTION_TYPE_CHOICES, null=True, blank=True)
    assembly_type = models.CharField(max_length=30, choices=ASSEMBLY_TYPE_CHOICES, null=True, blank=True)
    is_step1_complete = models.BooleanField(default=False)
    is_step2_complete = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)


# ---------------- Order Product ----------------
class OrderProduct(models.Model):
    """
    Product / Device Model shown in UI
    Example: GPS Tracker Pro, GPS Tracker Standard
    """
    name = models.CharField(max_length=100,unique=True,verbose_name="Product / Device Model")
    class Meta:
        ordering = ["name"]
        verbose_name = "Order Product"
        verbose_name_plural = "Order Products"

    def __str__(self):
        return self.name


# ---------------- Order Batch ----------------
class OrderBatch(models.Model):
    """
    Each product can have MULTIPLE batches.
    Each batch maintains ITS OWN stock.
    """
    product = models.ForeignKey(OrderProduct,on_delete=models.PROTECT,related_name="batches")
    batch_number = models.CharField(max_length=50)
    available_stock = models.PositiveIntegerField()
    class Meta:
        unique_together = ("product", "batch_number")
        ordering = ["batch_number"]
        verbose_name = "Order Batch"
        verbose_name_plural = "Order Batches"

    def __str__(self):
        return f"{self.product.name} | {self.batch_number}"


# ---------------- Sales Order ----------------
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
    discount_percent = models.DecimalField(max_digits=5,decimal_places=2,validators=[MinValueValidator(0), MaxValueValidator(100)],default=0)
    gst_percent = models.DecimalField(max_digits=5,decimal_places=2,validators=[MinValueValidator(0), MaxValueValidator(100)])
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


# --------------------------------Supplier / Vendor------------------------------
class SupplierVendor(models.Model):
    """
    Supplier / Vendor dropdown
    """
    name = models.CharField(max_length=255, unique=True)
    class Meta:
        ordering = ["name"]
        verbose_name = "Supplier / Vendor"
        verbose_name_plural = "Suppliers / Vendors"

    def __str__(self):
        return self.name


# -----------------------------Production Order------------------------------
class ProductionOrder(models.Model):
    PRODUCTION_TYPE_CHOICES = (
        ("add_to_stock", "Add to Stock"),
    )

    PRODUCT_CATEGORY_CHOICES = (
        ("gps_devices", "GPS Devices"),
        ("tracking_devices", "Tracking Devices"),
        ("iot_devices", "IoT Devices"),
        ("accessories", "Accessories"),
        ("components", "Components"),
    )
    production_type = models.CharField(max_length=20,choices=PRODUCTION_TYPE_CHOICES)
    product = models.ForeignKey(OrderProduct, on_delete=models.PROTECT)
    product_category = models.CharField(max_length=30,choices=PRODUCT_CATEGORY_CHOICES)
    quantity_added = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    total_value = models.DecimalField(max_digits=12, decimal_places=2)
    supplier_vendor = models.ForeignKey(SupplierVendor,on_delete=models.PROTECT)
    purchase_date = models.DateField()
    manufacturing_date = models.DateField()
    batch = models.ForeignKey(OrderBatch, on_delete=models.PROTECT)
    remarks = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    def calculate_total_value(self):
        return Decimal(self.quantity_added) * self.unit_price

    def __str__(self):
        return f"ProductionOrder-{self.id}"


# ---------------- Order Entry - Make To Order ----------------
class OrderEntryMakeToOrder(models.Model):
    CUSTOMER_TYPE_CHOICES = (
        ("b2b", "B2B Partner"),
        ("b2c", "B2C Customer"),
        ("distributor", "Distributor"),
        ("dealer", "Dealer"),
    )
    PAYMENT_TERMS_CHOICES = (
        ("100_advance", "100% Advance"),
        ("50_50", "50% Advance, 50% on Delivery"),
        ("30_70", "30% Advance, 70% on Delivery"),
        ("net_30", "Net 30 Days"),
        ("net_60", "Net 60 Days"),
        ("custom", "Custom Terms"),
    )
    PRIORITY_CHOICES = (
        ("low", "Low"),
        ("medium", "Medium"),
        ("high", "High"),
        ("urgent", "Urgent"),
    )
    order_entry = models.OneToOneField(OrderEntry, on_delete=models.CASCADE, related_name="make_to_order")
    customer_name = models.CharField(max_length=255)
    customer_type = models.CharField(max_length=20, choices=CUSTOMER_TYPE_CHOICES)
    contact_person = models.CharField(max_length=255)
    mobile_no = models.CharField(max_length=15)
    product = models.ForeignKey(OrderProduct, on_delete=models.PROTECT)
    product_specifications = models.TextField(blank=True)
    customization_details = models.TextField(blank=True)
    quantity = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    expected_delivery_date = models.DateField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    discount_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    gst_percent = models.DecimalField(max_digits=5, decimal_places=2)
    shipping_charges = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    grand_total = models.DecimalField(max_digits=12, decimal_places=2)
    advance_payment = models.DecimalField(max_digits=12, decimal_places=2)
    payment_terms = models.CharField(max_length=20, choices=PAYMENT_TERMS_CHOICES)
    order_priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES)
    special_instructions = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


# ---------------- Request For Quote (RFQ) ----------------
class RequestForQuote(models.Model):
    STATUS_CHOICES = (
        ("draft", "Draft"),
        ("submitted", "Submitted"),
    )

    ASSEMBLY_TYPE_CHOICES = (
        ("pcb_assembly", "PCB Assembly"),
        ("device_assembly", "Device Assembly"),
    )

    SRN_CHOICES = (
        ("SRN001", "Standard Requirement - Basic GPS"),
        ("SRN002", "Advanced Requirement - GPS + IoT"),
        ("SRN003", "Premium Requirement - Full Suite"),
        ("SRN004", "Custom Requirement - Specialized"),
    )
    # STEP 1
    order_reference = models.CharField(max_length=100)
    device_name = models.CharField(max_length=255)
    assembly_type = models.CharField(max_length=30, choices=ASSEMBLY_TYPE_CHOICES)
    quantity = models.PositiveIntegerField()
    # STEP 3
    srn_no = models.CharField(max_length=20, choices=SRN_CHOICES, null=True, blank=True)
    delivery_date = models.DateField(null=True, blank=True)
    delivery_address = models.TextField(null=True, blank=True)
    additional_requirements = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="draft")
    created_by = models.ForeignKey(User, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"RFQ-{self.id} | {self.order_reference}"


# ---------------- RFQ Selection ----------------
class RFQSelection(models.Model):
    ITEM_TYPE_CHOICES = (
        ("bom", "BOM Part"),
        ("component", "Component"),
        ("service", "Service"),
    )
    rfq = models.ForeignKey(RequestForQuote,on_delete=models.CASCADE,related_name="selections")
    item_type = models.CharField(max_length=20, choices=ITEM_TYPE_CHOICES)
    reference = models.CharField(
        max_length=255,
        help_text="Selected BOM ID / Component name / Service name"
    )


# ---------------- Create Purchase Order ----------------
class PurchaseOrder(models.Model):
    """
    Main entity: Create Purchase Order
    """
    ASSEMBLY_TYPE_CHOICES = (
        ("pcb", "PCB Assembly"),
        ("device", "Device Assembly"),
    )
    PAYMENT_TERMS_CHOICES = (
        ("full_payment", "Full Payment"),
        ("down_payment", "Down Payment"),
        ("advance", "Advance"),
        ("30_days", "30 Days Net"),
        ("60_days", "60 Days Net"),
        ("90_days", "90 Days Net"),
        ("cod", "Cash on Delivery"),
    )
    # ---------- STEP 1 ----------
    buyer_name = models.CharField(max_length=255)
    order_id = models.CharField(max_length=50)
    rfq_id = models.CharField(max_length=50)
    assembly_type = models.CharField(max_length=20,choices=ASSEMBLY_TYPE_CHOICES)
    # ---------- STEP 2 ----------
    wastage_percentage = models.PositiveIntegerField(null=True, blank=True)
    selected_vendor_id = models.CharField(max_length=50, null=True, blank=True)
    delivery_date = models.DateField(null=True, blank=True)
    payment_terms = models.CharField(max_length=20,choices=PAYMENT_TERMS_CHOICES,null=True,blank=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"PO-{self.id} | {self.order_id}"


# ---------------- Purchase Order Type ----------------
class PurchaseOrderType(models.Model):
    """
    Stores multi-select Order Types from UI
    """

    ORDER_TYPE_CHOICES = (
        ("bom", "Items (BOM Parts)"),
        ("component", "Components (Enclosure, Battery, etc.)"),
        ("service", "Services (Assembly, Quality Check, etc.)"),
    )
    purchase_order = models.ForeignKey(PurchaseOrder,on_delete=models.CASCADE,related_name="order_types")
    order_type = models.CharField(max_length=20,choices=ORDER_TYPE_CHOICES)

    class Meta:
        unique_together = ("purchase_order", "order_type")


# ---------------- Purchase Order Item ----------------
class PurchaseOrderItem(models.Model):
    """
    Selected items / components / services
    """
    ITEM_TYPE_CHOICES = (
        ("bom", "BOM Item"),
        ("component", "Component"),
        ("service", "Service"),
    )
    purchase_order = models.ForeignKey(PurchaseOrder,on_delete=models.CASCADE,related_name="items")
    item_code = models.CharField(max_length=50)
    item_type = models.CharField(max_length=20, choices=ITEM_TYPE_CHOICES)
    vendor_id = models.CharField(max_length=50)
    vendor_name = models.CharField(max_length=255)
    quantity = models.PositiveIntegerField(default=0)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    gst_amount = models.DecimalField(max_digits=10, decimal_places=2)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    delivery_days = models.PositiveIntegerField()


# ---------------- Material Receipt Note (MRN) ----------------
class MaterialReceiptNote(models.Model):
    INWARD_TYPE_CHOICES = (
        ("bom_items", "BOM Items"),
        ("materials", "Materials"),
        ("assembled_pcb", "Assembled PCB"),
        ("assembled_device", "Assembled Device"),
    )
    purchase_order = models.ForeignKey("PurchaseOrder",on_delete=models.PROTECT,related_name="mrns")
    po_date = models.DateField()
    vendor = models.ForeignKey(Vendor,on_delete=models.PROTECT,related_name="mrns")
    inward_type = models.CharField(max_length=30,choices=INWARD_TYPE_CHOICES)
    receipt_date = models.DateField()
    batch_number = models.CharField(max_length=50, unique=True)
    invoice_number = models.CharField(max_length=50, blank=True)
    delivery_challan_number = models.CharField(max_length=50, blank=True)
    eway_bill_number = models.CharField(max_length=50, blank=True)
    invoice_file = models.FileField(upload_to="mrn/invoice/", null=True, blank=True)
    challan_file = models.FileField(upload_to="mrn/challan/", null=True, blank=True)
    eway_bill_file = models.FileField(upload_to="mrn/eway/", null=True, blank=True)
    remarks = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"MRN-{self.id} | PO-{self.purchase_order.order_id}"


# ---------------- Material Receipt Item ----------------
class MaterialReceiptItem(models.Model):
    mrn = models.ForeignKey(MaterialReceiptNote,on_delete=models.CASCADE,related_name="items")
    purchase_order_item = models.ForeignKey("PurchaseOrderItem",on_delete=models.PROTECT,related_name="mrn_items")
    received_qty = models.PositiveIntegerField()
    serial_numbers = models.TextField(help_text="Comma separated serial numbers",blank=True)
    balance_qty = models.PositiveIntegerField()
    def save(self, *args, **kwargs):
        """
        Balance Qty = Ordered Qty - Total Received Qty (across all MRNs)
        """
        ordered_qty = self.purchase_order_item.quantity
        total_received = (
            MaterialReceiptItem.objects
            .filter(purchase_order_item=self.purchase_order_item)
            .exclude(pk=self.pk)
            .aggregate(models.Sum("received_qty"))["received_qty__sum"] or 0
        )
        self.balance_qty = ordered_qty - (total_received + self.received_qty)
        if self.balance_qty < 0:
            raise ValueError("Received quantity exceeds ordered quantity")
        super().save(*args, **kwargs)


# ---------------- Dispatch Workflow ----------------
class Dispatch(models.Model):
    """
    Dispatch workflow main model.
    """
    STATUS_CHOICES = (
        ("draft", "Draft"),
        ("completed", "Completed"),
    )
    ORDER_TYPE_CHOICES = (
        ("distributor", "Distributor"),
        ("dealer", "Dealer"),
        ("b2c", "B2C Customer"),
    )

    # ---------------- STEP 1 ----------------
    sales_order = models.ForeignKey(SalesOrder,on_delete=models.PROTECT,related_name="dispatches")
    order_type = models.CharField(max_length=20,choices=ORDER_TYPE_CHOICES)
    # ---------------- STEP 2 ----------------
    product = models.ForeignKey(OrderProduct,on_delete=models.PROTECT,null=True,blank=True)
    batch = models.ForeignKey(OrderBatch,on_delete=models.PROTECT,null=True,blank=True)
    dispatch_quantity = models.PositiveIntegerField(validators=[MinValueValidator(1)],null=True,blank=True)
    imei_number = models.CharField(max_length=50, blank=True)
    serial_number = models.CharField(max_length=50, blank=True)
    iccid_number = models.CharField(max_length=50, blank=True)
    # ---------------- STEP 3 ----------------
    dispatch_date = models.DateField(null=True, blank=True)
    dispatch_remarks = models.TextField(blank=True)
    # ---------------- STEP 4 ----------------
    customer_name = models.CharField(max_length=255, null=True, blank=True)
    customer_contact = models.CharField(max_length=15, null=True, blank=True)
    customer_email = models.EmailField(null=True, blank=True)
    customer_address = models.TextField(null=True, blank=True)

    urgent_delivery_required = models.BooleanField(default=False)
    insurance_required = models.BooleanField(default=False)

    # ---------------- WORKFLOW CONTROL ----------------
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="draft"
    )

    stock_deducted = models.BooleanField(default=False)

    # ---------------- SYSTEM ----------------
    created_by = models.ForeignKey(User, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-id"]

    def __str__(self):
        return f"Dispatch-{self.id} | {self.status.upper()}"


# ---------------- Post-Dispatch Returns Management ----------------
class PostDispatchReturn(models.Model):
    """
    Main model representing a post-dispatch return entry.
    One record per return request.
    """
    RETURN_TYPE_CHOICES = (
        ("full", "Full Return (All Items)"),
        ("partial", "Partial Return (Some Items)"),
        ("replacement", "Return for Replacement"),
    )
    RETURN_REASON_CHOICES = (
        ("damaged", "Damaged in Transit"),
        ("defective", "Defective Product"),
        ("wrong_item", "Wrong Item Delivered"),
        ("rejected", "Customer Rejection"),
        ("quality", "Quality Issues"),
        ("spec_mismatch", "Specification Mismatch"),
        ("other", "Other"),
    )
    # Dispatch reference information (read-only in UI)
    dispatch_id = models.CharField(max_length=50)
    invoice_no = models.CharField(max_length=50)
    customer_name = models.CharField(max_length=255)
    dispatch_total_value = models.DecimalField(max_digits=12,decimal_places=2)
    # Return details
    return_type = models.CharField(max_length=20,choices=RETURN_TYPE_CHOICES)
    return_reason = models.CharField(max_length=20,choices=RETURN_REASON_CHOICES)
    return_date = models.DateField()
    return_remarks = models.TextField(blank=True)
    # Calculated field
    total_return_amount = models.DecimalField(max_digits=12,decimal_places=2,default=0)
    # System fields
    created_by = models.ForeignKey(User,on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-id"]

    def __str__(self):
        return f"PostDispatchReturn-{self.id}"


# ---------------- Post-Dispatch Return Item ----------------
class PostDispatchReturnItem(models.Model):
    """
    Line items selected for return.
    """
    post_dispatch_return = models.ForeignKey(PostDispatchReturn,on_delete=models.CASCADE,related_name="items")
    product_id = models.CharField(max_length=50)
    description = models.CharField(max_length=255)
    dispatched_qty = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=10,decimal_places=2)
    return_qty = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    return_amount = models.DecimalField(max_digits=12, decimal_places=2)

    def __str__(self):
        return f"{self.product_id} | Return Qty: {self.return_qty}"


# ---------------- Module Management Account Registration ----------------
class AccountRegistration(models.Model):
    account_name = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=15)
    email = models.EmailField()
    address = models.TextField()
    state = models.ForeignKey(State, on_delete=models.PROTECT, related_name="account_registrations")
    district = models.ForeignKey(District, on_delete=models.PROTECT, related_name="account_registrations")
    aadhar_number = models.CharField(max_length=20)
    aadhar_document = models.FileField(upload_to="documents/aadhar/")
    pan_number = models.CharField(max_length=20)
    pan_document = models.FileField(upload_to="documents/pan/")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.account_name


# ---------------- Module Management QC Inspector Registration ----------------
class QCInspectorRegistration(models.Model):
    qc_inspector_name = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=15)
    email = models.EmailField()
    address = models.TextField()
    state = models.ForeignKey(State, on_delete=models.PROTECT, related_name="qc_inspectors")
    district = models.ForeignKey(District, on_delete=models.PROTECT, related_name="qc_inspectors")
    aadhar_number = models.CharField(max_length=20)
    aadhar_document = models.FileField(upload_to="documents/qc_inspector/aadhar/")
    pan_number = models.CharField(max_length=20)
    pan_document = models.FileField(upload_to="documents/qc_inspector/pan/")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.qc_inspector_name


# ---------------- Module Management Purchase Department Registration ----------------
class PurchaseDepartmentRegistration(models.Model):
    purchase_department_name = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=15)
    email = models.EmailField()
    address = models.TextField()
    state = models.ForeignKey(State, on_delete=models.PROTECT, related_name="purchase_departments")
    district = models.ForeignKey(District, on_delete=models.PROTECT, related_name="purchase_departments")
    aadhar_number = models.CharField(max_length=20)
    aadhar_document = models.FileField(upload_to="documents/purchase_department/aadhar/")
    pan_number = models.CharField(max_length=20)
    pan_document = models.FileField(upload_to="documents/purchase_department/pan/")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.purchase_department_name


# ---------------- Module Management Store Manager Registration ----------------
class StoreManagerRegistration(models.Model):
    store_manager_name = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=15)
    email = models.EmailField()
    address = models.TextField()
    state = models.ForeignKey(State, on_delete=models.PROTECT, related_name="store_managers")
    district = models.ForeignKey(District, on_delete=models.PROTECT, related_name="store_managers")
    aadhar_number = models.CharField(max_length=20)
    aadhar_document = models.FileField(upload_to="documents/store_manager/aadhar/")
    pan_number = models.CharField(max_length=20)
    pan_document = models.FileField(upload_to="documents/store_manager/pan/")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.store_manager_name


# ---------------- Module Management Repair Technician Registration ----------------
class RepairTechnicianRegistration(models.Model):
    repair_technician_name = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=15)
    email = models.EmailField()
    address = models.TextField()
    state = models.ForeignKey(State, on_delete=models.PROTECT, related_name="repair_technicians")
    district = models.ForeignKey(District, on_delete=models.PROTECT, related_name="repair_technicians")
    aadhar_number = models.CharField(max_length=20)
    aadhar_document = models.FileField(upload_to="documents/repair_technician/aadhar/")
    pan_number = models.CharField(max_length=20)
    pan_document = models.FileField(upload_to="documents/repair_technician/pan/")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.repair_technician_name


# ---------------- Store Transfer (Inventory Data) ----------------
class StoreTransfer(models.Model):
    DISPATCH_STATUS_CHOICES = (
        ("dispatched", "Dispatched"),
        ("non_dispatched", "Non-dispatched"),
        ("return", "Return"),
    )
    
    # Product Information
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name="store_transfers")
    product_name = models.CharField(max_length=255)
    category = models.ForeignKey('ProductCategory', on_delete=models.PROTECT, null=True, blank=True, related_name="store_transfers")
    # Transfer Details
    transfer_id = models.CharField(max_length=50, unique=True)
    mrn_number = models.CharField(max_length=50, null=True, blank=True)
    batch_number = models.CharField(max_length=50)
    # Vendor & Quantity
    vendor = models.ForeignKey(Vendor, on_delete=models.PROTECT, related_name="store_transfers")
    quantity = models.IntegerField(validators=[MinValueValidator(1)])
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    total_value = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0)])
    # Dates & Status
    transfer_date = models.DateField()
    dispatch_status = models.CharField(max_length=20, choices=DISPATCH_STATUS_CHOICES, default="non_dispatched")
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="created_store_transfers")
    
    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=['transfer_id']),
            models.Index(fields=['batch_number']),
            models.Index(fields=['dispatch_status']),
            models.Index(fields=['transfer_date']),
        ]
    
    def __str__(self):
        return f"Transfer {self.transfer_id} - {self.product_name}"


# -------------------- ProductCategory Model (if not exists) --------------------
class ProductCategory(models.Model):
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name_plural = "Product Categories"
        ordering = ['name']
    
    def __str__(self):
        return self.name


# ============================================================
# DEBIT NOTES & CREDIT NOTES - ACCOUNT MANAGEMENT
# ============================================================
class DebitNote(models.Model):
    """
    Debit Note for vendor returns, disputes, penalties, etc.
    """
    REASON_CHOICES = (
        ("vendor_rejected_return", "Vendor Rejected Return"),
        ("quality_dispute", "Quality Dispute"),
        ("late_delivery_penalty", "Late Delivery Penalty"),
        ("specification_mismatch", "Specification Mismatch"),
        ("warranty_claim_denied", "Warranty Claim Denied"),
        ("other", "Other"),
    )
    
    STATUS_CHOICES = (
        ("pending", "Pending"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
        ("processed", "Processed"),
    )
    
    # Auto-generated number in format DN-YYYY-NNN
    number = models.CharField(max_length=20, unique=True, db_index=True)
    date = models.DateField()
    vendor = models.CharField(max_length=255)
    reason = models.CharField(max_length=50, choices=REASON_CHOICES)
    amount = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0)])
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending", db_index=True)
    reference_document = models.CharField(max_length=255, blank=True, help_text="e.g., RTN-001, PO-001")
    remarks = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name="created_debit_notes")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["date"]),
            models.Index(fields=["vendor"]),
        ]
    
    def __str__(self):
        return f"{self.number} - {self.vendor}"


# ---------------- Credit Note ----------------
class CreditNote(models.Model):
    """
    Credit Note for customer returns, discounts, refunds, etc.
    """
    REASON_CHOICES = (
        ("return_accepted", "Return Accepted"),
        ("discount_adjustment", "Discount Adjustment"),
        ("overpayment_refund", "Overpayment Refund"),
        ("quality_issue", "Quality Issue"),
        ("price_correction", "Price Correction"),
        ("other", "Other"),
    )
    
    STATUS_CHOICES = (
        ("pending", "Pending"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
        ("processed", "Processed"),
    )
    
    # Auto-generated number in format CN-YYYY-NNN
    number = models.CharField(max_length=20, unique=True, db_index=True)
    date = models.DateField()
    customer = models.CharField(max_length=255)
    reason = models.CharField(max_length=50, choices=REASON_CHOICES)
    amount = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0)])
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending", db_index=True)
    reference_document = models.CharField(max_length=255, blank=True, help_text="e.g., INV-001, RTN-001")
    remarks = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name="created_credit_notes")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["date"]),
            models.Index(fields=["customer"]),
        ]
    
    def __str__(self):
        return f"{self.number} - {self.customer}"


# ---------------- Note Sequence ----------------
class NoteSequence(models.Model):
    """
    Maintains year-wise running sequence for Debit & Credit Notes
    """
    NOTE_TYPE_CHOICES = (
        ("debit", "Debit Note"),
        ("credit", "Credit Note"),
    )
    year = models.PositiveIntegerField()
    note_type = models.CharField(max_length=10, choices=NOTE_TYPE_CHOICES)
    last_number = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ("year", "note_type")

    def __str__(self):
        return f"{self.note_type.upper()}-{self.year}: {self.last_number}"


