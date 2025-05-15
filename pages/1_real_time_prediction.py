import streamlit as st
from home import face_rec
from streamlit_webrtc import webrtc_streamer
import av
import time
import pandas as pd
from datetime import datetime

# Page configuration
st.set_page_config(
    page_title="Live Attendance | AI Attendance",
    page_icon="🟢",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        color: #4CAF50;
        text-align: center;
        margin-bottom: 1.5rem;
        font-weight: 700;
    }
    .card {
        border-radius: 8px;
        padding: 25px;
        background-color: #f8f9fa;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
        margin-bottom: 20px;
    }
    .webcam-container {
        border: 2px solid #4CAF50;
        border-radius: 8px;
        padding: 15px;
        background-color: #f1f8e9;
    }
    .status-indicator {
        display: flex;
        align-items: center;
        margin-bottom: 10px;
    }
    .status-dot {
        width: 12px;
        height: 12px;
        border-radius: 50%;
        margin-right: 8px;
    }
    .active {
        background-color: #4CAF50;
        box-shadow: 0 0 8px #4CAF50;
        animation: pulse 2s infinite;
    }
    @keyframes pulse {
        0% { box-shadow: 0 0 0 0 rgba(76, 175, 80, 0.7); }
        70% { box-shadow: 0 0 0 10px rgba(76, 175, 80, 0); }
        100% { box-shadow: 0 0 0 0 rgba(76, 175, 80, 0); }
    }
    .inactive {
        background-color: #9e9e9e;
    }
    .section-title {
        font-size: 1.3rem;
        font-weight: 600;
        color: #424242;
        margin-bottom: 15px;
        padding-bottom: 8px;
        border-bottom: 2px solid #e0e0e0;
    }
    .attendance-table {
        font-size: 0.9rem;
    }
    .footer {
        text-align: center;
        margin-top: 30px;
        padding: 20px;
        color: #6c757d;
        border-top: 1px solid #e9ecef;
    }
    .stats-box {
        background-color: #f8f9fa;
        border-radius: 8px;
        padding: 15px;
        text-align: center;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    }
    .stats-number {
        font-size: 1.8rem;
        font-weight: bold;
        color: #4CAF50;
    }
    .stats-label {
        color: #757575;
        font-size: 0.9rem;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown("<h1 class='main-header'>🟢 Live Attendance Tracking</h1>", unsafe_allow_html=True)

# System status indicators
col1, col2, col3 = st.columns(3)
with col1:
    st.markdown("""
    <div class="status-indicator">
        <div class="status-dot active"></div>
        <div>Recognition System: <b>Active</b></div>
    </div>
    """, unsafe_allow_html=True)
with col2:
    st.markdown("""
    <div class="status-indicator">
        <div class="status-dot active"></div>
        <div>Database Connection: <b>Active</b></div>
    </div>
    """, unsafe_allow_html=True)
with col3:
    st.markdown("""
    <div class="status-indicator">
        <div class="status-dot active"></div>
        <div>Auto-Logging: <b>Enabled</b></div>
    </div>
    """, unsafe_allow_html=True)

# Main content
left_col, right_col = st.columns([3, 2])

with left_col:
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("<h2 class='section-title'>📹 Live Recognition Feed</h2>", unsafe_allow_html=True)
    
    # Retrieve registered data
    with st.spinner('Retrieving data from Redis database...'):
        try:
            redis_face_db = face_rec.retrive_data(name='academy:register')
            if not redis_face_db.empty:
                st.success('✅ User data retrieved successfully!')
            else:
                st.warning('⚠️ No registered users found in the database.')
        except Exception as e:
            st.error(f"Error retrieving data: {e}")
            redis_face_db = pd.DataFrame()
    
    # Configuration options
    with st.expander("Recognition Settings"):
        wait_time = st.slider("Log Update Interval (seconds)", 10, 120, 30)
        confidence_threshold = st.slider("Recognition Confidence Threshold", 0.3, 0.9, 0.5, 0.05)
    
    # Initialize real-time prediction
    set_time = time.time()
    realtime_pred = face_rec.RealTimePred()
    
    # Video frame callback function
    def video_frame_callback(frame):
        global set_time
        img = frame.to_ndarray(format="bgr24")
        
        # Perform face prediction
        pred_img = realtime_pred.face_prediction(
            img, 
            redis_face_db, 
            'Facial Feature', 
            ['Name', 'Role'], 
            thresh=confidence_threshold
        )
        
        # Check if it's time to save logs
        time_now = time.time()
        diff_time = time_now - set_time
        if diff_time >= wait_time:
            realtime_pred.saveLogs_redis()
            set_time = time.time()  # Reset timer
            
        return av.VideoFrame.from_ndarray(pred_img, format="bgr24")
    
    # Webcam feed with face recognition
    st.markdown("<div class='webcam-container'>", unsafe_allow_html=True)
    webrtc_streamer(
        key="realTimePrediction", 
        video_frame_callback=video_frame_callback,
        rtc_configuration={"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]},
        media_stream_constraints={"video": True, "audio": False},
    )
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Instructions
    st.info("""
    **Instructions:**
    1. Stand in front of the camera
    2. Wait for the system to recognize your face
    3. Your attendance will be logged automatically
    4. The system records entry and exit times
    """)
    
    st.markdown("</div>", unsafe_allow_html=True)

with right_col:
    # User database card
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("<h2 class='section-title'>👥 Registered Users</h2>", unsafe_allow_html=True)
    
    # Display registered users
    if not redis_face_db.empty:
        st.dataframe(
            redis_face_db[['Name', 'Role']].sort_values('Name'),
            use_container_width=True,
            hide_index=True,
            height=200
        )
        
        # Display statistics
        total_users = len(redis_face_db)
        students = len(redis_face_db[redis_face_db['Role'] == 'Student'])
        teachers = len(redis_face_db[redis_face_db['Role'] == 'Teacher'])
        
        st.markdown("<br>", unsafe_allow_html=True)
        stats_cols = st.columns(3)
        with stats_cols[0]:
            st.markdown(f"""
            <div class="stats-box">
                <div class="stats-number">{total_users}</div>
                <div class="stats-label">Total Users</div>
            </div>
            """, unsafe_allow_html=True)
        with stats_cols[1]:
            st.markdown(f"""
            <div class="stats-box">
                <div class="stats-number">{students}</div>
                <div class="stats-label">Students</div>
            </div>
            """, unsafe_allow_html=True)
        with stats_cols[2]:
            st.markdown(f"""
            <div class="stats-box">
                <div class="stats-number">{teachers}</div>
                <div class="stats-label">Teachers</div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.warning("No registered users found in the database.")
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Recent activity card
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("<h2 class='section-title'>🕒 Recent Activity</h2>", unsafe_allow_html=True)
    
    # Load and display recent logs
    try:
        logs_list = face_rec.r.lrange('attendance:logs', 0, 9)  # Get last 10 logs
        
        if logs_list:
            # Convert bytes to string and create dataframe
            logs_string = [log.decode('utf-8').split('@') for log in logs_list]
            logs_df = pd.DataFrame(logs_string, columns=['Name', 'Role', 'Timestamp'])
            
            # Format timestamp
            logs_df['Timestamp'] = pd.to_datetime(logs_df['Timestamp'],format='ISO8601')
            logs_df['Time'] = logs_df['Timestamp'].dt.strftime('%H:%M:%S')
            logs_df['Date'] = logs_df['Timestamp'].dt.strftime('%Y-%m-%d')
            
            # Display recent logs
            st.dataframe(
                logs_df[['Name', 'Role', 'Time', 'Date']],
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("No recent activity logged.")
    except Exception as e:
        st.error(f"Error loading logs: {e}")
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Quick actions
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("<h2 class='section-title'>⚡ Quick Actions</h2>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📊 View Reports", use_container_width=True):
            st.switch_page("pages/report.py")
    with col2:
        if st.button("📝 Add New User", use_container_width=True):
            st.switch_page("pages/page1.py")
    
    st.markdown("</div>", unsafe_allow_html=True)

# Footer
st.markdown("<div class='footer'>AI-Powered Attendance System • © 2025</div>", unsafe_allow_html=True)
