# Mapwala MIS Backend - Complete Project Documentation

**Project Type:** Django REST Framework Backend with JWT Authentication  
**Database:** PostgreSQL  
**Last Updated:** January 17, 2026

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
├── 🐳 Deployment & Config
│   ├── .dockerignore
│   ├── Dockerfile              # Docker image definition
│   ├── docker-compose.yml      # Container orchestration
│   ├── .env                    # Active environment variables (Secrets)
│   ├── env_example             # Template for environment variables
│   └── requirements.txt        # Python dependencies
│
├── ⚙️ Core Project (Mapwala_MIS_Backend)
│   ├── settings.py             # Main Django settings
│   ├── urls.py                 # Global URL routing
│   ├── asgi.py                 # ASGI config (Async entry point)
│   ├── wsgi.py                 # WSGI config (Sync entry point)
│   └── __init__.py
│
├── 📦 Main Application (mapwala_mis)
│   ├── admin.py                # Django Admin panel configuration
│   ├── apps.py                 # App configuration
│   ├── models.py               # Database schemas
│   ├── serializers.py          # DRF Serializers (JSON conversion)
│   ├── views.py                # API Logic and ViewSets
│   ├── urls.py                 # App-specific URL routing
│   ├── utils.py                # Helper functions/utilities
│   ├── tests.py                # Unit tests
│   ├── jazzmin_patch.py        # Customizations for Jazzmin (Admin Theme)
│   ├── migrations/             # Database migrations
│   └── __init__.py
│
└── 🚀 Management
    ├── manage.py               # Django command-line utility
    └── .gitignore              # Git ignore rules
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

The project uses 50+ serializers for request/response validation:

### **Core Serializers**

- `LoginSerializer` - Authentication with terms acceptance
- `StateSerializer`, `DistrictSerializer` - Location management
- `ProformaInvoiceCreateSerializer` - PI creation with party validation

### **Registration Serializers**

- `B2CCustomerRegistrationSerializer` - B2C customer with documents
- `B2BPartnerRegistrationSerializer` - B2B partner registration
- `DistributorRegistrationSerializer` - Distributor with authorized areas
- `DealerRegistrationSerializer` - Dealer with manufacturer/distributor FK selection

### **Device Creation Serializers (Steps 1-10)**

- `DeviceInformationSerializer` - Device specs
- `BOMSerializer` - BOM with upload type validation
- `BOMComponentSerializer` - Individual components
- `EnclosureSerializer`, `WireConnectorSerializer`, `WireHarnessSerializer` - Components
- `BatterySerializer`, `SOSButtonSerializer` - Specifications
- `StickerSerializer`, `UserManualSerializer`, `AccessorySerializer` - Attachments

### **Order Management Serializers**

- `OrderEntryStep1Serializer` - Order type selection
- `OrderProductSerializer`, `OrderBatchSerializer` - Dropdowns
- `SalesOrderCreateSerializer` - Sales order with stock validation
- `ProductionOrderCreateSerializer` - Production order with batch auto-creation

### **RFQ & Purchase Order Serializers**

- `RFQStep1Serializer`, `RFQStep2Serializer`, `RFQStep3Serializer` - RFQ workflow
- `PurchaseOrderStep1Serializer`, `PurchaseOrderStep2Serializer` - PO workflow
- `PurchaseOrderItemSerializer` - Line items

### **MRN & Dispatch Serializers**

- `MRNCreateSerializer` - Material receipt with item details
- `DispatchStep1Serializer` through `DispatchStep4Serializer` - Dispatch workflow
- `PostDispatchReturnCreateSerializer` - Return with line items

### **Account Management Serializers**

- `DebitNoteSerializer`, `CreditNoteSerializer` - Accounting documents
- `AccountManagementDashboardSerializer` - Dashboard data

### **Module Management Serializers**

- `AccountRegistrationSerializer` - Account registration
- `QCInspectorRegistrationSerializer` - QC inspector registration
- `PurchaseDepartmentRegistrationSerializer` - Purchase department registration
- `StoreManagerRegistrationSerializer` - Store manager registration

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
DB_ENGINE=postgresql
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

This documentation represents a complete understanding of the Mapwala MIS Backend project as of January 17, 2026.
