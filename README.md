# Mapwala MIS Backend - Complete Project Documentation

**Project Type:** Django REST Framework Backend with JWT Authentication  
**Database:** PostgreSQL  
**Last Updated:** January 13, 2026

---

## 📋 PROJECT OVERVIEW

Mapwala MIS (Management Information System) is a comprehensive backend service designed to manage:
- **User Authentication & Profiles** (JWT-based)
- **Geographical Data** (States & Districts)
- **Business Partners** (B2B, B2C, Distributors, Dealers, Vendors)
- **Manufacturing & Production** (Devices, BOMs, Components)
- **Order Management** (Production Orders, Sales Orders)
- **Inventory Management** (Stock tracking through batches)

---

## 🏗️ PROJECT STRUCTURE

```
Mapwala_MIS_Backend/
├── Mapwala_MIS_Backend/          # Django project settings
│   ├── settings.py               # Configuration & installed apps
│   ├── urls.py                   # Main URL router
│   ├── asgi.py                   # ASGI config
│   └── wsgi.py                   # WSGI config
├── mapwala_mis/                  # Django app (main business logic)
│   ├── models.py                 # Database models (701 lines)
│   ├── views.py                  # API endpoints (564 lines)
│   ├── serializers.py            # DRF serializers (506 lines)
│   ├── urls.py                   # App-specific routes
│   ├── admin.py                  # Django admin config
│   ├── apps.py                   # App configuration
│   ├── tests.py                  # Test cases
│   └── migrations/               # Database migration files
├── requirements.txt              # Python dependencies
├── manage.py                     # Django CLI
├── Dockerfile                    # Docker configuration
├── docker-compose.yml            # Docker Compose config
├── README.md                     # API documentation
└── env_example                   # Environment template
```

---

## 🗄️ DATABASE MODELS (Detailed Overview)

### 1. **User Management**

#### **UserProfile**
- Stores additional user information
- `user`: OneToOne relationship with Django's User model
- `accepted_terms`: Boolean flag for terms acceptance
- `accepted_at`: Timestamp of terms acceptance

---

### 2. **Geographic Models**

#### **State**
- Represents Indian states
- Fields: `name` (unique), `status` (active/inactive), `created_at`
- Relations: One-to-Many with Districts
- Protection: Cannot delete state with linked districts

#### **District**
- Represents districts within states
- Fields: `name`, `code` (unique per state), `state` (FK), `status`, `created_at`
- Unique Constraint: (code, state) - prevents duplicate codes per state
- Relations: Many-to-One with State

---

### 3. **Business Partner Models**

#### **ParentCompany**
- Root company information
- Core Fields: `name`, `phone_number`, `email`, `address`
- Location: `state`, `district` (single location, protected foreign keys)
- Bank Details: `bank_name`, `account_holder_name`, `account_number`, `ifsc_code`
- Tax Docs: `gst_document`, `tan_document`, `pan_document` (uploaded to documents/gst/, etc.)
- Indexed Fields: `gst_number`, `pan_number`

#### **Vendor**
- Supplier/Vendor information
- Similar structure to ParentCompany
- Documents uploaded to: `documents/vendor/gst/`, `documents/vendor/tan/`, `documents/vendor/pan/`
- Ordering: Latest first (id descending)

#### **B2CCustomer** (Business-to-Consumer)
- Individual customer information
- Fields include all standard business details + tax documents
- Documents uploaded to: `documents/b2c/`
- Indexed Fields: `gst_number`, `pan_number`, `phone_number`

#### **B2BPartner** (Business-to-Business)
- Partner company information
- Field name: `partner_name` (instead of just `name`)
- Documents uploaded to: `documents/b2b/`
- Indexed Fields: `gst_number`, `pan_number`, `phone_number`

#### **Manufacturer**
- Manufacturing company
- Minimal: `name` (unique)
- Relations: One-to-Many with Distributors and Dealers

#### **Distributor**
- Distribution network partner
- Core Fields: `name`, `phone_number`, `email`, `address`
- Location: Single registered `state` and `district`
- Linking: `linked_to` (manufacturer), `manufacturer` (FK, optional)
- Authorized Areas: 
  - `authorised_states` (Many-to-Many)
  - `authorised_districts` (Many-to-Many with validation)
