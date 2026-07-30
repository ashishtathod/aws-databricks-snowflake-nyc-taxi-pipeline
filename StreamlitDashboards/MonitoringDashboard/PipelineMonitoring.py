# ----------------------------------------------------------
# PIPELINE MONITORING DASHBOARD
# ----------------------------------------------------------

import altair as alt
import pandas as pd
import streamlit as st
from snowflake.snowpark.context import get_active_session

session = get_active_session()


st.title("🛠️ Pipeline Monitoring Dashboard")

st.caption(
    "Monitor pipeline health, processing volume, execution time, "
    "layer-level performance, and failures."
)

# ----------------------------------------------------------
# LOAD PIPELINE MONITORING DATA
# ----------------------------------------------------------

monitoring_df = session.sql("""
SELECT
    "layer_name",
    "status",
    "run_id",
    "execution_timestamp",
    "duration_seconds",
    "error_message",
    "records_processed"
FROM PIPELINE_MONITORING
ORDER BY "execution_timestamp" DESC
""").to_pandas()

monitoring_df.columns = monitoring_df.columns.str.lower()

# ----------------------------------------------------------
# CLEAN DATA TYPES
# ----------------------------------------------------------

monitoring_df["execution_timestamp"] = pd.to_datetime(
    monitoring_df["execution_timestamp"],
    errors="coerce"
)

monitoring_df["duration_seconds"] = pd.to_numeric(
    monitoring_df["duration_seconds"],
    errors="coerce"
).fillna(0)

monitoring_df["records_processed"] = pd.to_numeric(
    monitoring_df["records_processed"],
    errors="coerce"
).fillna(0)

monitoring_df["layer_name"] = (
    monitoring_df["layer_name"]
    .fillna("Unknown")
    .astype(str)
    .str.strip()
    .str.title()
)

monitoring_df["status"] = (
    monitoring_df["status"]
    .fillna("Unknown")
    .astype(str)
    .str.strip()
    .str.upper()
)

monitoring_df["run_id"] = (
    monitoring_df["run_id"]
    .fillna("Unknown")
    .astype(str)
)

monitoring_df["error_message"] = (
    monitoring_df["error_message"]
    .fillna("")
    .astype(str)
)

monitoring_df = (
    monitoring_df
    .dropna(subset=["execution_timestamp"])
    .sort_values("execution_timestamp", ascending=False)
    .reset_index(drop=True)
)

# ----------------------------------------------------------
# EMPTY TABLE HANDLING
# ----------------------------------------------------------

if monitoring_df.empty:
    st.warning("No pipeline monitoring records are available.")
    st.stop()

# ----------------------------------------------------------
# SIDEBAR FILTERS
# ----------------------------------------------------------

st.sidebar.header("Pipeline Filters")

available_layers = sorted(
    monitoring_df["layer_name"].dropna().unique().tolist()
)

available_statuses = sorted(
    monitoring_df["status"].dropna().unique().tolist()
)

selected_layers = st.sidebar.multiselect(
    "Layer",
    options=available_layers,
    default=available_layers
)

selected_statuses = st.sidebar.multiselect(
    "Status",
    options=available_statuses,
    default=available_statuses
)

minimum_date = monitoring_df["execution_timestamp"].min().date()
maximum_date = monitoring_df["execution_timestamp"].max().date()

selected_date_range = st.sidebar.date_input(
    "Execution Date Range",
    value=(minimum_date, maximum_date),
    min_value=minimum_date,
    max_value=maximum_date
)

# ----------------------------------------------------------
# APPLY FILTERS
# ----------------------------------------------------------

filtered_df = monitoring_df[
    monitoring_df["layer_name"].isin(selected_layers)
    & monitoring_df["status"].isin(selected_statuses)
].copy()

if isinstance(selected_date_range, tuple) and len(selected_date_range) == 2:
    start_date, end_date = selected_date_range

    filtered_df = filtered_df[
        (
            filtered_df["execution_timestamp"].dt.date >= start_date
        )
        & (
            filtered_df["execution_timestamp"].dt.date <= end_date
        )
    ]

if filtered_df.empty:
    st.warning("No monitoring records match the selected filters.")
    st.stop()

# ----------------------------------------------------------
# LATEST PIPELINE RUN
# ----------------------------------------------------------

latest_timestamp = filtered_df["execution_timestamp"].max()

latest_run_rows = filtered_df[
    filtered_df["execution_timestamp"] == latest_timestamp
].copy()

latest_run_id = latest_run_rows["run_id"].iloc[0]

latest_run_df = filtered_df[
    filtered_df["run_id"] == latest_run_id
].copy()

latest_run_statuses = latest_run_df["status"].tolist()

failure_statuses = {
    "FAILED",
    "FAILURE",
    "ERROR"
}

