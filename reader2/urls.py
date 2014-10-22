try:
    from django.conf.urls import *
except ImportError:  # django < 1.4
    from django.conf.urls.defaults import *

from django.views.generic.base import RedirectView
from reader2 import views

urlpatterns = patterns('',
    url(r'group/(?P<group_id>\d+)/$', views.view_group, name="view_group"),
    url(r'person/(?P<person_id>\d+)/$', views.view_person, name="view_person"),
    url(r'todo/(?P<todo_id>\d+)/$', views.view_todo, name="view_todo"),
    url(r'conversation/(?P<conversation_id>\d+)/$', views.view_conversation, name="view_conversation"),

    url(r'incoming/$', views.incoming_list, name="incoming_list"),
    url(r'todos/$', views.todo_list, name="todo_list"),
    url(r'other/$', views.other_list, name="other_list"),
)
