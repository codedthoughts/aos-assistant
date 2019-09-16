from threading import Thread
import time
from tkinter import *
from tkinter import ttk
from tkinter.ttk import *
from tkinter.messagebox import *
import memory
from commands.commands import Command
from process.process import AOSProcess
import os
import importlib
import inspect
import sys
import arrow
import copy

class OutputWindow:
	def __init__(self, master_window=None, *, title="Message", text="", geometry="280x240", font=[], size=8, bg='white', format_links_html=False):
		if master_window:
			self.frame = Frame(master_window)
			self.master = self.frame
		else:
			self.master = Toplevel()
			self.master.geometry(geometry)
			self.master.title(title)
			
		S = Scrollbar(self.master)
		S.pack(side=RIGHT, fill=BOTH)
		self.textbox = Text(self.master, height=20, width=70)
		self.textbox.pack(side=LEFT, fill=BOTH, expand=YES)
		S.config(command=self.textbox.yview)
		self.textbox.config(yscrollcommand=S.set)	
		
		
		#master.mainloop()

		self.textbox.tag_configure('red', foreground='red')
		self.textbox.tag_configure('white', foreground='white')
		self.textbox.tag_configure('yellow', foreground='yellow')
		self.textbox.tag_configure('green', foreground='green')
		self.textbox.tag_configure('orange', foreground='orange')
		self.textbox.tag_configure('grey', foreground='grey')
		self.textbox.tag_configure('gray', foreground='grey')
		self.textbox.tag_configure('bold', font=('bold'))
		self.textbox.tag_configure('italics', font=('italics'))
		self.textbox.tag_configure('size', font=(size))
		self.textbox.configure(bg=bg)
		self.textbox.insert('end', text, font)
		self.textbox.config(state="disabled")
	
	def delete(self, index, end_index):
		self.textbox.config(state="normal")
		self.textbox.delete(index, end_index)
		self.textbox.config(state="disabled")
		
	def insert(self, text, *, font=[], size=8, command=None, sep="\n", link_id = "", index='end', timestamp=True):
		self.textbox.config(state="normal")
		#print(f"Inserting `{text}` at `{index}`")
		#print(command)
		#print(link_id)
		if command:
			if link_id == "":
				raise AttributeError("If command is specified, you must give the link a unique ID usin the `link_id` argument.")
			self.textbox.tag_configure(link_id, foreground="blue", underline=1)
			self.textbox.tag_bind(link_id, "<Enter>", self._enter)
			self.textbox.tag_bind(link_id, "<Leave>", self._leave)
			self.textbox.tag_bind(link_id, "<Button-1>", command)
			self.textbox.insert(index, text+sep, link_id)
			self.textbox.config(state="disabled")
			return
		
		if timestamp:
			text = f"{arrow.now().format('HH:mm:ss')}: {text}"
		self.textbox.insert(index, f"{text}{sep}", font)
		self.textbox.see("end")
		self.textbox.config(state="disabled")
	
	def _enter(self, event):
		self.textbox.config(cursor="hand2")

	def _leave(self, event):
		self.textbox.config(cursor="")

	def _click(self, event):
		print(event.widget)

