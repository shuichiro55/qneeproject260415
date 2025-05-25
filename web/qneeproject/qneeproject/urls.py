"""
URL configuration for qneeproject project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView
from . import views

urlpatterns = [

    #path('', views.top_corporate, name='top'),
    
    path('admin/', admin.site.urls),

    path('', TemplateView.as_view(template_name="index/index_corporate.html"),name="index_corporate"), 
    path('accounts/', include('accounts.urls')),
    path('qpay/', include('qpay.urls')),
    path('',include('contact.urls')),

    path('corporate_info', TemplateView.as_view(template_name="index/corporate_info.html"),name="corporate_info"),
    path('index_qconnect_admin', TemplateView.as_view(template_name="index/index_qconnect_admin.html"),name="index_qconnect_admin"),
    path('index_qconnect_buyer', TemplateView.as_view(template_name="index/index_qconnect_buyer.html"),name="index_qconnect_buyer"),
    path('index_qconnect_seller', TemplateView.as_view(template_name="index/index_qconnect_seller.html"),name="index_qconnect_seller"),

    path('blog-list', TemplateView.as_view(template_name="index/blog-list.html"),name="blog-list"),
    path('blog-details', TemplateView.as_view(template_name="index/blog-details.html"),name="blog-details"),

    #後で見直し 24/09/15
    path('login', TemplateView.as_view(template_name="account/login.html"),name="login"),
    path('register', TemplateView.as_view(template_name="account/register.html"),name="register"),
    path('reset-password', TemplateView.as_view(template_name="account/reset-password.html"),name="reset-password"),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
# requestされたURLとMEDIA_URLが合致した時、次のdocument_root内のファイルを見つけに行く