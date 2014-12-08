import os
import hashlib
import uuid
from models import Message, Address, Person, MessageBody, MessageFlag, Header, Attachment
from models import files_dir
from django.utils.text import get_valid_filename
from email.Header import decode_header


def sync_flags(account, flagged_messages, flag):
    # make sure all messages in flagged_messages are flagged
    # can probably remove this loop as long as we're calling load_item with inbox=True...
    added = 0
    for message in flagged_messages:
        if flag == MessageFlag.INBOX_FLAG:
            if not message.is_in_inbox:
                message.flags.add(MessageFlag(flag=flag))
                added += 1
        elif flag == MessageFlag.UNREAD_FLAG:
            if not message.is_unread:
                message.flags.add(MessageFlag(flag=flag))
                added += 1
        else:
            raise Exception("Flag %s is not a syncable flag." % flag)

    # remove all messages that aren't in inbox_messages from inbox
    bad_inbox_flags = MessageFlag.objects.filter(message__account=account)
    bad_inbox_flags = bad_inbox_flags.filter(flag=flag)
    bad_inbox_flags = bad_inbox_flags.exclude(message__in=flagged_messages)
    removed = len(bad_inbox_flags)
    bad_inbox_flags.delete()

    print "Added {} flags and removed {} flags.".format(added, removed)

def get_or_create_person(address_tuple):
    name, email_address = address_tuple
    existing_addresses = Address.objects.filter(email=email_address.lower())
    if len(existing_addresses) == 0:
        new_person = Person(name=name)
        new_person.save()
        new_address = Address(email=email_address.lower(), person=new_person)
        new_address.save()
        return new_address
    elif len(existing_addresses) > 0:
        if len(existing_addresses) > 1:
            print "found multiple db entries for address %s - returning first" % email_address
        existing_address = existing_addresses[0]
        if existing_address.person.name == '':
            existing_address.person.name = name
            existing_address.person.save()
        return existing_address


def create_message(email_message):
    if email_message:
        message = Message()
        message.subject = email_message.subject
        message.sent_date = email_message.sent_date
        message.message_id = email_message.message_id
        message.thread_id = email_message.thread_id  # where should this logic live?


# saves content as a file and creates an Attachment connected to message
def handle_attachment(message, content, related=False):
#    r = ''
#    if related:
#        r = '(r)'

    filename, encoding = decode_header(content.get_filename())[0]
    if encoding:
        filename = filename.decode(encoding, errors='replace')

    #if not related:
    #    print "saving attachment [%s] of type %s from message %d %s" % (filename, content.get_content_type(), message.id, r)

    a = Attachment()
    a.filename = filename  # TODO need to parse weird strings from this
    if not a.filename:
        a.filename = str(uuid.uuid4())
    a.content_type = content.get_content_type()
    a.stored_location = os.path.join(files_dir, str(message.id), get_valid_filename(a.filename))
        # probably want to fix this too
    a.mime_related = related
        # load the file
    file_content = content.get_payload(decode=1)
    a.file_md5 = hashlib.md5(file_content).hexdigest()  # again, probably a better way to do this than all in memory
    # actually write it do disk - should wrap this in a try except too
    if not os.path.exists(os.path.join(files_dir, str(message.id))):
        os.makedirs(os.path.join(files_dir, str(message.id)))
    with open(a.stored_location, 'wb') as fp:
        fp.write(file_content)
    a.message = message
    a.save()


def import_message(gmail_message, account, save_attachments=True):
    # see if the message is already in the db
    if len(Message.objects.filter(message_id=gmail_message.message_id)) > 0:
        # already exists, skip
        # print "Message Id %s already in database, skipping (Subject: %s)" % (gmail_message.message_id, gmail_message.subject)
        # maybe update read status, or inbox status if I can figure out how to do that?
        return None

    new_message = Message(subject=gmail_message.subject,
                          sent_date=gmail_message.sent_at,
                          message_id=gmail_message.message_id,
                          thread_id=gmail_message.thread_id,
                          account=account)
    # new_message.save()
    # add the senders
    new_message.sender = get_or_create_person(gmail_message.fr)
    new_message.save()
    new_message.members.add(new_message.sender.person)
    for person in gmail_message.to + gmail_message.cc:
        p = get_or_create_person(person)
        new_message.recipients.add(p)
        new_message.members.add(p.person)

    new_message.save()
    if gmail_message.body:
        body_text = MessageBody(message=new_message,
                                type='text',
                                content=gmail_message.body)
        body_text.save()

    if gmail_message.html:
        body_html = MessageBody(message=new_message,
                                type='html',
                                content=gmail_message.html)
        body_html.save()

    if not gmail_message.is_read():
        new_message.flags.add(MessageFlag(flag=MessageFlag.UNREAD_FLAG))

    # add the headers
    for k, v in gmail_message.headers.iteritems():
        new_message.headers.add(Header(key=k, value=v))

    # need to handle attachments
    if save_attachments:
        for att, related in gmail_message.attachments:
            handle_attachment(new_message, att, related)

    return new_message
