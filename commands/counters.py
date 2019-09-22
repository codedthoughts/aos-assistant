from .commands import Command
import shlex
import psutil
import os
import subprocess
from tkinter import *
from tkinter.ttk import *
from tkinter.messagebox import *

class Counters(Command):
	def __init__(self, manager):
		super().__init__(manager)
		manager.registerConfig('counters') 
		
	def run(self, message):
		if message:
			if len(message.split()) == 1:
				v = self.manager.getConfig('counters').get(message, "not set")
				self.manager.say(f"{message} is {v}")
				
			if len(message.split()) == 2:
				key = message.split()[0]
				val = message.split()[1]
				if not val.isdigit():
					self.manager.say(f"Value should be a number.")
					return
				self.manager.getConfig('counters')._set(key, val)
				self.manager.say(f"{message} is {val}")
				
			if len(message.split()) == 3:
				key = message.split()[0]
				mod = message.split()[1]
				val = message.split()[2]
				v = self.manager.getConfig('counters').get(key, 0)
				print(f"{v}{mod}{val}")
				res = eval(f"{v}{mod}{val}")
				print(res)
				self.manager.getConfig('counters')._set(key, res)
				self.manager.say(f"{message} is {res}")		
				
class CountersGUI(Command):
	def __init__(self, manager):
		super().__init__(manager)
		self.check = self.dontCheck
		manager.registerConfig('counters') 
		self.selected_counter = None
		
	def enable(self):
		self.manager.addMenuOption('Counters', 'Open', lambda: self.openCounters())
		
	def disable(self):
		self.manager.removeMenuOption('Counters', 'Open')	
		
	def openCounters(self):
		self.countersui = Toplevel()
		self.refreshCounterUI()
		
	def onselect(self, evt):
		w = evt.widget
		selection=w.curselection()
		try:
			self.selected_counter = w.get(selection[0])		
			print(self.selected_counter)
			self.refreshCounterUI()
			
		except:
			pass
	
	def modCounter(self, typev):
		if typev == "+":
			cur = self.manager.getConfig('counters')[self.selected_counter]
			print(cur)
			self.manager.getConfig('counters')._set(self.selected_counter, cur+1)
			print(self.manager.getConfig('counters')[self.selected_counter])
		elif typev == "-":
			cur = self.manager.getConfig('counters')[self.selected_counter]
			self.manager.getConfig('counters')._set(self.selected_counter, cur-1)
		elif typev == "del":
			del self.manager.getConfig('counters').data[self.selected_counter]
			self.manager.getConfig('counters').save()
			self.selected_counter = None
		elif typev == "back":
			self.selected_counter = None
		
		self.refreshCounterUI()
	
	def addCounter(self):
		for widget in self.countersui.winfo_children():
			widget.destroy()
			
		self.new = Entry(self.countersui)
		self.new.grid()
		Button(self.countersui, text="Save", command=self.addCounterSave).grid(row=1)
		
	def addCounterSave(self):
		if self.new.get():
			self.manager.getConfig('counters')._set(self.new.get(), 0)
			self.refreshCounterUI()
			
	def refreshCounterUI(self):
		for widget in self.countersui.winfo_children():
			widget.destroy()
			
		if self.selected_counter:
			conf = self.manager.getConfig('counters')
			Label(self.countersui, text=self.selected_counter).grid(row=0, column=0)
			Label(self.countersui, text=conf[self.selected_counter]).grid(row=0, column=1)
			Button(self.countersui, text="+", command=lambda: self.modCounter('+')).grid(row=0, column=2)
			Button(self.countersui, text="-", command=lambda: self.modCounter('-')).grid(row=0, column=3)
			Button(self.countersui, text="X", command=lambda: self.modCounter('del')).grid(row=0, column=4)
			Button(self.countersui, text="Back", command=lambda: self.modCounter('back')).grid(row=1, column=0, columnspan=4)
		else:
			conf = self.manager.getConfig('counters').get()
			counters = Listbox(self.countersui)
			counters.grid()
			counters.bind('<<ListboxSelect>>', self.onselect)	
			for item in conf:
				counters.insert('end', item)
				
			Button(self.countersui, text="Add", command=self.addCounter).grid(row=1)
