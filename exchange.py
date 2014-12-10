from lxml import etree
from pyexchange import Exchange2010Service, ExchangeNTLMAuthConnection
from pyexchange.exchange2010.soap_request import M, T, NAMESPACES
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
        return self._item_id

    def message(self):
        if not self._message:
            root = self._mail.get_item_nck(self._item_id)
            self._message = self._mail.service.send(root)
        return self._message

class ExchangeMail():
    def __init__(self, url, username, password):
        self.url = url
        self.username = username
        self._get_service(url, username, password)


    def _get_service(self, url, username, password):
        connection = ExchangeNTLMAuthConnection(url=url, username=username, password=password)
        service = Exchange2010Service(connection)
        self.service = service


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
            child_folders = self.service.send(exml.get_child_folders(folder_id))
            #ipdb.set_trace()
            for folder in child_folders.xpath('//t:Folder', namespaces=NAMESPACES):
                if ptree:
                    print "-" * depth + "{}".format(folder.xpath('t:DisplayName', namespaces=NAMESPACES)[0].text)
                # is it our folder?
                if folder.xpath('t:DisplayName', namespaces=NAMESPACES)[0].text == folder_name:
                    print "Found Folder: {} ({})".format(folder_name, folder.xpath('t:FolderId', namespaces=NAMESPACES)[0].get('Id'))
                    ipdb.set_trace()
                    pxml(folder.xpath('t:TotalCount', namespaces=NAMESPACES)[0])
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

    # should be in soap_request
    # I might be able to do this with multiple itemids, which would speed things up

    def process_items(self, msgxml):
        msgs = msgxml.xpath(u'//m:ResponseMessages/m:GetItemResponseMessage', namespaces=NAMESPACES)
        out_messages = []
        for msg in msgs:
            if msg.get('ResponseClass') == 'Success':
                out_messages.append(xmltodict.parse(etree.tostring(msg)))
        return out_messages

        
    def get_folder_generator(self, folder_name, distinguished_folder=True, step=10):
        if distinguished_folder:
            pass
        else:
            folder = self.find_folder_named(folder_name)
            if not folder:
                raise Exception("Couldn't find folder named %s" % folder_name)
            folder_id, item_count = folder

        for i in xrange(int(item_count) / step):
            # get the list of step items
            body = exml.get_folder_items_range(folder_id=folder_id, format=u"IdOnly",
                max_entries=step, offset=i * step)
            raw_messages = self.service.send(body)
            items = raw_messages.xpath(u'//m:FindItemResponseMessage/m:RootFolder/t:Items/t:Message', namespaces=NAMESPACES)
            ids = items[0].xpath('//t:ItemId', namespaces=NAMESPACES)
            for id in ids:
                yield MessageItem(folder_id or folder_name, id.get('Id'), self)


    def get_folder(self, folder_name, distinguished_folder=True):
        if distinguished_folder:
            body = exml.get_folder_items(d_folder_id=folder_name, format=u"IdOnly")
        else:
            folder_id, item_count = self.find_folder_named(folder_name)
            body = exml.get_folder_items(folder_id=folder_id, format=u"IdOnly")
        pxml(body)
        # print "Sending request for folder..."
        raw_messages = self.service.send(body)
        items = raw_messages.xpath(u'//m:FindItemResponseMessage/m:RootFolder/t:Items/t:Message', namespaces=NAMESPACES)
        ids = items[0].xpath('//t:ItemId', namespaces=NAMESPACES)
        msgs = []
        for id in ids:
            tid = id.get('Id')
            tidck = id.get('ChangeKey')
            root = exml.get_item(tid, tidck, format=u"AllProperties")
            # print "Sending request for message {}".format(tid)
            msgxml = self.service.send(root)
            msgs.append(msgxml)
        return msgs

    def get_archive(self):
        return self.get_folder(u"Archive", distinguished_folder=False)

    def get_inbox(self):
        return self.get_folder(u"inbox")
