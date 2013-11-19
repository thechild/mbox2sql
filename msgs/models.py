from django.db import models
from operator import attrgetter
from itertools import chain
import hashlib

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

class Message(models.Model):
    # should probably rename these sender and recipients...
    sender = models.ForeignKey(Address, related_name='sent_messages')
    recipients = models.ManyToManyField(Address, related_name='received_messages')
    cc_recipients = models.ManyToManyField(Address, related_name='cc_messages')
    subject = models.CharField(max_length=200, default='')
    sent_date = models.DateTimeField()
    headers = models.TextField()
    body_text = models.TextField()
    body_html = models.TextField()
    message_id = models.CharField(max_length=200)
    related_messages = models.ManyToManyField('self')
    thread_index = models.CharField(max_length=200, blank=True, null=True, default=None)
    group_hash = models.CharField(max_length=40, blank=True, null=True)
    parent = models.ForeignKey('self', related_name='children', blank=True, null=True, default=None)

    def thread_messages(self):
        return self.children.order_by('sent_date')

    def cleaned_subject(self):
        return self.subject.replace('re: ','').replace('Re: ','').replace('RE: ','').replace('FW: ','').replace('Fwd: ','')

    def set_group_hash(self):
        hash_text = ''
        for r in self.all_related_people():
            hash_text = hash_text + str(r.id).zfill(10)
        self.group_hash = hashlib.md5(hash_text).hexdigest()

    def recipient_names(self):
        names = []
        for r in self.recipients.all():
            names.append(str.format('%s <%s>' % (str(r.name), str(r.address))))
        for r in self.cc_recipients.all():
            names.append(str.format('%s <%s>' % (str(r.name), str(r.address))))
        return '\n\t'.join(names)

    def all_related_people(self):
        people = set(chain(self.recipients.all(), self.cc_recipients.all()))
        people.add(self.sender)
        sorted_people = sorted(people, key=attrgetter('id'))
        return sorted_people

    def all_messages_in_group(self):
        return Message.objects.filter(group_hash=self.group_hash)

    def all_messages_in_broader_group(self):
        pass ## need to do this.  may be much easier if I drop cc_recipients and just have one recipients field in the db
        # this should return all messages (or really conversations) that include all the recipients and senders of this message

    def __unicode__(self):
        return "<%s> Subject: %s From: %s To: %s" % (self.message_id, self.subject, self.sender, self.recipients.all())

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

def messages_with_attachments():
    return Message.objects.annotate(num_attachments=models.Count('attachments')).filter(num_attachments__gt=0)

# next things to create: Conversations and Groups
# should groups be concrete, or created on the fly?  Let's try concrete but maybe remove it later? Or shoudl I try dynamic first?

def messages_from_sender(address):
    return Message.objects.filter(sender__address=address)