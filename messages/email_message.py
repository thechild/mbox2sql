from datetime import datetime
from email.utils import parsedate_tz, mktime_tz, parseaddr, getaddresses
from email.header import decode_header


class EmailMessage():

    body = {}
    attachments = []
    related_attachments = []

    def __init__(self, msg):
        self._email_message = msg
        self.parse_content()

    def parse_content(self, content=self._email_message, related=False):
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

    @property
    def sender(self):
        from_text = parseaddr(parse_header(self._email_message['from']))
        return getaddresses(from_text)

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
    return ''.join([ unicode(t[0], t[1] or default_charset) for t in dh])


def get_charset(message, default='ascii'):
    if message.get_content_charset():
        return message.get_content_charset()

    if message.get_charset():
        return message.get_charset()

    return default
