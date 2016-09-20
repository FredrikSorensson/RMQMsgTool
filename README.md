# RMQMsgTool
A simple GUI to read and write RMQ messages.

## Introduction

This is a simple GUI to read, browse and write messages to RabbitMQ. 
It is very simple and not very resilient, but may prove useful. It is not 
optimized in any way, and probably has problems with large messages. The Hex
viewer (see below) most definately won't handle data larger than 16MB, but the
tool will probably be unstable long before that.

## Installation

It should start on a fairly basic installation of Python, but it
needs the "pika" RabbitMQ client library. In most cases, an

  > pip install pika
  
  
should do the trick.

After that, it should start in the normal way you execute pyhton scripts
on your platform. On linux, do

 > ./rmqmsgtool.py 
 
with the script in the current directory. In windows, clicking on the script in a file
explorer may work. Otherwise, just run it from the command line. 

## The GUI

The GUI is divided in 5 parts:

- Connection details - Here is where you tell what queuemanager to connect to
- Message header - Here is where you configure the message header details
- Message body - Here is where the message body is presented
- Actions - The actions that can be performed 
- Results - A log window of actions performed

### Connection details

Here are all the usual conenction details. Not that you configure queues to read from
and exchanges to publish to separately.

### Message headers

Here you can view and manipulate the message headers. You can set all the  
message properties that RabbitMQ is aware of, like priotiry, expiry and delviery mode.
You can view the solution defined message headers, but you can't modify them (yet).

The main text view widget presents a raw python dump of the message headers structure. It
should be possible to understand even without knowledge of python.

### Message body

Here you view the message body. The viewer can present the message body in a few 
different ways, with different parsers. The radiobutton "Parse as" selects how to present
the data. The data is not changed by the presenter, only the way it is viewed.

**Text** - The data is presented as text. *Note!* The text renderer stops at the first instance
of a NULL character, so only partial data may be presented.

**Hex** - The data is presented in a Hexdump format. Sixteen bytes of data is presented per
line. Each line starts with the position, in hexadecimal notation, of the first byte of
the line. Then the data is presented in hex notation, with four groups of four bytes. 
Last, the data is presented as printabled characters. Non-printable characters are replaced
with dots, ".".

**XML** - The data is presented in XML. An effort is made to indent the data using the standard
minidom library, but the reslut may vary. If the data is not recognized as XML an error message
will be presented instead. 

**JSON** - The data is presented in JSON. An effort is made to indent the data using the standard
json library. If the data is not recognized as JSON an error message will be presented instead. 

### Actions

Here are a number of buttons for various actions.
 
**Get** - Get a message from the queue. *Note!* This is a destructive action, it reads the first
message.

**Start Browse** - Start a transacton and get the first message from the queue. Since the messages
are read under a transaction without acking, they are requeued when the transaction is broken, 
implementing a sort of non-destructive read. However, see the section below on browsing. When a
browse is started, the *Get* and *Start browse* buttons are disabled, to try to limit the 
confusion on how messages are consumed.

**Browse Next** - Browse the next message from the queue. If there are no messages left on queue,
the transaction is broken and all outstanding messages are requeued.

**End Browse** - Break the transaction and requeue all outstanding messages.

**Put** - Post message to the given exchange with the given routing key. The message is put with
the given message headers, both properties and solution defined headers, and the actual message
body. The message body presentation does not affect what is posted. Does not check if a message
is actually routed to a queue.

**Load** - Load message from file system. The Load fuction determines whether you load a full 
message with message headers as saved by the "Save Message" function, or if you load just data
to be used as message body. The message header is cleared, however, even if the data is loaded
without message headers. See below for information on the message save file format.

**Save Message** - The message is saved, both message headers and message body. It may be loaded 
again uysing the Load function.

**Save Body** - Save only the message body/payload to a file.

**Quit** - Exit the GUI. Any outstanding browse operation will be broken and rolled back.

**Clear** - Clear the message headers and the message body buffers. 

## Save file format

When saving the message with the Save Message function, the message is saved to a certain file
format. The format is simply a ZIP archive where each of message headers, message properties
and message body is saved to individual files called "headers", "properties" and "body".
A fourth file in the ZIP file called "RMQToolVer" is used to determine whether the ZIP file
is an actual RMQ Tool save file. So you can load ZIP files and post them as normal data too. :-)

You don't have to name the file in any certain way. The load function will try identify each file
as a ZIP file before falling back to just load the file as a message body. You can create message
save files outside RMQMsgTool, but beware that the load function only does a limited amount of
error handling, so it is very easy to make it confused and crash. 

You can use any ZIP utility to view and extract the data from the message save file. You might
have to rename the file with a .zip extension. 

## Browsing caveats

Note on browsing: The tool performs browsing, that is reading messages 
without removing them from the queue, using a simple trick. It
starts a transaction before reading the first message, keeps the 
transaction open, and then, when the entire queue is read or the
user clicks on "End Browse", the tool does an tx_rollback, meaning
that all messages will be rolled back to the queue. However,
no order is guaranteed, and the messages all have the redelivered flag
set. 

When browsing, the messages under transaction control seem to be loaded 
in the primary memory of the queuemanager. You can't have a larger 
transaction than the queuemanagers primary memory, it seems. When the 
memory requirements of the transaction exceeds the available primary 
memory of the queuemanager, something seems to crash. The good news is 
that the transcation is  properly broken and rolled back, so no data is lost.
Probably.

You have been warned.
