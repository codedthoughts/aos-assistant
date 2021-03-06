import shlex
import psutil
import os
import subprocess
from tkinter import *
from tkinter.ttk import *
from tkinter.messagebox import *
import random
import humanfriendly
import textblob
from contextlib import redirect_stdout
import io
import textwrap

class Command:
	def __init__(self, manager):
		self.manager = manager
		self.alias = []
		self.check = self.checkStart
		self.runThreaded = False
		
	def enable(self):
		pass
		
	def disable(self):
		pass
		
	def dontCheck(self, message):
		return False
	
	def checkStart(self, message):
		if len(self.alias):
			for alias in self.alias:
				if message.lower().startswith(f"{alias} "):
					return True
				
				if message.lower().startswith(f"{alias}"):
					return True		
		else:
			if message.lower().startswith(f"{type(self).__name__.lower()} "):
				return True
			
			if message.lower().startswith(f"{type(self).__name__.lower()}"):
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
					return msg[len(alias):]
		else:
			if msg.startswith(f"{type(self).__name__.lower()} "):
				return msg[len(type(self).__name__.lower())+1:]
			
			if msg.startswith(f"{type(self).__name__.lower()}"):
				return msg[len(type(self).__name__.lower()):]
		return msg

class PipCmd(Command):
	def __init__(self, manager):
		super().__init__(manager)
		self.alias = ['pip']
	
	def run(self, message):
		if message.startswith("list"):
			self.manager.say("Loading that...")
			self.manager.runAsync(self.getList)
	
	def getList(self):
		data = pipinter = self.manager.getLib('library', 'apip').app.list()
		out = ""
		for item in data:
			out += f"{item}, version {data[item]}\n"
		self.manager.say("Here you go.")
		self.manager.printf(out)
			
class AlsaVolumeSet(Command):
	def __init__(self, manager):
		super().__init__(manager)
		self.alias = ['set volume to', 'set volume', 'change volume to', 'change volume']
		
	def run(self, message):
		cmd = "amixer -D pulse sset Master "
		if not message.endswith("%"):
			message = f"{message}%"
		os.system(cmd+message)	

class AlsaVolumeControl(Command):
	def __init__(self, manager):
		super().__init__(manager)
		self.alias = ['volume']
		
	def run(self, message):
		cmd = "amixer -D pulse sset Master "
		if message.lower().startswith('up'):
			if len(message.split()) > 1:
				inc = message.split()[1]
				cmd += f"{inc}%+"
			else:
				cmd += "10%+"
		elif message.lower().startswith('down'):
			if len(message.split()) > 1:
				inc = message.split()[1]
				cmd += f"{inc}%-"
			else:
				cmd += "10%-"
		else:
			return
		
		os.system(cmd)	
		
class AlsaVolumeMute(Command):
	def __init__(self, manager):
		super().__init__(manager)
		self.check = self.checkFull
		self.alias = ['mute audio']
		
	def run(self, message):
		cmd = "amixer -D pulse sset Master 0%"
		os.system(cmd)	
		
class AlsaVolumeUnMute(Command):
	def __init__(self, manager):
		super().__init__(manager)
		self.check = self.checkFull
		self.alias = ['unmute audio']
		
	def run(self, message):
		cmd = f"amixer -D pulse sset Master 60%"
		os.system(cmd)	
		
class TestPanelMaker(Command):
	def __init__(self, manager):
		super().__init__(manager)
		self.check = self.checkFull
		self.alias = ['open debug panel']
		
	def run(self, message):
		pman = self.manager.getProcess('panelmanager')	
		pman.prepareCustomPanel()
		Label(self.manager.process.panels, text="This is a debug").grid()
		
