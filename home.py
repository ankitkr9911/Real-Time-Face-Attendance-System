import streamlit as st
import time
from PIL import Image
import base64

# Page configuration
st.set_page_config(
    page_title="AI Attendance System",
    page_icon="👁️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better appearance
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1E88E5;
        text-align: center;
        margin-bottom: 1rem;
        font-weight: 700;
    }
    .sub-header {
        font-size: 1.5rem;
        color: #424242;
        margin-top: 2rem;
        font-weight: 600;
    }
    .card {
        border-radius: 5px;
        padding: 20px;
        background-color: #f8f9fa;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        margin-bottom: 20px;
    }
    .success-box {
        background-color: #d4edda;
        color: #155724;
        padding: 15px;
        border-radius: 5px;
        margin-bottom: 20px;
    }
    .feature-icon {
        font-size: 1.8rem;
        margin-right: 10px;
    }
    .footer {
        text-align: center;
        margin-top: 50px;
        padding: 20px;
        color: #6c757d;
        border-top: 1px solid #e9ecef;
    }
</style>
""", unsafe_allow_html=True)

# Header with logo
col1, col2, col3 = st.columns([1, 3, 1])
with col2:
    st.markdown("<h1 class='main-header'>🔷 AI-Powered Attendance System</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; font-size: 1.2rem;'>Smart Recognition • Secure • Efficient</p>", unsafe_allow_html=True)

# Create two columns for content
left_col, right_col = st.columns([2, 1])

with left_col:
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    with st.spinner('🔄 Loading Models and Connecting to Database...'):
        try:
            import face_rec
            time.sleep(2)  # Simulating loading time
            st.markdown("<div class='success-box'><b>✅ Face Recognition Model:</b> Loaded Successfully</div>", unsafe_allow_html=True)
            st.markdown("<div class='success-box'><b>✅ Database Connection:</b> Connected to Redis DB</div>", unsafe_allow_html=True)
        except Exception as e:
            st.error(f"Error loading system components: {e}")
    st.markdown("</div>", unsafe_allow_html=True)
    
    # System features
    st.markdown("<h2 class='sub-header'>System Features</h2>", unsafe_allow_html=True)
    
    features = [
        ("👁️ Real-time Face Recognition", "Instant identification of registered users using advanced ML models"),
        ("⏱️ Automatic Attendance Logging", "Timestamps recorded automatically with entry and exit times"),
        ("🔐 Role-based Access Management", "Different access levels for students and teachers"),
        ("📊 Comprehensive Reports", "Generate detailed attendance reports with various filters"),
        ("⚡ High Performance", "Optimized for speed even with multiple simultaneous recognitions")
    ]
    
    for icon_title, description in features:
        st.markdown(f"""
        <div style='display: flex; align-items: center; margin-bottom: 15px;'>
            <div class='feature-icon'>{icon_title.split()[0]}</div>
            <div>
                <b>{" ".join(icon_title.split()[1:])}</b><br>
                <span style='color: #6c757d; font-size: 0.9rem;'>{description}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

with right_col:
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align: center;'>Quick Navigation</h3>", unsafe_allow_html=True)
    
    # Quick action buttons
    if st.button("📝 Register New User", use_container_width=True):
        st.switch_page("pages/2_registration_form.py")
        
    if st.button("🟢 Start Attendance Tracking", use_container_width=True):
        st.switch_page("pages/1_real_time_prediction.py")
        
    if st.button("📊 View Attendance Reports", use_container_width=True):
        st.switch_page("pages/3_report.py")
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    # System status
    st.markdown("<div class='card' style='margin-top: 20px;'>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align: center;'>System Status</h3>", unsafe_allow_html=True)
    
    # Display some system metrics
    col1, col2 = st.columns(2)
    with col1:
        st.metric(label="System Status", value="Online", delta="Active")
    with col2:
        st.metric(label="Database Status", value="Connected", delta="Active")
    
    st.markdown("</div>", unsafe_allow_html=True)

# Footer
st.markdown("<div class='footer'>AI-Powered Attendance System • © 2025</div>", unsafe_allow_html=True)