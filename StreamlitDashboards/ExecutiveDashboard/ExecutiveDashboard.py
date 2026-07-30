import streamlit as st
from snowflake.snowpark.context import get_active_session

# ----------------------------------------------------------
# PAGE CONFIG
# ----------------------------------------------------------

st.set_page_config(
    page_title="NYC Taxi Analytics Dashboard",
    page_icon="🚕",
    layout="wide"
)

session = get_active_session()

# ----------------------------------------------------------
# TITLE
# ----------------------------------------------------------

st.title("🚕 NYC Taxi Analytics Dashboard")
st.markdown("### Executive Overview")

st.divider()

# ----------------------------------------------------------
# LOAD KPI DATA
# ----------------------------------------------------------


kpi_df = session.sql("""
SELECT
    SUM("total_trips") AS total_trips,
    SUM("total_revenue") AS total_revenue,
    AVG("average_fare") AS average_fare,
    AVG("average_trip_distance") AS average_trip_distance,
    AVG("average_speed") AS average_speed,
    AVG("average_tip") AS average_tip
FROM GOLD_DASHBOARD_METRICS
""").to_pandas()

row = kpi_df.iloc[0]
# ----------------------------------------------------------
# KPI CARDS
# ----------------------------------------------------------

col1, col2, col3= st.columns(3)

col1.metric(
    "🚕 Total Trips",
    f"{row['TOTAL_TRIPS']/1_000_000:.2f} M")

col2.metric(
    "💰 Total Revenue",
    f"${row['TOTAL_REVENUE']/1_000_000:.2f} M"
)

col3.metric(
    "💵 Average Fare",
    f"${row['AVERAGE_FARE']:.2f}"
)

col4, col5, col6 = st.columns(3)

col4.metric(
    "📏 Avg Distance",
    f"{row['AVERAGE_TRIP_DISTANCE']:.2f} mi"
)

col5.metric(
    "⚡ Avg Speed",
    f"{row['AVERAGE_SPEED']:.2f} mph"
)

col6.metric(
    "🎁 Avg Tip",
    f"${row['AVERAGE_TIP']:.2f}"
)

st.divider()

# ----------------------------------------------------------
# LOAD DAILY METRICS
# ----------------------------------------------------------

daily_df = session.sql("""
SELECT
    "pickup_date",
    "total_trips",
    "total_revenue",
    "average_fare",
    "average_trip_distance",
    "average_tip",
    "vendor1_trips",
    "vendor2_trips",
    "credit_card_trips",
    "cash_trips",
    "morning_trips",
    "afternoon_trips",
    "evening_trips",
    "night_trips",
    "weekday_trips",
    "weekend_trips",
    "airport_pickups"
FROM GOLD_DASHBOARD_METRICS
where "pickup_date"> '2025-08-01'
ORDER BY "pickup_date"
""").to_pandas()

# ----------------------------------------------------------
# REVENUE TREND
# ----------------------------------------------------------

st.subheader("📈 Revenue Trend")

revenue_chart = (
    daily_df
    .set_index("pickup_date")["total_revenue"]
)

st.line_chart(
    revenue_chart,
    use_container_width=True
)

# ----------------------------------------------------------
# Trips by day
# ----------------------------------------------------------
st.subheader("🚕 Trips by Day")

trips_chart = (
    daily_df
    .set_index("pickup_date")["total_trips"]
)

st.area_chart(
    trips_chart,
    use_container_width=True
)

# ----------------------------------------------------------
# VENDOR ANALYSIS
# ----------------------------------------------------------

import altair as alt
import pandas as pd

st.subheader("🚖 Vendor Analysis")

# ----------------------------------------------------------
# LOAD VENDOR METRICS
# ----------------------------------------------------------

vendor_df = session.sql("""
SELECT
    SUM("vendor1_trips") AS vendor1_trips,
    SUM("vendor2_trips") AS vendor2_trips,
    SUM("vendor1_revenue") AS vendor1_revenue,
    SUM("vendor2_revenue") AS vendor2_revenue
FROM GOLD_DASHBOARD_METRICS
""").to_pandas()

vendor_df.columns = vendor_df.columns.str.lower()

# ----------------------------------------------------------
# TRANSFORM DATA INTO VENDOR-LEVEL ROWS
# ----------------------------------------------------------

vendor_analysis_df = pd.DataFrame(
    {
        "vendor": [
            "Creative Mobile Technologies",
            "VeriFone Inc."
        ],
        "total_trips": [
            vendor_df.loc[0, "vendor1_trips"],
            vendor_df.loc[0, "vendor2_trips"]
        ],
        "total_revenue": [
            vendor_df.loc[0, "vendor1_revenue"],
            vendor_df.loc[0, "vendor2_revenue"]
        ]
    }
)

vendor_analysis_df["total_trips"] = pd.to_numeric(
    vendor_analysis_df["total_trips"],
    errors="coerce"
).fillna(0)

