import streamlit as st

with st.form("my_form", clear_on_submit=True):
    st.write("Inside the form")
    slider_val = st.slider("Form slider")
    checkbox_val = st.checkbox("Form checkbox")
    reply = st.text_area('Enter reply here')

    # Every form must have a submit button.
    submitted = st.form_submit_button("Submit")
    if submitted:
        st.write("slider", slider_val, "checkbox", checkbox_val)
        st.write("Here's my reply:", reply)
        print(reply)
st.write("Outside the form")