class AddSystemTool(Command):
	def __init__(self, manager):
		super().__init__(manager)
		self.alias = ['add tool']
		
	def enable(self):
		self.manager.addMenuOption('Custom Tools', 'Add Tool', self.addToolMenu)
		self.manager.addMenuOption('Custom Tools', 'Remove Tool', self.remToolMenu)
		
	def disable(self):
		self.manager.removeMenuOption('Custom Tools', 'Add Tool')	
		self.manager.removeMenuOption('Custom Tools', 'Remove Tool')
		
	def addToolMenu(self):
		self.addToolWin = Toplevel()
		Label(self.addToolWin, text="Name:").grid(row=0, column=0)
		self.name_entry = Entry(self.addToolWin)
		self.name_entry.grid(row=0, column=1)
		Label(self.addToolWin, text="Command:").grid(row=1, column=0)
		self.command_entry = Entry(self.addToolWin)
		self.command_entry.grid(row=1, column=1)
		Button(self.addToolWin, text="Confirm", command=self.sendAddTool).grid(row=2, columnspan=2)
		
	def sendAddTool(self):
		if self.name_entry.get() and self.command_entry.get():
			self.run(f'"{self.name_entry.get()}" {self.command_entry.get()}')
			self.addToolWin.destroy()
			
	def remToolMenu(self):
		self.remToolWin = Toplevel()
		self.toollist = Listbox(self.remToolWin)
		self.toollist.grid(row=0, column=0, columnspan=2, sticky="nswe")
		logWinScroll = Scrollbar(self.remToolWin)
		logWinScroll.grid(column=2, row=0, sticky="ns")
		logWinScroll.config(command=self.toollist.yview)
		self.toollist.config(yscrollcommand=logWinScroll.set)
		
		custom_tools = self.manager.conf.get('custom_tools', {})
		for item in custom_tools:
			self.toollist.insert('end', item)
			
		self.remToolWin.rowconfigure(0, weight=1)
		self.remToolWin.columnconfigure(0, weight=1)
		
		self.toollist.bind('<<ListboxSelect>>', self.askRemTool)
	
	def askRemTool(self, evt):
		name = evt.widget.get(evt.widget.curselection()[0])
		if self.manager.promptConfirm(f'Really delete tool {name}?'):
			self.remToolWin.destroy()
			custom_tools = self.manager.conf.get('custom_tools', [])
			del custom_tools[name]
			self.manager.conf._set('custom_tools', custom_tools)
			self.manager.removeTool(name)
			self.remToolMenu()
			
	def run(self, message):
		print(message)
		name = shlex.split(message)[0]
		command = message[len(name)+3:]
		print(name)
		print(command)
		if not command:
			command = name
			
		custom_tools = self.manager.conf.get('custom_tools', {})
		custom_tools[name] = command
		self.manager.conf._set('custom_tools', custom_tools)

		if self.manager.conf.get('custom_tools_terminal', "NOTSET") == "NOTSET" and self.manager.conf.get('terminal', None):
			self.manager.conf._set('custom_tools_terminal', True)
			
		self.manager.say('New custom tool added.')
		self.manager.printf(f"Name: {name}")
		self.manager.printf(f"Command: {command}")
		self.manager.addTool(name, lambda: self.manager.systemCall(command))
	
class DefineWord(Command):
	def __init__(self, manager):
		super().__init__(manager)
		self.alias = ['define']
		
	def run(self, message):
		try:
			blob = textblob.Word(message)
			defs = blob.definitions
			s = ""
			if len(defs) > 0:
				for item in defs[0:4]:
					s += item.capitalize()+".\n"
				self.manager.say(s)
			else:
				self.manager.say("No result found.")
		except RuntimeError:	
			blob = textblob.Word(message)
			defs = blob.definitions
			s = ""
			if len(defs) > 0:
				for item in defs[0:4]:
					s += item.capitalize()+".\n"
				self.manager.say(s)
			else:
				self.manager.say("No result found.")
				
