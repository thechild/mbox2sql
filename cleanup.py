from django.db.models import Count
from msgs2.models import Address, Thread, Message
from msgs2.importing import get_or_create_thread


def cleanup_addresses():
	dupes = Address.objects.values('email').annotate(Count('id')).order_by().filter(id__count__gt=1)
	for d in dupes:
		email = d['email']
		print "deduping %s - %s instances" % (email, d['id__count'])
		addresses = Address.objects.filter(email=email)
		true_address = addresses[0]
		for false_address in addresses[1:]:
			for message in false_address.sent_messages.all():
				true_address.sent_messages.add(message)

			for message in false_address.received_messages.all():
				true_address.received_messages.add(message)

			for message in false_address.person.messages.all():
				true_address.person.messages.add(message)
				
			false_address.person.delete()
			false_address.delete()

def cleanup_threads():
	messages = Message.objects.all()
	not_updated = 0
	updated = 0
	new_threads = 0
	for m in messages:
		try:
			t = m.thread
			not_updated += 1
		except (Thread.DoesNotExist, ValueError):
			(new, m.thread) = get_or_create_thread(m.account, m.thread_id, True)
			m.save()
			updated += 1
			if new:
				new_threads += 1
	print "Sorted %s messages into %s new threads.  Ignored %s messages already in threads." % (updated, new_threads, not_updated)