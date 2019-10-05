from .commands import Command
import shlex
from tkinter import *
from tkinter.ttk import *
from tkinter.messagebox import *
import arrow

class ShowRecords(Command):
	def __init__(self, manager):
		super().__init__(manager)
		self.alias = ['show records', 'show records for']
		self.check = self.checkMulti
		
class RecordEvent(Command):
	def __init__(self, manager):
		super().__init__(manager)
		self.alias = ['remember that i', 'remember i']
		
	def run(self, message):
		eventtimes = {
			'this morning': {'hours': '9:00'},
			'this evening': {'hours': '18:00'},
			'this afternoon': {'hours': '3:00'},
			'yesterday morning': {'days': -1, 'hours': '9:00'},
			'yesterday evening': {'days': -1, 'hours': '18:00'},
			'yesterday afternoon': {'days': -1, 'hours': '3:00'},
			'yesterday': {'days': -1}
		}

		time = arrow.now()
		records = self.manager.conf.get('records', {})
		for evt in eventtimes:
			if evt in message.lower():
				data = eventtimes[evt]
				hours = data.get('hours', None)
				days = data.get('days', None)
				
				if message.lower().endswith(evt):
					message = message.lower().replace(evt, '')
				
				if days:
					if type(days) == int:
						time = time.shift(days=days)
				
				if hours:
					if type(hours) == int:
						time = time.shift(hours=hours)
					
					if type(hours) == str:
						time = time.replace(hour=int(hours.split(":")[0]), minute=int(hours.split(":")[1]))
		
		message = message.strip()
		date = time.format('DD-MM-YYYY')
		time = time.format('HH:mm')
		
		events = records.get(date, [])
		events.append({'time': time, 'record': message})
		records[date] = events
		self.manager.conf._set('records', records)
		self.manager.say('Recorded.')