- Documents: Same structure as ParentCompany
- Note: Can only be linked to Manufacturer

#### **Dealer**
- Retail/wholesale dealer
- Similar to Distributor but can link to EITHER Manufacturer OR Distributor
- Fields: `linked_to` with choices: "manufacturer" or "distributor"
- Relations:
  - `manufacturer` (FK, optional)
  - `distributor` (FK, optional)
- Authorized Areas: Multi-select states and districts with validation

---

### 4. **Device Manufacturing Models**

#### **Device**
- Master record for device creation
- Status: Draft → Completed (10-step process)
- Fields: `status`, `created_by` (User FK), `created_at`
- One-to-One relations: `info` (DeviceInformation), `bom` (BOM)
- One-to-Many relations: `accessories`, `stickers` (ForeignKey)

#### **DeviceInformation**
- Device specs (Step 1)
- Fields: `make`, `model`, `mrp`, `unit_of_measure`, `version`, `variant`, `state_of_supply`
- One-to-One: device

#### **BOM** (Bill of Materials)
- Master BOM record (Step 2)
- `upload_type`: "individual" or "bulk"
- `bom_file`: Excel file upload (optional, for bulk)
- One-to-One: device
- One-to-Many: components

#### **BOMComponent**
- Individual component in BOM (Step 3)
- Fields: `identification_mark`, `description`, `designator`, `footprint`
- Fields: `volt`, `part_no`, `part_make`, `per_device_quantity`, `remarks`
- Many-to-One: bom

#### **Enclosure** (Step 4)
- Device casing information
- Dimensions: `length`, `breadth`, `height` (Decimal)
- Fields: `color`, `material`, `quantity`, `make`, `part_number`

#### **WireHarness** (Step 5)
- Wiring assembly
- Fields: `number_of_wires`, `specification`, `make`, `part_number`
- One-to-Many: connectors

#### **WireConnector**
- Individual connector in harness
- Fields: `connector_name`, `number_of_pins`, `wire_colors`
- Many-to-One: wire_harness

#### **Battery** (Step 6)
- Battery specifications
- Fields: `capacity`, dimensions (length, breadth, height), `make`, `part_number`

#### **SOSButton** (Step 7)
- SOS button specifications
- Fields: `total_length`, `quantity_per_set`, `make`, `part_number`

#### **Sticker** (Step 8)
- Device stickers/labels (can be multiple)
- Fields: `name`, dimensions (length, breadth), `quantity`, `file`, `make`, `part_number`
- Many-to-One: device

#### **UserManual** (Step 9)
- Device manual/documentation
- Field: `file` (PDF/Document upload)
- One-to-One: device

#### **Accessory** (Step 10)
- Device accessories (can be multiple)
- Fields: `name`, `quantity`, `specifications`, `description`
- Many-to-One: device

---

### 5. **Proforma Invoice Model**

#### **ProformaInvoice**
- Quotation/PI for B2B/B2C/Dealer/Distributor
- Party Selection:
  - `party_type`: "b2b" | "b2c" | "dealer" | "distributor"
  - `b2b_partner`, `b2c_customer`, `dealer`, `distributor` (conditional ForeignKeys)
- Product Details:
  - `product` (FK to Product model)
  - `selling_price`, `discount_percent`, `quantity`
  - `shipping_charges`, `grand_total`
- Delivery:
  - `payment_terms`: "advance" | "on_delivery" | "full" | "partial"
  - `delivery_date`, `delivery_address`, `state`
- Contact:
  - `contact_person_name`, `mobile_no`, `gstn`
- Validation: Only ONE party field must be filled per party_type

---

### 6. **Order Management Models**

#### **OrderEntry**
- Master record for order creation flow
- `user`: Foreign Key to Django User
- `order_type`: "production" | "sales"
- `production_type`: "add_to_stock" | "make_to_order" (conditional)
- `assembly_type`: "fully_outsourced" | "pcb_device" | "pcb_outside_device_inside"
- Status Flags: `is_step1_complete`, `is_step2_complete`

