from django.conf.urls import patterns, url
from reader import views

urlpatterns = patterns('',
    url(r'^$', views.message_list, name='home'),
    url(r'c/$', views.conversation_list, name='chome'),
    url(r'message/(?P<message_id>\d+)/raw$', views.raw_message, name='raw_message'),
    url(r'message/(?P<message_id>\d+)/$', views.view_message, name="message"),
    url(r'message/(?P<message_id>\d+)/text$', views.view_message_text, name="messagetext"),
    url(r'message/(?P<message_id>\d+)/text/raw$', views.raw_message_text, name="raw_messagetext"),
    url(r'conversation/(?P<conversation_id>\d+)/$', views.view_conversation, name="conversation"),
    url(r'conversation/(?P<conversation_id>\d+)/text$', views.view_conversation_text, name="conversationtext"),
    url(r'person/(?P<person_id>\d+)/$', views.view_person, name="person"),
    url(r'people/$', views.people_list, name='people_list'),
    url(r'group/(?P<group_id>\d+)/$', views.view_group, name="view_group"),
    url(r'g/$', views.group_list, name='ghome'),
    )