import streamlit as st
import pandas as pd
from datetime import datetime
import time
import sqlite3

# Page Config
st.set_page_config(page_title="UniTransfer System", page_icon="🎓", layout="wide")

# --- Database Functions ---
def init_db():
    """Initialize the SQLite database and seed with demo data if empty."""
    conn = sqlite3.connect('transfer_system.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS requests (
            id TEXT PRIMARY KEY,
            uni_course TEXT,
            dip_course TEXT,
            grade TEXT,
            date TEXT,
            status TEXT,
            evidence TEXT
        )
    ''')
    
    # Check if empty, if so, seed
    c.execute('SELECT count(*) FROM requests')
    if c.fetchone()[0] == 0:
        seed_data = [
            ('REQ-1001', 'CS101 Intro to Programming', 'PRG100 Fundamentals of C++', 'A', '2023-10-24', 'Pending', 'transcript_sem1.pdf'),
            ('REQ-1002', 'MATH201 Calculus I', 'MAT101 Eng Math', 'B', '2023-10-25', 'Approved', 'math_syllabus.pdf'),
            ('REQ-1003', 'ENG102 Academic Writing', 'COM101 Comm Skills', 'C', '2023-10-26', 'Rejected', 'results.png')
        ]
        c.executemany('INSERT INTO requests VALUES (?,?,?,?,?,?,?)', seed_data)
        conn.commit()
    conn.close()

def get_requests():
    """Fetch all requests from the database."""
    conn = sqlite3.connect('transfer_system.db')
    conn.row_factory = sqlite3.Row # Allow accessing columns by name
    c = conn.cursor()
    c.execute('SELECT * FROM requests ORDER BY date DESC, id DESC')
    rows = c.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def add_request(req):
    """Insert a new request into the database."""
    conn = sqlite3.connect('transfer_system.db')
    c = conn.cursor()
    c.execute('INSERT INTO requests VALUES (?,?,?,?,?,?,?)',
              (req['id'], req['uni_course'], req['dip_course'], req['grade'], req['date'], req['status'], req['evidence']))
    conn.commit()
    conn.close()

def update_status(req_id, new_status):
    """Update the status of a request."""
    conn = sqlite3.connect('transfer_system.db')
    c = conn.cursor()
    c.execute('UPDATE requests SET status = ? WHERE id = ?', (new_status, req_id))
    conn.commit()
    conn.close()

# Initialize DB on load
init_db()

# --- Sidebar Navigation ---
st.sidebar.title("🎓 UniTransfer")
st.sidebar.markdown("Student Credit Transfer Portal")
role = st.sidebar.radio("Select Role", ["Student", "Admin"])

st.sidebar.divider()
st.sidebar.info("Database Mode: Data is stored in 'transfer_system.db' (SQLite).")

# --- Helper Functions ---
def get_status_color(status):
    if status == 'Approved': return 'green'
    if status == 'Rejected': return 'red'
    return 'orange'

# --- Load Data ---
# We fetch fresh data on every script rerun
requests_data = get_requests()

# --- STUDENT VIEW ---
if role == "Student":
    st.title("My Transfer Requests")
    st.markdown("Submit and track your credit transfer applications.")
    
    # Stats
    req_df = pd.DataFrame(requests_data)
    
    col1, col2, col3 = st.columns(3)
    if not req_df.empty:
        total = len(req_df)
        approved = len(req_df[req_df['status'] == 'Approved'])
        pending = len(req_df[req_df['status'] == 'Pending'])
    else:
        total, approved, pending = 0, 0, 0

    with col1:
        st.metric("Total Requests", total)
    with col2:
        st.metric("Approved", approved)
    with col3:
        st.metric("Pending", pending)
    
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
                    # Generate ID based on timestamp to ensure uniqueness roughly or count
                    new_id = f"REQ-{1000 + len(requests_data) + 1}"
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
                    
                    add_request(new_req)
                    
                    st.success(f"Request {new_id} submitted successfully!")
                    time.sleep(1) # Give time to read before rerun
                    st.rerun()
                else:
                    st.error("Please fill in all course details.")

    # Request List
    st.subheader("Application History")
    
    if len(requests_data) > 0:
        for req in requests_data:
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
    
    pending_reqs = [r for r in requests_data if r['status'] == 'Pending']
    history_reqs = [r for r in requests_data if r['status'] != 'Pending']
    
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
                    st.download_button("Download PDF", data="dummy data", file_name=req['evidence'], key=f"dl_{req['id']}")

                with col_actions:
                    st.markdown("**Action:**")
                    c_approve, c_reject = st.columns(2)
                    if c_approve.button("Approve", key=f"app_{req['id']}", type="primary"):
                        update_status(req['id'], 'Approved')
                        st.toast(f"Request {req['id']} Approved!")
                        time.sleep(0.5)
                        st.rerun()
                    
                    if c_reject.button("Reject", key=f"rej_{req['id']}"):
                        update_status(req['id'], 'Rejected')
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