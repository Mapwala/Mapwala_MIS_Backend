# mapwala_mis/urls.py
from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import (
    UserViewSet,
    LoginAPIView,
    B2CCustomerViewSet,
    B2BPartnerViewSet,
    DealerViewSet,
    AccountManagementDashboardAPIView,
    DebitNoteReasonsAPIView,
    CreditNoteReasonsAPIView,
    NoteStatusChoicesAPIView,
    DeviceStep1APIView,
    DeviceStep2APIView,
    DeviceStep3APIView,
    DeviceStep4APIView,
    DeviceStep5APIView,
    DeviceStep6APIView,
    DeviceStep7APIView,
    DeviceStep8APIView,
    DeviceStep9APIView,
    DeviceAccessoryAPIView,
    ProformaInvoiceCreateAPIView,
    ProductDropdownAPIView,
    ProductCreateAPIView,
    ProductCategoryDropdownAPIView,
    CustomerTypeDropdownAPIView,
    PaymentTermsDropdownAPIView,
    OrderPriorityDropdownAPIView,
    QuoteTypeDropdownAPIView,
    AssemblyTypeDropdownAPIView,
    SRNDropdownAPIView,
    VendorDropdownAPIView,
    Step1APIView,
    Step2APIView,
    MRNCreateAPIView,
    PurchaseOrderDropdown,
    InwardTypeDropdown,
    PurchaseOrderItemsAPIView,
    PostDispatchReturnCreateAPIView,
    ReturnTypeDropdownAPIView,
    ReturnReasonDropdownAPIView,
    DispatchStep1APIView,
    DispatchStep2APIView,
    DispatchStep3APIView,
    DispatchStep4APIView,
    SalesOrderDropdownAPIView,
    DispatchOrderTypeDropdownAPIView,
    DispatchProductDropdownAPIView,
    DispatchBatchDropdownAPIView,
    AccountRegistrationCreateAPIView,
    SelfOrderCreateAPIView,
    SelfOrderListAPIView,
    SelfOrderDetailAPIView,
    SelfOrderDeviceDropdownAPIView,
    GSTRateDropdownAPIView,
    QuotationCreateAPIView,
    QuotationListAPIView,
    QuotationDetailAPIView,
    QuotationApproveRejectAPIView,
    state_of_supply_dropdown,
    unit_of_measure_dropdown,
    StateViewSet,
    DistrictViewSet,
    ParentCompanyViewSet,
    VendorViewSet,
    StoreTransferViewSet,
    ProductCategoryViewSet,
    DebitNoteViewSet,
    CreditNoteViewSet,
    ReturnRequestViewSet,
    RepairRecordViewSet,
    RejectedItemViewSet,
    DeviceViewSet,
    ManufacturerViewSet,
    LinkedToChoicesAPIView,
    DistributorViewSet,
    QCInspectorViewSet,
    PurchaseDepartmentViewSet,
    StoreManagerViewSet,
    RepairTechnicianViewSet,
    DeviceInventoryViewSet,
    RFQViewSet,
    OrderEntryViewSet,
    OrderProductViewSet,
    SalesOrderViewSet,
    OrderBatchViewSet,
    ProductionOrderViewSet,
    B2BOrderViewSet,
    POOrderIDDropdownAPIView,
    POSelectRFQDropdownAPIView,
    Step2GetAPIView,
    OrderTypeDropdown,
)


router = DefaultRouter()

