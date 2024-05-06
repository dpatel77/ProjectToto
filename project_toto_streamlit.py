# # Ensure Streamit is installed:

# conda activate base
# pip install streamlit
# conda install -c conda-forge streamlit

# # Check if Streamlit is installed:

# streamlit --version

# # Running the Streamlit App:

# streamlit hello

# # Environment Issues:
# which python
# which streamlit

# # Reinstall Streamlit:

# pip uninstall streamlit
# pip install streamlit


import streamlit as st

st.write("Project Toto2")
st.write("## Real-Time Intelligent System for Tornado Prediction")
x = st.text_input("Spring 2024", "Real-Time Intelligent Systems")

if st.button("Click Me"):
    st.write(f"Your count are you looking for `{x}`")

