#!/usr/bin/env python
# -*- Mode: Python; coding: utf-8; indent-tabs-mode: t; c-basic-offset: 4; tab-width: 4 -*- 
#
# rmqmsgtool.py
# Copyright (C) 2016 Fredrik Sörensson <fredrik@sorensson.se>
# 
# RMQMsgTool is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the
# Free Software Foundation,version 3 of the License.
# 
# RMQMsgTool is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License along
# with this program.  If not, see <http://www.gnu.org/licenses/>.

from Tkinter import *

import ast
import json
import os.path
import pika
import time
import tkFileDialog
import xml.dom.minidom
import zipfile


FILTER=''.join([(len(repr(chr(x)))==3) and chr(x) or '.' for x in range(256)])
def hexdump2(src):
	result=[]
	for i in xrange(0, len(src), 16):
		s1 = src[i:i+16]
		s2 = []
		for j in xrange(0, len(s1), 4):
			s2.append(' '.join(["%02X"%ord(x) for x in s1[j:j+4] ] ) )
		hexa = '  '.join(s2)
		printable = s1.translate(FILTER)
		result.append("%08X   %-*s   %s\n" % (i, 16*3+4, hexa, printable))
	return ''.join(result)


PROPERTIES=['content_type','content_encoding','priority','correlation_id','reply_to','expiration','message_id','timestamp','type',
	'user_id','app_id','cluster_id','delivery_mode']
def basProp2jsonStr( inBasProp ):
	myJson = {}
	for key in PROPERTIES:
		if hasattr (inBasProp, key):
			myJson[key] = getattr (inBasProp, key)
	return json.dumps(myJson)

def jsonStr2BasProp( inJson ):
	myBasProp = pika.BasicProperties()
	myJson = json.loads(inJson)
	for key in PROPERTIES:
		if key in myJson:
			setattr (myBasProp, key, myJson[key] )
	return myBasProp	

def entryWithLabel(inParent, text, lwidth, ewidth, row, column, defval):
	myLabel = Label(inParent, text = text, width = lwidth, anchor=W)
	myLabel.grid(row = row, column = column, sticky=W)
	myEntry = Entry(inParent, width= ewidth )
	myEntry.grid( row=row, column=column+1, sticky=W)
	myEntry.insert(END, defval)
	return myEntry

