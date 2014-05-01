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

class sandbox(ConsolePlugin):
	VERSION = "0.0.1"
	playerlist = []
	leaderlist = []
	PHASE = 0
	CONFIG = None
	
	def onPluginLoad(self, config):
		self.ms = MasterServer ()
		self.CONFIG = config
		ini = ConfigParser.ConfigParser()
		ini.read(config)
		for (name, value) in ini.items('sandbox'):
			self.leaderlist.append({'name': name, 'level' : value})
		pass
	
	def reload_config(self):
		
		self.leaderlist = []
		ini = ConfigParser.ConfigParser()
		ini.read(self.CONFIG)

		for (name, value) in ini.items('sandbox'):
			self.leaderlist.append({'name': name, 'level' : value})

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
					 'leader' : False,})
	
	def onDisconnect(self, *args, **kwargs):
		
		cli = args[0]
		client = self.getPlayerByClientNum(cli)
		client ['active'] = False

	def onSetName(self, *args, **kwargs):
		
		cli = args[0]
		playername = args[1]
		client = self.getPlayerByClientNum(cli)
		client ['name'] = playername
					
	def onAccountId(self, *args, **kwargs):
		cli = args[0]
		id = args[1]
		stats = self.ms.getStatistics (id).get ('all_stats').get (int(id))
		level = int(stats['level'])
					
		client = self.getPlayerByClientNum(cli)
		client['level'] = level
		client['active'] = True	
		if self.isLeader(client, **kwargs):
			kwargs['Broadcast'].broadcast(\
			"SendMessage %s ^cYou are registered as an administrator. Send the chat message: ^rhelp ^cto see what commands you can perform."\
			 % (cli))
			client['leader'] = True
		
	def isLeader(self, client, **kwargs):
		leader = False
		
		for each in self.leaderlist:
			if client['name'].lower() == each:
				leader = True
		
		return leader

	def onMessage(self, *args, **kwargs):
		
		name = args[1]
		message = args[2]
		
		client = self.getPlayerByName(name)
		leader = self.isLeader(client, **kwargs)
		
		#ignore everything else if it isn't from admin
		if not leader:
			return

		giveteamgold = re.match("sb giveteamgold (\S+) (\S+)", message, flags=re.IGNORECASE)
		giveplayergold = re.match("sb givegold (\S+) (\S+)", message, flags=re.IGNORECASE)
		giveplayerammo = re.match("sb giveammo (\S+)", message, flags=re.IGNORECASE)
		kick = re.match("sb kick (\S+)", message, flags=re.IGNORECASE)
		slap = re.match("sb slap (\S+)", message, flags=re.IGNORECASE)
		changeworld = re.match("sb changeworld (\S+)", message, flags=re.IGNORECASE)
		help = re.match("help", message, flags=re.IGNORECASE)
		movespeed = re.match("sb mod movespeed (\S+)", message, flags=re.IGNORECASE)
		gravity = re.match("sb mod gravity (\S+)", message, flags=re.IGNORECASE)
		buildspeed = re.match("sb mod buildspeed (\S+)", message, flags=re.IGNORECASE)
		teamchange = re.match("sb allowteamchange", message, flags=re.IGNORECASE)
		teamdifference = re.match("sb teamdiff", message, flags=re.IGNORECASE)
		changepassword = re.match("sb password (\S+)", message, flags=re.IGNORECASE)
					
		if giveteamgold:
			kwargs['Broadcast'].broadcast("giveteamgold %s %s" % (giveteamgold.group(1), giveteamgold.group(2)))
			
		if giveplayergold:
			kwargs['Broadcast'].broadcast("givegold %s %s" % (giveplayergold.group(1), giveplayergold.group(2)))
			
		if giveplayerammo:
			kwargs['Broadcast'].broadcast("giveammo %s" % (giveplayerammo.group(1)))
		
		if kick:
			#kicks a player from the server
			reason = "An administrator has removed you from the server, probably for being annoying"
			kickclient = self.getPlayerByName(kick.group(1))
			kwargs['Broadcast'].broadcast("Kick %s \"%s\""% (kickclient['clinum'], reason))

		if slap:
			#slap will move a player x+100, y+200 to get them off of a structure
			
			slapclient = self.getPlayerByName(slap.group(1))
			kwargs['Broadcast'].broadcast(\
				"set _slapindex #GetIndexFromClientNum(%s)#;\
				 set _sx #GetPosX(|#_slapindex|#)#; set _sy #GetPosY(|#_slapindex|#)#; set _sz #GetPosZ(|#_slapindex|#)#;\
				 SetPosition #_slapindex# [_sx + 200] [_sy + 200] #_sz#;\
				 SendMessage %s ^cAn adminstrator has moved you for jumping on buildings. YOU WILL BE BANNED if this action persists"\
				 % (slapclient['clinum'], slapclient['clinum']))
			

		if changeworld:
			#change the map
			kwargs['Broadcast'].broadcast("changeworld %s" % (changeworld.group(1)))
		
		if movespeed:
			kwargs['Broadcast'].broadcast("set p_speed %s" % (movespeed.group(1)))
			
		if gravity:
			kwargs['Broadcast'].broadcast("set p_gravity %s" % (gravity.group(1)))
			
		if buildspeed:
			kwargs['Broadcast'].broadcast(\
				"set Player_Conjurer_BuildingRepairRate %s;\
				 set Player_Builder_BuildingRepairRate %s;"\
				 % (buildspeed.group(1)))
			
		if teamchange:
			kwargs['Broadcast'].broadcast("set g_allowteamchange true")

		if teamdifference:
			kwargs['Broadcast'].broadcast("set sv_maxTeamDifference 20")
			
		if changepassword:
			kwargs['Broadcast'].broadcast("set svr_connectpass %s" % (changepassword.group(1)))

		if help:
			kwargs['Broadcast'].broadcast(\
				"SendMessage %s All commands on the server are done through server chat."\
				 % (client['clinum']))
			kwargs['Broadcast'].broadcast(\
				"SendMessage %s ^rsb giveteamgold team amount^w. will give gold to a team."\
				 % (client['clinum']))
			kwargs['Broadcast'].broadcast(\
				"SendMessage %s ^rsb giveplayergold player amount ^wwill give gold to a player."\
				 % (client['clinum']))
			kwargs['Broadcast'].broadcast(\
				"SendMessage %s ^rsb giveplayerammo player ^wwill give ammo to a player."\
				 % (client['clinum']))
			kwargs['Broadcast'].broadcast(\
				"SendMessage %s ^rsb kick ^wwill remove a player from the server."\
				 % (client['clinum']))
			kwargs['Broadcast'].broadcast(\
				"SendMessage %s ^rsb slap playername ^wwill move the player. Use to get them off of structures if they are exploiting."\
				 % (client['clinum']))
			kwargs['Broadcast'].broadcast(\
				"SendMessage %s ^rsb changeworld mapname ^wwill change the map to the desired map."\
				 % (client['clinum']))
			kwargs['Broadcast'].broadcast(\
				"SendMessage %s ^rsb movespeed amount ^wwill change the movement speed of the server."\
				 % (client['clinum']))
			kwargs['Broadcast'].broadcast(\
				"SendMessage %s ^rsb gravity amount ^wwill change the gravity."\
				 % (client['clinum']))
			kwargs['Broadcast'].broadcast(\
				"SendMessage %s ^rsb buildspeed amount ^wwill change the build speed."\
				 % (client['clinum']))
			kwargs['Broadcast'].broadcast(\
				"SendMessage %s ^rsb teamchange ^wwill allow switching team."\
				 % (client['clinum']))
			kwargs['Broadcast'].broadcast(\
				"SendMessage %s ^rsb teamdifference ^wwill allow everyone to join in the same team."\
				 % (client['clinum']))
						
	def onPhaseChange(self, *args, **kwargs):
		phase = int(args[0])
		self.PHASE = phase

		if (phase == 7):
			self.banlist = []	
			for each in self.playerlist:
				each['team'] = 0
				each['commander'] = False
				
		if (phase == 6):
		#fetch admin list and reload at the start of each game
			try:
				response = urllib2.urlopen('http://cedeqien.com/leader.ini')
				leaderlist = response.read()
				leaderfile = os.path.join(os.path.dirname(self.CONFIG),'leader.ini')
				f = open(leaderfile, 'w')
				f.write(leaderlist)
				f.close
				#reload the config file		
				self.onPluginLoad(leaderfile)
			except:
				return