from msgs2 import inbox
from msgs2.models import Message
import json
from django.http import HttpResponse
from django.core.urlresolvers import reverse


# JSON API VIEWS

def primary_inbox(request):
	incoming_inbox = inbox.parse_inbox()['primary']
	return inbox_as_json_response(incoming_inbox, request.GET.get('bodies'))

def mass_inbox(request):
	mass_inbox = inbox.parse_inbox()['repeat_sender']
	return inbox_as_json_response(mass_inbox, request.GET.get('bodies'))

def new_inbox(request):
	new_inbox = inbox.parse_inbox()['new_sender']
	return inbox_as_json_response(new_inbox, request.GET.get('bodies'))

def get_message(request, message_id):
	try:
		message = Message.objects.get(id=message_id)
	except Message.DoesNotExist:
		return error_as_json_response('No message with the requested ID exists.')
	r = {'status': 'Success',
 		 'message_id': message.id,
		 'message': message.as_json() }
	return get_json_response(r)




### Helper functions ###

def error_as_json_response(error_message):
	r = {'status': 'Error',
		 'message': error_message}
	return get_json_response(r, status=404)

def inbox_as_json_response(inbox, include_message_bodies=True):
	json_inbox = inbox_as_json(inbox, include_message_bodies)
	r = {'status': 'Success',
		 'count': len(json_inbox),
		 'inbox': json_inbox}
	return get_json_response(r)
	
def inbox_as_json(inbox, include_message_bodies=True):
	json_inbox = [m.as_json(include_message_bodies) for m in inbox]
	for m in json_inbox:
		m['href'] = reverse('jsonapi:message', args=(m['message_id'], ))
	return json_inbox

def get_json_response(r_json, status=200):
	return HttpResponse(json.dumps(r_json, default=date_handler),
						content_type='application/json',
						status=status)

def date_handler(obj):
	return obj.isoformat() if hasattr(obj, 'isoformat') else obj

