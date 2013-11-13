# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Address'
        db.create_table(u'msgs_address', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('address', self.gf('django.db.models.fields.CharField')(unique=True, max_length=200)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=200)),
        ))
        db.send_create_signal(u'msgs', ['Address'])

        # Adding model 'Message'
        db.create_table(u'msgs_message', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('sender', self.gf('django.db.models.fields.related.ForeignKey')(related_name='sent_messages', to=orm['msgs.Address'])),
            ('subject', self.gf('django.db.models.fields.CharField')(default='', max_length=200)),
            ('sent_date', self.gf('django.db.models.fields.DateTimeField')()),
            ('headers', self.gf('django.db.models.fields.TextField')()),
            ('body_text', self.gf('django.db.models.fields.TextField')()),
            ('body_html', self.gf('django.db.models.fields.TextField')()),
            ('message_id', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('related_message_ids', self.gf('django.db.models.fields.CharField')(max_length=1000)),
        ))
        db.send_create_signal(u'msgs', ['Message'])

        # Adding M2M table for field recipients on 'Message'
        m2m_table_name = db.shorten_name(u'msgs_message_recipients')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('message', models.ForeignKey(orm[u'msgs.message'], null=False)),
            ('address', models.ForeignKey(orm[u'msgs.address'], null=False))
        ))
        db.create_unique(m2m_table_name, ['message_id', 'address_id'])

        # Adding M2M table for field cc_recipients on 'Message'
        m2m_table_name = db.shorten_name(u'msgs_message_cc_recipients')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('message', models.ForeignKey(orm[u'msgs.message'], null=False)),
            ('address', models.ForeignKey(orm[u'msgs.address'], null=False))
        ))
        db.create_unique(m2m_table_name, ['message_id', 'address_id'])

        # Adding M2M table for field related_messages on 'Message'
        m2m_table_name = db.shorten_name(u'msgs_message_related_messages')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('from_message', models.ForeignKey(orm[u'msgs.message'], null=False)),
            ('to_message', models.ForeignKey(orm[u'msgs.message'], null=False))
        ))
        db.create_unique(m2m_table_name, ['from_message_id', 'to_message_id'])

        # Adding model 'Attachment'
        db.create_table(u'msgs_attachment', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('filename', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('content_type', self.gf('django.db.models.fields.CharField')(max_length=50)),
            ('stored_location', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('file_md5', self.gf('django.db.models.fields.CharField')(max_length=40)),
            ('message', self.gf('django.db.models.fields.related.ForeignKey')(related_name='attachments', to=orm['msgs.Message'])),
        ))
        db.send_create_signal(u'msgs', ['Attachment'])


    def backwards(self, orm):
        # Deleting model 'Address'
        db.delete_table(u'msgs_address')

        # Deleting model 'Message'
        db.delete_table(u'msgs_message')

        # Removing M2M table for field recipients on 'Message'
        db.delete_table(db.shorten_name(u'msgs_message_recipients'))

        # Removing M2M table for field cc_recipients on 'Message'
        db.delete_table(db.shorten_name(u'msgs_message_cc_recipients'))

        # Removing M2M table for field related_messages on 'Message'
        db.delete_table(db.shorten_name(u'msgs_message_related_messages'))

        # Deleting model 'Attachment'
        db.delete_table(u'msgs_attachment')


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
            'related_message_ids': ('django.db.models.fields.CharField', [], {'max_length': '1000'}),
            'related_messages': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'related_messages_rel_+'", 'to': u"orm['msgs.Message']"}),
            'sender': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'sent_messages'", 'to': u"orm['msgs.Address']"}),
            'sent_date': ('django.db.models.fields.DateTimeField', [], {}),
            'subject': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '200'})
        }
    }

    complete_apps = ['msgs']