class Manager(Thread):
	def run(self):	
		self.conf = memory.Memory()
		self.scriptdir = os.path.dirname(os.path.realpath(__file__))+"/"
		self.process = AssistantWindow(self)
		self.process.start()
		self.commands = {}
		self.processes = {}
		self.modules = {'commands': [], 'processes': []}
		self.waitFor = None
		self.fallback = None
		self.exmenus = {}
		self.exmenuentries = {}
		
	def addMenuOption(self, entry, name, call, menu=None):
		m = menu or self.process.extramenu
		if not self.exmenus.get(entry, None):
			menu = Menu(m)
			m.add_cascade(label=entry, menu=menu)
			self.exmenus[entry] = menu
			self.exmenuentries[entry] = 0
			
		self.exmenus[entry].add_command(label=name, command=call)
		self.exmenuentries[entry] += 1
		print(self.exmenus)
		
	def removeMenuOption(self, entry, name, menu=None):
		m = menu or self.process.extramenu
		if not self.exmenus.get(entry, None):
			return
		
		self.exmenus[entry].delete(self.exmenus[entry].index(name))
		self.exmenuentries[entry] -= 1
		if self.exmenuentries[entry] == 0:
			m.delete(m.index(entry))
			del self.exmenus[entry]
			del self.exmenuentries[entry]
		#self.deleteMenu(name)
		
	def makeNewMenu(self, name):
		try:
			return self.process.menu.index(name)
		except:
			if not self.getMenu(name):
				menu = Menu(self.process.menu)
				self.process.menu.add_cascade(label=name, menu=menu)
				return menu
			return self.getMenu(name)
		
	def deleteMenu(self, name):
		self.process.menu.delete(self.process.menu.index(name))
		
	def promptConfirm(self, message):
		return askokcancel("Confirm", message)
	
	def say(self, text):
		if not self.conf._get('tts'):
			self.printf(text, tag="say-notts")
			return
		else:
			self.printf(text, tag="say")
		
		text = text.replace('"', "'") 
		#Preventing the console command breaking if the user inputs quote marks, since the .system will think THEIR quote marks are ending the ones this script uses, and means any other text in the input will be, at best ignored, at worst flite will try and translate them in to command args, which could result in random file dumping and other weird interactions
		os.system(f'padsp flite -voice file://{self.scriptdir}cmu_us_clb.flitevox -t "{text}" &')		
	
	def takeInput(self, cmd):
		self.waitFor = cmd
		self.process.addPromtCanceller(cmd)
	def clearInput(self):
		self.waitFor = None
		self.process.endPromptCanceller()
	
	def printf(self, message, **kargs):
		if kargs.get('tag') == 'debug' and not self.conf._get('debug'):
			return
		
		if kargs.get('tag') == 'say':
			self.process.log.insert(f"[ ATHENA ] {message}")
		elif kargs.get('tag') == 'say-notts':
			self.process.log.insert(f"[ QUIET ] {message}")	
		else:
			self.process.log.insert(f"{message}")	
			
	def initCacheProcess(self):
		off_modules = self.conf._get('disabled_modules')
		off_processes = self.conf._get('disabled_process')
		self.printf("Getting Process modules...", tag='info')
		for file in os.listdir(self.scriptdir+"process/"):
			filename = os.fsdecode(file)
			if filename.endswith(".py"):
				modname = filename.split(".")[0]
				if f"process.{modname}" not in off_modules:
					self.printf(f"Loading process module: {modname}", tag='debug')
					importlib.import_module("process."+modname)
					clsmembers = inspect.getmembers(sys.modules["process."+modname], inspect.isclass)
					for com in clsmembers:
						print(com[1].__name__)
						if issubclass(com[1], AOSProcess) and com[1] != AOSProcess:
							self.printf(f"Validated {com[1].__name__}", tag='debug')
							self.processes[com[0].lower()] = com[1](self)
							self.processes[com[0].lower()].daemon = True
							
							if com[1].__name__.lower() not in off_processes:
								self.processes[com[0].lower()].start()
								self.printf(f"Started process {com[1].__name__}", tag='debug')
								
							if modname not in self.modules['processes']:
								self.modules['processes'].append(modname)
								self.printf(f"Registered module {modname}")
				else:
					self.printf(f"Not loading {modname}", tag='debug')

	def initCacheCommands(self):
		try:
			if not self.process.log:
				time.sleep(1)
				self.initCacheCommands()
				return
		except:
			time.sleep(1)
			self.initCacheCommands()
			return
			
		off_modules = self.conf._get('disabled_modules')
		off_commands = self.conf._get('disabled_commands')
		self.printf("Getting Command modules...", tag='info')
		for file in os.listdir(self.scriptdir+"commands/"):
			filename = os.fsdecode(file)
			if filename.endswith(".py"):
				modname = filename.split(".")[0]
				if f"commands.{modname}" not in off_modules:
					self.printf(f"Loading command module: {modname}", tag='debug')
					importlib.import_module("commands."+modname)
					clsmembers = inspect.getmembers(sys.modules["commands."+modname], inspect.isclass)
					for com in clsmembers:
						if issubclass(com[1], Command) and com[1] != Command:
							self.printf(f"Validated {com[1].__name__}", tag='debug')
							self.commands[com[0].lower()] = com[1](self)
							if com[1].__name__.lower() not in off_commands:
								self.commands[com[0].lower()].enable()
							if modname not in self.modules['commands']:
								self.modules['commands'].append(modname)
								self.printf(f"Registered module {modname}", tag='debug')
							
							if com[1].__name__.lower() == self.conf._get('fallback', ''):
								self.fallback = self.commands[com[0].lower()]
				else:
					self.printf(f"Not loading {modname}", tag='debug')
		
