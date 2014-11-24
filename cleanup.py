from django.db.models import Count
from msgs2.models import Address


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