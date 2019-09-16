import shlex
import psutil
import os
from tkinter import *
from tkinter import ttk
from tkinter.ttk import *
from tkinter.messagebox import *

class Command:
	def __init__(self, manager):
		self.manager = manager
		self.alias = []
		self.check = self.checkStart
		
	def enable(self):
		pass
		
	def disable(self):
		pass
						
	def checkStart(self, message):
		if len(self.alias):
			for alias in self.alias:
				if message.lower().startswith(f"{alias} "):
					return True
						
		else:
			if message.lower().startswith(f"{type(self).__name__.lower()} "):
				return True
			
		return False
	
	def checkFull(self, message):
		if len(self.alias):
			for alias in self.alias:
				if message.lower() == alias.lower():
					return True
						
		else:
			if message.lower() == type(self).__name__.lower():
				return True
			
		return False
	
	def checkMulti(self, message):	
		if self.checkFull(message) or self.checkStart(message):
			return True
		
		return False
	
	def run(self, message):		
		pass
	
	def filterSelf(self, msg):
		if len(self.alias):
			for alias in self.alias:
				if msg.lower().startswith(f"{alias} "):
					return msg[len(alias)+1:]
				if msg.lower().startswith(f"{alias}"):
					return msg[len(alias)+1:]
		else:
			if msg.startswith(f"{type(self).__name__.lower()} "):
				return msg[len(type(self).__name__.lower())+1:]
			
		return msg
		
class Set(Command):
	def run(self, message):		
		args = shlex.split(self.filterSelf(message))
		try:
			key = args[0]
			value = args[1]
			if value.isdigit():
				value = int(value)
				
			elif value.lower() == "false":
				value = False
				
			elif value.lower() == "true":
				value = True
			self.manager.conf._set(key, value)
			self.manager.say(f"{key} set to {value}")
		except Exception as e:
			self.manager.say(e)
			
class Get(Command):
	def __init__(self, manager):
		super().__init__(manager)
		self.check = self.checkMulti
		
	def run(self, message=""):	
		message = self.filterSelf(message)
		if not message:
			self.manager.say("No message")
		else:
			args = shlex.split(message)
			try:
				key = args[0]

				self.manager.say(f"{key} is set to {self.manager.conf._get(key)}")
			except Exception as e:
				self.manager.say(e)	
			
class Echo(Command):
	def __init__(self, manager):
		super().__init__(manager)
		self.check = self.checkMulti
		
	def run(self, message):
		message = self.filterSelf(message)

		if not message:
			self.manager.say(f"You enter echo mode.")
			self.manager.takeInput(self)
		else:
			self.manager.say(message)
		
	def send(self, message):
		self.manager.say(f"{message}")
		if message == "quit":
			self.manager.say(f"You left echo mode.")
			self.manager.clearInput()
			
class Fallback(Command):
	def __init__(self, manager):
		super().__init__(manager)
		self.check = self.checkMulti
		
	def run(self, message):
		if not message:
			self.manager.say(f"What command should be fallback? Say NONE to disable or CANCEL to stop changing.")
			self.manager.takeInput(self)
		else:
			if message.lower() == "none":
				self.manager.fallback = None
				self.manager.conf._set('fallback', None)
				self.manager.say("Fallback disabled.")
				return
			try:
				self.manager.fallback = self.manager.commands[message]
				self.manager.conf._set('fallback', message)
				self.manager.say(f"Fallback set to {message}.")
			except:
				self.manager.say(f"Invalid command. Say NONE to disable or CANCEL to stop changing.")
				
	def send(self, message):
		if message.lower() == "none":
			self.manager.fallback = None
			self.manager.conf._set('fallback', None)
			self.manager.say("Fallback disabled.")
			return
		try:
			self.manager.fallback = self.manager.commands[message]
			self.manager.conf._set('fallback', message)
			self.manager.say(f"Fallback set to {message}.")
		except:
			self.manager.say(f"Invalid command. Say NONE to disable or CANCEL to stop changing.")
			
		if message.lower() == "cancel":
			self.manager.say(f"Okay, cancelling.")
			self.manager.clearInput()			

