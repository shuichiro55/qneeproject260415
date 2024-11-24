from django.contrib import admin
from django.urls import path
from django.urls.conf import include
from contact import views

urlpatterns = [
    # Contact
    path('contactus',views.Contactus.as_view(),name="contactus")
]