#### **OrderProduct**
- Product/Device Model for ordering (e.g., "GPS Tracker Pro")
- Field: `name` (unique)
- Example: "Product 101", "Product 102" (must match UI dropdown)
- Used in: Sales Orders, Production Orders

#### **OrderBatch**
- Batch-level inventory tracking
- `product`: FK to OrderProduct
- `batch_number`: String identifier per product
- `available_stock`: Current inventory count
- Unique Constraint: (product, batch_number)
- Usage: Each product can have MULTIPLE batches with separate stock

#### **SalesOrder**
- Customer purchase order
- Customer Info: `customer_name`, `customer_type`, `contact_person`, `mobile_no`
- Product + Batch: `product` (FK), `batch` (FK)
- Pricing: `quantity`, `unit_price`, `discount_percent`, `gst_percent`
- Charges: `shipping_charges`, `grand_total`
- Delivery: `delivery_date`, `delivery_address`
- Payment: `payment_mode`, `payment_status`
- Additional: `invoice_number`, `remarks`
- **Method**: `calculate_grand_total()` - calculates: (qty × unit_price - discount) × (1 + gst%) + shipping
- Stock Deduction: Reduces `available_stock` in OrderBatch

---

### 7. **Production & Supplier Models**

#### **SupplierVendor**
- Supplier/Vendor for production orders
- Field: `name` (unique)
- Dropdown usage for sourcing

#### **ProductionOrder**
- Manufacturing/Add-to-Stock order
- `production_type`: "add_to_stock"
- `product`: FK to OrderProduct
- `product_category`: "gps_devices" | "tracking_devices" | "iot_devices" | "accessories" | "components"
- Quantities: `quantity_added`, `unit_price`, `total_value`
- Sourcing: `supplier_vendor` (FK)
- Dates: `purchase_date`, `manufacturing_date`
- Batch: FK to OrderBatch (auto-create if needed)
- **Method**: `calculate_total_value()` - qty × unit_price
- Stock Addition: Increases `available_stock` in OrderBatch

---

## 🔌 API ENDPOINTS

### **Authentication**
- `POST /api/auth/login/`
  - Input: username, password, accepted_terms
  - Output: JWT access_token (24h validity), user info
  - Auth: AllowAny

### **Location Management**
- `GET/POST /api/states/` - List/Create states
- `GET /api/states/active/` - Active states only
- `DELETE /api/states/{id}/` - Delete with district validation
- `GET/POST /api/districts/` - List/Create districts
- `GET /api/districts/?state={state_id}` - Filter by state

### **Company Management**
- `GET/POST /api/parent-companies/` - Parent company CRUD
- `GET/POST /api/vendors/` - Vendor CRUD

### **Registration APIs**
- `POST /api/b2c/register/` - B2C Customer registration
- `POST /api/b2b/register/` - B2B Partner registration
- `POST /api/distributor/register/` - Distributor registration
- `POST /api/dealer/register/` - Dealer registration
- All support multipart file uploads (documents)
- Returns: created entity ID, name, email/contact

### **Device Creation (10-Step Process)**
- `POST /api/devices/step-1/` - Device info (DeviceInformation)
- `POST /api/devices/step-2/` - BOM (Bill of Materials)
- `POST /api/devices/step-3/` - BOM Components (array)
- `POST /api/devices/step-4/` - Enclosure
- `POST /api/devices/step-5/` - Wire Harness + Connectors
- `POST /api/devices/step-6/` - Battery
- `POST /api/devices/step-7/` - SOS Button
- `POST /api/devices/step-8/` - Stickers (multipart array)
- `POST /api/devices/step-9/` - User Manual
- `POST /api/devices/step-10/` - Accessories (array) + mark as completed

### **Proforma Invoice**
- `POST /api/pi/create/` - Create Proforma Invoice
- Input: party_type + party selection + product details
- Returns: pi_id, grand_total

### **Order Management**
- `POST /api/order-entry/step-1/` - Order entry initialization
- `GET /api/order-products/` - Product dropdown
- `GET /api/order-batches/?product_id={id}` - Batch dropdown
- `POST /api/sales-orders/create/` - Create sales order
  - Reduces batch stock
  - Returns: order_id, remaining_stock
- `POST /api/production-orders/add-to-stock/` - Production order
  - Increases batch stock
  - Returns: production_order_id, current_stock

