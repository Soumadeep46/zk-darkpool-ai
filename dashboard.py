from pathlib import Path
import json

import pandas as pd
import plotly.express as px
import streamlit as st


st.set_page_config(
    page_title="AI-ZK Dark Pool",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="expanded",
)


ROOT_DIR = Path(__file__).resolve().parent

BENCHMARK_PATH = (
    ROOT_DIR
    / "results"
    / "metrics"
    / "end_to_end_benchmark.json"
)


def load_results():

    if not BENCHMARK_PATH.exists():

        return None

    with open(
        BENCHMARK_PATH,
        "r",
        encoding="utf-8",
    ) as file:

        return json.load(file)


def get_ai_results(results):

    return results.get(
        "ai_zk_pipeline",
        {},
    )


def sort_selection_labels(ai_results):

    return sorted(
        ai_results.keys(),
        key=lambda label: float(
            ai_results[label].get(
                "selection_fraction",
                0,
            )
        ),
    )


def get_number(
    data,
    *keys,
    default=0,
):

    for key in keys:

        if key in data:

            return data[key]

    return default


def ms_to_seconds(value):

    return value / 1000


def build_dataframe(
    ai_results,
):

    rows = []

    labels = sort_selection_labels(
        ai_results
    )

    for label in labels:

        result = ai_results[
            label
        ]

        rows.append(
            {
                "Selection Fraction": (
                    result.get(
                        "selection_fraction",
                        0,
                    )
                    * 100
                ),

                "Selection Label": label,

                "AI Selected": get_number(
                    result,
                    "mean_candidates_processed",
                    "mean_candidates_selected_by_ai",
                ),

                "AI Eliminated": get_number(
                    result,
                    "mean_candidates_eliminated",
                    "mean_candidates_eliminated_by_ai",
                ),

                "Candidates Sent to ZK": get_number(
                    result,
                    "mean_candidates_sent_to_zk",
                ),

                "Candidates Filtered": get_number(
                    result,
                    "mean_candidates_filtered_before_zk",
                ),

                "Candidate Reduction": get_number(
                    result,
                    "candidate_reduction_percent",
                ),

                "ZK Work Reduction": get_number(
                    result,
                    "zk_work_reduction_percent",
                ),

                "Valid Matches": get_number(
                    result,
                    "mean_valid_matches",
                ),

                "Recall": (
                    get_number(
                        result,
                        "recall",
                    )
                    * 100
                ),

                "Precision": (
                    get_number(
                        result,
                        "precision",
                    )
                    * 100
                ),

                "Pipeline Latency ms": get_number(
                    result.get(
                        "pipeline_latency",
                        {},
                    ),
                    "mean_ms",
                ),

                "AI Ranking Latency ms": get_number(
                    result.get(
                        "ai_ranking_latency",
                        {},
                    ),
                    "mean_ms",
                ),

                "ZK Matching Latency ms": get_number(
                    result.get(
                        "zk_matching_latency",
                        {},
                    ),
                    "mean_ms",
                ),

                "Latency Reduction": get_number(
                    result,
                    "latency_reduction_percent",
                ),

                "Settlements": get_number(
                    result,
                    "mean_settlements",
                ),
            }
        )

    dataframe = pd.DataFrame(
        rows
    )

    return dataframe


def metric_card(
    column,
    label,
    value,
):

    with column:

        st.metric(
            label=label,
            value=value,
        )


