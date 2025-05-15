import streamlit as st
import pandas as pd
import datetime
import plotly.express as px
from home import face_rec
import time

# Page configuration
st.set_page_config(
    page_title="Attendance Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1E3A8A;
        margin-bottom: 1rem;
        text-align: center;
        padding: 1rem;
        border-bottom: 2px solid #E5E7EB;
    }
    .sub-header {
        font-size: 1.8rem;
        color: #1E3A8A;
        margin-top: 1rem;
    }
    .card {
        background-color: #F9FAFB;
        border-radius: 10px;
        padding: 1.5rem;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        margin-bottom: 1rem;
    }
    .metric-card {
        background-color: #EFF6FF;
        border-radius: 10px;
        padding: 1rem;
        text-align: center;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
    }
    .metric-value {
        font-size: 2rem;
        font-weight: bold;
        color: #1E40AF;
    }
    .metric-label {
        font-size: 1rem;
        color: #6B7280;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 4px 4px 0px 0px;
        padding: 10px 16px;
        background-color: #F3F4F6;
    }
    .stTabs [aria-selected="true"] {
        background-color: #DBEAFE;
        border-bottom: 2px solid #2563EB;
    }
    .dataframe {
        font-size: 14px;
    }
    .refresh-btn {
        background-color: #3B82F6;
        color: white;
        font-weight: bold;
        border-radius: 6px;
        padding: 8px 16px;
    }
    .filter-section {
        background-color: #F9FAFB;
        padding: 15px;
        border-radius: 10px;
        margin-bottom: 20px;
    }
