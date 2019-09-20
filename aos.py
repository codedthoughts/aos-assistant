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
import subprocess
import shlex
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
		self.textbox.tag_configure('blue', foreground='blue')
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
		
	def insert(self, text, **kargs):
		self.textbox.config(state="normal")
		#print(f"Inserting `{text}` at `{index}`")
		#print(command)
		#print(link_id)
		sep = kargs.get('sep', "\n")
		index = kargs.get('index', "end")
		if kargs.get('command'):
			if not kargs.get('link_id', None):
				raise AttributeError("If command is specified, you must give the link a unique ID usin the `link_id` argument.")
			link_id = kargs.get('link_id')
			self.textbox.tag_configure(link_id, foreground="blue", underline=1)
			self.textbox.tag_bind(link_id, "<Enter>", self._enter)
			self.textbox.tag_bind(link_id, "<Leave>", self._leave)
			self.textbox.tag_bind(link_id, "<Button-1>", kargs.get('command'))
			self.textbox.insert(index, text+sep, link_id)
			self.textbox.config(state="disabled")
			return
		
		if kargs.get('timestamp'):
			text = f"{arrow.now().format('HH:mm:ss')}: {text}"
		self.textbox.insert(index, f"{text}{sep}", kargs.get('font', []))
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
		self.scriptdir = os.path.dirname(os.path.realpath(__file__))+"/"
		self.conf = memory.Memory(path=self.scriptdir+'configs/')
		self.process = AssistantWindow(self)
		self.process.start()
		self.commands = {}
		self.processes = {}
		self.modules = {'commands': [], 'processes': []}
		self.waitFor = None
		self.fallback = None
		self.exmenus = {}
		self.exmenuentries = {}
		self.extconf = {}
		self.history_index = 0
		self.history = self.conf.get('history', [])
	
	def addUIScrollbar(self, widget):
		scroll = Scrollbar(widget.grid_info()['in'])
		
		scroll.config(command=widget.yview)
		widget.config(yscrollcommand=scroll.set)
		scroll.grid(column=widget.grid_info()['column']+1, row=widget.grid_info()['row'], sticky="ns", rowspan=widget.grid_info()['rowspan'])
		return scroll #.grid(column=2, row=0, sticky="ns")
		
	def systemCall(self, command):
		term = self.conf.get('terminal', None)
		if term:
			os.system(term.replace('$s', command+"&"))
		else:
			p = subprocess.run(shlex.split(command), stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

			output = p.stdout
			exitcode = p.returncode
			
			if output:
				self.printf(f" --- OUTPUT ---")
				self.printf(output.decode('utf-8'), timestamp=False)

			self.printf(f"EXIT CODE: {exitcode}", timestamp=False)
			self.printf(f" --- ----- ---")
	
	def systemInvoke(self, command):
		p = subprocess.run(shlex.split(command), stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

		output = p.stdout
		return output
	
	def addHistory(self, message):
		self.history_index = 0
		self.history.append(message)
		if len(self.history) > 9:
			del self.history[0]
			
		self.conf._set('history', self.history)
		
	def registerConfig(self, name):
		if not self.extconf.get(name, None):
			self.extconf[name] = memory.Memory(path=f'{self.scriptdir}configs/{name}.json')
	
	def getConfig(self, name):
		return self.extconf.get(name, None)
	
	def addTool(self, name, call):
		self.process.toolmenu.add_command(label=name, command=call)
		
	def removeTool(self, name):
		self.process.toolmenu.delete(self.process.toolmenu.index(name))
		
	def enableTool(self, name):
		self.process.toolmenu.entryconfig(name, state="normal")
		
	def disableTool(self, name):
		self.process.toolmenu.entryconfig(name, state="disabled")
		
	def addMenuOption(self, entry, name, call):
		m = self.process.extramenu
		if not self.exmenus.get(entry, None):
			menu = Menu(m, tearoff=0)
			m.add_cascade(label=entry, menu=menu)
			self.exmenus[entry] = menu
			self.exmenuentries[entry] = 0
			
		self.exmenus[entry].add_command(label=name, command=call)
		self.exmenuentries[entry] += 1
		
	def removeMenuOption(self, entry, name):
		m = self.process.extramenu
		if not self.exmenus.get(entry, None):
			return
		
		self.exmenus[entry].delete(self.exmenus[entry].index(name))
		self.exmenuentries[entry] -= 1
		if self.exmenuentries[entry] == 0:
			m.delete(m.index(entry))
			del self.exmenus[entry]
			del self.exmenuentries[entry]
		
	def promptConfirm(self, message):
		return askokcancel("Confirm", message)
	
	def say(self, text, **kargs):
		if not self.conf._get('tts'):
			kargs['tag'] = "say-notts"
			self.printf(text, **kargs)
			return
		else:
			kargs['tag'] = "say"
			self.printf(text, **kargs)
		
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
		
		times = kargs.get('timestamp', True)
		
		if "||" in message:
			msg_arr = message.split("||")
			if kargs.get('tag') == 'say':
				self.process.log.insert(f"[ ", sep="")
				self.process.log.insert(f"ATHENA", sep="", font=['blue'])
				self.process.log.insert(f" ] ", sep="")
			elif kargs.get('tag') == 'say-notts':
				self.process.log.insert(f"[ ", sep="")
				self.process.log.insert(f"SYSTEM", sep="", font=['blue'])
				self.process.log.insert(f" ] ", sep="")
			cnt = 0
			for item in msg_arr:
				targ = copy.copy(kargs)
				if (cnt % 2) == 0:
					del targ['link_id']
					del targ['command']
				
				self.process.log.insert(item, **targ, sep="")
				cnt += 1	
			self.process.log.insert("\n", sep="")	
		else:
			if kargs.get('tag') == 'say':
				self.process.log.insert(f"[ ", sep="")
				self.process.log.insert(f"ATHENA", sep="", font=['blue'])
				self.process.log.insert(f" ] ", sep="")

			elif kargs.get('tag') == 'say-notts':
				self.process.log.insert(f"[ ", sep="")
				self.process.log.insert(f"SYSTEM", sep="", font=['blue'])
				self.process.log.insert(f" ] ", sep="")
		
			self.process.log.insert(f"{message}", **kargs)
	
				
	def initCacheProcess(self):
		off_modules = self.conf._get('disabled_modules')
		off_processes = self.conf._get('disabled_process')
		self.printf("Getting Process modules...", tag='debug')
		for file in os.listdir(self.scriptdir+"process/"):
			filename = os.fsdecode(file)
			if filename.endswith(".py"):
				modname = filename.split(".")[0]
				if f"process.{modname}" not in off_modules:
					self.printf(f"Loading process module: {modname}", tag='debug')
					importlib.import_module("process."+modname)
					clsmembers = inspect.getmembers(sys.modules["process."+modname], inspect.isclass)
					for com in clsmembers:
						#print(com[1].__name__)
						if issubclass(com[1], AOSProcess) and com[1] != AOSProcess:
							self.printf(f"Validated {com[1].__name__}", tag='debug')
							self.processes[com[0].lower()] = com[1](self)
							self.processes[com[0].lower()].daemon = True
							
							if com[1].__name__.lower() not in off_processes:
								self.processes[com[0].lower()].start()
								self.printf(f"Started process {com[1].__name__}", tag='debug')
								
							if modname not in self.modules['processes']:
								self.modules['processes'].append(modname)
								self.printf(f"Registered module {modname}", tag='debug')
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
		self.printf("Getting Command modules...", tag='debug')
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
		self.listenHandler = None
	
	def listen(self):
		self.inputbar.delete(0, 'end')
		if self.listenHandler:
			inp = self.listenHandler()
		else:
			inp = "No listen handler installed."
		self.inputbar.insert(0, inp)

	def run(self):
		self.win = Tk()
		self.menu = Menu(self.win)
		self.win.config(menu=self.menu)
		self.filemenu = Menu(self.menu, tearoff=0)
		self.helpmenu = Menu(self.menu, tearoff=0)
		self.extramenu = Menu(self.menu, tearoff=0)
		self.toolmenu = Menu(self.menu, tearoff=0)
		self.filemenu.add_command(label="Modules", command=self.conf_modules)
		self.filemenu.add_command(label="Commands", command=self.conf_commands)
		self.filemenu.add_command(label="Processes", command=self.conf_processes)
		self.filemenu.add_separator()
		self.filemenu.add_command(label="Clear Log", command=self.clearlog)
		self.filemenu.add_separator()
		self.filemenu.add_command(label="Exit", command=lambda: quit())
		
		self.helpmenu.add_command(label="About", command=self.about)
		
		self.toolmenu.add_command(label="Config", command=self.confwinf)
		self.menu.add_cascade(label="File", menu=self.filemenu)
		self.menu.add_cascade(label="Extra", menu=self.extramenu)
		self.menu.add_cascade(label="Tools", menu=self.toolmenu)
		self.menu.add_cascade(label="Help", menu=self.helpmenu)
		self.win.title("AthenaOS Interface")
		self.win.protocol("WM_DELETE_WINDOW", lambda: quit())
		self.win.geometry("640x240")
		self.log = OutputWindow(self.win)
		self.log.master.grid(row=0, column=0, columnspan=10, rowspan=5, sticky="nswe")
		self.inputbar = Entry(self.win)
		self.inputbar.grid(row=6, columnspan=8, column=0, sticky="ew")
		self.inputbar.focus()
		def select_all(widget):
			self.inputbar.select_range(0, 'end')
			self.inputbar.icursor('end')
    
		def cycleHistUp(evt):
			self.manager.history_index -= 1
			if self.manager.history_index < 0:
				self.manager.history_index = (len(self.manager.history)-1)
				
			self.inputbar.delete(0, 'end')
			try:
				self.inputbar.insert(0, self.manager.history[self.manager.history_index])
			except:
				pass
			
		def cycleHistDown(evt):
			self.manager.history_index += 1
			if self.manager.history_index >= len(self.manager.history):
				self.manager.history_index = 0
			self.inputbar.delete(0, 'end')
			try:
				self.inputbar.insert(0, self.manager.history[self.manager.history_index])	
			except:
				pass
		self.inputbar.bind('<Control-KeyRelease-a>', select_all)	
		self.inputbar.bind('<Up>', cycleHistUp)
		self.inputbar.bind('<Down>', cycleHistDown)
		self.inputbar.bind('<Return>', self.sendMsg)
		self.inputButton = ttk.Button(self.win, text="Send", width=5, command=self.sendMsg).grid(row=6, column=8, columnspan=1)
		self.voiceButton = ttk.Button(self.win, text="LSTN", width=5, command=self.listen).grid(row=6, column=9, columnspan=1)
		
		for i in range(0, 4):
			self.win.columnconfigure(i, weight=1)
			
		for i in range(0, 5):
			self.win.rowconfigure(i, weight=1)	
			
		self.log.frame.columnconfigure(0, weight=1)
		self.log.frame.rowconfigure(0, weight=1)

		#print(f"Test: {self.menu.nametowidget('File')}")
		custom_tools = self.manager.conf.get('custom_tools', {})
		for item in custom_tools:
			self.manager.addTool(item, lambda: self.manager.systemCall(custom_tools[item]))	
			
		self.win.mainloop()

	def clearlog(self):
		self.log.delete('1.0', 'end')
	
	def confwinf(self):
		self.confwin = Toplevel()
		self.confwin.title('Config')
		self.toolmenu.entryconfig("Config", state="disabled")
		self.confwin.protocol("WM_DELETE_WINDOW", self.destroy_config )
		cmds = Listbox(self.confwin)
		cmds.grid(row=0, column=0, columnspan=2, sticky="nswe")
		logWinScroll = Scrollbar(self.confwin)
		logWinScroll.grid(column=2, row=0, sticky="ns")
		logWinScroll.config(command=cmds.yview)
		cmds.config(yscrollcommand=logWinScroll.set)
		
		for item in self.manager.conf.get():
			cmds.insert('end', item)
		cmds.bind('<<ListboxSelect>>', self.onselect_config)
		
		ttk.Button(self.confwin, text="Create New Entry", command=self.askCreateNew).grid(column=0, row=1, columnspan=2)
	
	def askCreateNew(self):
		self.confwin.destroy()
		self.askCrWin = Toplevel()
		self.askCrEn = Entry(self.askCrWin)
		self.askCrEn.grid()
		ttk.Button(self.askCrWin, text="Create New Entry", command=lambda: self.editConfVar(self.askCrWin, self.askCrEn.get())).grid(column=0, row=1, columnspan=2)
		
	def destroy_config(self):
		self.toolmenu.entryconfig("Config", state="normal")
		self.confwin.destroy()
		
	def onselect_config(self, evt):
		w = evt.widget
		selection=w.curselection()
		try:
			cmd = w.get(selection[0])	
			self.editConfVar(self.confwin, cmd)
		except:
			pass
	
	def editConfVar(self, hostwin, cmd):
		editor = Toplevel()
		hostwin.destroy()
		value = self.manager.conf.get(cmd, '')
		editor.protocol("WM_DELETE_WINDOW", lambda: self.destroyeditor(editor) )				
		if type(value) == str:
			en = Entry(editor)
			en.pack()
			en.insert('0', value)
			send = ttk.Button(editor, text="Confirm", command=lambda: self.send_config(editor, cmd, en.get()))
			send.pack()

		elif type(value) == bool:
			ttk.Button(editor, text="TRUE", command=lambda: self.send_config(editor, cmd, True)).pack()
			ttk.Button(editor, text="FALSE", command=lambda: self.send_config(editor, cmd, False)).pack()
			
		else:
			self.manager.say(f"Type {type(value)} currently not supported in live editing.")
			self.manager.say(f"{value}")
			editor.destroy()
			self.confwinf()		
			
	def destroyeditor(self, editor_window):
		editor_window.destroy()
		self.confwinf()
		
	def send_config(self, editor_window, key, value):
		self.manager.conf._set(key, value)
		self.destroyeditor(editor_window)
		
	def addPromtCanceller(self, cmd):
		self.promptmenu = Menu(self.menu, tearoff=0)
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
				del self.manager.processes[item]
				
			for item in copy.copy(self.manager.commands):
				self.manager.commands[item].disable()
				del self.manager.commands[item]
				
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
		self.manager.addHistory(cmd)
		self.inputbar.delete(0, 'end')
		self.log.insert(f"[ {man.conf.get('name', 'You')} ] {cmd}", font=['gray'])
		
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
man.say(f"Hello, {man.conf.get('name', 'there')}.")
#man.printf(f"This is a", sep=" ")
#man.printf(f"link", sep="", link_id="test1", command=lambda evt: print("lol"))
#man.printf(f".", sep="\n")
#man.printf(f"This is a", sep=" ")
#man.printf(f"link", sep="", link_id="test1", command=lambda evt: print("heh"))
#man.printf(f".", sep="\n")
#man.say(f"This ||may|| be a link.", link_id="test1", command=lambda evt: print("heh"))
#man.printf(f"This ||iisssss|| be a link.", link_id="test1", command=lambda evt: print("heh"))
#test = AOSProcess(man)
#test.start()
