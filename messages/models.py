from django.db import models

# Create your models here.


class Person(models.Model):
    name = models.CharField(max_length=200)


class Address(models.Model):
    email = models.EmailField()
    label = models.CharField(max_length=50)
    person = models.ForeignKey(Person, related_name='addresses')


class Message(models.Model):
    sender = models.ForeignKey(Address, related_name='sent_messages')
    recipients = models.ManyToManyField(Address, related_name='received_messages')
    members = models.ManyToManyField(Person, related_name='messages')
    subject = models.TextField()
    sent_date = models.DateTimeField()
    message_id = models.CharField(max_length=200)
    thread_id = models.CharField(max_length=200)


def get_or_create_person(address_tuple):
    name, email_address = address_tuple
    existing_addresses = Address.objects.filter(email=email_address.lower())
    if len(existing_addresses) == 0:
        new_person = Person(name=name)
        new_person.save()
        new_address = Address(email=email_address, person=new_person)
        new_address.save()
        return new_person
    elif len(existing_addresses) > 0:
        if len(existing_addresses) > 1:
            print "found multiple db entries for address %s - returning first" % email_address
        existing_address = existing_addresses[0]
        if existing_address.person.name == '':
            existing_address.person.name = name
            existing_address.person.save()
        return existing_address.person


def create_message(email_message):
    if email_message:
        message = Message()
        message.subject = email_message.subject
        message.sent_date = email_message.sent_date
        message.message_id = email_message.message_id
        message.thread_id = email_message.thread_id  # where should this logic live?


class Header(models.Model):
    key = models.CharField(max_length=200)
    value = models.TextField()
    message = models.ForeignKey(Message)


class MessageBody(models.Model):
    message = models.ForeignKey(Message, related_name='body')
    text = models.TextField()
    html = models.TextField()


class Attachment(models.Model):
    filename = models.CharField(max_length=200)
    content_type = models.CharField(max_length=50)
    stored_location = models.CharField(max_length=200)
    file_md5 = models.CharField(max_length=40)
    message = models.ForeignKey(Message, related_name='attachments')
    mime_related = models.BooleanField(default=False)

    def __unicode__(self):
        return self.filename


def import_message(gmail_message):
    # see if the message is already in the db
    if len(Message.objects.filter(message_id=gmail_message.message_id)) > 0:
        # already exists, skip
        print "Message Id %s already in database, skipping (Subject: %s)" % (gmail_message.message_id, gmail_message.subject)
        return None

    new_message = Message(subject=gmail_message.subject,
                          sent_date=gmail_message.sent_at,
                          message_id=gmail_message.message_id,
                          thread_id=gmail_message.thread_id)
    new_message.save()
    # add the senders
    new_message.sender = get_or_create_person(gmail_message.fr)
    new_message.members.add(new_message.sender)
    for person in gmail_message.tos + gmail_message.ccs:
        p = get_or_create_person(person)
        new_message.recipients.add(p)
        new_message.members.add(p)

    new_message.save()
    return new_message
