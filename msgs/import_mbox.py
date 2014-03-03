import mailbox, os, hashlib
from datetime import datetime
from email.utils import parsedate_tz, mktime_tz, parseaddr, getaddresses
from email.header import decode_header
import models
import uuid

from threading import setup_threads

files_dir = 'files' # where to save attachments

# parses all messages in an mbox file, and loads them into the database as Messages, skipping any that already are saved
def load_messages(filename='msgs/mbox', thread_all=False):
    mbox = mailbox.mbox(filename)
    count=0
    skip=0
    # first, load the messages into the database
    db_messages = [] # only run threading on the newly added messages - this
    for message in mbox:
        m = parse_message(message)
        if m:
            print m
            db_messages.append(m)
            count = count + 1
        else:
            skip = skip + 1
    print "***Loaded %d messages, skipped %d already in db" % (count,skip)
    # then, figure out threading
    print "Calculating threading..."
    if thread_all:
        setup_threads(models.Message.objects.all())
    else:
        setup_threads(db_messages)

# takes an email message and returns a Message object
def parse_message(message):
    ## should test to see if it's already in the db
    m = models.Message()
    if message_exists(message['Message-ID']):
        print "skipping message %s - already in db" % message['Message-ID']
        return None

    from_text = parseaddr(parse_header(message['from']))

    tos = message.get_all('to', []) + message.get_all('resent-to', [])
    ccs = message.get_all('cc', []) + message.get_all('resent-cc', [])

    m.message_id = message['Message-ID']
    m.sender = parse_address(from_text)
    m.sent_date = datetime.fromtimestamp(mktime_tz(parsedate_tz(message['Date'])))
    m.subject = parse_header(message['Subject'])
    if message['Thread-Index']:
        m.thread_index = message['Thread-Index']
    else:
        m.thread_index = m.message_id # TODO: this should be smarter, doesn't really work right now

    m.save()

    fill_in_headers(m, message._headers)

    m = fill_in_message_content(m, message)

    print "have %d tos and %d ccs" % (len(tos), len(ccs))

    for t in getaddresses(tos):
        print "added %s as to" % str(t)
        m.recipients.add(parse_address(t))

    for c in getaddresses(ccs):
        print "added %s as cc" % str(c)
        m.cc_recipients.add(parse_address(c))

    m.save()

    return m

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

# given a Message object and some email content, parses the email by Content-Type and fills in the right fields in the Message object
# doesn't handle multiple text or html parts well right now - just takes the first one - could just do an append?
# if encounters multipart content, it recurses on all the parts
# if Content-Type is not multipart/alternative, multipart/mixed, multipart/related, text/plain or text/html, assumes it's an attachment and reacts accordingly
def fill_in_message_content(message, content, related=False):
    if content.get_content_type() == 'multipart/related':
        for part in content.get_payload():
            message = fill_in_message_content(message, part, related=True)
    elif content.get_content_type() in ('multipart/alternative', 'multipart/mixed'):
        for part in content.get_payload():
            message = fill_in_message_content(message, part)
    elif content.get_content_type() == 'text/plain':
        message.body_text = unicode(content.get_payload(decode=True), encoding=get_charset(content))
    elif content.get_content_type() == 'text/html':
        message.body_html = unicode(content.get_payload(decode=True), encoding=get_charset(content))
    elif content.get_content_type() == 'text/enriched':
        pass #ignore rich text for now...
    elif 'message/' in content.get_content_type():
        pass #ignore this for now, but should probably save as an .eml or something?
    else:
        # assume it's an attachment (this may be a bad idea) and save it to disk
        message.save() # this feels a bit like cheating, but we need an id for the message now
        handle_attachment(message, content, related)
    return message


def get_charset(message, default='ascii'):

    if message.get_content_charset():
        return message.get_content_charset()

    if message.get_charset():
        return message.get_charset()

    return default

# saves content as a file and creates an Attachment connected to message
def handle_attachment(message, content, related):
    print "saving attachment of type %s from message %d " % (content.get_content_type(), message.id)
    a = models.Attachment()
    a.filename = content.get_filename() or str(uuid.uuid4())  ## some attachments appear to not have filenames (calendar invites?) so just make one up
    a.content_type = content.get_content_type()ename? WTF do we do then?
    a.stored_location = os.path.join(files_dir, str(message.id), a.filename) # probably want to fix this too
    a.mime_related = related
    # load the file
    file_content = content.get_payload(decode=1)
    a.file_md5 = hashlib.md5(file_content).hexdigest() # again, probably a better way to do this than all in memory
    # actually write it do disk - should wrap this in a try except too
    if not os.path.exists(os.path.join(files_dir, str(message.id))):
        os.makedirs(os.path.join(files_dir, str(message.id)))
    with open(a.stored_location, 'wb') as fp:
        fp.write(file_content)
    a.message = message
    a.save()

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
