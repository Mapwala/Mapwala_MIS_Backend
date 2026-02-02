# Mapwala MIS Backend - Complete Project Documentation

**Project Type:** Django REST Framework Backend with JWT Authentication  
**Database:** PostgreSQL  
**Last Updated:** January 22, 2026

---

## 📋 PROJECT OVERVIEW

Mapwala MIS (Management Information System) is a comprehensive backend service designed to manage:

- **User Authentication & Profiles** (JWT-based)
- **Geographical Data** (States & Districts)
- **Business Partners** (B2B, B2C, Distributors, Dealers, Vendors)
- **Manufacturing & Production** (Devices, BOMs, Components)
- **Order Management** (Production Orders, Sales Orders, RFQ, Purchase Orders)
- **Inventory Management** (Stock tracking through batches, Store Transfers, MRN)
- **Logistics & Dispatch** (Dispatch workflow, Post-Dispatch Returns)
- **Account Management** (Debit Notes, Credit Notes)
- **Module Management** (QC Inspectors, Purchase Departments, Store Managers, Repair Technicians)

---

## 🏗️ PROJECT STRUCTURE

```
Mapwala_MIS_Backend/
├── 🐳 .dockerignore            # Files excluded from Docker context
├── 🔐 .env                     # Active secrets & environment variables
├── 🙈 .gitignore               # Files ignored by Git
├── 🐳 Dockerfile               # Docker image blueprint
├── ⚙️ Mapwala_MIS_Backend/     # Core Project Configuration
│   ├── 🐍 __init__.py
│   ├── ⚡ asgi.py              # Async entry point (ASGI)
│   ├── 🛠️ settings.py          # Main Django settings
│   ├── 🛣️ urls.py              # Global URL routing
│   └── 🔌 wsgi.py              # Sync entry point (WSGI)
├── 🐙 docker-compose.yml       # Container orchestration config
├── 🚀 entrypoint.sh            # Container startup & init script
├── 📋 env_example              # Template for environment variables
├── 🕹️ manage.py                # Django CLI utility
├── 📦 mapwala_mis/             # Main Application Logic
│   ├── 🐍 __init__.py
│   ├── 🛡️ admin.py             # Admin panel configuration
│   ├── 🧩 apps.py              # App metadata
│   ├── 🎨 jazzmin_patch.py     # Admin theme customization
│   ├── 🗃️ migrations/          # Database schema history
│   ├── 🛢️ models.py            # Database models (Schema)
│   ├── 🔄 serializers.py       # JSON Serializers (DRF)
│   ├── 🧪 tests.py             # Unit & Integration tests
│   ├── 🔗 urls.py              # App-specific routes
│   ├── 🧰 utils.py             # Helper functions
│   └── 🧠 views.py             # API Business logic
└── 📥 requirements.txt         # Python dependencies
```

---

## 🗄️ DATABASE MODELS (Detailed Overview - 50+ Models)

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
- Documents uploaded to: `documents/b2c/gst/`, `documents/b2c/tan/`, `documents/b2c/pan/`
- Indexed Fields: `gst_number`, `pan_number`, `phone_number`

#### **B2BPartner** (Business-to-Business)

- Partner company information
- Field name: `partner_name` (instead of just `name`)
- Documents uploaded to: `documents/b2b/gst/`, `documents/b2b/tan/`, `documents/b2b/pan/`
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

### 6. **Product & Inventory Models**

#### **Product**

- Master product record
- Fields: `product_id` (unique, CharField), `created_at`
- String representation: "Product {product_id}"
- Usage: Base for ordering and inventory

#### **OrderProduct**

- Product/Device Model for ordering (e.g., "GPS Tracker Pro")
- Field: `name` (unique)
- Example: "Product 101", "Product 102" (must match UI dropdown)
- Used in: Sales Orders, Production Orders, Make-to-Order
- Ordering: By name

#### **OrderBatch**

- Batch-level inventory tracking
- `product`: FK to OrderProduct
- `batch_number`: String identifier per product
- `available_stock`: Current inventory count
- Unique Constraint: (product, batch_number)
- Usage: Each product can have MULTIPLE batches with separate stock
- Ordering: By batch_number

#### **SupplierVendor**

- Supplier/Vendor dropdown for production orders
- Field: `name` (unique)
- Ordering: By name

#### **ProductCategory**

- Product categorization
- Fields: `name` (unique), `description`, `created_at`
- Ordering: By name
- Related: One-to-Many with StoreTransfer

---

### 7. **Order Management Models**

#### **OrderEntry**

- Master record for order creation flow
- `user`: Foreign Key to Django User
- `order_type`: "production" | "sales"
- `production_type`: "add_to_stock" | "make_to_order" (conditional)
- `assembly_type`: "fully_outsourced" | "pcb_device" | "pcb_outside_device_inside"
- Status Flags: `is_step1_complete`, `is_step2_complete`

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

#### **OrderEntryMakeToOrder**

- Make-to-Order workflow with advanced customization
- Customer Info: `customer_name`, `customer_type`, `contact_person`, `mobile_no`
- Product Customization: `product_specifications`, `customization_details`
- Quantities: `quantity`, `unit_price`, `discount_percent`, `gst_percent`
- Payment: `advance_payment`, `payment_terms` (100% advance, 50/50, etc.)
- Priority: `order_priority` (low, medium, high, urgent)
- Expected Delivery: `expected_delivery_date`
- Additional: `special_instructions`, `grand_total`

---

### 8. **RFQ (Request For Quote) Models**

#### **RequestForQuote**

- Request for quotation management
- STEP 1: `order_reference`, `device_name`, `assembly_type`, `quantity`
- STEP 3: `srn_no`, `delivery_date`, `delivery_address`, `additional_requirements`
- Status: "draft" | "submitted"
- Relations: One-to-Many with RFQSelection

#### **RFQSelection**

- Selected items for RFQ
- Fields: `item_type` (bom, component, service), `reference` (BOM ID / Component name / Service name)
- Many-to-One: request_for_quote

---

### 9. **Purchase Order Models**

#### **PurchaseOrder**

- Main PO entity with 2-step workflow
- STEP 1: `buyer_name`, `order_id`, `rfq_id`, `assembly_type`
- STEP 2: `wastage_percentage`, `selected_vendor_id`, `delivery_date`, `payment_terms`
- Created by: User FK
- Relations: One-to-Many with PurchaseOrderItem, PurchaseOrderType

#### **PurchaseOrderType**

- Multi-select Order Types from UI
- Choices: "bom" (Items), "component" (Components), "service" (Services)
- Unique Constraint: (purchase_order, order_type)

#### **PurchaseOrderItem**

- Line items in PO
- Fields: `item_code`, `item_type`, `vendor_id`, `vendor_name`
- Quantities: `quantity`, `unit_price`, `gst_amount`, `total_price`
- Delivery: `delivery_days`
- Many-to-One: purchase_order

---

### 10. **Material Receipt Note (MRN) Models**

