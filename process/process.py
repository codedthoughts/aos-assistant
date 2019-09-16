from threading import Thread
import time

class AOSProcess(Thread):
	def __init__(self, manager):
		super().__init__()
		self.manager = manager
		self.daemon = True
		self.stopped = False
		
	def stop(self):
		self.stopped = True	

	def run(self):		
		pass
		
class Test(AOSProcess):
	def run(self):	
		while not self.stopped:
			time.sleep(5)
			self.manager.process.log.insert("TEST")	
			
