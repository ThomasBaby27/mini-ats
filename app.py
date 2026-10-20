import sqlite3
import pandas as pd
import streamlit as st

# Page configuration
st.set_page_config(page_title="Mini ATS Dashboard", layout="wide")

# Database Initialization
conn = sqlite3.connect("ats.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute(
    """
    CREATE TABLE IF NOT EXISTS candidates (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT NOT NULL,
        role TEXT NOT NULL,
        stage TEXT NOT NULL,
        applied_date DATE DEFAULT (DATE('now'))
    )
"""
)
conn.commit()

# Seed default data if table is empty
cursor.execute("SELECT COUNT(*) FROM candidates")
if cursor.fetchone()[0] == 0:
    sample_data = [
        (
            "Aarav Sharma",
            "aarav@example.com",
            "Full Stack Developer",
            "Interview",
        ),
        ("Priya Nair", "priya@example.com", "Frontend Engineer", "Offer"),
        ("Rohan Verma", "rohan@example.com", "Backend Developer", "Applied"),
        ("Sneha Patel", "sneha@example.com", "Full Stack Developer", "Screening"),
        ("Vikram Das", "vikram@example.com", "DevOps Engineer", "Rejected"),
    ]
    cursor.executemany(
        "INSERT INTO candidates (name, email, role, stage) VALUES (?, ?, ?, ?)",
        sample_data,
    )
    conn.commit()

# Main Header
st.title("Mini Applicant Tracking System (ATS)")
st.caption(
    "Manage candidates, update hiring pipeline stages, and track recruitment metrics"
)

# Top Metric Cards
df_all = pd.read_sql_query("SELECT * FROM candidates", conn)

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Applicants", len(df_all))
col2.metric("In Interview", len(df_all[df_all["stage"] == "Interview"]))
col3.metric("Offers Extended", len(df_all[df_all["stage"] == "Offer"]))
col4.metric("Rejected", len(df_all[df_all["stage"] == "Rejected"]))

st.divider()

# Sidebar: Add Candidate Form
with st.sidebar:
    st.header("➕ Add Candidate")
    with st.form("add_candidate_form", clear_on_submit=True):
        name = st.text_input("Candidate Name")
        email = st.text_input("Email Address")
        role = st.text_input("Applied Role", value="Full Stack Developer")
        stage = st.selectbox(
            "Initial Stage",
            ["Applied", "Screening", "Interview", "Offer", "Rejected"],
        )
        submitted = st.form_submit_button("Submit Candidate")

        if submitted:
            if name.strip() and email.strip():
                cursor.execute(
                    "INSERT INTO candidates (name, email, role, stage) VALUES (?, ?, ?, ?)",
                    (name, email, role, stage),
                )
                conn.commit()
                st.success(f"Added {name} successfully!")
                st.rerun()
            else:
                st.error("Please fill in both Name and Email.")

# Search and Stage Filters
f_col1, f_col2 = st.columns([3, 1])
with f_col1:
    search_query = st.text_input(
        "🔍 Search by name, email, or role", placeholder="Search candidates..."
    )
with f_col2:
    stage_filter = st.selectbox(
        "Filter by Stage",
        ["All", "Applied", "Screening", "Interview", "Offer", "Rejected"],
    )

# Filter Logic
query = "SELECT * FROM candidates WHERE 1=1"
params = []

if search_query:
    query += " AND (name LIKE ? OR email LIKE ? OR role LIKE ?)"
    wildcard = f"%{search_query}%"
    params.extend([wildcard, wildcard, wildcard])

if stage_filter != "All":
    query += " AND stage = ?"
    params.append(stage_filter)

filtered_df = pd.read_sql_query(query, conn, params=params)

# Candidate Management Section
st.subheader(f"Candidates ({len(filtered_df)})")

if filtered_df.empty:
    st.info("No candidates match your current search/filter criteria.")
else:
    for index, row in filtered_df.iterrows():
        c_col1, c_col2, c_col3, c_col4 = st.columns([3, 2, 2, 2])

        with c_col1:
            st.markdown(f"**{row['name']}**")
            st.caption(f"{row['email']}")

        with c_col2:
            st.write(f"Role: **{row['role']}**")

        with c_col3:
            st.write(f"Date: `{row['applied_date']}`")

        with c_col4:
            current_stage = row["stage"]
            new_stage = st.selectbox(
                "Stage",
                ["Applied", "Screening", "Interview", "Offer", "Rejected"],
                index=[
                    "Applied",
                    "Screening",
                    "Interview",
                    "Offer",
                    "Rejected",
                ].index(current_stage),
                key=f"stage_select_{row['id']}",
            )

            if new_stage != current_stage:
                cursor.execute(
                    "UPDATE candidates SET stage = ? WHERE id = ?",
                    (new_stage, row["id"]),
                )
                conn.commit()
                st.rerun()

        st.markdown("---")