#### **MaterialReceiptNote**

- GRN/Goods Receipt Note
- `purchase_order` (FK), `po_date`, `vendor` (FK)
- `inward_type`: bom_items, materials, assembled_pcb, assembled_device
- `receipt_date`, `batch_number` (unique)
- Documents: `invoice_file`, `challan_file`, `eway_bill_file`
- Fields: `invoice_number`, `delivery_challan_number`, `eway_bill_number`, `remarks`
- Created by: User FK

#### **MaterialReceiptItem**

- Individual items received in MRN
- `purchase_order_item` (FK)
- Quantities: `received_qty`, `balance_qty` (auto-calculated)
- Field: `serial_numbers` (comma-separated)
- Many-to-One: material_receipt_note

---

### 11. **Dispatch Workflow Models**

#### **Dispatch**

- Dispatch workflow main model (4-step process)
- Status: "draft" | "completed"
- STEP 1: `sales_order` (FK), `order_type`
- STEP 2: `product` (FK), `batch` (FK), `dispatch_quantity`
- Fields: `imei_number`, `serial_number`, `iccid_number`
- STEP 3: `dispatch_date`, `dispatch_remarks`
- STEP 4: `customer_name`, `customer_contact`, `customer_email`, `customer_address`
- Flags: `urgent_delivery_required`, `insurance_required`, `stock_deducted`
- Created by: User FK

---

### 12. **Post-Dispatch Returns Models**

#### **PostDispatchReturn**

- Post-dispatch return management
- Dispatch Reference: `dispatch_id`, `invoice_no`, `customer_name`, `dispatch_total_value` (read-only)
- Return Details:
  - `return_type`: "full" | "partial" | "replacement"
  - `return_reason`: "damaged", "defective", "wrong_item", "rejected", "quality", "spec_mismatch", "other"
  - `return_date`, `return_remarks`
- Calculated: `total_return_amount`
- Created by: User FK

#### **PostDispatchReturnItem**

- Line items for return
- Fields: `product_id`, `description`, `dispatched_qty`, `unit_price`
- Return Details: `return_qty`, `return_amount`
- Many-to-One: post_dispatch_return

---

### 13. **Inventory Models**

#### **StoreTransfer**

- Inventory data tracking
- Product Info: `product` (FK), `product_name`, `category` (FK to ProductCategory)
- Transfer Details: `transfer_id` (unique), `mrn_number`, `batch_number`
- Vendor & Quantity: `vendor` (FK), `quantity`, `unit_price`, `total_value`
- Dates: `transfer_date`, `created_at`, `updated_at`
- Status: `dispatch_status` ("dispatched", "non_dispatched", "return")
- Metadata: `created_by` (User FK)
- Indexes: transfer_id, batch_number, dispatch_status, transfer_date

---

### 14. **Account Management Models**

#### **DebitNote**

- Debit notes for vendor returns, disputes, penalties
- Fields: `number` (auto-generated: DN-YYYY-NNN), `date`, `vendor`, `amount`
- Reason: "vendor_rejected_return", "quality_dispute", "late_delivery_penalty", "specification_mismatch", "warranty_claim_denied", "other"
- Status: "pending" | "approved" | "rejected" | "processed"
- Reference: `reference_document` (RTN-001, PO-001, etc.)
- Created by: User FK

#### **CreditNote**

- Credit notes for customer returns, discounts, refunds
- Fields: `number` (auto-generated: CN-YYYY-NNN), `date`, `customer`, `amount`
- Reason: "return_accepted", "discount_adjustment", "overpayment_refund", "quality_issue", "price_correction", "other"
- Status: "pending" | "approved" | "rejected" | "processed"
- Reference: `reference_document` (INV-001, RTN-001, etc.)
- Created by: User FK

#### **NoteSequence**

- Maintains year-wise running sequence for DebitNote & CreditNote
- Fields: `year`, `note_type` ("debit" | "credit"), `last_number`
- Unique Constraint: (year, note_type)

---

### 15. **Module Management Registration Models**

#### **AccountRegistration**

- Account holder registration
- Fields: `account_name`, `phone_number`, `email`, `address`
- Location: `state` (FK), `district` (FK)
- Documents: `aadhar_number`, `aadhar_document`, `pan_number`, `pan_document`

#### **QCInspectorRegistration**

- QC Inspector registration
- Fields: `qc_inspector_name`, `phone_number`, `email`, `address`
- Location: `state` (FK), `district` (FK)
- Documents: `aadhar_number`, `aadhar_document`, `pan_number`, `pan_document`

#### **PurchaseDepartmentRegistration**

- Purchase Department registration
- Fields: `purchase_department_name`, `phone_number`, `email`, `address`
- Location: `state` (FK), `district` (FK)
- Documents: `aadhar_number`, `aadhar_document`, `pan_number`, `pan_document`

#### **StoreManagerRegistration**

- Store Manager registration
- Fields: `store_manager_name`, `phone_number`, `email`, `address`
- Location: `state` (FK), `district` (FK)
- Documents: `aadhar_number`, `aadhar_document`, `pan_number`, `pan_document`

#### **RepairTechnicianRegistration**

- Repair Technician registration
- Fields: `repair_technician_name`, `phone_number`, `email`, `address`
- Location: `state` (FK), `district` (FK)
- Documents: `aadhar_number`, `aadhar_document`, `pan_number`, `pan_document`

## 🔌 API ENDPOINTS (60+ Endpoints)

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
- `GET /api/dropdowns/states/` - States dropdown
- `GET /api/dropdowns/districts/` - Districts dropdown

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

### **Module Management Registrations**

- `POST /api/account/register/` - Account holder registration
- `POST /api/qc-inspectors/register/` - QC Inspector registration
- `POST /api/purchase-departments/register/` - Purchase Department registration
- `POST /api/store-managers/register/` - Store Manager registration

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
- `POST /api/order-entry/step-2/` - Order entry step 2
- `GET /api/order-products/` - Product dropdown
- `GET /api/order-batches/?product_id={id}` - Batch dropdown
- `POST /api/sales-orders/create/` - Create sales order
  - Reduces batch stock
  - Returns: order_id, remaining_stock
- `POST /api/production-orders/add-to-stock/` - Production order
  - Increases batch stock
  - Returns: production_order_id, current_stock
- `GET /api/dropdowns/products/` - All products for selection
- `GET /api/dropdowns/suppliers/` - All suppliers/vendors
- `GET /api/dropdowns/product-categories/` - Hardcoded category list
- `GET /api/dropdowns/customer-types/` - Customer type choices
- `GET /api/dropdowns/payment-terms/` - Payment terms choices
- `GET /api/dropdowns/order-priority/` - Order priority levels
- `GET /api/dropdowns/sales-orders/` - Sales orders dropdown

### **RFQ (Request For Quote) Management**

