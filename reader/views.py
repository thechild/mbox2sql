from django.shortcuts import render_to_response
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from msgs.models import Message, Address, Attachment, Conversation, get_all_message_threads, get_sorted_conversations, get_current_user
from msgs.groups import Group, group_from_url_representation, groups_including_person, group_from_conversation

messages_per_page = 25

########################
### HELPER FUNCTIONS ###
########################

# helper function to get information needed by the base.html template
def get_default_context(request):
    unread_message_count = len(get_all_message_threads()) ## clearly need to fix this
    unread_conversation_count = Conversation.objects.count() ## and this
    context = {'unread_message_count': unread_message_count,
               'unread_conversation_count': unread_conversation_count }
    return context

def get_context_with(request, dict):
    context = get_default_context(request)
    context.update(dict)
    return context

###########################
### RAW MESSAGE THREADS ###
###########################

# returns a raw message (used for iframes) in either html or text
def raw_message(request, message_id, text=False):
    message = Message.objects.get(id=message_id)
    context = get_default_context(request)
    raw_text = message.body_html
    if text or not message.body_html:
        raw_text = message.body_text
        text = True
    context.update({ 'raw_text': raw_text, 'pre': text })
    return render_to_response('raw_message.html', context)

def raw_message_text(request, message_id):
    return raw_message(request, message_id, text=True)

##################
### LIST VIEWS ###
##################

def conversation_list(request): #/mail/c
    message_list = get_sorted_conversations()
    paginator = Paginator(message_list, messages_per_page)

    page = request.GET.get('page')
    try:
        messages = paginator.page(page)
    except PageNotAnInteger:
        messages = paginator.page(1)
    except EmptyPage:
        messages = paginator.page(paginator.num_pages)

    context = get_default_context(request)
    context.update({'message_list': messages})

    return render_to_response('conversation_list.html', context)

def message_list(request): #/mail/
    message_list = get_all_message_threads()
    paginator = Paginator(message_list, messages_per_page)

    page = request.GET.get('page')
    try:
        messages = paginator.page(page)
    except PageNotAnInteger:
        messages = paginator.page(1)
    except EmptyPage:
        messages = paginator.page(paginator.num_pages)

    context = get_context_with(request, {'message_list': messages })
    return render_to_response('message_list.html', context)

def people_list(request): #/mail/people
    p_list = Address.objects.exclude(id=get_current_user().id) # this feels like it should be simpler

    def latest_convo_date(address):
        d = address.newest_conversation()
        if d:
            return d.latest_message_date
        else:
            return 0

    sp_list = sorted(p_list, key=latest_convo_date, reverse=True) # should do this in db

    context = get_context_with(request, {'people_list': sp_list })
    return render_to_response('people_list.html', context)

def group_list(request):
    person = get_current_user()
    groups = groups_including_person(person)
    context = get_context_with(request, {'groups': groups })
    return render_to_response('group_list.html', context)

###############################
### INDIVIDUAL OBJECT VIEWS ###
###############################

def view_conversation(request, conversation_id, text=False):
    conversation = Conversation.objects.get(id=conversation_id)

    context = get_context_with(request, {'conversation': conversation, 'show_text': text })
    return render_to_response('conversation.html', context)

def view_conversation_text(request, conversation_id):
    return view_conversation(request, conversation_id, text=True)

def view_message(request, message_id, text=False):
    message = Message.objects.get(id=message_id)
    context = get_context_with(request, {'message': message, 'show_text': text })
    return render_to_response('message.html', context)

def view_message_text(request, message_id):
    return view_message(request, message_id, text=True)

def view_person(request, person_id):
    person = Address.objects.get(id=person_id)
    context = get_context_with(request, {'person': person})
    return render_to_response('person.html', context)

def view_group(request, group_id):
    group = group_from_conversation(Conversation.objects.get(id=group_id))
    context = get_context_with(request, {'group': group})
    return render_to_response('view_group.html', context)
