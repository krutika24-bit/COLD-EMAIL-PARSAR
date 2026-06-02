import streamlit as st
import pandas as pd
from datetime import datetime
from pathlib import Path
from dataclasses import replace

from src.config import load_config, project_root
from src.loaders import load_targets
from src.email_generator import generate_email
from src.email_sender import send_or_draft, reset_send_count
from src.logger import log_outreach
from src.models import EmailDraft, ContactRecord

# Set page config for a premium wide layout
st.set_page_config(
    page_title="The Closer — Cold Email Outreach Console",
    page_icon="✉️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom premium styling for a sleek, dashboard-like look
st.markdown("""
    <style>
    /* Global styles and typography */
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', sans-serif;
    }
    
    /* Main panel cards */
    .metric-card {
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        border: 1px solid #334155;
        border-radius: 16px;
        padding: 20px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
    }
    
    .target-card {
        background-color: #1e293b;
        border: 1px solid #334155;
        border-radius: 12px;
        padding: 16px;
        margin-bottom: 12px;
        cursor: pointer;
        transition: all 0.2s ease-in-out;
    }
    
    .target-card:hover {
        border-color: #4f46e5;
        transform: translateY(-2px);
    }
    
    .target-card-active {
        background-color: #1e1b4b;
        border: 1.5px solid #6366f1;
        border-radius: 12px;
        padding: 16px;
        margin-bottom: 12px;
    }

    /* Badges */
    .badge {
        padding: 4px 10px;
        border-radius: 9999px;
        font-size: 0.75rem;
        font-weight: 600;
        display: inline-block;
    }
    .badge-pending { background-color: #334155; color: #94a3b8; }
    .badge-sent { background-color: #064e3b; color: #34d399; }
    .badge-skipped { background-color: #78350f; color: #fbbf24; }
    .badge-failed { background-color: #7f1d1d; color: #f87171; }
    .badge-drafted { background-color: #1e3a8a; color: #93c5fd; }
    
    /* Word count styling */
    .word-count-normal { color: #10b981; font-weight: 600; }
    .word-count-warn { color: #f59e0b; font-weight: 600; }
    .word-count-alert { color: #ef4444; font-weight: 600; }
    
    /* Footer */
    .footer-text {
        text-align: center;
        color: #64748b;
        font-size: 0.85rem;
        margin-top: 50px;
    }
    </style>
""", unsafe_allow_html=True)

# ----------------- SESSION STATE INITIALIZATION -----------------

# Load root project path
root = project_root()

# Load config once and store in session state
if "config" not in st.session_state:
    st.session_state.config = load_config(root / ".env")
    reset_send_count()

# Load targets
if "targets" not in st.session_state:
    input_path = root / st.session_state.config.input_path
    st.session_state.targets = load_targets(input_path if input_path.exists() else None)

# Initialize target statuses in run
if "statuses" not in st.session_state:
    st.session_state.statuses = {t.recipient_email: "Pending" for t in st.session_state.targets}

# Initialize email drafts cache (stores edits/LLM versions dynamically)
if "drafts_cache" not in st.session_state:
    st.session_state.drafts_cache = {}

# Initialize selected index
if "selected_index" not in st.session_state:
    st.session_state.selected_index = 0

# ----------------- HELPER FUNCTIONS -----------------

def get_current_record() -> ContactRecord | None:
    if 0 <= st.session_state.selected_index < len(st.session_state.targets):
        return st.session_state.targets[st.session_state.selected_index]
    return None

def get_draft(record: ContactRecord) -> EmailDraft:
    email = record.recipient_email
    if email not in st.session_state.drafts_cache:
        # Generate initial draft using the template
        st.session_state.drafts_cache[email] = generate_email(record, st.session_state.config)
    return st.session_state.drafts_cache[email]

def update_draft(record: ContactRecord, subject: str, body: str) -> None:
    st.session_state.drafts_cache[record.recipient_email] = EmailDraft(subject=subject, body=body)

def reset_draft(record: ContactRecord) -> None:
    # Temporarily remove cache to regenerate from scratch
    if record.recipient_email in st.session_state.drafts_cache:
        del st.session_state.drafts_cache[record.recipient_email]
    st.rerun()

# ----------------- SIDEBAR: CONTROLS & METRICS -----------------

st.sidebar.markdown("<h2 style='margin-bottom:0;'>✉️ The Closer</h2>", unsafe_allow_html=True)
st.sidebar.markdown("<p style='color:#64748b; font-size:0.85rem; margin-top:0;'>Cold Email Outreach Dashboard</p>", unsafe_allow_html=True)
st.sidebar.markdown("---")

# Editable configurations
st.sidebar.subheader("App Controls")
dry_run = st.sidebar.toggle("Dry Run (Simulated)", value=st.session_state.config.dry_run)
use_llm = st.sidebar.toggle("Use LLM Polishing (Groq)", value=st.session_state.config.use_llm)

# Update config if toggled
if dry_run != st.session_state.config.dry_run or use_llm != st.session_state.config.use_llm:
    st.session_state.config = replace(st.session_state.config, dry_run=dry_run, use_llm=use_llm)
    # Clear cache of pending targets to allow regeneration with/without LLM
    for email, status in st.session_state.statuses.items():
        if status == "Pending" and email in st.session_state.drafts_cache:
            del st.session_state.drafts_cache[email]
    st.rerun()

# Groq Key status indicator
if use_llm:
    st.sidebar.markdown(f"**Model:** `{st.session_state.config.groq_model}`")
    if st.session_state.config.groq_api_key:
         st.sidebar.success("Groq API Key Active")
    else:
         st.sidebar.error("Missing GROQ_API_KEY in .env")

st.sidebar.markdown("---")

# Batch run metrics
st.sidebar.subheader("Batch Progress")
total = len(st.session_state.targets)
sent = sum(1 for s in st.session_state.statuses.values() if s in ("Sent", "Drafted"))
skipped = sum(1 for s in st.session_state.statuses.values() if s == "Skipped")
failed = sum(1 for s in st.session_state.statuses.values() if s == "Failed")
pending = sum(1 for s in st.session_state.statuses.values() if s == "Pending")

# Circular / Progress-like overview in sidebar
st.sidebar.metric("Pending Tasks", f"{pending} / {total}")
st.sidebar.progress(1.0 - (pending / total) if total > 0 else 0)

col_s, col_sk, col_f = st.sidebar.columns(3)
col_s.metric("Sent", sent)
col_sk.metric("Skipped", skipped)
col_f.metric("Failed", failed)

# Reset Button to start batch over
if st.sidebar.button("🔄 Reset Current Batch", use_container_width=True):
    st.session_state.statuses = {t.recipient_email: "Pending" for t in st.session_state.targets}
    st.session_state.drafts_cache.clear()
    st.session_state.selected_index = 0
    reset_send_count()
    st.rerun()

# ----------------- MAIN LAYOUT -----------------

col_list, col_editor = st.columns([1, 2], gap="large")

# --- Column 1: Targets List Navigation ---
with col_list:
    st.subheader("Outreach Targets")
    st.markdown("<p style='color:#64748b; font-size:0.85rem; margin-top:-10px;'>Select a contact to review and edit their outreach template.</p>", unsafe_allow_html=True)
    
    for idx, t in enumerate(st.session_state.targets):
        status = st.session_state.statuses.get(t.recipient_email, "Pending")
        
        # Determine status badge text and class
        badge_style = "badge-pending"
        badge_text = "Pending"
        if status == "Sent":
            badge_style = "badge-sent"
            badge_text = "Sent"
        elif status == "Drafted":
            badge_style = "badge-drafted"
            badge_text = "Drafted"
        elif status == "Skipped":
            badge_style = "badge-skipped"
            badge_text = "Skipped"
        elif status == "Failed":
            badge_style = "badge-failed"
            badge_text = "Failed"
            
        is_active = idx == st.session_state.selected_index
        card_class = "target-card-active" if is_active else "target-card"
        
        # We wrap in a Streamlit button to make it interactive, but styled as a card
        label = f"**{t.company}** — {t.role}\n\nRecipient: {t.recipient_email}"
        
        with st.container():
            st.markdown(f"""
                <div class="{card_class}">
                    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
                        <span style="font-weight:700; font-size:1.05rem;">{t.company}</span>
                        <span class="badge {badge_style}">{badge_text}</span>
                    </div>
                    <div style="font-size:0.85rem; color:#94a3b8; font-weight:500;">{t.role}</div>
                    <div style="font-size:0.8rem; color:#64748b; margin-top:4px;">{t.recipient_email}</div>
                </div>
            """, unsafe_allow_html=True)
            
            # Clickable trigger to set active index
            if st.button(f"Open Editor", key=f"sel_{idx}", use_container_width=True):
                st.session_state.selected_index = idx
                st.rerun()

# --- Column 2: Outreach Editor & Actions ---
with col_editor:
    record = get_current_record()
    
    if record:
        st.subheader("Email Review & Editor")
        status = st.session_state.statuses[record.recipient_email]
        
        # Display target context in a neat visual card
        st.markdown(f"""
            <div class="metric-card" style="margin-bottom: 20px;">
                <h4 style="margin-top:0; color:#818cf8;">Target Context</h4>
                <table style="width:100%; font-size:0.9rem; border-collapse:collapse; color:#cbd5e1;">
                    <tr>
                        <td style="padding:4px 0; font-weight:600; width:140px; color:#94a3b8;">Recipient Name:</td>
                        <td style="padding:4px 0;">{record.display_name()}</td>
                    </tr>
                    <tr>
                        <td style="padding:4px 0; font-weight:600; color:#94a3b8;">Candidate Name:</td>
                        <td style="padding:4px 0;">{record.candidate_name}</td>
                    </tr>
                    <tr>
                        <td style="padding:4px 0; font-weight:600; color:#94a3b8;">Background:</td>
                        <td style="padding:4px 0;">{record.candidate_background}</td>
                    </tr>
                    <tr>
                        <td style="padding:4px 0; font-weight:600; color:#94a3b8;">Personalization Hook:</td>
                        <td style="padding:4px 0; font-style:italic; color:#e2e8f0;">"{record.personalization_note or 'Using default job listing fallback hook.'}"</td>
                    </tr>
                </table>
            </div>
        """, unsafe_allow_html=True)
        
        # Retrieve the draft (loads cache or generates fresh)
        draft = get_draft(record)
        
        # Text fields for Subject and Body
        subject_input = st.text_input("Subject Line", value=draft.subject, key=f"subj_{record.recipient_email}")
        body_input = st.text_area("Email Body", value=draft.body, height=260, key=f"body_{record.recipient_email}")
        
        # Update drafts cache immediately on edits
        update_draft(record, subject_input, body_input)
        
        # Word counts and warning indicator
        word_count = len(body_input.split())
        word_class = "word-count-normal"
        word_warning = ""
        
        if word_count > 150:
            word_class = "word-count-alert"
            word_warning = "⚠️ **Warning: Body exceeds the standard 150-word constraint.**"
        elif word_count > 130:
            word_class = "word-count-warn"
            word_warning = "⚠️ **Note: Approaching the 150-word constraint limit.**"
            
        st.markdown(f"Word Count: <span class='{word_class}'>{word_count} / 150</span> words {word_warning}", unsafe_allow_html=True)
        st.markdown("---")
        
        # Action Buttons
        col_act1, col_act2, col_act3 = st.columns([2, 1, 1])
        
        # Send / Draft Button
        action_label = "Draft Email" if st.session_state.config.email_mode == "draft" else "Send Email"
        if status in ("Sent", "Drafted"):
            col_act1.info(f"This email has already been successfully {status.lower()}!")
        elif status == "Skipped":
            col_act1.warning("This target was skipped. Re-run or reset batch to send.")
        else:
            # Action: Dispatch email
            if col_act1.button(f"🚀 {action_label}", type="primary", use_container_width=True):
                with st.spinner("Processing outreach..."):
                    # Retrieve the edited draft
                    final_draft = EmailDraft(subject=subject_input, body=body_input)
                    result = send_or_draft(final_draft, record, st.session_state.config)
                    
                    if result.status == "failed":
                        st.session_state.statuses[record.recipient_email] = "Failed"
                        st.error(f"Failed to dispatch: {result.error_message}")
                    else:
                        status_str = "Drafted" if st.session_state.config.email_mode == "draft" else "Sent"
                        st.session_state.statuses[record.recipient_email] = status_str
                        # Log to CSV
                        log_file = root / st.session_state.config.log_path
                        log_outreach(
                            record,
                            final_draft,
                            result.status,
                            log_path=log_file,
                            error_message=result.error_message,
                        )
                        st.success(f"Successfully {status_str.lower()} email to {record.recipient_email}!")
                        st.rerun()
                        
            # Action: Skip target
            if col_act2.button("⏭️ Skip Target", use_container_width=True):
                st.session_state.statuses[record.recipient_email] = "Skipped"
                # Log to CSV as skipped
                log_file = root / st.session_state.config.log_path
                log_outreach(
                    record,
                    EmailDraft(subject=subject_input, body=body_input),
                    "skipped",
                    log_path=log_file
                )
                st.warning("Target marked as skipped.")
                # Move to next target if available
                if st.session_state.selected_index < len(st.session_state.targets) - 1:
                    st.session_state.selected_index += 1
                st.rerun()
                
            # Action: Reset template
            if col_act3.button("🔄 Reset Draft", use_container_width=True):
                reset_draft(record)
                
    else:
        st.info("No targets available. Check your contacts input configuration.")

# --- Logs & Audit Trail Panel ---
st.markdown("---")
st.subheader("📊 Outreach Audit Log")
st.markdown("<p style='color:#64748b; font-size:0.85rem; margin-top:-10px;'>History of outreach attempts saved locally in `outreach_log.csv`.</p>", unsafe_allow_html=True)

log_file_path = root / st.session_state.config.log_path
if log_file_path.exists() and log_file_path.stat().st_size > 0:
    try:
        df_logs = pd.read_csv(log_file_path)
        # Parse timestamp for readability
        df_logs['timestamp'] = pd.to_datetime(df_logs['timestamp']).dt.strftime('%Y-%m-%d %H:%M:%S')
        # Display log in streamlit table
        st.dataframe(
            df_logs.sort_index(ascending=False), # Show most recent logs first
            use_container_width=True,
            column_config={
                "timestamp": st.column_config.TextColumn("Date & Time"),
                "recipient_email": st.column_config.TextColumn("Recipient"),
                "company": st.column_config.TextColumn("Company"),
                "role": st.column_config.TextColumn("Role"),
                "subject": st.column_config.TextColumn("Subject Line"),
                "status": st.column_config.TextColumn("Status"),
                "error_message": st.column_config.TextColumn("Errors")
            }
        )
    except Exception as e:
        st.error(f"Could not load log file: {e}")
else:
    st.info("No outreach attempts logged yet. Send or skip targets to start auditing.")

# Footer
st.markdown("<div class='footer-text'>The Closer — Built with Streamlit for Sprint 3. Safety first, outreach second.</div>", unsafe_allow_html=True)
