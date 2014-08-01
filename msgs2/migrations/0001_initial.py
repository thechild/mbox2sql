# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Person'
        db.create_table(u'msgs2_person', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=200)),
        ))
        db.send_create_signal(u'msgs2', ['Person'])

        # Adding model 'Address'
        db.create_table(u'msgs2_address', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('email', self.gf('django.db.models.fields.EmailField')(max_length=75)),
            ('label', self.gf('django.db.models.fields.CharField')(max_length=50)),
            ('person', self.gf('django.db.models.fields.related.ForeignKey')(related_name='addresses', to=orm['msgs2.Person'])),
        ))
        db.send_create_signal(u'msgs2', ['Address'])

        # Adding model 'Message'
        db.create_table(u'msgs2_message', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('sender', self.gf('django.db.models.fields.related.ForeignKey')(related_name='sent_messages', to=orm['msgs2.Address'])),
            ('subject', self.gf('django.db.models.fields.TextField')()),
            ('sent_date', self.gf('django.db.models.fields.DateTimeField')()),
            ('message_id', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('thread_id', self.gf('django.db.models.fields.CharField')(max_length=200)),
        ))
        db.send_create_signal(u'msgs2', ['Message'])

        # Adding M2M table for field recipients on 'Message'
        m2m_table_name = db.shorten_name(u'msgs2_message_recipients')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('message', models.ForeignKey(orm[u'msgs2.message'], null=False)),
            ('address', models.ForeignKey(orm[u'msgs2.address'], null=False))
        ))
        db.create_unique(m2m_table_name, ['message_id', 'address_id'])

        # Adding M2M table for field members on 'Message'
        m2m_table_name = db.shorten_name(u'msgs2_message_members')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('message', models.ForeignKey(orm[u'msgs2.message'], null=False)),
            ('person', models.ForeignKey(orm[u'msgs2.person'], null=False))
        ))
        db.create_unique(m2m_table_name, ['message_id', 'person_id'])

        # Adding model 'Header'
        db.create_table(u'msgs2_header', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('key', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('value', self.gf('django.db.models.fields.TextField')()),
            ('message', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['msgs2.Message'])),
        ))
        db.send_create_signal(u'msgs2', ['Header'])

        # Adding model 'MessageBody'
        db.create_table(u'msgs2_messagebody', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('message', self.gf('django.db.models.fields.related.ForeignKey')(related_name='body', to=orm['msgs2.Message'])),
            ('text', self.gf('django.db.models.fields.TextField')()),
            ('html', self.gf('django.db.models.fields.TextField')()),
        ))
        db.send_create_signal(u'msgs2', ['MessageBody'])

        # Adding model 'Attachment'
        db.create_table(u'msgs2_attachment', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('filename', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('content_type', self.gf('django.db.models.fields.CharField')(max_length=50)),
            ('stored_location', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('file_md5', self.gf('django.db.models.fields.CharField')(max_length=40)),
            ('message', self.gf('django.db.models.fields.related.ForeignKey')(related_name='attachments', to=orm['msgs2.Message'])),
            ('mime_related', self.gf('django.db.models.fields.BooleanField')(default=False)),
        ))
        db.send_create_signal(u'msgs2', ['Attachment'])


    def backwards(self, orm):
        # Deleting model 'Person'
        db.delete_table(u'msgs2_person')

        # Deleting model 'Address'
        db.delete_table(u'msgs2_address')

        # Deleting model 'Message'
        db.delete_table(u'msgs2_message')

        # Removing M2M table for field recipients on 'Message'
        db.delete_table(db.shorten_name(u'msgs2_message_recipients'))

        # Removing M2M table for field members on 'Message'
        db.delete_table(db.shorten_name(u'msgs2_message_members'))

        # Deleting model 'Header'
        db.delete_table(u'msgs2_header')

        # Deleting model 'MessageBody'
        db.delete_table(u'msgs2_messagebody')

        # Deleting model 'Attachment'
        db.delete_table(u'msgs2_attachment')


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
            'message': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['msgs2.Message']"}),
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
            'html': ('django.db.models.fields.TextField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'message': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'body'", 'to': u"orm['msgs2.Message']"}),
            'text': ('django.db.models.fields.TextField', [], {})
        },
        u'msgs2.person': {
            'Meta': {'object_name': 'Person'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'})
        }
    }

    complete_apps = ['msgs2']