running_statuses = {
    "RUNNING",
    "IN PROGRESS",
    "IN_PROGRESS",
    "STARTED"
}

if any(status in failure_statuses for status in latest_run_statuses):
    latest_pipeline_status = "Failed"
elif any(status in running_statuses for status in latest_run_statuses):
    latest_pipeline_status = "Running"
else:
    latest_pipeline_status = "Successful"

# ----------------------------------------------------------
# KPI CALCULATIONS
# ----------------------------------------------------------

total_executions = len(filtered_df)

successful_executions = filtered_df[
    filtered_df["status"].isin(
        ["SUCCESS", "SUCCEEDED", "COMPLETED"]
    )
].shape[0]

failed_executions = filtered_df[
    filtered_df["status"].isin(
        ["FAILED", "FAILURE", "ERROR"]
    )
].shape[0]

success_rate = (
    successful_executions / total_executions * 100
    if total_executions > 0
    else 0
)

latest_records_processed = latest_run_df[
    "records_processed"
].sum()

latest_duration_seconds = latest_run_df[
    "duration_seconds"
].sum()

latest_execution_time = latest_run_df[
    "execution_timestamp"
].max()

# ----------------------------------------------------------
# PIPELINE HEALTH STATUS
# ----------------------------------------------------------

status_icon_map = {
    "Successful": "🟢",
    "Running": "🟡",
    "Failed": "🔴"
}

latest_status_icon = status_icon_map.get(
    latest_pipeline_status,
    "⚪"
)

if latest_pipeline_status == "Successful":
    st.success(
        f"{latest_status_icon} Latest pipeline run completed successfully "
        f"— Run ID: {latest_run_id}"
    )

elif latest_pipeline_status == "Running":
    st.info(
        f"{latest_status_icon} Latest pipeline run is currently running "
        f"— Run ID: {latest_run_id}"
    )

else:
    st.error(
        f"{latest_status_icon} Latest pipeline run failed "
        f"— Run ID: {latest_run_id}"
    )

st.caption(
    "Latest execution: "
    f"{latest_execution_time.strftime('%d %b %Y, %I:%M:%S %p')}"
)
def format_compact_number(value):
    value = float(value)

    if value >= 1_000_000_000:
        return f"{value / 1_000_000_000:.2f} B"

    if value >= 1_000_000:
        return f"{value / 1_000_000:.2f} M"

    if value >= 1_000:
        return f"{value / 1_000:.2f} K"

    return f"{int(value):,}"


