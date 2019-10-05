from threading import Thread
import time
from tkinter import *
from tkinter.ttk import *
from tkinter.messagebox import *
from os.path import expanduser

class AOSProcess(Thread):
	def __init__(self, manager):
		super().__init__()
		self.manager = manager
		self.daemon = True
		self.stopped = False
		
	def cleanup(self):
		pass
		
	def stop(self):
		self.stopped = True	
		self.cleanup()
		
	def run(self):		
		pass

class DownloadManagerWget(AOSProcess):
	def run(self):	
		if not self.manager.downloadManager:
			self.manager.downloadManager = self.download
		
	def cleanup(self):		
		if self.manager.downloadManager == self.download:
			self.manager.downloadManager = None
	
	def download(self, url):
		home = f"{expanduser('~')}/Downloads"
		self.manager.systemCall(f'wget {url} -P {home}')
		
class NetworkMonitorFooter(AOSProcess):
	def run(self):	
		self.manager.process.footers.grid(ipady=20)
		self.status_label_name = Label(self.manager.process.footers, text="Network Status:")
		self.status_label_name.grid(row=0, column=0)
		
		self.status_label = Label(self.manager.process.footers, text="????")
		self.status_label.grid(row=0, column=1)
		
	def cleanup(self):		
		self.status_label_name.destroy()
		self.status_label.destroy()
		
		if len(self.manager.process.footers.winfo_children()) == 0:
			self.manager.process.footers.grid(ipady=0)
