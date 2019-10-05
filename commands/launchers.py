from .commands import Command
import shlex
from tkinter import *
from tkinter.ttk import *
from tkinter.messagebox import *
import subprocess
import json
import os

class ApplicationManager:
	def __init__(self, manager):
		self.manager = manager
		self.paths_raw = os.environ['PATH']
		self.paths = self.paths_raw.split(":")
		self.ignored = self.manager.conf._get('bin_ignored_paths')
		if not self.ignored:
			self.manager.conf._set('bin_ignored_paths', [])
			
		for item in self.paths:
			if item in self.ignored:
				self.paths.remove(item)	
	
		self.ailoc = self.manager.conf._get('appimage_location', '')
		
	def getBins(self, path):
		apps = []
		for file in os.listdir(path):
			apps.append(os.fsdecode(file))
			
		return apps
	
	def getAImg(self):
		apps = []
		for file in os.listdir(self.ailoc):
			apps.append(os.fsdecode(file))
			
		return apps
	
class AppsUI(Command):
	def __init__(self, manager):
		super().__init__(manager)
		self.check = self.dontCheck
		self.selected_app = ""
		self.selected_appimg = ""
		self.selected_path = ""
		
	def enable(self):
		self.manager.addTool('Apps', lambda: self.openApps())
		self.manager.addTool('AppImages', lambda: self.openAppImages())
		
	def disable(self):
		self.manager.removeTool('Apps')	
		self.manager.removeTool('AppImages')
	
	def changeAppImgLoc(self, evt=None):
		loc = filedialog.askdirectory()
		self.manager.conf._set('appimage_location', loc)
		self.appimswin.destroy()
		self.openAppImages()
		return loc
	
	def openAppImages(self):
		self.appimswin = Toplevel()
		
		aimg = ApplicationManager(self.manager)
		
		if not aimg.ailoc:
			Label(self.appimswin, text="No appimage location stored. Click the button to browse to the location").grid(row=0, column=0)
			Button(self.appimswin, text="Browse...", command=self.changeAppImgLoc).grid(row=1, column=0, sticky="ns")
			return
		
		self.apps = Listbox(self.appimswin)
		self.apps.grid(column=0, row=0, rowspan=4, sticky="nswe")
		self.manager.addUIScrollbar(self.apps)
		
		for item in ApplicationManager(self.manager).getAImg():
			if item not in self.manager.conf._get('hidden_appimages', []):
				self.apps.insert('end', item)
			
		self.apps.bind('<<ListboxSelect>>', self.onselect_appimg)
		self.appimswin.rowconfigure(0, weight=1)
		self.appimswin.columnconfigure(2, weight=1)
		self.appimswin.columnconfigure(0, weight=1)
		
		Button(self.appimswin, text="Launch", command=self.runAppImg).grid(row=0, column=4, sticky="ns")
		Button(self.appimswin, text="Browse Dir", command=self.browseToAIdir).grid(row=1, column=4, sticky="ns")
		Button(self.appimswin, text="Edit Img", command=self.editAI).grid(row=2, column=4, sticky="ns")
		Button(self.appimswin, text="Unhide...", command=self.unhideAI).grid(row=3, column=4, sticky="ns")
		
	def openApps(self):
		self.appswin = Toplevel()
		self.headers = Listbox(self.appswin)
		
		self.headers.grid(column=0, row=0, rowspan=4, sticky="nswe")
		self.manager.addUIScrollbar(self.headers)
		self.apps = Listbox(self.appswin)
		self.apps.grid(column=2, row=0, rowspan=4, sticky="nswe")
		self.manager.addUIScrollbar(self.apps)
		
		for item in ApplicationManager(self.manager).paths:
			self.headers.insert('end', item)
			
		self.headers.bind('<<ListboxSelect>>', self.onselect)
		self.apps.bind('<<ListboxSelect>>', self.onselect_apps)
		self.appswin.rowconfigure(0, weight=1)
		self.appswin.columnconfigure(2, weight=1)
		self.appswin.columnconfigure(0, weight=1)
		
		Button(self.appswin, text="Launch", command=self.runApp).grid(row=0, column=4, sticky="ns")
		Button(self.appswin, text="Browse To", command=self.browseTo).grid(row=1, column=4, sticky="ns")
		Button(self.appswin, text="Hide Path", command=self.hidePath).grid(row=2, column=4, sticky="ns")
		Button(self.appswin, text="Unhide...", command=self.hidePathManage).grid(row=3, column=4, sticky="ns")
		
	def runApp(self):
		if self.selected_app:
			self.manager.sendCommand(f'run {self.selected_app}')
			
	def runAppImg(self):
		if self.selected_appimg:
			os.system(f'{ApplicationManager(self.manager).ailoc}/{self.selected_appimg}&')
			
	def browseTo(self):
		if self.selected_path:
			os.system(f"xdg-open {self.selected_path}")
			
	def browseToAIdir(self):
		os.system(f"xdg-open {ApplicationManager(self.manager).ailoc}")	
			
	def hidePath(self):
		hidden = self.manager.conf._get('bin_ignored_paths')
		hidden.append(self.selected_path)
		self.manager.conf._set('bin_ignored_paths', hidden)
		self.appswin.destroy()
		self.openApps()

	def editAI(self):
		self.appimswin.destroy()
		self.appimswin = Toplevel()
		self.editen_name = Entry(self.appimswin)
		self.editen_name.insert('end', self.selected_appimg)
		self.editen_name.grid(row=0, column=0)
		Button(self.appimswin, text="Rename", command=self.renameAppImg).grid(row=0, column=1)
		
		Button(self.appimswin, text="Hide", command=self.hideAppImg).grid(row=1, column=1)
	
	def renameAppImg(self):
		new = self.editen_name.get()
		os.system(f'rename {self.selected_appimg} {new}')
		self.appimswin.destroy()
		self.openAppImages()		
		
	def hideAppImg(self):
		hidden = self.manager.conf._get('hidden_appimages', [])
		hidden.append(self.selected_appimg)
		self.manager.conf._set('hidden_appimages', hidden)
		self.appimswin.destroy()
		self.openAppImages()
		
	def unhideAI(self):
		self.appimswin.destroy()
		self.appimswin = Toplevel()
		self.headersa = Listbox(self.appimswin)
		self.headersa.grid(column=0, row=0, rowspan=4, sticky="nswe")
		self.manager.addUIScrollbar(self.headersa)
		
		for item in self.manager.conf._get('hidden_appimages', []):
			self.headersa.insert('end', item)
		self.headersa.bind('<<ListboxSelect>>', self.onselect_unhideai)	
		
	def onselect_unhideai(self, evt):
		w = evt.widget
		selection=w.curselection()
		try:
			cmd = w.get(selection[0])	
			self.selected_path = cmd
			hidden = self.manager.conf._get('hidden_appimages')
			hidden.remove(self.selected_path)
			self.manager.conf._set('hidden_appimages', hidden)
			self.appimswin.destroy()
			self.openAppImages()
		except:
			pass	
		
	def hidePathManage(self):
		self.appswin.destroy()
		self.appswin = Toplevel()
		self.headers = Listbox(self.appswin)
		self.headers.grid(column=0, row=0, rowspan=4, sticky="nswe")
		self.manager.addUIScrollbar(self.headers)
		
		for item in self.manager.conf._get('bin_ignored_paths', []):
			self.headers.insert('end', item)
		self.headers.bind('<<ListboxSelect>>', self.onselect_unhide)	
		
	def onselect_unhide(self, evt):
		w = evt.widget
		selection=w.curselection()
		try:
			cmd = w.get(selection[0])	
			self.selected_path = cmd
			hidden = self.manager.conf._get('bin_ignored_paths')
			hidden.remove(self.selected_path)
			self.manager.conf._set('bin_ignored_paths', hidden)
			self.appswin.destroy()
			self.openApps()
		except:
			pass	
		
	def onselect(self, evt):
		w = evt.widget
		selection=w.curselection()
		try:
			cmd = w.get(selection[0])	
			self.selected_path = cmd
			self.apps.delete('0', 'end')
			ap = ApplicationManager(self.manager)
			for item in ap.getBins(cmd):
				self.apps.insert('end', item)
		except:
			pass	
		
	def onselect_apps(self, evt):
		w = evt.widget
		selection=w.curselection()
		try:
			self.selected_app = w.get(selection[0])	
		except:
			pass	
		
	def onselect_appimg(self, evt):
		w = evt.widget
		selection=w.curselection()
		try:
			self.selected_appimg = w.get(selection[0])	
		except:
			pass			
class LaunchApp(Command):
	def __init__(self, manager):
		super().__init__(manager)
		self.alias = ['launch', 'run']
		self.runThreaded = True
		
	def run(self, message):
		for path in ApplicationManager(self.manager).paths:
			for file in os.listdir(path):
				filename = os.fsdecode(file)
				if filename.startswith(message):
					if self.manager.promptConfirm(f"Run {filename}?"):
						os.system(filename)
