from django.contrib import admin
from msgs.models import Message, Address, Attachment

# Register your models here.

def location_link(obj):
    return '<a href="/%s">%s</a>' % (obj.stored_location, obj.filename)

class AttachmentsInline(admin.TabularInline):
    model = Attachment
    fk_name = 'message'
    readonly_fields = ('filename', 'content_type', location_link, 'file_md5',)
    extra = 0
    fields = [location_link, 'content_type', 'file_md5']

class MessageAdmin(admin.ModelAdmin):
    readonly_fields = ('message_id', 'recipients', 'sender',)
    fields = ['message_id', 'subject', 'sender', 'recipients', 'sent_date', 'body_text']
    list_display = ['subject', 'sender', 'sent_date']
    inlines = [ AttachmentsInline, ]

class AttachmentAdmin(admin.ModelAdmin):
    location_link.allow_tags = True
    list_display = ('filename', 'content_type', location_link, )
    readonly_fields = ('filename', 'content_type', location_link, 'file_md5', )
    fields = (location_link, 'content_type', 'file_md5', )

admin.site.register(Address)
admin.site.register(Message, MessageAdmin)
admin.site.register(Attachment, AttachmentAdmin)