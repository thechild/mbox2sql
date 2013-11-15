from django.conf.urls import patterns, include, url
from django.conf.urls.static import static

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'mbox.views.home', name='home'),
    # url(r'^blog/', include('blog.urls')),
    url(r'^mail/', include('reader.urls', namespace="reader")),
    url(r'^admin/', include(admin.site.urls)),
) + static('/files/', document_root='/Users/cchild/Sites/mbox/files/') #grossly insecure