vendor_analysis_df["total_revenue"] = pd.to_numeric(
    vendor_analysis_df["total_revenue"],
    errors="coerce"
).fillna(0)

vendor_analysis_df["average_revenue_per_trip"] = (
    vendor_analysis_df["total_revenue"]
    / vendor_analysis_df["total_trips"].replace(0, pd.NA)
).fillna(0)

# ----------------------------------------------------------
# VENDOR KPI CARDS
# ----------------------------------------------------------

top_vendor_by_trips = vendor_analysis_df.loc[
    vendor_analysis_df["total_trips"].idxmax()
]

top_vendor_by_revenue = vendor_analysis_df.loc[
    vendor_analysis_df["total_revenue"].idxmax()
]

vendor_kpi_col1, vendor_kpi_col2, vendor_kpi_col3 = st.columns(3)

with vendor_kpi_col1:
    st.metric(
        label="Top Vendor by Trips",
        value=top_vendor_by_trips["vendor"],
        delta=f'{int(top_vendor_by_trips["total_trips"]):,} trips'
    )

with vendor_kpi_col2:
    st.metric(
        label="Top Vendor by Revenue",
        value=top_vendor_by_revenue["vendor"],
        delta=f'${top_vendor_by_revenue["total_revenue"]:,.2f}'
    )

with vendor_kpi_col3:
    combined_revenue = vendor_analysis_df["total_revenue"].sum()

    st.metric(
        label="Combined Vendor Revenue",
        value=f"${combined_revenue / 1_000_000:.2f} M"
    )

# ----------------------------------------------------------
# REVENUE BY VENDOR
# ----------------------------------------------------------

vendor_revenue_chart = (
    alt.Chart(vendor_analysis_df)
    .mark_bar(
        cornerRadiusTopLeft=5,
        cornerRadiusTopRight=5
    )
    .encode(
        x=alt.X(
            "vendor:N",
            title="Vendor",
            sort=alt.EncodingSortField(
                field="total_revenue",
                order="descending"
            ),
            axis=alt.Axis(
                labelAngle=0,
                labelLimit=250
            )
        ),
        y=alt.Y(
            "total_revenue:Q",
            title="Total Revenue",
            axis=alt.Axis(format="$,.2s")
        ),
        tooltip=[
            alt.Tooltip(
                "vendor:N",
                title="Vendor"
            ),
            alt.Tooltip(
                "total_revenue:Q",
                title="Total Revenue",
                format="$,.2f"
            ),
            alt.Tooltip(
                "total_trips:Q",
                title="Total Trips",
                format=","
            ),
            alt.Tooltip(
                "average_revenue_per_trip:Q",
                title="Revenue per Trip",
                format="$,.2f"
            )
        ]
    )
    .properties(
        height=400,
        title="Revenue by Vendor"
    )
)

# ----------------------------------------------------------
# TRIPS BY VENDOR
# ----------------------------------------------------------

vendor_trips_chart = (
    alt.Chart(vendor_analysis_df)
    .mark_bar(
        cornerRadiusTopLeft=5,
        cornerRadiusTopRight=5
    )
    .encode(
        x=alt.X(
            "vendor:N",
            title="Vendor",
            sort=alt.EncodingSortField(
                field="total_trips",
                order="descending"
            ),
            axis=alt.Axis(
                labelAngle=0,
                labelLimit=250
            )
        ),
        y=alt.Y(
            "total_trips:Q",
            title="Total Trips",
            axis=alt.Axis(format=",.2s")
        ),
        tooltip=[
            alt.Tooltip(
                "vendor:N",
                title="Vendor"
            ),
            alt.Tooltip(
                "total_trips:Q",
                title="Total Trips",
                format=","
            ),
            alt.Tooltip(
                "total_revenue:Q",
                title="Total Revenue",
                format="$,.2f"
            ),
            alt.Tooltip(
                "average_revenue_per_trip:Q",
                title="Revenue per Trip",
                format="$,.2f"
            )
        ]
    )
    .properties(
        height=400,
        title="Trips by Vendor"
    )
)

# ----------------------------------------------------------
# DISPLAY CHARTS SIDE BY SIDE
# ----------------------------------------------------------

vendor_chart_col1, vendor_chart_col2 = st.columns(2)

with vendor_chart_col1:
    st.altair_chart(
        vendor_revenue_chart,
        use_container_width=True
    )

with vendor_chart_col2:
    st.altair_chart(
        vendor_trips_chart,
        use_container_width=True
    )

# ----------------------------------------------------------
# VENDOR COMPARISON TABLE
# ----------------------------------------------------------

st.markdown("#### Vendor Comparison")

vendor_display_df = vendor_analysis_df.copy()

vendor_display_df["total_trips"] = vendor_display_df[
    "total_trips"
].map(lambda value: f"{int(value):,}")

