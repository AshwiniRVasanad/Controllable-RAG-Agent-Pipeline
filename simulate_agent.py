import os
import tempfile

import streamlit as st
import streamlit.components.v1 as components
from pyvis.network import Network

from functions_for_pipeline import *


def apply_custom_css():
    """Apply modern styling to the dashboard."""
    st.markdown(
        """
        <style>
        .main-header {
            background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
            padding: 1.5rem 2rem;
            border-radius: 12px;
            border: 1px solid #334155;
            margin-bottom: 1.5rem;
        }

        .main-header h1 {
            color: #f8fafc;
            font-size: 1.85rem;
            margin-bottom: 0.25rem;
        }

        .main-header p {
            color: #94a3b8;
            font-size: 0.95rem;
            margin: 0;
        }

        .final-answer-box {
            background: linear-gradient(135deg, #064e3b 0%, #022c22 100%);
            border: 1px solid #10b981;
            border-radius: 12px;
            padding: 1.25rem 1.5rem;
            color: #ecfdf5;
            margin-top: 1rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def create_network_graph(current_state):
    """Create the agent execution graph."""

    net = Network(
        directed=True,
        notebook=False,
        height="340px",
        width="100%",
        bgcolor="#0f172a",
        font_color="#f8fafc",
    )

    net.toggle_physics(False)

    nodes = [
        {"id": "anonymize_question", "label": "Anonymize\nQuestion", "x": 0, "y": 0},
        {"id": "planner", "label": "Planner", "x": 260, "y": -90},
        {"id": "de_anonymize_plan", "label": "De-Anonymize\nPlan", "x": 520, "y": -90},
        {"id": "break_down_plan", "label": "Break Down\nPlan", "x": 780, "y": -90},
        {"id": "task_handler", "label": "Task\nHandler", "x": 1040, "y": 0},
        {"id": "retrieve_chunks", "label": "Retrieve\nChunks", "x": 1320, "y": 160},
        {"id": "retrieve_summaries", "label": "Retrieve\nSummaries", "x": 1320, "y": 55},
        {"id": "retrieve_book_quotes", "label": "Retrieve\nQuotes", "x": 1320, "y": -55},
        {"id": "answer", "label": "Answer\nSubtask", "x": 1320, "y": -160},
        {"id": "replan", "label": "Replan", "x": 1600, "y": 0},
        {"id": "can_be_answered_already", "label": "Verify &\nCheck Ready", "x": 1860, "y": 0},
        {"id": "get_final_answer", "label": "Final\nAnswer", "x": 2120, "y": 0},
    ]

    edges = [
        ("anonymize_question", "planner"),
        ("planner", "de_anonymize_plan"),
        ("de_anonymize_plan", "break_down_plan"),
        ("break_down_plan", "task_handler"),
        ("task_handler", "retrieve_chunks"),
        ("task_handler", "retrieve_summaries"),
        ("task_handler", "retrieve_book_quotes"),
        ("task_handler", "answer"),
        ("retrieve_chunks", "replan"),
        ("retrieve_summaries", "replan"),
        ("retrieve_book_quotes", "replan"),
        ("answer", "replan"),
        ("replan", "can_be_answered_already"),
        ("replan", "break_down_plan"),
        ("can_be_answered_already", "get_final_answer"),
    ]

    for node in nodes:
        is_active = node["id"] == current_state

        color = {
            "background": "#10b981" if is_active else "#1e293b",
            "border": "#34d399" if is_active else "#475569",
            "highlight": {
                "background": "#10b981",
                "border": "#ecfdf5",
            },
        }

        net.add_node(
            node["id"],
            label=node["label"],
            x=node["x"],
            y=node["y"],
            color=color,
            shape="box",
            margin=12,
            borderWidth=3 if is_active else 1.5,
            physics=False,
            font={
                "size": 18,
                "color": "#ffffff",
                "face": "Inter, sans-serif",
            },
        )

    for source, target in edges:
        net.add_edge(
            source,
            target,
            color="#64748b",
            width=2,
            arrows="to",
        )

    net.options.edges.smooth.type = "cubicBezier"

    return net


def save_and_display_graph(net):
    """Save the graph temporarily and return HTML content."""

    tmp_path = None

    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            delete=False,
            suffix=".html",
            encoding="utf-8",
        ) as tmp_file:
            tmp_path = tmp_file.name

        net.write_html(tmp_path, notebook=False)

        with open(tmp_path, "r", encoding="utf-8") as file:
            return file.read()

    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)


def format_state_value(val):
    """Format lists and strings for display."""

    if isinstance(val, list):
        if not val:
            return "_None yet_"

        return "\n".join(
            f"{i + 1}. {item}"
            for i, item in enumerate(val)
        )

    return str(val) if val else "_Waiting..._"


def update_placeholders_and_graph(
    agent_state_value,
    placeholders,
    graph_placeholder,
    status_placeholder,
    previous_values,
    previous_state,
):
    """Update graph, status and reasoning panels."""

    current_state = agent_state_value.get("curr_state")

    if current_state:
        status_placeholder.info(
            f"**Active Node:** `{current_state}`"
        )

        net = create_network_graph(current_state)

        with graph_placeholder.container():
            components.html(
                save_and_display_graph(net),
                height=360,
                scrolling=False,
            )

    if current_state != previous_state and previous_state is not None:
        for key, placeholder in placeholders.items():
            if previous_values.get(key) is not None:
                placeholder.markdown(
                    format_state_value(previous_values[key])
                )

    for key in placeholders:
        if key in agent_state_value:
            previous_values[key] = agent_state_value[key]

    return previous_values, current_state


def execute_plan_and_print_steps(
    inputs,
    plan_and_execute_app,
    placeholders,
    graph_placeholder,
    status_placeholder,
    recursion_limit=25,
):
    """Execute the agent and display its progress."""

    config = {"recursion_limit": recursion_limit}

    agent_state_value = None
    progress_bar = st.progress(0)

    step = 0
    previous_state = None

    previous_values = {
        key: None for key in placeholders
    }

    try:
        for plan_output in plan_and_execute_app.stream(
            inputs,
            config=config,
        ):
            step += 1

            for _, agent_state_value in plan_output.items():

                previous_values, previous_state = (
                    update_placeholders_and_graph(
                        agent_state_value,
                        placeholders,
                        graph_placeholder,
                        status_placeholder,
                        previous_values,
                        previous_state,
                    )
                )

            progress_bar.progress(
                min(step / recursion_limit, 1.0)
            )

            if step >= recursion_limit:
                break

        for key, placeholder in placeholders.items():
            if previous_values[key] is not None:
                placeholder.markdown(
                    format_state_value(previous_values[key])
                )

        progress_bar.progress(1.0)

        status_placeholder.success(
            "**Execution Complete!**"
        )

        response = (
            agent_state_value.get("response", "No response found.")
            if agent_state_value
            else "No response found."
        )

    except Exception as e:
        response = f"An error occurred: {str(e)}"

        status_placeholder.error(
            f"Execution halted: {e}"
        )

    return response


@st.cache_resource
def load_compiled_agent():
    """Cache the compiled LangGraph agent."""

    return create_agent()


def main():

    st.set_page_config(
        page_title="Controllable RAG Agent Studio",
        page_icon="🧠",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    apply_custom_css()

    # Header
    st.markdown(
        """
        <div class="main-header">
            <h1>🧠 Controllable RAG Agent — Execution Studio</h1>
            <p>
                Deterministic LangGraph orchestration for multi-hop
                question answering with live state inspection.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Sidebar
    with st.sidebar:

        st.header("⚙️ Agent Settings")

        recursion_limit = st.slider(
            "Max Reasoning Steps (Recursion Limit)",
            min_value=10,
            max_value=50,
            value=25,
            step=5,
            help="Maximum number of graph node transitions allowed per query.",
        )

        st.divider()

        st.subheader("💡 Sample Multi-Hop Questions")

        sample_questions = [
            "What is the class that the professor who helped the villain is teaching?",
            "How did the protagonist defeat the villain's assistant?",
            "Who gave the protagonist the invisibility cloak and what was their connection to his father?",
        ]

        selected_sample = st.selectbox(
            "Choose an example:",
            ["Custom Question..."] + sample_questions,
        )

        st.divider()

        st.markdown(
            """
            **Pipeline Stages:**

            1. **Anonymize** entities to prevent bias
            2. **Plan & Decompose** into sub-tasks
            3. **Retrieve & Distill** chunks, summaries, or quotes
            4. **Verify & Replan** until grounded
            """
        )

    # Question Input
    default_q = (
        selected_sample
        if selected_sample != "Custom Question..."
        else "What is the class that the professor who helped the villain is teaching?"
    )

    col_input, col_btn = st.columns(
        [5, 1],
        vertical_alignment="bottom",
    )

    with col_input:
        question = st.text_input(
            "Ask a complex question about your documents:",
            value=default_q,
        )

    with col_btn:
        run_clicked = st.button(
            "🚀 Run Agent",
            type="primary",
            use_container_width=True,
        )

    # Live Graph
    st.subheader("🕸️ Live Agent Execution Graph")

    status_placeholder = st.empty()

    status_placeholder.info(
        "Ready. Click Run Agent to start execution."
    )

    graph_placeholder = st.empty()

    initial_net = create_network_graph(None)

    with graph_placeholder.container():
        components.html(
            save_and_display_graph(initial_net),
            height=360,
            scrolling=False,
        )

    # Reasoning Trace
    st.subheader("🔍 Reasoning Trace & State Inspector")

    tab_plan, tab_context, tab_answer = st.tabs(
        [
            "📋 Plan & Sub-Tasks",
            "📚 Accumulated Context & Past Steps",
            "✅ Final Answer",
        ]
    )

    with tab_plan:

        c1, c2 = st.columns(2)

        with c1:
            st.markdown("**Anonymized Question**")

            anon_q_placeholder = st.empty()
            anon_q_placeholder.markdown("Waiting for input...")

        with c2:
            st.markdown("**Generated Execution Plan**")

            plan_placeholder = st.empty()
            plan_placeholder.markdown("Waiting for input...")

    with tab_context:

        c3, c4 = st.columns(2)

        with c3:
            st.markdown("**Completed Reasoning Steps**")

            past_steps_placeholder = st.empty()
            past_steps_placeholder.markdown(
                "No steps executed yet."
            )

        with c4:
            st.markdown("**Retrieved & Distilled Context**")

            context_placeholder = st.empty()
            context_placeholder.markdown(
                "No context retrieved yet."
            )

    with tab_answer:

        final_answer_placeholder = st.empty()

        final_answer_placeholder.markdown(
            "The grounded final response will appear here once verification completes."
        )

    placeholders = {
        "anonymized_question": anon_q_placeholder,
        "plan": plan_placeholder,
        "past_steps": past_steps_placeholder,
        "aggregated_context": context_placeholder,
    }

    # Run Agent
    if run_clicked and question.strip():

        plan_and_execute_app = load_compiled_agent()

        inputs = {
            "question": question.strip()
        }

        final_response = execute_plan_and_print_steps(
            inputs=inputs,
            plan_and_execute_app=plan_and_execute_app,
            placeholders=placeholders,
            graph_placeholder=graph_placeholder,
            status_placeholder=status_placeholder,
            recursion_limit=recursion_limit,
        )

        final_answer_placeholder.markdown(
            f"""
            <div class="final-answer-box">
                <h3>🎯 Grounded Final Answer</h3>
                <p>{final_response}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )


if __name__ == "__main__":
    main()