"""
Basic Client-side app for interacting with our replicated bulletin board service
"""

import streamlit as st
import random

ARTICLE_CACHE = list(range(100))

# Should probably store the set of servers in a file or something read in
SERVERS = [('', 9900+i) for i in range(9)] # DEFAULTS TO 9 REPLICAS
COORDINATOR = SERVERS[0]

# def connect(choice):
#     # Run connection code
#     # Opens a TCP connection to a server
#     c = Client(mode="TCP")    
#     addr = c.connect(choice) # Check syntax in original project
#     return c, addr

def connect(choice):
    print("New choice of server: ", choice)
    st.session_state["SERVER_CONNECTION"] = choice # This will be the actual client connection
    return

if __name__=="__main__":
    st.title("Welcome to *consequor*! :classical_building::card_index:")
    st.write("This is a simple bulletin board app backed by a distributed set of remote server replicas. These server replicas each maintain a set (possibly out of sync) of articles and replies to articles for a single topic. You can post your own, read a list of all article titles, and post replies to articles you've chosen to view.")

    side = st.sidebar
    num_articles = side.slider("num_articles_shown", 5, 20)

    # Add button for connection management (drop down, reconnects on new selection)
    choice = side.selectbox("connect", SERVERS) # DEFAULTS TO 0th SERVER

    if st.session_state.get("SERVER_CONNECTION") != choice:
        connect(choice) # Will return our client
    
    st.write(f"You are connected to the following server: {st.session_state['SERVER_CONNECTION']}")

    # Buttons for read (get list of articles), choose (selects from listed articles which to open?), post (make a new article and posts to server)

    # Show article list
    shown_articles = [st.container(height=100) for _ in range(num_articles)]

    for i,a in enumerate(shown_articles):
        a.write(f"Hi, I'm article # {i}!")