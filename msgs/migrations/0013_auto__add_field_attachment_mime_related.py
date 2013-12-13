# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding field 'Attachment.mime_related'
        db.add_column(u'msgs_attachment', 'mime_related',
                      self.gf('django.db.models.fields.BooleanField')(default=False),
                      keep_default=False)


    def backwards(self, orm):
        # Deleting field 'Attachment.mime_related'
        db.delete_column(u'msgs_attachment', 'mime_related')


    models = {
        u'msgs.address': {
            'Meta': {'object_name': 'Address'},
            'address': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '200'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'})
        },
        u'msgs.attachment': {
            'Meta': {'object_name': 'Attachment'},
            'content_type': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'file_md5': ('django.db.models.fields.CharField', [], {'max_length': '40'}),
            'filename': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'message': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'attachments'", 'to': u"orm['msgs.Message']"}),
            'mime_related': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'stored_location': ('django.db.models.fields.CharField', [], {'max_length': '200'})
        },
        u'msgs.conversation': {
            'Meta': {'object_name': 'Conversation'},
            'creator': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'started_conversations'", 'null': 'True', 'to': u"orm['msgs.Address']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'latest_message_date': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(1980, 1, 1, 0, 0)'}),
            'members': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'conversations'", 'symmetrical': 'False', 'to': u"orm['msgs.Address']"}),
            'message_id': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'subject': ('django.db.models.fields.TextField', [], {})
        },
        u'msgs.header': {
            'Meta': {'object_name': 'Header'},
            'field': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'message': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'headers'", 'to': u"orm['msgs.Message']"}),
            'text': ('django.db.models.fields.TextField', [], {})
        },
        u'msgs.message': {
            'Meta': {'object_name': 'Message'},
            'body_html': ('django.db.models.fields.TextField', [], {}),
            'body_text': ('django.db.models.fields.TextField', [], {}),
            'cc_recipients': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'cc_messages'", 'symmetrical': 'False', 'to': u"orm['msgs.Address']"}),
            'conversation': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'related_name': "'messages'", 'null': 'True', 'blank': 'True', 'to': u"orm['msgs.Conversation']"}),
            'group_hash': ('django.db.models.fields.CharField', [], {'max_length': '40', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'message_id': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'related_name': "'children'", 'null': 'True', 'blank': 'True', 'to': u"orm['msgs.Message']"}),
            'recipients': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'received_messages'", 'symmetrical': 'False', 'to': u"orm['msgs.Address']"}),
            'related_messages': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'related_messages_rel_+'", 'to': u"orm['msgs.Message']"}),
            'sender': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'sent_messages'", 'to': u"orm['msgs.Address']"}),
            'sent_date': ('django.db.models.fields.DateTimeField', [], {}),
            'subject': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '200'}),
            'thread_index': ('django.db.models.fields.CharField', [], {'default': 'None', 'max_length': '200', 'null': 'True', 'blank': 'True'})
        }
    }

    complete_apps = ['msgs']