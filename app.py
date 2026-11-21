import json
import os
from datetime import date, timedelta
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv
from pydantic import ValidationError

from src.chatbot import answer
from src.database import delete_lead, hosted, list_leads, save_followup, save_lead
from src.models import Lead
from src.rag import properties, retrieve
from src.workflow import analyze_lead


load_dotenv()
st.set_page_config(page_title="LeadPilot AI", page_icon="🏡", layout="wide")
st.html(Path(__file__).parent / "assets" / "style.css")


def page_header(title, description):
    st.html(f'<div class="hero"><div class="eyebrow">LEADPILOT AI / SALES WORKSPACE</div><h1>{title}</h1><p>{description}</p></div>')


def show_analysis(record):
    lead, analysis = record["lead"], record["analysis"]
    st.subheader(lead["name"])
    st.caption(f'{lead["location"]} · ₹{lead["budget_lakh"]:g} lakh · {lead["timeline"]}')
    left, right = st.columns([2, 1])
    with left:
        st.markdown("**Lead summary**")
        st.write(analysis["summary"])
        st.markdown("**Customer intent**")
        st.write(analysis["intent"].capitalize())
    with right:
        st.metric(f'{analysis["priority"]} priority', f'{analysis["score"]}/100')
        with st.expander("Why this score?"):
            for reason, points in analysis["reasons"].items():
                st.write(f"{reason}: +{points}")
            for field in ("intent", "timeline", "financing"):
                if analysis.get(f"{field}_evidence"):
                    st.caption(f'{field.title()}: "{analysis[f"{field}_evidence"]}"')
    left, right = st.columns(2)
    for column, title, key in [(left, "Key requirements", "requirements"), (right, "Objections / concerns", "objections")]:
        with column:
            st.markdown(f"**{title}**")
            for item in analysis[key] or ["Not stated"]:
                st.write(f"• {item}")
    if analysis["missing_information"]:
        st.warning("To clarify: " + "; ".join(analysis["missing_information"]))
    st.info("Next action: " + analysis["next_action"])
    st.markdown("**Suggested customer response**")
    st.write(analysis["suggested_response"])
    with st.expander("Original enquiry"):
        st.write(lead["requirement"])
        st.write(lead["message"])


def followup_form(record):
    task = record.get("followup") or {}
    with st.form(f'followup_{record["id"]}'):
        action = st.text_input("Next action", value=task.get("action", record["analysis"]["next_action"]), max_chars=500)
        due = st.date_input("Follow-up date", value=date.fromisoformat(task["due_date"]) if task else date.today() + timedelta(days=1))
        status = st.selectbox("Status", ["Pending", "Completed"], index=1 if task.get("status") == "Completed" else 0)
        if st.form_submit_button("Save follow-up", type="primary"):
            try:
                save_followup(record["id"], {"action": action.strip(), "due_date": due.isoformat(), "status": status})
                st.rerun()
            except (RuntimeError, ValidationError) as exc:
                st.error(str(exc) if isinstance(exc, RuntimeError) else "Enter an action of at least 3 characters.")


def show_properties(rows, note):
    st.caption(note)
    for row in rows:
        with st.container(border=True):
            st.markdown(f'**{row["name"]} [{row["id"]}]**')
            st.caption(f'{row["area"]}, {row["city"]} · {row["bedrooms"]} BHK · ₹{row["price_lakh"]:g} lakh')
            st.write(row["description"])


def show_chat_message(message):
    st.write(message["content"])
    if message.get("properties"):
        show_properties(message["properties"], message.get("note", ""))


def lead_chat(record):
    histories = st.session_state.setdefault("chats", {})
    history = histories.setdefault(record["id"], [])
    st.caption("Ask what to emphasize on a call, or ask for a revised customer reply.")
    use_properties = st.checkbox("Search sample properties for this question", key=f'property_chat_{record["id"]}')
    conversation = st.container()
    for message in history:
        with conversation.chat_message(message["role"]):
            show_chat_message(message)
    question = st.chat_input("Ask about this lead", key=f'chat_{record["id"]}', max_chars=2000)
    if question:
        try:
            with conversation:
                with st.spinner("Preparing an answer..."):
                    reply, matches, note = answer(record, question, history, use_properties)
            response = {"role": "assistant", "content": reply, "properties": matches if use_properties else [], "note": note}
            history.extend([{"role": "user", "content": question}, response])
            with conversation.chat_message("user"):
                st.write(question)
            with conversation.chat_message("assistant"):
                show_chat_message(response)
        except RuntimeError as exc:
            conversation.error(str(exc))


def intake():
    page_header("Turn an enquiry into an opportunity", "Capture a new lead. Let AI help you understand their needs and plan your next move.")
    scenarios = json.loads((Path(__file__).parent / "data" / "hybrid_leads.json").read_text(encoding="utf-8"))
    scenario = st.selectbox("Hybrid lead scenario", scenarios, format_func=lambda row: f'{row["name"]} · {row["location"]}')
    if st.button("Fill hybrid enquiry"):
        st.session_state.update(scenario)
    with st.form("intake"):
        left, right = st.columns(2)
        with left:
            name = st.text_input("Name", key="name", max_chars=100)
            location = st.text_input("Location", key="location", max_chars=100)
            requirement = st.text_input("Property requirement", key="requirement", placeholder="2 BHK apartment near metro", max_chars=500)
        with right:
            budget = st.number_input("Budget (INR lakh)", min_value=0.0, max_value=100000.0, step=5.0, key="budget_lakh")
            timeline = st.text_input("Buying timeline", key="timeline", placeholder="Within 3 months / undecided", max_chars=200)
        message = st.text_area("Customer message", key="message", height=140, max_chars=5000)
        submitted = st.form_submit_button("Analyze and save lead", type="primary")
    if submitted:
        try:
            lead = Lead(name=name, location=location, requirement=requirement, budget_lakh=budget, timeline=timeline, message=message)
            with st.spinner("Analyzing the enquiry..."):
                analysis = analyze_lead(lead)
                record = save_lead(lead, analysis)
            st.session_state["selected_lead"] = record["id"]
            st.success("Lead saved. Open Dashboard to chat and plan a follow-up.")
            show_analysis(record)
        except ValidationError as exc:
            for error in exc.errors():
                st.error(f'{error["loc"][0].replace("_", " ").title()}: {error["msg"]}')
        except RuntimeError as exc:
            st.error(str(exc))


