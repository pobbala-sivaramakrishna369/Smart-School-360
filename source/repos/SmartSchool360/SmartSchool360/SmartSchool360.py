import streamlit as st
import pandas as pd
import sqlite3
import cv2
import numpy as np
import plotly.express as px
from datetime import datetime
import logging
from streamlit_webrtc import webrtc_streamer, VideoTransformerBase
import anthropic

# --- 1. ENTERPRISE CORE & LOGGING ---
logging.basicConfig(level=logging.INFO)
# Make sure to add your ANTHROPIC_API_KEY in Streamlit Secrets
client = anthropic.Anthropic(api_key=st.secrets["ANTHROPIC_API_KEY"])

class SmartSchool360:
    def __init__(self, db_name='smart_school_360_ultimate.db'):
        self.conn = sqlite3.connect(db_name, check_same_thread=False)
        self.init_tables()

    def init_tables(self):
        with self.conn:
            # Student Data Table
            self.conn.execute('''CREATE TABLE IF NOT EXISTS students 
                (id INTEGER PRIMARY KEY, name TEXT, attendance REAL, 
                math INTEGER, science INTEGER, english INTEGER, fee_status TEXT)''')
            # Career Logs Table (Updated for AI Insights)
            self.conn.execute('''CREATE TABLE IF NOT EXISTS career_logs 
                (id INTEGER PRIMARY KEY, student_name TEXT, suggested_course TEXT, insights TEXT, date TEXT)''')
    
    def add_student(self, data):
        with self.conn:
            self.conn.execute("INSERT INTO students (name, attendance, math, science, english, fee_status) VALUES (?,?,?,?,?,?)", data)

    def log_career_suggestion(self, name, course, insights):
        with self.conn:
            self.conn.execute("INSERT INTO career_logs (student_name, suggested_course, insights, date) VALUES (?,?,?,?)", 
                              (name, course, insights, datetime.now().strftime("%Y-%m-%d")))

db = SmartSchool360()

# --- 2. AI ATTENDANCE (Cloud-Compatible Vision) ---
class FaceDetector(VideoTransformerBase):
    def transform(self, frame):
        img = frame.to_ndarray(format="bgr24")
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.3, 5)
        for (x, y, w, h) in faces:
            cv2.rectangle(img, (x, y), (x+w, y+h), (0, 255, 0), 2)
        return img

# --- 3. UI CONFIGURATION ---
st.set_page_config(page_title="Smart School 360 | Anthropic Edition", layout="wide")

if 'auth' not in st.session_state:
    st.session_state['auth'] = False

# Authentication Layer
if not st.session_state['auth']:
    st.title("🛡️ Smart School 360 Global Gateway")
    u, p = st.text_input("Admin ID"), st.text_input("Access Key", type="password")
    if st.button("Authenticate"):
        if u == "admin" and p == "master2026":
            st.session_state['auth'] = True
            st.rerun()
else:
    st.sidebar.title("🏫 Smart School 360")
    st.sidebar.info("Admin: Sivarama Krishna")
    menu = ["📊 Dashboard", "🧬 AI Attendance", "📂 Student Records", "🚀 Smart Career AI (Claude)", "🚪 Logout"]
    choice = st.sidebar.radio("Command Center", menu)

    # --- 4. DASHBOARD ---
    if choice == "📊 Dashboard":
        st.title("🌍 360° Intelligence Overview")
        df = pd.read_sql_query("SELECT * FROM students", db.conn)
        if not df.empty:
            st.metric("Total Students Engaged", len(df))
            fig = px.bar(df, x="name", y=["math", "science", "english"], barmode="group")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("No records found. Please add students in 'Student Records'.")

    # --- 5. AI ATTENDANCE (Fixed for Streamlit Cloud) ---
    elif choice == "🧬 AI Attendance":
        st.title("📸 AI Vision Scanner")
        st.info("Using WebRTC for Cloud-Based Face Detection. Please allow camera access.")
        webrtc_streamer(key="attendance-scanner", video_transformer_factory=FaceDetector)

    # --- 6. STUDENT RECORDS ---
    elif choice == "📂 Student Records":
        st.title("📝 Data Management")
        with st.form("add_student"):
            name = st.text_input("Student Name")
            m = st.number_input("Math Score", 0, 100)
            s = st.number_input("Science Score", 0, 100)
            e = st.number_input("English Score", 0, 100)
            if st.form_submit_button("Save Record"):
                db.add_student((name, 100, m, s, e, "Paid"))
                st.success(f"Record for {name} saved successfully!")

    # --- 7. SMART CAREER AI (Anthropic Integration) ---
    elif choice == "🚀 Smart Career AI (Claude)":
        st.title("🚀 AI Career Path Recommender")
        st.markdown("This module uses **Anthropic Claude AI** to analyze scores and suggest Coursera paths.")
        
        df = pd.read_sql_query("SELECT * FROM students", db.conn)
        if not df.empty:
            selected_student = st.selectbox("Select Student for AI Analysis", df['name'])
            student_data = df[df['name'] == selected_student].iloc[0]
            
            if st.button("Generate AI Insights"):
                with st.spinner("Claude AI is analyzing performance..."):
                    # Constructing the AI Prompt
                    prompt = f"""
                    Analyze this student's performance:
                    Name: {selected_student}
                    Math: {student_data['math']}, Science: {student_data['science']}, English: {student_data['english']}.
                    Provide a personalized career suggestion and a brief motivation quote. 
                    Keep the tone professional and encouraging.
                    """

                    message = client.messages.create(
                        model="claude-3-5-sonnet-20240620",
                        max_tokens=500,
                        messages=[{"role": "user", "content": prompt}]
                    )
                    
                    ai_response = message.content[0].text
                    st.subheader(f"AI Recommendations for {selected_student}")
                    st.success(ai_response)
                    
                    # Log the suggestion to database
                    db.log_career_suggestion(selected_student, "Claude Analysis", ai_response)
                    st.info("Insights have been logged to the database.")
        else:
            st.error("No student data available for analysis.")

    # --- 8. LOGOUT ---
    elif choice == "🚪 Logout":
        st.session_state['auth'] = False
        st.rerun()
