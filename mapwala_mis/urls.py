from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import *

router = DefaultRouter()
router.register("states", StateViewSet, basename="states")
router.register("districts", DistrictViewSet, basename="districts")
router.register("parent-companies", ParentCompanyViewSet, basename="parent-companies")
router.register("vendors", VendorViewSet, basename="vendors")
router.register("store-transfers", StoreTransferViewSet, basename="store-transfers")
router.register("product-categories", ProductCategoryViewSet, basename="product-categories")
router.register("debit-notes", DebitNoteViewSet, basename="debit-notes")
router.register("credit-notes", CreditNoteViewSet, basename="credit-notes")

urlpatterns = [
    path("auth/login/", LoginAPIView.as_view(), name="login"),
    path("b2c/register/", B2CCustomerRegistrationAPIView.as_view(), name="b2c-register"),
    path("b2b/register/", B2BPartnerRegistrationAPIView.as_view(), name="b2b-register"),
    path("distributor/register/", DistributorRegistrationAPIView.as_view(), name="distributor-register"),
    path("dealer/register/",DealerRegistrationAPIView.as_view(),name="dealer-register"),
    
    # ============================================================
    # ACCOUNT MANAGEMENT - DEBIT & CREDIT NOTES
    # ============================================================
    path("account-management/dashboard/", AccountManagementDashboardAPIView.as_view(), name="account-dashboard"),
    path("debit-notes/reasons/", DebitNoteReasonsAPIView.as_view(), name="debit-note-reasons"),
    path("credit-notes/reasons/", CreditNoteReasonsAPIView.as_view(), name="credit-note-reasons"),
    path("notes/statuses/", NoteStatusChoicesAPIView.as_view(), name="note-statuses"),
    
    # ============================================================
    # DEVICE CREATION
    # ============================================================
    path("devices/step-1/", DeviceStep1APIView.as_view()),
    path("devices/step-2/", DeviceStep2APIView.as_view()),
    path("devices/step-3/", DeviceStep3APIView.as_view()),
    path("devices/step-4/", DeviceStep4APIView.as_view()),
    path("devices/step-5/", DeviceStep5APIView.as_view()),
    path("devices/step-6/", DeviceStep6APIView.as_view()),
    path("devices/step-7/", DeviceStep7APIView.as_view()),
    path("devices/step-8/", DeviceStep8APIView.as_view()),
    path("devices/step-9/", DeviceStep9APIView.as_view()),
    path("devices/step-10/", DeviceAccessoryAPIView.as_view()),
    
    # ============================================================
    # PROFORMA INVOICE
    # ============================================================
    path("pi/create/", ProformaInvoiceCreateAPIView.as_view(), name="create-pi"),
    
    # ============================================================
    # ORDER MANAGEMENT
    # ============================================================
    path("order-entry/step-1/", OrderEntryStep1APIView.as_view()),
    path("order-products/", OrderProductListAPIView.as_view()),
    path("order-batches/", OrderBatchListAPIView.as_view()),
    path("sales-orders/create/", SalesOrderCreateAPIView.as_view()),
    path("production-orders/add-to-stock/", ProductionOrderCreateAPIView.as_view()),
    path("dropdowns/products/", ProductDropdownAPIView.as_view()),
    path("dropdowns/suppliers/", SupplierVendorDropdownAPIView.as_view()),
    path("dropdowns/product-categories/", ProductCategoryDropdownAPIView.as_view()),

    path("order-entry/step-2/", OrderEntryStep2APIView.as_view()),
    
    # ============================================================
    # DROPDOWNS
    # ============================================================
    path("dropdowns/customer-types/", CustomerTypeDropdownAPIView.as_view()),
    path("dropdowns/payment-terms/", PaymentTermsDropdownAPIView.as_view()),
    path("dropdowns/order-priority/", OrderPriorityDropdownAPIView.as_view()),
    
    # ============================================================
    # RFQ MANAGEMENT
    # ============================================================
    path("rfq/step-1/", RFQStep1APIView.as_view()),
    path("rfq/step-2/", RFQStep2APIView.as_view()),
    path("rfq/step-3/", RFQStep3APIView.as_view()),
    path("dropdowns/quote-types/", QuoteTypeDropdownAPIView.as_view()),
    path("dropdowns/assembly-types/", AssemblyTypeDropdownAPIView.as_view()),
    path("dropdowns/srn/", SRNDropdownAPIView.as_view()),
    path("dropdowns/vendors/", VendorDropdownAPIView.as_view()),
    
    # ============================================================
    # PURCHASE ORDER
    # ============================================================
    path("purchase/step-1/", Step1APIView.as_view()),
    path("purchase/step-2/", Step2APIView.as_view()),
    path("dropdowns/order-types/", OrderTypeDropdown.as_view()),
    path("dropdowns/assembly-types/", AssemblyTypeDropdown.as_view()),
    path("dropdowns/payment-terms/", PaymentTermsDropdown.as_view()),
    
    # ============================================================
    # MRN (MATERIAL RECEIPT NOTE)
    # ============================================================
    path("mrn/create/", MRNCreateAPIView.as_view()),
    path("dropdowns/purchase-orders/", PurchaseOrderDropdown.as_view(), name="purchase-order-dropdown"),
    path("dropdowns/inward-types/", InwardTypeDropdown.as_view(), name="inward-type-dropdown"),
    path("purchase/<int:po_id>/items/", PurchaseOrderItemsAPIView.as_view(), name="purchase-order-items"),
    
    # ============================================================
    # POST-DISPATCH RETURNS
    # ============================================================
    path("returns/post-dispatch/create/", PostDispatchReturnCreateAPIView.as_view(), name="post-dispatch-return-create"),
    path("dropdowns/return-types/", ReturnTypeDropdownAPIView.as_view(), name="return-type-dropdown"),
    path("dropdowns/return-reasons/", ReturnReasonDropdownAPIView.as_view(), name="return-reason-dropdown"),
    
    # ============================================================
    # DISPATCH WORKFLOW
    # ============================================================
    path("dispatch/step-1/", DispatchStep1APIView.as_view()),
    path("dispatch/step-2/<int:dispatch_id>/", DispatchStep2APIView.as_view()),
    path("dispatch/step-3/<int:dispatch_id>/", DispatchStep3APIView.as_view()),
    path("dispatch/step-4/<int:dispatch_id>/", DispatchStep4APIView.as_view()),
    path("dropdowns/sales-orders/", SalesOrderDropdownAPIView.as_view()),
    path("dropdowns/dispatch-order-types/", DispatchOrderTypeDropdownAPIView.as_view()),
    path("dropdowns/dispatch-products/", DispatchProductDropdownAPIView.as_view()),
    path("dropdowns/dispatch-batches/", DispatchBatchDropdownAPIView.as_view()),
    
    # ============================================================
    # MODULE MANAGEMENT REGISTRATIONS
    # ============================================================
    path("dropdowns/states/", StateDropdownAPIView.as_view()),
    path("dropdowns/districts/", DistrictDropdownAPIView.as_view()),
    path("account/register/", AccountRegistrationCreateAPIView.as_view()),
    path("qc-inspectors/register/", QCInspectorRegistrationCreateAPIView.as_view()),
    path("purchase-departments/register/", PurchaseDepartmentRegistrationCreateAPIView.as_view()),
    path("store-managers/register/", StoreManagerRegistrationCreateAPIView.as_view()),
]

urlpatterns += router.urls
