from django.conf.urls import patterns, url, include
#from django.conf.urls.defaults import *  remove with 1.6

#import django.contrib.databrowse
#from django.contrib import databrowse
#import registration 

from django.views.generic import TemplateView


urlpatterns = patterns('',
    # Example:
    #(r'^admin/', include('django.contrib.admin.urls')),
    #(r'^', TemplateView.as_view(template_name='index.html', content_type='text/plain')),
    (r'^metobs/',include('metservice.oceansmap65.urls')),
    #(r'^',include('dwh_webservice.bio_j.urls')),
)
