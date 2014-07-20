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
    subject = models.CharField()
    sent_date = models.DateTimeField()
    message_id = models.CharField()
    thread_id = models.CharField()


class Header(models.Model):
    key = models.CharField()
    value = models.CharField()
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
