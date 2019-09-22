from .commands import Command
import shlex
from tkinter import *
from tkinter.ttk import *
from tkinter.messagebox import *
from netcrawler import *

class WhatIs(Command):
	def __init__(self, manager):
		super().__init__(manager)
		self.alias = ['what is', 'who is']
		self.runThreaded = True
		self.manager.linkHandlers['duckduckgo.com'] = self.run_link
		
	def run_link(self, link, args, path):
		if args.get('q', None):
			self.run(args['q'])
		
	def run(self, message):
		data = DuckDuckGo().get(message)
		if data['Entity']:
			self.manager.say(f"Here is what I found about the {data['Entity']} {data['Heading']}.\nAccording to {data['AbstractSource']}, {data['AbstractText']}.")
			infobox = data['Infobox'].get('content', [])
			for item in infobox:
				if item['label'] != "Instance of":
					self.manager.printf(f"{item['label']}:", sep=" ", font=['orange'])
					self.manager.printf(item['value'])
			
			if data['Image']:
				self.manager.printf(f"{data['Image']}")
				#self.manager.popupImage(data['Image'])
		else:
			self.manager.getCommand('searchfor').run(message)
class Search(Command):
	def __init__(self, manager):
		super().__init__(manager)
		self.alias = ['search']
		self.check = self.sfcheck
	
	def sfcheck(self, message):
		msgs = shlex.split(message)
		if len(msgs) > 3:
			if msgs[1].lower() in ['ddg', 'duckduckgo', 'sp', 'startpage'] and msgs[2] == "for":
				return True
			
		return False
	
	def run(self, message):
		msgs = shlex.split(message)
		new_engine = msgs[0]
		self.manager.conf._set('search_engine', new_engine)
		search = ' '.join(msgs[2:])
		self.manager.runAsync(self.manager.getCommand('searchfor').run, search)
		
class SearchFor(Command):
	def __init__(self, manager):
		super().__init__(manager)
		self.alias = ['search for']
		self.runThreaded = True
		
	def run(self, message):
		engine = self.manager.conf.get('search_engine', 'ddg')
		
		if engine == "ddg" or engine == "duckduckgo":
			s = DuckDuckGo()
		elif engine == "startpage" or engine == "sp":
			s = Startpage()
		else:
			s = DuckDuckGo()
			
		res = s.search(message)[0]
		self.manager.say(f"According to {res['title']}, {res['description']}")
