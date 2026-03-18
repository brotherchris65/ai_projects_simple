import json
import imaplib
import re
import ssl
from email import message_from_bytes
from email.header import decode_header
from email.utils import parseaddr, parsedate_to_datetime
from html import unescape
from datetime import datetime, timedelta, timezone
from pathlib import Path

import certifi
import pandas as pd
import streamlit as st

DEFAULT_EMAIL_KEYWORDS = [
    "interview",
    "recruiter",
    "application",
    "applied",
    "role",
    "position",
    "rejection",
    "follow up",
    "assessment",
    "hiring",
]

FEEDBACK_FILE = Path(__file__).with_name("feedback_rules.json")


def load_feedback_rules() -> dict:
    if not FEEDBACK_FILE.exists():
        return {"blocked_senders": [], "blocked_keywords": []}

    try:
        payload = json.loads(FEEDBACK_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {"blocked_senders": [], "blocked_keywords": []}

    blocked_senders = payload.get("blocked_senders", [])
    blocked_keywords = payload.get("blocked_keywords", [])
    return {
        "blocked_senders": sorted({str(sender).strip().lower() for sender in blocked_senders if str(sender).strip()}),
        "blocked_keywords": sorted({str(term).strip().lower() for term in blocked_keywords if str(term).strip()}),
    }


def save_feedback_rules(blocked_senders: list[str], blocked_keywords: list[str]) -> None:
    payload = {
        "blocked_senders": sorted({sender.strip().lower() for sender in blocked_senders if sender.strip()}),
        "blocked_keywords": sorted({term.strip().lower() for term in blocked_keywords if term.strip()}),
    }
    FEEDBACK_FILE.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def sender_is_blocked(sender: str, sender_email: str, blocked_senders: list[str]) -> bool:
    sender_lower = sender.strip().lower()
    sender_email_lower = sender_email.strip().lower()
    return any(blocked in sender_lower or blocked in sender_email_lower for blocked in blocked_senders)


def apply_feedback_filters_to_email_df(
    df: pd.DataFrame,
    blocked_senders: list[str],
    blocked_keywords: list[str],
) -> pd.DataFrame:
    if df.empty or "Subject" not in df.columns:
        return df

    filtered_df = df.copy()
    from_values = filtered_df.get("From", pd.Series(dtype=str)).fillna("").astype(str)
    from_email_values = filtered_df.get("From Email", pd.Series(dtype=str)).fillna("").astype(str)
    snippet_values = filtered_df.get("Snippet", pd.Series(dtype=str)).fillna("").astype(str)

    sender_mask = [
        not sender_is_blocked(sender, sender_email, blocked_senders)
        for sender, sender_email in zip(from_values.tolist(), from_email_values.tolist())
    ]

    if blocked_keywords:
        keyword_mask = []
        for subject, sender, sender_email, snippet in zip(
            filtered_df["Subject"].fillna("").astype(str).tolist(),
            from_values.tolist(),
            from_email_values.tolist(),
            snippet_values.tolist(),
        ):
            searchable = " ".join([subject, sender, sender_email, snippet]).lower()
            keyword_mask.append(not any(blocked in searchable for blocked in blocked_keywords))
    else:
        keyword_mask = [True] * len(filtered_df)

    return filtered_df[pd.Series(sender_mask, index=filtered_df.index) & pd.Series(keyword_mask, index=filtered_df.index)]


def get_secret(name: str) -> str:
    try:
        return st.secrets.get(name, "")
    except Exception:
        return ""


def decode_mime_text(value: str | None) -> str:
    if not value:
        return ""

    decoded_parts = []
    for part, encoding in decode_header(value):
        if isinstance(part, bytes):
            decoded_parts.append(part.decode(encoding or "utf-8", errors="replace"))
        else:
            decoded_parts.append(part)
    return "".join(decoded_parts)


def normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", unescape(value)).strip()


def strip_html(value: str) -> str:
    without_tags = re.sub(r"<[^>]+>", " ", value)
    return normalize_text(without_tags)


def extract_message_text(message) -> str:
    html_fragments = []

    if message.is_multipart():
        for part in message.walk():
            content_type = part.get_content_type()
            disposition = str(part.get("Content-Disposition", "")).lower()
            if "attachment" in disposition:
                continue

            payload = part.get_payload(decode=True)
            if not payload:
                continue

            charset = part.get_content_charset() or "utf-8"
            decoded = payload.decode(charset, errors="replace")

            if content_type == "text/plain":
                return normalize_text(decoded)
            if content_type == "text/html":
                html_fragments.append(strip_html(decoded))
    else:
        payload = message.get_payload(decode=True)
        if payload:
            charset = message.get_content_charset() or "utf-8"
            decoded = payload.decode(charset, errors="replace")
            if message.get_content_type() == "text/html":
                return strip_html(decoded)
            return normalize_text(decoded)

    return normalize_text(" ".join(html_fragments))


def fetch_gmail_emails(
    gmail_address: str,
    app_password: str,
    mailbox: str,
    days_to_scan: int,
    max_results: int,
    keywords: list[str],
    blocked_senders: list[str],
    blocked_keywords: list[str],
) -> list[dict]:
    ssl_context = ssl.create_default_context(cafile=certifi.where())
    since_date = (datetime.now(timezone.utc) - timedelta(days=days_to_scan)).strftime("%d-%b-%Y")
    matched_emails = []

    try:
        with imaplib.IMAP4_SSL("imap.gmail.com", ssl_context=ssl_context) as client:
            client.login(gmail_address, app_password)

            status, _ = client.select(f'"{mailbox}"', readonly=True)
            if status != "OK":
                raise RuntimeError(f"Unable to open mailbox: {mailbox}")

            status, data = client.search(None, f'(SINCE "{since_date}")')
            if status != "OK":
                raise RuntimeError("Unable to search Gmail messages.")

            for message_id in reversed(data[0].split()):
                status, payload = client.fetch(message_id, "(RFC822)")
                if status != "OK" or not payload or not payload[0]:
                    continue

                raw_message = payload[0][1]
                message = message_from_bytes(raw_message)

                subject = decode_mime_text(message.get("Subject")) or "(No subject)"
                sender_name, sender_email = parseaddr(decode_mime_text(message.get("From")))
                sender = sender_name or sender_email or "Unknown sender"
                body_text = extract_message_text(message)
                searchable = " ".join([subject, sender, sender_email, body_text]).lower()

                if sender_is_blocked(sender, sender_email, blocked_senders):
                    continue
                if any(blocked in searchable for blocked in blocked_keywords):
                    continue

                matched_terms = [keyword for keyword in keywords if keyword in searchable]

                if keywords and not matched_terms:
                    continue

                date_header = message.get("Date", "")
                try:
                    received_at = parsedate_to_datetime(date_header)
                    if received_at.tzinfo is None:
                        received_at = received_at.replace(tzinfo=timezone.utc)
                    received_at = received_at.astimezone(timezone.utc)
                except (TypeError, ValueError, IndexError, OverflowError):
                    received_at = None

                matched_emails.append(
                    {
                        "Received": received_at.strftime("%Y-%m-%d %H:%M UTC") if received_at else date_header,
                        "Received Timestamp": received_at,
                        "From": sender,
                        "From Email": sender_email,
                        "Subject": subject,
                        "Match Terms": ", ".join(matched_terms) if matched_terms else "All messages",
                        "Snippet": body_text[:240],
                    }
                )

                if len(matched_emails) >= max_results:
                    break
    except imaplib.IMAP4.error as exc:
        raise RuntimeError(
            "Unable to load Gmail messages. Use your full Gmail address and an App Password, not your normal account password."
        ) from exc
    except ssl.SSLError as exc:
        raise RuntimeError(f"Unable to establish a secure Gmail connection: {exc}") from exc

    return matched_emails


st.set_page_config(page_title="Job Hunter AI", layout="wide")
st.title("Job Search Intelligence")
st.markdown("Scan and review relevant Gmail messages for your job search.")

with st.sidebar:
    st.header("Controls")
    days_to_scan = st.slider("Scan the last X days", 1, 30, 7)
    max_results = st.slider("Max results", 10, 100, 25, step=5)

    gmail_address = ""
    gmail_app_password = ""
    mailbox = "INBOX"
    keywords = DEFAULT_EMAIL_KEYWORDS
    feedback_rules = load_feedback_rules()
    blocked_senders = feedback_rules["blocked_senders"]
    blocked_keywords = feedback_rules["blocked_keywords"]

    gmail_address = st.text_input("Gmail address", value=get_secret("gmail_address"), placeholder="name@gmail.com")
    gmail_app_password = st.text_input(
        "Gmail app password",
        value=get_secret("gmail_app_password"),
        type="password",
        placeholder="16-character app password",
    )
    mailbox = st.selectbox("Mailbox", ["INBOX", "[Gmail]/All Mail"], index=0)
    keyword_text = st.text_area(
        "Relevant keywords (comma-separated)",
        value=", ".join(DEFAULT_EMAIL_KEYWORDS),
        help="Messages are included when the subject, sender, or body contains one of these terms.",
    )
    keywords = [keyword.strip().lower() for keyword in keyword_text.split(",") if keyword.strip()]
    st.caption("Use a Gmail App Password. Regular account passwords will not work here.")
    if blocked_senders or blocked_keywords:
        st.caption(f"Active exclusions: {len(blocked_senders)} senders, {len(blocked_keywords)} keywords")

    st.divider()
    st.subheader("Improve matching")
    st.caption("Flag senders or phrases as not relevant. Future Gmail scans will exclude similar emails.")

    sender_option_map = {"": ""}
    if "data" in st.session_state:
        existing_df = pd.DataFrame(st.session_state.data)
        if "From" in existing_df.columns or "From Email" in existing_df.columns:
            from_values = existing_df.get("From", pd.Series(dtype=str)).fillna("").astype(str)
            email_values = existing_df.get("From Email", pd.Series(dtype=str)).fillna("").astype(str)

            for sender_name, sender_email in zip(from_values.tolist(), email_values.tolist()):
                clean_name = sender_name.strip()
                clean_email = sender_email.strip()
                if not clean_name and not clean_email:
                    continue

                label = f"{clean_name} <{clean_email}>" if clean_email and clean_name else (clean_email or clean_name)
                value = (clean_email or clean_name).lower()
                sender_option_map[label] = value

    sender_options = sorted([option for option in sender_option_map.keys() if option])

    sender_to_block = st.selectbox(
        "Flag sender as not relevant",
        options=[""] + sender_options,
        help="Run at least one Gmail scan to populate sender suggestions, or use the manual field below.",
    )
    sender_to_block_manual = st.text_input("Or type sender/email to block", placeholder="newsletter@example.com")
    keyword_to_block = st.text_input("Flag phrase/keyword as not relevant", placeholder="e.g. newsletter")

    col_a, col_b = st.columns(2)
    with col_a:
        if st.button("Save sender flag", use_container_width=True):
            selected_sender_value = sender_option_map.get(sender_to_block, sender_to_block).strip().lower()
            chosen_sender = (sender_to_block_manual or selected_sender_value).strip().lower()
            if not chosen_sender:
                st.warning("Choose or type a sender first.")
            else:
                latest = load_feedback_rules()
                latest_senders = set(latest["blocked_senders"])
                latest_senders.add(chosen_sender)
                save_feedback_rules(list(latest_senders), latest["blocked_keywords"])
                st.success(f"Sender flagged: {chosen_sender}")
                st.rerun()
    with col_b:
        if st.button("Save keyword flag", use_container_width=True):
            cleaned_term = keyword_to_block.strip().lower()
            if not cleaned_term:
                st.warning("Enter a keyword first.")
            else:
                latest = load_feedback_rules()
                latest_terms = set(latest["blocked_keywords"])
                latest_terms.add(cleaned_term)
                save_feedback_rules(latest["blocked_senders"], list(latest_terms))
                st.success(f"Keyword flagged: {cleaned_term}")
                st.rerun()

    latest_rules = load_feedback_rules()
    active_blocked_senders = latest_rules["blocked_senders"]
    active_blocked_keywords = latest_rules["blocked_keywords"]

    if active_blocked_senders:
        to_remove_senders = st.multiselect(
            "Remove sender flags",
            options=active_blocked_senders,
            default=[],
        )
        if st.button("Remove selected sender flags", use_container_width=True):
            updated_senders = [s for s in active_blocked_senders if s not in set(to_remove_senders)]
            save_feedback_rules(updated_senders, active_blocked_keywords)
            st.success("Sender flags updated.")
            st.rerun()

    if active_blocked_keywords:
        to_remove_keywords = st.multiselect(
            "Remove keyword flags",
            options=active_blocked_keywords,
            default=[],
        )
        if st.button("Remove selected keyword flags", use_container_width=True):
            updated_keywords = [k for k in active_blocked_keywords if k not in set(to_remove_keywords)]
            save_feedback_rules(active_blocked_senders, updated_keywords)
            st.success("Keyword flags updated.")
            st.rerun()

    if st.button("Load data", use_container_width=True):
        if not gmail_address or not gmail_app_password:
            st.error("Enter your Gmail address and App Password to load email data.")
        else:
            with st.spinner("Scanning Gmail..."):
                try:
                    st.session_state.data = fetch_gmail_emails(
                        gmail_address,
                        gmail_app_password,
                        mailbox,
                        days_to_scan,
                        max_results,
                        keywords,
                        blocked_senders,
                        blocked_keywords,
                    )
                    st.session_state.data_source = "Gmail inbox"
                except RuntimeError as exc:
                    st.error(str(exc))

if "data" in st.session_state:
    df = pd.DataFrame(st.session_state.data)
    df = apply_feedback_filters_to_email_df(df, blocked_senders, blocked_keywords)

    if df.empty:
        st.warning("No Gmail messages matched the current keywords. Try fewer keywords, a wider date range, or the All Mail mailbox.")
    else:
        col1, col2, col3 = st.columns(3)

        recent_emails = (df["Received Timestamp"] >= datetime.now(timezone.utc) - timedelta(days=1)).sum()
        col1.metric("Matched emails", len(df))
        col2.metric("Unique senders", df["From Email"].replace("", pd.NA).dropna().nunique())
        col3.metric("Received in 24h", recent_emails)

        st.divider()
        st.subheader("Results (Gmail inbox)")

        senders = sorted(df["From"].dropna().unique())
        selected_senders = st.multiselect("Filter by sender", options=senders, default=senders)
        filtered_df = df[df["From"].isin(selected_senders)].copy()

        column_config = {}

        if "Received Timestamp" in filtered_df.columns:
            filtered_df = filtered_df.sort_values("Received Timestamp", ascending=False)
            filtered_df = filtered_df.drop(columns=["Received Timestamp"])

        editable_df = filtered_df.copy()
        editable_df.insert(0, "Flag", False)
        edited_df = st.data_editor(
            editable_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                **column_config,
                "Flag": st.column_config.CheckboxColumn("Flag", help="Check rows to block that sender."),
            },
            disabled=[column for column in editable_df.columns if column != "Flag"],
            key="gmail_results_editor",
        )

        if st.button("Flag checked senders", use_container_width=True):
            selected_rows = edited_df[edited_df["Flag"]]
            senders_to_add = {
                (row.get("From Email") or row.get("From") or "").strip().lower()
                for _, row in selected_rows.iterrows()
                if (row.get("From Email") or row.get("From") or "").strip()
            }

            if not senders_to_add:
                st.warning("Check at least one sender row first.")
            else:
                latest = load_feedback_rules()
                updated_senders = set(latest["blocked_senders"])
                updated_senders.update(senders_to_add)
                save_feedback_rules(list(updated_senders), latest["blocked_keywords"])
                st.success(f"Flagged {len(senders_to_add)} sender(s).")
                st.rerun()
else:
    st.write("Enter your Gmail details in the sidebar, then click Load data.")