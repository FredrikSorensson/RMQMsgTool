# RMQMsgTool
A simple GUI to read and write RMQ messages.

## Introduction

This is a simple GUI to read, browse and write messages to RabbitMQ. 
It is very simple and not very resilient, but may prove useful

## Installation

It should start on a fairly basic installation of Python, but it
needs the "pika" RabbitMQ client librara. In most cases, an

  > pip install pika
  
  
should do the trick.

After that, it should start in the normal way you execute pyhton scripts
on your platform. On linux, do

 > ./rmqmsgtool.py 
 
with the script in the current directory.

## The GUI

The GUI is divided in 5 parts:

- Connection details - Here is where you tell what queuemanager to connect to
- Message header - Here is where you configure the message header details
- Message body - Here is where the message body is presented
- Actions - The actions that can be performed 
- Results - A log window of actions performed

## Browsing caveats

Note on browsing: The tool performs browsing, that is reading messages 
without removing them from the queue, using a simple trick. It
starts a transaction before reading the first message, keeps the 
transaction open, and then, when the entire queue is read or the
user clicks on "End Browse", the tool does an tx_rollback, meaning
that all messages will be rolled back to the queue. However,
no order is guaranteed, and the messages all have the redelivered flag
set. You have been warned.

