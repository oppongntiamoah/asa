from django.urls import path

from . import views

app_name = "news"

urlpatterns = [
    path("", views.news_list, name="list"),
    path("faq/", views.faq, name="faq"),
    path("contact/", views.contact, name="contact"),
    path("mark-seen/", views.mark_news_seen, name="mark_seen"),
    path("<slug:slug>/", views.news_detail, name="detail"),
]