- `POST /api/rfq/step-1/` - RFQ Step 1 (device & assembly info)
- `POST /api/rfq/step-2/` - RFQ Step 2 (selected items)
- `POST /api/rfq/step-3/` - RFQ Step 3 (delivery & requirements)
- `GET /api/dropdowns/quote-types/` - Quote type choices
- `GET /api/dropdowns/assembly-types/` - Assembly type choices
- `GET /api/dropdowns/srn/` - SRN choices (Standard Requirement Numbers)
- `GET /api/dropdowns/vendors/` - Vendors dropdown

### **Purchase Order Management**

- `POST /api/purchase/step-1/` - PO Step 1 (buyer & order info)
- `POST /api/purchase/step-2/` - PO Step 2 (vendor & terms)
- `GET /api/dropdowns/order-types/` - Order type choices (BOM, Component, Service)
- `GET /api/dropdowns/assembly-types/` - Assembly type choices
- `GET /api/dropdowns/payment-terms/` - Payment term choices

### **Material Receipt Note (MRN)**

- `POST /api/mrn/create/` - Create MRN
- `GET /api/dropdowns/purchase-orders/` - Purchase orders dropdown
- `GET /api/dropdowns/inward-types/` - Inward type choices
- `GET /api/purchase/{po_id}/items/` - Get PO items by purchase order ID

### **Dispatch Workflow (4-Step Process)**

- `POST /api/dispatch/step-1/` - Dispatch Step 1 (select sales order)
- `POST /api/dispatch/step-2/{dispatch_id}/` - Dispatch Step 2 (select product & batch)
- `POST /api/dispatch/step-3/{dispatch_id}/` - Dispatch Step 3 (dispatch date & remarks)
- `POST /api/dispatch/step-4/{dispatch_id}/` - Dispatch Step 4 (customer details & completion)
- `GET /api/dropdowns/dispatch-order-types/` - Dispatch order type choices
- `GET /api/dropdowns/dispatch-products/` - Products dropdown for dispatch
- `GET /api/dropdowns/dispatch-batches/` - Batches dropdown for dispatch

### **Post-Dispatch Returns Management**

- `POST /api/returns/post-dispatch/create/` - Create post-dispatch return
- `GET /api/dropdowns/return-types/` - Return type choices (Full, Partial, Replacement)
- `GET /api/dropdowns/return-reasons/` - Return reason choices

### **Account Management - Debit & Credit Notes**

- `GET /api/account-management/dashboard/` - Account management dashboard
- `GET /api/debit-notes/reasons/` - Debit note reason choices
- `GET /api/credit-notes/reasons/` - Credit note reason choices
- `GET /api/notes/statuses/` - Note status choices
- `GET/POST /api/debit-notes/` - Debit Notes CRUD (ViewSet)
- `GET/POST /api/credit-notes/` - Credit Notes CRUD (ViewSet)

### **Inventory Management**

- `GET/POST /api/store-transfers/` - Store transfers CRUD (ViewSet)

### **Product Management**

- `GET/POST /api/product-categories/` - Product categories CRUD (ViewSet)

---

---

## 📝 SERIALIZERS OVERVIEW

The project uses 80+ serializers for request/response validation and data transformation. Serializers ensure data integrity, perform validation, and handle complex nested structures.

### Core Serializers Architecture

- **Model Serializers**: Auto-generate fields from Django models (most common pattern)
- **Custom Serializers**: Manual field definitions for complex workflows (RFQ, Dispatch, Returns)
- **Nested Serializers**: Handle many-to-many and complex relationships
- **Validators**: Custom validation logic for business rules

### Authentication Serializers

#### `LoginSerializer`
- **Purpose**: Handle user authentication with terms acceptance
- **Fields**: `username`, `password`, `accepted_terms`
- **Validation**: Authenticates credentials and enforces terms acceptance

### Location & Company Serializers

#### `StateSerializer`, `DistrictSerializer`
- **Purpose**: Location management serializers
- **Fields**: State name, status, district code, state relationship

#### `ParentCompanySerializer`, `VendorSerializer`
- **Purpose**: Company and vendor information serialization
- **Features**: Validates state-district relationship, checks unique GST numbers

### Registration Serializers (5 Types)

#### 1. **B2CCustomerRegistrationSerializer**
- **Purpose**: B2C customer registration with documents
- **Validation**: Enforces state-district relationship, document uploads
- **Fields**: Customer info, address, banking details, tax documents

#### 2. **B2BPartnerRegistrationSerializer**
- **Purpose**: B2B partner registration
- **Validation**: District-state dependency validation
- **Fields**: Partner name, contact, documents, banking info

#### 3. **DistributorRegistrationSerializer**
- **Purpose**: Distributor registration with authorized areas
- **Validation**: Multi-select district-state validation, manufacturer linkage
- **Fields**: Contact info, documents, authorized states/districts, manufacturer FK

#### 4. **DealerRegistrationSerializer**
- **Purpose**: Dealer registration (linked to Manufacturer OR Distributor)
- **Validation**: Complex linking logic (XOR between manufacturer/distributor)
- **Fields**: Contact info, documents, linked_to field, conditional FKs

#### 5. **Module Management Registration Serializers**
- **AccountRegistrationSerializer**: Account holder registration
- **QCInspectorRegistrationSerializer**: QC inspector registration
- **PurchaseDepartmentRegistrationSerializer**: Purchase department registration
- **StoreManagerRegistrationSerializer**: Store manager registration
- **RepairTechnicianRegistrationSerializer**: Repair technician registration

All module registration serializers:
- **File Validation**: Enforce max file size via `validate_file_size` function
- **Location Validation**: Ensure district belongs to selected state
- **Fields**: Aadhar/PAN documents, location info, contact details

### Device Creation Serializers (10-Step Process)

| Step | Serializer | Purpose | Fields |
|------|-----------|---------|--------|
| 1 | `DeviceInformationSerializer` | Device specs | Make, model, MRP, version, variant, state of supply |
| 2 | `BOMSerializer` | Bill of Materials | Upload type (individual/bulk), file upload |
| 3 | `BOMComponentSerializer` | Individual components | Part details, quantity per device, specifications |
| 4 | `EnclosureSerializer` | Device casing | Dimensions, color, material, make, part number |
| 5a | `WireHarnessSerializer` | Wire assembly | Wire count, specification, make, part number |
| 5b | `WireConnectorSerializer` | Individual connector | Connector name, pin count, wire colors |
| 6 | `BatterySerializer` | Battery specs | Capacity, dimensions, make, part number |
| 7 | `SOSButtonSerializer` | SOS button | Length, quantity, make, part number |
| 8 | `StickerSerializer` | Device stickers | Name, dimensions, quantity, file upload |
| 9 | `UserManualSerializer` | Manual/documentation | File upload (PDF) |
| 10 | `AccessorySerializer` | Device accessories | Name, quantity, specifications, description |

### Order Management Serializers

#### Order Entry
- `OrderEntryStep1Serializer`: Order type selection (Production/Sales)
- `OrderEntryStep2MakeToOrderSerializer`: Make-to-order workflow details

