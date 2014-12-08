from django.conf.urls import patterns, include, url
from django.conf.urls.static import static

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'mbox.views.home', name='home'),
    # url(r'^blog/', include('blog.urls')),
    url(r'^mail/', include('reader2.urls', namespace="reader")),
    url(r'^api/v1/', include('jsonapi.urls', namespace="jsonapi")),
    url(r'^admin/', include(admin.site.urls)),
) + static('/files/', document_root='/Users/cchild/Sites/mbox/files/') #grossly insecure
