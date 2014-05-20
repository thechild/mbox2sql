from datetime import datetime
from email.header import decode_header
import models

# absurd that you have to do this...
def parse_header(subject):
    dh = decode_header(subject)
    default_charset = 'ASCII'
    return ''.join([ unicode(t[0], t[1] or default_charset) for t in dh ])

def fill_in_headers(message, headers):
    for field, text in headers:
        nh = models.Header()
        nh.field = field
        nh.text = text
        nh.message = message
        nh.save()

# tests if a message with message_id is already in the database
def message_exists(message_id):
    return len(models.Message.objects.filter(message_id=message_id)) > 0

def get_charset(message, default='ascii'):
    if message.get_content_charset():
        return message.get_content_charset()

    if message.get_charset():
        return message.get_charset()

    return default

## takes an email address tuple ('name', 'address') and returns and Address object (either existing or newly created)
def parse_address(raw_address):
    print raw_address

    text_name, text_address = raw_address

    text_address = text_address.lower()

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
        if text_name and not address.name: # if we didn't find a name before but have one now, update it
            address.name = text_name
            address.save()
    return address