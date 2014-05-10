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
	VERSION = "0.1.1"
	playerlist = []
	leaderlist = []
	PHASE = 0
	
	def onPluginLoad(self, config):
		self.ms = MasterServer ()
		self.CONFIG = config
		ini = ConfigParser.ConfigParser()
		ini.read(config)
		for (name, value) in ini.items('sandboxs'):
			self.leaderlist.append({'name': name, 'level' : value})
		pass
	
	def reload_config(self):
		
		self.leaderlist = []
		ini = ConfigParser.ConfigParser()
		ini.read(self.CONFIG)

		for (name, value) in ini.items('sandboxs'):
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
		
		kwargs['Broadcast'].broadcast("SendMessage %s ^yThis server is running the Sandbox plugin by GGGGGGGG. Version : %s. Mods currently active: ^r%" % (cli, self.VERSION, self.modlist))
					
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
			"SendMessage %s ^cYou are registered as a leader. You can now use the sandbox. Send the chat message: ^rsb help ^cto see what commands you can perform."\
			 % (cli))
			client['leader'] = True
			
	def modreset(self, **kwargs):
		self.modlist = []
		with open("./plugins/mods/reset.txt", 'r') as original:
			for line in original:
				kwargs['Broadcast'].broadcast("%s" % (line))
		original.close()		
		
	def isLeader(self, client, **kwargs):
		leader = False
		
		for each in self.leaderlist:
			if client['name'].lower() == each['name']:
				leader = True
		
		return leader

	def onMessage(self, *args, **kwargs):
		
		name = args[1]
		message = args[2]
		
		client = self.getPlayerByName(name)
		leader = self.isLeader(client, **kwargs)
			
			
		#disable for now, will figure it out tomorrow when I wake up
		#if not leader:
			#return
		
		startgame = re.match("sb startgame", message, flags=re.IGNORECASE)
		giveteamgold = re.match("sb giveteamgold (\S+) (\S+)", message, flags=re.IGNORECASE)
		giveplayergold = re.match("sb givegold (\S+) (\S+)", message, flags=re.IGNORECASE)
		giveplayersoul = re.match("sb givesoul (\S+) (\S+)", message, flags=re.IGNORECASE)
		giveplayerexperience = re.match("sb giveexp (\S+) (\S+)", message, flags=re.IGNORECASE)
		giveplayerammo = re.match("sb giveammo (\S+)", message, flags=re.IGNORECASE)
		kick = re.match("sb kick (\S+)", message, flags=re.IGNORECASE)
		slap = re.match("sb slap (\S+)", message, flags=re.IGNORECASE)
		changeworld = re.match("sb changeworld (\S+)", message, flags=re.IGNORECASE)
		help = re.match("sb help", message, flags=re.IGNORECASE)
		modhelp = re.match("sb mod help", message, flags=re.IGNORECASE)
		movespeed = re.match("sb mod movespeed (\S+)", message, flags=re.IGNORECASE)
		gravity = re.match("sb mod gravity (\S+)", message, flags=re.IGNORECASE)
		buildspeed = re.match("sb mod buildspeed (\S+)", message, flags=re.IGNORECASE)
		jump = re.match("sb mod jump (\S+)", message, flags=re.IGNORECASE)
		teamchange = re.match("sb allowteamchange", message, flags=re.IGNORECASE)
		teamdifference = re.match("sb teamdiff", message, flags=re.IGNORECASE)
		changepassword = re.match("sb password (\S+)", message, flags=re.IGNORECASE)
		swap = re.match("sb swap (\S+)", message, flags=re.IGNORECASE)
		spec = re.match("sb spec (\S+)", message, flags=re.IGNORECASE)
		
		
		modenable = re.match("mm enable (\S+)", message, flags=re.IGNORECASE)
		modactive = re.match("mm get active", message, flags=re.IGNORECASE)
		modindirectory = re.match("mm get list", message, flags=re.IGNORECASE)
		modreset = re.match("mm reset", message, flags=re.IGNORECASE)
		mmhelp = re.match("mm help", message, flags=re.IGNORECASE)
		
		if startgame:
			kwargs['Broadcast'].broadcast("startgame")
					
		if giveteamgold:
			kwargs['Broadcast'].broadcast("giveteamgold %s %s" % (giveteamgold.group(1), giveteamgold.group(2)))
			
		if giveplayergold:
			playergold = self.getPlayerByName(giveplayergold.group(1))
			kwargs['Broadcast'].broadcast("givegold %s %s" % (playergold['clinum'], giveplayergold.group(2)))
			
		if giveplayerammo:
			playerammo = self.getPlayerByName(giveplayerammo.group(1))
			kwargs['Broadcast'].broadcast("giveammo %s" % (playerammo['clinum']))

		if giveplayersoul:
			playersoul = self.getPlayerByName(giveplayersoul.group(1))
			kwargs['Broadcast'].broadcast("givesoul %s %s" % (playersoul['clinum'], giveplayersoul.group(2)))
			
		if giveplayerexperience:
			playerexperience = self.getPlayerByName(giveplayerexperience.group(1))
			kwargs['Broadcast'].broadcast("giveexp %s %s" % (playerexperience['clinum'], giveplayerexperience.group(2)))
		
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
		
		if jump:
			kwargs['Broadcast'].broadcast("set p_jump %s" % (jump.group(1)))
			
		if gravity:
			kwargs['Broadcast'].broadcast("set p_gravity %s" % (gravity.group(1)))
			
		if buildspeed:
			kwargs['Broadcast'].broadcast(\
				"set Player_Conjurer_BuildingRepairRate %s;\
				 set Player_Engineer_BuildingRepairRate %s;"\
				 % (buildspeed.group(1), buildspeed.group(1)))
			
		if teamchange:
			kwargs['Broadcast'].broadcast("set g_allowteamchange true")

		if teamdifference:
			kwargs['Broadcast'].broadcast("set sv_maxTeamDifference 20")
			
		if changepassword:
			kwargs['Broadcast'].broadcast("set svr_connectpass %s" % (changepassword.group(1)))
			
		if spec:
			specplayer = self.getPlayerByName(spec.group(1))
			specteam = 0
			kwargs['Broadcast'].broadcast(\
				"SetTeam #GetIndexFromClientNum(%s)# %s"\
				% (specplayer['clinum'], specteam))
				
		if swap:
			#swap a player to a different team
			swapplayer = self.getPlayerByName(swap.group(1))
			newteam = 0
			team = swapplayer['team']
			if team == 1:
				newteam = 2
			if team == 2:
				newteam = 1
			if newteam == 0:
				return
			kwargs['Broadcast'].broadcast(\
				"SetTeam #GetIndexFromClientNum(%s)# %s"\
				 % (swapplayer['clinum'], newteam))
			
		if help:
			kwargs['Broadcast'].broadcast(\
				"SendMessage %s All commands on the server are done through server chat."\
				 % (client['clinum']))
			kwargs['Broadcast'].broadcast(\
				"SendMessage %s ^rsb modhelp ^w for more info about the sb mod commands."\
				 % (client['clinum']))
			kwargs['Broadcast'].broadcast(\
				"SendMessage %s ^rsb startgame ^w will start the game"\
				% (client['clinum']))
			kwargs['Broadcast'].broadcast(\
				"SendMessage %s ^rsb giveteamgold team amount^w. will give gold to a team."\
				 % (client['clinum']))
			kwargs['Broadcast'].broadcast(\
				"SendMessage %s ^rsb givegold player amount ^wwill give gold to a player."\
				 % (client['clinum']))
			kwargs['Broadcast'].broadcast(\
				"SendMessage %s ^rsb givesoul player amount ^wwill give souls to a player."\
				 % (client['clinum']))
			kwargs['Broadcast'].broadcast(\
				"SendMessage %s ^rsb giveexperience player amount ^wwill give experience to a player."\
				 % (client['clinum']))
			kwargs['Broadcast'].broadcast(\
				"SendMessage %s ^rsb giveammo player ^wwill give ammo to a player."\
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
				"SendMessage %s ^rsb allowteamchange ^wwill allow switching team."\
				 % (client['clinum']))
			kwargs['Broadcast'].broadcast(\
				"SendMessage %s ^rsb teamdiff ^wwill allow everyone to join in the same team."\
				 % (client['clinum']))
			kwargs['Broadcast'].broadcast(\
				"SendMessage %s ^rsb changepassword ^wwill change the server's password."\
				% (client['clinum']))
			kwargs['Broadcast'].broadcast(\
				"SendMessage %s ^rsb spec playername ^wwill move a specific player to spec team."\
				 % (client['clinum']))
			kwargs['Broadcast'].broadcast(\
				"SendMessage %s ^rsb swap playername ^wwill move a specific player to another team."\
				 % (client['clinum']))
			
		if modhelp:
			kwargs['Broadcast'].broadcast(\
				"SendMessage %s ^rsb buildspeed amount ^wwill change the build speed."\
				 % (client['clinum']))
			kwargs['Broadcast'].broadcast(\
				"SendMessage %s ^rsb mod gravity amount ^wwill change the gravity."\
				 % (client['clinum']))
			kwargs['Broadcast'].broadcast(\
				"SendMessage %s ^rsb mod jump amount ^wwill change the jump height."\
				 % (client['clinum']))
			kwargs['Broadcast'].broadcast(\
				"SendMessage %s ^rsb mod movespeed amount ^wwill change the movement speed of the server."\
				 % (client['clinum']))

		if mmhelp:
			kwargs['Broadcast'].broadcast(\
				"SendMessage %s ^rmm enable modname ^wwill enable a mod."\
				 % (client['clinum']))
			kwargs['Broadcast'].broadcast(\
				"SendMessage %s ^rsb mm get active ^wwill show all active mods."\
				 % (client['clinum']))
			kwargs['Broadcast'].broadcast(\
				"SendMessage %s ^rsb mm get list ^wwill show all the possible mods."\
				 % (client['clinum']))
			kwargs['Broadcast'].broadcast(\
				"SendMessage %s ^rsb mm reset ^wwill reset everything to its default settings."\
				 % (client['clinum']))		
			
				
		if modenable:
			modName = "./plugins/mods/" + modenable.group(1)
			#if not os.path.isfile(modName):
				#kwargs['Broadcast'].broadcast("SendMessage -1 %s does not exist." % (modenable.group(1)))
			#else:
			with open(modName, 'r') as modfile:
				for line in modfile:
					kwargs['Broadcast'].broadcast("%s" % (line))
			self.modlist.append(modenable.group(1))
			kwargs['Broadcast'].broadcast("SendMessage -1 %s has been enabled." % (modenable.group(1)))
			modfile.close()
					
		if modactive:
			kwargs['Broadcast'].broadcast("SendMessage %s mods currently active on this server:" % (client['clinum']))
			for element in self.modlist:
				kwargs['Broadcast'].broadcast("SendMessage %s %s" % (client['clinum'], element))
		
		if modreset:
			self.modreset()
			kwargs['Broadcast'].broadcast("SendMessage -1 All mods have been reseted.")
			
		if modindirectory:
			modindir = os.listdir("./plugins/mods/")
			for each in modindir:
				kwargs['Broadcast'].broadcast("SendMessage %s %s" % (client['clinum'], each))			
						
	def onPhaseChange(self, *args, **kwargs):
		phase = int(args[0])
		self.PHASE = phase

		if (phase == 7):
			self.banlist = []
			self.modreset()	
			for each in self.playerlist:
				each['team'] = 0
				each['commander'] = False
				
		if (phase == 6):
		#fetch leader list and reload at the start of each game
			try:
				response = urllib2.urlopen('http://cedeqien.com/sandbox.ini')
				leaderlist = response.read()
				leaderfile = os.path.join(os.path.dirname(self.CONFIG),'sandbox.ini')
				f = open(leaderfile, 'w')
				f.write(leaderlist)
				f.close
				#reload the config file		
				self.onPluginLoad(leaderfile)
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