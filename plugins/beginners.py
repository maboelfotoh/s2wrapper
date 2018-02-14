# -*- coding: utf-8 -*-
# 03/15/11 - Add variables to beginners.ini
import re
import math
import time
import configparser
import threading
import os
from MasterServer import MasterServer
from PluginsManager import ConsolePlugin
from S2Wrapper import Savage2DaemonHandler


class beginners(ConsolePlugin):
	VERSION = "1.0.0"
	ms = None
	TIME = 0
	GAMESTARTED = 0
	STARTSTAMP = 0
	CHAT_INTERVAL = 10
	CHAT_STAMP = 0
	PHASE = 0
	MATCHES = 0
	playerlist = []
	adminlist = []
	ipban = []
	BANMATCH = 20
	SFLIMIT = 110
	LEVELLIMIT = 10
	MATCHLIMIT = 4
	
	def onPluginLoad(self, config):
		self.ms = MasterServer ()

		ini = configparser.ConfigParser()
		ini.read(config)
		
		for (name, value) in ini.items('var'):
			if (name == "banmatch"):
				self.BANMATCH = int(value)
			if (name == "sflimit"):
				self.SFLIMIT = int(value)
			if (name == "levellimit"):
				self.LEVELLIMIT = int(value)
			if (name == "matchlimit"):
				self.MATCHLIMIT = int(value)

		for (name, value) in ini.items('ipban'):
			self.ipban.append(name)

		admins = os.path.join(os.path.dirname(config),'admin.ini')	
		ini.read(admins)

		for (name, value) in ini.items('admin'):
			self.adminlist.append({'name': name, 'level' : value})
		print(self.adminlist)
		pass

	def onStartServer(self, *args, **kwargs):
		
		self.VERSION = "0.0.6"
		self.TIME = 0
		self.GAMESTARTED = 0
		self.STARTSTAMP = 0
		self.CHAT_INTERVAL = 10
		self.CHAT_STAMP = 0
		self.PHASE = 0
		self.MATCHES = 0
		self.playerlist = []

	def getPlayerByClientNum(self, cli):

		for client in self.playerlist:
			if (client['clinum'] == cli):
				return client


	def getPlayerByName(self, name):

		for client in self.playerlist:
			if (client['name'].lower() == name.lower()):
				return client


	def onConnect(self, *args, **kwargs):
		
		id = args[0]
		ip = args[2]
		for client in self.playerlist:
			if (client['clinum'] == id):
				print('already have entry with that clientnum!')
				return

		for each in self.ipban:
			if each == ip:
				kwargs['Broadcast'].broadcast("kick %s You are banned from this server" % (cli))
				

		self.playerlist.append ({'clinum' : id, 'acctid' : 0, 'level' : 0, 'sf' : 0, 'name' : 'X', 'active' : 0, 'banned' : False, 'ip' : ip, 'banstamp' : 0, 'kills' : 0})

		
	def onDisconnect(self, *args, **kwargs):
		
		cli = args[0]
		client = self.getPlayerByClientNum(cli)
		client ['active'] = 0
	

	def onSetName(self, *args, **kwargs):

		cli = args[0]
		playername = args[1]
		client = self.getPlayerByClientNum(cli)
		client ['name'] = playername
		

	def onAccountId(self, *args, **kwargs):

		doKick = False
		reason1 = "This is a beginners server. Please go play on a normal server."
		reason2 = "You (or someone at your IP address) have been temporarily prohibited from this server."
		reason3 = "Please go play on normal server."
		cli = args[0]
		id = args[1]
		stats = self.ms.getStatistics (id).get ('all_stats').get (int(id))
		
		level = int(stats['level'])
		sf = int(stats['sf'])
		wins = int(stats['wins'])
		losses = int(stats['losses'])
		dcs = int(stats['d_conns'])
		exp = int(stats['exp'])
		time = int(stats['secs'])
		if sf == 0 and time > 0:
			time = time/60
			sf = int(exp/time)
		total = wins + losses + dcs

		client = self.getPlayerByClientNum(cli)

		client ['acctid'] = int(id)
		client ['level'] = level
		client ['sf'] = sf
		client ['active'] = 1

		if client['banned']:
			reason = reason3
			doKick = True		

		for each in self.playerlist:
			if each['banned'] and (each['ip'] == client['ip']):
				reason = reason2
				doKick = True
				

		if (sf > self.SFLIMIT) and (total > self.MATCHLIMIT):
			reason = reason1
			doKick = True
			client ['banned'] = True
			client ['banstamp'] = self.MATCHES

		if (level > self.LEVELLIMIT):
			reason = reason1
			doKick = True

		for each in self.adminlist:
			if each['name'].lower() == client['name'].lower():
				doKick = False			
				client['banned'] = False
		if doKick:
			kwargs['Broadcast'].broadcast("kick %s \"%s\"" % (cli, reason))

		print(client)

	def onTeamChange (self, *args, **kwargs):
		
		team = int(args[1])
		cli = args[0]
		client = self.getPlayerByClientNum(cli)
		if (team > 0):
			client['active'] = 1
		if (team == 0):
			client['active'] = 0

	def onPhaseChange(self, *args, **kwargs):
		phase = int(args[0])
		self.PHASE = phase
	
		if (phase == 7):
			self.onGameEnd()
		if (phase == 5):
			self.onGameStart(*args, **kwargs)
		
	
	def onGameEnd(self, *args, **kwargs):
						
		self.MATCHES += 1
		#all players are unbanned after 15 matches
		for each in self.playerlist:
			each['kills'] = 0
			each['active'] = 0
			duration = self.MATCHES - int(each['banstamp'])
			if duration > self.BANMATCH:
				each['banned'] = False

		self.GAMESTARTED = 0


	def onGameStart (self, *args, **kwargs):
		
		
		self.STARTSTAMP = args[1]
		self.GAMESTARTED = 1
		for each in self.playerlist:
			each['kills'] = 0
	
	def onServerStatus(self, *args, **kwargs):
		CURRENTSTAMP = int(args[1])
		self.TIME = int(CURRENTSTAMP) - int(self.STARTSTAMP)
			
		if self.PHASE == 5:
			if (self.TIME > (10 * 60 * 1000)):
				self.smurfCheck (**kwargs)			

	def onGetLevels(self, *args, **kwargs):
		clinum = args[0]
		level = int(args[1])
		client = self.getPlayerByClientNum(clinum)
		

	def onGetLevels(self, *args, **kwargs):
		clinum = args[0]
		level = int(args[1])
		client = self.getPlayerByClientNum(clinum)
		doKick = False
		reason = "This is either a smurf account or you are too good for this server. You should play on another server."
		if level > 6:
			doKick = True
			client ['banned'] = True
			client ['banstamp'] = self.MATCHES

		if doKick:
			kwargs['Broadcast'].broadcast("kick %s \"%s\"" % (cli, reason))	
		
	def onHasKilled(self, *args, **kwargs):
		
		killed = self.getPlayerByName(args[0])
		killer = self.getPlayerByName(args[1])
		
		killer['kills'] += 1
		print(killer)
		print(killed)

	def smurfCheck(self, **kwargs):
		
		totalkills = 0
		activeplayers = 0
		avgkills = 0
		reason = "Congratulations! You have done a great job and have graduated from this server."

		for each in self.playerlist:
			if each['active'] == 1:
				activeplayers += 1
				totalkills += int(each['kills'])

		avgkills = int(totalkills/activeplayers)
		kwargs['Broadcast'].broadcast("echo BEGINNERS: Average kills: %s" % (avgkills))
		for players in self.playerlist:
			if players['active'] == 1:
				over = 'No'
				if (players['kills'] > (avgkills * 3)) and (players['kills'] > 20):
					over = 'Yes'
					cli = players['clinum']
					#players['banned'] = True
					#players['banstamp'] = self.MATCHES
					#kwargs['Broadcast'].broadcast("kick %s \"%s\"" % (cli, reason))
					kwargs['Broadcast'].broadcast("echo BEGINNERS: Player: %s, Kills: %s, Over?: %s" % (players['name'], players['kills'], over))
				
				
	def onMessage(self, *args, **kwargs):
		
		name = args[1]
		message = args[2]
		
		client = self.getPlayerByName(name)
		
		if (args[0] == "SQUAD") and (message == 'report bans'):
			for bans in self.playerlist:
				if bans['banned']:
					kwargs['Broadcast'].broadcast("SendMessage %s Banned: %s, IP: %s" % (client['clinum'], bans['name'], bans['ip']))



