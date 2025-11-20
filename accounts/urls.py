from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    LoginView, LogoutView, ChangePasswordView, MeView,
    CreateWardenView, ListWardensView, WardenDetailView, DeanProfileView
)

urlpatterns = [
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('change-password/', ChangePasswordView.as_view(), name='change_password'),
    path('me/', MeView.as_view(), name='me'),
    path('wardens/create/', CreateWardenView.as_view(), name='create_warden'),
    path('wardens/', ListWardensView.as_view(), name='list_wardens'),
    path('wardens/<int:pk>/', WardenDetailView.as_view(), name='warden_detail'),
    path('dean-profile/', DeanProfileView.as_view(), name='dean_profile'),
]
