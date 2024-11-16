"""
Basic Client-side app for interacting with our replicated bulletin board service
"""

from core import create_client, Modes
from msg_utils import *
import streamlit as st
from replica import TEST_CONNECTION_LIST
import random

# st.session_state["ARTICLES"] = list(range(100)) # This will be part of the session state and updated on each read operation (choose interacts with this Cached set of articles?)

# Should probably store the set of servers in a file or something read in
# SERVERS = [('', 9900+i) for i in range(9)] # DEFAULTS TO 9 REPLICAS
# SERVERS = [('localhost',TEST_TCP_SERVER_PORT+i) for i in range(9)]

SERVERS = TEST_CONNECTION_LIST

def connect(choice):
    print("Running connection code")
    # Opens a TCP connection to a server
    try:
        print(f"Attempting to connect to server at {choice}...")
        c = create_client(choice[0], choice[1], mode=Modes.TCP, block=True)
        print(f"Connected to server using new TCP port:", c)
        st.session_state["SERVER_CONNECTION"] = (choice, c) # This will be the actual client connection, if connection was successful
    except OSError as e:
        print(f'Could not connect to server at {choice}. Maybe it has not been initialized or has gone down?', e)

def disconnect(sock):
    sock.sendall(b'DEL')

def perform_reply(reply, parent):
    # request_type = pack('>Q', int(REQUEST_TYPE.REPLY))
    if st.session_state is not None:

        # Setup payload
        payload = json.dumps({"id": None,
                                "parent": parent,
                                "title": "",
                                "content": reply,
                                "user": THIS_USER}).encode('utf-8') # bytes

        length = pack('>Q', len(payload))
        request_type = pack('>Q', int(REQUEST_TYPE.POST))
        # Send POST
        st.session_state["SERVER_CONNECTION"][1].sendall(request_type+length+payload)

        ack = st.session_state["SERVER_CONNECTION"][1].recv(1000)

        st.write(ack, ':sparkles:')
        connect(st.session_state["SERVER_CONNECTION"][0])


# By default el is just the normal st context, otherwise our form is built on the given element el
def gen_reply_form(parent, el=st, height=400):
    # st.session_state.counter += 1
    with el.form("Reply Form", clear_on_submit=False):
        title = None # Replies don't have a title field!
        reply = st.text_area("Format your reply to the post here.", height=height)
        submit = st.form_submit_button("Click me to post reply!")
        if submit:
            if not reply:
                st.error("Please fill out the reply box!!!")
            else:
                perform_reply(reply, parent)
                st.write(f"User {THIS_USER} replied: {reply}")

def gen_post_form(user):
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

                # Setup payload
                payload = json.dumps({"id": None,
                                     "parent": 0,
                                     "title": title,
                                     "content": post,
                                     "user": user}).encode('utf-8') # bytes

                length = pack('>Q', len(payload))
                request_type = pack('>Q', int(REQUEST_TYPE.POST))
                # Send POST
                st.session_state["SERVER_CONNECTION"][1].sendall(request_type+length+payload)

                ack = st.session_state["SERVER_CONNECTION"][1].recv(1000)

                st.write(ack, ':sparkles:')
                connect(st.session_state["SERVER_CONNECTION"][0])

def perform_read():
    if st.session_state is not None:

        length = pack('>Q', 0)
        request_type = pack('>Q', int(REQUEST_TYPE.READ))

        # Send READ
        st.session_state["SERVER_CONNECTION"][1].sendall(request_type+length)

        # Wait for the biiiiiiig message of all the returned articles
        ret = read(st.session_state["SERVER_CONNECTION"][1]).decode('utf-8')
        # ret = st.session_state["SERVER_CONNECTION"][1].recv(1000)
        print(f"Return from read in perform: {ret}")
        if ret == "Nuthin":
            st.write("Oopsies... no articles yet :persevere: :sob: :poop:")
        else:
            st.session_state["ARTICLES"] = json.loads(ret)
        connect(st.session_state["SERVER_CONNECTION"][0])

def perform_sync():
    if st.session_state is not None:

        # Send a sync command and wait to get an ack, and then finally perform a read once I get that ack
        length = pack('>Q', 0)
        request_type = pack('>Q', int(REQUEST_TYPE.r_SYNC))

        # Send SYNC
        st.session_state["SERVER_CONNECTION"][1].sendall(request_type+length)

        # Recieve sync ack
        ack = read(st.session_state["SERVER_CONNECTION"][1]).decode('utf-8')
        
        perform_read()

