from django.shortcuts import render
from msgs.models import Message, Address, Attachment

# Create your views here.

def message_list(request):
    message_list = Message.objects.all().order_by('-sent_date')
    print message_list.count()
    context = {'message_list': message_list}
    return render(request, 'message_list.html', context)

def view_message(request, message_id, text=False):
    message = Message.objects.get(id=message_id)
    context = {'message': message, 'show_text': text}
    return render(request, 'message.html', context)

def view_message_text(request, message_id):
    return view_message(request, message_id, text=True)

def view_person(request, person_id):
    person = Address.objects.get(id=person_id)
    context = {'person': person}
    return render(request, 'person.html', context)

def view_group(request, group_hash):
    pass