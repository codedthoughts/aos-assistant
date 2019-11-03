from threading import Thread
from tkinter import *
from tkinter.ttk import Style
from subprocess import run, PIPE, STDOUT
try:
	import pipin
	PIPIN_FOUND = True
except:
	PIPIN_FOUND = False
	
class AOSLibrary:
	def __init__(self, manager):
		self.manager = manager
		self.delayEnable = False

class APIP(AOSLibrary):
	def __init__(self, manager):
		super().__init__(manager)
		self.delayEnable = True
		self.app = None
		
	def enable(self):
		if PIPIN_FOUND:
			self.app = pipin.PIP(command=['python3', '-m', 'pip'])
		
class SphinxListener(AOSLibrary):
	def __init__(self, manager):
		super().__init__(manager)
		
	def enable(self):
		if not self.manager.process.listenHandler:
			self.manager.process.listenHandler = self.listen
			
	def disable(self):
		if self.manager.process.listenHandler == self.listen:
			self.manager.process.listenHandler = None
	
	def listen(self):
		self.manager.printf(f" --- SPEAK ---")
		p = run([self.manager.conf.get('python_command', 'python3'), self.manager.scriptdir+'sph.py'], stdout=PIPE, stderr=STDOUT)

		output = p.stdout
		exitcode = p.returncode
		
		if output:
			return output.decode('utf-8')[:-1]
		
class DefaultThemingEngine(AOSLibrary):
	def __init__(self, manager):
		super().__init__(manager)
		self.manager.registerConfig('theme')
		self.style = Style()
		self.style.configure("Tk", background="#000000", foreground="white")
		self.delayEnable = True
		
	def enable(self):
		self.manager.addTool('Edit Theme', self.themeList)
		self.loadTheme()
		
	def disable(self):
		self.manager.removeTool('Edit Theme')	

	def themeList(self):
		self.themelistwin = Toplevel()

		Label(self.themelistwin, text="Log Window background:").grid(row=0, column=0)
		self.textbox_bg = Entry(self.themelistwin)
		self.textbox_bg.grid(row=0, column=1)
		self.textbox_bg.insert(0, self.manager.process.log.textbox['background'])
		
		Label(self.themelistwin, text="Log Window Font Colour:").grid(row=0, column=2)
		self.textbox_fg = Entry(self.themelistwin)
		self.textbox_fg.grid(row=0, column=3)
		self.textbox_fg.insert(0, self.manager.process.log.textbox['foreground'])
		
		Label(self.themelistwin, text="Buttons background:").grid(row=1, column=0)
		self.button_bg = Entry(self.themelistwin)
		self.button_bg.grid(row=1, column=1)
		self.button_bg.insert(0, self.style.lookup("TButton", "background"))

		Label(self.themelistwin, text="Buttons padding:").grid(row=2, column=0)
		self.button_fbg = Entry(self.themelistwin)
		self.button_fbg.grid(row=2, column=1)
		self.button_fbg.insert(0, self.style.lookup("TButton", "padding"))
		
		Label(self.themelistwin, text="Buttons foreground:").grid(row=3, column=0)
		self.button_fg = Entry(self.themelistwin)
		self.button_fg.grid(row=3, column=1)
		self.button_fg.insert(0, self.style.lookup("TButton", "foreground"))
		
		Label(self.themelistwin, text="Buttons relief:").grid(row=4, column=0)
		self.button_rf = Entry(self.themelistwin)
		self.button_rf.grid(row=4, column=1)
		self.button_rf.insert(0, self.style.lookup("TButton", "relief"))
		
		Button(self.themelistwin, text="Save", command=self.saveTheme).grid(row=10, column=0)
		self.themelistwin.bind('<Return>', lambda evt: self.saveTheme())
		
	def saveTheme(self):
		self.manager.getConfig('theme')._set('theme_outputwin', self.textbox_bg.get())
		self.manager.getConfig('theme')._set('theme_outputwin_font', self.textbox_fg.get())
		self.manager.process.log.textbox.configure(bg=self.textbox_bg.get())
		self.manager.process.log.textbox.configure(fg=self.textbox_fg.get())
		self.style.configure("TButton", padding=self.button_fbg.get(), relief=self.button_rf.get(), background=self.button_bg.get(), foreground=self.button_fg.get())
		
		data = {
			'button': {
				'padding': self.button_fbg.get(), 'relief': self.button_rf.get(), 'background': self.button_bg.get(), 'foreground': self.button_fg.get()
				}
		}
		self.manager.getConfig('theme')._set('theme', data)
	
	def loadTheme(self):
		tbb = self.manager.getConfig('theme').get('theme_outputwin', self.manager.process.log.textbox['background'])
		tbf = self.manager.getConfig('theme').get('theme_outputwin_font', self.manager.process.log.textbox['foreground'])

		self.manager.process.log.textbox.configure(bg=tbb)
		self.manager.process.log.textbox.configure(fg=tbf)
		
		data = self.manager.getConfig('theme').get('theme', {})
		if data:
			theme_b = data.get('button', None)
			#print(theme_b)
			if theme_b:
				#print(theme_b.get('background'))
				self.style.configure("TButton", 
						 padding=theme_b.get('padding', self.style.lookup("TButton", "padding")), 
						 relief=theme_b.get('relief', self.style.lookup("TButton", "relief")), 
						 background=theme_b.get('background', self.style.lookup("TButton", "background")), 
						 foreground=theme_b.get('foreground', self.style.lookup("TButton", "foreground"))
						)
