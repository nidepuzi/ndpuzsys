from django.conf.urls.defaults import patterns, url
from shopback.base.authentication import UserLoggedInAuthentication
from shopback.base.views import CreateModelView,InstanceModelView
from shopback.base.permissions import IsAuthenticated, PerUserThrottling
from shopback.task.resources import ItemTaskResource
from shopback.task.views import direct_update_listing,direct_del_listing,ListItemTaskView


urlpatterns = patterns('',

    url(r'^update/(?P<num_iid>[^/]+)/(?P<num>[^/]+)/$',direct_update_listing,name='update_listing'),
    url(r'^delete/(?P<num_iid>[^/]+)/$',direct_del_listing,name='delete_listing'),
    url(r'^$', CreateModelView.as_view(resource=ItemTaskResource, authentication=(UserLoggedInAuthentication,), permissions=(IsAuthenticated,),)),
    url(r'^(?P<pk>[^/]+)/$', InstanceModelView.as_view(resource=ItemTaskResource, authentication=(UserLoggedInAuthentication,), permissions=(IsAuthenticated,))),
    url(r'^list/self/$', ListItemTaskView.as_view(resource=ItemTaskResource, authentication=(UserLoggedInAuthentication,), permissions=(IsAuthenticated,),)),

)
  