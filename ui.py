import streamlit as st 
from agent import build_agent

st.set_page_config(
    page_title="VidBrief",
    layout="centered"
)

st.title("🎥 AI Youtube Video Analyze")

# caching
@st.cache_resource
def get_agent():
    return build_agent()

agent=get_agent()

#Input box
video_url=st.text_input("Enter youtube video link") #Str
button=st.button("Analyze video") # True/False

if video_url and button:
    with st.spinner("Analyzing video ..."):
        response=agent.run(
            f"Analyze this video :{video_url}"
            )
    st.markdown("Analysis Report of video:")
    st.write(response.content)