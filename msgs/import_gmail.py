import os
import hashlib
import models
import gmail.gmail as gmail
from model_helpers import parse_address, message_exists, get_charset
from pprint import pprint

files_dir = 'files'


# log in to gmail using the given username and password, and return the gmail object
def login(un=None, pw=None):
    if not un:
        with open('pw', 'r') as pwf:
            pw = pwf.read()
        un = "thechild@gmail.com"
    print "logging in to gmail as %s" % un
    gm = gmail.login(un, pw)
    if gm.logged_in:
        print "logged in"
    else:
        print "error logging in"
    return gm


# get all messages since date if date is given.  Set inbox_only to False to get all_mail
def import_messages_since(gm, inbox_only=True, date=None):
    mailbox = gm.all_mail()

    if inbox_only:
        mailbox = gm.inbox()

    print "fetching messages in folder %s" % mailbox.name

    if date:
        messages = mailbox.mail(after=date)
    else:
        messages = mailbox.mail()

    print "found %s messages - downloading" % len(messages)

    new_messages = []

    for index, m in enumerate(messages):
        print "fetching messages for message %s of %s" % (index, len(messages))
        m.fetch_thread()
        nm = parse_message(m)
        if nm:
            new_messages.append(nm)
        for tm in m.thread:
            tm.fetch()
            tnm = parse_message(tm)
            if tnm:
                new_messages.append(tnm)

    return new_messages


def parse_conversation(message):
    # want to do a lot of this with the oldest message in thread, so need to find that
    conversations = models.Conversation.objects.filter(thread_id=message.thread_index)
    if len(conversations) == 0:
        conversation = models.Conversation()
        print 'creating new conversation: (%s)' % (message.subject)
        conversation.creator = message.sender
        conversation.subject = message.subject
        conversation.message_id = message.message_id
        conversation.thread_id = message.thread_index
        conversation.save()
    else:
        conversation = conversations[0]
    
    conversation.add_message(message)
    conversation.save()
    # could optimize this by taking in the thread here too


def parse_message(message):
    m = models.Message()
    if message_exists(message.uid):
        print "skiping message %s - already in db" % message.uid
        return None

    m.message_id = message.uid
    m.sender = parse_address(message.fr)
    m.sent_date = message.sent_at
    m.subject = message.subject
    m.thread_index = message.thread_id

    m.save()

    print "headers: %s" % message.headers

    fill_in_headers(m, message.headers)

    m = fill_in_message_content(m, message.message)

    for t in message.to:
        m.recipients.add(parse_address(t))

    for c in message.cc:
        m.cc_recipients.add(parse_address(c))

    m.save()
    parse_conversation(m)

    return m


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
        pass  # ignore rich text for now
    else:
        # assume its an attachment
        message.save()
        handle_attachment(message, content, related)
    return message


def fill_in_headers(message, headers):
    for field, text in headers.iteritems():
        nh = models.Header()
        nh.field = field
        nh.text = text
        nh.message = message
        nh.save()


def handle_attachment(message, content, related):
    print "saving attachment of type %s from message %d " % (content.get_content_type(), message.id)
    a = models.Attachment()
    a.filename = content.get_filename() or content.get_content_type().split('/')[-1]
    a.content_type = content.get_content_type()
    folder = os.path.join(files_dir, str(message.id))
    file_path = os.path.join(folder, a.filename)
    a.stored_location = file_path
    a.mime_related = related
    file_content = content.get_payload(decode=1)
    a.file_md5 = hashlib.md5(file_content).hexdigest()

    if not os.path.exists(folder):
        os.makedirs(folder)
    with open(a.stored_location, 'wb') as fp:
        fp.write(file_content)

    a.message = message
    a.save()
