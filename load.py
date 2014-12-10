import os
import argparse

if __name__ == "__main__":
	if not os.environ.has_key('DJANGO_SETTINGS_MODULE'):
		os.environ['DJANGO_SETTINGS_MODULE'] = 'mbox.settings'

import pickle
import exchange_fetcher
import fetcher as gmail_fetcher
import time

PW_FN = 'pws'
UN_FN = 'uns'
URL_FN = 'urls'

def load_exchange(url, username, password):
	print "Loading messages from exchange for user %s" % username
	fetcher = exchange_fetcher.ExchangeFetcher(url, username, password)
	#fetcher.load_inbox()
	fetcher.load_archive()
	print "Finished loading exchange messages."

def load_gmail(username, password):
	print "Loading messages from gmail for user %s" % username
	fetcher = gmail_fetcher.Fetcher()
	fetcher.login(username, password)
	fetcher.load_new_messages()
	fetcher.sync_inbox_state()
	print "Finished loading gmail messages."

def unpickle(filename):
	with open(filename, 'r') as f:
		data = pickle.load(f)
	return data

def get_fetchers():
	pws = unpickle(PW_FN)
	uns = unpickle(UN_FN)
	urls = unpickle(URL_FN)

	e_fetcher = exchange_fetcher.ExchangeFetcher(urls['exchange'], uns['exchange'], pws['exchange'])
	g_fetcher = gmail_fetcher.Fetcher()
	g_fetcher.login(uns['gmail'], pws['gmail'])

	return (e_fetcher, g_fetcher)
	
def load_messages(exchange=True, gmail=True):
	pws = unpickle(PW_FN)
	uns = unpickle(UN_FN)
	urls = unpickle(URL_FN)
	start_gmail = None

	if exchange:
		start_exchange = time.time()
		load_exchange(urls['exchange'], uns['exchange'], pws['exchange'])
	if gmail:
		start_gmail = time.time()
		load_gmail(uns['gmail'], pws['gmail'])
	finish_time = time.time()

	if gmail and exchange:
		print "\nTotal Time:\t{:.2f}".format(finish_time - start_exchange)
	if exchange:
		print "Exchange:\t{:.2f}".format((start_gmail or finish_time) - start_exchange)
	if gmail:
		print "Gmail:\t\t{:.2f}".format(finish_time - start_gmail)

# archive_folder_id = u'AAATAGNjaGlsZEByZWRwb2ludC5jb20ALgAAAAAAraG1Y5iBIE2Pttml6WCoNgEA1R/peAifyESnEhL2wqjzXwEMby8thwAA'

if __name__ == "__main__":
	parser = argparse.ArgumentParser()
	parser.add_argument('-ne', '--noexchange', dest='exchange', action='store_false')
	parser.add_argument('-ng', '--nogmail', dest='gmail', action='store_false')
	args = parser.parse_args()

	load_messages(exchange=args.exchange, gmail=args.gmail)