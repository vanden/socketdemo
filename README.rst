===========
SOCKET DEMO
===========

This document has the following sections:

1. Overview
2. Installation
3. Requirements
4. Bugs
5. Design Decisions


OVERVIEW
========

The files provide a simple POC of a socket server and client. The client
sends messages to the server from the terminal. The server logs the
messages (as structured JSON log entries with timestamp and source
address information), echos the message to its terminal, and returns the
entire message to the client. The host, port, and logfile location are
all determined by environment variables, or, failing that, configuration
file values. On the first run of either the client or the server, a
default configuration file is created if one does not already exist.

That's all.


INSTALLATION
============

There is no setup.py and no need for a virtual environment. Clone the
git repository and you will have the needed files, ready to run.

On first run of either server.py or client.py, a default-valued local
config file serverconf.ini will be created.

To run the client and server, open two terminals, change into the cloned
git repositories directory in both. In one, run ``python3 server.py``
and in the other ``python3 client.py``. (If your system is configured so
that the default python is python3, then run ``python server.py`` and
``python client.py`` instead.) Then, in the client terminal, type some
text and hit Enter. Repeat. In either terminal, hit Crtl-C to shutdown
the respective program. In the client terminal, you can also send an
empty msg (just hit enter as distinct from hitting the space-bar then
enter) to shutdown the client.


REQUIREMENTS
============

Only packages from the Python standard library are used.

It was developed against Python 3.7.2. But, while not tested with
earlier versions, it should almost certainly work with any Python 3.7.x
and in all likelihood any 3.6.x or even 3.5.x. But, no warranties.

It will not, however, work with Python 2.x. It probably could be made to
work with Python 2.7.x fairly easily (the chief block is the print
function, which can be imported from future), but I haven't bothered to
try.


BUGS
====

Yes.

There are three major ones:

1. There are no unit tests. This is a bad bug. But, in the context, it
   seemed better to write solid manually tested code than to write unit
   tests, especially as the context of the code would have required a
   fair bit of mocking. This wouldn't be acceptable for production code,
   but might be acceptable for POC code such as this.
2. If the server is terminated, the client continues to wait for input
   from the user. Only when that input is provided does the client
   proceed, notice that the server is down, inform the user, and halt.
   This wouldn't be acceptable for real code as it would both be quite
   annoying and could also lead to data loss (client sends a message
   which is dropped on the floor).
3. If the server already has a client connected, a second client
   attempting to connect is not loudly rejected. Instead, it seems to
   accept user input, but then falls over after a timeout.

There is at least one minor one:

1. Both config.Config and server._main allow envars to over-ride
   configured values from the config file. This is bad design as
   eliminating the over-ride from one place will not have the expected
   effect. Ultimately, it probably should be that the over-ride is in
   config.Config alone (thus visible to both the Client and the Server).
   But, I'm out of cycles to fix it.


DESIGN DECISIONS
================

The code is object oriented. There is no pressing need for that. In fact
the first spike was procedural. The main reason I went object oriented
is that function signatures were becoming uncomfortably long; the
object's namespacing allowed for more readable code.

The server is configured to immediately relauch a socket at its
configured address when a client closes the connection. This allows the
immediate creation of another client without the delay that the default
timeout before reuse of the socket address would cause.

As indicated in the BUGS section, I favoured solid, readable code for
the single-active client at a time POC, rather than spending the time on
multiple active clients at the cost of lesser code quality. Were this
more than a POC, that would be the wrong choice. But, as the point
seemed to me to be to given an impression of what sort of code I write,
in the context, better code of lesser scope seemed correct. That is
also why there are no tests.

There is perhaps some small interest in the way config.py was designed.
It ensures that a default-valued config file is present on disk in the
working directory when it is first run. It also allows envars to
override the values it finds in the config file.

A possible design bug is the use of a threaded LogWorker to take
messages from the Server on a queue.queue for writing to the log file.
This was done both to minimize the impact of IO-bound blocking and
because I originally had a design idea involving more threads. (That
idea didn't prove well-conceived and insofar as the design is a product
of it, it is a design bug.)
