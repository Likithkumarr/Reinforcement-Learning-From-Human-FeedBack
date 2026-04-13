import json
import os
import streamlit as st
from openai import AzureOpenAI
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(page_title="RLHF LLM Trainer", page_icon="🤖")

client = AzureOpenAI(
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    azure_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT"),
    api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
    api_key=os.getenv("AZURE_OPENAI_API_KEY")
)

feedback_file = "feedbackstreamlit2.json"

st.title("RLHF LLM Trainer")
st.write("Type a question and provide feedback on the LLM response.")

# --- CALLBACK FUNCTION ---
# Function start
def save_feedback():
    """This function runs BEFORE the script reruns, allowing state modification."""

    # 1. Save the data
    feedback_data = {
        "question": st.session_state.question,
        "response": st.session_state.response,
        "feedback": "Good" #feedback
    }
    
    if not os.path.exists(feedback_file):
        open(feedback_file, 'w').close()  # Create the file if it doesn't exist

    with open(feedback_file, 'a') as f:
        f.write(json.dumps(feedback_data) + '\n')
    
    # 2. Clear all states
    st.session_state.response = ""
    st.session_state.question = ""
    st.session_state.user_input = "" # This now works because it's in a callback!
# ----Function end----

# Initialize session state for non-widget keys
if "response" not in st.session_state:
    st.session_state.response = ""
if "question" not in st.session_state:
    st.session_state.question = ""

def generate_response(prompt):
    try:
        response = client.chat.completions.create(
            model=os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT"),
            messages=[{"role": "user", "content": prompt}],
            max_tokens=100
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Error: {str(e)}"

# Input Section - Note: we don't use 'value=' here because 'key=' handles it
input_text = st.text_input("Ask a question:", key="user_input") #key="user_input gives unique name to input box

if st.button("Generate Response"):
    if input_text:
        st.session_state.question = input_text
        st.session_state.response = generate_response(input_text)
    else:
        st.error("Please enter a question first.")

# Feedback Section
if st.session_state.response:
    st.subheader("LLM Response Feedback")
    st.info(f"**Current Response:** {st.session_state.response}") # Display the response prominently for better feedback context 
    #info() gives it a colored box to stand out, and ** ** makes the text bold for emphasis.
    # feedback=st.text_input("Enter 👍 for good answer or 👎 for bad answer")
    st.write("Click 👍 for good answer or 👎 for bad answer")
    feedback = st.radio("Is this response good?", ["👍", "👎"], index=0)
    
    if feedback == "👍":
        # Use the callback function here
        st.button("Submit Feedback", on_click=save_feedback, type="primary")
        print(feedback)
    else:
        if st.button("Submit Feedback"):
            st.warning("Regenerating a new response...")
            st.session_state.response = generate_response(st.session_state.question)
            st.rerun()


            


                