if __name__=="__main__":
    # Set up "login" page so each post has a username and address attached
    st.title("Welcome to *consequor*! :classical_building::card_index:")
    st.write("This is a simple bulletin board app backed by a distributed set of remote server replicas. These server replicas each maintain a set (possibly out of sync) of articles and replies to articles for a single topic. You can post your own, read a list of all article titles, and post replies to articles you've chosen to view.")
    if not st.session_state.get('counter'):
        st.session_state['counter'] = 0

    if not st.session_state.get('current_article'):
        st.session_state['current_article'] = 0 # First root article by default

    if not st.session_state.get('ARTICLES'):
        st.session_state['ARTICLES'] = {}

    if not st.session_state.get('SERVER_CONNECTION'):
        st.session_state['SERVER_CONNECTION'] = (None, None)

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
            print(f"Currently connected to server {client_state[0]} via TCP socket at {client_state[1]}")
            connect(choice)

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

            # Get updated article dictionary
            bcols = st.columns(2)
            with bcols[0]:
                if st.button("Read", 'Read-Read-Button'):
                    perform_read()
            with bcols[1]:
                if st.button("Sync", 'Read-Sync-Button'):
                    perform_sync()

            with st.container(height=380):
                # num_articles = st.slider("# Articles Shown", 5, 20)
                # num_pages = (len(st.session_state["ARTICLES"]) // num_articles) + 1 # st.session_state["ARTICLES"] WILL COME FROM READS ON THE CONNECTED REPLICA

                # # Add functionality to "page" through the articles?
                # paging = st.columns(3)
                # if paging[0].button(":arrow_backward:", use_container_width=True): # If clicked, add -1 to page_num, unless min page number
                #     st.session_state["PAGE_NUM"] = min(st.session_state["PAGE_NUM"]-1, 0)
                # if paging[1].button(":arrow_forward:", use_container_width=True): # If clicked, add 1 to page_num, unless max page number
                #     st.session_state["PAGE_NUM"] = min(st.session_state["PAGE_NUM"]+1, num_pages)
                
                # paging[2].write(f"Showing page {st.session_state['PAGE_NUM']} of {num_pages}")

                # Show article list
                # shown_articles = [st.container(height=100) for _ in range(len(st.session_state["ARTICLES"]))]
                
                # for i,a in enumerate(shown_articles):

                # RH: REWORKING THIS PAGE TO JUST BE SIMPLER
                keys = sorted(list(st.session_state['ARTICLES'].keys()))
                subcontainers = [st.container(height=100) for _ in range(len(keys))]
                for i,k in enumerate(keys):
                    a = subcontainers[i]
                    a.write(f"Article ID #{st.session_state['ARTICLES'][k]['id']}")
                    a.write(f"*Title: {st.session_state['ARTICLES'][k]['title']}*")
                    a.write(f"**User: {st.session_state['ARTICLES'][k]['user']}**")
                    a.write(f"{st.session_state['ARTICLES'][k]['content']}")
        
        with tabs[1]:
            st.header("Focus One Article")

            # Maybe some navigation buttons here for going up a level? Every article should have a parent, unless it's 0 (root)
            article = st.selectbox("Choose an article from the dropdown:", list(st.session_state["ARTICLES"].keys())) # SHOULD ONLY ALLOW SELECTION OF ROOT ARTICLES INITIALLY, THEN ANY SUB ARTICLE CAN BE SELECTED!!!
            st.session_state["current_article"] = article

            button_cols = st.columns(2)

            with button_cols[0]:
                if st.button('Change Focus to Parent Article'): # Trigger callback? Simply set article=parent and then st.rerun?
                    parent = st.session_state["ARTICLES"][article]["parent"]
                    if parent not in st.session_state["ARTICLES"].keys():
                        # If we don't have that article, then sync first
                        perform_sync()
                    st.session_state["current_article"] = parent

            with button_cols[1]:
                if st.button("Sync", 'ChooseReply-Sync-Button'):
                    perform_sync()

            choose_reply_cols = st.columns(2)
            with choose_reply_cols[0]:
                with st.container(height=500):
                    st.write(f"I selected article #{st.session_state['current_article']}")
            
            # Ensures that we only have a single reply form available!!!
            gen_reply_form( st.session_state["current_article"], choose_reply_cols[1])
            
        with tabs[2]:
            st.header("Create A New Post")

            if st.button("Sync", 'Post-Sync-Button'):
                perform_sync()

            gen_post_form(THIS_USER)

