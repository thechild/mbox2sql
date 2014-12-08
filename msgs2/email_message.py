from datetime import datetime
from email.utils import parsedate_tz, mktime_tz, parseaddr, getaddresses
from email.header import decode_header
import re


class EmailMessage():

    body = {}
    attachments = []
    related_attachments = []

    def __init__(self, msg):
        self._email_message = msg
        self.raw_headers = {}
        self.thread_id = None
        self.message_id = None
        self.parse_content(self._email_message)
        self.parse_headers()

    def __repr(self):
        return 'EmailMessage(subject="%s", sender="%s")' % (self.subject, self.sender)

    def parse_content(self, content, related=False):
        ct = content.get_content_type()
        if content.is_multipart():
            r = '/related' in ct
            for part in content.get_payload():
                self.parse_content(part, related=r)
        elif 'text/' in ct:
            key = ct.replace('text/', '')
            cur_val = self.body.setdefault(key, '')
            self.body[key] = cur_val + unicode(content.get_payload(decode=True), encoding=get_charset(content))
        elif 'message/' in ct:
            pass  # TODO go down this rabbit hole later
        else:
            # assume it's an attachment since we don't know what to do with it
            if related:
                self.related_attachments.append(content)
            else:
                self.attachments.append(content)

    def parse_headers(self):

        for hdr in self._email_message.keys():
            self.raw_headers[hdr] = self._email_message[hdr]




        raw_headers = self._email_message.raw_headers


        if re.search(r'X-GM-THRID (\d+)', raw_headers):
            self.thread_id = re.search(r'X-GM-THRID (\d+)', raw_headers).groups(1)[0]
        if re.search(r'X-GM-MSGID (\d+)', raw_headers):
            self.message_id = re.search(r'X-GM-MSGID (\d+)', raw_headers).groups(1)[0]


    @property
    def sender(self):
        from_text = parseaddr(parse_header(self._email_message['from']))
        return from_text

    @property
    def tos(self):
        tos = self._email_message.get_all('to', []) + self._email_message.get_all('resent-to', [])
        return getaddresses(tos)

    @property
    def ccs(self):
        ccs = self._email_message.get_all('cc', []) + self._email_message.get_all('resent-cc', [])
        return getaddresses(ccs)

    @property
    def sent_date(self):
        return datetime.fromtimestamp(mktime_tz(parsedate_tz(self._email_message['Date'])))

    @property
    def subject(self):
        return parse_header(self._email_message['Subject'])

    @property
    def headers(self):
        return [decode_header(h) for h in self._email_message.items()]


# absurd that you have to do this...
def parse_header(subject):
    dh = decode_header(subject)
    default_charset = 'ASCII'
    return ''.join([unicode(t[0], t[1] or default_charset) for t in dh])


def get_charset(message, default='ascii'):
    if message.get_content_charset():
        return message.get_content_charset()

    if message.get_charset():
        return message.get_charset()

    return default
