from django.db import models
from operator import attrgetter
from itertools import chain
import hashlib
from msgs.helpers import get_reply_from_html, get_reply_from_text
from datetime import datetime

# Create your models here.

class Address(models.Model):
    address = models.CharField(max_length=200, unique=True) #need to make this case insensitive (or at least searching on it)
    name = models.CharField(max_length=200)
    #person = models.ForeignKey(Person)
    # this means that right now you have to deal with addresses not people, but should have a way to combine multiple addresses into one person and operate on the person

    def newest_sent_message(self):
        msgs = self.sent_messages.all().order_by('-sent_date')
        if msgs:
            return msgs[0]
        else:
            return None

    def newest_conversation(self):
        convos = self.conversations.order_by('-latest_message_date')
        if convos:
            return convos[0]
        else:
            return None

    def last_sent_message_snippet(self):
        if len(self.sent_messages.all()) > 0:
            return self.sent_messages.all().order_by('-sent_date')[0].snippet()
        else:
            return ''

    # returns sent messages and received messages, including ccs
    def all_messages(self): # can probably make the db do this...
        msgs = sorted(
                      chain(self.sent_messages.all(),
                            self.received_messages.all(),
                            self.cc_messages.all()),
                      key=attrgetter('sent_date'))
        return msgs

    def sent_attachments(self):
        return Attachment.objects.filter(message__sender=self).exclude(mime_related=True).order_by('-message__sent_date')

    def __unicode__(self):
        return "%s <%s>" % (self.name, self.address)

class Conversation(models.Model):
    creator = models.ForeignKey(Address, related_name='started_conversations', null=True)
    members = models.ManyToManyField(Address, related_name='conversations')
    subject = models.TextField()
    message_id = models.CharField(max_length=200)
    thread_id = models.CharField(max_length=200, unique=True, null=True)
    latest_message_date = models.DateTimeField(default=datetime(1980, 1, 1))

    def add_message(self, message):
        if message not in self.messages.all():
            self.messages.add(message)
            if message.sent_date > self.latest_message_date:
                self.latest_message_date = message.sent_date
                self.save()
            for person in message.all_related_people():
                self.members.add(person)

    def trimmed_members(self):
        return self.members.exclude(get_current_user())

    def original_message(self):
        return self.sorted_messages()[0]

    def sorted_messages(self):
        return self.messages.order_by('-sent_date')

    def latest_message(self):
        return self.messages.order_by('-sent_date')[0]

    def attachments_count(self):
        return self.attachments().count()

    def attachments(self):  # currently orders by oldest first
        a = Attachment.objects.filter(message__conversation=self)
        a = a.exclude(mime_related=True)
        a = a.order_by('message__sent_date')
        return a

    def __unicode__(self):
        return "[%s] - %d messages, %d participants" % (self.subject, self.messages.count(), self.members.count())


class Message(models.Model):
    sender = models.ForeignKey(Address, related_name='sent_messages')
    recipients = models.ManyToManyField(Address, related_name='received_messages')
    cc_recipients = models.ManyToManyField(Address, related_name='cc_messages')
    subject = models.CharField(max_length=200, default='')
    sent_date = models.DateTimeField()
    body_text = models.TextField()
    body_html = models.TextField()
    message_id = models.CharField(max_length=200)
    related_messages = models.ManyToManyField('self')
    thread_index = models.CharField(max_length=200, blank=True, null=True, default=None)
    group_hash = models.CharField(max_length=40, blank=True, null=True)
    parent = models.ForeignKey('self', related_name='children', blank=True, null=True, default=None)
    conversation = models.ForeignKey(Conversation, related_name='messages', blank=True, null=True, default=None)

    def body_reply_text(self):
        return get_reply_from_text(self.body_text)

    def body_remaining_text(self):
        rt = self.body_reply_text()
        a = self.body_text.find(rt)
        if a > -1:
            return self.body_text[a+len(rt):]
        else:
            return self.body_text

    def body_reply_html(self):
        print "called body_reply_html on message %d" % self.id
        return get_reply_from_html(self.body_reply_text(), self.body_html)

    def thread_messages(self):
        return self.children.order_by('sent_date')

    def cleaned_subject(self):
        return self.subject.replace('re: ','').replace('Re: ','').replace('RE: ','').replace('FW: ','').replace('Fwd: ','')

    def all_related_people(self):
        people = set(chain(self.recipients.all(), self.cc_recipients.all()))
        people.add(self.sender)
        sorted_people = sorted(people, key=attrgetter('id'))
        return sorted_people

    def snippet(self):
        return self.body_reply_text()[:75]

    def __unicode__(self):
        return "[%s] <%s> Subject: %s From: %s To: %s" % (self.id, self.message_id, self.subject, self.sender, self.recipients.all())


class Header(models.Model):
    message = models.ForeignKey(Message, related_name="headers")
    field = models.CharField(max_length=200)
    text = models.TextField()

    def __unicode__(self):
        return "%s: %s" % (self.field, self.text)


class Attachment(models.Model):
    filename = models.CharField(max_length=200)
    content_type = models.CharField(max_length=50)
    stored_location = models.CharField(max_length=200)
    file_md5 = models.CharField(max_length=40)
    message = models.ForeignKey(Message, related_name='attachments')
    mime_related = models.BooleanField(default=False)

    def __unicode__(self):
        return self.filename

    # should probably override delete and actually delete the file too


def get_current_user():
    # obviously a hack
    # return Address.objects.get(address='cchild@redpoint.com')
    return Address.objects.get(address='thechild@gmail.com')


def get_sorted_conversations():
    conversations = Conversation.objects.filter(members=get_current_user()).order_by('-latest_message_date')
    return conversations


def get_all_message_threads():
    messages = Message.objects.filter(recipients=get_current_user()).filter(parent__isnull=True).order_by('-sent_date')
    threads = []
    seen_threads = set()
    for message in messages:
        if message.thread_index not in seen_threads:
            seen_threads.add(message.thread_index)
            threads.append(message)
    return threads

# should groups be concrete, or created on the fly?  Let's try concrete but maybe remove it later? Or shoudl I try dynamic first?
