# SimpleClientServer :speech_balloon:

## Project 1 - Distributed Systems
Author: Ryan Hartzell
Date:   AUG 29 2024

NOTE: PLEASE RENDER THIS README AS MARKDOWN

## Description
This is a simple implementation of a Server and Client in Python which are allowed to communicate over sockets. My Server implementation supports both TCP and UDP communications simultaneously via socket selection. My Server is also single threaded but still reliable. All incoming and outgoing messages are chunked by default so that packet sizes stay manageable, and any meaningful (user generated) messages are restored to a contiguous message string prior to being pushed to the Server's Queue. Large (>3000byte) messages can be handled in either direction, and the next message off the Queue is guaranteed to only flow to one client.

## Setup 
My project has been tagged on Gitlab and packaged into a zip file. This zip file contains the following project structure:

* In the root of the project are the PDFs, this README (please render as markdown!), and several project files (LICENSE, .gitignore).
* The 'src' directory contains two python modules and a piece of test data in the form of a text file.
* 'core.py' contains all utilities for working with sockets and message packing, the Server implementation, and the Client implementation.
* 'cli.py' is a loose wrapper around the functionality in 'core.py', and provides a command line interface application for running various commands (described below).

This project was tested locally on my development laptop running Ubuntu 20.04 Focal and on isengard.mines.edu. My local development version of Python was 3.8.10, whereas the Python version on Isengard is also 3.8.10, and I only used the Python standard library for this project. Therefore there should already be everything you need to run this project on Isengard. Just unzip the archive in your folder of choice, navigate to the 'src' directory, and run the cli.py script. Details provided in the Usage section.

## Usage and Examples
The CLI application has pretty decent guardrails, and a complete --help command that should walk you through the different options. Mostly though this CLI follows the examples in the project description. 

All of the CLI functionality stems from this prefix:

```bash
python3.8 cli.py COMMAND ...
```

COMMAND should be one of `--help`, `--server`, or `--client`. The different options following each of these commands are as follows:

### `--help`
This command is a good starting point and will give pretty much the same info I'm listing here.

### `--server`
This command spawns the Server instance with active UDP and TCP ports on localhost. `TCP_PORT` and `UDP_PORT` must be integers that can be mapped to open ports on the host machine you're starting the server on. Once running, the Server will print diagnostics to std.out until it is exited with a CTRL-C keypress. Server instantiation command format:

```bash
python3.8 cli.py --server TCP_PORT UDP_PORT
```
Example:
```bash
python3.8 cli.py --server 54345 54346
```
### `--client`
Finally, the Client instantiation command should be run from its own terminal/shell each time it is invoked. The command always requires the user to provide a `HOST` and `PORT` (the target Server address), a `MODE` of communication (TCP or UDP), and a request type `REQUEST`. The CLI only keeps the client alive long enough to perform one of two sub-commands: `send` or `receive`. For the `send` request type, there are two extra arguments that can be provided, detailed below:

Generic command format.
```bash
python3.8 cli.py --client HOST PORT MODE REQUEST [...]
```

Example - Receive over TCP ('' denotes localhost). Note that you may receive a message about the Queue being empty if there are no messages available yet.
```bash
python3.8 cli.py --client '' 54345 TCP receive
```

Example - Receive over UDP (Note how the port number must match the appropriate socket address on the server for which communication mode you've specified)
```bash
python3.8 cli.py --client '' 54346 UDP receive
```

Example - Send command-line message over TCP
```bash
python3.8 cli.py --client '' 54345 TCP send --msg "Hello world! :D"
```

Example - Send command-line message over UDP
```bash
python3.8 cli.py --client '' 54346 UDP send --msg "Hello World 2: Electric Boogaloo!"
```

Example - Send a text file (works for either comm mode, and can be >3000 bytes)
```bash
python3.8 cli.py --client '' 54345 TCP send --file tester.txt
```


All of these examples will receive an ACK (acknowledgement message) from the Server, and possibly some low-footprint diagnostics.

Have fun!