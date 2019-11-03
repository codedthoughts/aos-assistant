from .commands import Command
import shlex
import psutil
import os
import subprocess
from tkinter import *
from tkinter.ttk import *
from tkinter.messagebox import * 

class PDFUI:
	pass

class TextFileUI:
	pass

class AudioFileUI:
	pass

class FileBrowser(Command):
	"""
	Has a list of file handlers and a method for adding new.
	Add a method to manager for FileManager to handle local files
	
	Adds a tool for file browsing, which triggers a related call
	
	"""
	pass
