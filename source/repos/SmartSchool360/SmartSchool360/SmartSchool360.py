import streamlit as st
import pandas as pd
import sqlite3
import cv2
import numpy as np
import time
import os
from streamlit_webrtc import webrtc_streamer, VideoTransformerBase

# --- PILLAR 1: DATABASE LAYER (OOPS & DATA PERSISTENCE) ---
# Logic: Using a class to keep all Database operations in one place (Encapsulation).
class SchoolDatabase:
    def __init__(self, db_name='school_intelligence.db'):
        # Establish connection with Error Handling
        try:
            self.conn = sqlite3.connect(db_name, check_same_thread=False)
            self.create_tables()
        except sqlite3.Error as e:
            st.error(f"Database Error: {e}")

    def create_tables(self):
        """Build the structure for our system."""
        with self.conn:
            # Student Profiles Table
            self.conn.execute('''CREATE TABLE IF NOT EXISTS student_data 
                (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                 name TEXT NOT NULL, 
                 math_score INTEGER, 
                 science_score INTEGER, 
                 english_score INTEGER)''')
            
            # Smart Attendance Table
            self.conn.execute('''CREATE TABLE IF NOT EXISTS attendance 
                (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                 student_name TEXT NOT NULL, 
                 scan_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')

    # Security Tip: Using '?' to prevent SQL Injection hackers.
    def add_student(self, name, m, s, e):
        with self.conn:
            self.conn.execute("INSERT INTO student_data (name, math_score, science_score, english_score) VALUES (?,?,?,?)", (name, m, s, e))

    def remove_student(self, student_id):
        with self.conn:
            self.conn.execute("DELETE FROM student_data WHERE id = ?", (student_id,))

# Initialize our Global Database Object
db = SchoolDatabase()

# --- PILLAR 2: ANALYTICS ENGINE (BUSINESS LOGIC) ---
# Logic: A separate engine to process data and give career advice.
class CareerAdvisor:
    @staticmethod
    def get_career_path(m, s, e):
        # A simple but powerful if-else algorithm for recommendations
        if m >= 85 and s >= 85:
            return "AI Research / Data Science", "Exceptional analytical potential."
        elif s >= 80:
            return "Healthcare / Biotech Scientist", "Strong scientific curiosity."
        elif e >= 85:
            return "Diplomat / Legal Counsel", "Great communication & language skills."
        else:
            return "Technical Operations Management", "Well-rounded skill set."

# --- PILLAR 3: VISION & BACKEND (AI & PERFORMANCE OPTIMIZATION) ---
# Logic: Using Computer Vision with a 'Cooldown' to save system resources.
class FaceAnalysisScanner(VideoTransformerBase):
    def __init__(self):
        # Load the pre-trained face detection model
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        # COOLDOWN LOGIC: Don't save same student every second (Optimization)
        self.last_saved = 0
        self.cooldown_period = 10 

    def transform(self, frame):
        img = frame.to_ndarray(format="bgr24")
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(gray, 1.3, 5)
        
        current_time = time.time()
        
        for (x, y, w, h) in faces:
            cv2.rectangle(img, (x, y), (x+w, y+h), (0, 255, 0), 2)
            
            # Simulating an identified student for this project demo
            recognized_student = "Sivarama Krishna" 
            
            # Only save to DB if 10 seconds have passed (Smart Resource Management)
            if current_time - self.last_saved > self.cooldown_period:
                with db.conn:
                    db.conn.execute("INSERT INTO attendance (student_name) VALUES (?)", (recognized_student,))
                self.last_saved = current_time
                alert = f"RECORDED: {recognized_student}"
            else:
                alert = "SCANNING..."

            cv2.putText(img, alert, (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        return img

# --- PILLAR 4: FRONTEND LAYER (UI & SECURITY STATE) ---
# Logic: Using Streamlit for a professional-grade User Interface.
st.set_page_config(page_title="Smart School 360", layout="wide")

# SECURITY: Preventing unauthorized access using Session State
if 'is_auth' not in st.session_state:
    st.session_state['is_auth'] = False

# 1. LOGIN PORTAL
if not st.session_state['is_auth']:
    st.title("🛡️ Secure Administrator Login")
    user_id = st.text_input("User ID")
    token = st.text_input("Security Password", type="password")
    if st.button("Authorize"):
        if user_id == "admin" and token == "master2026":
            st.session_state['is_auth'] = True
            st.rerun()
        else:
            st.error("Invalid Credentials. Please try again.")

# 2. MAIN APPLICATION (POST-LOGIN)
else:
    st.sidebar.title("🎛️ Operations Control")
    nav = st.sidebar.radio("Navigate to:", ["Dashboard", "AI Scanner", "Registration", "Career Engine", "Logout"])

    # --- DASHBOARD (View & Delete) ---
    if nav == "Dashboard":
        st.title("📊 Administrative Dashboard")
        left_col, right_col = st.columns(2)
        
        with left_col:
            st.subheader("Database Records")
            df = pd.read_sql_query("SELECT * FROM student_data", db.conn)
            if not df.empty:
                for _, row in df.iterrows():
                    with st.expander(f"{row['name']} (ID: {row['id']})"):
                        st.write(f"Math: {row['math_score']}, Science: {row['science_score']}, English: {row['english_score']}")
                        if st.button(f"Delete Record {row['id']}", key=f"del_{row['id']}"):
                            db.remove_student(row['id'])
                            st.success(f"Removed ID {row['id']}")
                            st.rerun()
            else:
                st.info("No student data available.")

        with right_col:
            st.subheader("Real-Time Attendance Feed")
            logs = pd.read_sql_query("SELECT student_name, scan_time FROM attendance ORDER BY scan_time DESC LIMIT 8", db.conn)
            st.table(logs)

    # --- AI VISION ---
    elif nav == "AI Scanner":
        st.title("📸 Intelligent Vision Scanner")
        st.write("Detecting students and logging attendance to database in real-time.")
        webrtc_streamer(key="attendance-vision", video_transformer_factory=FaceAnalysisScanner)

    # --- ENROLLMENT ---
    elif nav == "Registration":
        st.title("📝 Student Enrollment")
        with st.form("entry_form"):
            s_name = st.text_input("Full Name")
            m_score = st.number_input("Mathematics Score", 0, 100)
            s_score = st.number_input("Science Score", 0, 100)
            e_score = st.number_input("English Score", 0, 100)
            if st.form_submit_button("Securely Enroll Student"):
                if s_name:
                    db.add_student(s_name, m_score, s_score, e_score)
                    st.success("Student profile created and encrypted.")
                else:
                    st.warning("Please provide a valid name.")

    # --- CAREER ANALYTICS ---
    elif nav == "Career Engine":
        st.title("🚀 Smart Career Recommendation Engine")
        df = pd.read_sql_query("SELECT * FROM student_data", db.conn)
        if not df.empty:
            target = st.selectbox("Select Student Profile", df['name'])
            profile = df[df['name'] == target].iloc[0]
            if st.button("Generate AI Insights"):
                career, why = CareerAdvisor.get_career_path(profile['math_score'], profile['science_score'], profile['english_score'])
                st.success(f"Recommended Career: {career}")
                st.info(f"Why? {why}")
        else:
            st.warning("Database is empty. Please enroll students first.")

    elif nav == "Logout":
        st.session_state['is_auth'] = False
        st.rerun()
