# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Deleting field 'Message.uid'
        db.delete_column(u'msgs2_message', 'uid')


    def backwards(self, orm):
        # Adding field 'Message.uid'
        db.add_column(u'msgs2_message', 'uid',
                      self.gf('django.db.models.fields.CharField')(default=0, max_length=200),
                      keep_default=False)


    models = {
        u'msgs2.address': {
            'Meta': {'object_name': 'Address'},
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'label': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'person': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'addresses'", 'to': u"orm['msgs2.Person']"})
        },
        u'msgs2.attachment': {
            'Meta': {'object_name': 'Attachment'},
            'content_type': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'file_md5': ('django.db.models.fields.CharField', [], {'max_length': '40'}),
            'filename': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'message': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'attachments'", 'to': u"orm['msgs2.Message']"}),
            'mime_related': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'stored_location': ('django.db.models.fields.CharField', [], {'max_length': '200'})
        },
        u'msgs2.header': {
            'Meta': {'object_name': 'Header'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'key': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'message': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'headers'", 'to': u"orm['msgs2.Message']"}),
            'value': ('django.db.models.fields.TextField', [], {})
        },
        u'msgs2.message': {
            'Meta': {'object_name': 'Message'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'members': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'messages'", 'symmetrical': 'False', 'to': u"orm['msgs2.Person']"}),
            'message_id': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'recipients': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'received_messages'", 'symmetrical': 'False', 'to': u"orm['msgs2.Address']"}),
            'sender': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'sent_messages'", 'to': u"orm['msgs2.Address']"}),
            'sent_date': ('django.db.models.fields.DateTimeField', [], {}),
            'subject': ('django.db.models.fields.TextField', [], {}),
            'thread_id': ('django.db.models.fields.CharField', [], {'max_length': '200'})
        },
        u'msgs2.messagebody': {
            'Meta': {'object_name': 'MessageBody'},
            'content': ('django.db.models.fields.TextField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'message': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'body'", 'to': u"orm['msgs2.Message']"}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '10'})
        },
        u'msgs2.messageflag': {
            'Meta': {'object_name': 'MessageFlag'},
            'flag': ('django.db.models.fields.CharField', [], {'max_length': '1'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'message': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'flags'", 'to': u"orm['msgs2.Message']"})
        },
        u'msgs2.person': {
            'Meta': {'object_name': 'Person'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'})
        },
        u'msgs2.todo': {
            'Meta': {'object_name': 'ToDo'},
            'date_created': ('django.db.models.fields.DateField', [], {'default': 'datetime.datetime(2014, 10, 22, 0, 0)'}),
            'date_due': ('django.db.models.fields.DateField', [], {'default': 'datetime.datetime(2014, 10, 23, 0, 0)'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'message': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'todos'", 'null': 'True', 'to': u"orm['msgs2.Message']"}),
            'note_text': ('django.db.models.fields.TextField', [], {'default': "''"}),
            'subject': ('django.db.models.fields.CharField', [], {'max_length': '200'})
        }
    }

    complete_apps = ['msgs2']