#### Order Dropdowns
- `OrderProductSerializer`: Product/device model selection
- `OrderBatchSerializer`: Batch selection with available stock

#### Sales Order
- `SalesOrderCreateSerializer`
  - **Accepts**: `product_device_model` (string), `batch` (string: batch_number)
  - **Resolves**: Product from name, batch from batch_number
  - **Validates**: Stock availability, grand total calculation
  - **Action**: Decrements `OrderBatch.available_stock`

#### Production Order
- `ProductionOrderCreateSerializer`
  - **Accepts**: `product_device_model`, `batch_number`, `supplier_vendor_id`
  - **Creates**: Auto-creates batch if not exists
  - **Validates**: Total value calculation
  - **Action**: Increments `OrderBatch.available_stock`

### RFQ (Request for Quote) Serializers

#### Three-Step RFQ Workflow
- `RFQStep1Serializer`: Device info, assembly type, quantity
- `RFQStep2Serializer`: Select items (BOM parts, components, services)
- `RFQStep3Serializer`: Vendor selection, delivery details, SRN

#### RFQ Views
- `RFQListSerializer`: List view with vendor names, item counts
- `RFQDetailSerializer`: Full RFQ details with all selections
- `RFQSelectionSerializer`: Individual item selections

### Purchase Order Serializers

#### Two-Step Purchase Order Workflow
- `PurchaseStep1Serializer`: Buyer info, order reference, assembly type, order types
- `PurchaseLineSerializer`: Individual line item details (price, GST, delivery)
- `PurchaseStep2Serializer`: Vendor selection, wastage %, payment terms, items array

### Material Receipt Note (MRN) Serializers

- `MRNCreateSerializer`: MRN creation with multiple items
- `MRNItemSerializer`: Individual MRN line items
- **Features**: Receipt quantity tracking, balance quantity auto-calculation, serial number capture

### Dispatch Workflow Serializers (4-Step)

| Step | Serializer | Purpose |
|------|-----------|---------|
| 1 | `DispatchStep1Serializer` | Select sales order, order type |
| 2 | `DispatchStep2Serializer` | Product, batch, dispatch quantity, IMEI/serial numbers |
| 3 | `DispatchStep3Serializer` | Dispatch date, remarks, urgency flags |
| 4 | `DispatchStep4Serializer` | Customer details, completion |

### Post-Dispatch Return Serializers

- `PostDispatchReturnHeaderSerializer`: Return header (dispatch ref, type, reason, date)
- `PostDispatchReturnItemSerializer`: Individual return items with quantity validation
- `PostDispatchReturnCreateSerializer`: Full return submission with header and items

### Account Management Serializers

#### Debit Notes
- `DebitNoteListSerializer`: List view with vendor, reason, status
- `DebitNoteDetailSerializer`: Full debit note details
- `DebitNoteCreateUpdateSerializer`: Create/update with auto-generated number

#### Credit Notes
- `CreditNoteListSerializer`: List view with customer, reason, status
- `CreditNoteDetailSerializer`: Full credit note details
- `CreditNoteCreateUpdateSerializer`: Create/update with auto-generated number

### Inventory Management Serializers

#### Store Transfer
- `StoreTransferListSerializer`: List view with dispatch status, total value
- `StoreTransferDetailSerializer`: Full details including creator info
- `StoreTransferCreateUpdateSerializer`: Create/update with value validation

#### Product Category
- `ProductCategorySerializer`: Simple category serializer with name, description

### Vendor Management Serializers

#### Return Requests
- `ReturnRequestSerializer`: Complete return request details
- `ReturnRequestListSerializer`: Lightweight list view
- `ReturnRequestCountSerializer`: Status-wise return counts

#### Repair Records
- `RepairRecordSerializer`: Repair tracking with quantity validation
- `RepairRecordListSerializer`: Lightweight repair list

#### Rejected Items
- `RejectedItemSerializer`: QC rejected items tracking
- `RejectedItemListSerializer`: Lightweight rejected items list

### Device Management Serializers

#### Device Views
- `DeviceListSerializer`: Simplified device list (device_id, name, model, status)
- `DeviceDetailSerializer`: Full device details with all components

#### Component Detail Serializers (used in Device detail)
- `EnclosureDetailSerializer`: Enclosure info with formatted dimensions
- `WireHarnessDetailSerializer`: Wire harness with connector details
- `BatteryDetailSerializer`: Battery specs with parsed dimensions
- `SOSButtonDetailSerializer`: SOS button specifications
- `StickerDetailSerializer`: Sticker info with file extraction
- `BOMDetailSerializer`: BOM with component items list
- `UserManualDetailSerializer`: Manual with file URL generation
- `AccessoryDetailSerializer`: Accessory specs

### Self Orders Serializers

- `SelfOrderSerializer`
  - **Purpose**: Self-order creation with automatic GST calculation
  - **Fields**: Device, quantity, rate, GST rate, delivery details
  - **Auto-Calculation**: `gross_amount = (quantity × rate) × (1 + gst_rate%)`

### Quotation Management Serializers

#### Quotation Item
- `QuotationItemSerializer`: Individual quotation line items with GST calculation

#### Quotation Operations
- `QuotationCreateSerializer`: Create quotation from RFQ with items, auto-generates quotation number
- `QuotationListSerializer`: List view with vendor, totals, item count
- `QuotationDetailSerializer`: Full quotation with all items, status
- `QuotationApproveRejectSerializer`: Status update (approve/reject)

### Serializer Validation Patterns

#### 1. **State-District Validation** (Used in 8+ serializers)
```python
if district.state_id != state.id:
    raise ValidationError("District does not belong to state")
```

#### 2. **Quantity Validation** (Sales, Production, Dispatch)
```python
if quantity > available_stock:
    raise ValidationError("Insufficient stock")
```

#### 3. **Grand Total Validation** (Sales, Production, Self Orders)
```python
calculated = (qty × price - discount) × (1 + gst%) + shipping
if calculated != grand_total:
    raise ValidationError("Total mismatch")
```

#### 4. **Linking Logic Validation** (Dealer, Distributor)
```python
# Ensure exactly one party is selected
# Prevent both from being filled simultaneously
```

#### 5. **File Size Validation** (All registrations)
```python
def validate_file_size(file):
    if file.size > settings.FILE_UPLOAD_MAX_MEMORY_SIZE:
        raise ValidationError("File too large")
```

---

---

## � UTILITY FUNCTIONS & HELPERS

### Concurrency-Safe Number Generators

The `utils.py` file provides thread-safe number generators for automatic sequential numbering of business documents:

#### `generate_note_number(note_type: str) -> str`

Generates unique note numbers for Debit and Credit Notes with automatic year-wise sequencing.

- **Format**: `DN-YYYY-NNN` (Debit Note) or `CN-YYYY-NNN` (Credit Note)
- **Thread-Safe**: Uses `select_for_update()` to prevent concurrent duplication
- **Year-Based**: Resets sequence annually
- **Parameters**:
  - `note_type` (str): Either "debit" or "credit"
