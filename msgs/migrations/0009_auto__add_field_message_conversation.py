# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding field 'Message.conversation'
        db.add_column(u'msgs_message', 'conversation',
                      self.gf('django.db.models.fields.related.ForeignKey')(default=None, related_name='messages', null=True, blank=True, to=orm['msgs.Conversation']),
                      keep_default=False)

        # Removing M2M table for field conversations on 'Message'
        db.delete_table(db.shorten_name(u'msgs_message_conversations'))


    def backwards(self, orm):
        # Deleting field 'Message.conversation'
        db.delete_column(u'msgs_message', 'conversation_id')

        # Adding M2M table for field conversations on 'Message'
        m2m_table_name = db.shorten_name(u'msgs_message_conversations')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('message', models.ForeignKey(orm[u'msgs.message'], null=False)),
            ('conversation', models.ForeignKey(orm[u'msgs.conversation'], null=False))
        ))
        db.create_unique(m2m_table_name, ['message_id', 'conversation_id'])


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
        u'msgs.conversation': {
            'Meta': {'object_name': 'Conversation'},
            'creator': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'started_conversations'", 'to': u"orm['msgs.Address']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'members': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'conversations'", 'symmetrical': 'False', 'to': u"orm['msgs.Address']"}),
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