import mailbox, os, hashlib
from datetime import datetime
from email.utils import parsedate_tz, mktime_tz, parseaddr, getaddresses
import pickle
import models

files_dir = 'files' # where to save attachments

# parses all messages in an mbox file, and loads them into the database as Messages, skipping any that already are saved
def load_messages(filename):
    mbox = mailbox.mbox(filename)
    count=0
    skip=0
    for message in mbox:
        m = parse_message(message)
        if m:
            print m
            count = count + 1
        else:
            skip = skip + 1
    print "***Loaded %d messages, skipped %d already in db" % (count,skip)

# takes an email message and returns a Message object
def parse_message(message):
    ## should test to see if it's already in the db
    m = models.Message()
    if message_exists(message['Message-ID']):
        print "skipping message %s - already in db" % message['Message-ID']
        return None

    from_text = parseaddr(message['from'])

    tos = message.get_all('to', [])
    ccs = message.get_all('cc', [])
    tos = tos + message.get_all('resent-to', [])
    ccs = ccs + message.get_all('resent-cc', [])

    m.message_id = message['Message-ID']
    m.sender = parse_address(from_text)
    m.sent_date = datetime.fromtimestamp(mktime_tz(parsedate_tz(message['Date'])))
    m.subject = message['Subject']
    m.headers = pickle.dumps(message._headers)
    if message['Thread-Index']:
        m.thread_index = message['Thread-Index']

    m.save()

    m = fill_in_message_content(m, message)

    for t in getaddresses(tos):
        m.recipients.add(parse_address(t))

    for c in getaddresses(ccs):
        m.cc_recipients.add(parse_address(t))

    m.save()

    m.set_group_hash()
    m.save()

    return m

# tests if a message with message_id is already in the database
def message_exists(message_id):
    return len(models.Message.objects.filter(message_id=message_id)) > 0

# given a Message object and some email content, parses the email by Content-Type and fills in the right fields in the Message object
# doesn't handle multiple text or html parts well right now - just takes the first one - could just do an append?
# if encounters multipart content, it recurses on all the parts
# if Content-Type is not multipart/alternative, multipart/mixed, multipart/related, text/plain or text/html, assumes it's an attachment and reacts accordingly
def fill_in_message_content(message, content):
    if content.get_content_type() in ('multipart/alternative', 'multipart/mixed', 'multipart/related'):
        for part in content.get_payload():
            message = fill_in_message_content(message, part)
    elif content.get_content_type() == 'text/plain':
        message.body_text = content.get_payload()
    elif content.get_content_type() == 'text/html':
        message.body_html = content.get_payload()
    else:
        # assume it's an attachment (this may be a bad idea) and save it to disk
        message.save() # this feels a bit like cheating, but we need an id for the message now
        handle_attachment(message, content)
    return message


# saves content as a file and creates an Attachment connected to message
def handle_attachment(message, content):
    print "saving attachment of type %s from message %d " % (content.get_content_type(), message.id)
    a = models.Attachment()
    a.filename = content.get_filename()
    a.content_type = content.get_content_type()
    a.stored_location = os.path.join(files_dir, str(message.id), a.filename) # probably want to fix this too
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

# takes a Message object and connects it up to other Message objects
def connect_related_messages(message):
    thread_index = ''
    references = ''
    in_reply_to = ''
    thread_messages = []
    replied_message = []

    # first, look for anything with the same thread-index as this message
    # super inefficient, but here goes
    for h in pickle.loads(message.headers):
        title, data = h
        if title == 'Thread-Index':
            thread_index = data
        elif title == 'References':
            references = data.split('\n\t')
        elif title == 'In-Reply-To':
            in_reply_to = data

    # find messages with the same thread index
    if thread_index:
        thread_messages = models.Message.objects.filter(thread_index=thread_index).exclude(id=message.id)

    if in_reply_to:
        replied_messages = models.Message.objects.filter(message_id=in_reply_to)
        if replied_messages:
            replied_message = replied_messages[0]

    if replied_message:
        a = "a"
    else:
        a = "no"
    print "found %d references, %d thread messages, and %s replied messages" % (len(references), len(thread_messages), a)
    for r in references:
        refd_msg = models.Message.objects.filter(message_id=r).exclude(id=message.id)
        if refd_msg:
            message.related_messages.add(refd_msg[0])
    for m in thread_messages:
        message.related_messages.add(m)
    if replied_message:
        message.related_messages.add(replied_message)

    message.save()