vendor_display_df["total_revenue"] = vendor_display_df[
    "total_revenue"
].map(lambda value: f"${value:,.2f}")

vendor_display_df["average_revenue_per_trip"] = vendor_display_df[
    "average_revenue_per_trip"
].map(lambda value: f"${value:,.2f}")

vendor_display_df = vendor_display_df.rename(
    columns={
        "vendor": "Vendor",
        "total_trips": "Total Trips",
        "total_revenue": "Total Revenue",
        "average_revenue_per_trip": "Average Revenue per Trip"
    }
)

st.dataframe(
    vendor_display_df,
    use_container_width=True,
    hide_index=True
)

# ----------------------------------------------------------
# PAYMENT METHOD ANALYSIS
# ----------------------------------------------------------

import altair as alt
import pandas as pd

st.subheader("💳 Payment Method Analysis")

# ----------------------------------------------------------
# LOAD PAYMENT METRICS
# ----------------------------------------------------------

payment_df = session.sql("""
SELECT
    "payment_type",
    "total_trips",
    "total_revenue",
    "avg_fare_amount",
    "avg_trip_distance"
FROM GOLD_PAYMENT_METRICS
ORDER BY "total_trips" DESC
""").to_pandas()

payment_df.columns = payment_df.columns.str.lower()

# ----------------------------------------------------------
# CLEAN PAYMENT LABELS
# ----------------------------------------------------------

payment_labels = {
    1: "Credit Card",
    2: "Cash",
    3: "No Charge",
    4: "Dispute",
    0: "Unknown"
}

payment_df["payment_method"] = (
    pd.to_numeric(
        payment_df["payment_type"],
        errors="coerce"
    )
    .map(payment_labels)
    .fillna("Other")
)

for column in [
    "total_trips",
    "total_revenue",
    "avg_fare_amount",
    "avg_trip_distance"
]:
    payment_df[column] = pd.to_numeric(
        payment_df[column],
        errors="coerce"
    ).fillna(0)

# ----------------------------------------------------------
# CALCULATE PAYMENT SHARE
# ----------------------------------------------------------

total_payment_trips = payment_df["total_trips"].sum()

payment_df["trip_percentage"] = (
    payment_df["total_trips"]
    / total_payment_trips
    * 100
).fillna(0)

top_payment_method = payment_df.loc[
    payment_df["total_trips"].idxmax()
]

# ----------------------------------------------------------
# PAYMENT KPI CARDS
# ----------------------------------------------------------

payment_kpi_col1, payment_kpi_col2, payment_kpi_col3 = st.columns(3)

with payment_kpi_col1:
    st.metric(
        label="Most Used Payment Method",
        value=top_payment_method["payment_method"],
        delta=f'{int(top_payment_method["total_trips"]):,} trips'
    )

with payment_kpi_col2:
    st.metric(
        label="Payment Method Share",
        value=f'{top_payment_method["trip_percentage"]:.2f}%'
    )

with payment_kpi_col3:
    st.metric(
        label="Total Payment Revenue",
        value=f'${payment_df["total_revenue"].sum() / 1_000_000:.2f} M'
    )

# ----------------------------------------------------------
# TRIPS BY PAYMENT METHOD
# ----------------------------------------------------------

payment_trips_chart = (
    alt.Chart(payment_df)
    .mark_bar(
        cornerRadiusTopLeft=5,
        cornerRadiusTopRight=5
    )
    .encode(
        x=alt.X(
            "payment_method:N",
            title="Payment Method",
            sort=alt.EncodingSortField(
                field="total_trips",
                order="descending"
            ),
            axis=alt.Axis(
                labelAngle=0,
                labelLimit=150
            )
        ),
        y=alt.Y(
            "total_trips:Q",
            title="Total Trips",
            axis=alt.Axis(format=",.2s")
        ),
        tooltip=[
            alt.Tooltip(
                "payment_method:N",
                title="Payment Method"
            ),
            alt.Tooltip(
                "total_trips:Q",
                title="Total Trips",
                format=","
            ),
            alt.Tooltip(
                "trip_percentage:Q",
                title="Trip Share",
                format=".2f"
            ),
            alt.Tooltip(
                "total_revenue:Q",
                title="Total Revenue",
                format="$,.2f"
            )
        ]
    )
    .properties(
        height=400,
        title="Trips by Payment Method"
    )
)

# ----------------------------------------------------------
# REVENUE BY PAYMENT METHOD
# ----------------------------------------------------------

