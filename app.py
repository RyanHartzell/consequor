"""
Basic Client-side app for interacting with our replicated bulletin board service
"""

from src.core import Client, Modes
from src.msg_utils import *
import streamlit as st
import random

TEST_TCP_SERVER_PORT = 54345

ARTICLE_CACHE = list(range(100)) # This will be part of the session state and updated on each read operation (choose interacts with this Cached set of articles?)

# Should probably store the set of servers in a file or something read in
# SERVERS = [('', 9900+i) for i in range(9)] # DEFAULTS TO 9 REPLICAS
SERVERS = [('localhost',TEST_TCP_SERVER_PORT+i) for i in range(9)]
COORDINATOR = SERVERS[0]

def connect(choice):
    print("Running connection code")
    # Opens a TCP connection to a server
    try:
        print(f"Attempting to connect to server at {choice}...")
        c = Client(choice[0], choice[1], mode=Modes.TCP)
        print(f"Connected to server using new TCP port:", c.socket)
        st.session_state["SERVER_CONNECTION"] = (choice, c) # This will be the actual client connection, if connection was successful
    except OSError as e:
        print(f'Could not connect to server at {choice}. Maybe it has not been initialized or has gone down?', e)

def disconnect(sock):
    sock.sendall(b'DEL')

# By default el is just the normal st context, otherwise our form is built on the given element el
def gen_reply_form(el=st, height=400):
    # st.session_state.counter += 1
    with el.form("Reply Form", clear_on_submit=False):
        title = None # Replies don't have a title field!
        reply = st.text_area("Format your reply to the post here.", height=height)
        submit = st.form_submit_button("Click me to post reply!")
        if submit:
            if not reply:
                st.error("Please fill out the reply box!!!")
            else:
                st.write(f"User {THIS_USER} replied: {reply}")

def gen_post_form():
    # st.session_state.counter += 1    
    with st.form('Post Form', clear_on_submit=False):
        title = st.text_input("Title of your post")
        post = st.text_area("Format your post here.", height=300)
        submit = st.form_submit_button("Click me submit your post!")
        if submit:
            if not post:
                st.error("Please fill out the post text box prior to clicking submit!!!")
            else:
                st.markdown(f"User *{THIS_USER}* created a post titled ***{title}***")


if __name__=="__main__":
    # Set up "login" page so each post has a username and address attached
    st.title("Welcome to *consequor*! :classical_building::card_index:")
    st.write("This is a simple bulletin board app backed by a distributed set of remote server replicas. These server replicas each maintain a set (possibly out of sync) of articles and replies to articles for a single topic. You can post your own, read a list of all article titles, and post replies to articles you've chosen to view.")
    if not st.session_state.get('counter'):
        st.session_state['counter'] = 0

    if not st.session_state.get('current_article'):
        st.session_state['current_article'] = 0 # First root article by default

    # 'Login' with username
    THIS_USER = st.text_input("Enter a username:")
    if THIS_USER:

        side = st.sidebar

        # Add button for connection management (drop down, reconnects on new selection)
        choice = side.selectbox("Connect to a new Server", SERVERS) # DEFAULTS TO 0th SERVER

        # Check client's server attribute, and if not equal to choice of format (HOST_ADDR, HOST_PORT), or is None, then connect
        client_state = st.session_state.get("SERVER_CONNECTION")
        if client_state is None:
            connect(choice)
        elif client_state[0] != choice:
            print(f"Currently connected to server {client_state[0]} via TCP socket at {client_state[1].socket}")
            # st.session_state["SERVER_CONNECTION"][1].kill_request() # This might be causing issues, so should look at explicitly disconnecting if possible (socket.close()?)
            connect(choice)
            print(f"Now connected to server {client_state[0]} via TCP socket at {client_state[1].socket}")

        # print("CURRENT STATE: ", st.session_state)
        
        st.write(f"You are connected to the following server: {st.session_state.get('SERVER_CONNECTION')}")

        # Try tabs instead!
        tabs = st.tabs(["[READ]", "[CHOOSE/REPLY]", "[POST]"])

        with tabs[0]:
            st.header("List All Primary Articles")
            st.write("This tab shows all articles which belong to the root topic thread, and are not replies.")

            # Init page num state variable
            if not "PAGE_NUM" in st.session_state:
                st.session_state["PAGE_NUM"] = 0

            with st.container(height=400):
                num_articles = st.slider("# Articles Shown", 5, 20)
                num_pages = (len(ARTICLE_CACHE) // num_articles) + 1 # ARTICLE_CACHE WILL COME FROM READS ON THE CONNECTED REPLICA

                # Add functionality to "page" through the articles?
                paging = st.columns(3)
                if paging[0].button(":arrow_backward:", use_container_width=True): # If clicked, add -1 to page_num, unless min page number
                    st.session_state["PAGE_NUM"] = min(st.session_state["PAGE_NUM"]-1, 0)
                if paging[1].button(":arrow_forward:", use_container_width=True): # If clicked, add 1 to page_num, unless max page number
                    st.session_state["PAGE_NUM"] = min(st.session_state["PAGE_NUM"]+1, num_pages)
                
                paging[2].write(f"Showing page {st.session_state['PAGE_NUM']} of {num_pages}")

                # Show article list
                shown_articles = [st.container(height=100) for _ in range(num_articles)]
                for i,a in enumerate(shown_articles):
                    a.write(f"Hi, I'm article # {i+st.session_state['PAGE_NUM']*num_articles}!")
        
        with tabs[1]:
            st.header("Focus One Article")

            # Maybe some navigation buttons here for going up a level? Every article should have a parent, unless it's 0 (root)
            article = st.selectbox("Choose an article from the dropdown:", ARTICLE_CACHE) # SHOULD ONLY ALLOW SELECTION OF ROOT ARTICLES INITIALLY, THEN ANY SUB ARTICLE CAN BE SELECTED!!!
            st.session_state["current_article"] = article

            if st.button('Change Focus to Parent Article'): # Trigger callback? Simply set article=parent and then st.rerun?
                st.write("I'd switch to displaying the parent article and its children instead here")
                st.session_state["current_article"] = 0 #article["parent"]

            choose_reply_cols = st.columns(2)
            with choose_reply_cols[0]:
                with st.container(height=500):
                    st.write(f"I selected article # {st.session_state['current_article']}")
            
            # Ensures that we only have a single reply form available!!!
            gen_reply_form(choose_reply_cols[1])
            
        with tabs[2]:
            st.header("Create A New Post")

            gen_post_form()

