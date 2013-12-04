from models import Message, Conversation
from threadMessages import threadMessages, ccThreadMessages
from helpers import clean_subject

#################
### THREADING ###
#################

def setup_threads(message_list=None):
    ccThreadMessages.kModuleDebug = 1
    ccThreadMessages.kModuleVerbose = 1

    if not message_list:
        message_list = Message.objects.all() #default to running it on the whole set

    #t = threadMessages.jwzThread(mbox) #old version
    t = ccThreadMessages.ccThread(message_list)

    for tree in t:
        # see if a conversation already exists with the given message_id
        if tree.messageID:
            convo = get_conversation_from_messageid(tree.messageID)
            if not convo.subject:
                convo.subject = clean_subject(tree.subject)
                convo.save()
            # should deal with conversations in here, but not sure how yet
        else:
            print "no messageID: %s" % tree
        recurse_and_update(tree, convo)

def get_conversation_from_messageid(message_id):
    convo = []
    convos = Conversation.objects.filter(message_id = message_id)
    if convos.count() == 0:
        convo = Conversation()
        convo.message_id = message_id
        convo.save()
    else:
        convo = convos[0]
        if convos.count() > 1:
            print "found multiple conversations with message id: %s" % tree.messageID
    return convo

def recurse_and_update(node, conversation, depth=0, default_parent=None):
    for message in node.messages:
        print "  "*depth + "%s [%s]" % (message.subject, message.id)
        set_parent(message, node, depth, default_parent)
        message.save()
        conversation.add_message(message)

    if node.messages:
        default_parent = node.messages[0]
    elif not default_parent:
        print "  "*depth + "%s" % node.subject
        print "node has no messages, so setting to first child..."
        for child in node.children:
            if child.messages:
                default_parent = child.messages[0]
                break

    for child in node.children:
        recurse_and_update(child, conversation, depth+1, default_parent)
    return None

def set_parent(message, node, depth=0, default_parent=None):
    if node.parent:
        if node.parent.messages:
            message.parent = node.parent.messages[0]
            print "  "*depth + "set %s parent to be parent %s" % (message.id, message.parent.id)
        elif node.parent.parent:
            set_parent(message, node.parent, depth, default_parent)
        else:
            if default_parent and not default_parent.id == message.id:
                message.parent = default_parent
                print "  "*depth + "couldn't find parent message for message id %s, using default_parent %s" % (message.id, default_parent.id)
            else:
                print "  "*depth + "well, couldn't find a default_parent either! %s" % message.id
    else:
        if default_parent:
            message.parent = default_parent
            print "  "*depth + "set %s parent to be default parent %s" % (message.id, message.parent.id)
        else:
            #print "  "*depth + "message has no parent, and no default_parent"
            pass

def set_parent_old(message, node):
    if node.parent:
        messages_db = Message.objects.filter(message_id = node.messageID)
        if messages_db.count() > 0:
            message_db = messages_db[0]
            # found the message, now let's see if the parent exists
            parents_db = Message.objects.filter(message_id = node.parent.messageID)
            if parents_db.count() > 0:
                parent_db = parents_db[0]
                #found the parent, let's link them
                message_db.parent = parent_db
                message_db.save()
                print "set %s parent to be %s" % (message_db.message_id, parent_db.message_id)
            else:
                print node
                print "couldn't find parent of %s in db, setting to node parent [%s]" % (message_db.message_id, node.parent.messageID)
        else:
            print "*** couldn't find message in db [%s]" % node.messageID
    return None

#####################
### CONVERSATIONS ###
#####################

### this is old - use the setup_threads way instead

# run this after setting up threads
def setup_conversations(message_list=None):
    if not message_list:
        message_list = Message.objects.all() # default to all messages if no list is provided

    convo_list = []
    for message in message_list:
        convo = get_or_create_conversation_from_message(message)
        convo_list.append(convo)

    print "Added %d messages to %d conversations" % (len(message_list), len(convo_list))

def get_or_create_conversation_from_message(message):
    top_message = get_ultimate_parent(message)
    convo = Conversation.objects.filter(initial_message__id = top_message.id)
    if len(convo) == 0:
        convo = Conversation()
        convo.subject = top_message.cleaned_subject
        convo.creator = top_message.sender
        convo.save()
        convo.messages.add(top_message)
        for person in top_message.all_related_people():
            convo.members.add(person)
    else:
        convo = convo[0]

    for person in message.all_related_people():
        convo.members.add(person)
    convo.messages.add(message)
    convo.save()
    return convo

def get_ultimate_parent(message):
    if not message.parent:
        return message
    else:
        return get_ultimate_parent(message.parent)