def format_duration(seconds):
    seconds = float(seconds)

    if seconds >= 3600:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)

        return f"{hours}h {minutes}m"

    if seconds >= 60:
        minutes = int(seconds // 60)
        remaining_seconds = int(seconds % 60)

        return f"{minutes}m {remaining_seconds}s"

    return f"{seconds:.1f} s"


# ----------------------------------------------------------
# PRIMARY KPI ROW
# ----------------------------------------------------------

primary_kpi_col1, primary_kpi_col2, primary_kpi_col3 = st.columns(3)

with primary_kpi_col1:
    st.metric(
        label="Latest Run Status",
        value=f"{latest_status_icon} {latest_pipeline_status}"
    )

with primary_kpi_col2:
    st.metric(
        label="Latest Records Processed",
        value=format_compact_number(
            latest_records_processed
        ),
        help=f"Exact count: {int(latest_records_processed):,}"
    )

with primary_kpi_col3:
    st.metric(
        label="Success Rate",
        value=f"{success_rate:.1f}%"
    )

# ----------------------------------------------------------
# SECONDARY KPI ROW
# ----------------------------------------------------------

secondary_kpi_col1, secondary_kpi_col2, secondary_kpi_col3 = (
    st.columns(3)
)

with secondary_kpi_col1:
    st.metric(
        label="Latest Duration",
        value=format_duration(
            latest_duration_seconds
        ),
        help=f"Exact duration: {latest_duration_seconds:,.2f} seconds"
    )

with secondary_kpi_col2:
    st.metric(
        label="Total Layer Executions",
        value=f"{total_executions:,}"
    )

with secondary_kpi_col3:
    st.metric(
        label="Failed Executions",
        value=f"{failed_executions:,}"
    )

# ----------------------------------------------------------
# OPTIONAL SUCCESSFUL EXECUTIONS KPI
# ----------------------------------------------------------

st.metric(
    label="Successful Executions",
    value=f"{successful_executions:,}"
)

# ----------------------------------------------------------
# LATEST RUN LAYER STATUS
# ----------------------------------------------------------

st.subheader("Latest Run by Layer")

latest_layer_display_df = latest_run_df[
    [
        "layer_name",
        "status",
        "records_processed",
        "duration_seconds",
        "execution_timestamp",
        "error_message"
    ]
].copy()

latest_layer_display_df = latest_layer_display_df.sort_values(
    "execution_timestamp"
)

latest_layer_display_df["records_processed"] = latest_layer_display_df[
    "records_processed"
].map(lambda value: f"{int(value):,}")

latest_layer_display_df["duration_seconds"] = latest_layer_display_df[
    "duration_seconds"
].map(lambda value: f"{value:,.2f}")

latest_layer_display_df["execution_timestamp"] = latest_layer_display_df[
    "execution_timestamp"
].dt.strftime("%d %b %Y, %I:%M:%S %p")

latest_layer_display_df = latest_layer_display_df.rename(
    columns={
        "layer_name": "Layer",
        "status": "Status",
        "records_processed": "Records Processed",
        "duration_seconds": "Duration (Seconds)",
        "execution_timestamp": "Execution Timestamp",
        "error_message": "Error Message"
    }
)

st.dataframe(
    latest_layer_display_df,
    use_container_width=True,
    hide_index=True
)

# ----------------------------------------------------------
# RECORDS PROCESSED BY LAYER
# ----------------------------------------------------------

records_by_layer_df = (
    filtered_df
    .groupby("layer_name", as_index=False)["records_processed"]
    .sum()
)

records_by_layer_chart = (
    alt.Chart(records_by_layer_df)
    .mark_bar(
        cornerRadiusTopLeft=5,
        cornerRadiusTopRight=5
    )
    .encode(
        x=alt.X(
            "layer_name:N",
            title="Pipeline Layer",
            sort="-y"
        ),
        y=alt.Y(
            "records_processed:Q",
            title="Records Processed",
            axis=alt.Axis(format=",.2s")
        ),
        tooltip=[
            alt.Tooltip(
                "layer_name:N",
                title="Layer"
            ),
            alt.Tooltip(
                "records_processed:Q",
                title="Records Processed",
                format=","
            )
        ]
    )
    .properties(
        height=350,
        title="Total Records Processed by Layer"
    )
)

# ----------------------------------------------------------
# AVERAGE DURATION BY LAYER
# ----------------------------------------------------------

duration_by_layer_df = (
    filtered_df
    .groupby("layer_name", as_index=False)["duration_seconds"]
    .mean()
)

duration_by_layer_chart = (
    alt.Chart(duration_by_layer_df)
    .mark_bar(
        cornerRadiusTopLeft=5,
        cornerRadiusTopRight=5
    )
    .encode(
        x=alt.X(
            "layer_name:N",
            title="Pipeline Layer",
            sort="-y"
        ),
        y=alt.Y(
            "duration_seconds:Q",
            title="Average Duration (Seconds)"
        ),
        tooltip=[
            alt.Tooltip(
                "layer_name:N",
                title="Layer"
            ),
            alt.Tooltip(
                "duration_seconds:Q",
                title="Average Duration",
                format=".2f"
            )
        ]
    )
    .properties(
        height=350,
        title="Average Processing Duration by Layer"
    )
)

layer_chart_col1, layer_chart_col2 = st.columns(2)

with layer_chart_col1:
    st.altair_chart(
        records_by_layer_chart,
        use_container_width=True
    )

with layer_chart_col2:
    st.altair_chart(
        duration_by_layer_chart,
        use_container_width=True
    )

# ----------------------------------------------------------
# EXECUTION STATUS DISTRIBUTION
# ----------------------------------------------------------

status_summary_df = (
    filtered_df
    .groupby("status", as_index=False)
    .size()
    .rename(columns={"size": "execution_count"})
)

status_chart = (
    alt.Chart(status_summary_df)
    .mark_arc(innerRadius=70)
    .encode(
        theta=alt.Theta(
            "execution_count:Q"
        ),
        color=alt.Color(
            "status:N",
            title="Status"
        ),
        tooltip=[
            alt.Tooltip(
                "status:N",
                title="Status"
            ),
            alt.Tooltip(
                "execution_count:Q",
                title="Executions",
                format=","
            )
        ]
    )
    .properties(
        height=350,
        title="Execution Status Distribution"
    )
)

# ----------------------------------------------------------
# RECORDS PROCESSING TREND
# ----------------------------------------------------------

processing_trend_chart = (
    alt.Chart(filtered_df)
    .mark_line(point=True)
    .encode(
        x=alt.X(
            "execution_timestamp:T",
            title="Execution Timestamp"
        ),
        y=alt.Y(
            "records_processed:Q",
            title="Records Processed",
            axis=alt.Axis(format=",.2s")
        ),
        color=alt.Color(
            "layer_name:N",
            title="Layer"
        ),
        tooltip=[
            alt.Tooltip(
                "execution_timestamp:T",
                title="Execution Time",
                format="%d %b %Y %H:%M:%S"
            ),
            alt.Tooltip(
                "layer_name:N",
                title="Layer"
            ),
            alt.Tooltip(
                "status:N",
                title="Status"
            ),
            alt.Tooltip(
                "records_processed:Q",
                title="Records Processed",
                format=","
            ),
            alt.Tooltip(
                "duration_seconds:Q",
                title="Duration",
                format=".2f"
            )
        ]
    )
    .properties(
        height=350,
        title="Records Processed Over Time"
    )
)

status_chart_col1, status_chart_col2 = st.columns(2)

with status_chart_col1:
    st.altair_chart(
        status_chart,
        use_container_width=True
    )

with status_chart_col2:
    st.altair_chart(
        processing_trend_chart,
        use_container_width=True
    )

# ----------------------------------------------------------
# EXECUTION DURATION TREND
# ----------------------------------------------------------

duration_trend_chart = (
    alt.Chart(filtered_df)
    .mark_line(point=True)
    .encode(
        x=alt.X(
            "execution_timestamp:T",
            title="Execution Timestamp"
        ),
        y=alt.Y(
            "duration_seconds:Q",
            title="Duration (Seconds)"
        ),
        color=alt.Color(
            "layer_name:N",
            title="Layer"
        ),
        tooltip=[
            alt.Tooltip(
                "execution_timestamp:T",
                title="Execution Time",
                format="%d %b %Y %H:%M:%S"
            ),
            alt.Tooltip(
                "run_id:N",
                title="Run ID"
            ),
            alt.Tooltip(
                "layer_name:N",
                title="Layer"
            ),
            alt.Tooltip(
                "duration_seconds:Q",
                title="Duration",
                format=".2f"
            )
        ]
    )
    .properties(
        height=400,
        title="Pipeline Execution Duration Trend"
    )
)

st.altair_chart(
    duration_trend_chart,
    use_container_width=True
)

# ----------------------------------------------------------
# FAILED EXECUTIONS
# ----------------------------------------------------------

st.subheader("Failed Executions")

failed_runs_df = filtered_df[
    filtered_df["status"].isin(
        ["FAILED", "FAILURE", "ERROR"]
    )
].copy()

if failed_runs_df.empty:
    st.success("No failed executions were found for the selected filters.")
else:
    failed_runs_display_df = failed_runs_df[
        [
            "execution_timestamp",
            "run_id",
            "layer_name",
            "status",
            "records_processed",
            "duration_seconds",
            "error_message"
        ]
    ].copy()

    failed_runs_display_df["execution_timestamp"] = (
        failed_runs_display_df["execution_timestamp"]
        .dt.strftime("%d %b %Y, %I:%M:%S %p")
    )

    failed_runs_display_df["records_processed"] = (
        failed_runs_display_df["records_processed"]
        .map(lambda value: f"{int(value):,}")
    )

    failed_runs_display_df["duration_seconds"] = (
        failed_runs_display_df["duration_seconds"]
        .map(lambda value: f"{value:,.2f}")
    )

    failed_runs_display_df = failed_runs_display_df.rename(
        columns={
            "execution_timestamp": "Execution Timestamp",
            "run_id": "Run ID",
            "layer_name": "Layer",
            "status": "Status",
            "records_processed": "Records Processed",
            "duration_seconds": "Duration (Seconds)",
            "error_message": "Error Message"
        }
    )

    st.dataframe(
        failed_runs_display_df,
        use_container_width=True,
        hide_index=True
    )

# ----------------------------------------------------------
# PIPELINE EXECUTION HISTORY
# ----------------------------------------------------------

st.subheader("Pipeline Execution History")

execution_history_df = filtered_df[
    [
        "execution_timestamp",
        "run_id",
        "layer_name",
        "status",
        "records_processed",
        "duration_seconds",
        "error_message"
    ]
].copy()

execution_history_df["execution_timestamp"] = (
    execution_history_df["execution_timestamp"]
    .dt.strftime("%d %b %Y, %I:%M:%S %p")
)

execution_history_df["records_processed"] = (
    execution_history_df["records_processed"]
    .map(lambda value: f"{int(value):,}")
)

execution_history_df["duration_seconds"] = (
    execution_history_df["duration_seconds"]
    .map(lambda value: f"{value:,.2f}")
)

execution_history_df = execution_history_df.rename(
    columns={
        "execution_timestamp": "Execution Timestamp",
        "run_id": "Run ID",
        "layer_name": "Layer",
        "status": "Status",
        "records_processed": "Records Processed",
        "duration_seconds": "Duration (Seconds)",
        "error_message": "Error Message"
    }
)

st.dataframe(
    execution_history_df,
    use_container_width=True,
    hide_index=True
)