from pyexchange.exchange2010.soap_request import M, T

def get_folder_items(format=u"Default", d_folder_id=u"inbox", folder_id=None):
      if folder_id:
        root =    root = M.FindItem(
                    {u'Traversal': u'Shallow'},
                    M.ItemShape(T.BaseShape(format)),
                    M.IndexedPageItemView({u'MaxEntriesReturned': u'10', u'BasePoint': u'Beginning', u'Offset': u'0'}),
                    M.ParentFolderIds(T.FolderId(Id=folder_id)),
                    )
      else:
        root = M.FindItem(
            {u'Traversal': u'Shallow'},
            M.ItemShape(T.BaseShape(format)),
            M.ParentFolderIds(T.DistinguishedFolderId(Id=d_folder_id)),
            )
      return root

def get_folder_items_range(format=u"Default", d_folder_id=u"inbox", folder_id=None, max_entries=None, offset=None):
    if folder_id:
        folder = T.FolderId(Id=folder_id)
    else:
        folder = T.DistinguishedFolderId(Id=d_folder_id)

    root = M.FindItem(
        {u'Traversal': u'Shallow'},
        M.ItemShape(T.BaseShape(format)),
        M.IndexedPageItemView({u'MaxEntriesReturned': unicode(max_entries), u'BasePoint': u'Beginning', u'Offset': unicode(offset)}),
        M.ParentFolderIds(folder),
        )
    return root

def get_child_folders(folder_id, format=u"Default"):
    root = M.FindFolder(
        {u'Traversal': u'Shallow'},
        M.FolderShape(
            T.BaseShape(format)),
        M.ParentFolderIds(
            T.FolderId(Id=folder_id)))
    return root

def get_folder_xml(folder, format=u"Default"):
    root = M.GetFolder(
        M.FolderShape(T.BaseShape(format)),
        M.FolderIds(T.DistinguishedFolderId(Id=folder))
        )
    return root

def get_item_nck(id, format=u"Default"):
    root = M.GetItem(
        M.ItemShape(T.BaseShape(format),
                    T.IncludeMimeContent("true")),
        M.ItemIds(
            T.ItemId({'Id': id})))
    return root

def get_item(id, change_key, format=u"Default"):
    root = M.GetItem(
        M.ItemShape(T.BaseShape(format),
                    T.IncludeMimeContent("true")),
        M.ItemIds(
            T.ItemId({'Id': id, 'ChangeKey': change_key})))
    return root


def get_items(ids, format=u"Default"):
    itemids = [T.ItemId({'Id': id, 'ChangeKey': change_key}) for id, change_key in ids]
    root = M.GetItem(
        M.ItemShape(T.BaseShape(format),
                    T.IncludeMimeContent("true")),
        *itemids)
    return root

