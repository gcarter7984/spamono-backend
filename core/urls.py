from django.contrib import admin
from django.urls import path
from core.views import (
    UserRegistrationView,
    UserLoginView,
    UserProfileView,
    ContactListView,
    ContactDetailView,
    ReportSpamView,
    SearchByNameView,
    SearchByPhoneView
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('auth/register/', UserRegistrationView.as_view(), name='register'),
    path('auth/login/', UserLoginView.as_view(), name='login'),
    path('user/profile/', UserProfileView.as_view(), name='user-profile'),
    path('contacts/', ContactListView.as_view(), name='contact-list'),
    path('contacts/<uuid:id>/', ContactDetailView.as_view(), name='contact-detail'),
    path('spam/report/', ReportSpamView.as_view(), name='report-spam'),
    path('search/name/', SearchByNameView.as_view(), name='search-by-name'),
    path('search/phone/', SearchByPhoneView.as_view(), name='search-by-phone'),
]