payment_revenue_chart = (
    alt.Chart(payment_df)
    .mark_bar(
        cornerRadiusTopLeft=5,
        cornerRadiusTopRight=5
    )
    .encode(
        x=alt.X(
            "payment_method:N",
            title="Payment Method",
            sort=alt.EncodingSortField(
                field="total_revenue",
                order="descending"
            ),
            axis=alt.Axis(
                labelAngle=0,
                labelLimit=150
            )
        ),
        y=alt.Y(
            "total_revenue:Q",
            title="Total Revenue",
            axis=alt.Axis(format="$,.2s")
        ),
        tooltip=[
            alt.Tooltip(
                "payment_method:N",
                title="Payment Method"
            ),
            alt.Tooltip(
                "total_revenue:Q",
                title="Total Revenue",
                format="$,.2f"
            ),
            alt.Tooltip(
                "avg_fare_amount:Q",
                title="Average Fare",
                format="$,.2f"
            ),
            alt.Tooltip(
                "avg_trip_distance:Q",
                title="Average Trip Distance",
                format="$,.2f"
            )
        ]
    )
    .properties(
        height=400,
        title="Revenue by Payment Method"
    )
)

# ----------------------------------------------------------
# DISPLAY PAYMENT CHARTS
# ----------------------------------------------------------

payment_chart_col1, payment_chart_col2 = st.columns(2)

with payment_chart_col1:
    st.altair_chart(
        payment_trips_chart,
        use_container_width=True
    )

with payment_chart_col2:
    st.altair_chart(
        payment_revenue_chart,
        use_container_width=True
    )

# ----------------------------------------------------------
# PAYMENT COMPARISON TABLE
# ----------------------------------------------------------

st.markdown("#### Payment Method Comparison")

payment_display_df = payment_df[
    [
        "payment_method",
        "total_trips",
        "trip_percentage",
        "total_revenue",
        "avg_fare_amount",
        "avg_trip_distance"
    ]
].copy()

payment_display_df["total_trips"] = payment_display_df[
    "total_trips"
].map(lambda value: f"{int(value):,}")

payment_display_df["trip_percentage"] = payment_display_df[
    "trip_percentage"
].map(lambda value: f"{value:.2f}%")

for column in [
    "total_revenue",
    "avg_fare_amount",
    "avg_trip_distance"
]:
    payment_display_df[column] = payment_display_df[
        column
    ].map(lambda value: f"${value:,.2f}")

payment_display_df = payment_display_df.rename(
    columns={
        "payment_method": "Payment Method",
        "total_trips": "Total Trips",
        "trip_percentage": "Trip Share",
        "total_revenue": "Total Revenue",
        "avg_fare_amount": "Average Fare",
        "avg_trip_distance": "Average Trip Distance"
    }
)

st.dataframe(
    payment_display_df,
    use_container_width=True,
    hide_index=True
)

# ----------------------------------------------------------
# HOURLY ANALYSIS
# ----------------------------------------------------------

st.subheader("⏰ Hourly Analysis")

# ----------------------------------------------------------
# LOAD HOURLY METRICS
# ----------------------------------------------------------

hourly_df = session.sql("""
SELECT
    "pickup_hour",
    "total_trips",
    "total_revenue",
    "avg_trip_distance",
    "avg_trip_duration_minutes",
    "avg_total_amount",
    "gold_updated_at"
FROM GOLD_HOURLY_METRICS
ORDER BY "pickup_hour"
""").to_pandas()

hourly_df.columns = hourly_df.columns.str.lower()

# ----------------------------------------------------------
# CLEAN DATA TYPES
# ----------------------------------------------------------

numeric_columns = [
    "pickup_hour",
    "total_trips",
    "total_revenue",
    "avg_trip_distance",
    "avg_trip_duration_minutes",
    "avg_total_amount"
]

for column in numeric_columns:
    hourly_df[column] = pd.to_numeric(
        hourly_df[column],
        errors="coerce"
    ).fillna(0)

hourly_df["pickup_hour"] = hourly_df["pickup_hour"].astype(int)

# Create readable hour labels
hourly_df["hour_label"] = hourly_df["pickup_hour"].apply(
    lambda hour: (
        "12 AM"
        if hour == 0
        else "12 PM"
        if hour == 12
        else f"{hour} AM"
        if hour < 12
        else f"{hour - 12} PM"
    )
)

# Keep chart hours in chronological order
hour_sort_order = hourly_df["hour_label"].tolist()

# ----------------------------------------------------------
# CALCULATE HOURLY KPIS
# ----------------------------------------------------------

peak_trip_row = hourly_df.loc[
    hourly_df["total_trips"].idxmax()
]

peak_revenue_row = hourly_df.loc[
    hourly_df["total_revenue"].idxmax()
]

average_hourly_trips = hourly_df["total_trips"].mean()
average_revenue_per_hour = hourly_df["total_revenue"].mean()

# ----------------------------------------------------------
# HOURLY KPI CARDS
# ----------------------------------------------------------

hourly_kpi_col1, hourly_kpi_col2, hourly_kpi_col3, hourly_kpi_col4 = (
    st.columns(4)
)