- **Returns**: Formatted string like "DN-2026-001", "CN-2026-042"
- **Example Usage**:
  ```python
  from mapwala_mis.utils import generate_note_number
  
  # Generate debit note number
  dn_number = generate_note_number("debit")  # Returns: DN-2026-001
  
  # Generate credit note number
  cn_number = generate_note_number("credit")  # Returns: CN-2026-001
  ```

#### `generate_quotation_number() -> str`

Generates unique quotation numbers with automatic year-wise sequencing.

- **Format**: `QT-YYYY-NNN`
- **Thread-Safe**: Uses `select_for_update()` for database-level locking
- **Year-Based**: Resets sequence annually
- **Returns**: Formatted string like "QT-2026-001", "QT-2026-043"
- **Example Usage**:
  ```python
  from mapwala_mis.utils import generate_quotation_number
  
  qt_number = generate_quotation_number()  # Returns: QT-2026-001
  ```

#### Key Features:
- **Database-Level Locking**: Uses PostgreSQL row-level locks to ensure thread safety
- **Atomic Transactions**: All operations wrapped in `transaction.atomic()`
- **Auto-Increment**: Automatically increments `last_number` in sequence table
- **Year Isolation**: Each year maintains its own sequence counter
- **Performance**: Minimal performance impact with direct update operations

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

### **Dispatch Validation**

- Sales order must exist and be in valid state
- Product & batch must match sales order
- Dispatch quantity ≤ sales order quantity
- IMEI/Serial/ICCID numbers: Optional, unique if provided

### **Post-Dispatch Return Validation**

- Dispatch must exist (referenced via dispatch_id)
- Return quantity ≤ dispatched quantity per item
- Return reason must be valid choice
- Total return amount calculated from line items

### **MRN Validation**

- Purchase order must exist
- Vendor must match PO vendor
- Received quantity + total received (from all MRNs) ≤ ordered quantity
- Balance qty auto-calculated: ordered_qty - (total_received + current_received_qty)

### **Account Note Validation**

- Debit Note: Vendor name required, amount > 0
- Credit Note: Customer name required, amount > 0
- Note numbers: Auto-generated in format DN-YYYY-NNN / CN-YYYY-NNN
- Status progression: pending → approved/rejected → processed

---

## 💾 DATABASE CONSTRAINTS

### **Unique Constraints**

- `State.name`
- `District (code, state)`
- `OrderProduct.name`
- `OrderBatch (product, batch_number)`
- `SupplierVendor.name`
- `Manufacturer.name`
- `MaterialReceiptNote.batch_number`
- `StoreTransfer.transfer_id`
- `ProductCategory.name`
- `DebitNote.number` (auto-generated)
- `CreditNote.number` (auto-generated)
- `NoteSequence (year, note_type)`
- `PurchaseOrderType (purchase_order, order_type)`

### **Indexed Fields**

- `State`: id
- `District`: (code, state)
- `ParentCompany`: gst_number, pan_number
- `Vendor`: gst_number, pan_number
- `B2CCustomer`: gst_number, pan_number, phone_number
- `B2BPartner`: gst_number, pan_number, phone_number
- `OrderBatch`: (product, batch_number)
- `StoreTransfer`: transfer_id, batch_number, dispatch_status, transfer_date
- `DebitNote`: status, date, vendor
- `CreditNote`: status, date, customer

### **Foreign Key Protection**

- `on_delete=PROTECT`: Prevents deletion if children exist
  - State (on Districts)
  - OrderProduct (on OrderBatch, SalesOrder, ProductionOrder)
  - Vendor (on MRN)
  - Distributor (on Dealers)
  - SupplierVendor (on ProductionOrder)
- `on_delete=CASCADE`: Deletes children when parent deleted
  - Device (on DeviceInformation, BOM, Enclosure, WireHarness, Battery, SOSButton, UserManual, Sticker, Accessory)
  - BOM (on BOMComponent)
  - OrderEntry (on OrderEntryMakeToOrder)
  - PurchaseOrder (on PurchaseOrderItem, PurchaseOrderType)
  - MaterialReceiptNote (on MaterialReceiptItem)
  - PostDispatchReturn (on PostDispatchReturnItem)
  - RFQ (on RFQSelection)

- `on_delete=SET_NULL`: Only if field is nullable
  - User (on StoreTransfer.created_by)

---

## 📦 DEPENDENCIES

**Key Packages**:

- **Django 6.0** - Web framework
- **djangorestframework 3.16.1** - REST API framework
- **djangorestframework-simplejwt 5.5.1** - JWT authentication
- **psycopg2-binary 2.9.11** - PostgreSQL adapter
- **django-jazzmin 3.0.1** - Admin interface enhancement
- **django-cors-headers 4.9.0** - CORS support
- **python-dotenv 1.2.1** - Environment variables
- **dj-database-url 3.1.0** - Database URL parsing

See `requirements.txt` for complete list with versions.

---

## 🔧 CONFIGURATION

### 🔐 Django Secret Key Setup

Django requires a secure `SECRET_KEY` for cryptographic signing.  
This project does **not** store the secret key in the codebase — it must be generated and stored in a `.env` file.

#### 1️⃣ Generate a secure secret key

From the project root, run:

```bash
python - << 'EOF'
from django.core.management.utils import get_random_secret_key
print(get_random_secret_key())
EOF
```

OR

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

Or, if you are already inside the Django shell:

```python
from django.core.management.utils import get_random_secret_key
print(get_random_secret_key())
```

This will output a long random string — copy it.

#### 2️⃣ Create a .env file

In the project root, create a file named `.env` and add:

```env
SECRET_KEY=your_generated_secret_key_here
DEBUG=True
DATABASE_URL=postgresql://user:password@localhost:5432/mapwala_mis
ALLOWED_HOSTS=localhost,127.0.0.1
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```

Or use individual database settings:

```env
SECRET_KEY=your_generated_secret_key_here
DEBUG=True
DB_ENGINE=django.db.backends.postgresql
DB_NAME=mapwala_mis
DB_USER=postgres
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=5432
ALLOWED_HOSTS=localhost,127.0.0.1
CORS_ALLOWED_ORIGINS=http://localhost:3000
```

⚠️ Do not commit this file — make sure `.env` is in `.gitignore`.

#### 3️⃣ Django will automatically load it

The project loads environment variables using `python-dotenv` inside `settings.py`.
Django will fail to start if `SECRET_KEY` is missing.

#### 🔒 Security Notes

- Never commit or share your `SECRET_KEY`.
- Use a different key for each environment (local, staging, production).
- Rotate the key immediately if it is exposed.

### **Django Settings**

- **DEBUG**: Controlled via .env (DEBUG=True/False)
- **ALLOWED_HOSTS**: From .env (default: localhost)
- **Installed Apps**: jazzmin, admin, auth, contenttypes, sessions, messages, staticfiles, corsheaders, rest_framework, mapwala_mis
- **Authentication**: JWTAuthentication (djangorestframework-simplejwt)
- **Default Permission**: IsAuthenticated on most endpoints
- **CORS**: Configured via CORS_ALLOWED_ORIGINS from .env

