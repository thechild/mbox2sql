from msgs2.models import Person, Address, Account, Message, MessageBody, MessageFlag, Header, Attachment, ToDo
from collections import OrderedDict
from django.shortcuts import render_to_response

# Create your views here.

def incoming_list(request):
	incoming_inbox = parse_inbox()['primary']
	return render_to_response('thread_list.html', {'messages': incoming_inbox})


### Helper functions ###

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

# note, only threads messages in the passed in object, maintaining order
# should be replaced by a first class database thread support
def thread_messages(inbox):
	threads = OrderedDict()
	for m in inbox:
		if m.thread_id in threads:
			print "appending message to thread %s" % m.thread_id
			threads[m.thread_id] = threads[m.thread_id] + [m]
		else:
			print "new thread %s" % m.thread_id
			threads[m.thread_id] = [m]
	return threads