class LimitProcess(Command):
	def __init__(self, manager):
		super().__init__(manager)
		self.check = self.checkMulti
		self.alias = ['limit process']
	
	def enable(self):
		self.manager.addMenuOption('System Manager', 'Limit Process', lambda: self.asklimit())
		self.manager.addMenuOption('System Manager', 'Check CPU Limiters', lambda: self.checklimits())
		
	def disable(self):
		self.manager.removeMenuOption('System Manager', 'Limit Process')		
		self.manager.removeMenuOption('System Manager', 'Check CPU Limiters')	
	
	def checklimits(self):
		self.delimwin = Toplevel()
		self.delimwin.title("DeLimit Process")
		self.deproclist = Listbox(self.delimwin)
		self.deproclist.grid(row=0, column=0, columnspan=2, sticky="nswe")
		logWinScroll = Scrollbar(self.delimwin)
		logWinScroll.grid(column=2, row=0, sticky="ns")
		logWinScroll.config(command=self.deproclist.yview)
		self.deproclist.config(yscrollcommand=logWinScroll.set)
		
		self.delimwin.rowconfigure(0, weight=1)
		self.delimwin.columnconfigure(0, weight=1)
		
		self.delimwin.bind('<<ListboxSelect>>', lambda evt: self.delimit(evt.widget.get(evt.widget.curselection()[0])))
		
		found = False
		for p in psutil.process_iter():
			#print(p.name())
			if p.name() == "cpulimit":
				cmd = p.cmdline()
				pid = cmd[cmd.index("--pid")+1]
				limit = cmd[cmd.index("--limit")+1]
				name = "DEFAULT"
				for n in psutil.process_iter():
					if n.pid == int(pid):
						name = n.name()
				self.deproclist.insert('end', f"{pid}: {name} / {limit}%")
				found = True
				
		if not found:
			self.delimwin.destroy()
			self.manager.say("No limiters running.")
			
	def delimit(self, proc):
		for p in psutil.process_iter():
			if p.name() == "cpulimit":
				#print(f"{n.pid} ({type(n.pid)}) {pid} {type(pid)}")
				if int(p.cmdline()[p.cmdline().index("--pid")+1]) == int(proc.split(":")[0]):
					if self.manager.promptConfirm(f'DeLimit {proc}?'):
						p.kill()
			
		self.delimwin.destroy()
		
		for p in psutil.process_iter():
			if p.name() == "cpulimit":	
				self.checklimits()
				return
		
		
	def asklimit(self):
		self.limwin = Toplevel()
		self.limwin.title("Limit Process")
		self.proclist = Listbox(self.limwin)
		self.proclist.grid(row=0, column=0, columnspan=2, sticky="nswe")
		logWinScroll = Scrollbar(self.limwin)
		logWinScroll.grid(column=2, row=0, sticky="ns")
		logWinScroll.config(command=self.proclist.yview)
		self.proclist.config(yscrollcommand=logWinScroll.set)
		
		self.percent = Entry(self.limwin)
		self.percent.grid(row=1, column=0, columnspan=2, sticky="ew")
		self.percent.insert(0, '30')
		self.limwin.rowconfigure(0, weight=1)
		self.limwin.columnconfigure(0, weight=1)
		
		self.limwin.bind('<<ListboxSelect>>', lambda evt: self.send(f"{evt.widget.get(evt.widget.curselection()[0])} {self.percent.get()}"))
		
		sortedlist = []
		for p in psutil.process_iter():
			sortedlist.append(p.name())
		
		for item in sorted(sortedlist):
			self.proclist.insert('end', item)
			
	def run(self, message):
		print(message)
		if not message:
			self.manager.say(f"What process should be limited? Say CANCEL to stop changing.")
			self.manager.takeInput(self)
			return
		
		if len(message.split()) > 1:
			if not message.split()[1].isdigit():
				self.manager.say("Percentage is not a valid number.")
				return
			
			self.limitTarget(message.split()[0], message.split()[1])
		else:
			self.manager.say("Should be in format of <process limit_percent>.")
			
	def send(self, message):
		print(message)
		if message.lower() == "cancel":
			self.manager.clearInput()
			self.manager.say("Cancelled.")
			return	
		
		if len(message.split()) > 1:
			if not message.split()[1].isdigit():
				self.manager.say("Percentage is not a valid number.")
				return
			
			self.limitTarget(message.split()[0], message.split()[1])
		else:
			self.manager.say("Should be in format of <process limit_percent>.")
			
	def limitTarget(self, target, value):
		for p in psutil.process_iter():
			if target.lower() in p.name().lower() or target in p.cmdline():# or value in p.exe():
				if self.manager.promptConfirm(f"Really limit process {p.name()} to {value}% usage?"):
					os.system(f"{self.manager.scriptdir}bin/cpulimit --pid {p.pid} --limit {value}&")
					self.manager.say(f"Limited {p.name()}.")
					return
				else:
					self.manager.say("Cancelled.")
					return
		
		self.manager.say("Process not found.")	
		
class KillProc(Command):
	def __init__(self, manager):
		super().__init__(manager)
		self.check = self.checkMulti
		self.alias = ['kill']
		self.killwin = None
		
	def enable(self):
		self.manager.addMenuOption('System Manager', 'Kill Process', lambda: self.askkill())
		
	def disable(self):
		self.manager.removeMenuOption('System Manager', 'Kill Process')
	
	def askkill(self):
		self.killwin = Toplevel()
		self.killwin.title("Kill Process")
		self.proclist = Listbox(self.killwin)
		self.proclist.grid(row=0, column=0, columnspan=2, sticky="nswe")
		logWinScroll = Scrollbar(self.killwin)
		logWinScroll.grid(column=2, row=0, sticky="ns")
		logWinScroll.config(command=self.proclist.yview)
		self.proclist.config(yscrollcommand=logWinScroll.set)
		
		self.killwin.rowconfigure(0, weight=1)
		self.killwin.columnconfigure(0, weight=1)

		self.killwin.bind('<<ListboxSelect>>', lambda evt: self.send(evt.widget.get(evt.widget.curselection()[0])))
		sortedlist = []
		for p in psutil.process_iter():
			sortedlist.append(p.name())
		
		for item in sorted(sortedlist):
			self.proclist.insert('end', item)
			
	def run(self, message):
		print(message)
		if not message:
			self.manager.say(f"What process should be killed? Say CANCEL to stop changing.")
			self.manager.takeInput(self)
			return
		
		self.killTarget(message)
		
	def send(self, message):
		print(message)
		if message.lower() == "cancel":
			self.manager.clearInput()
			self.manager.say("Cancelled.")
			return	
		
		self.killTarget(message)
		
	def killTarget(self, target):
		for p in psutil.process_iter():
			if target.lower() in p.name().lower() or target in p.cmdline():# or value in p.exe():
				if self.manager.promptConfirm(f"Really kill process {' '.join(p.cmdline())}?"):
					p.kill()
					self.manager.say(f"Killed {p.name()}.")
					return
				else:
					self.manager.say("Cancelled.")
					return
		
		self.manager.say("Process not found.")