### **JWT Configuration**

- **ACCESS_TOKEN_LIFETIME**: 24 hours
- **REFRESH_TOKEN_LIFETIME**: Not used (single access token)
- **AUTH_HEADER_TYPES**: Bearer

### **Database**

- **Engine**: PostgreSQL
- **Configuration**: Via DATABASE*URL or individual DB*\* env variables
- **Connection Pooling**: conn_max_age=600

### **Admin Interface (Jazzmin)**

- **Site Title**: Mapwala MIS Admin
- **Icons**: Custom icons for models
- **Search Models**: User, Group, ParentCompany, Vendor, B2CCustomer, B2BPartner

### **File Uploads**

- **Media Root**: Configured for document uploads
- **Upload Paths**: Organized folder structure (documents/, mrn/, bom/, etc.)

---

## 🛣️ URL ROUTING & API STRUCTURE

The `urls.py` file organizes 70+ API endpoints using Django REST Framework's DefaultRouter and custom URL patterns. All endpoints are organized by business domain for clarity and maintainability.

### Router Configuration

```python
from rest_framework.routers import DefaultRouter

router = DefaultRouter()

# ViewSets (auto-generates CRUD endpoints)
router.register(r'states', StateViewSet)
router.register(r'districts', DistrictViewSet)
router.register(r'vendors', VendorViewSet)
router.register(r'product-categories', ProductCategoryViewSet)
router.register(r'debit-notes', DebitNoteViewSet)
router.register(r'credit-notes', CreditNoteViewSet)
router.register(r'return-requests', ReturnRequestViewSet)
router.register(r'repair-records', RepairRecordViewSet)
router.register(r'rejected-items', RejectedItemViewSet)
router.register(r'devices', DeviceViewSet)
router.register(r'store-transfers', StoreTransferViewSet)

urlpatterns = router.urls
```

### Endpoint Categories

#### 1. **Authentication & Registration** (7 endpoints)
- `POST /api/auth/login/` - User authentication with JWT generation
- `POST /api/b2c/register/` - B2C customer registration
- `POST /api/b2b/register/` - B2B partner registration
- `POST /api/distributor/register/` - Distributor registration
- `POST /api/dealer/register/` - Dealer registration
- Additional module registration endpoints for QC, Purchase, Store, Account roles

#### 2. **Device Management** (12 endpoints)
- `POST /api/devices/step-1/` through `POST /api/devices/step-10/` - 10-step device creation workflow
- `POST /api/device-accessories/` - Device accessory addition
- `GET /api/devices/` - List all devices
- `GET /api/devices/{id}/` - Get full device details with all components

#### 3. **Order Management** (8 endpoints)
- `POST /api/order-entry/step-1/` - Order type selection
- `POST /api/order-entry/step-2/` - Order entry completion
- `POST /api/sales-orders/create/` - Create sales order with stock validation
- `POST /api/production-orders/add-to-stock/` - Add production quantity to inventory
- Related dropdown endpoints for products, batches, customer types, suppliers

#### 4. **RFQ Workflow** (3 endpoints)
- `POST /api/rfq/step-1/` - RFQ initialization (device, quantity, assembly type)
- `POST /api/rfq/step-2/` - Item selection (BOM, components, services)
- `POST /api/rfq/step-3/` - Vendor selection and delivery details
- Additional endpoints: List RFQ, Get RFQ details, Vendor quotations

#### 5. **Purchase Order Workflow** (2 endpoints)
- `POST /api/purchase/step-1/` - Buyer info and order reference
- `POST /api/purchase/step-2/` - Vendor selection and payment terms

#### 6. **Material Receipt Note (MRN)** (1 endpoint + dropdown)
- `POST /api/mrn/create/` - MRN creation with received items
- `GET /api/dropdowns/purchase-orders/` - Purchase orders dropdown
- `GET /api/purchase/{po_id}/items/` - Get purchase order items

#### 7. **Dispatch Workflow** (4 endpoints + dropdowns)
- `POST /api/dispatch/step-1/` - Select sales order
- `POST /api/dispatch/step-2/{dispatch_id}/` - Product and batch selection
- `POST /api/dispatch/step-3/{dispatch_id}/` - Dispatch date and remarks
- `POST /api/dispatch/step-4/{dispatch_id}/` - Customer details and completion

#### 8. **Post-Dispatch Returns** (1 endpoint + dropdowns)
- `POST /api/returns/post-dispatch/create/` - Create return with line items
- Return type and reason dropdown endpoints

#### 9. **Account Management** (3+ endpoints)
- `GET /api/account-management/dashboard/` - Financial dashboard summary
- `GET/POST /api/debit-notes/` - Debit notes CRUD (ViewSet)
- `GET/POST /api/credit-notes/` - Credit notes CRUD (ViewSet)
- Status and reason dropdown endpoints

#### 10. **Quotations** (4 endpoints)
- `POST /api/quotations/create/` - Create quotation from RFQ
- `GET /api/quotations/` - List all quotations
- `GET /api/quotations/{id}/` - Get quotation details
- `POST /api/quotations/{id}/approve-reject/` - Approve or reject quotation

#### 11. **Self Orders** (3 endpoints)
- `POST /api/self-orders/create/` - Create self order
- `GET /api/self-orders/` - List self orders
- `GET /api/self-orders/{id}/` - Get self order details

#### 12. **Location Management** (6 endpoints)
- `GET/POST /api/states/` - States CRUD
- `GET /api/states/active/` - Active states only
- `GET/POST /api/districts/` - Districts CRUD (filterable by state)
- `GET /api/districts/?state={state_id}` - Districts by state filter

#### 13. **Dropdown APIs** (15+ endpoints for form selections)
- **General**: States, Districts, Product categories, Suppliers/vendors
- **Order Related**: Products, Batches, Customer types, Payment modes
- **Device Related**: Assembly types, SRN options, Quote types
- **Dispatch Related**: Order types, Dispatch products, Dispatch batches
- **Return Related**: Return types, Return reasons
- **Note Related**: Debit/Credit note reasons, Note statuses

---

## 🔧 VIEWS & API IMPLEMENTATIONS

The `views.py` file contains 40+ API view classes organized into 13 sections, implementing all business logic and workflows.

### View Types & Patterns

#### 1. **ViewSets** (Django REST Framework CRUD Auto-generation)

ViewSets automatically generate these endpoints:
- `GET /endpoint/` - List all
- `POST /endpoint/` - Create new
- `GET /endpoint/{id}/` - Get detail
- `PUT /endpoint/{id}/` - Full update
- `PATCH /endpoint/{id}/` - Partial update
- `DELETE /endpoint/{id}/` - Delete

