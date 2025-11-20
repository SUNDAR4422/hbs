from django.urls import path
from .views import (
    HostelListView, HostelDetailView, HostelCreateView,
    WardenProfileView, CreateWardenProfileView, WardenListView, WardenDetailView,
    BankAccountListCreateView, BankAccountDetailView
)

urlpatterns = [
    path('', HostelListView.as_view(), name='hostel_list'),
    path('create/', HostelCreateView.as_view(), name='hostel_create'),
    path('<int:pk>/', HostelDetailView.as_view(), name='hostel_detail'),
    path('warden/profile/', WardenProfileView.as_view(), name='warden_profile'),
    path('warden/create/', CreateWardenProfileView.as_view(), name='create_warden_profile'),
    path('wardens/', WardenListView.as_view(), name='warden_list'),
    path('wardens/<int:pk>/', WardenDetailView.as_view(), name='warden_detail'),

    # Bank Account Management
    path('bank-accounts/', BankAccountListCreateView.as_view(), name='bank_account_list'),
    path('bank-accounts/<int:pk>/', BankAccountDetailView.as_view(), name='bank_account_detail'),
]