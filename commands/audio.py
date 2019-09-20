from tkinter import *
from tkinter import ttk
from tkinter.ttk import *
from tkinter.messagebox import *
import json
from .commands import Command
import os
import psutil
import shlex
import random 

class NowPlaying(Command):
	def __init__(self, manager):
		super().__init__(manager)
		self.alias = ['now playing']
		self.check = self.checkFull
		
	def run(self, message):
		self.manager.say(f"Currently {self.manager.conf.get('now_playing')} is playing.")
		
class Favouriter(Command):
	def __init__(self, manager):
		super().__init__(manager)
		self.alias = ['fave']
		manager.registerConfig('youtube') 
		self.check = self.checkMulti
		
	def run(self, message):
		if message:
			to_add = message
		else:
			to_add = self.manager.conf.get('now_playing', '')
			
			if not to_add:
				self.manager.say("Nothing is playing.")
				return
			
		faves = self.manager.getConfig('youtube').get('faves')
		faves.append(to_add)
		self.manager.getConfig('youtube')._set('faves', faves)
		self.manager.say(f"Saved {to_add}.")
class YTPlayer(Command):
	def __init__(self, manager):
		super().__init__(manager)
		self.alias = ['play']
		manager.registerConfig('youtube') 
		
	def procStop(self, evt=None):
		for p in psutil.process_iter():
			if p.name() == "ffplay":
				self.manager.say("Stopping current track.")
				p.kill()
				self.manager.conf._set('now_playing', '')
				break
	
	def enable(self):
		for p in psutil.process_iter():
			if p.name() == "ffplay":
				self.manager.printf(f"An audio track is playing. Click ||here|| to stop playing.", link_id="stopaudio", command=self.procStop)
				break

		self.manager.addMenuOption('Media Player', 'Youtube Favourites', self.favesUI)
		
	def disable(self):
		self.manager.removeMenuOption('Media Player', 'Youtube Favourites')	
		
	def run(self, message):
		g = " -nodisp"
		if self.manager.conf.get('radio_vis', False):
			g = ""
		

		if message.startswith("http") and "youtube.com" in message:
			self.manager.conf._set('now_playing', message)
			self.procStop()
			os.system(f'youtube-dl -q -o - {message} | ffplay -{g} -autoexit -loglevel quiet&')	
		else:
			f = self.manager.systemInvoke(f'youtube-dl ytsearch:"{message}" --dump-json')
			#print(f)
			sid = json.loads(f)['id']
			name = json.loads(f)['title']
			self.procStop()
			os.system(f'youtube-dl -q -o - http://youtube.com/watch?v={sid} | ffplay -{g} -autoexit -loglevel quiet&')
			self.manager.printf(f"Stream Name: {name}\nURL: http://youtube.com/watch?v={sid}")
			self.manager.printf(f"Click ||here|| to stop playing.", link_id="stopaudio", command=self.procStop)
			self.manager.say(f"Started streaming {name}.")	
			self.manager.conf._set('now_playing', name)
			
	def favesUI(self):
		self.radiowin = Toplevel()
		self.radiowin.geometry("480x220")
		self.radiowin.title("Favourites")
		self.stations = Listbox(self.radiowin)
		self.stations.grid(row=0, column=0, sticky="nswe")
		scroll = self.manager.addUIScrollbar(self.stations)
		faves = self.manager.getConfig('youtube').get('faves')
		for item in faves:
			self.stations.insert('end', item)
		self.stations.bind('<<ListboxSelect>>', self.onselect)	
		self.radiowin.columnconfigure(0, weight=1)
		self.radiowin.rowconfigure(0, weight=1)	
			
	def onselect(self, evt):
		w = evt.widget
		selection=w.curselection()
		try:
			selected = w.get(selection[0])		
			self.fwin = Toplevel()
			ttk.Button(self.fwin, text="Play", command=lambda: self.run(selected)).grid()
			ttk.Button(self.fwin, text="Edit", command=lambda: self.editFave(selected)).grid()
			ttk.Button(self.fwin, text="Delete", command=lambda: self.delFave(selected)).grid()
			
		except Exception as e:
			print(e)
	
	def editFave(self, track):
		self.fwin.destroy()
		self.efwin = Toplevel()
		self.efedit = Entry(self.efwin)
		self.efedit.grid()
		ttk.Button(self.efedit, text="Edit", command=lambda: self.commitEditFave(track)).grid(column=1)
	
	def commitEditFave(self, track):
		new = self.efedit.get()
		old = track
		self.delFave(track)
		faves = self.manager.getConfig('youtube').get('faves')
		faves.append(new)
		self.manager.getConfig('youtube')._set('faves', faves)
		self.efwin.destroy()
		
	def delFave(self, track):
		self.fwin.destroy()
		faves = self.manager.getConfig('youtube').get('faves')
		faves.remove(track)
		self.manager.getConfig('youtube')._set('faves', faves)	
		
