from django.shortcuts import render_to_response
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from msgs.models import Message, Address, Attachment, get_all_message_threads

messages_per_page = 25

# Create your views here.

def get_default_context(request):
    unread_message_count = len(get_all_message_threads()) ## clearly need to fix this
    context = {'unread_message_count': unread_message_count }
    return context

def message_list(request):
    message_list = get_all_message_threads()
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

    return render_to_response('message_list.html', context)

def view_message(request, message_id, text=False):
    message = Message.objects.get(id=message_id)
    context = get_default_context(request)
    context.update({ 'message': message, 'show_text': text })

    return render_to_response('message.html', context)

def view_message_text(request, message_id):
    return view_message(request, message_id, text=True)

def view_person(request, person_id):
    person = Address.objects.get(id=person_id)
    context = get_default_context(request)
    context.update({ 'person': person })
    return render_to_response('person.html', context)

def view_group(request, group_hash):
    pass