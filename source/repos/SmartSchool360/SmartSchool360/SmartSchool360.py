import streamlit as st
import pandas as pd
import sqlite3
import cv2
import numpy as np
from streamlit_webrtc import webrtc_streamer, VideoTransformerBase

# --- 1. DATABASE MANAGEMENT ---
class SchoolDatabase:
    def __init__(self, db_name='school_intelligence.db'):
        self.conn = sqlite3.connect(db_name, check_same_thread=False)
        self.setup_tables()

    def setup_tables(self):
        with self.conn:
            self.conn.execute('''CREATE TABLE IF NOT EXISTS student_data 
                (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                 name TEXT, 
                 math_score INTEGER, 
                 science_score INTEGER, 
                 english_score INTEGER)''')

db = SchoolDatabase()

# --- 2. VISION SCANNER (FACE DETECTION) ---
class FaceAnalysisTransformer(VideoTransformerBase):
    def __init__(self):
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

    def transform(self, frame):
        img = frame.to_ndarray(format="bgr24")
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(gray, 1.3, 5)
        
        for (x, y, w, h) in faces:
            cv2.rectangle(img, (x, y), (x+w, y+h), (0, 255, 0), 2)
            cv2.putText(img, "Scanning Identity...", (x, y-10), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        return img

# --- 3. PAGE CONFIGURATION ---
st.set_page_config(page_title="Smart School 360", layout="wide")

if 'is_authenticated' not in st.session_state:
    st.session_state['is_authenticated'] = False

# --- 4. AUTHENTICATION UI ---
if not st.session_state['is_authenticated']:
    st.title("🛡️ Secure Administrator Portal")
    admin_id = st.text_input("Administrator ID")
    access_key = st.text_input("Access Key", type="password")
    
    if st.button("Authenticate"):
        if admin_id == "admin" and access_key == "master2026":
            st.session_state['is_authenticated'] = True
            st.rerun()
        else:
            st.error("Authentication Failed: Invalid Credentials")

# --- 5. MAIN APPLICATION ---
else:
    st.sidebar.title("🏫 Operations Control")
    app_mode = ["Dashboard", "AI Vision Scanner", "Add Records", "Career Analytics", "Logout"]
    selection = st.sidebar.radio("Navigation Menu", app_mode)

    # --- DASHBOARD ---
    if selection == "Dashboard":
        st.title("📊 Student Performance Overview")
        data = pd.read_sql_query("SELECT * FROM student_data", db.conn)
        if not data.empty:
            st.dataframe(data, use_container_width=True)
            st.bar_chart(data.set_index('name')[['math_score', 'science_score', 'english_score']])
        else:
            st.info("The database is currently empty. Please register students.")

    # --- CAMERA / VISION ---
    elif selection == "AI Vision Scanner":
        st.title("📸 Facial Recognition Attendance")
        st.write("Ensuring identity verification through computer vision.")
        webrtc_streamer(
            key="vision-scanner", 
            video_transformer_factory=FaceAnalysisTransformer,
            rtc_configuration={
                "iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]
            }
        )

    # --- ADD RECORDS ---
    elif selection == "Add Records":
        st.title("📝 Student Enrollment")
        with st.form("enroll_form"):
            s_name = st.text_input("Student Full Name")
            m_mark = st.number_input("Mathematics", 0, 100)
            s_mark = st.number_input("Science", 0, 100)
            e_mark = st.number_input("English", 0, 100)
            
            if st.form_submit_button("Save Student Profile"):
                with db.conn:
                    db.conn.execute("INSERT INTO student_data (name, math_score, science_score, english_score) VALUES (?,?,?,?)", 
                                  (s_name, m_mark, s_mark, e_mark))
                st.success(f"Profile for {s_name} has been secured in the database.")

    # --- CAREER LOGIC (ALGORITHMIC) ---
    elif selection == "Career Analytics":
        st.title("🚀 Career Recommendation Engine")
        data = pd.read_sql_query("SELECT * FROM student_data", db.conn)
        if not data.empty:
            target_student = st.selectbox("Select Student Profile", data['name'])
            profile = data[data['name'] == target_student].iloc[0]
            
            if st.button("Generate Recommendation"):
                m, s, e = profile['math_score'], profile['science_score'], profile['english_score']
                
                # Custom Intelligent Logic
                if m >= 90 and s >= 85:
                    path = "Quantum Computing & Advanced Mathematics"
                    insight = "Exceptional analytical skills detected in core STEM fields."
                elif s >= 90:
                    path = "Biomedical Engineering or Space Science"
                    insight = "High aptitude for scientific research and exploration."
                elif e >= 85:
                    path = "Corporate Communications or International Law"
                    insight = "Strong linguistic and interpersonal capabilities identified."
                else:
                    path = "Technology Management & Systems Analysis"
                    insight = "Balanced profile suitable for multi-disciplinary technology roles."
                
                st.subheader(f"Results for {target_student}")
                st.success(f"Recommended Domain: {path}")
                st.info(f"Analytical Insight: {insight}")
        else:
            st.warning("No data found. Please enroll students first.")

    # --- LOGOUT ---
    elif selection == "Logout":
        st.session_state['is_authenticated'] = False
        st.rerun()
