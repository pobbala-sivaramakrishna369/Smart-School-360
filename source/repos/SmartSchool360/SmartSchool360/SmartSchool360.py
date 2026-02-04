import streamlit as st
import pandas as pd
import sqlite3
import cv2
import numpy as np
import plotly.express as px
from datetime import datetime
import logging

# --- 1. ENTERPRISE CORE & LOGGING ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SmartSchool360:
    def __init__(self, db_name='smart_school_360_ultimate.db'):
        self.conn = sqlite3.connect(db_name, check_same_thread=False)
        self.init_tables()

    def init_tables(self):
        with self.conn:
            # విద్యార్థుల డేటా
            self.conn.execute('''CREATE TABLE IF NOT EXISTS students 
                (id INTEGER PRIMARY KEY, name TEXT, attendance REAL, 
                math INTEGER, science INTEGER, english INTEGER, fee_status TEXT)''')
            # కెరీర్ స్కిల్స్ డేటా (New Module)
            self.conn.execute('''CREATE TABLE IF NOT EXISTS career_logs 
                (id INTEGER PRIMARY KEY, student_name TEXT, suggested_course TEXT, date TEXT)''')
    
    def add_student(self, data):
        with self.conn:
            self.conn.execute("INSERT INTO students (name, attendance, math, science, english, fee_status) VALUES (?,?,?,?,?,?)", data)

    def log_career_suggestion(self, name, course):
        with self.conn:
            self.conn.execute("INSERT INTO career_logs (student_name, suggested_course, date) VALUES (?,?,?)", 
                              (name, course, datetime.now().strftime("%Y-%m-%d")))

db = SmartSchool360()

# --- 2. AI ATTENDANCE (Vision) ---
def start_ai_attendance():
    cap = cv2.VideoCapture(0)
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    start_time = datetime.now()
    found = False
    while True:
        ret, frame = cap.read()
        if not ret: break
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.3, 5)
        for (x, y, w, h) in faces:
            cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
            found = True
        cv2.imshow('Smart School 360 AI', frame)
        if cv2.waitKey(1) & 0xFF == ord('q') or (datetime.now() - start_time).seconds > 5:
            break
    cap.release()
    cv2.destroyAllWindows()
    return found

# --- 3. UI CONFIGURATION ---
st.set_page_config(page_title="Smart School 360 | Coursera Edition", layout="wide")

if 'auth' not in st.session_state:
    st.session_state['auth'] = False

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
    menu = ["📊 Dashboard", "🧬 AI Attendance", "📂 Student Records", "🚀 Smart Career AI", "📥 Reports", "🚪 Logout"]
    choice = st.sidebar.radio("Command Center", menu)

    # --- 4. DASHBOARD ---
    if choice == "📊 Dashboard":
        st.title("🌍 360° Intelligence Overview")
        df = pd.read_sql_query("SELECT * FROM students", db.conn)
        if not df.empty:
            st.metric("Total Students Engaged", len(df))
            fig = px.bar(df, x="name", y=["math", "science", "english"], barmode="group")
            st.plotly_chart(fig, use_container_width=True)

    # --- 5. AI ATTENDANCE ---
    elif choice == "🧬 AI Attendance":
        st.title("📸 AI Vision Scanner")
        if st.button("Start Scan"):
            if start_ai_attendance(): st.success("Attendance Synced! ✅")

    # --- 6. STUDENT RECORDS ---
    elif choice == "📂 Student Records":
        st.title("📝 Data Management")
        with st.form("add_student"):
            name = st.text_input("Student Name")
            m = st.number_input("Math", 0, 100)
            s = st.number_input("Science", 0, 100)
            e = st.number_input("English", 0, 100)
            if st.form_submit_button("Save Record"):
                db.add_student((name, 100, m, s, e, "Paid"))
                st.success("Record Saved!")

    # --- 7. SMART CAREER AI (REPLACED ORCHARD) ---
    elif choice == "🚀 Smart Career AI":
        st.title("🚀 AI Career Path Recommender")
        st.info("ఈ విభాగం విద్యార్థుల మార్కులను బట్టి వారికి కావలసిన కోర్సులను కురిసేరా ద్వారా సూచిస్తుంది.")
        
        df = pd.read_sql_query("SELECT * FROM students", db.conn)
        if not df.empty:
            selected_student = st.selectbox("Select Student to Analyze", df['name'])
            student_data = df[df['name'] == selected_student].iloc[0]
            
            # Logic for Recommendation
            suggestion = ""
            if student_data['math'] < 50:
                suggestion = "Coursera: Basic Mathematics Specialist"
            elif student_data['science'] < 50:
                suggestion = "Coursera: Foundation of Data Science"
            else:
                suggestion = "Coursera: Advanced Python & AI Engineering"
            
            st.subheader(f"Recommended for {selected_student}:")
            st.success(f"🎯 {suggestion}")
            
            if st.button("Log Suggestion to Database"):
                db.log_career_suggestion(selected_student, suggestion)
                st.write("Logged successfully!")

    # --- 8. REPORTS ---
    elif choice == "📥 Reports":
        st.title("📑 Intelligence Reports")
        df_career = pd.read_sql_query("SELECT * FROM career_logs", db.conn)
        st.write("Career Logs:")
        st.dataframe(df_career)

    elif choice == "🚪 Logout":
        st.session_state['auth'] = False
        st.rerun()