with hourly_kpi_col1:
    st.metric(
        label="Peak Trip Hour",
        value=peak_trip_row["hour_label"],
        delta=f'{int(peak_trip_row["total_trips"]):,} trips'
    )

with hourly_kpi_col2:
    st.metric(
        label="Peak Revenue Hour",
        value=peak_revenue_row["hour_label"],
        delta=f'${peak_revenue_row["total_revenue"]:,.2f}'
    )

with hourly_kpi_col3:
    st.metric(
        label="Average Trips per Hour",
        value=f"{average_hourly_trips:,.0f}"
    )

with hourly_kpi_col4:
    st.metric(
        label="Average Revenue per Hour",
        value=f"${average_revenue_per_hour / 1_000_000:.2f} M"
    )

# ----------------------------------------------------------
# TRIPS BY HOUR
# ----------------------------------------------------------

trips_by_hour_chart = (
    alt.Chart(hourly_df)
    .mark_line(point=True)
    .encode(
        x=alt.X(
            "hour_label:N",
            title="Pickup Hour",
            sort=hour_sort_order,
            axis=alt.Axis(
                labelAngle=0,
                labelOverlap=True
            )
        ),
        y=alt.Y(
            "total_trips:Q",
            title="Total Trips",
            axis=alt.Axis(format=",.2s")
        ),
        tooltip=[
            alt.Tooltip(
                "hour_label:N",
                title="Pickup Hour"
            ),
            alt.Tooltip(
                "total_trips:Q",
                title="Total Trips",
                format=","
            ),
            alt.Tooltip(
                "total_revenue:Q",
                title="Total Revenue",
                format="$,.2f"
            )
        ]
    )
    .properties(
        height=400,
        title="Trips by Pickup Hour"
    )
)

# ----------------------------------------------------------
# REVENUE BY HOUR
# ----------------------------------------------------------

revenue_by_hour_chart = (
    alt.Chart(hourly_df)
    .mark_line(point=True)
    .encode(
        x=alt.X(
            "hour_label:N",
            title="Pickup Hour",
            sort=hour_sort_order,
            axis=alt.Axis(
                labelAngle=0,
                labelOverlap=True
            )
        ),
        y=alt.Y(
            "total_revenue:Q",
            title="Total Revenue",
            axis=alt.Axis(format="$,.2s")
        ),
        tooltip=[
            alt.Tooltip(
                "hour_label:N",
                title="Pickup Hour"
            ),
            alt.Tooltip(
                "total_revenue:Q",
                title="Total Revenue",
                format="$,.2f"
            ),
            alt.Tooltip(
                "total_trips:Q",
                title="Total Trips",
                format=","
            )
        ]
    )
    .properties(
        height=400,
        title="Revenue by Pickup Hour"
    )
)

# ----------------------------------------------------------
# DISPLAY MAIN HOURLY CHARTS
# ----------------------------------------------------------

hourly_chart_col1, hourly_chart_col2 = st.columns(2)

with hourly_chart_col1:
    st.altair_chart(
        trips_by_hour_chart,
        use_container_width=True
    )

with hourly_chart_col2:
    st.altair_chart(
        revenue_by_hour_chart,
        use_container_width=True
    )

# ----------------------------------------------------------
# AVERAGE TRIP DISTANCE BY HOUR
# ----------------------------------------------------------

distance_by_hour_chart = (
    alt.Chart(hourly_df)
    .mark_bar(
        cornerRadiusTopLeft=4,
        cornerRadiusTopRight=4
    )
    .encode(
        x=alt.X(
            "hour_label:N",
            title="Pickup Hour",
            sort=hour_sort_order,
            axis=alt.Axis(
                labelAngle=0,
                labelOverlap=True
            )
        ),
        y=alt.Y(
            "avg_trip_distance:Q",
            title="Average Trip Distance"
        ),
        tooltip=[
            alt.Tooltip(
                "hour_label:N",
                title="Pickup Hour"
            ),
            alt.Tooltip(
                "avg_trip_distance:Q",
                title="Average Trip Distance",
                format=".2f"
            )
        ]
    )
    .properties(
        height=350,
        title="Average Trip Distance by Hour"
    )
)

# ----------------------------------------------------------
# AVERAGE TRIP DURATION BY HOUR
# ----------------------------------------------------------

duration_by_hour_chart = (
    alt.Chart(hourly_df)
    .mark_line(point=True)
    .encode(
        x=alt.X(
            "hour_label:N",
            title="Pickup Hour",
            sort=hour_sort_order,
            axis=alt.Axis(
                labelAngle=0,
                labelOverlap=True
            )
        ),
        y=alt.Y(
            "avg_trip_duration_minutes:Q",
            title="Average Trip Duration (Minutes)"
        ),
        tooltip=[
            alt.Tooltip(
                "hour_label:N",
                title="Pickup Hour"
            ),
            alt.Tooltip(
                "avg_trip_duration_minutes:Q",
                title="Average Duration",
                format=".2f"
            )
        ]
    )
    .properties(
        height=350,
        title="Average Trip Duration by Hour"
    )
)

