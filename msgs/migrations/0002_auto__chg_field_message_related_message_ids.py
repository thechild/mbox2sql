# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):

        # Changing field 'Message.related_message_ids'
        db.alter_column(u'msgs_message', 'related_message_ids', self.gf('django.db.models.fields.CharField')(max_length=1000, null=True))

    def backwards(self, orm):

        # Changing field 'Message.related_message_ids'
        db.alter_column(u'msgs_message', 'related_message_ids', self.gf('django.db.models.fields.CharField')(default=None, max_length=1000))

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
            'stored_location': ('django.db.models.fields.CharField', [], {'max_length': '200'})
        },
        u'msgs.message': {
            'Meta': {'object_name': 'Message'},
            'body_html': ('django.db.models.fields.TextField', [], {}),
            'body_text': ('django.db.models.fields.TextField', [], {}),
            'cc_recipients': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'cc_messages'", 'symmetrical': 'False', 'to': u"orm['msgs.Address']"}),
            'headers': ('django.db.models.fields.TextField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'message_id': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'recipients': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'received_messages'", 'symmetrical': 'False', 'to': u"orm['msgs.Address']"}),
            'related_message_ids': ('django.db.models.fields.CharField', [], {'max_length': '1000', 'null': 'True', 'blank': 'True'}),
            'related_messages': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'related_messages_rel_+'", 'to': u"orm['msgs.Message']"}),
            'sender': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'sent_messages'", 'to': u"orm['msgs.Address']"}),
            'sent_date': ('django.db.models.fields.DateTimeField', [], {}),
            'subject': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '200'})
        }
    }

    complete_apps = ['msgs']