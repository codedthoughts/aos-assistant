import shlex

class Command:
	def __init__(self, manager):
		self.manager = manager
		self.alias = []
		self.check = self.checkStart
		
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
		message = self.filterSelf(message)

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
class NotValid:
	pass