# ----------------------------------------------------------
# DISPLAY SECONDARY HOURLY CHARTS
# ----------------------------------------------------------

hourly_detail_col1, hourly_detail_col2 = st.columns(2)

with hourly_detail_col1:
    st.altair_chart(
        distance_by_hour_chart,
        use_container_width=True
    )

with hourly_detail_col2:
    st.altair_chart(
        duration_by_hour_chart,
        use_container_width=True
    )

# ----------------------------------------------------------
# AVERAGE TOTAL AMOUNT BY HOUR
# ----------------------------------------------------------

average_amount_chart = (
    alt.Chart(hourly_df)
    .mark_line(point=True)
    .encode(
        x=alt.X(
            "hour_label:N",
            title="Pickup Hour",
            sort=hour_sort_order,
            axis=alt.Axis(
                labelAngle=0,
                labelOverlap=True
            )
        ),
        y=alt.Y(
            "avg_total_amount:Q",
            title="Average Total Amount",
            axis=alt.Axis(format="$,.2f")
        ),
        tooltip=[
            alt.Tooltip(
                "hour_label:N",
                title="Pickup Hour"
            ),
            alt.Tooltip(
                "avg_total_amount:Q",
                title="Average Total Amount",
                format="$,.2f"
            )
        ]
    )
    .properties(
        height=350,
        title="Average Total Amount by Hour"
    )
)

st.altair_chart(
    average_amount_chart,
    use_container_width=True
)

# ----------------------------------------------------------
# HOURLY COMPARISON TABLE
# ----------------------------------------------------------

st.markdown("#### Hourly Metrics Comparison")

hourly_display_df = hourly_df[
    [
        "hour_label",
        "total_trips",
        "total_revenue",
        "avg_trip_distance",
        "avg_trip_duration_minutes",
        "avg_total_amount"
    ]
].copy()

hourly_display_df["total_trips"] = hourly_display_df[
    "total_trips"
].map(lambda value: f"{int(value):,}")

hourly_display_df["total_revenue"] = hourly_display_df[
    "total_revenue"
].map(lambda value: f"${value:,.2f}")

hourly_display_df["avg_trip_distance"] = hourly_display_df[
    "avg_trip_distance"
].map(lambda value: f"{value:.2f}")

hourly_display_df["avg_trip_duration_minutes"] = hourly_display_df[
    "avg_trip_duration_minutes"
].map(lambda value: f"{value:.2f}")

hourly_display_df["avg_total_amount"] = hourly_display_df[
    "avg_total_amount"
].map(lambda value: f"${value:.2f}")

hourly_display_df = hourly_display_df.rename(
    columns={
        "hour_label": "Pickup Hour",
        "total_trips": "Total Trips",
        "total_revenue": "Total Revenue",
        "avg_trip_distance": "Average Trip Distance",
        "avg_trip_duration_minutes": "Average Duration (Minutes)",
        "avg_total_amount": "Average Total Amount"
    }
)

st.dataframe(
    hourly_display_df,
    use_container_width=True,
    hide_index=True
)

# ----------------------------------------------------------
# DAILY PERFORMANCE
# ----------------------------------------------------------

st.subheader("📅 Daily Performance")

# ----------------------------------------------------------
# LOAD DAILY METRICS
# ----------------------------------------------------------

daily_df = session.sql("""
SELECT
    "pickup_date",
    "total_trips",
    "total_revenue",
    "avg_fare_amount",
    "avg_fare_per_mile",
    "avg_trip_distance",
    "avg_trip_duration_minutes",
    "gold_updated_at"
FROM GOLD_DAILY_METRICS
where "pickup_date" > '2025-07-01'
ORDER BY "pickup_date"
""").to_pandas()

daily_df.columns = daily_df.columns.str.lower()

# ----------------------------------------------------------
# CLEAN DATA TYPES
# ----------------------------------------------------------

daily_df["pickup_date"] = pd.to_datetime(
    daily_df["pickup_date"],
    errors="coerce"
)

numeric_columns = [
    "total_trips",
    "total_revenue",
    "avg_fare_amount",
    "avg_fare_per_mile",
    "avg_trip_distance",
    "avg_trip_duration_minutes"
]

for column in numeric_columns:
    daily_df[column] = pd.to_numeric(
        daily_df[column],
        errors="coerce"
    ).fillna(0)

daily_df = (
    daily_df
    .dropna(subset=["pickup_date"])
    .sort_values("pickup_date")
    .reset_index(drop=True)
)

daily_df["date_label"] = daily_df["pickup_date"].dt.strftime("%d %b %Y")
daily_df["day_name"] = daily_df["pickup_date"].dt.day_name()

# ----------------------------------------------------------
# CALCULATE DAILY KPIS
# ----------------------------------------------------------

