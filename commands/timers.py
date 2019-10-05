from .commands import Command
import shlex
from tkinter import *
from tkinter.ttk import *
from tkinter.messagebox import *
import arrow

class TimeManager:
	def __init__(self):
		self.offset = arrow.now().utcoffset().total_seconds()
		
	def convert(self, timestamp):
		return arrow.get(timestamp).shift(seconds=self.offset)
	
class AddTimer(Command):
	def __init__(self, manager):
		super().__init__(manager)
		self.alias = ['set timer for']
		
class RemindMe(Command):
	def __init__(self, manager):
		super().__init__(manager)
		self.alias = ['remind me']
		
	def run(self, message):
		if message.startswith("to"):
			#<timer name> [in] <time>
			#if no "in" in message then prompt for time seperately
			#or if last word "tomorrow", "tonight", "later" then set a pre-set time
			pass
			
			
