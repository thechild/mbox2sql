from django.db import models
import os
import hashlib

files_dir = 'files'

# Create your models here.


class Person(models.Model):
    name = models.CharField(max_length=200)

    def __unicode__(self):
        addresses = ', '.join(str.format("<%s>", x.email) for x in self.addresses)
        return "<Person %s [%s]>" % (self.name, addresses)


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


class Header(models.Model):
    key = models.CharField(max_length=200)
    value = models.TextField()
    message = models.ForeignKey(Message)


class MessageBody(models.Model):
    message = models.ForeignKey(Message, related_name='body')
    type = models.CharField(max_length=10)
    content = models.TextField()


class Attachment(models.Model):
    filename = models.CharField(max_length=200)
    content_type = models.CharField(max_length=50)
    stored_location = models.CharField(max_length=200)
    file_md5 = models.CharField(max_length=40)
    message = models.ForeignKey(Message, related_name='attachments')
    mime_related = models.BooleanField(default=False)

    def __unicode__(self):
        return self.filename


def get_or_create_person(address_tuple):
    name, email_address = address_tuple
    existing_addresses = Address.objects.filter(email=email_address.lower())
    if len(existing_addresses) == 0:
        new_person = Person(name=name)
        new_person.save()
        new_address = Address(email=email_address, person=new_person)
        new_address.save()
        return new_address
    elif len(existing_addresses) > 0:
        if len(existing_addresses) > 1:
            print "found multiple db entries for address %s - returning first" % email_address
        existing_address = existing_addresses[0]
        if existing_address.person.name == '':
            existing_address.person.name = name
            existing_address.person.save()
        return existing_address


def create_message(email_message):
    if email_message:
        message = Message()
        message.subject = email_message.subject
        message.sent_date = email_message.sent_date
        message.message_id = email_message.message_id
        message.thread_id = email_message.thread_id  # where should this logic live?


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
    # new_message.save()
    # add the senders
    new_message.sender = get_or_create_person(gmail_message.fr)
    new_message.save()
    new_message.members.add(new_message.sender.person)
    for person in gmail_message.to + gmail_message.cc:
        p = get_or_create_person(person)
        new_message.recipients.add(p)
        new_message.members.add(p.person)

    new_message.save()
    if gmail_message.body:
        body_text = MessageBody(message=new_message,
                                type='text',
                                content=gmail_message.body)
        body_text.save()

    if gmail_message.html:
        body_html = MessageBody(message=new_message,
                                type='html',
                                content=gmail_message.html)
        body_html.save()

    # need to handle attachments
    for att in gmail_message.attachments:
        handle_attachment(new_message, att, False) # need to figure out how to get related from the gmail class

    return new_message


# saves content as a file and creates an Attachment connected to message
def handle_attachment(message, content, related=False):
    print "saving attachment %s of type %s from message %d " % (content.name, content.content_type, message.id)
    a = Attachment()
    a.filename = content.name
    a.content_type = content.content_type
    a.stored_location = os.path.join(files_dir, str(message.id), a.filename) # probably want to fix this too
    a.mime_related = related
    # load the file
    file_content = content.payload
    a.file_md5 = hashlib.md5(file_content).hexdigest() # again, probably a better way to do this than all in memory
    # actually write it do disk - should wrap this in a try except too
    if not os.path.exists(os.path.join(files_dir, str(message.id))):
        os.makedirs(os.path.join(files_dir, str(message.id)))
    with open(a.stored_location, 'wb') as fp:
        fp.write(file_content)
    a.message = message
    a.save()