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
    # Set up "login" page so each post has a username and address attached


    st.title("Welcome to *consequor*! :classical_building::card_index:")
    st.write("This is a simple bulletin board app backed by a distributed set of remote server replicas. These server replicas each maintain a set (possibly out of sync) of articles and replies to articles for a single topic. You can post your own, read a list of all article titles, and post replies to articles you've chosen to view.")

    side = st.sidebar
    # num_articles = side.slider("num_articles_shown", 5, 20)

    # Add button for connection management (drop down, reconnects on new selection)
    choice = side.selectbox("Connect to a new Server", SERVERS) # DEFAULTS TO 0th SERVER

    if st.session_state.get("SERVER_CONNECTION") != choice:
        connect(choice) # Will return our client
    
    st.write(f"You are connected to the following server: {st.session_state['SERVER_CONNECTION']}")

    # Buttons for read (get list of articles), choose (selects from listed articles which to open?), post (make a new article and posts to server)
    # state = None
    # cols = st.columns(3)
    # cols[0].button("List All Articles", use_container_width=True) # READ
    # cols[1].button("Focus One Article", use_container_width=True) # CHOOSE
    # cols[2].button("Create A New Post", use_container_width=True) # POST

    # # Buttons switch between container view based on state
    # if state == "CHOOSE":
    #     print("Create view of one post and all its children") # Will get published to server on enter as JSON
    # if state == "POST":
    #     print("Open a new text input box or form") # Will get published to server on enter as JSON
    # else:
    #     # By default, just list all articles in order for "READ" options

    # Try tabs instead!
    tabs = st.tabs(["[READ]", " [CHOOSE]", "[POST]"])

    with tabs[0]:
        st.header("List All Primary Articles")
        st.write("This tab shows all articles which belong to the root topic thread, and are not replies.")
        page_num = 0
        with st.container(height=400):
            num_articles = st.slider("# Articles Shown", 5, 20)
            num_pages = (len(ARTICLE_CACHE) // num_articles) + 1

            # Add functionality to "page" through the articles?
            paging = st.columns(3)
            paging[0].button(":arrow_backward:", use_container_width=True) # If clicked, add -1 to page_num, unless min page number
            paging[1].button(":arrow_forward:", use_container_width=True) # If clicked, add 1 to page_num, unless max page number
            paging[2].write(f"Showing page {page_num} of {num_pages}")

            # Show article list
            shown_articles = [st.container(height=100) for _ in range(num_articles)]
            for i,a in enumerate(shown_articles):
                a.write(f"Hi, I'm article # {i}!")
    
    with tabs[1]:
        st.header("Focus One Article")
        # Maybe some navigation buttons here for going up a level? Every article should have a parent, unless it's 0 (root)
        st.button('Change Focus to Parent Article') # Trigger callback? Simply set article=parent and then st.rerun?

        article = st.selectbox("Choose an article from the dropdown:", ARTICLE_CACHE)
        with st.container(height=400):
            st.write(f"I selected article # {article}")
    
    with tabs[2]:
        st.header("Create A New Post")