</style>
""", unsafe_allow_html=True)

# Header section
st.markdown('<h1 class="main-header">Attendance Management Dashboard</h1>', unsafe_allow_html=True)

# Function to load logs
def load_logs(name, end=-1):
    with st.spinner('Loading attendance logs...'):
        logs_list = face_rec.r.lrange(name, start=0, end=end)
        return logs_list

# Function to process logs into DataFrame
def process_logs(logs_list):
    # Convert bytes to string
    logs_list_string = [log.decode('utf-8') for log in logs_list]
    
    # Split string by @ and create nested list
    logs_nested_list = [log.split('@') for log in logs_list_string]
    
    # Convert nested list into dataframe
    logs_df = pd.DataFrame(logs_nested_list, columns=['Name', 'Role', 'Timestamp'])
    
    # Time based analysis
    logs_df['Timestamp'] = pd.to_datetime(logs_df['Timestamp'], format='mixed')
    logs_df['Date'] = logs_df['Timestamp'].dt.date
    
    # Calculate Intime and outtime
    report_df = logs_df.groupby(by=['Date', 'Name', 'Role']).agg(
        In_time=pd.NamedAgg('Timestamp', 'min'),
        Out_time=pd.NamedAgg('Timestamp', 'max')
    ).reset_index()
    
    report_df['In_time'] = pd.to_datetime(report_df['In_time'])
    report_df['Out_time'] = pd.to_datetime(report_df['Out_time'])
    report_df['duration'] = report_df['Out_time'] - report_df['In_time']
    
    # Mark attendance status
    all_dates = report_df['Date'].unique()
    name_role = report_df[['Name', 'Role']].drop_duplicates().values.tolist()
    date_name_role_zip = []
    for dt in all_dates:
        for name, role in name_role:
            date_name_role_zip.append([dt, name, role])
            
    full_df = pd.DataFrame(date_name_role_zip, columns=['Date', 'Name', 'Role'])
    full_df = pd.merge(full_df, report_df, how='left', on=['Date', 'Name', 'Role'])
    full_df['Duration_seconds'] = full_df['duration'].dt.total_seconds()
    full_df['Duration_hours'] = full_df['Duration_seconds'] / (60 * 60)
    
    def status_marker(x):
        if pd.isna(x):
            return 'Absent'
        elif x >= 0 and x < 1:
            return 'Absent (Less than 1 hour)'
        elif x >= 1 and x < 4:
            return 'Half Day (less than 4 hours)'
        elif x >= 4 and x < 6:
            return 'Half Day'
        elif x >= 6:
            return "Present"
    
    full_df['Status'] = full_df['Duration_hours'].apply(status_marker)
    return logs_df, full_df

# Create tabs with more visual appeal
tab1, tab2, tab3 = st.tabs(["📊 Dashboard", "📋 Attendance Records", "🔍 Search & Filter"])

# Tab 1: Dashboard
with tab1:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<h2 class="sub-header">Registered Personnel</h2>', unsafe_allow_html=True)
    
    col1, col2 = st.columns([1, 3])
    
    with col1:
        if st.button('Refresh Data', key='refresh_data', help="Load the latest data from database"):
            with st.spinner('Retrieving data from database...'):
                redis_face_db = face_rec.retrive_data(name='academy:register')
                total_registered = len(redis_face_db)
                st.success(f"Successfully loaded {total_registered} records")
        
    with col2:
        try:
            redis_face_db = face_rec.retrive_data(name='academy:register')
            st.dataframe(redis_face_db[['Name', 'Role']], use_container_width=True)
            
            # Count by role for visualization
            role_counts = redis_face_db['Role'].value_counts().reset_index()
            role_counts.columns = ['Role', 'Count']
            
            fig = px.pie(role_counts, values='Count', names='Role', 
                         title='Distribution by Role',
                         color_discrete_sequence=px.colors.qualitative.Pastel)
            st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            st.info("Click 'Refresh Data' to load registered personnel")
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Recent attendance logs
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<h2 class="sub-header">Recent Attendance Activity</h2>', unsafe_allow_html=True)
    
    if st.button('Load Recent Activity', key='load_recent'):
        logs_list = load_logs(name='attendance:logs', end=10)
        if logs_list:
            st.success(f"Showing {len(logs_list)} recent logs")
            logs_list_string = [log.decode('utf-8') for log in logs_list]
            
            # Create a more structured view of logs
            for i, log in enumerate(logs_list_string):
                parts = log.split('@')
                if len(parts) >= 3:
                    name, role, timestamp = parts[0], parts[1], parts[2]
                    col1, col2, col3 = st.columns([1, 1, 2])
                    with col1:
                        st.write(f"**{name}**")
                    with col2:
                        st.write(f"{role}")
                    with col3:
                        st.write(f"{timestamp}")
                    st.divider()
        else:
            st.info("No recent logs found")
    
    st.markdown('</div>', unsafe_allow_html=True)

# Tab 2: Attendance Records 
with tab2:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<h2 class="sub-header">Complete Attendance Report</h2>', unsafe_allow_html=True)
    
    if st.button('Generate Full Report', key='gen_report'):
        with st.spinner("Processing attendance data..."):
            # Load and process logs
            logs_list = load_logs(name='attendance:logs')
            if logs_list:
                logs_df, full_df = process_logs(logs_list)
                
                # Summary metrics
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                    st.markdown(f'<div class="metric-value">{len(full_df["Date"].unique())}</div>', unsafe_allow_html=True)
                    st.markdown('<div class="metric-label">Total Days</div>', unsafe_allow_html=True)
                    st.markdown('</div>', unsafe_allow_html=True)
                
                with col2:
                    st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                    st.markdown(f'<div class="metric-value">{len(full_df["Name"].unique())}</div>', unsafe_allow_html=True)
                    st.markdown('<div class="metric-label">Total Personnel</div>', unsafe_allow_html=True)
                    st.markdown('</div>', unsafe_allow_html=True)
                
                with col3:
                    present_count = len(full_df[full_df['Status'] == 'Present'])
                    st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                    st.markdown(f'<div class="metric-value">{present_count}</div>', unsafe_allow_html=True)
                    st.markdown('<div class="metric-label">Present Records</div>', unsafe_allow_html=True)
                    st.markdown('</div>', unsafe_allow_html=True)
                
                with col4:
                    absent_count = len(full_df[full_df['Status'] == 'Absent'])
                    st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                    st.markdown(f'<div class="metric-value">{absent_count}</div>', unsafe_allow_html=True)
                    st.markdown('<div class="metric-label">Absent Records</div>', unsafe_allow_html=True)
                    st.markdown('</div>', unsafe_allow_html=True)
                
                # Status distribution visualization
                status_counts = full_df['Status'].value_counts().reset_index()
                status_counts.columns = ['Status', 'Count']
                
                fig = px.bar(status_counts, x='Status', y='Count', 
                             title='Attendance Status Distribution',
                             color='Status',
                             color_discrete_sequence=px.colors.qualitative.Bold)
                st.plotly_chart(fig, use_container_width=True)
                
                # Display the complete report table
                st.subheader("Detailed Attendance Records")
                
                # Format columns for better display
                display_df = full_df.copy()
                display_df['Date'] = pd.to_datetime(display_df['Date']).dt.strftime('%Y-%m-%d')
                display_df['In_time'] = pd.to_datetime(display_df['In_time']).dt.strftime('%H:%M:%S')
                display_df['Out_time'] = pd.to_datetime(display_df['Out_time']).dt.strftime('%H:%M:%S')
                display_df['Duration_hours'] = display_df['Duration_hours'].round(2)
                
                # Choose columns to display
                display_cols = ['Date', 'Name', 'Role', 'In_time', 'Out_time', 'Duration_hours', 'Status']
                st.dataframe(display_df[display_cols], use_container_width=True)
                
                # Option to download the report
                csv = display_df[display_cols].to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="Download Report as CSV",
                    data=csv,
                    file_name=f"attendance_report_{datetime.datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv",
                )
            else:
                st.warning("No attendance logs found. Make sure the system is recording attendance.")
    else:
        st.info("Click 'Generate Full Report' to process and display attendance data")
    
    st.markdown('</div>', unsafe_allow_html=True)

# Tab 3: Search & Filter
with tab3:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<h2 class="sub-header">Search Records</h2>', unsafe_allow_html=True)
    
    # Load data first before showing filters
    load_data_btn = st.button("Load Data for Filtering", key="load_filter_data")
    
    if load_data_btn:
        with st.spinner("Loading data..."):
            logs_list = load_logs(name='attendance:logs')
            if logs_list:
                logs_df, full_df = process_logs(logs_list)
                st.session_state['full_df'] = full_df
                st.success("Data loaded successfully! You can now filter the records.")
            else:
                st.warning("No attendance logs found to filter.")
    
    if 'full_df' in st.session_state:
        full_df = st.session_state['full_df']
        
        st.markdown('<div class="filter-section">', unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        
        with col1:
            # Date filter
            date_options = sorted([str(date) for date in full_df['Date'].unique()])
            date_in = st.selectbox('Select Date', ['ALL'] + date_options, index=0)
            
            # Name filter
            name_list = sorted(full_df['Name'].unique().tolist())
            name_in = st.selectbox('Select Name', ['ALL'] + name_list)
        
        with col2:
            # Role filter
            role_list = sorted(full_df['Role'].unique().tolist())
            role_in = st.selectbox('Select Role', ['ALL'] + role_list)
            
            # Status filter
            status_list = sorted(full_df['Status'].unique().tolist())
            status_in = st.multiselect('Select Status', ['ALL'] + status_list, default=['Present'])
        
        # Duration filter with slider
        duration_in = st.slider('Filter by minimum duration in hours', 0, 12, 0)
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Apply filters
        if st.button('Apply Filters', key='apply_filters'):
            with st.spinner("Filtering records..."):
                # Convert date column to string for comparison
                filter_df = full_df.copy()
                filter_df['Date'] = filter_df['Date'].astype(str)
                
                # Apply each filter
                if date_in != 'ALL':
                    filter_df = filter_df[filter_df['Date'] == date_in]
                
                if name_in != 'ALL':
                    filter_df = filter_df[filter_df['Name'] == name_in]
                
                if role_in != 'ALL':
                    filter_df = filter_df[filter_df['Role'] == role_in]
                
                if duration_in > 0:
                    filter_df = filter_df[filter_df['Duration_hours'] > duration_in]
                
                if 'ALL' not in status_in and len(status_in) > 0:
                    filter_df = filter_df[filter_df['Status'].isin(status_in)]
                
                if len(filter_df) > 0:
                    # Format display columns
                    display_df = filter_df.copy()
                    display_df['Date'] = pd.to_datetime(display_df['Date']).dt.strftime('%Y-%m-%d') if 'datetime' in str(type(display_df['Date'].iloc[0])) else display_df['Date']
                    if not pd.isna(display_df['In_time'].iloc[0]):
                        display_df['In_time'] = pd.to_datetime(display_df['In_time']).dt.strftime('%H:%M:%S')
                        display_df['Out_time'] = pd.to_datetime(display_df['Out_time']).dt.strftime('%H:%M:%S')
                    display_df['Duration_hours'] = display_df['Duration_hours'].round(2)
                    
                    display_cols = ['Date', 'Name', 'Role', 'In_time', 'Out_time', 'Duration_hours', 'Status']
                    st.dataframe(display_df[display_cols], use_container_width=True)
                    
                    # Option to download filtered results
                    csv = display_df[display_cols].to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label="Download Filtered Results",
                        data=csv,
                        file_name=f"filtered_attendance_{datetime.datetime.now().strftime('%Y%m%d')}.csv",
                        mime="text/csv",
                    )
                    
                    # Visual summary of filtered results
                    if len(display_df) > 1:
                        status_filtered = display_df['Status'].value_counts().reset_index()
                        status_filtered.columns = ['Status', 'Count']
                        
                        fig = px.pie(status_filtered, values='Count', names='Status', 
                                    title='Status Distribution in Filtered Results',
                                    hole=0.4,
                                    color_discrete_sequence=px.colors.qualitative.Pastel)
                        st.plotly_chart(fig, use_container_width=True)
                else:
                    st.warning("No records match your filter criteria.")
    else:
        st.info("Please click 'Load Data for Filtering' first to enable search functionality.")
    
    st.markdown('</div>', unsafe_allow_html=True)

# Footer
st.markdown("""
<div style="text-align: center; margin-top: 30px; padding: 20px; background-color: #F3F4F6; border-radius: 10px;">
    <p style="color: #6B7280; font-size: 14px;">Attendance Management System © 2025</p>
</div>
""", unsafe_allow_html=True)