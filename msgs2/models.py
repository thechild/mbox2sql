from django.db import models
from django.utils.text import get_valid_filename
from email.Header import decode_header
import os
import hashlib
import uuid
import datetime

files_dir = 'files'


class Person(models.Model):
    name = models.CharField(max_length=200)

    def __unicode__(self):
        addresses = ', '.join(str.format("<%s>", x.email) for x in self.addresses)
        return "<Person %s [%s]>" % (self.name, addresses)


class Address(models.Model):
    email = models.EmailField()
    label = models.CharField(max_length=50)
    person = models.ForeignKey(Person, related_name='addresses')

    def __unicode__(self):
        return "{}".format(self.email)


class Message(models.Model):
    sender = models.ForeignKey(Address, related_name='sent_messages')
    recipients = models.ManyToManyField(Address,
                                        related_name='received_messages')
    members = models.ManyToManyField(Person, related_name='messages')
    subject = models.TextField()
    sent_date = models.DateTimeField()
    message_id = models.CharField(max_length=200)
    thread_id = models.CharField(max_length=200)

    @property
    def is_unread(self):
        return self.flags.exists(flag=MessageFlag.UNREAD_FLAG)

    @property
    def is_in_inbox(self):
        return self.flags.exists(flag=MessageFlag.INBOX_FLAG)

    @property
    def is_starred(self):
        return self.flags.exists(flag=MessageFlag.STARRED_FLAG)

    def archive(self):
        self.flags.filter(flag=MessageFlag.INBOX_FLAG).delete()
        # TODO somehow store this for the server...

    def mark_read(self):
        self.flags.filter(flag=MessageFlag.UNREAD_FLAG).delete()
        # TODO somehow store this for the server...

    def __unicode__(self):
        return "Message <Sender: {}, Subject: {}>".format(self.sender.email, self.subject)


class MessageFlag(models.Model):
    UNREAD_FLAG = 'U'
    INBOX_FLAG = 'I'
    STARRED_FLAG = 'S'
    IMPORTANT_FLAG = 'M'

    FLAGS = (
        (UNREAD_FLAG, 'Unread'),
        (INBOX_FLAG, 'Inbox'),
        (STARRED_FLAG, 'Starred'),
        (IMPORTANT_FLAG, 'Important'),
    )
    message = models.ForeignKey(Message, related_name='flags')
    flag = models.CharField(max_length=1, choices=FLAGS)

    def __unicode_(self):
        return [y[0] for y in MessageFlag.FLAGS if y[0] == self.flag][0]


class Header(models.Model):
    key = models.CharField(max_length=200)
    value = models.TextField()
    message = models.ForeignKey(Message, related_name='headers')

    def __unicode__(self):
        return "{}: {}".format(self.key, self.value)


class MessageBody(models.Model):
    message = models.ForeignKey(Message, related_name='body')
    type = models.CharField(max_length=10)
    content = models.TextField()

    def __unicode__(self):
        return "[{}]: {}".format(self.type, self.content[:100])


class Attachment(models.Model):
    filename = models.CharField(max_length=200)
    content_type = models.CharField(max_length=50)
    stored_location = models.CharField(max_length=200)
    file_md5 = models.CharField(max_length=40)
    message = models.ForeignKey(Message, related_name='attachments')
    mime_related = models.BooleanField(default=False)

    def __unicode__(self):
        return self.filename


class ToDo(models.Model):
    date_created = models.DateField(default=datetime.date.today())
    date_due = models.DateField(default=datetime.date.today() + datetime.timedelta(days=1))
    subject = models.CharField(max_length=200)
    message = models.ForeignKey(Message, blank=True, null=True, related_name='todos')
    note_text = models.TextField(default='')

    def __unicode__(self):
        return "ToDo: {}".format(self.subject)


def add_todo_from_message(message):
    if len(message.todos) > 0:  # a todo already exists for this message, so surface it
        return message.todos[0]

    todo = ToDo()
    todo.subject = message.subject
    todo.save()
    todo.message = message
    todo.save()
    return todo


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


def import_message(gmail_message, save_attachments=True):
    # see if the message is already in the db
    if len(Message.objects.filter(message_id=gmail_message.message_id)) > 0:
        # already exists, skip
        # print "Message Id %s already in database, skipping (Subject: %s)" % (gmail_message.message_id, gmail_message.subject)
        # maybe update read status, or inbox status if I can figure out how to do that?
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

    if not gmail_message.is_read():
        new_message.flags.add(MessageFlag(flag=MessageFlag.UNREAD_FLAG))

    # add the headers
    for k, v in gmail_message.headers.iteritems():
        new_message.headers.add(Header(key=k, value=v))

    # need to handle attachments
    if save_attachments:
        for att, related in gmail_message.attachments:
            handle_attachment(new_message, att, related)

    return new_message


# return all messages in the inbox
def get_inbox():
    return Message.objects.filter(flags__flag=MessageFlag.INBOX_FLAG)


def is_sender_legit(email):
    return Message.objects.filter(sender__email='thechild@gmail.com', members__addresses__email=email).exists()


# get all messages from senders that I've replied to before
def get_incoming_inbox():
    inbox = get_inbox()
    return [m for m in inbox if is_sender_legit(m.sender.email)]


def get_other_inbox():
    inbox = get_inbox()
    return [m for m in inbox if not is_sender_legit(m.sender.email)]


# saves content as a file and creates an Attachment connected to message
def handle_attachment(message, content, related=False):
    r = ''
    if related:
        r = '(r)'

    filename, encoding = decode_header(content.get_filename())[0]
    if encoding:
        filename = filename.decode(encoding, errors='replace')

    if not related:
        print "saving attachment [%s] of type %s from message %d %s" % (filename, content.get_content_type(), message.id, r)

    a = Attachment()
    a.filename = filename  # TODO need to parse weird strings from this
    if not a.filename:
        a.filename = str(uuid.uuid4())
    a.content_type = content.get_content_type()
    a.stored_location = os.path.join(files_dir, str(message.id), get_valid_filename(a.filename))
        # probably want to fix this too
    a.mime_related = related
        # load the file
    file_content = content.get_payload(decode=1)
    a.file_md5 = hashlib.md5(file_content).hexdigest()  # again, probably a better way to do this than all in memory
    # actually write it do disk - should wrap this in a try except too
    if not os.path.exists(os.path.join(files_dir, str(message.id))):
        os.makedirs(os.path.join(files_dir, str(message.id)))
    with open(a.stored_location, 'wb') as fp:
        fp.write(file_content)
    a.message = message
    a.save()
