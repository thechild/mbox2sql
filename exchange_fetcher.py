import exchange
import email
from msgs2.models import Message, Attachment, MessageBody, Header, MessageFlag
import msgs2.importing as importing
import uuid
import os
from django.utils.text import get_valid_filename
import hashlib
from datetime import datetime

class ExchangeFetcher():
	def __init__(self, url, username, password):
		self.exchange = exchange.ExchangeMail(url, username, password)

	def load_inbox(self):
		self.raw_inbox = self.exchange.get_inbox()
		self.processed_inbox = [self.exchange.process_items(m) for m in self.raw_inbox]
		print "Loaded exchange mailbox, found {} messages".format(len(self.processed_inbox))
		for message in self.processed_inbox:
			self.load_item(message)

	def walk_message(self, mime_message, db_message):
		def parse_attachment(message_part):
			content_disposition = message_part.get("Content-Disposition", None)
			if content_disposition:
				dispositions = content_disposition.strip().split(';')
				if bool(content_disposition and dispositions[0].lower() == 'attachment'):
					# what happens to the related stuff?
					file_data = message_part.get_payload(decode=True)
					a = Attachment()
					a.content_type = message_part.get_content_type()

					for param in dispositions[1:]:
						name, value = param.split("=")
						name = name.lower()

						if name == "filename":
							a.filename = value

					if not a.filename:
						a.filename = str(uuid.uuid4())
					a.stored_location = os.path.join(importing.files_dir,
						str(db_message.id),
						get_valid_filename(a.filename))
					a.file_md5  = hashlib.md5(file_data).hexdigest()

					if not os.path.exists(os.path.join(importing.files_dir, str(db_message.id))):
						os.makedirs(os.path.join(importing.files_dir, str(db_message.id)))
					with open(a.stored_location, 'wb') as fp:
						fp.write(file_data)
					a.message = db_message
					a.save()

		def decode_part(part):
			return unicode(
				part.get_payload(decode=True),
				part.get_content_charset() or 'ascii',
				'replace').encode('utf8', 'replace')

		body = ""
		html = ""

		for part in mime_message.walk():
			attachment = parse_attachment(part)
			if not attachment:
				if part.get_content_type() == 'text/plain':
					body += decode_part(part)
				elif part.get_content_type() == 'text/html':
					html += decode_part(part)

		if body != "":
			body_text = MessageBody(message=db_message,
									type='text',
									content=body)
			body_text.save()

		if html != "":
			body_html = MessageBody(message=db_message,
									type='html',
									content=html)
			body_html.save()

	def load_item(self, item):
		if item[0]['m:GetItemResponseMessage']['@ResponseClass'] == u'Success':
			message = item[0]['m:GetItemResponseMessage']['m:Items']['t:Message']
			
			if Message.objects.filter(message_id=message['t:ItemId']).count() > 0:
				return None
			# maybe use this for attachments? or pull them from exchange somehow?
			e_message = email.message_from_string(message['t:MimeContent']['#text'].decode('base64'))
			
			# this is currently saving everything in UTC (Z) time, not sure what I'm doing with Gmail
			m = Message(subject=message['t:Subject'],
						sent_date=datetime.strptime(message['t:DateTimeSent'], '%Y-%m-%dT%H:%M:%SZ'),
						message_id=message['t:ItemId'],
						thread_id=message['t:ConversationIndex']
						)
			m.sender = importing.get_or_create_person((
				message['t:From']['t:Mailbox']['t:Name'],
				message['t:From']['t:Mailbox']['t:EmailAddress']))
			m.save()
			m.members.add(m.sender.person)

			def parse_recipients(recipients, msg):
				def import_person(person):
					p = importing.get_or_create_person((
						person['t:Name'], person['t:EmailAddress']))
					msg.recipients.add(p)
					msg.members.add(p.person)

				if hasattr(recipients['t:Mailbox'], 'keys'):
					print "importing person {}".format(recipients['t:Mailbox'])
					import_person(recipients['t:Mailbox'])
				else:
					for person in recipients['t:Mailbox']:
						print "importing person {}".format(person)
						import_person(person)

			parse_recipients(message['t:ToRecipients'], m)

			if u't:CcRecipients' in message.keys():
				parse_recipients(message['t:CcRecipients'], m)

			# walk through the mime content to get the bodies and attachments
			self.walk_message(e_message, m)
			# walk through the internet headers to add them (from exchange or mime?)
			for header in message['t:InternetMessageHeaders']['t:InternetMessageHeader']:
				m.headers.add(Header(key=header['@HeaderName'], value=header['#text']))
			# add flags - read, inbox, etc

			if message['t:IsRead'] == u'true':
				m.flags.add(MessageFlag(flag=MessageFlag.UNREAD_FLAG))

			return m
		else:
			print "One message failed to load: {}".format(item[0])
			return None
