from django.db import models
from operator import attrgetter
from itertools import chain
import hashlib
from msgs.helpers import get_reply_from_html, get_reply_from_text

# Create your models here.

class Address(models.Model):
    address = models.CharField(max_length=200, unique=True) #need to make this case insensitive (or at least searching on it)
    name = models.CharField(max_length=200)
    #person = models.ForeignKey(Person)
    # this means that right now you have to deal with addresses not people, but should have a way to combine multiple addresses into one person and operate on the person

    # returns sent messages and received messages, including ccs
    def all_messages(self):
        msgs = sorted(
            chain(self.sent_messages.all(),
                self.received_messages.all(),
                self.cc_messages.all()
                ),
            key=attrgetter('sent_date')
            )
        return msgs

    def sent_attachments(self):
        attachments = []
        for m in self.sent_messages.all():
            attachments = attachments + list(m.attachments.all())
        return attachments

    def __unicode__(self):
        return "%s <%s>" % (self.name, self.address)

class Conversation(models.Model):
    creator = models.ForeignKey(Address, related_name='started_conversations', null=True)
    members = models.ManyToManyField(Address, related_name='conversations')
    subject = models.TextField()

    def sorted_messages(self):
        return self.messages.order_by('-sent_date')

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

    def __unicode__(self):
        return self.filename

    # should probably override delete and actually delete the file too

def get_all_message_threads():
    messages = Message.objects.filter(parent__isnull=True).order_by('-sent_date')
    threads = []
    seen_threads = set()
    for message in messages:
        if message.thread_index not in seen_threads:
            seen_threads.add(message.thread_index)
            threads.append(message)
    return threads

# next things to create: Conversations and Groups
# should groups be concrete, or created on the fly?  Let's try concrete but maybe remove it later? Or shoudl I try dynamic first?