**Implemented ViewSets**:
- `StateViewSet` - State management with deletion protection (cannot delete if districts exist)
- `DistrictViewSet` - District management with state filtering
- `ParentCompanyViewSet` - Parent company management
- `VendorViewSet` - Vendor management with GST uniqueness validation
- `ProductCategoryViewSet` - Product category management
- `DebitNoteViewSet` - Debit notes with auto-generated numbers
- `CreditNoteViewSet` - Credit notes with auto-generated numbers
- `ReturnRequestViewSet` - Return request tracking with status filtering
- `RepairRecordViewSet` - Repair tracking with statistics
- `RejectedItemViewSet` - Quality control rejected items tracking
- `DeviceViewSet` - Device viewing (read-only, nested details)
- `StoreTransferViewSet` - Inventory data with dispatch status filtering

#### 2. **Custom APIView Classes**

**Workflow Pattern**: Single responsibility, specific business operation

##### Authentication & Registration (7 views)
- `LoginAPIView` - JWT token generation with user profile creation
- `B2CCustomerRegistrationAPIView` - B2C registration with multipart document upload
- `B2BPartnerRegistrationAPIView` - B2B registration
- `DistributorRegistrationAPIView` - Distributor with authorized areas
- `DealerRegistrationAPIView` - Dealer with conditional linking
- Plus 4 module registration views (Account, QC, Purchase, Store, Repair)

##### Device Creation (10 views - DeviceStep1APIView to DeviceStep10APIView)
- `DeviceStep1APIView` - Device information (make, model, MRP, etc.)
- `DeviceStep2APIView` - BOM upload (individual or bulk Excel)
- `DeviceStep3APIView` - BOM component entry
- `DeviceStep4APIView` - Enclosure specification
- `DeviceStep5APIView` - Wire harness and connectors
- `DeviceStep6APIView` - Battery specification
- `DeviceStep7APIView` - SOS button specification
- `DeviceStep8APIView` - Sticker uploads (multiple files)
- `DeviceStep9APIView` - User manual PDF upload
- `DeviceStep10APIView` - Accessories array + mark device as completed

**Common Pattern**:
```python
def post(self, request):
    # Get existing device or create new
    device = Device.objects.get_or_create(...)
    
    # Validate using serializer
    serializer = DeviceStepXSerializer(data=request.data)
    if serializer.is_valid():
        # Create/update model with device FK
        serializer.save(device=device)
        return Response({"device_id": device.id, "status": "success"})
    return Response(serializer.errors, status=400)
```

##### Order Management (6 views)
- `OrderEntryStep1APIView` - Order type selection (Production/Sales) and assembly type
- `OrderEntryStep2APIView` - Order details completion
- `SalesOrderCreateAPIView` - Create sales order with automatic stock deduction
- `ProductionOrderCreateAPIView` - Add quantity to stock with batch auto-creation
- Related dropdown views for products, batches, customers

##### RFQ Workflow (3 views)
- `RFQStep1APIView` - Initialize RFQ with device and assembly info
- `RFQStep2APIView` - Select items (BOM, components, services)
- `RFQStep3APIView` - Vendor selection and final requirements
- `RFQListAPIView` - List all RFQs with vendor names and item counts
- `RFQDetailAPIView` - Get RFQ with all selections

##### Purchase Order Workflow (2 views)
- `PurchaseOrderStep1APIView` - Buyer and order information
- `PurchaseOrderStep2APIView` - Vendor selection, payment terms, items

##### MRN Management (1 view + dropdowns)
- `MRNCreateAPIView` - Create material receipt note with line items

##### Dispatch Workflow (4 views)
- `DispatchStep1APIView` - Select sales order from list
- `DispatchStep2APIView` - Select product/batch with automatic stock validation
- `DispatchStep3APIView` - Set dispatch date, remarks, and urgency flags
- `DispatchStep4APIView` - Customer details, mark as completed (stock deducted here)

**Key Feature**: Stock deduction happens only at Step 4 completion, not during selection

##### Post-Dispatch Returns (1 view)
- `PostDispatchReturnCreateAPIView` - Create return with header (dispatch ref) and line items (quantities)

##### Account Management (3 views)
- `AccountManagementDashboardAPIView` - Financial dashboard with summary
- Auto-number generation for Debit/Credit notes (handled in serializer)
- DebitNoteViewSet / CreditNoteViewSet handle CRUD

##### Module Management (5 registration views)
- `AccountRegistrationAPIView`
- `QCInspectorRegistrationAPIView`
- `PurchaseDepartmentRegistrationAPIView`
- `StoreManagerRegistrationAPIView`
- `RepairTechnicianRegistrationAPIView`

##### Quotation Management (4 views)
- `QuotationCreateAPIView` - Create quotation from RFQ with items
- `QuotationListAPIView` - List all quotations with filters
- `QuotationDetailAPIView` - Get quotation with all items
- `QuotationApproveRejectAPIView` - Status update to approved/rejected

##### Self Orders (3 views)
- `SelfOrderCreateAPIView` - Create self order with automatic GST calculation
- `SelfOrderListAPIView` - List user's self orders
- `SelfOrderDetailAPIView` - Get single self order details

#### 3. **Dropdown APIViews** (15+ views)

Return `[{id/key, label/name}]` arrays for form selections:

**Location Dropdowns**:
- `StateDropdownAPIView` - All states
- `DistrictDropdownAPIView` - Districts by state

**Order Dropdowns**:
- `OrderProductsDropdownAPIView` - Product names
- `OrderBatchesDropdownAPIView` - Batches by product
- `CustomerTypeDropdownAPIView` - [b2c, distributor, dealer]
- `PaymentModeDropdownAPIView` - [cash, bank_transfer, cheque, credit_card, upi]
- `PaymentTermsDropdownAPIView` - Various terms
- `OrderPriorityDropdownAPIView` - [low, medium, high, urgent]
- `SalesOrdersDropdownAPIView` - Available sales orders

**Device Dropdowns**:
- `AssemblyTypeDropdownAPIView` - Assembly type choices
- `QuoteTypeDropdownAPIView` - Quote types
- `SRNDropdownAPIView` - Standard Requirement Numbers

**Dispatch Dropdowns**:
- `DispatchOrderTypesDropdownAPIView` - [distributor, dealer, b2c]
- `DispatchProductsDropdownAPIView` - Products for dispatch
- `DispatchBatchesDropdownAPIView` - Batches for dispatch

**Return Dropdowns**:
- `ReturnTypeDropdownAPIView` - [full, partial, replacement]
- `ReturnReasonDropdownAPIView` - Rejection reasons

**Note Dropdowns**:
- `DebitNoteReasonsDropdownAPIView` - Debit note reason choices
- `CreditNoteReasonsDropdownAPIView` - Credit note reason choices
- `NoteStatusesDropdownAPIView` - Note statuses

### Common View Patterns

#### Pattern 1: Step-Based Workflow
```python
def post(self, request):
    # Validation
    serializer = StepXSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=400)
    
    # Processing
    result = perform_business_logic(serializer.validated_data)
    
    # Response
    return Response({
        "success": True,
        "data": result,
        "next_step": "next_endpoint"
    })
```