### **Dropdowns**
- `GET /api/dropdowns/products/` - All products for selection
- `GET /api/dropdowns/suppliers/` - All suppliers/vendors
- `GET /api/dropdowns/product-categories/` - Hardcoded category list

---

## 📝 SERIALIZERS BREAKDOWN

### **Authentication**
- `LoginSerializer`: Validates username, password, terms acceptance. Returns authenticated user.

### **Location**
- `StateSerializer`: id, name, status
- `DistrictSerializer`: id, name, code, state, state_name, status (includes state name)

### **Registrations**
- `B2CCustomerRegistrationSerializer`: 16 fields including documents
- `B2BPartnerRegistrationSerializer`: 16 fields (partner_name instead of name)
- `DistributorRegistrationSerializer`: 21 fields + authorised_states/districts
- `DealerRegistrationSerializer`: 21 fields + manufacturer/distributor FK selection

### **Device Steps (1-10)**
- `DeviceInformationSerializer`: Device specs excluding device FK
- `BOMSerializer`: Upload type + file (validates bulk/individual)
- `BOMComponentSerializer`: Component fields excluding bom FK
- `EnclosureSerializer`: Dimensions, material, quantity
- `WireConnectorSerializer`: Connector details
- `WireHarnessSerializer`: Nested connector serializer with create method
- `BatterySerializer`: Capacity and dimensions
- `SOSButtonSerializer`: SOS button specs
- `StickerSerializer`: Sticker details (multiple allowed)
- `UserManualSerializer`: Manual file upload
- `AccessorySerializer`: Accessory details (multiple allowed)

### **Order Management**
- `OrderEntryStep1Serializer`: order_type, production_type, assembly_type
- `OrderProductSerializer`: id, name (dropdown)
- `OrderBatchSerializer`: id, batch_number, available_stock
- `SalesOrderCreateSerializer`:
  - Input: product_device_model (string), batch (string)
  - Resolves to actual product/batch objects
  - Validates stock availability
  - Validates grand_total calculation
- `ProductionOrderCreateSerializer`:
  - Input: product_device_model, batch_number, supplier_vendor_id
  - Auto-creates batch if needed
  - Validates total_value calculation

### **Proforma Invoice**
- `ProformaInvoiceCreateSerializer`: All fields, validates single party selection

---

## 🔐 AUTHENTICATION & PERMISSIONS

- **JWT-based**: Access tokens with 24-hour validity
- **Token Structure**: Bearer token in Authorization header
- **Authentication Classes**: JWTAuthentication
- **Default Permissions**: IsAuthenticated on most endpoints
- **AllowAny**: Login endpoint only

### **Key Security Features**
- 24-hour token expiration
- No refresh token (single access token only)
- Terms acceptance tracking
- User profile created on login

---

## 🛠️ VALIDATION LOGIC

### **Location Validation**
- District must belong to its parent State
- State cannot be deleted if districts exist

### **Registration Validation**
- District state ID must match selected state
- Distributor must link to Manufacturer (required when linked_to="manufacturer")
- Dealer must link to EITHER Manufacturer OR Distributor (not both, not neither)
- Authorized districts must belong to selected authorized states

### **Device Validation**
- BOM upload_type: If "bulk" → file required; If "individual" → no file allowed
- File uploads: Documents stored in organized folder structure

### **Order Validation**
- Product must exist in OrderProduct table
- Batch must belong to selected product
- Stock check: Requested quantity ≤ available_stock
- Grand total calculation: Must match backend computation
- Supplier must exist in SupplierVendor table

### **Proforma Invoice Validation**
- Exactly ONE party field must be filled (rest must be null/empty)
- Party type must match the filled party field

---

## 💾 DATABASE CONSTRAINTS

- **Unique Constraints**:
  - State.name
  - District (code, state)
  - OrderProduct.name
  - OrderBatch (product, batch_number)
  - SupplierVendor.name
  - Manufacturer.name
  - ParentCompany: Indexes on GST/PAN numbers

- **Foreign Key Protection**:
  - on_delete=PROTECT: Prevents deletion if children exist
  - on_delete=CASCADE: Deletes children when parent deleted
  - on_delete=SET_NULL: Only if field is nullable