class Translate(Command):
	def enable(self):
		self.manager.addTool('Translator', self.translateWindow)
		
	def disable(self):
		self.manager.removeTool('Translator')	
	
	def translateWindow(self):
		w = Toplevel()
		self.tr_input = Text(w, height=20, width=30)
		self.tr_output = Text(w, height=20, width=30)
		self.tr_lang = Entry(w)
		
		self.tr_input.grid(row=0, column=0, columnspan=2)
		self.tr_output.grid(row=0, column=3)
		self.tr_lang.grid(row=1, column=0)
		self.tr_lang.insert('end', self.manager.conf.get('default_translator', 'de'))
		Button(w, text="Translate", command=self.execTranslate).grid(row=1, column=1)
	
	def execTranslate(self):
		tolang = self.tr_lang.get()
		self.tr_output.delete('1.0', 'end')
		if tolang != self.manager.conf.get('default_translator', 'de'):
			self.manager.conf._set('default_translator', tolang)
			
		msg = textblob.TextBlob(self.tr_input.get('1.0', 'end'))
		try:
			self.tr_output.insert('1.0', msg.translate(to=tolang))
		except textblob.exceptions.NotTranslated:
			self.tr_output.insert('1.0', "The text was not translated. Are you trying to translate to and from the same language, or the word couldn't be translated?")
		except textblob.exceptions.TranslatorError:
			self.tr_output.insert('1.0', "There was an error on the translator side. Maybe try again later?")	
			
	def run(self, message):
		if len(shlex.split(message)) > 2:
			if shlex.split(message)[-2] == "to":
				lang = shlex.split(message)[-1]
				message = message[:-6]
		else:
			lang = self.manager.conf.get('default_translator', 'de')
		
		
		msg = textblob.TextBlob(message)
		try:
			self.manager.say(msg.translate(to=lang))
		except textblob.exceptions.NotTranslated:
			self.manager.say("The text was not translated. Are you trying to translate to and from the same language, or the word couldn't be translated?")
		except textblob.exceptions.TranslatorError:
			self.manager.say("There was an error on the translator side. Maybe try again later?")	

class SendIRC(Command):
	def __init__(self, manager):
		super().__init__(manager)
		self.alias = ['irc: ']
		
	def run(self, message):
		client = self.manager.getLib('libirc', 'ircclient')
		self.manager.runAsync(client.send, message)
		
class Bash(Command):
	def __init__(self, manager):
		super().__init__(manager)
		self.alias = ['bash', '$']
	
	def run(self, message):
		self.manager.systemCall(message)
			
class EightBall(Command):
	def __init__(self, manager):
		super().__init__(manager)
		self.alias = ['8ball']
		
	def run(self, message):
		responses = ["as I see it, yes",
		"ask again later",
		"better not tell you now",
		"cannot predict now",
		"concentrate and ask again",
		"don’t count on it",
		"it is certain",
		"it is decidedly so",
		"most likely",
		"my reply is no",
		"my sources say no",
		"outlook good",
		"outlook not so good",
		"reply hazy try again",
		"signs point to yes",
		"very doubtful",
		"without a doubt",
		"yes",
		"yes, definitely",
		"you may rely on it"]
		res = random.choice(responses)
		self.manager.say(res.capitalize()+".")	
		
class Roll(Command):
	def __init__(self, manager):
		super().__init__(manager)
		self.alias = ['random']
		
	def run(self, message):
		if message == "":
			message = "10"
		if not message.isdigit():
			return self.message("Value must be a number.")
		random.randint(0, int(message))
		self.manager.say(f"You rolled {random.randint(0, int(message))} out of {message}.")
		
class Flip(Command):
	def __init__(self, manager):
		super().__init__(manager)
		self.alias = ['flip a coin']
		self.check = self.checkFull
		
	def run(self, message):
		if random.random() < 0.5:
			self.manager.say(f"You flipped heads.")
		else:
			self.manager.say(f"You flipped tails.")

class Dice(Command):
	def __init__(self, manager):
		super().__init__(manager)
		self.alias = ['roll']
		self.check = self.checkMulti
		
	def run(self, message):
		notation = message
		if not notation:
			notation = "2d6"
		try:
			dm = 0
			if "+" in notation:
				dm = int(notation.split("+")[1]) #modifier; 2d12+2 adds 2 to total
				notation = notation.split("+")[0]
			dn = int(notation.split("d")[0]) #number of die; eg 2d12 is 2
			ds = int(notation.split("d")[1]) #sides of the die; eg 2d12 is 12
			if dn <= 0 or ds <= 1:
				return self.message("Dice count should be above 1 and sides should be above 0.")
			
			dies = []
			while dn > 0:
				dies.append(random.randint(1, ds))
				dn -= 1

			dies_sl = []
			dies_total = 0
			for item in dies:
				dies_total += int(item)
				dies_sl.append(str(item))
			
			if dm > 0:
				dies_total += dm
				dies_total = f"{dies_total} (+{dm})"
				
			dies_string = humanfriendly.text.concatenate(dies_sl)

			self.manager.say(f"You rolled {dies_string}. (Total: {dies_total})")
		except IndexError:
			self.manager.say("Error in notation; example is `2d6`.")
		except ValueError:
			self.manager.say("One of the values is not a real number.")
		except Exception as e:
			self.manager.say(f"Some problem; {e}")		