#### Pattern 2: Stock Management (Sales vs Production)
```python
# Sales Order - DEDUCT stock
order.batch.available_stock -= order.quantity
order.batch.save()

# Production Order - ADD stock
batch.available_stock += order.quantity_added
batch.save()
```

#### Pattern 3: Auto-Number Generation
```python
from utils import generate_note_number, generate_quotation_number

# In serializer create()
note_number = generate_note_number("debit")
debit_note = DebitNote.objects.create(number=note_number, ...)
```

#### Pattern 4: State-District Cascading
```python
# Validate in serializer
if district.state_id != state.id:
    raise ValidationError("District must belong to selected state")
```

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

### **Example 4: RFQ → Purchase Order → MRN Workflow**

1. **Create RFQ (3-Step)**

   ```
   POST /api/rfq/step-1/  → device info, quantity
   POST /api/rfq/step-2/  → select items (BOM parts, components, services)
   POST /api/rfq/step-3/  → delivery details, SRN number
   Returns: rfq_id
   ```

2. **Create Purchase Order (2-Step)**

   ```
   POST /api/purchase/step-1/  → buyer info, RFQ reference
   POST /api/purchase/step-2/  → vendor selection, payment terms
   Returns: po_id
   ```

3. **Create Material Receipt Note (MRN)**
   ```
   POST /api/mrn/create/
   Body: po_id, vendor, inward_type, received_qty
   Returns: mrn_id, batch_number
   ```

### **Example 5: Dispatch & Post-Dispatch Return Workflow**

1. **Create Dispatch (4-Step)**

   ```
   POST /api/dispatch/step-1/           → select sales order
   POST /api/dispatch/step-2/<id>/      → select product & batch
   POST /api/dispatch/step-3/<id>/      → dispatch date & remarks
   POST /api/dispatch/step-4/<id>/      → customer details, mark completed
   Returns: dispatch_id, status=completed, stock_deducted=true
   ```

2. **Create Post-Dispatch Return**
   ```
   POST /api/returns/post-dispatch/create/
   Body: dispatch_ref, return_type, return_reason, return_qty
   Returns: return_id, total_return_amount
   ```

### **Example 6: Account Management (Debit & Credit Notes)**

1. **Create Debit Note (Vendor)**

   ```
   POST /api/debit-notes/
   Body: vendor, reason, amount, reference_document
   Auto-generated: DN-2026-001, DN-2026-002, etc.
   Returns: debit_note_id, number
   ```

2. **Create Credit Note (Customer)**
   ```
   POST /api/credit-notes/
   Body: customer, reason, amount, reference_document
   Auto-generated: CN-2026-001, CN-2026-002, etc.
   Returns: credit_note_id, number
   ```

### **Example 7: Make-to-Order Production**

1. **Create Order Entry with Make-to-Order**

   ```
   POST /api/order-entry/step-1/
   Body: order_type="production", production_type="make_to_order"
   ```

2. **Create Make-to-Order Details**
   ```
   POST /api/order-entry/step-2/
   Body: customer_type, product_specifications, customization_details,
         quantity, expected_delivery_date, payment_terms, order_priority
   Returns: order_id
   ```

## 🚀 RUNNING THE PROJECT

### **Prerequisites**

- Python 3.10+
- PostgreSQL 12+
- Virtual environment (venv, conda, etc.)

### **Local Development Setup**

1. **Clone the repository**

   ```bash
   cd /home/vaibhav/project/Mapwala_MIS_Backend
   ```

2. **Create & activate virtual environment**

   ```bash
   python -m venv vir_env
   source vir_env/bin/activate  # On Windows: vir_env\Scripts\activate
   ```

3. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

4. **Create .env file** (see Configuration section above)

   ```bash
   cp env_example .env
   # Edit .env with your settings
   ```

5. **Run migrations**

   ```bash
   python manage.py migrate
   ```

6. **Create superuser (for admin access)**

   ```bash
   python manage.py createsuperuser
   ```

7. **Run development server**

   ```bash
   python manage.py runserver
   # Server runs on http://localhost:8000
   ```

8. **Access admin panel**
   ```
   http://localhost:8000/admin/
   ```

### **Docker Deployment**

1. **Build Docker image**

   ```bash
   docker build -t mapwala-mis .
   ```

2. **Run with Docker Compose**

   ```bash
   docker-compose up -d
   ```

3. **Run migrations in container**
   ```bash
   docker-compose exec web python manage.py migrate
   docker-compose exec web python manage.py createsuperuser
   ```

### **Production Deployment**

- Use gunicorn or uWSGI as application server
- Configure reverse proxy (nginx/Apache)
- Set DEBUG=False in .env
- Use strong SECRET_KEY
- Configure allowed hosts properly
- Set up SSL/TLS certificates
- Use environment-specific database
- Enable CORS only for trusted origins
- Configure static files serving

---

## 🚀 DEPLOYMENT NOTES

- **Docker Support**: Dockerfile and docker-compose.yml provided
- **Media Root**: Configured for document uploads
- **Static Files**: Basic static configuration
- **Database**: PostgreSQL with connection pooling (conn_max_age=600)
- **Environment Variables**: .env file required (see env_example)
- **Logging**: Standard Django logging configured
- **Rate Limiting**: Login endpoint has throttling enabled

---

## ✅ COMPLETE UNDERSTANDING CHECKLIST

- ✅ **Models**: 50+ models thoroughly documented including new RFQ, Purchase Order, MRN, Dispatch, Post-Dispatch Returns, Account Management, and Module Registration models
- ✅ **Relationships**: Foreign keys, many-to-many, one-to-one mapped with proper protection modes
- ✅ **APIs**: 60+ endpoints across all features documented with methods and parameters
- ✅ **Authentication**: JWT implementation with 24h tokens and terms acceptance tracking
- ✅ **Business Logic**: Multi-step device creation, order workflows, RFQ-PO-MRN pipeline, dispatch workflow, post-dispatch returns
- ✅ **Inventory Management**: Batch-level stock tracking, production orders, store transfers
- ✅ **Validation**: Comprehensive validation at serializer and model level
- ✅ **Database Constraints**: Unique constraints, indexes, protection modes documented
- ✅ **Permissions**: IsAuthenticated on protected endpoints, AllowAny on login
- ✅ **Configuration**: Django settings, JWT config, Database config, CORS setup
- ✅ **File Uploads**: Multipart handling for documents and files with organized folder structure
- ✅ **Account Management**: Debit/Credit notes with auto-numbered sequences
- ✅ **Module Management**: QC Inspectors, Purchase Departments, Store Managers, Repair Technicians, Account Registrations
- ✅ **Workflow Integration**: Complete end-to-end examples from registration to dispatch and returns

---

This documentation represents a complete understanding of the Mapwala MIS Backend project as of January 22, 2026.
