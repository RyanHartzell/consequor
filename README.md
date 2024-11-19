# consequor
A simple  bulletin board app using CONsistent, SEQuential, QUORum-based resource replication strategy.

The name of this repo means "to follow, catch up with, or follow up", lending to the goal of synchronized resource replication between servers.

## Authors
Matt Desaulniers and Ryan Hartzell

## Overview
This library contains a client web application and a Replica server class which can be instantiated upwards of 5000 instances! Writes and Reads are guaranteed to be safe via sequential consistency, quorum-based consistency, and read-your-write consistency methods, as chosen by a user upon replica server instantiation. Likewise, a user may open multiple clients and connect dynamically to any available replica on a local network and submit 5 primary public API requests: READ, POST, CHOOSE, REPLY, and SYNC. Note that sync is not automatically performed in any mode except read-your-write, which implements a local-write, total sync-on-read approach. Sequential mode has no need for synchronization as all articles are assigned a monotonically sequential ID by a coordinator node in the network, and all reads and writes are broadcast to all replicas in the network. Finally, if the coordination node in the replica network goes down, this will be detected and a new leader will be elected dynamically, with the new leader (backup) having been synced to the state of the coordinator node during runtime. Since the coordinator syncs with the backup replica on every sequential ID draw, and blocks for ack, we are guaranteed that the id will be unique and incremented and robust to coordinator failure.

## Installation
In either Linux or Windows, having installed python3.8>= (replacing the 3.X below with your major.minor revision python version):

```bash
git clone "https://github.com/RyanHartzell/consequor.git" && cd consequor
python3.X -m venv venv
```
Activate your virtual environment and install 
```bash
source venv/bin/activate    # Windows:   .\venv\Scripts\activate
pip install -r requirements.txt
```

Now you should be ready to run *consequor*!

## How-to
To run the client app:

```bash
source venv/bin/activate    # Windows:   .\venv\Scripts\activate
cd ~/consequor/src
streamlit run app.py
```

The streamlit command will open a page on your browser which will allow you to interface with a predefined set of 3 replicas, although the script at the bottom of *replica.py* should allow for easy editing to accomodate any number of replicas, perhaps run via a for loop and subprocess. In fact, if running without the graphical UI client application, you can use *fake_client.py* as a model for how to do this. To use the client application properly with ANY replica address, you MUST edit the constant *TEST_CONNECTIONS_LIST* to include all known addresses which can then be selected from and connected to in the web client.

To set up the replicas, run the following commands in separate terminals, once per replica:

```bash
source venv/bin/activate    # Windows:   .\venv\Scripts\activate
cd ~/consequor/src
python replica.py <ID> <MODE>
```

The "\<ID>" parameter can be any unsigned integer (only 0,1,2 allowed for the current example code) and "\<MODE>" parameter can take values in ["sequential", "quorum", "read-your-write"], controlling the flow of the program for consistency purposes.

At this point, all terminals with replicas should be up and show that they are connected and listening, and the streamlit app should display a user login. Enter a username, and you will be default connected to the coordinator node of the network. The server can be changed at any time as we use an ephemeral connection approach to TCP comms with the replica network. At any time, connecting to any replica in the network, a user may submit READ, POST, CHOOSE, REPLY, or SYNC requests via the interfaces presented on the various sub pages of the web client app. Have fun and explore ***consequor***!