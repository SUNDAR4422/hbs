from django.urls import path
from .views import (
    CreateBonafideRequestView, StudentBonafideRequestListView,
    WardenPendingRequestsView, WardenReviewRequestView,
    DeanPendingRequestsView, DeanReviewRequestView,
    DownloadBonafideView, VerifyBonafideView,
    AllBonafideRequestsView, BonafideSettingsView
)

urlpatterns = [
    path('request/create/', CreateBonafideRequestView.as_view(), name='create_bonafide_request'),
    path('requests/my/', StudentBonafideRequestListView.as_view(), name='my_bonafide_requests'),
    path('requests/all/', AllBonafideRequestsView.as_view(), name='all_bonafide_requests'),
    path('requests/warden/pending/', WardenPendingRequestsView.as_view(), name='warden_pending_requests'),
    path('requests/dean/pending/', DeanPendingRequestsView.as_view(), name='dean_pending_requests'),
    path('review/warden/<uuid:request_id>/', WardenReviewRequestView.as_view(), name='warden_review'),
    path('review/dean/<uuid:request_id>/', DeanReviewRequestView.as_view(), name='dean_review'),
    path('download/<uuid:request_id>/', DownloadBonafideView.as_view(), name='download_bonafide'),
    path('verify/<str:verification_code>/', VerifyBonafideView.as_view(), name='verify_bonafide'),
    path('settings/', BonafideSettingsView.as_view(), name='bonafide_settings'),
]
