import streamlit as st
import pandas as pd
from datetime import datetime
import time

# Page Config
st.set_page_config(page_title="UniTransfer System", page_icon="🎓", layout="wide")

# --- State Management ---
if 'requests' not in st.session_state:
    st.session_state.requests = [
        {'id': 'REQ-1001', 'uni_course': 'CS101 Intro to Programming', 'dip_course': 'PRG100 Fundamentals of C++', 'grade': 'A', 'date': '2023-10-24', 'status': 'Pending', 'evidence': 'transcript_sem1.pdf'},
        {'id': 'REQ-1002', 'uni_course': 'MATH201 Calculus I', 'dip_course': 'MAT101 Eng Math', 'grade': 'B', 'date': '2023-10-25', 'status': 'Approved', 'evidence': 'math_syllabus.pdf'},
        {'id': 'REQ-1003', 'uni_course': 'ENG102 Academic Writing', 'dip_course': 'COM101 Comm Skills', 'grade': 'C', 'date': '2023-10-26', 'status': 'Rejected', 'evidence': 'results.png'}
    ]

# --- Sidebar Navigation ---
st.sidebar.title("🎓 UniTransfer")
st.sidebar.markdown("Student Credit Transfer Portal")
role = st.sidebar.radio("Select Role", ["Student", "Admin"])

st.sidebar.divider()
st.sidebar.info("Prototype Mode: Data is stored in session state and resets if the server restarts.")

# --- Helper Functions ---
def get_status_color(status):
    if status == 'Approved': return 'green'
    if status == 'Rejected': return 'red'
    return 'orange'

# --- STUDENT VIEW ---
if role == "Student":
    st.title("My Transfer Requests")
    st.markdown("Submit and track your credit transfer applications.")
    
    # Stats
    req_df = pd.DataFrame(st.session_state.requests)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Requests", len(req_df))
    with col2:
        st.metric("Approved", len(req_df[req_df['status'] == 'Approved']))
    with col3:
        st.metric("Pending", len(req_df[req_df['status'] == 'Pending']))
    
    st.divider()

    # New Request Form
    with st.expander("📝 Create New Request", expanded=False):
        with st.form("new_request_form"):
            c1, c2 = st.columns(2)
            with c1:
                uni_course = st.text_input("Target University Course", placeholder="e.g. CS101 Intro to CS")
                dip_course = st.text_input("Previous Diploma Course", placeholder="e.g. DIT105 Programming")
            with c2:
                grade = st.selectbox("Grade Obtained", ["A+", "A", "A-", "B+", "B", "C", "D"])
                evidence = st.file_uploader("Upload Transcript/Syllabus", type=['pdf', 'png', 'jpg'])
            
            submitted = st.form_submit_button("Submit Application")
            
            if submitted:
                if uni_course and dip_course and grade:
                    new_id = f"REQ-{1000 + len(st.session_state.requests) + 1}"
                    file_name = evidence.name if evidence else "manual_submission.pdf"
                    
                    new_req = {
                        'id': new_id,
                        'uni_course': uni_course,
                        'dip_course': dip_course,
                        'grade': grade,
                        'date': datetime.now().strftime("%Y-%m-%d"),
                        'status': 'Pending',
                        'evidence': file_name
                    }
                    st.session_state.requests.insert(0, new_req) # Add to top
                    st.success(f"Request {new_id} submitted successfully!")
                    time.sleep(1) # Give time to read before rerun
                    st.rerun()
                else:
                    st.error("Please fill in all course details.")

    # Request List
    st.subheader("Application History")
    
    if len(st.session_state.requests) > 0:
        # Custom display for better UX than raw dataframe
        for req in st.session_state.requests:
            with st.container(border=True):
                c1, c2, c3, c4 = st.columns([2, 3, 2, 2])
                with c1:
                    st.caption(f"ID: {req['id']}")
                    st.markdown(f"**{req['date']}**")
                with c2:
                    st.markdown(f"**{req['uni_course']}**")
                    st.caption(f"from: {req['dip_course']}")
                with c3:
                    st.caption("Grade")
                    st.markdown(f"**{req['grade']}**")
                with c4:
                    color = get_status_color(req['status'])
                    st.markdown(f":{color}[{req['status']}]")
    else:
        st.info("No requests found.")


# --- ADMIN VIEW ---
elif role == "Admin":
    st.title("Admin Dashboard")
    st.markdown("Review student transfer credit applications.")
    
    pending_reqs = [r for r in st.session_state.requests if r['status'] == 'Pending']
    history_reqs = [r for r in st.session_state.requests if r['status'] != 'Pending']
    
    # Stats
    col1, col2 = st.columns(2)
    with col1:
        st.info(f"Pending Review: {len(pending_reqs)}")
    with col2:
        approval_rate = 0
        if len(history_reqs) > 0:
            approved = len([r for r in history_reqs if r['status'] == 'Approved'])
            approval_rate = int((approved / len(history_reqs)) * 100)
        st.metric("Approval Rate", f"{approval_rate}%")

    st.divider()

    # Queue
    st.subheader("⏳ Pending Review Queue")
    
    if not pending_reqs:
        st.success("All caught up! No pending requests.")
    else:
        for req in pending_reqs:
            with st.container(border=True):
                col_details, col_evidence, col_actions = st.columns([3, 2, 2])
                
                with col_details:
                    st.markdown(f"### {req['uni_course']}")
                    st.markdown(f"**Student Grade:** {req['grade']} | **From:** {req['dip_course']}")
                    st.caption(f"ID: {req['id']} • Submitted: {req['date']}")
                
                with col_evidence:
                    st.markdown("**Evidence:**")
                    st.code(req['evidence'], language="text")
                    # In a real app, this would be a download_button
                    st.download_button("Download PDF", data="dummy data", file_name=req['evidence'], key=f"dl_{req['id']}")

                with col_actions:
                    st.markdown("**Action:**")
                    c_approve, c_reject = st.columns(2)
                    if c_approve.button("Approve", key=f"app_{req['id']}", type="primary"):
                        req['status'] = 'Approved'
                        st.toast(f"Request {req['id']} Approved!")
                        time.sleep(0.5)
                        st.rerun()
                    
                    if c_reject.button("Reject", key=f"rej_{req['id']}"):
                        req['status'] = 'Rejected'
                        st.toast(f"Request {req['id']} Rejected.")
                        time.sleep(0.5)
                        st.rerun()

    st.divider()
    
    # History
    st.subheader("📜 Recent History")
    if history_reqs:
        # Prepare data for simple table
        hist_data = []
        for r in history_reqs:
            hist_data.append({
                "ID": r['id'],
                "Course": r['uni_course'],
                "Status": r['status'],
                "Date": r['date']
            })
        st.dataframe(pd.DataFrame(hist_data), use_container_width=True, hide_index=True)