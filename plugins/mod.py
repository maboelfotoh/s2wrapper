# -*- coding: utf-8 -*-
import re
import math
import time
import ConfigParser
import threading
import random
import os
import PluginsManager
from MasterServer import MasterServer
from PluginsManager import ConsolePlugin
from S2Wrapper import Savage2DaemonHandler
from operator import itemgetter
from random import choice
import urllib2
import subprocess
import glob

class mod(ConsolePlugin):
	VERSION = "0.0.1"
	playerlist = []
	superlist = []
	modlist = []
	PHASE = 0
	
	def onPluginLoad(self, config):
		self.ms = MasterServer ()
		self.CONFIG = config
		ini = ConfigParser.ConfigParser()
		ini.read(config)
		for (name, value) in ini.items('admin'):
			self.superlist.append({'name': name, 'level' : value})
		pass
	
	def reload_config(self):
		
		self.superlist = []
		ini = ConfigParser.ConfigParser()
		ini.read(self.CONFIG)

		for (name, value) in ini.items('admin'):
			self.superlist.append({'name': name, 'level' : value})

	def reload_plugins(self):
	
		config = os.path.realpath(os.path.dirname (os.path.realpath (__file__)) + "/../s2wrapper.ini")
		
		ini = ConfigParser.ConfigParser()
		ini.read(config)
		for name in ini.options('plugins'):
			if name == 'sandbox':
				PluginsManager.reload(name)
				continue
			if ini.getboolean('plugins', name):
				PluginsManager.reload(name)
		
	def onStartServer(self, *args, **kwargs):
				
		self.playerlist = []
		self.modreset()
		

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

		for client in self.playerlist:
			if (client['clinum'] == id):
				return
		
		self.playerlist.append ({'clinum' : id,\
					 'acctid' : 0,\
					 'name' : 'X',\
					 'active' : False,\
					 'level' : 0,\
					 'super' : False,})
	
	def onDisconnect(self, *args, **kwargs):
		
		cli = args[0]
		client = self.getPlayerByClientNum(cli)
		client ['active'] = False

	def onSetName(self, *args, **kwargs):
		
		cli = args[0]
		playername = args[1]
		client = self.getPlayerByClientNum(cli)
		client ['name'] = playername
		
		kwargs['Broadcast'].broadcast("SendMessage %s ^yThis server is running the Mod Manager plugin by GGGGGGGG. It's currently running the version %s of the plugin. This is a very simple mod manager that changes the variables according to the modfiles.." % (cli, self.VERSION))
		kwargs['Braodcast'].broadcast("SendMessage %s ^yMods currently active: %" % (cli, self.modlist))
					
	def onAccountId(self, *args, **kwargs):
		cli = args[0]
		id = args[1]
		stats = self.ms.getStatistics (id).get ('all_stats').get (int(id))
		level = int(stats['level'])
					
		client = self.getPlayerByClientNum(cli)
		client['level'] = level
		client['active'] = True	
		if self.isSuperuser(client, **kwargs):
			kwargs['Broadcast'].broadcast(\
			"SendMessage %s ^cYou are registered as a sudo. You can now enable mods on the server Use ^rmod help ^cfor more information.."\
			 % (cli))
			client['super'] = True
		
	def isSuperuser(self, client, **kwargs):
		superuser = False

		for each in self.superlist:
			if client['name'].lower() == each['name']:
				if each['rank'] == 'super':
					superuser = True
		
		return superuser
	
	def modreset(self, **kwargs):
		self.modlist = []
		with open("../mod/reset.txt", 'r') as original:
			for line in original:
				kwargs['Broadcast'].broadcast("%s" % (line))
		original.close()		

	def onMessage(self, *args, **kwargs):
		
		name = args[1]
		message = args[2]
		
		client = self.getPlayerByName(name)
		superuser = self.isSuperUser(client, **kwargs)
			
			
		if not superuser:
			return
		
		modenable = re.match("mod enable (\S+)", message, flags=re.IGNORECASE)
		modactive = re.match("mod get active", message, flags=re.IGNORECASE)
		modindirectory = re.match("mod get list", message, flags=re.IGNORECASE)
		modreset = re.match("mod reset", message, flags=re.IGNORECASE)
		
		if modenable:
			modName = "../mod/" + modenable.group(1) + ".txt"
			self.modlist.append(modenable.group(1))
			with open(modName, 'r') as modfile:
				for line in modfile:
					kwargs['Broadcast'].broadcast("%s" % (line))
			modfile.close()
			kwargs['Broadcast'].broadcast("SendMessage -1 %s has been enabled." % (modenable.group(1)))
					
		if modactive:
			kwargs['Broadcast'].broadcast("SendMessage %s mods currently active on this server:" % (client['clinum']))
			for element in modactive:
				kwargs['Broadcast'].broadcast("SendMessage %s %s" % (client['clinum'], element))
		
		if modreset:
			self.modreset()
			kwargs['Broadcast'].broadcast("SendMessage -1 All mods have been reseted.")
			
		if modindirectory:
			modindir = os.listdir("../mod/")
			for each in modindir:
				kwargs['Broadcast'].broadcast("%s %s" % (client['clinum'], each))
						
	def onPhaseChange(self, *args, **kwargs):
		phase = int(args[0])
		self.PHASE = phase

		if (phase == 7):
			self.modreset()	
			for each in self.playerlist:
				each['team'] = 0
				each['commander'] = False
				
		if (phase == 6):
		#fetch leader list and reload at the start of each game
			try:
				response = urllib2.urlopen('http://188.40.92.72/admin.ini')
				superlist = response.read()
				superfile = os.path.join(os.path.dirname(self.CONFIG),'mod.ini')
				f = open(superfile, 'w')
				f.write(superlist)
				f.close
				#reload the config file		
				self.onPluginLoad(superfile)
			except:
				return
				
	def onListClients(self, *args, **kwargs):
		clinum = int(args[0])
		name = args[2]
		ip = args[1]
		

		client = self.getPlayerByName(name)
		if not client:
		#if a player is missing from the list this will put them as an active player and get stats
		#usually used when reloading plugin during a game
			acct = self.ms.getAccount(name)
			acctid = acct[name]
			self.onConnect(clinum, 0000, ip, 0000, **kwargs)
			self.onSetName(clinum, name, **kwargs)
			self.onAccountId(clinum, acctid, **kwargs)
			client = self.getPlayerByName(name)
			
		client['active'] = True
		kwargs['Broadcast'].broadcast(\
		"echo CLIENT %s is on TEAM #GetTeam(|#GetIndexFromClientNum(%s)|#)#"\
		 % (client['clinum'], client['clinum']))