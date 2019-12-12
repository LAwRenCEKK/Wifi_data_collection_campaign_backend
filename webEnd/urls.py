from django.conf.urls import patterns, url
from rest_framework.urlpatterns import format_suffix_patterns
from webEnd import views


urlpatterns = [
    url(r'^$', views.showWeb,name='Webisite_display'),
    ]
