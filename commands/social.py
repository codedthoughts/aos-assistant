from .commands import Command
import shlex
import psutil
import os
import subprocess
from tkinter import *
from tkinter import ttk
from tkinter.ttk import *
from tkinter.messagebox import *

class ContactsManager(Command):
	def __init__(self, manager):
		super().__init__(manager)
		self.check = self.dontCheck
		manager.registerConfig('social')
		self.selected_person = ""
		self.selected_value = ""
		
	def enable(self):
		self.manager.addTool('Contacts', lambda: self.openContactsUI())
		
	def disable(self):
		self.manager.removeTool('Contacts')	
	
	def closeContactsUI(self):
		self.manager.enableTool('Contacts')
		self.contactswin.destroy()
		
	def closeEditorUI(self):
		self.editor.destroy()	
		self.openContactsUI()
		
	def onselect_values(self, evt):
		w = evt.widget
		selection=w.curselection()
		try:
			self.selected_value = w.get(selection[0])		
			print(self.selected_value)
		except:
			pass	
		
	def onselect(self, evt):
		w = evt.widget
		selection=w.curselection()
		try:
			self.selected_person = w.get(selection[0])		
			print(self.selected_person)
			conf = self.manager.getConfig('social').get('contacts', {}).get(self.selected_person, {})
			self.values.delete(0, 'end')
			for item in conf:
				if item != 'name':
					self.values.insert('end', f"{item}: {conf.get(item)}")
			
		except:
			pass
	
	def newcontact(self):
		self.selected_person = None
		self.editcontact()
		
	def editcontact(self):
		self.closeContactsUI()
		self.editor = Toplevel()
		self.editor.protocol("WM_DELETE_WINDOW", self.closeEditorUI )
		self.editorprops = []
		self.editorvals = []
		conf = self.manager.getConfig('social').get('contacts', {}).get(self.selected_person, {})
		self.editor.title(conf.get('name', 'New Person'))
		
		name_label = Label(self.editor, text="Name", width=14)
		name_label.grid(column=0, row=0)
		self.name_entry = Entry(self.editor)
		self.name_entry.grid(column=1, row=0)
		
		if conf.get('name'):
			self.name_entry.insert(0, conf.get('name'))
		
		for key in conf:
			if key != 'name':
				le = Entry(self.editor, width=12)
				le.grid(column=0, row=len(self.editorprops)+1)
				le.insert(0, key)
				lv = Entry(self.editor)
				lv.grid(column=1, row=len(self.editorvals)+1)
				lv.insert(0, conf[key])
				self.editorprops.append(le)
				self.editorvals.append(lv)
			
		self.plus_lines = ttk.Button(self.editor, text="+", command=self.add_editor_line, width=2)
		self.plus_lines.grid(column=2, row=0)
		
		self.minus_lines = ttk.Button(self.editor, text="-", command=self.minus_editor_line, width=2)
		self.minus_lines.grid(column=3, row=0)	
		if len(conf) <= 1:
			self.minus_lines.config(state='disabled')
		self.savec = ttk.Button(self.editor, text="SAVE", command=self.save_contact, width=2)
		self.savec.grid(column=4, row=0)	
	
	def save_contact(self):
		data = {'name': self.name_entry.get()}

		for i in range(0, len(self.editorprops)):
			p = self.editorprops[i].get()
			v = self.editorvals[i].get()
			data[p] = v
		
		conf = self.manager.getConfig('social').get('contacts', {})
		#print(data)
		conf[data['name']] = data
		self.manager.getConfig('social')._set('contacts', conf)
		self.closeEditorUI()
		
	def add_editor_line(self):
		self.minus_lines.config(state="normal")
		le = Entry(self.editor, width=12)
		le.grid(column=0, row=len(self.editorprops)+1)
		lv = Entry(self.editor)
		lv.grid(column=1, row=len(self.editorvals)+1)
		self.editorprops.append(le)
		self.editorvals.append(lv)
		
	def minus_editor_line(self):
		try:
			self.editorprops[len(self.editorprops)-1].destroy()
			self.editorprops.pop()
			self.editorvals[len(self.editorvals)-1].destroy()
			self.editorvals.pop()
			if len(self.editorvals) == 0:
				self.minus_lines.config(state="disabled")
		except IndexError:
			pass
	
	def deletecontact(self):
		if self.selected_person:
			if self.manager.promptConfirm(f"Really delete contact {self.selected_person}?"):
				conf = self.manager.getConfig('social').get('contacts', {})
				del conf[self.selected_person]
				self.manager.getConfig('social')._set('contacts', conf)
				self.contactswin.destroy()
				self.openContactsUI()
				
	def openContactsUI(self):
		self.contactswin = Toplevel()
		self.contactswin.title("Contacts")
		self.manager.disableTool('Contacts')	
		people = Listbox(self.contactswin)
		people.grid(row=0, column=0, columnspan=2, rowspan=3, sticky="nswe")
		logWinScroll = Scrollbar(self.contactswin)
		logWinScroll.grid(column=2, row=0, sticky="ns", rowspan=3)
		logWinScroll.config(command=people.yview)
		people.config(yscrollcommand=logWinScroll.set)
		
		self.values = Listbox(self.contactswin)
		self.values.grid(row=0, column=3, columnspan=2, sticky="nswe", rowspan=3)
		logWinScroll2 = Scrollbar(self.contactswin)
		logWinScroll2.grid(column=5, row=0, sticky="ns", rowspan=3)
		logWinScroll2.config(command=self.values.yview)
		self.values.config(yscrollcommand=logWinScroll2.set)		
		
		ttk.Button(self.contactswin, text='Add Contact', command=self.newcontact).grid(column=6, row=0, sticky="nsew")
		ttk.Button(self.contactswin, text='Edit Contact', command=self.editcontact).grid(column=6, row=1, sticky="nsew")
		ttk.Button(self.contactswin, text='Delete Contact', command=self.deletecontact).grid(column=6, row=2, sticky="nsew")
		people.bind('<<ListboxSelect>>', self.onselect)	
		#self.values.bind('<<ListboxSelect>>', self.onselect_values)	
		self.contactswin.protocol("WM_DELETE_WINDOW", self.closeContactsUI )
		
		for item in self.manager.getConfig('social').get('contacts', {}):
			people.insert('end', item)
			
		self.contactswin.columnconfigure(0, weight=1)	
		self.contactswin.columnconfigure(1, weight=1)
		self.contactswin.columnconfigure(3, weight=1)	
		self.contactswin.columnconfigure(4, weight=1)	
		for i in range(0, 1):
			self.contactswin.rowconfigure(i, weight=1)		
