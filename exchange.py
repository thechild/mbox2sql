from lxml import etree
from pyexchange import Exchange2010Service, ExchangeNTLMAuthConnection
from pyexchange.exchange2010.soap_request import M, T, NAMESPACES
import pyexchange
import xmltodict
import ipdb

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
	def get_folder_items(self, format=u"Default", d_folder_id=u"inbox", folder_id=None):
	  if folder_id:
	  	root = 	  root = M.FindItem(
				    {u'Traversal': u'Shallow'},
				    M.ItemShape(T.BaseShape(format)),
				    M.ParentFolderIds(T.FolderId(Id=folder_id)),
				    )
	  else:
		root = M.FindItem(
		    {u'Traversal': u'Shallow'},
		    M.ItemShape(T.BaseShape(format)),
		    M.ParentFolderIds(T.DistinguishedFolderId(Id=d_folder_id)),
		    )
	  return root


	def get_child_folders(self, folder_id, format=u"Default"):
		root = M.FindFolder(
			{u'Traversal': u'Shallow'},
			M.FolderShape(
				T.BaseShape(format)),
			M.ParentFolderIds(
				T.FolderId(Id=folder_id)))
		return root


	def get_distinguished_folder_id(self, d_folder_id, format=u"Default"):
		root = M.GetFolder(
			M.FolderShape(T.BaseShape(format)),
			M.FolderIds(T.DistinguishedFolderId(Id=d_folder_id)))
		try:
			resp = self.service.send(root)
		except pyexchange.FailedExchangeException:
			print "Error with Exchange, perhaps there is no such folder as {}.".format(d_folder_id)
			return None
		return resp.xpath('//t:FolderId', namespaces=NAMESPACES)[0].get('Id')

	def find_folder_named(self, folder_name, ptree=False):
		# first find the root folder
		rootfolder_id = self.get_distinguished_folder_id('root')
		print "Root folder: {}".format(rootfolder_id)


		def search_children(folder_id, depth=0, ptree=False):
			child_folders = self.service.send(self.get_child_folders(folder_id))
			#ipdb.set_trace()
			for folder in child_folders.xpath('//t:Folder', namespaces=NAMESPACES):
				if ptree:
					print "-" * depth + "{}".format(folder.xpath('t:DisplayName', namespaces=NAMESPACES)[0].text)
				# is it our folder?
				if folder.xpath('t:DisplayName', namespaces=NAMESPACES)[0].text == folder_name:
					print "Found Folder: {} ({})".format(folder_name, folder.xpath('t:FolderId', namespaces=NAMESPACES)[0].get('Id'))
					return folder.xpath('t:FolderId', namespaces=NAMESPACES)[0].get('Id')
				# does it have child folders?
				elif int(folder.xpath('t:ChildFolderCount', namespaces=NAMESPACES)[0].text) > 0:
					chain_id = search_children(folder.xpath('t:FolderId', namespaces=NAMESPACES)[0].get('Id'), depth+1, ptree)
					if chain_id:
						return chain_id
			return None
		
		# then iterate through each folder recursively until you find the right name
		return search_children(rootfolder_id, ptree=ptree)

	def get_folder_xml(self, folder, format=u"Default"):
		root = M.GetFolder(
			M.FolderShape(T.BaseShape(format)),
			M.FolderIds(T.DistinguishedFolderId(Id=folder))
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


	def get_folder(self, folder_name, distinguished_folder=True):
		if distinguished_folder:
			body = self.get_folder_items(d_folder_id=folder_name)
		else:
			folder_id = self.find_folder_named(folder_name)
			body = self.get_folder_items(folder_id=folder_id)
		print "Sending request for folder..."
		raw_messages = self.service.send(body)
		items = raw_messages.xpath(u'//m:FindItemResponseMessage/m:RootFolder/t:Items/t:Message', namespaces=NAMESPACES)
		ids = items[0].xpath('//t:ItemId', namespaces=NAMESPACES)
		msgs = []
		for id in ids:
			tid = id.get('Id')
			tidck = id.get('ChangeKey')
			root = self.get_item(tid, tidck, format=u"AllProperties")
			print "Sending request for message {}".format(tid)
			msgxml = self.service.send(root)
			msgs.append(msgxml)
		return msgs

	def get_archive(self):
		return self.get_folder(u"Archive", distinguished_folder=False)

	def get_inbox(self):
		return self.get_folder(u"inbox")