def dashboard(records):
    page_header("Your lead pipeline", "Know who to call, what matters to them, and what to do next.")
    with st.container(key="pipeline_metrics"):
        counts = st.columns(4)
    counts[0].metric("Saved leads", len(records))
    counts[1].metric("Hot leads", sum(r["analysis"]["priority"] == "Hot" for r in records))
    counts[2].metric("Warm leads", sum(r["analysis"]["priority"] == "Warm" for r in records))
    counts[3].metric("Due follow-ups", sum(bool(r.get("followup") and r["followup"]["status"] == "Pending" and r["followup"]["due_date"] <= date.today().isoformat()) for r in records))
    left, middle, right = st.columns([2, 1, 1])
    search = left.text_input("Search leads", placeholder="Name, location or requirement").casefold().strip()
    priority = middle.selectbox("Priority", ["All", "Hot", "Warm", "Cold"])
    order = right.selectbox("Sort by", ["Highest priority", "Newest first"])
    records = [r for r in records if search in " ".join(str(v) for v in r["lead"].values()).casefold() and (priority == "All" or r["analysis"]["priority"] == priority)]
    records.sort(key=lambda r: r["analysis"]["score"] if order == "Highest priority" else r["created_at"], reverse=True)
    if not records:
        st.info("No leads to show. Add a lead or adjust your filters.")
        return
    st.dataframe([{"Name": r["lead"]["name"], "Location": r["lead"]["location"], "Budget (lakh)": r["lead"]["budget_lakh"], "Timeline": r["lead"]["timeline"], "Priority": r["analysis"]["priority"], "Score": r["analysis"]["score"]} for r in records], hide_index=True, width="stretch", column_config={"Score": st.column_config.ProgressColumn("Score", min_value=0, max_value=100, format="%d")})
    ids = [r["id"] for r in records]
    if st.session_state.get("selected_lead") not in ids:
        st.session_state["selected_lead"] = ids[0]
    labels = {r["id"]: f'{r["lead"]["name"]} · {r["lead"]["location"]} · {r["id"][:6]}' for r in records}
    selected = st.selectbox("Open a lead", ids, format_func=labels.get, key="selected_lead")
    record = next(r for r in records if r["id"] == selected)
    overview, chat, planner, matches = st.tabs(["Overview", "Lead assistant", "Follow-up", "Property matches"])
    with overview:
        show_analysis(record)
        with st.expander("Manage lead"):
            confirmed = st.checkbox("Delete this lead permanently", key=f"confirm_{selected}")
            if st.button("Delete lead", disabled=not confirmed, key=f"delete_{selected}"):
                delete_lead(selected)
                st.session_state.get("chats", {}).pop(selected, None)
                st.rerun()
    with chat:
        lead_chat(record)
    with planner:
        followup_form(record)
    with matches:
        st.caption("Fictional catalogue. Exact location and bedroom filters; price cannot exceed the saved budget.")
        if st.button("Find matching properties", key=f"match_{selected}"):
            with st.spinner("Searching the sample catalogue..."):
                rows, note = retrieve(record["lead"], record["lead"]["requirement"] + " " + record["lead"]["message"])
            show_properties(rows, note)


def planner(records):
    page_header("Keep the conversation moving", "Plan your follow-ups and track the next step for every lead. No messages are sent automatically.")
    tasks = [r for r in records if r.get("followup")]
    tasks.sort(key=lambda r: (r["followup"]["status"] == "Completed", r["followup"]["due_date"]))
    if not tasks:
        st.info("Open a lead on the dashboard and save its first follow-up.")
    for record in tasks:
        task = record["followup"]
        overdue = task["status"] == "Pending" and task["due_date"] < date.today().isoformat()
        with st.expander(f'{record["lead"]["name"]} · {task["due_date"]} · {"Overdue" if overdue else task["status"]}', expanded=overdue):
            followup_form(record)


def main():
    with st.sidebar:
        st.title("LeadPilot AI")
        st.caption("Know the lead. Take the next step.")
        page = st.radio("Workspace", ["Dashboard", "New lead", "Follow-ups", "Sample catalogue"])
        st.divider()
        st.caption("Gemini configured" if os.getenv("GEMINI_API_KEY", "").strip() else "Add your Gemini key in .env to enable AI.")
        st.caption("Storage: Supabase" if hosted() else "Storage: local SQLite")
        st.caption("Interview demo: use fictional customer data. This shared app has no user accounts.")
    if page == "New lead":
        intake()
    elif page == "Sample catalogue":
        page_header("Find their next home", "Explore the sample property catalogue and compare requirements.")
        show_properties(properties(), "All listings and prices are fictional. Prices are in INR lakh; 1 lakh = ₹100,000.")
    else:
        records = list_leads()
        if page == "Dashboard":
            dashboard(records)
        else:
            planner(records)


try:
    main()
except RuntimeError as exc:
    st.error(str(exc))