class AssistantWindow(Thread):
	def __init__(self, manager):
		super().__init__()
		self.manager = manager
		
	def run(self):
		self.win = Tk()
		self.win.title("AthenaOS Interface")
		self.win.protocol("WM_DELETE_WINDOW", lambda: quit())
		self.win.geometry("640x240")
		self.log = OutputWindow(self.win)
		self.log.master.grid(row=0, column=0, columnspan=5, rowspan=5, sticky="nswe")
		self.inputbar = Entry(self.win)
		self.inputbar.grid(row=6, columnspan=4, sticky="ew")
		self.inputbar.focus()
		def select_all(widget):
			self.inputbar.select_range(0, 'end')
			self.inputbar.icursor('end')
    
		self.inputbar.bind('<Control-KeyRelease-a>', select_all)	
		
		self.inputButton = ttk.Button(self.win, text="Send", width=5, command=self.sendMsg).grid(row=6, column=4, columnspan=2)
		self.inputbar.bind('<Return>', self.sendMsg)
		
		for i in range(0, 4):
			self.win.columnconfigure(i, weight=1)
			
		for i in range(0, 5):
			self.win.rowconfigure(i, weight=1)	
			
		self.log.frame.columnconfigure(0, weight=1)
		self.log.frame.rowconfigure(0, weight=1)
	
	
		self.menu = Menu(self.win)
		self.win.config(menu=self.menu)
		self.filemenu = Menu(self.menu)
		self.helpmenu = Menu(self.menu)
		self.extramenu = Menu(self.menu)
		self.filemenu.add_command(label="Modules", command=self.conf_modules)
		self.filemenu.add_command(label="Commands", command=self.conf_commands)
		self.filemenu.add_command(label="Processes", command=self.conf_processes)
		self.helpmenu.add_command(label="About", command=self.about)
		self.menu.add_cascade(label="File", menu=self.filemenu)
		self.menu.add_cascade(label="Extra", menu=self.extramenu)
		self.menu.add_cascade(label="Help", menu=self.helpmenu)
		#print(f"Test: {self.menu.nametowidget('File')}")
		self.win.mainloop()
	
	def addPromtCanceller(self, cmd):
		self.promptmenu = Menu(self.menu)
		self.promptmenu.add_command(label=f"Cancel {type(cmd).__name__}", command=self.manager.clearInput)
		self.menu.add_cascade(label="Prompt", menu=self.promptmenu)
		
	def endPromptCanceller(self):
		self.manager.printf("Cancelling current prompt.")
		self.menu.delete(self.menu.index('Prompt'))
		
	def conf_modules(self):
		self.modules = Toplevel()
		self.modules.transient(self.win)
		self.modules.title("Modules")
		
		cmds = Listbox(self.modules)
		cmds.grid(row=0, column=0, columnspan=2, sticky="nswe")
		logWinScroll = Scrollbar(self.modules)
		logWinScroll.grid(column=2, row=0, sticky="ns")
		logWinScroll.config(command=cmds.yview)
		cmds.config(yscrollcommand=logWinScroll.set)
		cmds.bind('<<ListboxSelect>>', self.onselect_modules)	
		i = 0
		for item in self.manager.modules['commands']:
			cmds.insert('end', f"commands.{item}")	
			if item in self.manager.conf.get('disabled_modules'):
				cmds.itemconfig(i, {'bg':'grey', 'fg': 'white'})
			i += 1
			
		for item in self.manager.modules['processes']:
			cmds.insert('end', f"process.{item}")	
			if item in self.manager.conf.get('disabled_modules'):
				cmds.itemconfig(i, {'bg':'grey', 'fg': 'white'})
			i += 1
			
		for item in self.manager.conf.get('disabled_modules', []):
			cmds.insert('end', item)	
			cmds.itemconfig(i, {'bg':'grey', 'fg': 'white'})
			i += 1	
			
		for i in range(0, 2):
			self.modules.columnconfigure(i, weight=1)	
			
		for i in range(0, 1):
			self.modules.rowconfigure(0, weight=1)	
			
	def onselect_modules(self, evt):
		w = evt.widget
		selection=w.curselection()
		try:
			cmd = w.get(selection[0])	
			ls = self.manager.conf.get('disabled_modules', [])
			if cmd in ls:
				ls.remove(cmd)
			else:
				ls.append(cmd)
					
			self.manager.conf._set('disabled_modules', ls)
			self.modules.destroy()
			for item in copy.copy(self.manager.processes):
				self.manager.processes[item].stop()
				
			self.manager.commands = {}
			self.manager.processes = {}
			self.manager.modules = {'commands': [], 'processes': []}
			self.manager.initCacheCommands()
			self.manager.initCacheProcess()
			self.conf_modules()
		except IndexError:
			pass	
		
	def conf_processes(self):
		self.processes = Toplevel()
		self.processes.transient(self.win)
		self.processes.title("Processes")
		
		cmds = Listbox(self.processes)
		cmds.grid(row=0, column=0, columnspan=2, sticky="nswe")
		logWinScroll = Scrollbar(self.processes)
		logWinScroll.grid(column=2, row=0, sticky="ns")
		logWinScroll.config(command=cmds.yview)
		cmds.config(yscrollcommand=logWinScroll.set)
		cmds.bind('<<ListboxSelect>>', self.onselect_processes)	
		i = 0
		for item in self.manager.processes:
			filename = inspect.getfile(self.manager.processes[item].__class__).split("/")[-1].split(".")[0]
			cmds.insert('end', f"{filename}.{item}")
			if item in self.manager.conf.get('disabled_process'):
				cmds.itemconfig(i, {'bg':'grey', 'fg': 'white'})
			i += 1
			
		for i in range(0, 2):
			self.processes.columnconfigure(i, weight=1)	
			
		for i in range(0, 1):
			self.processes.rowconfigure(0, weight=1)	

	def onselect_processes(self, evt):
		w = evt.widget
		selection=w.curselection()
		try:
			cmd = w.get(selection[0])	
			cmd = cmd.split(".")[1]
			ls = self.manager.conf.get('disabled_process', [])
			if cmd in ls:
				ls.remove(cmd)
			else:
				ls.append(cmd)
				self.manager.processes[cmd].stop()
			
			self.manager.conf._set('disabled_process', ls)
			self.processes.destroy()
			self.manager.processes = {}
			self.manager.initCacheProcess()
			self.conf_processes()
		except IndexError:
			pass	
		
	def conf_commands(self):
		self.commands = Toplevel()
		self.commands.transient(self.win)
		self.commands.title("Commands")
		
		cmds = Listbox(self.commands)
		cmds.grid(row=0, column=0, columnspan=2, sticky="nswe")
		logWinScroll = Scrollbar(self.commands)
		logWinScroll.grid(column=2, row=0, sticky="ns")
		logWinScroll.config(command=cmds.yview)
		cmds.config(yscrollcommand=logWinScroll.set)
		cmds.bind('<<ListboxSelect>>', self.onselect_commands)	
		i = 0
		for item in self.manager.commands:
			filename = inspect.getfile(self.manager.commands[item].__class__).split("/")[-1].split(".")[0]
			cmds.insert('end', f"{filename}.{item}")
			if item in self.manager.conf.get('disabled_commands'):
				cmds.itemconfig(i, {'bg':'grey', 'fg': 'white'})
			
			i += 1
			
		for i in range(0, 2):
			self.commands.columnconfigure(i, weight=1)	
			
		for i in range(0, 1):
			self.commands.rowconfigure(0, weight=1)	
	def onselect_commands(self, evt):
		w = evt.widget
		selection=w.curselection()
		try:
			cmd = w.get(selection[0])	
			cmd = cmd.split(".")[1]
			ls = self.manager.conf.get('disabled_commands', [])
			if cmd in ls:
				ls.remove(cmd)
				self.manager.commands[cmd].enable()
				
			else:
				ls.append(cmd)
				self.manager.commands[cmd].disable()
				
			self.manager.conf._set('disabled_commands', ls)
			self.commands.destroy()
			self.conf_commands()
		except IndexError:
			pass	
		
	def about(self):
		showinfo(title="About", message="AthenaOS Assistant\nBy Kaiser")
		
	def sendMsg(self, evt=None):
		cmd = self.inputbar.get()
		self.inputbar.delete(0, 'end')
		self.log.insert(cmd, font=['gray'])
		
		if self.manager.waitFor:
			self.manager.waitFor.send(cmd)
			return
			
		for item in self.manager.commands:
			if self.manager.commands[item].check(cmd) and item not in self.manager.conf.get('disabled_commands'):
				self.manager.commands[item].run(self.manager.commands[item].filterSelf(cmd))
				return

		if self.manager.fallback:
			self.manager.fallback.run(cmd)
			
man = Manager()
man.start()
man.join()
man.initCacheCommands()
man.initCacheProcess()
#test = AOSProcess(man)
#test.start()
