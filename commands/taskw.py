from .commands import Command
import shlex
from tkinter import *
from tkinter.ttk import *
from tkinter.messagebox import *
import subprocess
import json

class TaskAPI:
	def __init__(self, logging=False):
		self.logging = logging
		
	def fprint(self, message):
		if self.logging:
			print(message)
			
	def _formatOutput(self, data):
		self.fprint(data)
		try:
			return json.loads(data)
		except:
			return str(data, 'latin-1')
		
	def cmd(self, command):
		self.fprint(f"Executing {command}")
		if not command.startswith("task "):
			command = f"task {command}"
			
		command = f"{command} rc.confirmation:0"
		self.fprint(f"Command finalized: {command}")
		
		f = subprocess.run(command.split(), stderr=subprocess.PIPE, stdout=subprocess.PIPE)
			
		if f.stdout:
			return self._formatOutput(f.stdout)
		else:
			return self._formatOutput(f.stderr)
		
	def add(self, description):
		return self.cmd(f'task add {description}')
	
	def done(self, _id):
		return self.cmd(f'task done {_id}')	
	
	def delete(self, _id):
		return self.cmd(f'task delete {_id}')		
	
	def export(self, _id = ""):
		if _id:
			f = f'task {str(_id)} export'
		else:
			f = 'task export'
			
		return self.cmd(f)
		
	def get(self, dom):
		return self.cmd(f'task _get {dom}')
	
class ShowTasks(Command):
	def __init__(self, manager):
		super().__init__(manager)
		self.alias = ['show tasks', 'list tasks', 'check tasks', 'check task', 'show task']
		self.check = self.checkMulti
		
	def run(self, message):
		t = TaskAPI()
		resp = t.export(message)
		respf = self.manager.say
		if message == "":
			self.manager.say("Here is a list of your tasks.")
			respf = self.manager.printf
		
		for item in resp:
			if item['status'] != 'deleted' and item['status'] != 'completed':
				project = ""
				if item.get('project', None):
					project = f" [{item['project']}]"
					

				respf(f"#{item['id']}{project} - {item['description']}")	

class AddTask(Command):
	def __init__(self, manager):
		super().__init__(manager)
		self.alias = ['add task', 'note']
		
	def run(self, message):
		t = TaskAPI()
		resp = t.add(message)
		self.manager.say(resp)
		
class DoneTask(Command):
	def __init__(self, manager):
		super().__init__(manager)
		self.alias = ['complete task', 'finish task']
		
	def run(self, message):
		t = TaskAPI()
		_id = t.done(message)
		self.manager.say(f"Task saved at ID {_id}.")	
		
class DeleteTask(Command):
	def __init__(self, manager):
		super().__init__(manager)
		self.alias = ['remove task', 'delete task']
		
	def run(self, message):
		t = TaskAPI()
		resp = t.delete(message)
		self.manager.say(resp)		