class Calculate(Command):
	def __init__(self, manager):
		super().__init__(manager)
		self.alias = ['calc']
	
	def run(self, message):
		try:
			value = eval(message, {})
			return self.manager.say(f"{message} evaluates to {str(value)}")
		except Exception as e:
			return self.manager.say("Syntax error.")
				
class Eval(Command):
	def __init__(self, manager):
		super().__init__(manager)
		self.alias = ['eval', 'py']
		
	def enable(self):
		self.manager.addMenuOption('Python', 'Evaluate', lambda: self.evalmenu())
		
	def disable(self):
		self.manager.removeMenuOption('Python', 'Evaluate')		
		
	def run(self, message):
		env = {
			'_config': self.manager.conf,
			'_manager': self.manager,
			'_window': self.manager.process
		}
		#message = message.strip('` \n')
		env.update(globals())
		stdout = io.StringIO()
		
		
		to_compile = f'def func():\n{textwrap.indent(message, "  ")}'
		try:
			exec(to_compile, env)
		except Exception as e:
			return self.manager.say(f"An error was encounter during compilation: {e}")
			
		func = env['func']
		try:
			with redirect_stdout(stdout):
				func()
		except Exception as e:
			self.manager.say(f"An error was raised: {e}")
			
		value = stdout.getvalue()
		self.manager.printf(value)
		
	def evalmenu(self):
		w = Toplevel()
		self.textbox = Text(w, height=20, width=70)
		self.textbox.grid(row=0, column=0, columnspan=5)
		logWinScroll = Scrollbar(w)
		logWinScroll.grid(column=5, row=0, sticky="ns")
		logWinScroll.config(command=self.textbox.yview)
		self.textbox.config(yscrollcommand=logWinScroll.set)
		
		self.fileselecten = Entry(w)
		self.fileselecten.grid(row=1, column=0)
		
		
		Button(w, text="Open", command=self.openFile).grid(row=1, column=1)
		Button(w, text="Save", command=self.saveFile).grid(row=1, column=2)
		Button(w, text="Evaluate", command=self.execute).grid(row=1, column=3)
	
	def getPath(self):
		if not self.fileselecten.get():
			path = self.manager.scriptdir+'_temp/eval.py'
		else:
			path = self.manager.scriptdir+'_temp/'+self.fileselecten.get()+'.py'
			
		return path
	
	def openFile(self):
		if not os.path.isdir(self.manager.scriptdir+'_temp'):
			os.mkdir(self.manager.scriptdir+'_temp')
			
		path = self.getPath()
		
		if os.path.isfile(path):
			with open(path, 'r') as f:
				self.textbox.delete('1.0', 'end')
				self.textbox.insert('1.0', f.read())
				
	def saveFile(self):
		if not os.path.isdir(self.manager.scriptdir+'_temp'):
			os.mkdir(self.manager.scriptdir+'_temp')
			
		path = self.getPath()
			
		#print(path)	
		with open(path, 'w') as f:
			f.write(self.textbox.get(1.0, 'end'))
	
	def execute(self):
		self.saveFile()
		path = self.getPath()
		with open(path, 'r') as f:
			#print(f.read())
			self.run(f.read())
			
	def execute2(self):
		self.saveFile()
		path = self.getPath()
		#os.system(f"{self.manager.get('python_command', 'python3')} {path}")
		p = subprocess.run([self.manager.conf.get('python_command', 'python3'), path], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

		output = p.stdout
		exitcode = p.returncode
		
		if output:
			self.manager.printf(f" --- OUTPUT ---")
			self.manager.printf(output.decode('utf-8'), timestamp=False)

		self.manager.printf(f"EXIT CODE: {exitcode}", timestamp=False)
		self.manager.printf(f" --- ----- ---")
		
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
		#print(message)
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
		#print(message)
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
		#print(message)
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
		#print(message)
		if not message:
			self.manager.say(f"What process should be killed? Say CANCEL to stop changing.")
			self.manager.takeInput(self)
			return
		
		self.killTarget(message)
		
	def send(self, message):
		#print(message)
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

