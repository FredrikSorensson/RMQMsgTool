# RMQMsgTool
A simple GUI to read and write RMQ messages.

This is a simple GUI to read, browse and write messages to RabbitMQ. 
It is very simple and not very resilient, but may prove useful

It should start on a fairly basic installation of Python, but it
needs the "pika" RabbitMQ client librara. In most cases, an

  > pip install pika
  
  
should do the trick.

Note on browsing: The tool performs browsing using a simple trick. It
starts a transaction before reading the first message, keeps the 
transaction open, and then, when the entire queue is read or the
user clicks on "End Browse", the tool does an tx_rollback, meaning
that all messages will be rolled back to the queue. However,
no order is guaranteed, and the messages all have the redelivered flag
set. You have been warned.