class RadioPlayer(Command):
	def __init__(self, manager):
		super().__init__(manager)
		manager.registerConfig('radio') 
		self.alias = ['play radio']
		self.check = self.checkMulti
		self.selected_station = None
	
	def run(self, message):
		if not message:
			self.stationsUI()
			return
		for item in self.manager.getConfig('radio').get():
			station = self.manager.getConfig('radio')[item]
			if message.lower() in station['name'].lower():
				self.procStop()
				self.selected_station = station
				self.procPlay()
				break
			
	def enable(self):
		self.manager.addMenuOption('Media Player', 'Internet Radio', self.stationsUI)
		
	def disable(self):
		self.manager.removeMenuOption('Media Player', 'Internet Radio')	

	def stationsUI(self):
		self.radiowin = Toplevel()
		self.radiowin.geometry("480x220")
		self.radiowin.title("Radio")
		self.stations = Listbox(self.radiowin)
		self.stations.grid(row=0, column=0, rowspan=5, sticky="nswe")
		scroll = self.manager.addUIScrollbar(self.stations)
		self.stations.bind('<<ListboxSelect>>', self.onselect)	
		for item in self.manager.getConfig('radio').get():
			station = self.manager.getConfig('radio')[item]
			self.stations.insert('end', station['name'])
			
		self.radiowin.columnconfigure(0, weight=1)
			
		for i in range(0, 5):
			self.radiowin.rowconfigure(i, weight=1)		
			
		self.playbutton = ttk.Button(self.radiowin, text="Play", command=self.playStation)
		self.playbutton.grid(row=0, column=2, sticky="ns")
		self.stopbutton = ttk.Button(self.radiowin, text="Stop", command=self.stopStation)
		self.stopbutton.grid(row=1, column=2, sticky="ns")
		self.addbutton = ttk.Button(self.radiowin, text="Add", command=self.addStation)
		self.addbutton.grid(row=2, column=2, sticky="ns")
		self.deletestation = ttk.Button(self.radiowin, text="Delete", command=self.deleteStation)
		self.deletestation.grid(row=3, column=2, sticky="ns")
		self.editstation = ttk.Button(self.radiowin, text="Edit", command=self.editStation)
		self.editstation.grid(row=4, column=2, sticky="ns")
		for p in psutil.process_iter():
			if p.name() == "ffplay":
				self.playbutton.configure(state='disabled')
				self.stopbutton.configure(state='normal')
				return
			
		self.playbutton.configure(state='normal')
		self.stopbutton.configure(state='disabled')
		
	def playStation(self):
		self.stopStation()
		
		self.procPlay()
		self.playbutton.configure(state='disabled')
		self.stopbutton.configure(state='normal')
		
	def stopStation(self):
		self.procStop()
		self.stopbutton.configure(state='disabled')
		self.playbutton.configure(state='normal')
	
	def procPlay(self):
		g = " -nodisp"
		if self.manager.conf.get('radio_vis', False):
			g = ""
		
		track = self.selected_station['url']
		self.manager.say(f"Playing {self.selected_station['name']}")
		os.system(f'ffplay "{track}"{g} -autoexit -loglevel quiet&')
		self.manager.conf._set('now_playing', self.selected_station['name'])
		
	def procStop(self):
		for p in psutil.process_iter():
			if p.name() == "ffplay":
				self.manager.say("Stopping current track.")
				p.kill()
				self.manager.conf._set('now_playing', '')
				break
			
	def addStation(self):
		self.selected_station = None
		self.editStation()
		
	def deleteStation(self):
		for item in self.manager.getConfig('radio').get():
			if self.manager.getConfig('radio').get()[item] == self.selected_station:
				station = self.manager.getConfig('radio')[item]
				if self.manager.promptConfirm(f"Really delete {item}: {station['name']}, {station['url']}. `{station['description']}`"):
					ls = self.manager.getConfig('radio').get()
					del ls[item]
					self.manager.getConfig('radio').data = ls
					self.manager.getConfig('radio').save()
					self.radiowin.destroy()
					self.stationsUI()
					break
				
	def editStation(self):
		self.editui = Toplevel()
		self.editui.title("New station")
		
		Label(self.editui, text="Name").grid(row=0, column=0)
		Label(self.editui, text="Description").grid(row=1, column=0)
		Label(self.editui, text="URL").grid(row=2, column=0)
		
		self.nameentry = Entry(self.editui)
		self.nameentry.grid(row=0, column=1, sticky="we")
		self.identry = Entry(self.editui)
		self.identry.grid(row=1, column=1, sticky="we")
		self.urlentry = Entry(self.editui)
		self.urlentry.grid(row=2, column=1, sticky="we")
		self.tagentry = Entry(self.editui)
		self.tagentry.grid(row=3, column=1, sticky="we")
		ttk.Button(self.editui, text="Save", command=self.saveStation).grid(row=3, column=0)
		
		self.editui.columnconfigure(1, weight=1)
			
		for i in range(0, 3):
			self.editui.rowconfigure(i, weight=1)	
			
		if self.selected_station:
			self.editui.title(self.selected_station['name'])
			self.identry.insert('0', self.selected_station['description'])
			self.nameentry.insert('0', self.selected_station['name'])
			self.urlentry.insert('0', self.selected_station['url'])
			for item in self.manager.getConfig('radio').get():
				if self.manager.getConfig('radio').get()[item] == self.selected_station:
					self.tagentry.insert('0', item)
					break

	def saveStation(self):
		data = {'name': self.nameentry.get(), 'description': self.identry.get(), 'url': self.urlentry.get()}
		ls = self.manager.getConfig('radio').get()
		ls[self.tagentry.get()] = data
		self.manager.getConfig('radio').data = ls
		self.manager.getConfig('radio').save()
		self.radiowin.destroy()
		self.editui.destroy()
		self.stationsUI()	
	
	def onselect(self, evt):
		w = evt.widget
		selection=w.curselection()
		try:
			selected = w.get(selection[0])		
			for item in self.manager.getConfig('radio').get():
				station = self.manager.getConfig('radio')[item]
				#print(station)
				if station['name'] == selected:
					self.selected_station = station
					break
		except Exception as e:
			print(e)
			
