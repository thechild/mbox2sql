from msgs2 import inbox
from msgs2.models import Message, Address, Thread
from django.shortcuts import render_to_response

# Create your views here.

def inbox_list(request):
	inboxen = inbox.parse_inbox_threads()
	primary_inbox = inboxen['primary']
	new_sender_inbox = inboxen['new_sender']
	repeat_sender_inbox = inboxen['repeat_sender']
	return render_to_response('inbox_list.html', {
		'primary_inbox': primary_inbox,
		'new_sender_inbox': new_sender_inbox,
		'repeat_sender_inbox': repeat_sender_inbox
		})