st.markdown(
    """
    <style>

    .stApp {
        background-color: #0f1726;
        color: #e5e7eb;
    }

    [data-testid="stSidebar"] {
        background-color: #121c2c;
        border-right: 1px solid #26344a;
    }

    [data-testid="stSidebar"] * {
        color: #d1d5db;
    }

    .main-title {
        font-size: 2.2rem;
        font-weight: 700;
        color: #f3f4f6;
        margin-bottom: 0.3rem;
        letter-spacing: 0.01em;
    }

    .subtitle {
        font-size: 1rem;
        color: #94a3b8;
        margin-bottom: 2rem;
    }

    .section-title {
        font-size: 1.25rem;
        font-weight: 600;
        color: #e5e7eb;
        margin-top: 1.6rem;
        margin-bottom: 0.9rem;
    }

    div[data-testid="stMetric"] {
        background-color: #162235;
        border: 1px solid #2b3b55;
        border-radius: 14px;
        padding: 18px;
        min-height: 125px;
    }

    div[data-testid="stMetricLabel"] {
        color: #9caec4;
        font-size: 0.95rem;
    }

    div[data-testid="stMetricValue"] {
        color: #f8fafc;
        font-size: 2rem;
    }

    div[data-testid="stDataFrame"] {
        border: 1px solid #2b3b55;
        border-radius: 12px;
        overflow: hidden;
    }

    .status-card {
        background-color: #162235;
        border: 1px solid #2b3b55;
        border-radius: 14px;
        padding: 20px;
        min-height: 140px;
    }

    .status-title {
        color: #9caec4;
        font-size: 0.9rem;
        margin-bottom: 12px;
    }

    .status-value {
        color: #f8fafc;
        font-size: 1.05rem;
        font-weight: 600;
        margin-top: 8px;
    }

    .status-success {
        color: #65d6a7;
        font-size: 1rem;
        font-weight: 600;
        margin-top: 8px;
    }

    hr {
        border-color: #26344a;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


results = load_results()


if results is None:

    st.error(
        "Benchmark results were not found."
    )

    st.write(
        f"Expected file: {BENCHMARK_PATH}"
    )

    st.stop()


ai_results = get_ai_results(
    results
)


if not ai_results:

    st.error(
        "No AI-ZK benchmark results were found."
    )

    st.stop()


dataframe = build_dataframe(
    ai_results
)


selection_labels = (
    dataframe[
        "Selection Label"
    ].tolist()
)


st.sidebar.markdown(
    "## AI-ZK Dark Pool"
)

st.sidebar.divider()

selected_label = st.sidebar.selectbox(
    "AI Selection Fraction",
    selection_labels,
)


selected_result = ai_results[
    selected_label
]


st.sidebar.divider()

st.sidebar.markdown(
    "### Benchmark Configuration"
)


cpu_threads = results.get(
    "cpu_threads",
    "N/A",
)


parallel_zk_workers = results.get(
    "parallel_zk_workers",
    "N/A",
)


repetitions = results.get(
    "repetitions",
    "N/A",
)


st.sidebar.metric(
    "CPU Threads",
    cpu_threads,
)


st.sidebar.metric(
    "Parallel ZK Workers",
    parallel_zk_workers,
)


st.sidebar.metric(
    "Benchmark Repetitions",
    repetitions,
)


st.markdown(
    """
    <div class="main-title">
        AI-ZK Dark Pool Execution Dashboard
    </div>
    """,
    unsafe_allow_html=True,
)


st.markdown(
    """
    <div class="subtitle">
        Private order matching with AI candidate selection and zero-knowledge verification
    </div>
    """,
    unsafe_allow_html=True,
)


st.markdown(
    '<div class="section-title">Pipeline Status</div>',
    unsafe_allow_html=True,
)


status_col1, status_col2, status_col3, status_col4 = (
    st.columns(4)
)


with status_col1:

    st.markdown(
        """
        <div class="status-card">
            <div class="status-title">
                Private Orders
            </div>
            <div class="status-value">
                BUY: Hidden
            </div>
            <div class="status-value">
                SELL: Hidden
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


with status_col2:

    st.markdown(
        """
        <div class="status-card">
            <div class="status-title">
                Order Privacy
            </div>
            <div class="status-success">
                Commitments Generated
            </div>
            <div class="status-success">
                Order Proof Valid
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


with status_col3:

    ai_selected = get_number(
        selected_result,
        "mean_candidates_processed",
        "mean_candidates_selected_by_ai",
    )


    ai_eliminated = get_number(
        selected_result,
        "mean_candidates_eliminated",
        "mean_candidates_eliminated_by_ai",
    )


    st.markdown(
        f"""
        <div class="status-card">
            <div class="status-title">
                AI Candidate Selection
            </div>
            <div class="status-value">
                Selected: {ai_selected:.0f}
            </div>
            <div class="status-value">
                Eliminated: {ai_eliminated:.0f}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


with status_col4:

    st.markdown(
        """
        <div class="status-card">
            <div class="status-title">
                Verification and Settlement
            </div>
            <div class="status-success">
                ZK Match Verified
            </div>
            <div class="status-success">
                Settlement Complete
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


st.markdown(
    '<div class="section-title">Selected Pipeline Performance</div>',
    unsafe_allow_html=True,
)


performance_col1, performance_col2, performance_col3, performance_col4, performance_col5 = (
    st.columns(5)
)


metric_card(
    performance_col1,
    "Candidates Sent to ZK",
    f"{get_number(selected_result, 'mean_candidates_sent_to_zk'):.0f}",
)


metric_card(
    performance_col2,
    "Valid Matches",
    f"{get_number(selected_result, 'mean_valid_matches'):.0f}",
)


metric_card(
    performance_col3,
    "Recall",
    f"{get_number(selected_result, 'recall') * 100:.2f}%",
)


metric_card(
    performance_col4,
    "Precision",
    f"{get_number(selected_result, 'precision') * 100:.2f}%",
)


metric_card(
    performance_col5,
    "ZK Work Reduction",
    f"{get_number(selected_result, 'zk_work_reduction_percent'):.2f}%",
)


latency_col1, latency_col2, latency_col3, latency_col4 = (
    st.columns(4)
)


pipeline_latency = get_number(
    selected_result.get(
        "pipeline_latency",
        {},
    ),
    "mean_ms",
)


ai_ranking_latency = get_number(
    selected_result.get(
        "ai_ranking_latency",
        {},
    ),
    "mean_ms",
)


zk_matching_latency = get_number(
    selected_result.get(
        "zk_matching_latency",
        {},
    ),
    "mean_ms",
)


latency_reduction = get_number(
    selected_result,
    "latency_reduction_percent",
)


metric_card(
    latency_col1,
    "Pipeline Latency",
    f"{ms_to_seconds(pipeline_latency):.2f} s",
)


metric_card(
    latency_col2,
    "AI Ranking Latency",
    f"{ai_ranking_latency:.2f} ms",
)


metric_card(
    latency_col3,
    "ZK Matching Latency",
    f"{ms_to_seconds(zk_matching_latency):.2f} s",
)


metric_card(
    latency_col4,
    "Latency Reduction",
    f"{latency_reduction:.2f}%",
)


st.divider()


st.markdown(
    '<div class="section-title">Baseline Performance</div>',
    unsafe_allow_html=True,
)


baseline = results.get(
    "baseline",
    {},
)


baseline_latency = (
    baseline.get(
        "pipeline_latency",
        {},
    )
)


baseline_final_run = (
    baseline.get(
        "final_run",
        {},
    )
)


baseline_col1, baseline_col2, baseline_col3, baseline_col4, baseline_col5 = (
    st.columns(5)
)


metric_card(
    baseline_col1,
    "Mean Latency",
    f"{ms_to_seconds(get_number(baseline_latency, 'mean_ms')):.2f} s",
)


metric_card(
    baseline_col2,
    "Candidates",
    f"{get_number(baseline_final_run, 'candidates')}",
)


metric_card(
    baseline_col3,
    "Candidates Sent to ZK",
    f"{get_number(baseline_final_run, 'candidates_sent_to_zk')}",
)


metric_card(
    baseline_col4,
    "Valid Matches",
    f"{get_number(baseline_final_run, 'valid_matches')}",
)


metric_card(
    baseline_col5,
    "Settlements",
    f"{get_number(baseline_final_run, 'settlements')}",
)


st.divider()


st.markdown(
    '<div class="section-title">Benchmark Analysis</div>',
    unsafe_allow_html=True,
)


chart_col1, chart_col2 = st.columns(2)


recall_chart = px.line(
    dataframe,
    x="Selection Fraction",
    y="Recall",
    markers=True,
    template="plotly_dark",
)


recall_chart.update_layout(
    title="Selection Fraction vs Valid Match Recall",
    xaxis_title="AI Selection Fraction (%)",
    yaxis_title="Valid Match Recall (%)",
    paper_bgcolor="#121722",
    plot_bgcolor="#121722",
    font=dict(
        color="#dbe5f1",
    ),
    margin=dict(
        l=30,
        r=30,
        t=60,
        b=30,
    ),
)


recall_chart.update_traces(
    line=dict(
        width=3,
    ),
    marker=dict(
        size=9,
    ),
)


with chart_col1:

    st.plotly_chart(
        recall_chart,
        use_container_width=True,
    )


latency_chart = px.bar(
    dataframe,
    x="Selection Fraction",
    y="Pipeline Latency ms",
    template="plotly_dark",
)


latency_chart.update_layout(
    title="AI Selection Fraction vs Pipeline Latency",
    xaxis_title="AI Selection Fraction (%)",
    yaxis_title="Pipeline Latency (ms)",
    paper_bgcolor="#121722",
    plot_bgcolor="#121722",
    font=dict(
        color="#dbe5f1",
    ),
    margin=dict(
        l=30,
        r=30,
        t=60,
        b=30,
    ),
)


with chart_col2:

    st.plotly_chart(
        latency_chart,
        use_container_width=True,
    )


reduction_chart = px.line(
    dataframe,
    x="Candidate Reduction",
    y="ZK Work Reduction",
    markers=True,
    template="plotly_dark",
)


reduction_chart.update_layout(
    title="AI Candidate Reduction vs ZK Verification Work",
    xaxis_title="AI Candidate Reduction (%)",
    yaxis_title="ZK Verification Work Reduction (%)",
    paper_bgcolor="#121722",
    plot_bgcolor="#121722",
    font=dict(
        color="#dbe5f1",
    ),
    margin=dict(
        l=30,
        r=30,
        t=60,
        b=30,
    ),
)


reduction_chart.update_traces(
    line=dict(
        width=3,
    ),
    marker=dict(
        size=9,
    ),
)


st.plotly_chart(
    reduction_chart,
    use_container_width=True,
)


st.divider()


st.markdown(
    '<div class="section-title">Detailed Benchmark Results</div>',
    unsafe_allow_html=True,
)


table_dataframe = dataframe[
    [
        "Selection Label",
        "AI Selected",
        "AI Eliminated",
        "Candidates Sent to ZK",
        "Candidates Filtered",
        "Candidate Reduction",
        "ZK Work Reduction",
        "Valid Matches",
        "Recall",
        "Precision",
        "Pipeline Latency ms",
        "Latency Reduction",
        "Settlements",
    ]
].copy()


table_dataframe[
    "Candidate Reduction"
] = table_dataframe[
    "Candidate Reduction"
].map(
    lambda value: f"{value:.2f}%"
)


table_dataframe[
    "ZK Work Reduction"
] = table_dataframe[
    "ZK Work Reduction"
].map(
    lambda value: f"{value:.2f}%"
)


table_dataframe[
    "Recall"
] = table_dataframe[
    "Recall"
].map(
    lambda value: f"{value:.2f}%"
)


table_dataframe[
    "Precision"
] = table_dataframe[
    "Precision"
].map(
    lambda value: f"{value:.2f}%"
)


table_dataframe[
    "Pipeline Latency ms"
] = table_dataframe[
    "Pipeline Latency ms"
].map(
    lambda value: f"{value / 1000:.2f} s"
)


table_dataframe[
    "Latency Reduction"
] = table_dataframe[
    "Latency Reduction"
].map(
    lambda value: f"{value:.2f}%"
)


st.dataframe(
    table_dataframe,
    use_container_width=True,
    hide_index=True,
)


st.divider()


st.markdown(
    """
    <div style="
        text-align: center;
        color: #64748b;
        font-size: 0.85rem;
        padding: 1rem;
    ">
        AI-ZK Dark Pool Benchmark System
    </div>
    """,
    unsafe_allow_html=True,
)