---

## 📦 DEPENDENCIES

**Key Packages**:
- Django 6.0 - Web framework
- djangorestframework 3.16.1 - REST API framework
- djangorestframework-simplejwt 5.5.1 - JWT authentication
- psycopg2-binary 2.9.11 - PostgreSQL adapter
- django-jazzmin 3.0.1 - Admin interface enhancement
- python-dotenv 1.2.1 - Environment variables
- dj-database-url 3.1.0 - Database URL parsing

---

## 🔧 CONFIGURATION

### **Django Settings**
- **DEBUG**: Controlled via .env (DEBUG=True/False)
- **ALLOWED_HOSTS**: * (all hosts allowed)
- **Installed Apps**: jazzmin, admin, auth, contenttypes, sessions, messages, staticfiles, rest_framework, mapwala_mis
- **Authentication**: JWTAuthentication
- **Default Permission**: IsAuthenticated
- **CORS**: Not explicitly configured (all origins)

### **JWT Configuration**
- **ACCESS_TOKEN_LIFETIME**: 24 hours
- **REFRESH_TOKEN_LIFETIME**: 0 seconds (no refresh)
- **AUTH_HEADER_TYPES**: Bearer

### **Admin Interface (Jazzmin)**
- **Site Title**: Mapwala MIS Admin
- **Icons**: Custom icons for models
- **Search Models**: User, Group, ParentCompany, Vendor, B2CCustomer, B2BPartner

---

## 📊 WORKFLOW EXAMPLES

### **Example 1: B2B Registration → Proforma Invoice → Sales Order**

1. **Register B2B Partner**
   ```
   POST /api/b2b/register/
   Body: partner_name, contact details, documents
   Returns: partner_id
   ```

2. **Create Proforma Invoice**
   ```
   POST /api/pi/create/
   Body: party_type="b2b", b2b_partner=<id>, product_id, qty, prices
   Returns: pi_id, grand_total
   ```

3. **Create Sales Order**
   ```
   POST /api/sales-orders/create/
   Body: product_device_model="Product 101", batch="BATCH-001", qty, prices
   Returns: order_id, remaining_stock (decremented)
   ```

### **Example 2: Device Creation (10 Steps)**

1. Step 1: POST device info → device_id
2. Step 2: POST BOM with device_id
3. Step 3: POST BOM components with device_id
4. Steps 4-9: POST individual components/files
5. Step 10: POST accessories array, mark device as "completed"

### **Example 3: Production Order (Add to Stock)**

1. **Create Production Order**
   ```
   POST /api/production-orders/add-to-stock/
   Body: product_device_model, batch_number, supplier_vendor_id, qty, prices
   Returns: production_order_id, current_stock (incremented)
   ```

2. **Stock Updated**
   - OrderBatch.available_stock += quantity_added
   - Batch auto-created if doesn't exist

---

## 🚀 DEPLOYMENT NOTES

- **Docker Support**: Dockerfile and docker-compose.yml provided
- **Media Root**: Configured for document uploads
- **Static Files**: Basic static configuration
- **Database**: PostgreSQL with connection pooling (conn_max_age=600)
- **Environment Variables**: .env file required (see env_example)

---

## ✅ COMPLETE UNDERSTANDING CHECKLIST

- ✅ **Models**: All 31 models thoroughly documented
- ✅ **Relationships**: Foreign keys, many-to-many, one-to-one mapped
- ✅ **APIs**: All 30+ endpoints with methods and parameters documented
- ✅ **Serializers**: 20+ serializers with validation rules
- ✅ **Authentication**: JWT implementation with 24h tokens
- ✅ **Business Logic**: Multi-step device creation, order workflows, stock management
- ✅ **Validation**: Comprehensive validation at serializer level
- ✅ **Database Constraints**: Unique together, indexes, protection modes
- ✅ **Permissions**: IsAuthenticated on protected endpoints
- ✅ **Configuration**: Django settings, JWT config, Jazzmin admin
- ✅ **File Uploads**: Multipart handling for documents and files
- ✅ **Transactions**: Atomic transactions for stock management

---

This documentation represents a complete understanding of the Mapwala MIS Backend project as of January 13, 2026.