peak_trip_row = daily_df.loc[
    daily_df["total_trips"].idxmax()
]

peak_revenue_row = daily_df.loc[
    daily_df["total_revenue"].idxmax()
]

average_daily_trips = daily_df["total_trips"].mean()
average_daily_revenue = daily_df["total_revenue"].mean()

# ----------------------------------------------------------
# DAILY KPI CARDS
# ----------------------------------------------------------

daily_kpi_col1, daily_kpi_col2, daily_kpi_col3, daily_kpi_col4 = (
    st.columns(4)
)

with daily_kpi_col1:
    st.metric(
        label="Busiest Day",
        value=peak_trip_row["pickup_date"].strftime("%d %b"),
        delta=f'{int(peak_trip_row["total_trips"]):,} trips'
    )

with daily_kpi_col2:
    st.metric(
        label="Highest Revenue Day",
        value=peak_revenue_row["pickup_date"].strftime("%d %b"),
        delta=f'${peak_revenue_row["total_revenue"]:,.2f}'
    )

with daily_kpi_col3:
    st.metric(
        label="Average Daily Trips",
        value=f"{average_daily_trips:,.0f}"
    )

with daily_kpi_col4:
    st.metric(
        label="Average Daily Revenue",
        value=f"${average_daily_revenue / 1_000_000:.2f} M"
    )

# ----------------------------------------------------------
# DAILY TRIPS TREND
# ----------------------------------------------------------

daily_trips_chart = (
    alt.Chart(daily_df)
    .mark_line(point=True)
    .encode(
        x=alt.X(
            "pickup_date:T",
            title="Pickup Date",
            axis=alt.Axis(format="%d %b")
        ),
        y=alt.Y(
            "total_trips:Q",
            title="Total Trips",
            axis=alt.Axis(format=",.2s")
        ),
        tooltip=[
            alt.Tooltip(
                "date_label:N",
                title="Date"
            ),
            alt.Tooltip(
                "day_name:N",
                title="Day"
            ),
            alt.Tooltip(
                "total_trips:Q",
                title="Total Trips",
                format=","
            )
        ]
    )
    .properties(
        height=400,
        title="Daily Trips Trend"
    )
)

# ----------------------------------------------------------
# DAILY REVENUE TREND
# ----------------------------------------------------------

daily_revenue_chart = (
    alt.Chart(daily_df)
    .mark_area(
        line=True,
        opacity=0.35
    )
    .encode(
        x=alt.X(
            "pickup_date:T",
            title="Pickup Date",
            axis=alt.Axis(format="%d %b")
        ),
        y=alt.Y(
            "total_revenue:Q",
            title="Total Revenue",
            axis=alt.Axis(format="$,.2s")
        ),
        tooltip=[
            alt.Tooltip(
                "date_label:N",
                title="Date"
            ),
            alt.Tooltip(
                "day_name:N",
                title="Day"
            ),
            alt.Tooltip(
                "total_revenue:Q",
                title="Total Revenue",
                format="$,.2f"
            )
        ]
    )
    .properties(
        height=400,
        title="Daily Revenue Trend"
    )
)

# ----------------------------------------------------------
# DISPLAY DAILY TREND CHARTS
# ----------------------------------------------------------

daily_chart_col1, daily_chart_col2 = st.columns(2)

with daily_chart_col1:
    st.altair_chart(
        daily_trips_chart,
        use_container_width=True
    )

with daily_chart_col2:
    st.altair_chart(
        daily_revenue_chart,
        use_container_width=True
    )

# ----------------------------------------------------------
# AVERAGE FARE AMOUNT BY DAY
# ----------------------------------------------------------

average_fare_chart = (
    alt.Chart(daily_df)
    .mark_bar(
        cornerRadiusTopLeft=4,
        cornerRadiusTopRight=4
    )
    .encode(
        x=alt.X(
            "pickup_date:T",
            title="Pickup Date",
            axis=alt.Axis(format="%d %b")
        ),
        y=alt.Y(
            "avg_fare_amount:Q",
            title="Average Fare Amount",
            axis=alt.Axis(format="$,.2f")
        ),
        tooltip=[
            alt.Tooltip(
                "date_label:N",
                title="Date"
            ),
            alt.Tooltip(
                "avg_fare_amount:Q",
                title="Average Fare",
                format="$,.2f"
            )
        ]
    )
    .properties(
        height=350,
        title="Average Fare Amount by Day"
    )
)

# ----------------------------------------------------------
# AVERAGE FARE PER MILE BY DAY
# ----------------------------------------------------------

