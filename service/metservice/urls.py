#from django.conf.urls.defaults import patterns, include, url
#from django.contrib import admin
#admin.autodiscover()

#from django.conf.urls.defaults import *
from django.conf.urls import patterns, url, include
#from django.contrib import databrowse
import registration
from django.views.generic.simple import direct_to_template



# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    #url(r'^$', 'ctdservice.ctd.views.test', name='home'),
    # url(r'^ctdservice/', include('ctdservice.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    #(r'^admin/', include('django.contrib.admin.urls')),
    #(r'^/',include('metservice.oceansmap65.urls')),
    #(r"^$", direct_to_template, {"template": "index.html"})
#    (r'^databrowse/(.*)', databrowse.site.root),
)
