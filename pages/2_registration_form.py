import streamlit as st
import face_rec
import cv2
import numpy as np
from streamlit_webrtc import webrtc_streamer
import av
import time

# Page configuration
st.set_page_config(
    page_title="User Registration | AI Attendance",
    page_icon="📝",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        color: #1E88E5;
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
    .instructions {
        background-color: #e8f4f8;
        border-left: 4px solid #1E88E5;
        padding: 15px;
        margin-bottom: 20px;
        border-radius: 4px;
    }
    .submit-button {
        background-color: #4CAF50;
        color: white;
        padding: 12px 24px;
        font-size: 16px;
        border-radius: 4px;
        border: none;
        cursor: pointer;
        width: 100%;
    }
    .input-label {
        font-weight: 600;
        color: #424242;
        margin-bottom: 8px;
    }
    .webcam-container {
        border: 2px dashed #1E88E5;
        border-radius: 8px;
        padding: 10px;
        margin-top: 10px;
    }
    .step-counter {
        background-color: #1E88E5;
        color: white;
        border-radius: 50%;
        width: 25px;
        height: 25px;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        margin-right: 10px;
    }
    .step-title {
        font-size: 1.2rem;
        font-weight: 600;
        color: #1E88E5;
    }
    .footer {
        text-align: center;
        margin-top: 30px;
        padding: 20px;
        color: #6c757d;
        border-top: 1px solid #e9ecef;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown("<h1 class='main-header'>📝 User Registration Form</h1>", unsafe_allow_html=True)

# Progress bar for registration process
step = 1
steps = ["Enter Information", "Capture Face", "Submit Registration"]
progress = (step / len(steps))

st.progress(progress, text=f"Step {step} of {len(steps)}: {steps[step-1]}")

# Main content in columns
left_col, right_col = st.columns([3, 2])

with left_col:
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    
    # Instructions
    st.markdown("<div class='instructions'>", unsafe_allow_html=True)
    st.markdown("""
    🔹 Please complete all fields below
    🔹 Face capture requires good lighting
    🔹 Look directly at the camera
    🔹 Remove glasses and face coverings
    """)
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Initialize registration form
    registration_form = face_rec.RegistrationForm()
    
    # Step 1: Collect person name and role
    st.markdown("<div class='step-title'><span class='step-counter'>1</span> Personal Information</div>", unsafe_allow_html=True)
    st.markdown("<p class='input-label'>Full Name</p>", unsafe_allow_html=True)
    person_name = st.text_input(label="", placeholder="Enter your first and last name", label_visibility="collapsed")
    
    st.markdown("<p class='input-label'>Select Role</p>", unsafe_allow_html=True)
    role = st.selectbox(label="", options=("Student", "Teacher"), label_visibility="collapsed")
    
    # Additional information (optional)
    with st.expander("Additional Information (Optional)"):
        st.text_input("Email Address")
        st.text_input("ID Number")
        col1, col2 = st.columns(2)
        with col1:
            st.date_input("Date of Birth")
        with col2:
            st.selectbox("Department", ["Computer Science", "Engineering", "Business", "Arts", "Science"])
    
    st.markdown("</div>", unsafe_allow_html=True)

with right_col:
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    
    # Step 2: Collect facial embedding of that person
    st.markdown("<div class='step-title'><span class='step-counter'>2</span> Face Capture</div>", unsafe_allow_html=True)
    st.write("Please position your face in the frame and wait for the system to capture your facial features.")
    
    # Face capture status indicators
    status_placeholder = st.empty()
    
    # Custom face capture function
    def video_callback_func(frame):
        img = frame.to_ndarray(format='bgr24')
        reg_img, embedding = registration_form.get_embedding(img)
        
        # Save embedding if available
        if embedding is not None:
            with open('face_embedding.txt', mode='ab') as f:
                np.savetxt(f, embedding)
            status_placeholder.success("✅ Face captured successfully!")
        
        return av.VideoFrame.from_ndarray(reg_img, format='bgr24')
    
    # Webcam feed
    st.markdown("<div class='webcam-container'>", unsafe_allow_html=True)
    webrtc_streamer(
        key='registration', 
        video_frame_callback=video_callback_func,
        rtc_configuration={"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]},
        media_stream_constraints={"video": True, "audio": False},
    )
    st.markdown("</div>", unsafe_allow_html=True)
    
    st.markdown("</div>", unsafe_allow_html=True)

# Step 3: Submit button and save the data
st.markdown("<div class='card'>", unsafe_allow_html=True)
st.markdown("<div class='step-title'><span class='step-counter'>3</span> Complete Registration</div>", unsafe_allow_html=True)

col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    if st.button("Register User", key="submit_button", use_container_width=True):
        with st.spinner("Processing registration..."):
            time.sleep(1)  # Simulate processing
            return_val = registration_form.save_data_in_redis_db(person_name, role)
            
            if return_val == True:
                st.success(f"✅ {person_name} registered successfully!")
                st.balloons()
                # Add a timer for redirecting
                st.write("Redirecting to home page in 5 seconds...")
                time.sleep(5)
                st.switch_page("home.py")
            elif return_val == 'name_false':
                st.error("❌ Please enter a valid name. Name cannot be empty or contain only spaces.")
            elif return_val == 'file_false':
                st.error("❌ Face embedding data not found. Please refresh the page and try again.")

st.markdown("</div>", unsafe_allow_html=True)

# Footer
st.markdown("<div class='footer'>AI-Powered Attendance System • © 2025</div>", unsafe_allow_html=True)
