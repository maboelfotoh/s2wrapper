# -*- coding: utf-8 -*-

import os
import re
import math
import time
import ConfigParser
from MasterServer import MasterServer
from PluginsManager import ConsolePlugin
from S2Wrapper import Savage2DaemonHandler

#This plugin was written by Old55 and he takes full responsibility for the junk below.
#He does not know python so the goal was to make something functional, not something
#efficient or pretty.


class balancer(ConsolePlugin):

	ms = None
	THRESHOLD = 10
	DIFFERENCE = -1
	TARGET = -1
	GAMESTARTED = 0
	STARTSTAMP = 0
	DENY = 0
	OPTION = 0
	DENOM = 6
	_level = 3
	reason = ("You_must_be_level_%s_to_play_on_this_server" % (_level))
	playerlist = []
	itemlist = []
	teamOne = {'size' : 0, 'avgBF' : -1, 'combinedBF' : 0, 'players' : []}
	teamTwo = {'size' : 0, 'avgBF' : -1, 'combinedBF' : 0, 'players' : []}
	game = {'size' : 0, 'avgBF' : -1}
	switchlist = []

	def onPluginLoad(self, **kwargs):
		self.ms = MasterServer ()

		Config = ConfigParser.ConfigParser ()
		#Config.read ('%s/balancer.ini' % os.path.dirname (os.path.realpath (__file__)))
		#for (name, value) in Config.items ('Restrict'):
		#	if (name == "level"):
		#		self._level = int(value)

		#	if (name == "sf"):
		#		self._sf = int(value)
		
		pass

	def getPlayerByClientNum(self, cli):

		for client in self.playerlist:
			if (client['clinum'] == cli):
				return client

	def getPlayerByName(self, name):

		for client in self.playerlist:
			if (client['name'] == name):
				return client

	def onConnect(self, *args, **kwargs):
		
		id = args[0][0]
		
		for client in self.playerlist:
			if (client['clinum'] == id):
				#added 10/12. If a player DCs and reconnects, they are auto-joined to their old team
				#but there is no team join message. This automatically adds them back to the balancer team list.
				print 'already have entry with that clientnum!'
				team = int(client['team'])
				if (self.GAMESTARTED == 1) and (team > 0):
					teamlists = self.GetTeamLists(client, team)
					toteam = teamlists ['toteam']
					fromteam = teamlists ['fromteam']
					self.addTeamMember(client, fromteam, team, **kwargs)
					return
		self.playerlist.append ({'clinum' : id, 'acctid' : 0, 'level' : 0, 'sf' : 0, 'lf' : 0, 'name' : 'X', 'team' : 0, 'moved' : 0, 'index' : 0, 'exp' : 2, 'value' : 150, 'prevent' : 0})
		

	def onSetName(self, *args, **kwargs):

		print args
		
		cli = args[0][0]
		playername = args[0][1]
		

		client = self.getPlayerByClientNum(cli)

		client ['name'] = playername
		


	def onReceivedAccountId(self, *args, **kwargs):

		doKick = False

		cli = args[0][0]
		id = args[0][1]
		stats = self.ms.getStatistics (id).get ('all_stats').get (int(id))
		
		level = int(stats['level'])
		sf = int(stats['sf'])
		lf = int(stats['lf'])
		exp = int(stats['exp'])

		client = self.getPlayerByClientNum(cli)

		client ['acctid'] = int(id)
		client ['level'] = level
		client ['sf'] = sf
		client ['lf'] = lf
		client ['exp'] += exp
		
		if (level < self._level):
			doKick = True
			
		if (doKick):
			kwargs['Broadcast'].put ("kick %s %s" % (args[0][0], self.reason))
			kwargs['Broadcast'].broadcast ()
		
	def checkForSpectator (self, cli):
		player = self.getPlayerByClientNum(cli)

		if (player['team'] > 0):
			print 'client is changing to spectator!'
			return cli
		else:
			return -1
	
	def getTeamMember (self, item, cli, fromteam):
		
		indice = -1
		
		for player in fromteam['players']:
			
			indice += 1
							
			if (player['clinum'] == cli):
				
				return indice
			
					
	def getPlayerIndex (self, cli):
		
		indice = -1
		for player in self.playlist:
			indice += 1
							
			if (player['clinum'] == cli):
				return indice
			
			
	def removeTeamMember (self, client, fromteam, team, **kwargs):
		print 'Removing player....'
		client ['team'] = team
		cli = client ['clinum']
		item = 'clinum'
		PLAYER_INDICE = self.getTeamMember(item, cli, fromteam)
		fromteam ['size'] -= 1
		fromteam ['combinedBF'] -= fromteam['players'][PLAYER_INDICE]['bf']

		if (fromteam ['size'] <= 0):
			fromteam ['avgBF'] = -1
		else:
			fromteam ['avgBF'] = (fromteam['combinedBF'] / fromteam['size'])

		del fromteam['players'][PLAYER_INDICE]
		
		self.getGameInfo(**kwargs)

	def addTeamMember (self, client, toteam, team, **kwargs):
		
		print 'Adding player....'	
		cli = client['clinum']
		NAME = client['name']
		level = client['level']
		SF = client['sf']
		toteam ['size'] += 1
		#BF = client['sf']
		#LF = (client['lf'] + 20)
		BF = int((client['sf'] * math.log10(client['exp'])/self.DENOM))
		LF = int(((client['lf'] + 10) * math.log10(client['exp'])/self.DENOM))
		moved = client['moved']
		client ['team'] = team
		
		toteam ['combinedBF'] += int(BF)
		toteam ['players'].append ({'clinum' : cli, 'name' : NAME, 'sf' : SF,  'lf' : LF, 'level' : level, 'moved' : moved, 'bf' : BF})
		toteam ['avgBF'] = (toteam['combinedBF'] / toteam['size'])
		
		self.getGameInfo(**kwargs)

	def GetTeamLists (self, client, team):

		currentteam = client ['team']
		
		L = {'toteam' : '0', 'fromteam' : '0'}

		if (int(currentteam) == 1):
			L ['fromteam'] = self.teamOne
			L ['toteam'] = self.teamTwo
			return L
		if (int(currentteam) == 2):
			L ['fromteam'] = self.teamTwo
			L ['toteam'] = self.teamOne
			return L

		if (int(team) == 1):
			L ['toteam'] = self.teamOne
			
		if (int(team) == 2):
			L ['toteam'] = self.teamTwo
			
				
		return L
		#don't think I need this but I am leaving it in
		del L [0]

	def onTeamChange (self, *args, **kwargs):
		
		spec = -1
		team = int(args[0][1])
		cli = args[0][0]
		client = self.getPlayerByClientNum(cli)
		currentteam = client ['team']
		prevented = int(client ['prevent'])
		teamlists = self.GetTeamLists(client, team)
		toteam = teamlists ['toteam']
		fromteam = teamlists ['fromteam']
		
		#check to see if the player is on a team and going to spectator. spec = -1 unless the player is already on a team
		if (int(team) == 0):
			print 'checking for spec'
			spec = self.checkForSpectator(cli)
		#need to have this to avoid having players added multiple times as I have seen happen
		if (spec == -1) and (int(currentteam) == int(team)):
			
			return
		#if the player is switching teams, add them to the new team and remove from the old			
		if (spec == -1) and (int(currentteam) > 0):
			
			self.addTeamMember(client, toteam, team, **kwargs)
			self.removeTeamMember(client, fromteam, team, **kwargs)
		#if the player hasn't joined a team yet, go ahead and add them to the team	
		elif (spec == -1):
			self.addTeamMember(client, toteam, team, **kwargs)
			self.getGameInfo(**kwargs)
			#Players are prevented from joining in the deny phase if they will cause greater than a 15% stack
			#this applies to both even and uneven games. The player is forced back to team 0.
			if (self.DENY == 1):
				self.checkStack(**kwargs)
				print 'deny phase true'
				print self.DIFFERENCE
				if (self.DIFFERENCE > 15):
					action = 'PREVENT'
					self.retrieveIndex(client, action, **kwargs)
					return
				#There may be an issue if the player is forced back to team 0 that they can't join a team
				#even if conditions are met. This just forcibly puts the player on the team they are are trying to join
				#provided the above critera is not true.
				if (prevented == 1):
					print 'allow hit'
					action = 'ALLOW'
					#have to remove them first so we don't duplicate when we force them to join
					team = 0
					#self.removeTeamMember(client, fromteam, team, **kwargs)
					print 'made it past remove'
					self.retrieveIndex(client, action, **kwargs)
					return
		#if the player is going to spec, just remove them from the team
		if (spec > -1):
			self.removeTeamMember(client, fromteam, team, **kwargs)
						
		self.getGameInfo(**kwargs)
						

	def onDisconnect(self, *args, **kwargs):
		
		cli = args[0][0]			
		client = self.getPlayerByClientNum(cli)

		team = client ['team']

		if (int(team) > 0):

			teamlist = self.GetTeamLists(client, team)
			fromteam = teamlist ['fromteam']
			print fromteam
			self.removeTeamMember(client, fromteam, team, **kwargs)

		#self.playerlist.remove (client)
		
		self.sendGameInfo(**kwargs)
		

	def onCommResign(self, *args, **kwargs):
		name = args[0][0]
		
		client = self.getPlayerByName(name)
		team = client['team']
		cli = client['clinum']
		
		teamlist = self.GetTeamLists(client, team)
		fromteam = teamlist ['fromteam']
		item = 'clinum'
		PLAYER_INDICE = self.getTeamMember(item, cli, fromteam)
		
		#fromteam['players'][PLAYER_INDICE]['bf'] = client ['sf']
		fromteam['players'][PLAYER_INDICE]['bf'] = int((client['sf'] * math.log10(client['exp'])/self.DENOM))
		fromteam['players'][PLAYER_INDICE]['moved'] = 0
		
		client ['moved'] = 0	
		
		print fromteam['players'][PLAYER_INDICE]

		self.sendGameInfo(**kwargs)

	def onCommand(self, *args, **kwargs):
		
		cli = args[0][0]
		client = self.getPlayerByClientNum(cli)
		team = client['team']
		teamlist = self.GetTeamLists(client, team)
		fromteam = teamlist ['fromteam']
		item = 'clinum'
		PLAYER_INDICE = self.getTeamMember(item, cli, fromteam)
		
		#fromteam['players'][PLAYER_INDICE]['bf'] = client ['lf']
		fromteam['players'][PLAYER_INDICE]['bf'] = fromteam['players'][PLAYER_INDICE]['lf']
		fromteam['players'][PLAYER_INDICE]['moved'] = 1
		#set moved to 1 to prevent the player from being auto-swapped as commander
		client['moved'] = 1
		
		self.sendGameInfo(**kwargs)

	def onCommandalt(self, *args, **kwargs):
		
		self.onCommand(*args, **kwargs)

	def onPhaseChange(self, *args, **kwargs):
		phase = int(args[0][0])
		print ('Current phase: %d' % (phase))
		if (phase == 7):
			self.onGameEnd()
		if (phase == 5):
			self.onGameStart(*args, **kwargs)
		if (phase == 6):
			self.onNewGame(*args, **kwargs)
		
	def onGameEnd(self, *args, **kwargs):

		print "clearing dictionary...."
		#clear out the team dictionary info and globals when the map is reloaded
		del self.teamOne ['players'][:]
		del self.teamTwo ['players'][:]
		self.teamOne ['size'] = 0
		self.teamOne ['avgBF'] = -1
		self.teamOne ['combinedBF'] = 0
		self.teamTwo ['size'] = 0
		self.teamTwo ['avgBF'] = -1
		self.teamTwo ['combinedBF'] = 0
		self.GAMESTARTED = 0
		self.STARTSTAMP = 0
		self.DENY = 0
		self.OPTION = 0
		#probably don't need this since the info is put in later, but just to be on the safe side
		for player in self.playerlist:
			player ['moved'] = 0
			player ['team'] = 0
			player ['value'] = 150
			player ['prevent']= 0
		
	def onNewGame(self, *args, **kwargs):
		
		print "clearing dictionary...."
		#clear out the team dictionary info and globals when the map is reloaded
		del self.teamOne ['players'][:]
		del self.teamTwo ['players'][:]
		self.teamOne ['size'] = 0
		self.teamOne ['avgBF'] = -1
		self.teamOne ['combinedBF'] = 0
		self.teamTwo ['size'] = 0
		self.teamTwo ['avgBF'] = -1
		self.teamTwo ['combinedBF'] = 0
		self.GAMESTARTED = 0
		self.STARTSTAMP = 0
		self.DENY = 0
		self.OPTION = 0
		#probably don't need this since the info is put in later, but just to be on the safe side
		for player in self.playerlist:
			player ['moved'] = 0
			player ['team'] = 0
			player ['value'] = 150
			player ['prevent']= 0

		self.RegisterScripts(**kwargs)

	def RegisterScripts(self, **kwargs):
		#any extra scripts that need to go in can be done here
		#these are for identifying bought and sold items
		kwargs['Broadcast'].put ("RegisterGlobalScript -1 \"set _client #GetScriptParam(clientid)#; set _item #GetScriptParam(itemname)#; echo ITEM: Client #_client# SOLD #_item#; echo\" sellitem")
		kwargs['Broadcast'].broadcast ()
		kwargs['Broadcast'].put ("RegisterGlobalScript -1 \"set _client #GetScriptParam(clientid)#; set _item #GetScriptParam(itemname)#; echo ITEM: Client #_client# BOUGHT #_item#; echo\" buyitem")
		kwargs['Broadcast'].broadcast ()
		#this makes sure we get an update every minute. This is the startup.cfg default, but just to be sure we put it here as well		
		kwargs['Broadcast'].put ("set sv_statusNotifyTime 60000")
		kwargs['Broadcast'].broadcast ()
		
		#kwargs['Broadcast'].put ("RegisterGlobalScript -1 \"echo calling gamestart...; set _player_count 2000; set _i 0;@start_loop; if [_i == _player_count] goto end; set _idx = 0; set _idx #GetIndexFromClientNum(|#_i|#); set _team #GetTeam(|#_idx|#)#; if #EntityExists(|#_idx|#)# echo CLIENT #_i# on TEAM #_team#; set _i [_i + 1];  goto start_loop;@end; echo\" gamestart")
		#kwargs['Broadcast'].broadcast ()

	def ItemList(self, *args, **kwargs):
		#The item list to get gold values. I had hoped to make this more dynamic, but the server won't return 'Consumable_Advanced_Sights' so it is difficult to get the value
		#directly from game_settings.cfg. Modification to remove appends from winex, 10/12.
		self.itemlist = {
			'Advanced Sights' : 700,
			'Ammo Pack' : 500,
			'Ammo Satchel' : 200,
			'Chainmail' : 300,
			'Gust of Wind' : 450,
			'Magic Amplifier' : 700,
			'Brain of Maliken' : 750,
			'Heart of Maliken' : 950,
			'Lungs of Maliken' : 800,
			'Mana Crystal' : 500,
			'Mana Stone' : 200,
			'Platemail' : 650,
			'Power Absorption' : 350,
			'Shield of Wisdom' : 650,
			'Stone Hide' : 650,
			'Tough Skin' : 300,
			'Trinket of Restoration' : 575,
			}
		
			
	def onItemTransaction(self, *args, **kwargs):
		#adjust 'value' in playerlist to reflect what the player has bought or sold
		cli = args[0][0]
		trans = args[0][1]
		newitem = args[0][2]
		client = self.getPlayerByClientNum(cli)

		try:
			value = self.itemlist[newitem]
		except:
			return

		if (trans == 'BOUGHT'):
			client['value'] += value
		elif (trans == 'SOLD'):
			client['value'] -= value


	def retrieveIndex(self, mover, action, **kwargs):
		#Use this for any manipulations when you need to get the current player index from the server. This is used for MOVE, PREVENT, ALLOW
		cli = mover['clinum']
		client = self.getPlayerByClientNum(cli)
		client ['moved'] = 1
		kwargs['Broadcast'].put ("set _value #GetIndexFromClientNum(%s)#; echo Sv: Client %s index is #_value#. ACTION: %s" % (cli, cli, action))
		kwargs['Broadcast'].broadcast ()

	def onRetrieveIndex(self, *args, **kwargs):
		#get stuff from parser
		clinum = args[0][0]
		index = args[0][1]
		action = args[0][2]
		if (action == 'MOVE'):
			self.move(clinum, index, **kwargs)
		if (action == 'PREVENT'):
			self.prevent(clinum, index, **kwargs)
		if (action == 'ALLOW'):
			self.allow(clinum, index, **kwargs)

	def runBalancer (self, **kwargs):
		#determines if it is even or uneven balancer
		
		diff = self.teamOne['size'] - self.teamTwo['size']
		print diff
		if (diff == 0):
			print 'even balancer'
			self.EvenTeamBalancer(**kwargs)
		#uneven balancer if there is a difference between 1-3. if it more than that, it would be best to restart, but that has not been implemented
		elif (abs(diff) > 0 and abs(diff) < 4):
			print 'uneven balancer'
			self.UnEvenTeamBalancer(**kwargs)
			
		else:
			print "SUGGESTION: RESTART"
			return

	def onGameStart (self, *args, **kwargs):
		
		self.ItemList()
		self.STARTSTAMP = args[0][1]
		self.GAMESTARTED = 1
		kwargs['Broadcast'].put ("echo GAMESTARTED")
		kwargs['Broadcast'].broadcast ()

		self.sendGameInfo(**kwargs)
		#self.runBalancer (**kwargs)
		
		kwargs['Broadcast'].put ("Serverchat ^cIf necessary, the teams will be auto-balanced at 1, 3, and 6 minutes of game time.")
		kwargs['Broadcast'].broadcast ()
		kwargs['Broadcast'].put ("Serverchat ^cAfter 10 minutes, joining will be limited to players that do not generate imbalance.")
		kwargs['Broadcast'].broadcast ()
		kwargs['Broadcast'].put ("Serverchat ^cAt 5 minute increments starting at minute 10, the server will check for imbalance and give players that can improve balance the option to switch")
		kwargs['Broadcast'].broadcast ()
		kwargs['Broadcast'].put ("Serverchat ^cYou will receive a message. Send the message 'switch' to ALL, TEAM, or SQUAD to accept the change.")
		kwargs['Broadcast'].broadcast ()
		self.RegisterScripts(**kwargs)

	#Run balancer at 1, 3 and 6 minutes. Deny phase begins at 8 minutes
	def onServerStatus(self, *args, **kwargs):
		CURRENTSTAMP = int(args[0][1])
		
		TIME = int(CURRENTSTAMP) - int(self.STARTSTAMP)

		if (self.GAMESTARTED == 1):
			if (TIME == (1 * 60 * 1000)):
				self.runBalancer (**kwargs)
			elif (TIME == (3 * 60 * 1000)):
				self.runBalancer (**kwargs)
			elif (TIME == (6 * 60 * 1000)):
				self.runBalancer (**kwargs)
			if (TIME >= (10 * 60 * 1000)):
				self.DENY = 1
				self.OPTION = 1
				del self.switchlist[:]
				if (TIME % (5 * 60 * 1000)) == 0:
					self.runBalancer (**kwargs)

		self.sendGameInfo(**kwargs)

	def evaluateBalance (self, BF, **kwargs):
		#This was written specifically for uneven balancing, but is essentially identical to checkStack, so they could potentially be combined
		large = self.getLargeTeam()
		small = self.getSmallTeam()
		newlargeBF = (float(large ['combinedBF'] - BF) / float(large ['size'] - 1))
		newsmallBF = (float(small ['combinedBF'] + BF) / float(small ['size'] + 1))
		sumavg = newlargeBF + newsmallBF
		largesize = float(large ['size'] - 1.0)
		smallsize = float(small ['size'] + 1.0)
		totalsize = largesize + smallsize
		largepercent = (float(newlargeBF / sumavg) + float(largesize/totalsize))
		smallpercent = float(2.0 - (largepercent))
		ratio = abs(((largepercent - smallpercent) * 100) - self.TARGET)
		#ratio = abs(int((newsmallBF / newlargeBF) * 100) - self.TARGET)
		print newlargeBF, newsmallBF,sumavg, largesize, smallsize, totalsize, largepercent, smallpercent, ratio
		return ratio
 
	def getClosestPersonToTarget (self, team, **kwargs):
		
		lowest = -1
		pick = None
		
		print 'Target is %s' % self.TARGET
		for player1 in team ['players']:

			if (player1['moved'] == 1):
				print 'this player cannot be moved'
				continue

			
			ltarget = self.evaluateBalance (float(player1 ['bf']))
			print ltarget
			if (lowest < 0):
				lowest = ltarget
				# wouldn't work if the first player was the one to pick, so had to do this here
				pick = player1
				continue
			
			if (lowest < ltarget):
				continue
			
			lowest = ltarget
			print 'lowest is %s' % lowest
			pick = player1
		
		print pick

		if (pick == None):
			kwargs['Broadcast'].put ("echo UNEVEN balancer was not happy for some reason I can't figure out")
			kwargs['Broadcast'].broadcast ()
			return

		Large = self.getLargeTeam () 
		Small = self.getSmallTeam ()
		diff = Large['avgBF'] - Small['avgBF']
		LargeBF = (Large['combinedBF'] - pick['bf']) / (Large['size'] - 1)
		SmallBF = (Small['combinedBF'] + pick['bf']) / (Small['size'] + 1) 
		newdiff = abs((SmallBF / LargeBF) - ((Large['size'] - 1) / (Small['size'] + 1)) * 100)
		
		kwargs['Broadcast'].put ("echo UNEVEN balancer selections: Client %s with bf %s for a starting BF stacking of %s to %s" % (pick['clinum'], pick['bf'], self.DIFFERENCE, lowest))
		kwargs['Broadcast'].broadcast ()
		#if the selected option doesn't actually improve anything, terminate
		if (lowest > self.DIFFERENCE):
			print 'nonproductive. terminate'
			kwargs['Broadcast'].put ("echo unproductive UNEVEN balance")
			kwargs['Broadcast'].broadcast ()
			return

		if (self.OPTION == 0):	
			#get the player index and move them
			action = 'MOVE'
			self.retrieveIndex(pick, action, **kwargs)
			return
		
		if (self.OPTION == 1):
			self.switchlist.append ({'name' : pick ['name'], 'clinum' : pick ['clinum'], 'accept' : 0})
			print self.switchlist
			self.giveOption (**kwargs)
		
	def getClosestTwoToTarget (self, team1, team2, **kwargs):
		
		lowest = -1
		pick1 = None
		pick2 = None
		

		for player1 in team1 ['players']:
			if (player1['moved'] == 1):
				print 'this player cannot be moved'
				continue
			for player2 in team2 ['players']:

				if (player2['moved'] == 1):
					print 'this player cannot be moved'
					continue
				
				ltarget = math.fabs (int(player1['bf']) - int(player2['bf']) + int(self.TARGET))
				
				if (lowest < 0):
					lowest = ltarget
					pick1 = player1
					pick2 = player2
					continue
			
				if (lowest < ltarget):
					continue
			
				lowest = ltarget
				pick1 = player1
				pick2 = player2

		
		print pick1, pick2


		diff = math.fabs((team1 ['avgBF']) - (team2 ['avgBF']))
		team1BF = team1['combinedBF'] - pick1['bf'] + pick2['bf']
		team2BF = team2['combinedBF'] - pick2['bf'] + pick1['bf']
		newdiff = math.fabs((team1BF / team1['size']) - (team2BF / team2['size']))
		print diff
		print newdiff
		kwargs['Broadcast'].put ("echo EVEN balancer selections: Clients %s, %s with BF %s, %s for a starting BF difference of %s, ending BF difference %s" % (pick1['clinum'], pick2['clinum'], pick1['bf'], pick2['bf'], diff, newdiff))
		kwargs['Broadcast'].broadcast ()

		if (newdiff >= diff):
			print 'unproductive balance. terminate'
			kwargs['Broadcast'].put ("echo unproductive EVEN balance")
			kwargs['Broadcast'].broadcast ()
			return
		if (self.OPTION == 0):	
			action = 'MOVE'
			self.retrieveIndex(pick1, action, **kwargs)
			self.retrieveIndex(pick2, action, **kwargs)
			return
		if (self.OPTION == 1):
			self.switchlist.append ({'name' : pick1['name'], 'clinum' : pick1['clinum'], 'accept' : 0})
			self.switchlist.append ({'name' : pick2['name'], 'clinum' : pick2['clinum'], 'accept' : 0})
			print self.switchlist
			self.giveOption (**kwargs)
	
	def giveOption(self, **kwargs):
		print self.switchlist
		index = -1
		playermessage = "You have been selected to change teams to promote balance. To accept, send the message 'switch' to ALL, TEAM, or SQUAD. You will be reimbursed for your non-consumable items and your attributes will be reset. If there are an even number of players on each team you will be switched only if both players accept the change. You have one minute to accept."
		for player in self.switchlist:
			index += 1
			kwargs['Broadcast'].put ("SendMessage %s %s" % (player['clinum'], playermessage))
			kwargs['Broadcast'].broadcast ()
			
		if (index == 0):
			kwargs['Broadcast'].put ("ServerChat Teams are currently unbalanced. ^r%s ^yhas been selected to improve balance. Please encourage this player to switch by telling them to send the message 'switch' to ALL or TEAM" % (self.switchlist[0]['name']))
			kwargs['Broadcast'].broadcast ()
		else:
			kwargs['Broadcast'].put ("ServerChat Teams are currently unbalanced. ^r%s ^yand ^r%s ^yhave been selected to improve balance. Please encourage these players to switch by telling them to send the message 'switch' to ALL or TEAM" % (self.switchlist[0]['name'], self.switchlist[1]['name']))
			kwargs['Broadcast'].broadcast ()

	def onMessage (self, *args, **kwargs):
		name = args[0][1]
		message = args[0][2]
		
		if (self.OPTION == 1) and (message == 'switch'):
			for player in self.switchlist:
				if (player['name'] == name):
					print 'player accepted!'
					player ['accept'] = 1
					print self.switchlist
					self.optionCheck(**kwargs)

	def optionCheck(self, **kwargs):
		domove = 1
		print 'checking'
		for player in self.switchlist:
			if (player['accept'] == 0):
				domove = 0

		if (domove == 1):
			print 'doing move!'
			for player in self.switchlist:
				action = 'MOVE'
				self.retrieveIndex(player, action, **kwargs)
			del self.switchlist[:]

	def move(self, clinum, index, **kwargs):
		
		client = self.getPlayerByClientNum(clinum)
		
		client ['moved'] = 1
		name = client ['name']
		#only have to move players that are already on a team, and since they can only go to the other, team we can use this
		if (int(client['team']) == 1):
			newteam = 2		
		else:
			newteam = 1

				
		kwargs['Broadcast'].put ("SetTeam %s %s" % (index, newteam))
		kwargs['Broadcast'].broadcast ()
		
		kwargs['Broadcast'].put ("Serverchat ^r%s ^yhas switched teams to promote balance." % (name))
		kwargs['Broadcast'].broadcast ()

		kwargs['Broadcast'].put ("ResetAttributes %s" % (index))
		kwargs['Broadcast'].broadcast ()
		print 'moving player...'
		
		self.moveNotify(clinum, **kwargs)

	def prevent(self, clinum, index, **kwargs):
		client = self.getPlayerByClientNum(clinum)
		client ['prevent'] = 1		
		newteam = 0
				
		kwargs['Broadcast'].put ("SetTeam %s %s" % (index, newteam))
		kwargs['Broadcast'].broadcast ()
		
		print 'removing player...'
		
		self.preventNotify(clinum, **kwargs)

	def allow(self, clinum, index, **kwargs):
		client = self.getPlayerByClientNum(clinum)		
		team = client ['team']
				
		kwargs['Broadcast'].put ("SetTeam %s %s" % (index, team))
		kwargs['Broadcast'].broadcast ()
		client ['prevent'] = 0
		print 'allowing player...'
		
		
	def moveNotify(self, clinum, **kwargs):
		#this lets the player know the have been moved and compensates them for their purchased items. There is current no way to know
		#how much gold a player holds, though I think gold may actually transfer. Not 100% sure.
		client = self.getPlayerByClientNum(clinum)

		value = client ['value']		

		kwargs['Broadcast'].put ("SendMessage %s You have automatically switched teams to promote balance." % (clinum))
		kwargs['Broadcast'].broadcast ()
		
		kwargs['Broadcast'].put ("SendMessage %s You have been compensated %s gold for your non-consumable items and your attributes have been reset." % (clinum, value))
		kwargs['Broadcast'].broadcast ()

		kwargs['Broadcast'].put ("GiveGold %s %s" % (clinum, value))
		kwargs['Broadcast'].broadcast ()
	
		client ['value'] = 0

	def preventNotify(self, clinum, **kwargs):
		
		kwargs['Broadcast'].put ("SendMessage %s You cannot join that team as it will create imbalance. Please wait for another player to join or leave." % (clinum))
		kwargs['Broadcast'].broadcast ()

	def getSmallTeam (self):
		#writing these all out explicitly because I was having trouble with them
		if (self.teamOne ['size'] < self.teamTwo ['size']):
			return self.teamOne
		if (self.teamTwo ['size'] < self.teamOne ['size']):
			return self.teamTwo
		if (self.teamTwo ['size'] == self.teamOne ['size']):
			return self.teamTwo	

	def getLargeTeam (self):
		#writing these all out explicitly because I was having trouble with them
		if (self.teamOne ['size'] > self.teamTwo ['size']):
			return self.teamOne
		if (self.teamTwo ['size'] > self.teamOne ['size']):
			return self.teamTwo
		if (self.teamTwo ['size'] == self.teamOne ['size']):
			return self.teamOne

	def getHighTeam (self):
		if (self.teamOne ['avgBF'] <= self.teamTwo ['avgBF']):
			return self.teamOne 
		else:
			return self.teamTwo

	def getLowTeam (self):
		if (self.teamOne ['avgBF'] >= self.teamTwo ['avgBF']):
			return self.teamOne 
		else:
			return self.teamTwo

	def getTeamOne (self):
		return self.teamOne

	def getTeamTwo (self):
		return self.teamTwo

	def getTeamAvg (self, team):
		#this updates the info for a team		
		team ['combinedBF'] = 0

		for clients in team ['players']:
			team ['combinedBF'] += clients ['bf']
		if (team ['size'] > 0):
			team ['avgBF'] = (team ['combinedBF'] / team ['size'])

		

	def getGameInfo (self, **kwargs):

		self.getTeamAvg (self.teamOne)
		self.getTeamAvg (self.teamTwo)

		self.game ['size'] = (self.teamOne ['size'] + self.teamTwo ['size'])
		self.game ['avgBF'] = ((self.teamOne ['avgBF'] +  self.teamTwo ['avgBF']) / 2)
		
	def sendGameInfo (self, **kwargs):

		self.getGameInfo(**kwargs)

		if (self.GAMESTARTED == 1):
			self.checkStack(**kwargs)

		kwargs['Broadcast'].put ("Serverchat Current balance: Team 1: ^g%s (%s players), ^yTeam 2: ^g%s (%s players). Stack percentage: %s" % (self.teamOne ['avgBF'], self.teamOne ['size'], self.teamTwo ['avgBF'], self.teamTwo ['size'], round(self.DIFFERENCE, 1) ))
		kwargs['Broadcast'].broadcast ()


	def checkStack(self, **kwargs):
		large = self.getLargeTeam ()
		small = self.getSmallTeam ()
		largeavg = float(large ['avgBF'])
		smallavg = float(small ['avgBF'])
		sumavg = largeavg + smallavg
		largesize = float(large ['size'])
		smallsize = float(small ['size'])
		totalsize = largesize + smallsize
		largepercent = ((largeavg / sumavg) + (largesize/totalsize))
		smallpercent = (2.0 - (largepercent))
		self.DIFFERENCE = abs(largepercent - smallpercent) * 100
		print self.DIFFERENCE
		print largeavg, smallavg,sumavg, largesize, smallsize, totalsize, largepercent, smallpercent, self.DIFFERENCE
	def EvenTeamBalancer(self, **kwargs):
		self.getGameInfo(**kwargs)
		self.THRESHOLD = 10

		self.checkStack()
		absdiff = abs(self.DIFFERENCE)
		if (absdiff > self.THRESHOLD):

			self.TARGET = abs(self.game['avgBF'] * (self.teamOne['size']) - self.teamOne['combinedBF'])
			print self.TARGET
			self.getClosestTwoToTarget (self.getHighTeam (), self.getLowTeam (),  **kwargs)
		else:
			print 'threshold not met'
			kwargs['Broadcast'].put ("Serverchat Even team balancer initiated but current balance ratio of %s does not meet the threshold of %s" % (self.DIFFERENCE, self.THRESHOLD))
			kwargs['Broadcast'].broadcast ()
	def UnEvenTeamBalancer(self, **kwargs):
		self.getGameInfo(**kwargs)
		self.THRESHOLD = 10
		fromteam = self.getLargeTeam ()
		toteam = self.getSmallTeam ()
		self.checkStack()
		absdiff = abs(self.DIFFERENCE)
		print self.DIFFERENCE		
		if (absdiff > self.THRESHOLD): 

			
			#self.TARGET = int(self.game['avgBF'] * (self.getSmallTeam () ['size']) - (self.getSmallTeam () ['combinedBF']))
			#self.TARGET = int(self.game['avgBF']/2)
			#self.TARGET = (float(toteam ['size']) / float(fromteam ['size']) * 100)
			#_IF_ we believe the stack percentage, we really want it to be as low as possible so we just make TARGET = 0
			self.TARGET = 0.00
			self.getClosestPersonToTarget (self.getLargeTeam (), **kwargs)
				
		else:
			print 'threshold not met'
			kwargs['Broadcast'].put ("Serverchat Uneven team balancer initiated, but current balance ratio of %s does not meet the threshold of %s" % (self.DIFFERENCE, self.THRESHOLD))
			kwargs['Broadcast'].broadcast ()
		