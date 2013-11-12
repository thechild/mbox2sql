from django.db import models

# Create your models here.

class Person(models.Model):
    name = models.CharField(max_length=200)

class Address(models.Model):
    address = models.CharField(max_length=200, unique=True)
    name = models.CharField(max_length=200)
    #person = models.ForeignKey(Person)
    # this means that right now you have to deal with addresses not people, but should have a way to combine multiple addresses into one person and operate on the person

    def __unicode__(self):
        return "%s <%s>" % (self.name, self.address)

class Message(models.Model):
    # should probably rename these sender and recipients...
    from_address = models.ForeignKey(Address, related_name='sent_messages')
    to_address = models.ManyToManyField(Address, related_name='received_messages')
    subject = models.CharField(max_length=200, default='')
    sent_date = models.DateTimeField()
    headers = models.TextField()
    raw_message = models.TextField()
    body_text = models.TextField()
    body_html = models.TextField()
    message_id = models.CharField(max_length=200)
    related_message_ids = models.CharField(max_length=1000)
    related_messages = models.ManyToManyField('self', related_name='m+')

    def __unicode__(self):
        return "<%s> Subject: %s From: %s To: %s" % (self.message_id, self.subject, self.from_address, self.to_address.all())