fare_per_mile_chart = (
    alt.Chart(daily_df)
    .mark_line(point=True)
    .encode(
        x=alt.X(
            "pickup_date:T",
            title="Pickup Date",
            axis=alt.Axis(format="%d %b")
        ),
        y=alt.Y(
            "avg_fare_per_mile:Q",
            title="Average Fare per Mile",
            axis=alt.Axis(format="$,.2f")
        ),
        tooltip=[
            alt.Tooltip(
                "date_label:N",
                title="Date"
            ),
            alt.Tooltip(
                "avg_fare_per_mile:Q",
                title="Average Fare per Mile",
                format="$,.2f"
            )
        ]
    )
    .properties(
        height=350,
        title="Average Fare per Mile by Day"
    )
)

# ----------------------------------------------------------
# DISPLAY FARE CHARTS
# ----------------------------------------------------------

daily_fare_col1, daily_fare_col2 = st.columns(2)

with daily_fare_col1:
    st.altair_chart(
        average_fare_chart,
        use_container_width=True
    )

with daily_fare_col2:
    st.altair_chart(
        fare_per_mile_chart,
        use_container_width=True
    )

# ----------------------------------------------------------
# AVERAGE DISTANCE BY DAY
# ----------------------------------------------------------

daily_distance_chart = (
    alt.Chart(daily_df)
    .mark_line(point=True)
    .encode(
        x=alt.X(
            "pickup_date:T",
            title="Pickup Date",
            axis=alt.Axis(format="%d %b")
        ),
        y=alt.Y(
            "avg_trip_distance:Q",
            title="Average Trip Distance"
        ),
        tooltip=[
            alt.Tooltip(
                "date_label:N",
                title="Date"
            ),
            alt.Tooltip(
                "avg_trip_distance:Q",
                title="Average Distance",
                format=".2f"
            )
        ]
    )
    .properties(
        height=350,
        title="Average Trip Distance by Day"
    )
)

# ----------------------------------------------------------
# AVERAGE DURATION BY DAY
# ----------------------------------------------------------

daily_duration_chart = (
    alt.Chart(daily_df)
    .mark_line(point=True)
    .encode(
        x=alt.X(
            "pickup_date:T",
            title="Pickup Date",
            axis=alt.Axis(format="%d %b")
        ),
        y=alt.Y(
            "avg_trip_duration_minutes:Q",
            title="Average Trip Duration (Minutes)"
        ),
        tooltip=[
            alt.Tooltip(
                "date_label:N",
                title="Date"
            ),
            alt.Tooltip(
                "avg_trip_duration_minutes:Q",
                title="Average Duration",
                format=".2f"
            )
        ]
    )
    .properties(
        height=350,
        title="Average Trip Duration by Day"
    )
)

# ----------------------------------------------------------
# DISPLAY OPERATIONAL CHARTS
# ----------------------------------------------------------

daily_operations_col1, daily_operations_col2 = st.columns(2)

with daily_operations_col1:
    st.altair_chart(
        daily_distance_chart,
        use_container_width=True
    )

with daily_operations_col2:
    st.altair_chart(
        daily_duration_chart,
        use_container_width=True
    )

# ----------------------------------------------------------
# DAILY PERFORMANCE TABLE
# ----------------------------------------------------------

st.markdown("#### Daily Metrics Comparison")

daily_display_df = daily_df[
    [
        "pickup_date",
        "day_name",
        "total_trips",
        "total_revenue",
        "avg_fare_amount",
        "avg_fare_per_mile",
        "avg_trip_distance",
        "avg_trip_duration_minutes"
    ]
].copy()

daily_display_df["pickup_date"] = daily_display_df[
    "pickup_date"
].dt.strftime("%d %b %Y")

daily_display_df["total_trips"] = daily_display_df[
    "total_trips"
].map(lambda value: f"{int(value):,}")

daily_display_df["total_revenue"] = daily_display_df[
    "total_revenue"
].map(lambda value: f"${value:,.2f}")

daily_display_df["avg_fare_amount"] = daily_display_df[
    "avg_fare_amount"
].map(lambda value: f"${value:.2f}")

daily_display_df["avg_fare_per_mile"] = daily_display_df[
    "avg_fare_per_mile"
].map(lambda value: f"${value:.2f}")

daily_display_df["avg_trip_distance"] = daily_display_df[
    "avg_trip_distance"
].map(lambda value: f"{value:.2f}")

daily_display_df["avg_trip_duration_minutes"] = daily_display_df[
    "avg_trip_duration_minutes"
].map(lambda value: f"{value:.2f}")

daily_display_df = daily_display_df.rename(
    columns={
        "pickup_date": "Pickup Date",
        "day_name": "Day",
        "total_trips": "Total Trips",
        "total_revenue": "Total Revenue",
        "avg_fare_amount": "Average Fare",
        "avg_fare_per_mile": "Average Fare per Mile",
        "avg_trip_distance": "Average Trip Distance",
        "avg_trip_duration_minutes": "Average Duration (Minutes)"
    }
)

st.dataframe(
    daily_display_df,
    use_container_width=True,
    hide_index=True
)