# Master data
router.register(r"users", UserViewSet, basename="users")
router.register(r"states", StateViewSet, basename="states")
router.register(r"districts", DistrictViewSet, basename="districts")
router.register(r"b2c-customers", B2CCustomerViewSet, basename="b2c-customers")
router.register(r"b2b-partners", B2BPartnerViewSet, basename="b2b-partners")
router.register(r"dealers", DealerViewSet, basename="dealers")
router.register(r"parent-companies", ParentCompanyViewSet, basename="parent-companies")
router.register(r"vendors", VendorViewSet, basename="vendors")
router.register(r"devices", DeviceViewSet, basename="devices")
router.register(r"store-transfers", StoreTransferViewSet, basename="store-transfers")
router.register(r"product-categories", ProductCategoryViewSet, basename="product-categories")
router.register(r"distributors", DistributorViewSet, basename="distributors")
router.register(r"manufacturers", ManufacturerViewSet, basename="manufacturers")
router.register(r"debit-notes", DebitNoteViewSet, basename="debit-notes")
router.register(r"credit-notes", CreditNoteViewSet, basename="credit-notes")
router.register(r"return-requests", ReturnRequestViewSet, basename="return-request")
router.register(r"repair-records", RepairRecordViewSet, basename="repair-record")
router.register(r"rejected-items", RejectedItemViewSet, basename="rejected-item")
router.register(r"qc-inspectors", QCInspectorViewSet, basename="qc-inspectors")
router.register(r"purchase-departments", PurchaseDepartmentViewSet, basename="purchase-departments")
router.register(r"store-managers", StoreManagerViewSet, basename="store-managers")
router.register(r"repair-technicians", RepairTechnicianViewSet, basename="repair-technicians")
router.register(r"reports/devices", DeviceInventoryViewSet, basename="device-inventory")
router.register(r"rfq", RFQViewSet, basename="rfq")
# Order Entry
router.register(r"order-entries", OrderEntryViewSet, basename="order-entry")
router.register(r"order-products", OrderProductViewSet, basename="order-product")
router.register(r"order-batches", OrderBatchViewSet, basename="order-batch")
router.register(r"sales-orders", SalesOrderViewSet, basename="sales-order")
router.register(r"production-orders", ProductionOrderViewSet, basename="production-order")
router.register(r"b2b-orders", B2BOrderViewSet, basename="b2b-order")


