import gmail.gmail as gmail
import datetime
import time
from msgs2.models import Message, MessageFlag, Account
from msgs2.importing import import_message

### Usage:
### For a new account, call load_all_messages to get the full history (at least since since_date) into the db
### This will take a long time, depending on number of messages (~2-3 minutes per 2000 messages)
###
### For accounts that have already been loaded, call load_new_messages to bring them up to date with server
###
### For all accounts, call sync_inbox_state to correctly set the inbox flags.  Note this is currently just one-way
### Sync - inbox flags propagage from server to db, but not the other way around.

### TODO should combine load_all_messages and load_new_messages (or at least the logic for error handling etc)


class Fetcher():
    _gmail = None
    _account = None

    def login(self, un=None, pw=None):
        """

        :rtype : Gmail object
        """
        if not pw:
            with open('pw', 'r') as pwf:
                pw = pwf.read()
                if pw:
                    print "using saved password"

        if not un:
            un = "thechild@gmail.com"

        print "logging in to gmail as %s" % (un)
        gm = gmail.login(un, pw)
        if gm.logged_in:
            print "logged in"
        else:
            print "error logging in."
        self._gmail = gm

        accs = Account.objects.filter(address=un)
        if accs.count() == 0:
            self._account = Account(name='Gmail',
                                    server_type=Account.TYPE_GMAIL,
                                    address=un)
            self._account.save()
        else:
            self._account = accs[0]

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
            nm = import_message(m, self._account)
            new_messages.append(nm)
        return nm

    # loads all messages since the last time it was run or 30 days ago, whichever is smaller
    # set newest_time to an older time to get older messages, or just use load_all_messages
    def load_new_messages(self, newest_time=datetime.datetime.today() - datetime.timedelta(days=30)):
        if Message.objects.exists():
            newest_time = max(newest_time, Message.objects.latest(field_name='sent_date').sent_date)

        return self.load_all_messages(since_date=newest_time)

    def fetch_multiple_messages(self, messages):
        message_dict = {m.uid: m for m in messages}
        print "Fetching {} messages...".format(len(messages))
        start_time = time.time()
        fetched_messages = self.gm().fetch_multiple_messages(message_dict)
        end_time = time.time()
        print "Fetched them in {} seconds. Starting import process...".format(end_time - start_time)
        return fetched_messages

    # Loads all messages received since since_date in steps of step (I've been using 2000)
    # Used for loading large volumes of messages from gmail
    def load_all_messages(self, step=100, since_date=None):
        gm = self.gm()

        load_start = time.time()

        print "Loading all messages since {} in steps of {}...".format(since_date, step)
        # loads all messages since since_date (or forever if it is None)
        # in blocks of step (default 10)

        # first, get all messages
        if since_date:
            all_messages = gm.all_mail().mail(after=since_date)
        else:
            all_messages = gm.all_mail().mail()
        print "Found a total of {} messages, starting the process...".format(len(all_messages))

        num_added = 0
        steps = 0

        failed_messages = {}

        for message_chunk in [all_messages[i:i + step] for i in range(0, len(all_messages), step)]:
            steps = steps + 1
            print "Fetching group {} of {}...".format(steps, (len(all_messages) - 1) / step + 1)
            # TODO don't fetch messages where the uid is already in the db (only works when we only pull from all_mail)
            fetched_messages = self.fetch_multiple_messages(message_chunk)
            for message in fetched_messages.values():
                try:
                    m = import_message(message, self._account)
                except (KeyboardInterrupt, SystemExit):
                    raise
                except Exception as e:
                    print "XXXX: Exception parsing message with uid {} and messageid {}".format(
                        message.uid, message.message_id)
                    print e
                    failed_messages[message.uid] = (message, e)

                if m:
                    num_added += 1

        load_end = time.time()

        if len(all_messages) > 0:                
            print "***Fetched a total of {} messages in {:.2f} seconds, and added {} ({:.2f}%) to the db.".format(
                len(all_messages), load_end - load_start, num_added, 100.0 * num_added / len(all_messages))
        else:
            print "***There were no new messages."

        if failed_messages:
            print "***Encountered a total of {} messages that had an error.  Returning them.".format(
                len(failed_messages.keys()))
        return failed_messages

    # moves all messages in db out of the inbox, then moves those in the inbox (on gmail) into the db's inbox, adding
    # them if necessary, and setting the correct read/unread state
    def sync_inbox_state(self):
        print "Beginning inbox synchronization..."
        gm = self.gm()

        clean_inbox()

        # find messages that are in the inbox, and flag them as such, adding to db if not already there
        inbox_messages = gm.inbox().mail(prefetch=True)
        for message in inbox_messages:
            try:
                dbm = Message.objects.get(message_id=message.message_id)
            except Message.DoesNotExist:
                dbm = import_message(message, self._account)

            dbm.flags.add(MessageFlag(flag=MessageFlag.INBOX_FLAG))
            dbm.flags.filter(flag=MessageFlag.UNREAD_FLAG).delete()
            if not message.is_read():
                dbm.flags.add(MessageFlag(flag=MessageFlag.UNREAD_FLAG))

        print "Updated inbox - there are {} messages in the inbox.".format(len(inbox_messages))


def clean_inbox():
    MessageFlag.objects.filter(flag=MessageFlag.INBOX_FLAG).delete()


if __name__ == "__main__":
    print "Updating message store..."
    f = Fetcher()
    f.login()
    nm = f.load_new_messages()
    print "Finished loading {} new messages.".format(len(nm))
