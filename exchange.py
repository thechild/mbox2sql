from lxml import etree
from pyexchange import Exchange2010Service, ExchangeNTLMAuthConnection
from pyexchange.exchange2010.soap_request import M, T, NAMESPACES
import xmltodict

def pxml(xml):
	print(etree.tostring(xml, pretty_print=True))

class ExchangeMail():
	def __init__(self, url, username, password):
		self.url = url
		self.username = username
		self._get_service(url, username, password)


	def _get_service(self, url, username, password):
		connection = ExchangeNTLMAuthConnection(url=url, username=username, password=password)
		service = Exchange2010Service(connection)
		self.service = service


	# should be in soap_request
	def get_inbox_items(self, format=u"Default"):
	  root = M.FindItem(
	    {u'Traversal': u'Shallow'},
	    M.ItemShape(T.BaseShape(format)),
	    M.ParentFolderIds(T.DistinguishedFolderId(Id=u"inbox")),
	    )
	  return root


	# should be in soap_request
	# I might be able to do this with multiple itemids, which would speed things up
	def get_item(self, id, change_key, format=u"Default"):
		root = M.GetItem(
			M.ItemShape(T.BaseShape(format),
						T.IncludeMimeContent("true")),
			M.ItemIds(
	            T.ItemId({'Id': id, 'ChangeKey': change_key})))
		return root


	def process_items(self, msgxml):
		msgs = msgxml.xpath(u'//m:ResponseMessages/m:GetItemResponseMessage', namespaces=NAMESPACES)
		out_messages = []
		for msg in msgs:
			if msg.get('ResponseClass') == 'Success':
				out_messages.append(xmltodict.parse(etree.tostring(msg)))
		return out_messages


	def get_inbox(self):
		body = self.get_inbox_items()
		raw_messages = self.service.send(body)
		items = raw_messages.xpath(u'//m:FindItemResponseMessage/m:RootFolder/t:Items/t:Message', namespaces=NAMESPACES)
		ids = items[0].xpath('//t:ItemId', namespaces=NAMESPACES)
		msgs = []
		for id in ids:
			tid = id.get('Id')
			tidck = id.get('ChangeKey')
			root = self.get_item(tid, tidck, format=u"AllProperties")
			msgxml = self.service.send(root)
			msgs.append(msgxml)
		return msgs