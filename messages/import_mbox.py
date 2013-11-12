import mailbox
import re
import models
from email.utils import parsedate_tz, mktime_tz, parseaddr
from datetime import datetime

class mbox:

    def __init__(self, mbox):
        self.mbox = mailbox.mbox(mbox)

    def load_messages(self):
        for message in self.mbox:
            m = parse_message(message)
            print m

def parse_message(message):
    ## should test to see if it's already in the db
    m = models.Message()
    if message_exists(message['Message-ID']):
        print "skipping message %s - already in db" % message['Message-ID']
        return None

    from_text = message['from']
    to_text = message['to']

    m.message_id = message['Message-ID']
    m.from_address = parse_address(from_text)
    m.sent_date = datetime.fromtimestamp(mktime_tz(parsedate_tz(message['Date'])))
    m.subject = message['Subject']
    m.headers = ''
    m.raw_message = message.as_string()

    m = fill_in_message_content(m, message)

    m.save()

    for t in to_text.split(','):
        m.to_address.add(parse_address(t))

    m.save()

    return m

def message_exists(message_id):
    return len(models.Message.objects.filter(message_id=message_id)) > 0

def fill_in_message_content(message, content):
    if content.get_content_type() in ('multipart/alternative', 'multipart/mixed', 'multipart/related'):
        for part in content.get_payload():
            message = fill_in_message_content(message, part)
    elif content.get_content_type() == 'text/plain':
        message.body_text = content.get_payload()
    elif content.get_content_type() == 'text/html':
        message.body_html = content.get_payload()
    else:
        print 'unknown part of type %s in message %s' % (content.get_content_type(), message.message_id)
    return message

def parse_address(address):
    name, email = parseaddr(address)
    return get_address(email, name)

def get_address(text_address, text_name):
    address = None
    matches = models.Address.objects.filter(address=text_address)
    if len(matches) == 0:
        address = models.Address()
        print 'creating new address: (%s %s)' % (text_name, text_address)
        address.name = text_name
        address.address = text_address
        address.save()
    else:
        address = matches[0]
    return address

