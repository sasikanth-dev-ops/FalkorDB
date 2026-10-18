"""AI Career Mentor — Streamlit Web Application Dashboard."""

from __future__ import annotations

import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from urllib.parse import urlparse

import streamlit as st

st.set_page_config(
    page_title="AI Career Mentor | Persistent Graph Career Co-Pilot",
    page_icon="🧭",
    layout="wide",
    initial_sidebar_state="expanded",
)

from frontend.api_client import CareerMentorAPIClient
from frontend.components.graph_view import render_knowledge_graph
from frontend.components.styles import CUSTOM_CSS

# Inject custom CSS
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# Initialize API client
api = CareerMentorAPIClient()

# Session State Initialization
if "student_id" not in st.session_state:
    st.session_state.student_id = "seed-student-001"
WELCOME_MESSAGE = (
    "Hello! I am your AI Career Mentor. I track your skills, projects, and goals "
    "in a persistent knowledge graph to recommend high-impact hackathons, bounties, "
    "and personalized learning roadmaps. What are you currently working on or learning?"
)


def reset_chat_for_student(student_id: str) -> None:
    st.session_state.student_id = student_id
    st.session_state.chat_history = [
        {
            "role": "assistant",
            "content": WELCOME_MESSAGE,
            "memory_updates": None,
            "opportunities": [],
            "roadmap": [],
        }
    ]


if "chat_history" not in st.session_state:
    st.session_state.chat_history = [
        {
            "role": "assistant",
            "content": WELCOME_MESSAGE,
            "memory_updates": None,
            "opportunities": [],
            "roadmap": [],
        }
    ]
if any(
    item.get("role") == "assistant"
    and "Student not found" in item.get("content", "")
    for item in st.session_state.chat_history
):
    reset_chat_for_student(st.session_state.student_id)
if "last_query" not in st.session_state:
    st.session_state.last_query = ""


