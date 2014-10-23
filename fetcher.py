import gmail.gmail as gmail
import datetime
import time
from msgs2.models import import_message, Message, MessageFlag, Address, Attachment, Person

class Fetcher():
    _gmail = None

    def login(self):
        """

        :rtype : Gmail object
        """
        with open('pw', 'r') as pwf:
            pw = pwf.read()
            if pw:
                print "using saved password"
        un = "thechild@gmail.com"

        print "logging in to gmail as %s" % (un)
        gm = gmail.login(un, pw)
        if gm.logged_in:
            print "logged in"
        else:
            print "error logging in."
        self._gmail = gm
        return self._gmail

    def gm(self):
        if self._gmail:
            return self._gmail
        else:
            return self.login()

    def import_messages_from_inbox(self, since_date=None):
        gm = self.gm()

        if since_date:
            inbox = gm.all_mail().mail(after=since_date, prefetch=True)
        else:
            inbox = gm.inbox().mail(prefetch=True)

        new_messages = []
        for (index, m) in enumerate(inbox):
            print "fetching message (%s/%s)" % (index+1, len(inbox))
            m.fetch()
            nm = import_message(m)
            new_messages.append(nm)
        return nm

    # loads new messages into the db - run as a batch job
    def load_new_messages(self, newest_time=datetime.datetime.today() - datetime.timedelta(days=30), full_pull=False,
                          prefetch=True):
        gm = self.gm()
        # find the newest message in the database

        if (not full_pull) and Message.objects.exists():
            newest_time = max(newest_time, Message.objects.latest(field_name='sent_date').sent_date)
            # TODO note, will not pull messages older than newest_time, no matter what

        print "Fetching all messages since {}".format(newest_time)

        messages = gm.all_mail().mail(after=newest_time, prefetch=prefetch)  # TODO this is probably buggy

        for (index, m) in enumerate(messages):
            print "Fetching message ({}/{})".format(index+1, len(messages))
            m.fetch_thread()
            new_messages = [import_message(m) for m in m.thread]

        return new_messages

    def load_all_messages(self, step=100, since_date=None):
        gm = self.gm()

        load_start = time.time()

        print "Loading all messages since {} in steps of {}...".format(since_date, step)
        # this should be called very infrequently.
        # loads all messages since since_date (or forever if it is None)
        # in blocks of step (default 10)

        # first, get all messages
        if since_date:
            all_messages = gm.all_mail().mail(after=since_date)
        else:
            all_messages = gm.all_mail().mail()
        print "Found a total of {} messages, starting the process...".format(len(all_messages))

        # helper to actually process a set of messages:
        def load_messages(messages):
            message_dict = {m.uid: m for m in messages}
            print "Fetching {} messages...".format(len(messages))
            start_time = time.time()
            fetched_messages = gm.fetch_multiple_messages(message_dict)
            end_time = time.time()
            print "Fetched them in {} seconds. Starting import process...".format(end_time - start_time)
            for message in fetched_messages.values():
                import_message(message)
            print "Imported."

        for message_chunk in [all_messages[i:i + step] for i in range(0, len(all_messages), step)]:
            load_messages(message_chunk)

        load_end = time.time()

        print "***Fetched a total of {} messages in {} seconds.".format(len(all_messages), load_end - load_start)


    # moves all messages in db out of the inbox, then moves those in the inbox (on gmail) into the db's inbox, adding
    # them if necessary, and setting the correct read/unread state
    def sync_inbox_state(self):
        gm = self.gm()

        clean_inbox()

        # find messages that are in the inbox, and flag them as such, adding to db if not already there
        inbox_messages = gm.inbox().mail(prefetch=True)
        for message in inbox_messages:
            try:
                dbm = Message.objects.get(message_id=message.message_id)
            except Message.DoesNotExist:
                dbm = import_message(message)

            dbm.flags.add(MessageFlag(flag=MessageFlag.INBOX_FLAG))
            dbm.flags.filter(flag=MessageFlag.UNREAD_FLAG).delete()
            if not message.is_read():
                dbm.flags.add(MessageFlag(flag=MessageFlag.UNREAD_FLAG))


def clean_inbox():
    MessageFlag.objects.filter(flag=MessageFlag.INBOX_FLAG).delete()


if __name__ == "__main__":
    print "Updating message store..."
    f = Fetcher()
    f.login()
    nm = f.load_new_messages()
    print "Finished loading {} new messages.".format(len(nm))