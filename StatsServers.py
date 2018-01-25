#!/usr/bin/env python

import httplib, urllib, re, sys, logging, glob
#import parakmiko
from phpserialize import *
from scp import *
from urllib import urlencode

class StatsServers:

	S2GHOST = "masterserver1.talesfonewerth.com"
	S2GURL = "/irc_updater/irc_stats.php"
	headers = {}

	def __init__(self):
		self.headers = {
			"User-Agent": "PHP Script",
			"Content-Type": "application/x-www-form-urlencoded"
		}


	def decode (self, response):
		return loads(response, object_hook=phpobject)

	def queryserver (self, params):
		url = "/irc_updater/svr_request_pub.php"
		conn = httplib.HTTPConnection (self.MASTERHOST)
		conn.request ("POST", url, params, self.headers)

	def s2gstats (self, params):

		conn = httplib.HTTPConnection (self.S2GHOST)
		conn.request ("POST", self.S2GURL, params, self.headers)

		response = conn.getresponse()

		if response.status <> 200:
			return None

		data = response.read()
		conn.close()
		
		#print params
		#print data
		return data

	def replays (self, params):
		
		conn = httplib.HTTPConnection (self.S2GHOST)
		json_headers = {'content-type' : 'application/json'}
		conn.request ("POST", self.S2GURL, params, json_headers)

		response = conn.getresponse()

		if response.status <> 200:
			return None

		data = response.read()
		conn.close()
		#print params
		#print data
		return data

	#This is currently not used. Replays are sent using os.system
	'''
	def sendreplay (self, params):
		server = '188.40.92.72'
		port = 22
		user = 'scponly'
		remotepath = 'incoming'
		client = paramiko.SSHClient()
		client.load_system_host_keys()
		client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
		client.connect(server, port, user)
		
		scp = SCPClient(client.get_transport())
		scp.put(params, remote_path=remotepath)
		client.close()
	'''
if __name__ == '__main__':

	ss = StatsServer()
	sentdir = 'sent'
	for infile in glob.glob('*.s2r'):
		print "Sending replay file: " + infile
		replay = infile
		try:
			ss.sendreplay(replay)
			
		except:
			print 'upload failed. replay not sent'				
			

		print 'Sent replay'
		

