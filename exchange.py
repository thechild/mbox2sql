from lxml import etree
from pyexchange import Exchange2010Service, ExchangeNTLMAuthConnection
from pyexchange.exchange2010.soap_request import NAMESPACES
import pyexchange
import xmltodict
import ipdb
import exchange_soap as exml

def pxml(xml):
    print(etree.tostring(xml, pretty_print=True))

# lazy pulling of message bodies
class MessageItem():
    def __init__(self, folder_id, item_id, mail):
        self._folder_id = folder_id
        self._item_id = item_id
        self._mail = mail
        self._message = None

    @property
    def folder_id(self):
        return self._folder_id

    @property
    def item_id(self):
        return unicode(self._item_id)

    def message(self):
        if not self._message:
            root = exml.get_item_nck(self._item_id, format=u"AllProperties")
            print "Fetching message for message {}.".format(self.item_id)
            self._message = self._mail.service.send(root)
        return self._message

    def processed_message(self):
        msg = self.message().xpath(u'//m:ResponseMessages/m:GetItemResponseMessage', namespaces=NAMESPACES)[0]
        if msg.get('ResponseClass') == 'Success':
            return xmltodict.parse(etree.tostring(msg))


class ExchangeMail():
    def __init__(self, url, username, password):
        self.url = url
        self.username = username
        self._get_service(url, username, password)


    def _get_service(self, url, username, password):
        connection = ExchangeNTLMAuthConnection(url=url, username=username, password=password)
        service = Exchange2010Service(connection)
        self.service = service


    def get_distinguished_folder(self, d_folder_id, format=u"Default"):
        root = exml.get_folder_xml(d_folder_id)
        try:
            resp = self.service.send(root)
        except pyexchange.FailedExchangeException:
            print "Error with Exchange, perhaps there is no such folder as {}.".format(d_folder_id)
            return None
        return resp


    def get_distinguished_folder_id(self, d_folder_id, format=u"Default"):
        folder = self.get_distinguished_folder(d_folder_id, format)
        return folder.xpath('//t:FolderId', namespaces=NAMESPACES)[0].get('Id')


    def find_folder_named(self, folder_name, ptree=False):
        # first find the root folder
        rootfolder_id = self.get_distinguished_folder_id('root')
        print "Root folder: {}".format(rootfolder_id)

        def search_children(folder_id, depth=0, ptree=False):
            child_folders = self.service.send(exml.get_child_folders(folder_id))
            #ipdb.set_trace()
            for folder in child_folders.xpath('//t:Folder', namespaces=NAMESPACES):
                if ptree:
                    print "-" * depth + "{}".format(folder.xpath('t:DisplayName', namespaces=NAMESPACES)[0].text)
                # is it our folder?
                if folder.xpath('t:DisplayName', namespaces=NAMESPACES)[0].text == folder_name:
                    print "Found Folder: {} ({})".format(folder_name, folder.xpath('t:FolderId', namespaces=NAMESPACES)[0].get('Id'))
                    #ipdb.set_trace()
                    #pxml(folder.xpath('t:TotalCount', namespaces=NAMESPACES)[0])
                    return (folder.xpath('t:FolderId', namespaces=NAMESPACES)[0].get('Id'),
                            folder.xpath('t:TotalCount', namespaces=NAMESPACES)[0].text)
                # does it have child folders?
                elif int(folder.xpath('t:ChildFolderCount', namespaces=NAMESPACES)[0].text) > 0:
                    chain_id = search_children(folder.xpath('t:FolderId', namespaces=NAMESPACES)[0].get('Id'), depth+1, ptree)
                    if chain_id:
                        return chain_id
            return None
        
        # then iterate through each folder recursively until you find the right name
        return search_children(rootfolder_id, ptree=ptree) 
        
    def get_folder_generator(self, folder_name, distinguished_folder=True, step=10):
        if distinguished_folder:
            folder = self.get_distinguished_folder(folder_name)
            folder_id = folder.xpath('//t:FolderId', namespaces=NAMESPACES)[0].get('Id')
            item_count = folder.xpath('//t:TotalCount', namespaces=NAMESPACES)[0].text
            print "There should be {} items in the {} folder.".format(item_count, folder_name)
        else:
            folder = self.find_folder_named(folder_name)
            if not folder:
                raise Exception("Couldn't find folder named %s" % folder_name)
            folder_id, item_count = folder

        # not deterministic time, as it sometimes (once every step calls) hits the server...
        for i in xrange(int(item_count) / step + 1):
            # get the list of step items
            body = exml.get_folder_items_range(folder_id=folder_id, format=u"IdOnly",
                max_entries=step, offset=i * step)
            raw_messages = self.service.send(body)
            items = raw_messages.xpath(u'//m:FindItemResponseMessage/m:RootFolder/t:Items/t:Message', namespaces=NAMESPACES)
            ids = items[0].xpath('//t:ItemId', namespaces=NAMESPACES)
            for id in ids:
                yield MessageItem(folder_id or folder_name, id.get('Id'), self)

    def get_archive(self):
        return self.get_folder_generator(u"Archive", distinguished_folder=False)

    def get_inbox(self):
        return self.get_folder_generator(u"inbox")
