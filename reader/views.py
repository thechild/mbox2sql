from django.shortcuts import render_to_response
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from msgs.models import Message, Address, Attachment

messages_per_page = 25

# Create your views here.

def message_list(request):
    message_list = Message.objects.all().order_by('-sent_date')
    paginator = Paginator(message_list, messages_per_page)

    page = request.GET.get('page')
    try:
        messages = paginator.page(page)
    except PageNotAnInteger:
        messages = paginator.page(1)
    except EmptyPage:
        messages = paginator.page(paginator.num_pages)

    return render_to_response('message_list.html', {"message_list": messages})

def view_message(request, message_id, text=False):
    message = Message.objects.get(id=message_id)
    return render_to_response('message.html', {'message': message, 'show_text': text})

def view_message_text(request, message_id):
    return view_message(request, message_id, text=True)

def view_person(request, person_id):
    person = Address.objects.get(id=person_id)
    return render_to_response('person.html', {'person': person})

def view_group(request, group_hash):
    pass