# ---------------- SIDEBAR ----------------
with st.sidebar:
    st.markdown(
        """
        <div style="display: flex; align-items: center; gap: 0.75rem; margin-bottom: 1rem;">
            <div style="font-size: 2rem;">🧭</div>
            <div>
                <div style="font-size: 1.15rem; font-weight: 800; color: #f8fafc; letter-spacing: -0.01em;">AI Career Mentor</div>
                <div style="font-size: 0.75rem; color: #818cf8; font-weight: 600;">AGENTIC KNOWLEDGE GRAPH</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Health check
    health = api.check_health()
    if health.get("status") == "connected":
        st.markdown(
            '<div style="background: rgba(16, 185, 129, 0.15); border: 1px solid rgba(16, 185, 129, 0.4); color: #34d399; padding: 0.45rem 0.75rem; border-radius: 8px; font-size: 0.8rem; font-weight: 600; margin-bottom: 1.25rem;">● FalkorDB & FastAPI Connected</div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            '<div style="background: rgba(239, 68, 68, 0.15); border: 1px solid rgba(239, 68, 68, 0.4); color: #f87171; padding: 0.45rem 0.75rem; border-radius: 8px; font-size: 0.8rem; font-weight: 600; margin-bottom: 1.25rem;">○ Backend Offline (Start FastAPI)</div>',
            unsafe_allow_html=True,
        )

    st.markdown("### 👤 Active Student Profile")
    student_options = [f"seed-student-{index:03}" for index in range(1, 6)]
    student_options.append("Custom ID...")
    selected_option = st.selectbox(
        "Choose profile",
        options=student_options,
        index=(
            student_options.index(st.session_state.student_id)
            if st.session_state.student_id in student_options
            else len(student_options) - 1
        ),
        label_visibility="collapsed",
    )

    if selected_option == "Custom ID...":
        custom_id = st.text_input("Enter Student ID", value=st.session_state.student_id)
        if custom_id and custom_id != st.session_state.student_id:
            reset_chat_for_student(custom_id)
            st.rerun()
    else:
        if st.session_state.student_id != selected_option:
            reset_chat_for_student(selected_option)
            st.rerun()

    profile = api.get_student_profile(st.session_state.student_id)
    graph_state = api.get_graph_state(st.session_state.student_id)

    if profile:
        st.markdown(
            f"""
            <div class="glass-card" style="padding: 1rem; margin-top: 0.5rem; margin-bottom: 1rem;">
                <div style="font-weight: 700; color: #f1f5f9; font-size: 0.95rem;">{profile.get('name', 'Student')}</div>
                <div style="font-size: 0.8rem; color: #94a3b8;">{profile.get('branch', 'Engineering')} • Year {profile.get('year', '3')}</div>
                <div style="font-size: 0.8rem; color: #818cf8; margin-top: 0.25rem;">🎯 Target: {profile.get('target_role', 'AI Engineer')}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.warning(
            f"No profile exists for `{st.session_state.student_id}`. "
            "Create one below before starting a chat."
        )
        if health.get("status") == "connected":
            with st.form("create_student_profile"):
                profile_name = st.text_input("Your name")
                target_role = st.text_input("Target role", value="Software Developer")
                create_profile = st.form_submit_button("Create student profile")
            if create_profile:
                if not profile_name.strip():
                    st.error("Enter your name to create a profile.")
                else:
                    saved_profile = api.save_student_profile(
                        {
                            "student_id": st.session_state.student_id,
                            "name": profile_name.strip(),
                            "target_role": target_role.strip() or None,
                            "skills": [],
                            "goals": [],
                        }
                    )
                    if saved_profile:
                        st.success("Student profile created.")
                        st.rerun()
                    else:
                        st.error(
                            "Could not create the profile. Check the API and graph "
                            "database, then try again."
                        )

    # Graph quick stats
    if graph_state:
        nodes = graph_state.get("nodes", [])
        edges = graph_state.get("edges", [])
        skills_count = len(profile.get("skills", [])) if profile else 0
        goals_count = len(profile.get("goals", [])) if profile else 0

        st.markdown("### 📊 Graph Memory Metrics")
        col_m1, col_m2 = st.columns(2)
        with col_m1:
            st.markdown(
                f'<div class="metric-box"><div class="metric-num">{len(nodes)}</div><div class="metric-lbl">Graph Nodes</div></div>',
                unsafe_allow_html=True,
            )
        with col_m2:
            st.markdown(
                f'<div class="metric-box"><div class="metric-num">{len(edges)}</div><div class="metric-lbl">Graph Edges</div></div>',
                unsafe_allow_html=True,
            )

        col_m3, col_m4 = st.columns(2)
        with col_m3:
            st.markdown(
                f'<div class="metric-box" style="margin-top: 0.5rem;"><div class="metric-num">{skills_count}</div><div class="metric-lbl">Known Skills</div></div>',
                unsafe_allow_html=True,
            )
        with col_m4:
            st.markdown(
                f'<div class="metric-box" style="margin-top: 0.5rem;"><div class="metric-num">{goals_count}</div><div class="metric-lbl">Active Goals</div></div>',
                unsafe_allow_html=True,
            )

    st.markdown("---")
    st.markdown("### 🚀 Quick Demo Prompts")
    if st.button("💬 'I'm learning FastAPI & want an AI hackathon'"):
        st.session_state.quick_prompt = "I'm building projects with Python and FastAPI. I want to join an AI hackathon, but I'm still new to vector databases."
    if st.button("🎯 'Show me opportunities for backend dev'"):
        st.session_state.quick_prompt = "Can you recommend top opportunities for my backend skills and show me what prerequisites I am missing?"
    if st.button("🗺️ 'Generate my personalized learning roadmap'"):
        st.session_state.quick_prompt = "Please build a step-by-step roadmap to prepare me for the AI hackathon."


# ---------------- MAIN HEADER ----------------
st.markdown(
    """
    <div style="margin-bottom: 1.5rem;">
        <div class="hero-badge">⚡ Persistent Graph Agent • FalkorDB + LangGraph</div>
        <div class="gradient-title">AI Career Mentor <span class="gradient-title-accent">Intelligence Platform</span></div>
        <div style="color: #94a3b8; font-size: 1.05rem; max-width: 900px; line-height: 1.5;">
            Dynamic career intelligence that turns your evolving skills, projects, and goals into a persistent memory graph—delivering explainable opportunity matching and custom learning roadmaps.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)


# ---------------- TABS ----------------
tab_chat, tab_graph, tab_memory, tab_opps, tab_roadmap, tab_ingestion = st.tabs(
    [
        "💬 AI Mentor Chat",
        "🕸️ Interactive Graph",
        "🧠 Persistent Memory",
        "🎯 Opportunity Explorer",
        "🗺️ Actionable Roadmap",
        "⚡ Ingestion & Scrapers",
    ]
)


# ---------------- TAB 1: AI MENTOR CHAT ----------------
with tab_chat:
    st.markdown("#### Conversation with Persistent Career Memory")

    # Display chat history
    for item in st.session_state.chat_history:
        role = item["role"]
        content = item["content"]
        memory_updates = item.get("memory_updates")
        opps = item.get("opportunities", [])
        roadmap = item.get("roadmap", [])

        with st.chat_message(role):
            st.markdown(content)
            if item.get("model_degraded"):
                st.warning(
                    "Gemini is unavailable; this answer uses local guidance."
                )

            # Memory update alert banner
            if memory_updates and any(memory_updates.values()):
                skills = memory_updates.get("skills", [])
                goals = memory_updates.get("goals", [])
                projects = memory_updates.get("projects", [])

                summary_parts = []
                if skills:
                    summary_parts.append(f"<b>Skills:</b> {', '.join(skills)}")
                if goals:
                    summary_parts.append(f"<b>Goals:</b> {', '.join(goals)}")
                if projects:
                    summary_parts.append(f"<b>Projects:</b> {', '.join(projects)}")

                st.markdown(
                    f"""
                    <div class="memory-pill-alert">
                        ⚡ <b>Persistent Graph Updated:</b> Extracted and saved to FalkorDB &nbsp;•&nbsp; {" | ".join(summary_parts)}
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            # Recommendations preview inside chat
            if opps:
                verified_opps = [
                    opp
                    for opp in opps
                    if urlparse(opp.get("url") or "").hostname != "example.org"
                ]
                if verified_opps:
                    st.markdown("##### 🎯 Recommended Opportunities for this turn:")
                cols = st.columns(min(len(verified_opps), 3)) if verified_opps else []
                for i, opp in enumerate(verified_opps[:3]):
                    with cols[i]:
                        match_percentage = opp.get("match_percentage")
                        match_badge = (
                            f"{round(match_percentage)}% Match"
                            if match_percentage is not None
                            else "Match unavailable"
                        )
                        with st.container():
                            st.caption(
                                f"{opp.get('platform', 'Platform')} · {match_badge}"
                            )
                            st.write(opp.get("title", "Opportunity"))
                            st.write(
                                opp.get("description")
                                or "No description published by source."
                            )
                            st.caption(
                                f"Deadline: {opp.get('deadline') or 'Not listed by source'}"
                            )
                            if not opp.get("required_skills"):
                                st.info(
                                    "The source has not published skill requirements; "
                                    "match percentage is unavailable."
                                )
                            url = opp.get("url")
                            if url and urlparse(url).scheme in {"http", "https"}:
                                st.markdown(f"[View official listing]({url})")
            elif item.get("intent") in {"opportunities", "roadmap"}:
                st.info(
                    "No verified opportunities matched this request yet. "
                    "Refresh official listings in the Ingestion & Scrapers tab."
                )

            # Roadmap preview inside chat
            if roadmap:
                st.markdown("##### 🗺️ Learning Roadmap Action Steps:")
                for step in roadmap[:3]:
                    st.markdown(
                        f"""
                        <div style="background: rgba(99, 102, 241, 0.08); border-left: 3px solid #6366f1; padding: 0.6rem 0.9rem; margin-bottom: 0.4rem; border-radius: 0 8px 8px 0; font-size: 0.88rem;">
                            <b>Step {step.get('step')}: {step.get('action')}</b> ({step.get('skill')})
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

    # Chat Input
    user_input = st.chat_input("Ask for advice, tell the mentor what you are building, or seek opportunities...")

    # Check for quick prompt button trigger
    if "quick_prompt" in st.session_state and st.session_state.quick_prompt:
        user_input = st.session_state.quick_prompt
        st.session_state.quick_prompt = None

    if user_input and not profile:
        st.warning("Create or select an existing student profile before chatting.")
    elif user_input:
        st.session_state.chat_history.append({"role": "user", "content": user_input})

        with st.spinner("AI Mentor is reasoning over your career graph..."):
            res = api.send_chat_message(st.session_state.student_id, user_input)

            if res.get("success"):
                data = res["data"]
                st.session_state.chat_history.append(
                    {
                        "role": "assistant",
                        "content": data.get("message", "I have updated your career memory."),
                        "memory_updates": data.get("memory_updates"),
                        "opportunities": data.get("opportunities", []),
                        "roadmap": data.get("roadmap", []),
                        "intent": data.get("intent"),
                        "model_degraded": data.get("model_degraded", False),
                    }
                )
            else:
                st.session_state.chat_history.append(
                    {
                        "role": "assistant",
                        "content": f"⚠️ Error: {res.get('error', 'Could not process request.')}",
                        "memory_updates": None,
                        "opportunities": [],
                        "roadmap": [],
                        "intent": None,
                    }
                )
        st.rerun()


# ---------------- TAB 2: INTERACTIVE KNOWLEDGE GRAPH ----------------
with tab_graph:
    st.markdown(
        """
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
            <div>
                <h4 style="margin: 0;">Interactive Career Knowledge Graph</h4>
                <div style="color: #94a3b8; font-size: 0.85rem;">Powered by FalkorDB graph relationships & Pyvis force-directed physics.</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Visual Legend
    st.markdown(
        """
        <div style="display: flex; gap: 0.75rem; flex-wrap: wrap; margin-bottom: 1rem; font-size: 0.8rem;">
            <span style="display: inline-flex; align-items: center; gap: 0.35rem;"><span style="width: 12px; height: 12px; background: #6366f1; border-radius: 50%;"></span> Student</span>
            <span style="display: inline-flex; align-items: center; gap: 0.35rem;"><span style="width: 12px; height: 12px; background: #10b981; border-radius: 50%;"></span> Skill</span>
            <span style="display: inline-flex; align-items: center; gap: 0.35rem;"><span style="width: 12px; height: 12px; background: #f59e0b; border-radius: 50%;"></span> Goal</span>
            <span style="display: inline-flex; align-items: center; gap: 0.35rem;"><span style="width: 12px; height: 12px; background: #06b6d4; border-radius: 50%;"></span> Project</span>
            <span style="display: inline-flex; align-items: center; gap: 0.35rem;"><span style="width: 12px; height: 12px; background: #ec4899; border-radius: 50%;"></span> Event / Opportunity</span>
            <span style="display: inline-flex; align-items: center; gap: 0.35rem;"><span style="width: 12px; height: 12px; background: #8b5cf6; border-radius: 50%;"></span> Course Resource</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col_btn, _ = st.columns([1, 4])
    with col_btn:
        if st.button("🔄 Refresh Graph View", use_container_width=True):
            graph_state = api.get_graph_state(st.session_state.student_id)

    if graph_state:
        render_knowledge_graph(graph_state, height="600px")
    else:
        st.info("No graph state found for this student. Connect backend and run bootstrap setup.")


# ---------------- TAB 3: PERSISTENT MEMORY INSPECTOR ----------------
with tab_memory:
    st.markdown("#### Structured Student Memory Graph Inspector")
    st.markdown(
        "Direct visibility into the student profile facts extracted from conversations and persisted in FalkorDB."
    )

    if profile:
        col_p1, col_p2 = st.columns([1, 1])

        with col_p1:
            st.markdown("##### 🛠️ Verified Skills & Proficiencies")
            skills = profile.get("skills", [])
            if skills:
                for skill in skills:
                    proficiency = skill.get("proficiency") or "beginner"
                    color_cls = "pill-matched" if proficiency in ("intermediate", "advanced") else "pill-missing"
                    st.markdown(
                        f"""
                        <div style="display: flex; justify-content: space-between; align-items: center; background: rgba(30, 41, 59, 0.5); border: 1px solid rgba(99, 102, 241, 0.15); border-radius: 8px; padding: 0.6rem 0.9rem; margin-bottom: 0.4rem;">
                            <span style="font-weight: 600; color: #f1f5f9;">{skill.get('name')}</span>
                            <span class="pill {color_cls}" style="margin: 0;">{proficiency.upper()}</span>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
            else:
                st.caption("No skills currently recorded in memory.")

            st.markdown("##### 🎯 Career Goals")
            goals = profile.get("goals", [])
            if goals:
                for goal in goals:
                    target_date = goal.get("target_date") or "Ongoing"
                    st.markdown(
                        f"""
                        <div style="background: rgba(245, 158, 11, 0.08); border-left: 3px solid #f59e0b; border-radius: 0 8px 8px 0; padding: 0.65rem 0.9rem; margin-bottom: 0.4rem;">
                            <div style="font-weight: 600; color: #fde68a;">{goal.get('description')}</div>
                            <div style="font-size: 0.78rem; color: #94a3b8; margin-top: 0.2rem;">Target: {target_date}</div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
            else:
                st.caption("No goals recorded in memory.")

        with col_p2:
            st.markdown("##### 💻 Portfolio Projects")
            projects = profile.get("projects", [])
            if projects:
                for proj in projects:
                    stack = proj.get("tech_stack") or []
                    stack_html = " ".join([f"<span class='pill pill-category'>{t}</span>" for t in stack])
                    st.markdown(
                        f"""
                        <div class="glass-card" style="padding: 1rem; margin-bottom: 0.75rem;">
                            <div style="font-weight: 700; color: #38bdf8; font-size: 0.95rem;">{proj.get('title')}</div>
                            <div style="margin: 0.4rem 0;">{stack_html}</div>
                            <a href="{proj.get('repo_url') or '#'}" target="_blank" style="color: #818cf8; font-size: 0.8rem; text-decoration: none;">GitHub Repository ↗</a>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
            else:
                st.caption("No projects recorded in memory.")

        st.markdown("---")
        st.markdown("##### ✏️ Update Profile Details")
        with st.form("update_profile_form"):
            col_f1, col_f2, col_f3 = st.columns(3)
            with col_f1:
                new_name = st.text_input("Name", value=profile.get("name", ""))
            with col_f2:
                new_branch = st.text_input("Branch", value=profile.get("branch", ""))
            with col_f3:
                new_role = st.text_input("Target Role", value=profile.get("target_role", ""))

            submitted = st.form_submit_button("Save Profile Updates")
            if submitted:
                payload = {
                    "student_id": st.session_state.student_id,
                    "name": new_name,
                    "branch": new_branch,
                    "year": profile.get("year", 3),
                    "target_role": new_role,
                    "skills": profile.get("skills", []),
                    "goals": profile.get("goals", []),
                    "projects": profile.get("projects", []),
                }
                res = api.save_student_profile(payload)
                if res:
                    st.success("Profile updated successfully in FalkorDB!")
                    st.rerun()
                else:
                    st.error("Failed to update profile.")
    else:
        st.info("Profile not found. Make sure FalkorDB is running and seeded.")


# ---------------- TAB 4: OPPORTUNITY EXPLORER ----------------
with tab_opps:
    st.markdown("#### Graph-Ranked Opportunity Explorer")
    st.markdown(
        "FalkorDB matches required skills through graph relationships; token overlap helps rank text-search results. Skill percentages count exact graph matches only."
    )
    st.caption(
        "Prerequisite paths below are graph evidence for what to learn next; they do not count those skills as already owned."
    )
    include_demo = st.checkbox(
        "Include synthetic example listings",
        value=False,
        help="These records are test fixtures with example.org links, not real opportunities.",
    )

    col_s1, col_s2, col_s3 = st.columns([2, 1, 1])
    with col_s1:
        search_query = st.text_input(
            "Semantic Query (e.g. 'GenAI Hackathon', 'Backend FastAPI', 'Web3')",
            value=st.session_state.last_query,
            placeholder="Type your interests or query...",
        )
    with col_s2:
        filter_type = st.selectbox(
            "Event Type",
            ["All", "Hackathon", "Bounty", "Internship", "Event"],
            index=1,
        )
    with col_s3:
        filter_cat = st.selectbox("Category", ["All", "AI", "Backend", "Web3", "Frontend", "Cloud"])

    opportunities = api.get_opportunities(
        student_id=st.session_state.student_id,
        query=search_query,
        event_type=filter_type,
        category=filter_cat,
        limit=20,
        include_demo=include_demo,
    )

    if any(
        urlparse(opp.get("url") or "").hostname == "example.org"
        for opp in opportunities
    ):
        st.warning(
            "Synthetic development fixtures are shown with example.org URLs. "
            "They are not live opportunities; verify real listings before presenting or applying."
        )

    st.markdown(f"**Found {len(opportunities)} opportunities matching your criteria:**")

    for opp in opportunities:
        match_pct = round(opp.get("match_percentage") or 0.0)
        sim_score = opp.get("similarity_score")
        hybrid_score = opp.get("hybrid_score")

        matched_skills = opp.get("matched_skills") or []
        missing_skills = opp.get("missing_skills") or []
        prerequisite_paths = opp.get("prerequisite_paths") or []
        is_demo_fixture = (
            urlparse(opp.get("url") or "").hostname == "example.org"
        )

        matched_html = " ".join([f"<span class='pill pill-matched'>✓ {s}</span>" for s in matched_skills])
        missing_html = " ".join([f"<span class='pill pill-missing'>+ Need: {s}</span>" for s in missing_skills])

        score_details = (
            f"<span class='pill pill-matched' style='font-size: 0.85rem;'>{match_pct}% Match</span>"
            if opp.get("match_percentage") is not None
            else "<span class='pill pill-category'>Match unavailable — source lists no required skills</span>"
        )
        if hybrid_score is not None:
            score_details += f" <span class='pill pill-category'>Hybrid: {hybrid_score}</span>"
        if is_demo_fixture:
            score_details += " <span class='pill pill-category'>SYNTHETIC DEMO DATA</span>"

        st.markdown(
            f"""
            <div class="glass-card">
                <div style="display: flex; justify-content: space-between; align-items: start; flex-wrap: wrap; gap: 0.5rem; margin-bottom: 0.5rem;">
                    <div>
                        <div style="font-size: 1.15rem; font-weight: 700; color: #f8fafc;">{opp.get('title')}</div>
                        <div style="display: flex; gap: 0.4rem; align-items: center; margin-top: 0.3rem;">
                            <span class="pill pill-platform">{opp.get('platform', 'Platform')}</span>
                            <span class="pill pill-category">{opp.get('type', 'Event')}</span>
                            <span style="font-size: 0.8rem; color: #94a3b8;">📅 Deadline: {opp.get('deadline') or 'Not listed by source'}</span>
                        </div>
                    </div>
                    <div>{score_details}</div>
                </div>
                <div style="color: #cbd5e1; font-size: 0.88rem; line-height: 1.5; margin: 0.6rem 0;">
                    {opp.get('description') or 'No description provided.'}
                </div>
                <div style="margin-top: 0.75rem;">
                    {matched_html} {missing_html}
                </div>
                <div style="margin-top: 0.75rem; display: flex; justify-content: flex-end;">
                    {"<span class='pill pill-category'>Example only — no real opportunity link</span>" if is_demo_fixture else f"<a href='{opp.get('url')}' target='_blank' rel='noopener noreferrer' style='background: linear-gradient(135deg, #6366f1 0%, #a855f7 100%); color: white; padding: 0.45rem 1rem; border-radius: 8px; font-size: 0.85rem; font-weight: 600; text-decoration: none;'>View official listing →</a>"}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if prerequisite_paths:
            with st.expander(
                f"Inspect FalkorDB reasoning ({len(prerequisite_paths)} prerequisite path"
                f"{'s' if len(prerequisite_paths) != 1 else ''})"
            ):
                for evidence in prerequisite_paths:
                    st.caption(
                        f"Learn next: {' → '.join(evidence['path'])} "
                        "(prerequisite path; not counted as an owned skill)"
                    )


# ---------------- TAB 5: ACTIONABLE LEARNING ROADMAP ----------------
with tab_roadmap:
    st.markdown("#### Personalized Skill-Gap Learning Roadmap")
    st.markdown(
        "Converts missing prerequisite skills for your target opportunities into a step-by-step learning sequence backed by verified course resources in the graph."
    )

    roadmap_steps = api.get_roadmap(st.session_state.student_id)

    if roadmap_steps:
        st.markdown(f"**Action plan to close skill gaps for `{st.session_state.student_id}`:**")

        for step in roadmap_steps:
            step_num = step.get("step", 1)
            skill = step.get("skill", "")
            action = step.get("action", "")
            resource = step.get("resource")

            resource_html = ""
            if resource:
                resource_html = f"""
                <div style="background: rgba(139, 92, 246, 0.1); border: 1px solid rgba(139, 92, 246, 0.3); border-radius: 8px; padding: 0.75rem; margin-top: 0.6rem;">
                    <div style="font-size: 0.78rem; text-transform: uppercase; color: #c4b5fd; font-weight: 700; letter-spacing: 0.05em;">Recommended Course</div>
                    <div style="font-weight: 700; color: #f8fafc; font-size: 0.95rem; margin-top: 0.2rem;">{resource.get('title')}</div>
                    <div style="font-size: 0.8rem; color: #94a3b8; margin: 0.25rem 0;">Provider: {resource.get('provider')} • Duration: ~{resource.get('duration_hours', 10)} hours</div>
                    <a href="{resource.get('url')}" target="_blank" style="color: #a78bfa; font-size: 0.82rem; font-weight: 600; text-decoration: none;">Open Course Material ↗</a>
                </div>
                """

            st.markdown(
                f"""
                <div class="glass-card" style="border-left: 4px solid #6366f1;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.4rem;">
                        <span class="pill pill-category" style="font-size: 0.85rem;">Milestone {step_num}</span>
                        <span class="pill pill-missing">Target Skill: {skill}</span>
                    </div>
                    <div style="font-size: 1.05rem; font-weight: 700; color: #f1f5f9;">{action}</div>
                    {resource_html}
                </div>
                """,
                unsafe_allow_html=True,
            )
    else:
        st.info("No roadmap steps needed! Either you match all requirements, or no matching target opportunity is currently selected.")


# ---------------- TAB 6: INGESTION & SCRAPERS ----------------
with tab_ingestion:
    st.markdown("#### Live Opportunity Ingestion Pipeline")
    st.markdown(
        "Fetch and normalize live hackathons and bounties directly into the FalkorDB knowledge graph with required skill relationships."
    )

    col_sc1, col_sc2 = st.columns(2)
    with col_sc1:
        st.markdown(
            """
            <div class="glass-card">
                <h5>Configured Platforms</h5>
                <ul>
                    <li><b>WeMakeDevs:</b> Live hackathons & event cards</li>
                    <li><b>GitHub:</b> Live issue bounties API</li>
                    <li><b>Unstop:</b> Competition & hackathon structured parser</li>
                </ul>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col_sc2:
        st.markdown(
            """
            <div class="glass-card">
                <h5>Trigger Scraping</h5>
                <p style="font-size: 0.85rem; color: #94a3b8;">
                    Scrapes configured HTTPS sources, normalizes records with required skills, and merges them into FalkorDB idempotently.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    sources_to_scrape = st.multiselect(
        "Select platforms to scrape:",
        ["wemakedevs", "github_bounties", "unstop"],
        default=["wemakedevs"],
    )

    if st.button("🚀 Run Scraper Ingestion Job", type="primary"):
        with st.spinner("Scraping and normalizing opportunities..."):
            result = api.scrape_sources(sources_to_scrape)
            if result.get("success"):
                data = result["data"]
                st.success(f"Successfully ingested {data.get('ingested', 0)} opportunities into the graph!")
                st.json(data)
            else:
                st.error(f"Scraper error: {result.get('error')}")