urlpatterns = [
    # Auth & registration
    path("auth/login/", LoginAPIView.as_view(), name="login"),
    path("dropdowns/linked-to/", LinkedToChoicesAPIView.as_view()),
    # Product Dropdowns
    path("dropdowns/products/", ProductDropdownAPIView.as_view(), name="product-dropdown"),
    path("products/", ProductCreateAPIView.as_view(), name="product-create"),
    # Account management
    path("account-management/dashboard/", AccountManagementDashboardAPIView.as_view()),
    path("debit-notes/reasons/", DebitNoteReasonsAPIView.as_view()),
    path("credit-notes/reasons/", CreditNoteReasonsAPIView.as_view()),
    path("notes/statuses/", NoteStatusChoicesAPIView.as_view()),
    # Device creation (steps)
    path("devices/dropdowns/unit-of-measure/",unit_of_measure_dropdown,name="unit-of-measure-dropdown"),
    path("devices/dropdowns/state-of-supply/",state_of_supply_dropdown,name="state-of-supply-dropdown"),
    path("devices/step-1/", DeviceStep1APIView.as_view(), name="device-step-1"),
    path("devices/step-2/", DeviceStep2APIView.as_view(), name="device-step-2"),
    path("devices/step-3/", DeviceStep3APIView.as_view(), name="device-step-3"),
    path("devices/step-4/", DeviceStep4APIView.as_view(), name="device-step-4"),
    path("devices/step-5/", DeviceStep5APIView.as_view(), name="device-step-5"),
    path("devices/step-6/", DeviceStep6APIView.as_view(), name="device-step-6"),
    path("devices/step-7/", DeviceStep7APIView.as_view(), name="device-step-7"),
    path("devices/step-8/", DeviceStep8APIView.as_view(), name="device-step-8"),
    path("devices/step-9/", DeviceStep9APIView.as_view(), name="device-step-9"),
    path("devices/step-10/", DeviceAccessoryAPIView.as_view(), name="device-step-10"),
    # Proforma invoice
    path("pi/create/", ProformaInvoiceCreateAPIView.as_view()),
    
    # # Order Entry Dropdowns
    path("dropdowns/customer-types/", CustomerTypeDropdownAPIView.as_view()),
    path("dropdowns/product-categories/", ProductCategoryDropdownAPIView.as_view()),
    path("dropdowns/payment-terms/", PaymentTermsDropdownAPIView.as_view()), 
    path("dropdowns/order-priority/", OrderPriorityDropdownAPIView.as_view()), 
    
    # RFQ
    path("dropdowns/quote-types/", QuoteTypeDropdownAPIView.as_view()),
    path("dropdowns/assembly-types/", AssemblyTypeDropdownAPIView.as_view()),
    path("dropdowns/srn/", SRNDropdownAPIView.as_view()),
    path("dropdowns/vendors/", VendorDropdownAPIView.as_view()),
    # Purchase & MRN
    path("purchase/dropdowns/order-ids/",POOrderIDDropdownAPIView.as_view(),name="purchase-dropdown-order-ids"),
    path("purchase/dropdowns/rfqs/",POSelectRFQDropdownAPIView.as_view(),name="purchase-dropdown-rfqs"),
    path("purchase/<int:po_id>/step-2/",Step2GetAPIView.as_view(),name="purchase-step-2-get"),
    path("purchase/step-1/", Step1APIView.as_view()),
    path("purchase/step-2/", Step2APIView.as_view()),
    path("mrn/create/", MRNCreateAPIView.as_view()),
    path("dropdowns/order-types/",    OrderTypeDropdown.as_view(),    name="dropdown-order-types"),
    path("dropdowns/purchase-orders/", PurchaseOrderDropdown.as_view()),
    path("dropdowns/inward-types/", InwardTypeDropdown.as_view()),
    path("purchase/<int:po_id>/items/", PurchaseOrderItemsAPIView.as_view()),
    # Post-dispatch returns
    path("returns/post-dispatch/create/", PostDispatchReturnCreateAPIView.as_view()),
    path("dropdowns/return-types/", ReturnTypeDropdownAPIView.as_view()),
    path("dropdowns/return-reasons/", ReturnReasonDropdownAPIView.as_view()),
    # Dispatch
    path("dispatch/step-1/", DispatchStep1APIView.as_view()),
    path("dispatch/step-2/<int:dispatch_id>/", DispatchStep2APIView.as_view()),
    path("dispatch/step-3/<int:dispatch_id>/", DispatchStep3APIView.as_view()),
    path("dispatch/step-4/<int:dispatch_id>/", DispatchStep4APIView.as_view()),
    path("dropdowns/sales-orders/", SalesOrderDropdownAPIView.as_view()),
    path("dropdowns/dispatch-order-types/", DispatchOrderTypeDropdownAPIView.as_view()),
    path("dropdowns/dispatch-products/", DispatchProductDropdownAPIView.as_view()),
    path("dropdowns/dispatch-batches/", DispatchBatchDropdownAPIView.as_view()),
    # Module registrations
    path("account/register/", AccountRegistrationCreateAPIView.as_view()),
    # Self orders
    path("self-orders/create/", SelfOrderCreateAPIView.as_view()),
    path("self-orders/", SelfOrderListAPIView.as_view()),
    path("self-orders/<int:pk>/", SelfOrderDetailAPIView.as_view()),
    path("self-orders/devices/", SelfOrderDeviceDropdownAPIView.as_view()),
    path("self-orders/gst-rates/", GSTRateDropdownAPIView.as_view()),
    # Quotations
    path("quotations/create/", QuotationCreateAPIView.as_view()),
    path("quotations/", QuotationListAPIView.as_view()),
    path("quotations/<int:quotation_id>/", QuotationDetailAPIView.as_view()),
    path("quotations/<int:quotation_id>/approve-reject/", QuotationApproveRejectAPIView.as_view()),
]

urlpatterns += router.urls
