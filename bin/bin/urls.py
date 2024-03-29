"""bin URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.2/topics/http/urls/
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
from django.contrib import admin
from django.conf.urls import url
from django.urls import path
from webclient import views

urlpatterns = [
    path('admin/', admin.site.urls),
    url(r'^index/', views.index),
    url(r'^logon$', views.logon),
    url(r'^login$', views.login),
    url(r'^logout$', views.logout),
    url(r'^record/add$', views.add_record),
    url(r'^record/(.+)/delete$', views.delete_record),
    url(r'^record/(.+)/update$', views.update_record),
    url(r'^record/(.+)$', views.get_record),
    url(r'^record/$', views.query),
]
