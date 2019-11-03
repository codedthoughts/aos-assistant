import subprocess
import shlex
import socket

class PIP:
	"""
		freeze                      Output installed packages in requirements format.
		config                      Manage local and global configuration.
		wheel                       Build wheels from your requirements.
		hash                        Compute hashes of package archives.
		completion                  A helper command used for command completion.
		debug                       Show information useful for debugging.

	"""
	def __init__(self, **kwargs):
		self.options = kwargs.get('options', [])
		self.command = kwargs.get('command', ['pip3'])
		
	def run(self, command, *options):
		return self.__systemCall([command]+list(options)+self.options)

	def check(self, module_name, *options):
		res = self.__systemCall(['check', module_name]+list(options)+self.options)['output']
		return res
	
	def show(self, module_name, *options):
		res = self.__systemCall(['show', module_name]+list(options)+self.options)['output']
		data = {}
		for item in res.split("\n"):
			if item.split(":")[0]:
				try:
					data[item.split(": ")[0]] = item.split(": ")[1]
				except:
					data[item.split(": ")[0]] = None
					
		return data
	
	def search(self, module_name, *options):
		res = self.__systemCall(['search', module_name]+list(options)+self.options)['output']
		while "\n  INSTALLED" in res:
			res = res.replace("\n  INSTALLED", " - INSTALLED")
		out = {}
		for item in res.split("\n"):
			if item:
				name = item.split()[0]
				ver = item.split("(")[1].split(")")[0]
				desc = item.split(" - ")[1]
				
				if len(item.split(" - ")) > 2:
					installed = item.split(" - ")[2].split()[1]
				else:
					installed = "None"
				out[name] = {'version': ver, 'description': desc, 'installed': installed}
		return out
	
	def install(self, module_name, *options):
		return self.__systemCall(['install', module_name]+list(options)+self.options)
	
	def uninstall(self, module_name, *options):
		return self.__systemCall(['uninstall', module_name]+list(options)+self.options)
	
	def download(self, module_name, *options):
		return self.__systemCall(['download', module_name]+list(options)+self.options)
	
	def update(self, module_name, *options):
		options = list(options)
		options.append("--upgrade")
		return self.__systemCall(['install', module_name]+options+self.options)
	
	def help(self, subject):
		return self.__systemCall(['help', subject]+self.options)
	
	def list(self, *options):
		ls = self.__systemCall(['list']+list(options)+self.options)

		ls = ls['output'].split("\n")
		
		while "" in ls:
			ls.remove("")
				
		ls = ls[2:]
		
		result = {}
		for item in ls:
			data = item.split()
			if len(data) == 2:
				result[item.split()[0]] = item.split()[1]
			else:
				result[item.split()[0]] = {'current': item.split()[1], 'latest': item.split()[2], 'type': item.split()[3]}
		return result

	def checkNetwork(self, host="8.8.8.8", port=53, timeout=3):
		if self.options.get('force_offline', False):
			return False
		try:
			socket.setdefaulttimeout(timeout)
			socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
			return True
		except Exception as ex:
			print( ex)
			return False
	
	def __systemCall(self, command):
		pre = self.command
		command = pre+command
		p = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

		output = p.stdout
		exitcode = p.returncode
		
		out = {}
		out['output'] = output.decode('utf-8')

		out['exit'] = exitcode
			
		return out
	
#out = PIP().install('memory3', '--user', '--upgrade')
#out = PIP().show('jrnl')
#print(out)
