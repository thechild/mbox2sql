from msgs2.models import Person, Address, Account, Message, MessageBody, MessageFlag, Header, Attachment, ToDo
import json
from django.http import HttpResponse


# JSON API VIEWS

def primary_inbox(request):
	incoming_inbox = parse_inbox()['primary']
	return inbox_as_json_response(incoming_inbox)

def mass_inbox(request):
	mass_inbox = parse_inbox()['repeat_sender']
	return inbox_as_json_response(mass_inbox)

def new_inbox(request):
	new_inbox = parse_inbox()['new_sender']
	return inbox_as_json_response(new_inbox)

### Helper functions ###

def inbox_as_json_response(inbox):
	json_inbox = [m.as_json() for m in inbox]
	r = {'Status': 'Success',
		 'Inbox': json_inbox}
	return HttpResponse(json.dumps(r, default=date_handler), mimetype='application/json')

def date_handler(obj):
	return obj.isoformat() if hasattr(obj, 'isoformat') else obj

def get_inbox(account=None):
	full_inbox = Message.objects.filter(flags__flag=MessageFlag.INBOX_FLAG).order_by('-sent_date')
	if account:
		return full_inbox.filter(account=account)
	else:
		return full_inbox

# have I ever sent an email to this person before
def is_sender_legit(email, account=None):
	if not account:
		accounts = Account.objects.all()
		return Message.objects.filter(sender__email__in=[account.email_address() for account in accounts],
									  members__addresses__email=email).exists()
	else:
		return Message.objects.filter(sender__email=account.email_address(),
									  members__addresses__email=email).exists()


def is_repeat_sender(email, account=None):
	return Address.objects.get(email=email).sent_messages.count() > 1


# gets the inbox and splits it - should make this all DB calls if possible
def parse_inbox(account=None):
	inbox = get_inbox(account)

	primary_inbox = []
	new_sender_inbox = []
	repeat_sender_inbox = []

	# I bet the database can do a lot of this, but that's an optimization for later
	for m in inbox:
		if is_sender_legit(m.sender.email):
			primary_inbox.append(m)
		elif is_repeat_sender(m.sender.email):
			repeat_sender_inbox.append(m)
		else:
			new_sender_inbox.append(m)

	return {'primary': primary_inbox,
			'new_sender': new_sender_inbox,
			'repeat_sender': repeat_sender_inbox}
