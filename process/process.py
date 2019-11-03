from threading import Thread
import time
from tkinter import *
from tkinter.ttk import *
from tkinter.messagebox import *
import os
from PIL import Image, ImageTk
from io import BytesIO
from os.path import expanduser
import requests

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

class TestPanels(AOSProcess):
	def run(self):	
		self.manager.addPanel(VPanel())
		self.manager.addPanel(TPanel())
		
		
	def cleanup(self):
		self.manager.removePanel('testp')
		self.manager.removePanel('volp')
		
class PanelManager(AOSProcess):
	def run(self):
		self.fwindex = 0
		if self.manager.conf.get('autostart_panel', "NOVAR") == "NOVAR":
			self.manager.conf._set('autostart_panel', True)
		
		self.manager.addFileHandler('.jpeg', self.panelImage)
		self.manager.addFileHandler('.jpg', self.panelImage)
		self.manager.addFileHandler('.png', self.panelImage)
		self.manager.addFileHandler('.bmp', self.panelImage)
		
		self.manager.addTool('Toggle Panel', self.togglePanel)
		self.wls = self.manager.getPanels()
		while len(self.wls) == 0:
			self.wls = self.manager.getPanels()
			time.sleep(5)
			
		self.purge()
		self.createPanelInterface()			
		wf = self.wls[self.fwindex]
		wf.create(self.manager.process.panels)
	
	def prepareCustomPanel(self):
		if not self.manager.process.panels.grid_info().get('in', None):
			self.manager.process.panels.grid(row=0, column=11, sticky="nsew", rowspan=6)
		self.purge()
		self.createReturnPanelInterface()
		
	def panelImage(self, *args):
		"""Open image in side panel."""
		url = f"https://{args[0]}{args[2]}"
		
		self.prepareCustomPanel()
		
		headers = {
			'User-Agent':'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:61.0) Gecko/20100101 Firefox/61.0'
		}
		if url.startswith("http"):
			raw_data = requests.get(url, headers=headers).content
			im = Image.open(BytesIO(raw_data))
		else:
			im = Image.open(url)
		
		img = ImageTk.PhotoImage(im)
		l = Label(self.manager.process.panels, image=img)
		l.image = img
		l.grid(row=1, column=0)
		
	def cycleup(self):
		self.purge()
		self.createPanelInterface()
		self.fwindex += 1
		if self.fwindex >= len(self.wls):
			self.fwindex = 0
		
		wf = self.wls[self.fwindex]
		wf.create(self.manager.process.panels)
			
	def cycledown(self):
		self.purge()
		self.createPanelInterface()
		self.fwindex -= 1
		if self.fwindex < 0:
			self.fwindex = (len(self.wls) - 1)
		
		wf = self.wls[self.fwindex]
		wf.create(self.manager.process.panels)
	
	def returnPanel(self):
		self.purge()
		self.createPanelInterface()
		wf = self.wls[self.fwindex]
		wf.create(self.manager.process.panels)	
		
	def createPanelInterface(self):
		mframe = Frame(self.manager.process.panels)
		mframe.grid(row=0, columnspan=10)
		Button(mframe, text="<", command=self.cycledown).grid(row=0, column=0)
		Button(mframe, text=">", command=self.cycleup).grid(row=0, column=1)
		
	def createReturnPanelInterface(self):
		mframe = Frame(self.manager.process.panels)
		mframe.grid(row=0, columnspan=10)
		Button(mframe, text="Close", command=self.returnPanel).grid(row=0, column=0)
		#self.manager.say("Click ||here|| to revert side panel.", link_id="revertpanel", command=lambda evt: self.returnPanel())
		
	def purge(self):
		for item in self.manager.process.panels.winfo_children():
			item.destroy()
			
	def cleanup(self):		
		self.purge()
		self.manager.process.panels.grid(ipady=0, ipadx=0)	
		self.manager.process.win.columnconfigure(11, weight=0)	
		self.manager.removeTool('Toggle Panel')
		
	def togglePanel(self):
		if self.manager.process.panels.grid_info().get('in', None):
			self.manager.process.panels.grid_forget()
		else:
			self.manager.process.panels.grid(row=0, column=11, sticky="nsew", rowspan=5)

class TPanel:
	def __init__(self):
		self.name = "testp"
		
	def create(self, frame):
		self.status_label_name = Label(frame, text="Network Status:")
		self.status_label_name.grid(row=1, column=0)
		
		self.status_label = Label(frame, text="????")
		self.status_label.grid(row=1, column=1)	
		
class VPanel:
	def __init__(self):
		self.name = "volp"
		
	def create(self, frame):
		Label(frame, text="Volume").grid(row=1, column=0, columnspan=3)
		Button(frame, text="0", command=self.volMute).grid(row=2, column=0)
		Button(frame, text="-", command=self.volDown).grid(row=2, column=1)
		Button(frame, text="+", command=self.volUp).grid(row=2, column=2)

	def volUp(self):
		os.system("amixer -D pulse sset Master 10%+")
	def volDown(self):
		os.system("amixer -D pulse sset Master 10%-")
	def volMute(self):
		os.system("amixer -D pulse sset Master 0%")

class NMFooterW:
	def __init__(self):
		self.name = "networkmanager"
		
	def create(self, frame):
		self.status_label_name = Label(frame, text="Network Status:")
		self.status_label_name.grid(row=0, column=0)
		
		self.status_label = Label(frame, text="????")
		self.status_label.grid(row=0, column=1)	
		
class TFooterW:
	def __init__(self):
		self.name = "tester"
		
	def create(self, frame):
		self.status_label_name = Label(frame, text="Test Status:")
		self.status_label_name.grid(row=0, column=0)
		
		self.status_label = Label(frame, text="????")
		self.status_label.grid(row=0, column=1)	
	
class CycleFooters(AOSProcess):
	def run(self):
		self.fwindex = -1
		
		while not self.stopped:
			wls = self.manager.getFooters()
			while len(wls) == 0:
				wls = self.manager.getFooters()
				time.sleep(5)
				
			self.purge()
			#self.manager.process.footers.grid(ipady=2)
			self.fwindex += 1
			if self.fwindex >= len(wls):
				self.fwindex = 0
				
			wf = wls[self.fwindex]
			
			wf.create(self.manager.process.footers)
			time.sleep(self.manager.conf.get('footer_delay', 10))
	
	def purge(self):
		for item in self.manager.process.footers.winfo_children():
			item.destroy()
			
	def cleanup(self):		
		self.purge()
		self.manager.process.footers.grid(ipady=0)	
		self.manager.process.win.rowconfigure(7, weight=1)	
		
class NetworkMonitorFooter(AOSProcess):
	def run(self):	
		self.manager.addFooter(NMFooterW())
		self.manager.addFooter(TFooterW())
		
	def cleanup(self):
		self.manager.removeFooter('networkmanager')
		self.manager.removeFooter('tester')
