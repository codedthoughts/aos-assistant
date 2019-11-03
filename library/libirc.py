from .library import AOSLibrary

class IRCClient(AOSLibrary):
	def __init__(self, manager):
		super().__init__(manager)
		self.client = None
		
	def send(self, msg):
		if self.client:
			self.manager.say(f"Sending {msg} to client")
		else:
			self.manager.say("No IRC client active.")

