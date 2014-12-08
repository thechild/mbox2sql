from django.conf.urls import patterns, url
from jsonapi import views

urlpatterns = patterns('',
    url(r'^inbox/$', views.all_inboxen, name='full_inbox'),
    url(r'^inbox/primary/$', views.primary_inbox, name='primary_inbox'),
    url(r'^inbox/mass/$', views.mass_inbox, name='mass_inbox'),
    url(r'^inbox/new/$', views.new_inbox, name='new_inbox'),
    url(r'message/(?P<message_id>\d+)/$', views.get_message, name='message'),
#    url(r'message/(?P<message_id>\d+)/$', views.view_message, name="message"),
#    url(r'message/(?P<message_id>\d+)/text$', views.view_message_text, name="messagetext"),
#    url(r'message/(?P<message_id>\d+)/text/raw$', views.raw_message_text, name="raw_messagetext"),
#    url(r'conversation/(?P<conversation_id>\d+)/$', views.view_conversation, name="conversation"),
#    url(r'conversation/(?P<conversation_id>\d+)/text$', views.view_conversation_text, name="conversationtext"),
    url(r'person/(?P<address_id>\d+)/$', views.get_person_from_address, name="person"),
#    url(r'people/$', views.people_list, name='people_list'),
#    url(r'group/(?P<group_id>\d+)/$', views.view_group, name="view_group"),
#    url(r'g/$', views.group_list, name='ghome'),
    )