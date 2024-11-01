"""
CLI app for running Simple Client/Server utilities.

    Provides command line interface for:
        - Creating a Server (UDP+TCP by default!)
        - Creating Client instances in either UDP or TCP mode
        - Sending or receiving messages via Client instances
"""

__author__="Ryan Hartzell"
__email__="ryan_hartzell@mines.edu"
__copyright__="Copyright Ryan Hartzell, AUG 29 2024"

# Imports
import sys
from core import Client, Server, Modes

HELP_STRING = """
Help for `cli.py`:

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

"""

if __name__=="__main__":
    args = sys.argv
    print(args)

    if len(args) < 2:
        print(HELP_STRING)
        raise ValueError("Too few arguments. Exiting now...")

    # CLI logic
    if args[1].lower()=='--server':
        # Get other args
        try:
            tcp_port = int(args[2])
            udp_port = int(args[3])
        except:
            print(HELP_STRING)
            raise ValueError(f"One or both PORT args could not be converted to an integer. See 'help' via `python cli.py --help`.")

        # Do server stuff
        server = Server('', tcp_port, udp_port)
        print("TCP: ", server.tcp_socket)
        print("UDP: ", server.udp_socket)
        print("* Serving forever... CTRL-C to exit.")
        server.run()

    elif args[1].lower()=='--client':
        # Get other args
        if len(args) < 6:
            print(HELP_STRING)
            raise ValueError("Incorrect number of args provided for mode '--client'. See 'help' via `python cli.py --help`.")
        
        # server addr
        addr = args[2]

        # server port        
        try:
            port = int(args[3])
        except:
            print(HELP_STRING)
            raise ValueError(f"PORT=<{args[3]}> could not be converted to an integer. See 'help' via `python cli.py --help`.")
        
        # comm mode
        if args[4].upper() not in ['TCP', 'UDP']:
            print(HELP_STRING)
            raise ValueError(f"<MODE> must be one of 'TCP' or 'UDP'. See 'help' via `python cli.py --help`.")
        else:
            mode = Modes.TCP if args[4].upper()=='TCP' else Modes.UDP
        
        # Do client stuff
        client = Client(addr, port, mode)

        # SEND / PUT
        if args[5].lower() == 'send':
            if len(args) < 8:
                print(HELP_STRING)
                raise ValueError("Incorrect number of args provided for mode '--client' with 'send' request. See 'help' via `python cli.py --help`.")

            if args[6]=='--msg':
                # Handle sending the argument as is via client
                print(client.put_request(args[7]))

            if args[6]=='--file':
                fname = args[7]
                with open(fname, 'r') as f:
                    msg = ''.join(f.readlines())
                print(client.put_request(msg))

        # RECEIVE / GET
        elif args[5].lower() in ['receive', 'recieve']: # including incorrect spelling because I do it literally all the time
            print(client.get_request())

        else:
            print(HELP_STRING)
            raise ValueError("Request must be either 'send' or 'receive'. Feel free to try again! Exiting...")

        # Finally, signal server to clean client instance and its TCP connection up, if TCP.
        if mode == Modes.TCP:
            print(client.kill_request())
            del client

    elif args[1].lower()=='--help':
        print(HELP_STRING)