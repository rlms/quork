Overview
========

Quork is a text based shooter (Quork = Quake + Zork), inspired by xkcd 91:
![xkcd 91](http://imgs.xkcd.com/comics/pwned.png)

You control your character like in classic text based adventure games - `go north`, `look west` etc.
However, the gameplay revolves around finding other players, and doing `aim player_name`, `fire`, `fire`, `fire`, `fire`, `fire` before they can.

This repo contains both the server used to host the game, and the clients used to connect to it.
The source code is available, and if the client is updated to have a more user friendly interface, packages will be created for it.

So far, there are no permanent servers for the game, so you are limited to playing it over a LAN (or VPN).
If someone with a spare server wants to host a few games, that would be great.

Running a server
================

To run a server, download one of the archives (`quork_server.zip` or `quork_server.tar.gz`).
Extract it somewhere, and run

FAQ
===

No questions have been frequently asked yet.

Contribution
============

For anyone who wants to contribute code, but doesn't have any particular ideas as to what, here are some updates that I think would be good:

* Improved client - a GUI would be good, to avoid the awkward use of `KeyboardInterrupt` to allow input.
* Extra weapons
* Extra verbs
* Other objects in the game
* Different game modes
* Computer controlled enemies

You do not need any programming knowledge to create new maps, so anyone could do that.

Dependencies
============

Both the server and the client require Python 3.x, although the client could easily be rewritten to use something else.
I find it is easier to play the game from IDLE, rather than the command line.

The server also uses the `enum` module.
Although it may still run without it, unexpected behaviour is likely to occur.
It is recommended that you either use Python 3.4, or install the `enum` module, with `$ pip install enum34`.

The software has only been tested on Windows, but it should work on other operating systems.