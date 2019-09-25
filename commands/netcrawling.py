from .commands import Command
import shlex
from tkinter import *
from tkinter.ttk import *
from tkinter.messagebox import *
from netcrawler import *

class WikiTools(Command):
	def __init__(self, manager):
		super().__init__(manager)
		self.check = self.dontCheck
		
	def enable(self):
		self.manager.addMenuOption('Wikipedia', 'Todays Featured Article', self.getTodayFeat)
		self.manager.addMenuOption('Wikipedia', 'On this day', self.getOnThisDay)
		
	def disable(self):
		self.manager.removeMenuOption('Wikipedia', 'Todays Featured Article')	
		self.manager.removeMenuOption('Wikipedia', 'On this day')
		
	def getTodayFeat(self):
		data = Wiki().page('')
		self.manager.say(data["From today's featured article"][0])
		
	def getOnThisDay(self):
		data = Wiki().page('')
		self.manager.say(data["On this day"][0])
		
class WikiSearch(Command):
	def __init__(self, manager):
		super().__init__(manager)
		self.alias = ['search wikipedia for']
		self.runThreaded = True
		self.manager.addLinkHandler('wikipedia.org', self.run_wlink)
		self.manager.addLinkHandler('en.wikipedia.org', self.run_wlink)

	def run_wlink(self, link, args, path):
		"""Open in WikiUI"""
		self.runui(path.split("/wiki/")[1])
	
	def run(self, message):
		res = Wiki().openSearch(message)
		key = list(res.keys())[0]
		lim = 5
		if lim > len(res.keys()):
			lim = len(res.keys())
			
		count = 0
		for item in list(res.keys()):
			if count == 0:
				self.manager.say(res[item]['value'])
			else:
				self.manager.printf(res[item]['value'])
			self.manager.printf(f"Open in UI: {res[item]['url']}")
			
			count += 1
			if count > lim:
				break
			
	def runui(self, msg):
		self.data = Wiki().page(msg)
		self.wikiwin = Toplevel()
		self.headers = Listbox(self.wikiwin)
		
		self.headers.grid(column=0, row=0, sticky="nswe")
		self.manager.addUIScrollbar(self.headers)
		self.body = Text(self.wikiwin)
		self.body.grid(column=2, row=0, sticky="nswe")
		self.manager.addUIScrollbar(self.body)
		
		for item in self.data:
			if len(self.data[item]) > 0:
				self.headers.insert('end', item)
			
		self.headers.bind('<<ListboxSelect>>', self.onselect)
		
		self.wikiwin.rowconfigure(0, weight=1)
		self.wikiwin.columnconfigure(2, weight=1)
		self.wikiwin.columnconfigure(0, weight=1)

	def onselect(self, evt):
		w = evt.widget
		selection=w.curselection()
		try:
			cmd = w.get(selection[0])	
			self.body.delete('1.0', 'end')
			for item in self.data[cmd]:
				self.body.insert('end', item)
		except:
			pass	
		
class ShowResults(Command):
	def __init__(self, manager):
		super().__init__(manager)
		self.alias = ['show results for']
		self.runThreaded = True
		self.manager.addLinkHandler('startpage.com', self.run_result_link_s)
		self.manager.addLinkHandler('duckduckgo.com', self.run_result_link_d)
		
	def run_result_link_s(self, link, args, path):
		"""Show listings from Startpage"""
		if args.get('query', None):
			self.run(args['query'])
			
	def run_result_link_d(self, link, args, path):
		"""Show listings from DuckDuckGo"""
		if args.get('q', None):
			self.run(args['q'])	
			
	def run(self, message):
		self.manager.say(f"One moment.")
		
		if shlex.split(message)[-2].lower() == "from":
			engine = shlex.split(message)[-1]
		else:
			engine = self.manager.conf.get('search_engine', 'ddg')
		if engine == "ddg" or engine == "duckduckgo":
			s = DuckDuckGo()
			s_eng_str = "DuckDuckGo"
		elif engine == "startpage" or engine == "sp":
			s = Startpage()
			s_eng_str = "Startpage"
		else:
			s = DuckDuckGo()
			s_eng_str = "DuckDuckGo"
			
		res = s.search(message)
		self.manager.say(f"Here are some results from {s_eng_str}.")
		for item in res:
			self.manager.printf("", timestamp = False)
			self.manager.printf(item['title'], font=['orange'], timestamp = False)
			self.manager.printf(item['description'], timestamp = False)
			if item['url'].startswith('http'):
				self.manager.printf(f"Source: {item['url']}", timestamp = False)	
			else:
				self.manager.printf(f"Source: https://{item['url']}", timestamp = False)
		
class WhatIs(Command):
	def __init__(self, manager):
		super().__init__(manager)
		self.alias = ['what is', 'who is']
		self.runThreaded = True
		#self.manager.linkHandlers['duckduckgo.com'] = self.run_link
		self.manager.addLinkHandler('duckduckgo.com', self.run_link)
		
	def run_link(self, link, args, path):
		"""Show specific information about the query."""
		
		if args.get('q', None):
			self.run(args['q'])
		
	def run(self, message):
		self.manager.say(f"One moment.")
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
		#self.manager.linkHandlers['startpage.com'] = self.run_link
		self.manager.addLinkHandler('startpage.com', self.run_links)
		self.manager.addLinkHandler('duckduckgo.com', self.run_linkd)
		
	def run_links(self, link, args, path):
		"""Search Startpage"""
		if args.get('query', None):
			self.run(args['query'])
			
	def run_linkd(self, link, args, path):
		"""Search DuckDuckGo"""
		if args.get('q', None):
			self.run(args['q'])	
			
	def run(self, message):
		self.manager.say(f"One moment.")
		engine = self.manager.conf.get('search_engine', 'ddg')
		
		if engine == "ddg" or engine == "duckduckgo":
			s = DuckDuckGo()
		elif engine == "startpage" or engine == "sp":
			s = Startpage()
		else:
			s = DuckDuckGo()
			
		res = s.search(message)[0]
		self.manager.say(f"According to {res['title']}, {res['description']}")
		if res['url'].startswith('http'):
			self.manager.printf(f"Source: {res['url']}", timestamp = False)	
		else:
			self.manager.printf(f"Source: https://{res['url']}", timestamp = False)
