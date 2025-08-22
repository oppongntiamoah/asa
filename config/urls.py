
from django.contrib import admin
from django.urls import path
from bookings import views
from django.contrib.auth import views as auth_views


urlpatterns = [
    path('admin/', admin.site.urls),
    path('activity/', views.activity_list, name='activity_list'),
    path('book/<int:pk>/', views.book_activity, name='book_activity'),
    path('unbook/<int:pk>/', views.unbook_activity, name='unbook_activity'),
    path('', views.dashboard, name='dashboard'),
    path('booking-wizard/<int:step>/', views.booking_wizard, name='booking_wizard'),

    path("register", views.register, name="register"),
    path("login/", auth_views.LoginView.as_view(template_name="accounts/login.html"), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
]
