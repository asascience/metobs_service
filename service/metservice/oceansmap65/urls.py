from django.conf.urls import patterns, include, url
#from django.views.generic import DetailView, ListView

# Uncomment the next two lines to enable the admin:
#from django.contrib import admin
#admin.autodiscover()

#'ctd_j.views'
urlpatterns = patterns('', #'',
    # Examples:
    #url(r'^$', 'gulftoolservice.views.home', name='home'),
    # url(r'^gulftoolservice/', include('gulftoolservice.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
#    url(r'^polls/$','polls.views.index'),
#    url(r'^polls/(?P<poll_id>\d+)/$','polls.views.detail'),
#    url(r'^polls/(?P<poll_id>\d+)/results/$','polls.views.results'),
#    url(r'^polls/(?P<poll_id>\d+)/vote/$','polls.views.vote'),
#    url(r'^admin/', include(admin.site.urls)),
    
    #===========================================================================
    # This is functionally identical to the previous formatting. It's just a bit tidier.
    #===========================================================================
#    url(r'^polls/$','index'),
#    url(r'^polls/(?P<poll_id>\d+)/$','detail'),
#    url(r'^polls/(?P<poll_id>\d+)/results/$','results'),
#    url(r'^polls/(?P<poll_id>\d+)/vote/$','vote'),
    
    #===========================================================================
    # After decoupled, you can omit 
    #===========================================================================    
    url(r'^getstations/$', 'metservice.oceansmap65.views.getstations'),
    url(r'^gettimeseries/$', 'metservice.oceansmap65.views.gettimeseries'),
    url(r'^getvertprofile/$', 'metservice.oceansmap65.views.getvertprofile'),
    url(r'^getvertprofile/$', 'metservice.oceansmap65.views.getvalue'),
    #url(r'^metobs/getcruises/$','metservice.oceansmap65.views.getcruises'),
    #url(r'^ctd_j/getcruises/$','dwh_webservice.ctd_j.views.getcruises'),
    
    #===========================================================================
    # Shortcut
    #===========================================================================
#    url(r'^$',
#        ListView.as_view(
#            queryset=Poll.objects.order_by('-pub_date')[:5],
#            context_object_name='latest_poll_list',
#            template_name='polls/index.html')),
#    url(r'^(?P<pk>\d+)/$',
#        DetailView.as_view(
#            model=Poll,
#            template_name='polls/detail.html')),
#    url(r'^(?P<pk>\d+)/results/$',
#        DetailView.as_view(
#            model=Poll,
#            template_name='polls/results.html'),
#        name='poll_results'),
#    url(r'^(?P<poll_id>\d+)/vote/$', 'polls.views.vote'),
#    url(r'^getstation/(?P<attr>)/(?P<depthindex>)/(?P<startTime>)/(?P<endTime>)/(?P<mode>)/(?P<whereclause>)/$', 'polls.views.getstation'),
)

#===============================================================================
# Since you generally don't want the prefix for one app to be applied to every callback 
# in your URLconf, you can concatenate multiple patterns(). 
# Your full mysite/urls.py might now look like this:
#===============================================================================
#urlpatterns += patterns('',
#    url(r'^admin/', include('django.contrib.admin')),
#)
