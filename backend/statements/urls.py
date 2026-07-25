from django.urls import path

from . import views

app_name = "statements"

urlpatterns = [
    path("", views.statement_list, name="list"),
    path("upload/", views.upload, name="upload"),
    path("<int:pk>/status/", views.status, name="status"),
    path("<int:pk>/review/", views.review, name="review"),
    path("<int:pk>/confirmed/", views.confirmed, name="confirmed"),
    path("<int:pk>/delete/", views.delete, name="delete"),
    path("<int:pk>/replace/", views.replace, name="replace"),
]
