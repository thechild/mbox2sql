import datetime
import email
import re
import time
import os
from email.header import decode_header, make_header
from email.utils import getaddresses
from imaplib import ParseFlags


class Message():

    def __repr__(self):
        return '<Message: uid: %s date: %s subject %s>' % (self.uid, self.sent_at, self.subject)

    def __init__(self, mailbox, uid):
        self.uid = uid
        self.mailbox = mailbox
        self.gmail = mailbox.gmail if mailbox else None

        self.message = None
        self.headers = {}

        self.subject = None
        self.body = None
        self.html = None

        self.to = None
        self.fr = None
        self.cc = None
        self.delivered_to = None
        self.members = None

        self.sent_at = None

        self.flags = []
        self.labels = []

        self.thread_id = None
        self.thread = []
        self.message_id = None

        self.attachments = []

    def is_read(self):
        return ('\\Seen' in self.flags)

    def read(self):
        flag = '\\Seen'
        self.gmail.imap.uid('STORE', self.uid, '+FLAGS', flag)
        if flag not in self.flags: self.flags.append(flag)

    def unread(self):
        flag = '\\Seen'
        self.gmail.imap.uid('STORE', self.uid, '-FLAGS', flag)
        if flag in self.flags: self.flags.remove(flag)

    def is_starred(self):
        return ('\\Flagged' in self.flags)

    def star(self):
        flag = '\\Flagged'
        self.gmail.imap.uid('STORE', self.uid, '+FLAGS', flag)
        if flag not in self.flags: self.flags.append(flag)

    def unstar(self):
        flag = '\\Flagged'
        self.gmail.imap.uid('STORE', self.uid, '-FLAGS', flag)
        if flag in self.flags: self.flags.remove(flag)

    def is_draft(self):
        return ('\\Draft' in self.flags)

    def has_label(self, label):
        full_label = '%s' % label
        return (full_label in self.labels)

    def add_label(self, label):
        full_label = '%s' % label
        self.gmail.imap.uid('STORE', self.uid, '+X-GM-LABELS', full_label)
        if full_label not in self.labels: self.labels.append(full_label)

    def remove_label(self, label):
        full_label = '%s' % label
        self.gmail.imap.uid('STORE', self.uid, '-X-GM-LABELS', full_label)
        if full_label in self.labels: self.labels.remove(full_label)


    def is_deleted(self):
        return ('\\Deleted' in self.flags)

    def delete(self):
        flag = '\\Deleted'
        self.gmail.imap.uid('STORE', self.uid, '+FLAGS', flag)
        if flag not in self.flags: self.flags.append(flag)

        trash = '[Gmail]/Trash' if '[Gmail]/Trash' in self.gmail.labels() else '[Gmail]/Bin'
        if self.mailbox.name not in ['[Gmail]/Bin', '[Gmail]/Trash']:
            self.move_to(trash)

    # def undelete(self):
    #     flag = '\\Deleted'
    #     self.gmail.imap.uid('STORE', self.uid, '-FLAGS', flag)
    #     if flag in self.flags: self.flags.remove(flag)

    def move_to(self, name):
        self.gmail.copy(self.uid, name, self.mailbox.name)
        if name not in ['[Gmail]/Bin', '[Gmail]/Trash']:
            self.delete()

    def archive(self):
        self.move_to('[Gmail]/All Mail')

    def parse_headers(self, message):
        hdrs = {}
        for hdr in message.keys():
            hdrs[unicode(hdr)] = message[unicode(hdr)]
        return hdrs

    def parse_flags(self, headers):
        return list(ParseFlags(headers))
        # flags = re.search(r'FLAGS \(([^\)]*)\)', headers).groups(1)[0].split(' ')

    def parse_labels(self, headers):
        if re.search(r'X-GM-LABELS \(([^\)]+)\)', headers):
            labels = re.search(r'X-GM-LABELS \(([^\)]+)\)', headers).groups(1)[0].split(' ')
            return map(lambda l: l.replace('"', '').decode("string_escape"), labels)
        else:
            return list()

    def parse_encoded(self, encoded_subject):
        dh = decode_header(encoded_subject)
        default_charset = 'ASCII'
        return ''.join([ unicode(t[0], t[1] or default_charset, 'replace') for t in dh ])

    def parse_recipients(self):
        self.to = getaddresses(self.message.get_all('to', []))
        self.cc = getaddresses(self.message.get_all('cc', []))
        resent_tos = getaddresses(self.message.get_all('resent-to', []))
        resent_ccs = getaddresses(self.message.get_all('resent-cc', []))
        self.delivered_to = getaddresses(self.message.get_all('delivered_to', []))
        self.fr = getaddresses(self.message.get_all('from', []))[0]
        self.members = set([(self.parse_encoded(n),e) for (n, e) in self.to + self.cc + resent_tos + resent_ccs + [self.fr]])
        self.fr = (self.parse_encoded(self.fr[0]), self.fr[1])
        return self.members

    def parse(self, raw_message):
        raw_headers = raw_message[0]
        raw_email = raw_message[1]

        self.message = email.message_from_string(raw_email)
        self.headers = self.parse_headers(self.message)

        self.parse_recipients()

        self.subject = self.parse_encoded(self.message['subject'])

        #if self.message.get_content_maintype() == "multipart":
        #    for content in self.message.walk():
        #        if content.get_content_type() == "text/plain":
        #            self.body = content.get_payload(decode=True)
        #        elif content.get_content_type() == "text/html":
        #            self.html = content.get_payload(decode=True)
        #elif self.message.get_content_maintype() == "text":
        #    self.body = self.message.get_payload()

        self.cc_message_parse(self.message)

        self.flags = self.parse_flags(raw_headers)

        self.labels = self.parse_labels(raw_headers)

        if re.search(r'X-GM-THRID (\d+)', raw_headers):
            self.thread_id = re.search(r'X-GM-THRID (\d+)', raw_headers).groups(1)[0]
        if re.search(r'X-GM-MSGID (\d+)', raw_headers):
            self.message_id = re.search(r'X-GM-MSGID (\d+)', raw_headers).groups(1)[0]

        if self.message['date']:
            self.sent_at = datetime.datetime.fromtimestamp(time.mktime(email.utils.parsedate_tz(self.message['date'])[:9]))
        else:
            self.sent_at = datetime.datetime(year=1980, month=1, day=1)
            print "Message {} <{}> didn't have a sent date, setting to 1/1/1980".format(self.message_id, self.subject)

        # Parse attachments into attachment objects array for this message
        #self.attachments = [
        #    Attachment(attachment) for attachment in self.message._payload
        #        if not isinstance(attachment, basestring) and attachment.get('Content-Disposition') is not None
        #]

    @staticmethod
    def get_decoded_payload(content):

        if content.get_content_charset():
            encoding = content.get_content_charset()
        elif content.get_charset():
            encoding = content.get_content_charset()
        else:
            encoding = 'ascii'

        payload = content.get_payload(decode=True)

        try:
            decoded = payload.decode(encoding, 'replace')
        except UnicodeDecodeError:
            decoded = payload.decode('utf8', errors='replace')
        except LookupError:
            decoded = payload.decode('utf8', errors='replace')

        return decoded

    def cc_message_parse(self, content, related=False):
        if content.get_content_type() == 'multipart/related':
            for part in content.get_payload():
                self.cc_message_parse(part, related=True)
        elif content.get_content_type() in ('multipart/alternative', 'multipart/mixed'):
            for part in content.get_payload():
                self.cc_message_parse(part)
        elif content.get_content_type() == 'text/plain':
            self.body = self.get_decoded_payload(content)
        elif content.get_content_type() == 'text/html':
            self.html = self.get_decoded_payload(content)
        elif content.get_content_type() == 'text/enriched':
            pass  # ignore rich text for now...
        elif 'message/' in content.get_content_type():
            pass  # ignore this for now, but should probably save as an .eml or something?
        else:
            self.attachments.append((content, related))

    def fetch(self):
        if not self.message:
            response, results = self.gmail.imap.uid('FETCH', self.uid, '(BODY.PEEK[] FLAGS X-GM-THRID X-GM-MSGID X-GM-LABELS)')

            self.parse(results[0])

        return self.message

    # returns a list of fetched messages (both sent and received) in chronological order
    def fetch_thread(self):
        self.fetch()
        print "fetching thread id: %s" % self.thread_id

        original_mailbox = self.mailbox

        #btw, this doesn't search all_mail, just the current mailbox.  I think i'll generally be calling it from all_mail, but need to be careful
        def fetch_and_cache_messages(gmail, mailbox, thread_id):
            gmail.use_mailbox(mailbox.name)
            response, results = gmail.imap.uid('SEARCH', None, '(X-GM-THRID ' + thread_id + ')')
            messages = {}
            if response == 'OK':
                uids = results[0].split(' ')
                for uid in uids:
                    messages[uid] = Message(mailbox, uid)
                if messages:
                    gmail.fetch_multiple_messages(messages)
                    mailbox.messages.update(messages)

            return messages

        # should this first line use the all_mail mailbox, or self.mailbox?  Also, if we use all mail do we need sent mail?
        received_messages = fetch_and_cache_messages(self.gmail, self.gmail.mailboxes['[Gmail]/All Mail'], self.thread_id)
        # print "got %s received messages from %s" % (len(received_messages), self.gmail.current_mailbox)
        #sent_messages = fetch_and_cache_messages(self.gmail, self.gmail.mailboxes['[Gmail]/Sent Mail'], self.thread_id)
        #print "and %s sent messages from %s" % (len(sent_messages), self.gmail.current_mailbox)
        #if set(received_messages).issuperset(sent_messages):
        #    print "all sent messages were included in all mail pull"
        #else:
        #    print "XXX: some sent messages were not included in all mail pull" # should have some debugging output here
        sent_messages = {}

        self.gmail.use_mailbox(original_mailbox.name)

        self.thread = sorted(dict(received_messages.items() + sent_messages.items()).values(),
            key=lambda m: m.sent_at)

        print "fetched {} messages".format(len(received_messages))
        return self.thread


    def fetch_thread_old(self):
        self.fetch()
        original_mailbox = self.mailbox
        self.gmail.use_mailbox(original_mailbox.name)

        # fetch and cache messages from inbox or other received mailbox
        response, results = self.gmail.imap.uid('SEARCH', None, '(X-GM-THRID ' + self.thread_id + ')')
        received_messages = {}
        uids = results[0].split(' ')
        if response == 'OK':
            for uid in uids:
                received_messages[uid] = Message(original_mailbox, uid)
            if received_messages:
                self.gmail.fetch_multiple_messages(received_messages)
                self.mailbox.messages.update(received_messages)

        # fetch and cache messages from 'sent'
        self.gmail.use_mailbox('[Gmail]/Sent Mail')
        response, results = self.gmail.imap.uid('SEARCH', None, '(X-GM-THRID ' + self.thread_id + ')')
        sent_messages = {}
        uids = results[0].split(' ')
        if response == 'OK':
            for uid in uids:
                sent_messages[uid] = Message(self.gmail.mailboxes['[Gmail]/Sent Mail'], uid)
            if sent_messages:
                self.gmail.fetch_multiple_messages(sent_messages)
                self.gmail.mailboxes['[Gmail]/Sent Mail'].messages.update(sent_messages)

        self.gmail.use_mailbox(original_mailbox.name)

        # combine and sort sent and received messages
        return sorted(dict(received_messages.items() + sent_messages.items()).values(), key=lambda m: m.sent_at)


class Attachment:

    def __init__(self, attachment):
        self.name = attachment.get_filename()
        # Raw file data
        self.payload = attachment.get_payload(decode=True)
        self.content_type = attachment.get_content_type()
        # Filesize in kilobytes
        self.size = int(round(len(self.payload)/1000.0))

    def save(self, path=None):
        if path is None:
            # Save as name of attachment if there is no path specified
            path = self.name
        elif os.path.isdir(path):
            # If the path is a directory, save as name of attachment in that directory
            path = os.path.join(path, self.name)

        with open(path, 'wb') as f:
            f.write(self.payload)


def get_charset(message, default='utf8'):

        if message.get_content_charset():
            default = message.get_content_charset()

        if message.get_charset():
            default = message.get_charset()

        print "charset: %s" % default
        return default
