# -*- coding: utf-8 -*-

import os
import re
import configparser
from PluginsManager import ConsolePlugin

class BanList(ConsolePlugin):

	reason = "BANNED! :P"
	bans  = {}
	regex = []

	def onPluginLoad(self, config):
		# clear our static members
		self.bans  = {}
		self.regex = []

		ini = configparser.ConfigParser()
		ini.read(config)
		for (name, value) in ini.items('banlist'):
			if   name == "@reason":
				self.reason = value
			elif name.startswith("@regex"):
				self.regex += [re.compile(value)]
			else:
				self.bans[name] = value

		print("bans : %s" % self.bans)
		print("regex: %s" % self.regex)


	def onSetName(self, *args, **kwargs):
		id   = args[0]
		name = args[1]
		reason = self.reason

		if name in self.bans:
			if self.bans[name]:
				reason = self.bans[name]
			return self.doKick(id, reason, **kwargs)

		for regex in self.regex:
			if regex.match(name):
				return self.doKick(id, reason, **kwargs)

	def doKick(self, id, reason, **kwargs):
		kwargs['Broadcast'].broadcast("kick %s \"%s\"" % (id, reason))
