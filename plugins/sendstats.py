# -*- coding: utf-8 -*-
#22/4/11 - Send stats to both S2G and Salvage servers
import re
import configparser
import _thread
import glob
import os
import shutil
import urllib.request, urllib.parse, urllib.error
import time
import base64
import json
from StatsServers import StatsServers
from MasterServer import MasterServer
from PluginsManager import ConsolePlugin
from S2Wrapper import Savage2DaemonHandler
from urllib.parse import urlencode

class sendstats(ConsolePlugin):
    base = None
    sent = None
    playerlist = []
    login = None
    lpass = None
    broadcast = 0
    serverid = 0
    loaded = False
    sending = False
    def onPluginLoad(self, config):
        self.ms = MasterServer ()
        ini = configparser.ConfigParser()
        ini.read(config)

        for (name, value) in ini.items('paths'):
            if (name == "base"):
                self.base = value
            if (name == "sent"):
                self.sent = value

    def getPlayerByName(self, name):

        client = None

        for client in self.playerlist:
            if (client['name'].lower() == name.lower()):
                return client

    def onPhaseChange(self, *args, **kwargs):
        phase = int(args[0])


        if not self.loaded:
            kwargs['Broadcast'].broadcast("echo SERVERVAR: svr_login is #svr_login#")
            kwargs['Broadcast'].broadcast("echo SERVERVAR: svr_pass is #svr_pass#")
            kwargs['Broadcast'].broadcast("echo SERVERVAR: svr_broadcast is #svr_broadcast#")
            self.loaded = True
        #Everytime we start a game, start a new thread to send all the stats to eaxs' script, and replays to stony
        if (phase == 6):

            uploadthread = _thread.start_new_thread(self.uploadstats, ())
            #eventthread  = thread.start_new_thread(self.uploadevent, ())


    def uploadstats(self):
        print('starting uploadstats')
        self.ss = StatsServers ()
        home  = os.environ['HOME']
        path =     os.path.join(home, self.base)
        sentdir = os.path.join(home, self.sent)

        for infile in glob.glob( os.path.join(home, self.base,'*.stats') ):
            print("Sending stat file: " + infile)
            statstring_raw = open(infile, 'r')
            datastat = statstring_raw.readlines()
            statstring = datastat[1]
            replayname = os.path.splitext(os.path.basename(infile))[0]
            try:
                replaysize = os.path.getsize(os.path.join(home, self.base, replayname+'.s2r'))
            except:
                replaysize = 100000

            statstring_replay = statstring + ("&file_name=%s.s2r&file_size=%s" % (replayname,replaysize))

            try:
                self.ss.s2gstats(statstring_replay)

            except Exception as e:
                print(e.message)
                print('upload failed. no stats sent')
                continue

            try:
                shutil.copy(infile,sentdir)
                os.remove(os.path.join(home, self.base, infile))
            except:
                continue

        #if not self.sending:
            #self.uploadreplay()

    def uploadevent(self):

        self.ss = StatsServers ()
        home  = os.environ['HOME']
        path =     os.path.join(home, self.base)
        sentdir = os.path.join(home, self.sent)

        for infile in glob.glob( os.path.join(home, self.base,'*.event') ):
            match = os.path.splitext(os.path.basename(infile))[0]
            s2pfile = infile
            statstring = open(infile, 'r').read()
            decoded = urllib.parse.quote(statstring)
            stats = ("event%s=%s" % (match,decoded))

            try:
                self.ss.s2pstats(stats)

            except:
                print('upload failed. no stats sent')
                return

            try:
                shutil.copy(infile,sentdir)
                os.remove(os.path.join(home, self.base, infile))
            except:
                continue

    def getServerVar(self, *args, **kwargs):

        var = args[0]

        if var == 'svr_login':
            self.login = args[1]

        if var == 'svr_pass':
            self.lpass = args[1]

        if var == 'svr_broadcast':
            self.broadcast = int(args[1])

        self.ms = MasterServer ()

        if self.broadcast > 0:
            server = self.ms.getServer(self.login, self.lpass, self.broadcast)
            self.serverid = server['svr_id']
            print(self.serverid)

    def uploadreplay(self):
        print('starting uploadreplay')
        self.sending = True
        self.ss = StatsServers ()
        home  = os.environ['HOME']
        sentdir = os.path.join(home, self.sent)
        time.sleep(1)
        for infile in glob.glob( os.path.join(home, self.base,'*.s2r') ):
            print("Sending replay file: " + infile)
            with open(infile, 'rb') as f:
                data = f.read()
                encoded = base64.b64decode(data)

            replay = {'id':infile, 'login':self.login, 'pass':self.lpass, 'content':encoded}
            replayjson = json.dumps(replay)

            try:
                self.ss.replays(replayjson)

            except:
                print('upload failed. replay not sent')
                continue

            print('Sent replay')

            try:
                shutil.copy(infile,sentdir)
                os.remove(os.path.join(home, self.base, infile))
            except:
                continue

        self.sending = False

    def getPlayerByClientNum(self, cli):

        for client in self.playerlist:
            if (client['clinum'] == cli):
                return client

    def onConnect(self, *args, **kwargs):

        id = args[0]
        ip = args[2]

        self.playerlist.append ({'clinum' : id, 'acctid' : 0,'name' : 'X', 'ip' : ip})

    def onSetName(self, *args, **kwargs):

        cli = args[0]
        playername = args[1]

        client = self.getPlayerByClientNum(cli)
        client ['name'] = playername

    def onAccountId(self, *args, **kwargs):
        self.ss = StatsServers ()
        cli = args[0]
        id = args[1]
        client = self.getPlayerByClientNum(cli)
        client ['acctid'] = int(id)
        name = client ['name']
        ip = client['ip']
        server = self.serverid

        playerinfo = ("sync_user=1&username=%s&acc=%s&ip=%s&svr=%s" % (name, id, ip, server))

        #Send info to PS2
        self.ss.salvagestats(playerinfo)

    def onDisconnect(self, *args, **kwargs):

        cli = args[0]
        client = self.getPlayerByClientNum(cli)

        acct = client['acctid']
        name = client['name']
        server = self.serverid

        playerinfo = ("sync_user=2&username=%s&acc=%s&svr=%s" % (name, id, server))
        #Send info to PS2
        self.ss.salvagestats(playerinfo)

    def onListClients(self, *args, **kwargs):
        clinum = args[0]
        name = args[2]
        ip = args[1]

        client = self.getPlayerByName(name)
        if not client:
        #if a player is missing from the list this will put them as an active player
            acct = self.ms.getAccount(name)
            acctid = acct[name]
            self.onConnect(clinum, 0000, ip, 0000, **kwargs)
            self.onSetName(clinum, name, **kwargs)
            self.onAccountId(clinum, acctid, **kwargs)
