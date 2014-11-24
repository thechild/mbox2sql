from django.db import models
from collections import OrderedDict
import datetime

files_dir = 'files'


class Person(models.Model):
    name = models.CharField(max_length=200)

    def __unicode__(self):
        addresses = ', '.join(str.format("<%s>", x.email) for x in self.addresses.all())
        return "<Person %s [%s]>" % (self.name, addresses)


class Address(models.Model):
    email = models.EmailField()
    label = models.CharField(max_length=50)
    person = models.ForeignKey(Person, related_name='addresses')

    def __unicode__(self):
        return "{}".format(self.email)


class Account(models.Model):
    TYPE_EXCHANGE = 'E'
    TYPE_GMAIL = 'G'

    SERVER_TYPES = (
        (TYPE_EXCHANGE, 'Exchange'),
        (TYPE_GMAIL, 'Gmail'))

    name = models.CharField(max_length=200)
    server_type = models.CharField(max_length=1, choices=SERVER_TYPES)
    address = models.CharField(max_length=200)

    def email_address(self):
        if self.server_type == self.TYPE_EXCHANGE:
            parts = self.address.split('\\')
            return u"{}@{}".format(parts[1], parts[0])
        else:
            return self.address

    def __unicode__(self):
        return "{}: {}".format(self.name, self.address)


class Message(models.Model):
    sender = models.ForeignKey(Address, related_name='sent_messages')
    recipients = models.ManyToManyField(Address,
                                        related_name='received_messages')
    members = models.ManyToManyField(Person, related_name='messages')
    subject = models.TextField()
    sent_date = models.DateTimeField()
    message_id = models.CharField(max_length=200)
    thread_id = models.CharField(max_length=200)
    account = models.ForeignKey(Account, related_name='messages', null=True)

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

    def __unicode__(self):
        return [y[1] for y in MessageFlag.FLAGS if y[0] == self.flag][0]


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
        return "[{}]: {}".format(self.type, self.content)


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


# return all messages in the inbox
def get_inbox():
    return Message.objects.filter(flags__flag=MessageFlag.INBOX_FLAG)


# get all messages from senders that I've replied to before
def get_incoming_inbox():
    inbox = get_inbox()
    return [m for m in inbox if is_sender_legit(m.sender.email)]


# gets all messages in inbox but not in get_incoming_inbox()
def get_other_inbox():
    inbox = get_inbox()
    return [m for m in inbox if not is_sender_legit(m.sender.email)]


# return a list of unique threads from a list of messages.
# can be called on get_inbox(), get_incoming_inbox(), get_other_inbox(), or any list of Message objects
def get_threads_from_messages(messages):
    thread_ids = list(OrderedDict.fromkeys([m.thread_id for m in messages]))
    return [Message.objects.filter(thread_id=tid) for tid in thread_ids]


def get_thread_for_message(message):
    return Message.objects.filter(thread_id=message.thread_id)


def is_sender_legit(email):
    return Message.objects.filter(sender__email='thechild@gmail.com', members__addresses__email=email).exists()
