from django.db import models

# Create your models here.

class Address(models.Model):
    address = models.CharField(max_length=200, unique=True) #need to make this case insensitive (or at least searching on it)
    name = models.CharField(max_length=200)
    #person = models.ForeignKey(Person)
    # this means that right now you have to deal with addresses not people, but should have a way to combine multiple addresses into one person and operate on the person

    def __unicode__(self):
        return "%s <%s>" % (self.name, self.address)

class Message(models.Model):
    # should probably rename these sender and recipients...
    sender = models.ForeignKey(Address, related_name='sent_messages')
    recipients = models.ManyToManyField(Address, related_name='received_messages')
    cc_recipients = models.ManyToManyField(Address, related_name='cc_messages')
    ## need to add CC
    subject = models.CharField(max_length=200, default='')
    sent_date = models.DateTimeField()
    headers = models.TextField()
    body_text = models.TextField()
    body_html = models.TextField()
    message_id = models.CharField(max_length=200)
    related_message_ids = models.CharField(max_length=1000)
    related_messages = models.ManyToManyField('self', related_name='m+')

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

def messages_with_attachments():
    return Message.objects.annotate(num_attachments=models.Count('attachments')).filter(num_attachments__gt=0)

# next things to create: Conversations and Groups
# should groups be concrete, or created on the fly?  Let's try concrete but maybe remove it later? Or shoudl I try dynamic first?
