import streamlit as st
import chromadb
import os
from dotenv import load_dotenv
import json
import uuid
import time
from datetime import datetime

# LangChain imports
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import CharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_openai import AzureOpenAI, AzureOpenAIEmbeddings, AzureChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_classic.chains import create_history_aware_retriever
from langchain_classic.chains.retrieval import create_retrieval_chain
from langchain_classic.chains.combine_documents import create_stuff_documents_chain


load_dotenv()


@st.cache_resource
def get_db():
    return chromadb.PersistentClient(path="./chroma_db_storageauth")

client = get_db()
# This collection stores the finished sessions
collection = client.get_or_create_collection(name="user_sessions")

# 2. SESSION CHECK: Check if the user was already logged in
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

# --- AUTHENTICATION LOGIC ---
if not st.session_state["logged_in"]:
    st.title("🔐 Login to RAG System")
    st.info("Don't have an account? Go to **Sign Up**. Already have an account? Go to **Sign In**.")

    menu = st.sidebar.selectbox("Menu", ["Sign In", "Sign Up"])

    if menu == "Sign Up":
        username = st.text_input("Choose Username")
        password = st.text_input("Choose Password", type="password")
        if st.button("Create Account"):
            # Check if exists
            existing = collection.get(ids=[username])
            if existing["ids"]:
                st.error("User already exists!")
            else:
                collection.add(
                    ids=[username],
                    documents=["user_profile"],
                    metadatas=[{"password": password}]
                )
                st.success("Account created! Now go to Sign In.")

    elif menu == "Sign In":
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("Login"):
            result = collection.get(ids=[username])
            if result["ids"] and result["metadatas"][0]["password"] == password:
                st.session_state.messages = []
                st.session_state.chat_history = []
                st.session_state["logged_in"] = True
                st.session_state["username"] = username
                st.session_state.current_session_id = str(uuid.uuid4()) 

                # --- 🔑 THE FIX: Load Past Questions into memory IMMEDIATELY on login ---
                previous_sessions = collection.get(where={"username": username})
                all_past_questions = []
                if previous_sessions["ids"]:
                    for doc in previous_sessions["documents"]:
                        try:
                            old_msgs = json.loads(doc)
                            for m in old_msgs:
                                if m["role"] == "user":
                                    all_past_questions.append(m["content"])
                        except: continue
                
                # Store these in a specific state variable for the AI to use
                st.session_state["past_questions_list"] = all_past_questions
                st.rerun()
# --- MAIN PROJECT AREA ---
else:
    # --- Configuration ---
    current_user = st.session_state['username']

    # Initialize Session States
    if "current_session_id" not in st.session_state:
        st.session_state.current_session_id = f"session_{current_user}"  # Unique session ID per user
    if "messages" not in st.session_state:
        st.session_state.messages = []
        # st.session_state.chat_history = []
    if "chat_history" not in st.session_state:
        st.session_state.chat_history=[]
    # 1. Initialize the variable so it is 'defined'
    if "question_count" not in st.session_state:
        st.session_state["question_count"] = 0
    with st.sidebar:
        st.success(f"Logged in as: {current_user}")
        
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.username = None
            st.session_state.messages = []
            st.session_state.chat_history = []
            # st.session_state.current_session_id = str(uuid.uuid4())  # Reset session ID for next login
            st.rerun()
            # --- Add logic to remember previous sessions ---
            # Load all previous sessions for the current user
            previous_sessions = collection.get(where={"username": current_user})
            st.session_state["previous_questions"] = []
            if previous_sessions["ids"]:
                for i, session_id in enumerate(previous_sessions["ids"]):
                    # Skip current session
                    if session_id == st.session_state.current_session_id:
                        continue
                    try:
                        messages = json.loads(previous_sessions["documents"][i])
                        for msg in messages:
                            if msg["role"] == "user":
                                st.session_state["previous_questions"].append(msg["content"])
                    except Exception:
                        pass

            # Helper function to answer "what question did I ask in previous session"
            def handle_previous_questions_request(prompt):
                keywords = [
                    "what question did i ask",
                    "what questions did i ask",
                    "give me what question i asked",
                    "previous session",
                    "previous sessions"
                ]
                if any(k in prompt.lower() for k in keywords):
                    if st.session_state["previous_questions"]:
                        questions = "\n".join(
                            [f"{i+1}. {q}" for i, q in enumerate(st.session_state["previous_questions"])]
                        )
                        return f"Here are the questions you asked in previous sessions:\n{questions}"
                    else:
                        return "You have not asked any questions in previous sessions."
                return None
    # 2. Clear Chat History Button
        if st.button("Clear Chat History"):
            # client.delete_collection(name=f"chat_log_{current_user}")
                    
            st.session_state.messages = []
            st.session_state.chat_history = []
            try:
                collection.delete(ids=[st.session_state.current_session_id])
            except Exception as e:
                pass
            st.session_state.current_session_id = str(uuid.uuid4())  # New session ID for fresh start
            st.success("Chat history cleared! Starting a new session.")
            st.rerun()
        st.divider()

    with st.sidebar:
        st.title("📜 Chat History")

        
        # New Chat Button (Gives the "Fresh Page" you requested)
        if st.button("➕ New Chat", use_container_width=True):
            # Save current session if it's not empty before clearing
            if st.session_state.messages:
                session_title = st.session_state.messages[0]["content"][:30] + "..."
                collection.add(
                    ids=[st.session_state.current_session_id],
                    documents=[json.dumps(st.session_state.messages)], # Save full conversation
                    metadatas=[{"username": current_user, "title": session_title, "date": str(datetime.now())}]
                )
            
            # Reset for fresh page
            st.session_state.current_session_id = str(uuid.uuid4())
            st.session_state.messages = []
            st.rerun()
        
        if st.button("🗑️ Clear All History"):
            try:
                collection.delete(where={"username": current_user})
            except Exception as e:
                pass
            st.session_state.messages = []
            st.session_state.chat_history = []
            st.rerun()
        st.divider()

        # Load and Display Previous Sessions for THIS user
        user_sessions = collection.get(where={"username": current_user})
        if user_sessions["ids"]:
            for i, session_id in enumerate(user_sessions["ids"]):
                title = user_sessions["metadatas"][i].get("title")
                if st.button(f"💬 {title}", key=session_id):
                    # Load the clicked session
                    st.session_state.current_session_id = session_id
                    st.session_state.messages = json.loads(user_sessions["documents"][i])
                    st.rerun()

        st.divider()

    st.title("🤖 Document QA with Azure OpenAI")
    st.set_page_config(page_title="RLHF LLM Trainer", page_icon="🤖")

    connection = AzureOpenAI(
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
            response = connection.chat.completions.create(
                model=os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT"),
                messages=[{"role": "user", "content": prompt}],
                max_tokens=200
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

        feedback = st.radio("Is this response good?", ["Yes", "No"], index=0)
        
        if feedback == "Yes":
            # Use the callback function here
            st.button("Submit Feedback", on_click=save_feedback, type="primary")
            print(feedback)
        else:
            if st.button("Submit Feedback"):
                st.warning("Regenerating a new response...")
                st.session_state.response = generate_response(st.session_state.question)
                st.rerun()