class MainWindow:

	def __init__(self, master):

		# Here we set up the main window
		master.title("RMQMsgTool v0.1")

		# Pre-defines
		self.properties = pika.BasicProperties()
		self.body = ''	
		vcmd = (master.register(self.valNum), '%d', '%i', '%P', '%s', '%S', '%v', '%V', '%W')
		
		# User interface setup starts heretest
		#
		# connectFrame with connection details
		self.connectFrame = LabelFrame(master, text = "Connection details", width=150)
		self.connectFrame.grid(row = 0, sticky = W+E)
		# Row 0
		self.hostEntry = entryWithLabel(self.connectFrame, "Host", 10, 30, 0, 0, '127.0.0.1')
		self.hostEntry.focus()
		self.portEntry = entryWithLabel(self.connectFrame, "Port", 10, 30, 0, 2, '5672')
		self.portEntry.config(validate = 'key', validatecommand = vcmd)
		self.vhostEntry = entryWithLabel(self.connectFrame, "Vhost", 10, 30, 0, 4, '/')
		# Row 1
		self.userEntry = entryWithLabel(self.connectFrame, "Username", 10, 20, 1, 0, 'guest')
		self.pwdEntry = entryWithLabel(self.connectFrame, "Password", 10, 20, 1, 2, 'guest')
		# Row 2
		# Queuename
		self.queueEntry = entryWithLabel(self.connectFrame, "Queuename", 10, 20, 2, 0, 'test')
		self.exchangeEntry = entryWithLabel(self.connectFrame, "Exchange", 10, 20, 2, 2, '')
		self.routingKeyEntry = entryWithLabel(self.connectFrame, "Routing key", 10, 20, 2, 4, 'test')

		# headerFrame with the message header stuff
		self.headerFrame = LabelFrame(master, text = "Message header")
		self.headerFrame.grid(row = 1, sticky=W+E)

		# Button row 0
		self.cthEntry = entryWithLabel(self.headerFrame, "content_type", 15, 20, 0, 0, '')
		self.cehEntry = entryWithLabel(self.headerFrame, "content_encoding", 15, 20, 0, 2, '')
		self.prhEntry = entryWithLabel(self.headerFrame, "priority", 15, 20, 0, 4, '')
		self.prhEntry.config(validate = 'key', validatecommand = vcmd)
		# Button row 1
		self.cohEntry = entryWithLabel(self.headerFrame, "correlation_id", 15, 20, 1, 0, '')
		self.rthEntry = entryWithLabel(self.headerFrame, "reply_to", 15, 20, 1, 2, '')
		self.exhEntry = entryWithLabel(self.headerFrame, "expiration", 15, 20, 1, 4, '')
		self.exhEntry.config(validate = 'key', validatecommand = vcmd)
		# Button row 2
		self.mihEntry = entryWithLabel(self.headerFrame, "message_id", 15, 20, 2, 0, '')
		self.tshEntry = entryWithLabel(self.headerFrame, "timestamp", 15, 20, 2, 2, '')
		self.tshEntry.config(validate = 'key', validatecommand = vcmd)
		self.tyhEntry = entryWithLabel(self.headerFrame, "type", 15, 20, 2, 4, '')
		# Button row 3
		self.uihEntry = entryWithLabel(self.headerFrame, "user_id", 15, 20, 3, 0, '')
		self.aihEntry = entryWithLabel(self.headerFrame, "app_id", 15, 20, 3, 2, '')
		self.cihEntry = entryWithLabel(self.headerFrame, "cluster_id", 15, 20, 3, 4, '')
		# Row 4
		self.dmhLabel = Label(self.headerFrame, text = "delivery_mode", width = 15, anchor="w")
		self.dmhLabel.grid(row = 4, column = 0)
		self.dmhChoices = [ '1 - Non-persistent', '2 - Peristent']
		self.dmhVar = StringVar()
		self.dmhVar.set(self.dmhChoices[0])
		self.dmhEntry = OptionMenu(self.headerFrame, self.dmhVar, *self.dmhChoices )
		self.dmhEntry.grid(row = 4, column = 1, sticky=W)
		
		# Row 5
		self.headerField = Text(self.headerFrame, height=5, width=100)
		self.headerField.grid(row=5, column=0, columnspan=6, sticky=W)
		self.headerField.config(state=DISABLED)
		
		# bodyFrame with the message body
		self.bodyFrame = LabelFrame(master, text = "Message body")
		self.bodyFrame.grid(row = 2, sticky=W+E)

		self.bodyScroll = Scrollbar(self.bodyFrame)	
		self.bodyField = Text(self.bodyFrame, height=30, width=100, yscrollcommand=self.bodyScroll.set)
		self.bodyScroll.config(command=self.bodyField.yview)
		self.bodyField.grid(row=0, column=0)
		self.bodyScroll.grid(row=0, column=1, sticky=N+S+W+E)
		self.bodyField.config(state=DISABLED)
		
		self.bPresFrame = LabelFrame(self.bodyFrame, text = "Parse as")
		self.bPresFrame.grid(row=0, column=2, sticky=N)

		self.radioVal = StringVar()
		self.rbt = Radiobutton(self.bPresFrame, text="Text", variable=self.radioVal, value="text", command=self.setBody )
		self.rbt.pack(anchor=W)
		self.rbt.select()
		self.rbh = Radiobutton(self.bPresFrame, text="Hex", variable=self.radioVal, value="hex", command=self.setBody )
		self.rbh.pack(anchor=W)
		self.rbx = Radiobutton(self.bPresFrame, text="XML", variable=self.radioVal, value="XML", command=self.setBody )
		self.rbx.pack(anchor=W)
		self.rbj = Radiobutton(self.bPresFrame, text="JSON", variable=self.radioVal, value="JSON", command=self.setBody )
		self.rbj.pack(anchor=W)

		# actionFrame with all the fun buttons
		self.actionFrame = LabelFrame(master, text = "Actions")
		self.actionFrame.grid(row = 3, sticky=W+E)

		self.get = Button(self.actionFrame, text = "Get", command=self.onGet)
		self.get.grid(row = 0, column = 0, sticky=W)
		self.startBrowse = Button(self.actionFrame, text = "Start Browse", command=self.onStartBrowse )
		self.startBrowse.grid(row = 0, column = 1, sticky=W)
		self.nextBrowse = Button(self.actionFrame, text = "Browse Next", command=self.onBrowseNext )
		self.nextBrowse.grid(row = 0, column = 2, sticky=W)
		self.endBrowse = Button(self.actionFrame, text = "End Browse", command=self.onEndBrowse )
		self.endBrowse.grid(row = 0, column = 3, sticky=W)
		self.put = Button(self.actionFrame, text = "Put", command=self.onPut)
		self.put.grid(row = 0, column = 4, sticky=W)
		self.load = Button(self.actionFrame, text = "Load", command=self.onLoad)
		self.load.grid(row = 0, column = 5, sticky=W)
		self.saveM = Button(self.actionFrame, text = "Save Message", command=self.onSaveMessage)
		self.saveM.grid(row = 0, column = 6, sticky=W)
		self.saveB = Button(self.actionFrame, text = "Save Body", command=self.onSaveBody)
		self.saveB.grid(row = 0, column = 7, sticky=W)
	
		self.quit = Button(self.actionFrame, text = "Quit", command=master.quit)
		self.quit.grid(row = 0, column = 8, sticky=W)
		self.quit = Button(self.actionFrame, text = "Clear", command=self.onClear)
		self.quit.grid(row = 0, column = 9, sticky=W)

		# resultFrame with a log of results
		self.resultFrame = LabelFrame(master, text = "Results")	
		self.resultFrame.grid(row = 4, sticky=W+E)

		self.resultScroll = Scrollbar(self.resultFrame)
		self.resultField = Text(self.resultFrame, height=4, width=100, yscrollcommand=self.resultScroll.set)
		self.resultScroll.config(command=self.resultField.yview)
		self.resultField.grid(row=0, column=0)
		self.resultScroll.grid(row=0, column=1, sticky=N+S+W+E)
		self.resultField.config(state=DISABLED)
		#
		# User Interface setup stops here

	def valNum(self, action, index, value_if_allowed, prior_value, text, validation_type, trigger_type, widget_name):
		if(action=='1'):
			if text in '0123456789':
				return True
			else:
				return False
		else:
			return True	
		
		
	# Ugly header management
	#
	# Set the header fields from the buffered properties field
	def setHeader(self):
		self.headerField.config(state=NORMAL)
		self.headerField.delete(1.0, END)
		self.headerField.insert(END, self.properties )
		self.headerField.config(state=DISABLED)		

		self.cthEntry.delete(0, END)
		if self.properties.content_type:
			self.cthEntry.insert(END, self.properties.content_type )

		self.cehEntry.delete(0, END)
		if self.properties.content_encoding:
			self.cehEntry.insert(END, self.properties.content_encoding )

		self.prhEntry.delete(0, END)
		if self.properties.priority:
			self.prhEntry.insert(END, self.properties.priority )
			
		self.cohEntry.delete(0, END)
		if self.properties.correlation_id:
			self.cohEntry.insert(END, self.properties.correlation_id )

		self.rthEntry.delete(0, END)
		if self.properties.reply_to:
			self.rthEntry.insert(END, self.properties.reply_to )

		self.exhEntry.delete(0, END)
		if self.properties.expiration:
			self.exhEntry.insert(END, self.properties.expiration )

		self.mihEntry.delete(0, END)
		if self.properties.message_id:
			self.mihEntry.insert(END, self.properties.message_id )

		self.tshEntry.delete(0, END)
		if self.properties.timestamp:
			self.tshEntry.insert(END, self.properties.timestamp )

		self.tyhEntry.delete(0, END)
		if self.properties.type:
			self.tyhEntry.insert(END, self.properties.type )

		self.uihEntry.delete(0, END)
		if self.properties.user_id:
			self.uihEntry.insert(END, self.properties.user_id )

		self.aihEntry.delete(0, END)
		if self.properties.app_id:
			self.aihEntry.insert(END, self.properties.app_id )

		self.cihEntry.delete(0, END)
		if self.properties.cluster_id:
			self.cihEntry.insert(END, self.properties.cluster_id )

		# Deliv mode
		if self.properties.delivery_mode:
			self.dmhVar.set(self.dmhChoices[self.properties.delivery_mode -1])
			
	# Sync the properties buffer from the fields
	def updateHeader(self):

		self.properties.content_type = None
		if self.cthEntry.get():
			self.properties.content_type = self.cthEntry.get()

		self.properties.content_encoding = None
		if self.cehEntry.get():
			self.properties.content_encoding = self.cehEntry.get()

		self.properties.priority = None	
		if self.prhEntry.get():
			self.properties.priority = int(self.prhEntry.get())

		self.properties.correlation_id = None
		if self.cohEntry.get():
			self.properties.correlation_id = self.cohEntry.get()

		self.properties.reply_to = None
		if self.rthEntry.get():
			self.properties.reply_to = self.rthEntry.get()

		self.properties.expiration = None
		if self.exhEntry.get():
			self.properties.expiration = self.exhEntry.get() 

		self.properties.message_id = None
		if self.mihEntry.get():
			self.properties.message_id = self.mihEntry.get()

		self.properties.timestamp = None
		if self.tshEntry.get():
			self.properties.timestamp = float(self.tshEntry.get())

		self.properties.type = None
		if self.tyhEntry.get():
			self.properties.type = self.tyhEntry.get()

		self.properties.user_id = None
		if self.uihEntry.get():
			self.properties.user_id = self.uihEntry.get()

		self.properties.app_id = None
		if self.aihEntry.get():
			self.properties.app_id = self.aihEntry.get()

		self.properties.cluster_id = None
		if self.cihEntry.get():
			self.properties.cluster_id = self.cihEntry.get()

		# Deliv mode
		if self.dmhVar.get():
			dm = self.dmhVar.get()
			self.properties.delivery_mode = int(dm[0:1])

	# Presentation 
	#
	# Add a line to the result log
	def addResult(self, message):
			self.resultField.config(state=NORMAL)
			self.resultField.insert(END, message)
			self.resultField.see(END)
			self.resultField.config(state=DISABLED)		
			
	# Present the body
	def setBody(self):
		self.bodyField.config(state=NORMAL)
		self.bodyField.delete(1.0, END)
		if self.radioVal.get() == 'hex':
			self.setBodyHex()
		elif self.radioVal.get() == 'XML':
			self.setBodyXML()
		elif self.radioVal.get() == 'JSON':
			self.setBodyJSON()
		else:
			self.setBodyText()			
		self.bodyField.config(state=DISABLED)		

	# Various presentations of the body
	def setBodyText(self):
		self.bodyField.insert(END, self.body.replace('\r\n','\n') )

	def setBodyHex(self):
		self.bodyField.insert(END, hexdump2(self.body) )
	
	def setBodyXML(self):
		try:
			self.bodyField.insert(END, xml.dom.minidom.parseString(self.body).toprettyxml(indent="    ") )
		except xml.parsers.expat.ExpatError, e:
			self.bodyField.insert(END, '*** Not an XML message' )
			
	def setBodyJSON(self):
		try:
			self.bodyField.insert(END, json.dumps(json.loads(self.body), indent=4) )
		except ValueError, e:
			self.bodyField.insert(END, '*** Not a JSON message' )

	# Button actions
	# Get
	def onGet(self):
		self.params = pika.ConnectionParameters(
				host=self.hostEntry.get(),
    			port=int( self.portEntry.get() ),
	 			virtual_host=self.vhostEntry.get(),
    			credentials=pika.credentials.PlainCredentials(self.userEntry.get(), self.pwdEntry.get()),
			)
		try:
			self.getConnection = pika.BlockingConnection(self.params)
		except pika.exceptions.ConnectionClosed as e:
			self.addResult( "ERR: Could not connect to host %s port %s\n" % ( self.hostEntry.get(), self.portEntry.get() ) )
			return
		except pika.exceptions.ProbableAuthenticationError as e:
			self.addResult( "ERR: Could not connect, wrong credentials\n")
			return			
		except pika.exceptions.ProbableAccessDeniedError as e:
			self.addResult( "ERR: Could not connect, wrong vhost or authorization error\n")
			return			
		except:
			self.addResult("ERR: Unexpected error\n" )
			return

		self.channel = self.getConnection.channel()
		
		try:
			self.method_frame, properties, body = self.channel.basic_get(self.queueEntry.get())
		except pika.exceptions.ChannelClosed as e:
			self.addResult("ERR: Could not get message. Error %s - %s\n" % (e.args[0], e.args[1]) )
			return
			
		if self.method_frame:
			# I've got a message, save it and let's present it
			self.body = body
			self.properties = properties
			self.setHeader()
			self.setBody()

			# Ack and be out
			self.channel.basic_ack(self.method_frame.delivery_tag)
			self.channel.close()
			self.getConnection.close()

			self.addResult("Got message (%d bytes), %d left in queue\n" % ( len(self.body), self.method_frame.message_count) )	
		else:
			self.addResult("Could not get message from queue, queue empty.\n")
		
	# Start Browse
	def onStartBrowse(self):

		# Set up connection
		self.params = pika.ConnectionParameters(
				host=self.hostEntry.get(),
    			port=int( self.portEntry.get() ),
	 			virtual_host=self.vhostEntry.get(),
    			credentials=pika.credentials.PlainCredentials(self.userEntry.get(), self.pwdEntry.get()),
			)

		try:
			self.getBrowseConnection = pika.BlockingConnection(self.params)
		except pika.exceptions.ConnectionClosed as e:
			self.addResult( "ERR: Could not connect to host %s port %s\n" % ( self.hostEntry.get(), self.portEntry.get() ) )
			return
		except pika.exceptions.ProbableAuthenticationError as e:
			self.addResult( "ERR: Could not connect, wrong credentials\n")
			return				
		except pika.exceptions.ProbableAccessDeniedError as e:
			self.addResult( "ERR: Could not connect, wrong vhost or authorization error\n")
			return			

		self.browseChannel = self.getBrowseConnection.channel()
		self.browseChannel.tx_select()

		# Browse message
		try:
			self.method_frame, properties, body = self.browseChannel.basic_get(self.queueEntry.get())
		except pika.exceptions.ChannelClosed as e:
			self.addResult("ERR: Could not get message. Error %s - %s\n" % (e.args[0], e.args[1]) )
			return
			
		if self.method_frame:
			# I've got a message, let's present it
			self.body = body
			self.properties = properties
			self.setHeader()
			self.setBody()

			# Inform user
			self.addResult("Browsed message (%d bytes), %d left in queue\n" % ( len(self.body), self.method_frame.message_count) )	

			# Disable Get and Browse to reduce the possibility of mixups
			self.get.config(state=DISABLED)
			self.startBrowse.config(state=DISABLED)

		else:
			self.addResult("Could not get message from queue, queue empty.\n")
			self.onEndBrowse()

	# Browse next
	def onBrowseNext(self):
		if hasattr(self, 'browseChannel'):
			if self.browseChannel.is_open: 
				# Browse next message
				try:
					self.method_frame, properties, body = self.browseChannel.basic_get(self.queueEntry.get())
				except pika.exceptions.ChannelClosed as e:
					self.addResult("ERR: Could not get message. Error %s - %s\n" % (e.args[0], e.args[1]) )
					self.onEndBrowse()
					return
				if self.method_frame:
					# I've got a message, let's present it
					self.body = body
					self.properties = properties
					self.setHeader()
					self.setBody()

					# Inform user
					self.addResult("Browsed message (%d bytes), %d left in queue\n" % ( len(self.body), self.method_frame.message_count) )	
				else:
					self.addResult("Could not get message from queue, queue empty.\n")
					self.onEndBrowse()
		
	# End browse
	def onEndBrowse(self):
		# Reset buttons
		self.get.config(state=NORMAL)
		self.startBrowse.config(state=NORMAL)

		if self.browseChannel.is_open: 
			# Rollback connection
			self.browseChannel.tx_rollback()
			self.browseChannel.close()
			self.getBrowseConnection.close()	

			# Inform user   
			self.addResult("Queue closed, messages rolled back\n")

	# Put message
	def onPut(self):
		self.params = pika.ConnectionParameters(
				host=self.hostEntry.get(),
    			port=int( self.portEntry.get() ),
	 			virtual_host=self.vhostEntry.get(),
    			credentials=pika.credentials.PlainCredentials(self.userEntry.get(), self.pwdEntry.get()),
			)
		try:
			self.getConnection = pika.BlockingConnection(self.params)
		except pika.exceptions.ConnectionClosed as e:
			self.addResult( "ERR: Could not connect to host %s port %s\n" % ( self.hostEntry.get(), self.portEntry.get() ) )
			return
		except pika.exceptions.ProbableAuthenticationError as e:
			self.addResult( "ERR: Could not connect, wrong credentials\n")
			return
		except pika.exceptions.ProbableAccessDeniedError as e:
			self.addResult( "ERR: Could not connect, wrong vhost or authorization error\n")
			return			
		self.channel = self.getConnection.channel()
		self.updateHeader()

		# Publish to what's configured
		try:
			self.channel.basic_publish(exchange=self.exchangeEntry.get(), routing_key=self.routingKeyEntry.get(), body = self.body, properties = self.properties )
			self.channel.close()
		except pika.exceptions.ChannelClosed as e:
			self.addResult("ERR: Could not put message. Error %s - %s\n" % (e.args[0], e.args[1]) )
			return
		self.getConnection.close()
		self.addResult("Message posted (%d bytes).\n" % len(self.body) )

	# Load Message
	def onLoad(self):
		self.filename = tkFileDialog.askopenfilename(title = 'Load message...')
		if os.path.isfile(self.filename):
			# Here we check if zip-file
			if zipfile.is_zipfile(self.filename):
				# We load zipfile
				with zipfile.ZipFile(self.filename, 'r') as self.zf:
					self.zfList = self.zf.namelist()
					if 'RMQToolVer' in self.zfList:
						self.body = self.zf.read('body')
						self.properties = jsonStr2BasProp(self.zf.read('properties'))	
						self.properties.headers = ast.literal_eval(self.zf.read('headers'))
						self.addResult("File %s read (%d bytes) with message headers.\n" % (self.filename, len(self.body) ) )
					else:
						# It is a ZIP file but doesn't have any magic marker, so load it as a file
						with open(self.filename, mode='rb') as file: 
							self.body = file.read()
						self.properties = pika.BasicProperties()
						self.addResult("File %s read (%d bytes).\n" % (self.filename, len(self.body) ) )
			# We load regular file
			else:
				with open(self.filename, mode='rb') as file: 
					self.body = file.read()
				self.properties = pika.BasicProperties()	
				self.addResult("File %s read (%d bytes).\n" % (self.filename, len(self.body) ) )
			self.setHeader()
			self.setBody()				

		else:	
			self.addResult("File not read.\n")
		
	# Save Body
	def onSaveBody(self):
		self.updateHeader()
		self.filename = tkFileDialog.asksaveasfilename(title = 'Save body as...')
		if self.filename:
			with open(self.filename, "wb") as file:
				file.write(self.body)
			self.addResult("File %s written (%d bytes).\n" % (self.filename, len(self.body) ) )
		else:	
			self.addResult("File not saved.\n")		

	# Save Message
	def onSaveMessage(self):
		self.updateHeader()
		self.filename = tkFileDialog.asksaveasfilename(title = 'Save body as...')
		if self.filename:
			self.zf = zipfile.ZipFile(self.filename, mode='w')
			self.zf.writestr('properties', basProp2jsonStr (self.properties))
			self.zf.writestr('headers', str(self.properties.headers) )
			self.zf.writestr('body', self.body)
			self.zf.writestr('RMQToolVer', 'v1.0') 
			self.zf.close()
			self.addResult("File %s written (%d bytes in body).\n" % (self.filename, len(self.body) ) )
		else:	
			self.addResult("File note saved.\n")

	# Clear
	def onClear(self):
		self.properties = pika.BasicProperties()
		self.setHeader()
		self.body = ''
		self.setBody()	
		self.addResult("Cleared all data.\n")

			
# Main is here
root = Tk()
app = MainWindow(root)
root.mainloop()
root.destroy() # optional; see description below
