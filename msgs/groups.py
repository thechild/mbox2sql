from models import Address, Conversation, Message, Attachment
import pickle


def attachments_in_conversations(conversations):
    return Attachment.objects.filter(message__conversation__in=conversations).filter(mime_related=False)

class Group():
    members = []
    core_member = None

    def other_members(self):
        return self.members.exclude(id = self.core_member.id)

    ### return all conversations involving all members of this group ###
    # could cache this I guess, not sure we need to
    def conversations(self):
        conversations = []
        if len(self.members) > 0:
            conversations = Conversation.objects
            for member in self.members:
                conversations = conversations.filter(members=member)
        return conversations

    ### return all conversations involving ONLY the members ###
    def solo_conversations(self):
        cs = self.conversations()
        if cs:
            return cs.filter(members__count=len(self.members))
        else:
            return cs

    def first_conversation(self):
        return self.conversations()[0]

    ### return all attachments in conversations the group members are involved in ###
    def attachments(self):
        return attachments_in_conversations(self.conversations())

    def attachments_count(self):
        return len(self.attachments())

    def solo_attachments(self):
        return attachments_in_conversation(self.solo_conversations())

    def url_representation(self):
    #    ids = map(lambda a: a.id, self.members)
    #    return pickle.dumps(ids)
        return self.first_conversation().id

    def __unicode__(self):
        return "<Group: %s>" % str(self.members)

    # members is a list of Address objects
    def __init__(self, members, core_member=None):
        self.members = members
        self.core_member = core_member

# this needs to be made much saner
def group_from_url_representation(text):
    try:
        ids = pickle.loads(text)
    except pickle.UnpicklingError:
        print "bad url"
        return None

    addresses = Address.objects.filter(id__in=ids)
    return Group(addresses)

def group_from_conversation(conversation):
    return Group(conversation.members.all())

def groups_including_group(group):
    groups = []
    # loop through all conversations in the group excluding ones that are solo conversations
    for conversation in group.conversations().filter(members__count_gt=len(group.members)):
        g = group_from_conversation(conversation)
        if g not in groups:
            groups.append(g)
    return groups

# conversations will get everything, but there might be messages with fewer people...
def groups_including_person(person):
    conversations = person.conversations.all()
    groups = []
    for convo in conversations:
        group = Group(convo.members.all(), person)
        if group not in groups:
            groups.append(group)
    return groups