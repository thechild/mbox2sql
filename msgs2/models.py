from django.db import models
import datetime

files_dir = 'files' #this should be a variable somewhere...

class Thread(models.Model):
    account = models.ForeignKey('Account', related_name='threads')
    thread_id = models.CharField(max_length=200)

    @property
    def subject(self):
        return self.messages.all().order_by('sent_date')[0].subject #grab the subject of the oldest message

    @property
    def members(self):
        s = set()
        for m in self.messages.all():
            s.update(m.members.all())
        return list(s)

    def __unicode__(self):
        return "Thread <{}>, Subject <{}>, Messages <{}>".format(self.thread_id, self.subject, self.messages.all().count())


    def as_json(self, include_bodies=False):
        return {'thread_id': self.id,
                'internet_thread_id': self.thread_id,
                'subject': self.subject,
                'members': [member.as_json() for member in self.members],
                'messages': [message.as_json() for message in self.messages.all()]}


class Person(models.Model):
    name = models.CharField(max_length=200)

    def __unicode__(self):
        addresses = ', '.join(str.format("<%s>", x.email) for x in self.addresses.all())
        return "<Person %s [%s]>" % (self.name, addresses)

    def as_json(self):
        return {'name': self.name,
                'person_id': self.id,
                'addresses': [a.as_json(include_name=False) for a in self.addresses.all()]}


class Address(models.Model):
    email = models.EmailField()
    label = models.CharField(max_length=50)
    person = models.ForeignKey(Person, related_name='addresses')

    def __unicode__(self):
        return "{}".format(self.email)

    def as_json(self, include_name=True):
        r = {'email': self.email,
             'address_id': self.id}
        if include_name:
            r['name'] = self.person.name
        return r


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
    thread = models.ForeignKey(Thread, related_name='messages', null=True)
    account = models.ForeignKey(Account, related_name='messages', null=True)
    # need to add support for a snippet, probably dynamic

    @property
    def is_unread(self):
        return self.flags.filter(flag=MessageFlag.UNREAD_FLAG).exists()

    @property
    def is_in_inbox(self):
        return self.flags.filter(flag=MessageFlag.INBOX_FLAG).exists()

    @property
    def is_starred(self):
        return self.flags.filter(flag=MessageFlag.STARRED_FLAG).exists()

    def archive(self):
        self.flags.filter(flag=MessageFlag.INBOX_FLAG).delete()
        # TODO somehow store this for the server...

    def mark_read(self):
        self.flags.filter(flag=MessageFlag.UNREAD_FLAG).delete()
        # TODO somehow store this for the server...

    def __unicode__(self):
        return "Message <Sender: {}, Subject: {}>".format(self.sender.email, self.subject)

    def as_json(self, include_bodies=False):
        m = {}
        m['message_id'] = self.id
        m['thread_id'] = self.thread_id
        m['sender'] = self.sender.as_json()
        m['recipients'] = [r.as_json() for r in self.recipients.all()]
        m['subject'] = self.subject
        m['sent_date'] = self.sent_date
        m['unread'] = self.is_unread
        m['starred'] = self.is_starred
        if include_bodies:
            m['body'] = [b.as_json() for b in self.body.all()]
        m['attachments'] = 'not yet implemented'
        return m


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

    def as_json(self):
        return {'type': self.type,
                'content': self.content}


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
