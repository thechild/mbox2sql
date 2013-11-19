from email_reply_parser import EmailReplyParser
from HTMLParser import HTMLParser

def get_reply_from_text(text):
    return EmailReplyParser.parse_reply(text)

def get_stripped_html_simple(text, html):
    a = html.find(text)
    if a > -1:
        return html[0:a+len(text)]

class MyHTMLParser(HTMLParser):
    search_text = ""
    found_search_text = False
    open_tags = []
    built_text = ""

    def handle_starttag(self, tag, attrs):
        if not self.found_search_text:
            self.open_tags.insert(0,tag)
            self.built_text = self.built_text + self.get_starttag_text()

    def handle_endtag(self, tag):
        if tag in self.open_tags:
            self.open_tags.remove(tag)
            self.built_text = self.built_text + ("</%s>" % tag)
        elif not self.found_search_text:
            print "tag closing that wasn't opened - leaving out: %s" % tag

    def handle_data(self, data):
        if not self.found_search_text: # if we found it, who cares
            if self.search_text in data:
                # found it
                self.found_search_text = True
            self.built_text = self.built_text + data

def get_reply_from_html(text, html):
    parser = MyHTMLParser()
    lines = text.split("\n")
    lines.reverse()
    for l in lines:
        if l:
            parser.search_text = l
            break

    if parser.search_text:
        parser.feed(html)
        return parser.built_text
    else:
        return html