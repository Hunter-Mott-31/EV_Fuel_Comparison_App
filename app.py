from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

from calculations import *

# --------------------------------------------------
# PAGE SETTINGS
# --------------------------------------------------

st.set_page_config(
    page_title="Vehicle Fuel Cost Comparison",
    page_icon="🚗",
    layout="wide"
)

st.title("🚗 Vehicle Fuel Cost Comparison Tool")

# --------------------------------------------------
# LOAD DATA
# --------------------------------------------------

def load_vehicle_data():
    candidates = [
        Path(__file__).resolve().parent / "Data" / "vehicles.csv",
        Path(__file__).resolve().parent / "data" / "vehicles.csv",
        Path.cwd() / "Data" / "vehicles.csv",
        Path.cwd() / "data" / "vehicles.csv",
    ]

    for path in candidates:
        if path.exists():
            return pd.read_csv(path, low_memory=False)

    checked_paths = "\n".join(str(path) for path in candidates)
    raise FileNotFoundError(
        "Could not find vehicles.csv. Checked:\n"
        f"{checked_paths}"
    )


try:
    df = load_vehicle_data()
except FileNotFoundError as exc:
    st.error(str(exc))
    st.stop()

# --------------------------------------------------
# CREATE VEHICLE LABELS
# --------------------------------------------------

df["vehicle_label"] = (
    df["year"].astype(str)
    + " "
    + df["make"]
    + " "
    + df["model"]
)

# --------------------------------------------------
# VEHICLE TYPE CLASSIFICATION
# --------------------------------------------------

df["vehicle_type"] = df.apply(
    vehicle_type,
    axis=1
)

# --------------------------------------------------
# SIDEBAR INPUTS
# --------------------------------------------------

st.sidebar.header("Fuel Cost Assumptions")

gas_price = st.sidebar.number_input(
    "Gas Price ($/gal)",
    0.00,
    20.00,
    4.50
)

home_rate = st.sidebar.number_input(
    "Home Electricity ($/kWh)",
    0.00,
    3.00,
    0.14
)

dcfc_rate = st.sidebar.number_input(
    "DC Fast Charging ($/kWh)",
    0.00,
    5.00,
    0.40
)

annual_miles = st.sidebar.number_input(
    "Annual Miles Driven",
    1000,
    50000,
    12000
)

home_percent = st.sidebar.slider(
    "Percent Home Charging",
    0,
    100,
    80
)

# --------------------------------------------------
# FILTERS
# --------------------------------------------------

filtered_df = df

make_list = sorted(
    filtered_df["make"].dropna().unique()
)

st.sidebar.header("EPA Dataset Filters")

search_text = st.sidebar.text_input(
    "Search Make or Model",
    placeholder="e.g. Tesla"
)

year_min = int(filtered_df["year"].min())
year_max = int(filtered_df["year"].max())

year_range = st.sidebar.slider(
    "Model Year Range",
    year_min,
    year_max,
    (year_min, year_max)
)

default_make = "Toyota"
current_vehicle_label = "2026 Toyota Tundra 2WD"
replacement_vehicle_label = "2026 Toyota Prius"

current_make = st.selectbox(
    "Current Vehicle Make",
    make_list,
    index=make_list.index(default_make) if default_make in make_list else 0
)

new_make = st.selectbox(
    "Replacement Vehicle Make",
    make_list,
    index=make_list.index(default_make) if default_make in make_list else 0
)

# --------------------------------------------------
# VEHICLE SELECTIONS
# --------------------------------------------------

current_make_df = filtered_df[
    filtered_df["make"] == current_make
]

new_make_df = filtered_df[
    filtered_df["make"] == new_make
]

col1, col2 = st.columns(2)

current_vehicle_options = sorted(
    current_make_df["vehicle_label"].unique()
)
new_vehicle_options = sorted(
    new_make_df["vehicle_label"].unique()
)

current_vehicle_index = (
    current_vehicle_options.index(current_vehicle_label)
    if current_vehicle_label in current_vehicle_options
    else 0
)
new_vehicle_index = (
    new_vehicle_options.index(replacement_vehicle_label)
    if replacement_vehicle_label in new_vehicle_options
    else 0
)

with col1:

    current_vehicle_name = st.selectbox(
        "Current Vehicle",
        current_vehicle_options,
        index=current_vehicle_index
    )

with col2:

    new_vehicle_name = st.selectbox(
        "Replacement Vehicle",
        new_vehicle_options,
        index=new_vehicle_index
    )

# --------------------------------------------------
# RETRIEVE SELECTED VEHICLES
# --------------------------------------------------

current_vehicle = current_make_df[
    current_make_df["vehicle_label"]
    == current_vehicle_name
].iloc[0]

new_vehicle = new_make_df[
    new_make_df["vehicle_label"]
    == new_vehicle_name
].iloc[0]

# --------------------------------------------------
# COST CALCULATIONS
# --------------------------------------------------

effective_rate = (
    (home_percent / 100) * home_rate
    +
    ((100 - home_percent) / 100) * dcfc_rate
)

current_cpm = calculate_cost_per_mile(
    current_vehicle,
    gas_price,
    effective_rate
)

new_cpm = calculate_cost_per_mile(
    new_vehicle,
    gas_price,
    effective_rate
)

current_annual = (
    current_cpm * annual_miles
)

new_annual = (
    new_cpm * annual_miles
)

annual_savings = (
    current_annual - new_annual
)

monthly_savings = (
    annual_savings / 12
)

five_year_savings = (
    annual_savings * 5
)

# --------------------------------------------------
# TABS
# --------------------------------------------------

tab1, tab2, tab3, tab4 = st.tabs(
    [
        "Comparison",
        "EV Charging",
        "Vehicle Details",
        "EPA Dataset"
    ]
)

# ==================================================
# TAB 1 - COMPARISON
# ==================================================

with tab1:

    st.header("Cost Comparison")

    metric1, metric2, metric3 = st.columns(3)

    with metric1:
        st.metric(
            "Current Vehicle",
            f"${current_annual:,.0f}/yr"
        )

    with metric2:
        st.metric(
            "Replacement Vehicle",
            f"${new_annual:,.0f}/yr"
        )

    with metric3:
        st.metric(
            "Annual Savings",
            f"${annual_savings:,.0f}",
            delta=f"${annual_savings:,.0f}"
        )

    metric4, metric5, metric6 = st.columns(3)

    with metric4:
        st.metric(
            "Monthly Savings",
            f"${monthly_savings:,.0f}"
        )

    with metric5:
        st.metric(
            "5-Year Savings",
            f"${five_year_savings:,.0f}"
        )

    with metric6:
        st.metric(
            "Fuel Cost Difference Per Mile",
            f"${abs(current_cpm-new_cpm):.3f}"
        )

    cpm_col1, cpm_col2 = st.columns(2)

    with cpm_col1:
        st.metric(
            "Current Cost Per Mile",
            f"${current_cpm:.3f}"
        )

    with cpm_col2:
        st.metric(
            "Replacement Cost Per Mile",
            f"${new_cpm:.3f}"
        )

    chart_df = pd.DataFrame(
        {
            "Vehicle": [
                "Current Vehicle",
                "Replacement Vehicle"
            ],
            "Annual Cost": [
                current_annual,
                new_annual
            ]
        }
    )

    fig = px.bar(
        chart_df,
        x="Vehicle",
        y="Annual Cost",
        color="Vehicle",
        text="Annual Cost",
        title="Annual Fuel Cost Comparison",
        color_discrete_map={
            "Current Vehicle": "red",
            "Replacement Vehicle": "royalblue"
        }
    )

    fig.update_traces(
        texttemplate="$%{y:,.0f}",
        textposition="outside"
    )

    fig.update_layout(
        title_x=0.5,
        showlegend=False,
        yaxis_title="Annual Fuel Cost ($)",
        xaxis_title=""
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

# ==================================================
# TAB 2 - EV CHARGING
# ==================================================

with tab2:

    if vehicle_type(new_vehicle) == "BEV":

        home_cpm = (
            new_vehicle["combE"] / 100
        ) * home_rate

        fast_cpm = (
            new_vehicle["combE"] / 100
        ) * dcfc_rate

        left_col, right_col = st.columns(2)

        with left_col:

            st.metric(
                "Home Charging",
                f"${home_cpm:.3f}/mile"
            )

        with right_col:

            st.metric(
                "DC Fast Charging",
                f"${fast_cpm:.3f}/mile"
            )

        st.info(
            f"{home_percent}% home charging assumed."
        )

    else:

        st.warning(
            "Replacement vehicle is not a BEV."
        )

# ==================================================
# TAB 3 - VEHICLE DETAILS
# ==================================================

with tab3:

    left, right = st.columns(2)

    with left:

        st.subheader("Current Vehicle")

        st.write(f"Make: {current_vehicle['make']}")
        st.write(f"Model: {current_vehicle['model']}")
        st.write(f"Vehicle Type: {vehicle_type(current_vehicle)}")
        st.write(f"Fuel Type: {current_vehicle['fuelType1']}")
        st.write(f"Combined MPG: {current_vehicle['comb08']}")
        st.write(f"Cost Per Mile: ${current_cpm:.3f}")
        st.write(f"Annual Fuel Cost: ${current_annual:,.0f}")

        if pd.notna(current_vehicle["combE"]):
            st.write(
                f"Electric Consumption: "
                f"{current_vehicle['combE']} kWh/100 miles"
            )

    with right:

        st.subheader("Replacement Vehicle")

        st.write(f"Make: {new_vehicle['make']}")
        st.write(f"Model: {new_vehicle['model']}")
        st.write(f"Vehicle Type: {vehicle_type(new_vehicle)}")
        st.write(f"Fuel Type: {new_vehicle['fuelType1']}")
        st.write(f"Combined MPG: {new_vehicle['comb08']}")
        st.write(f"Cost Per Mile: ${new_cpm:.3f}")
        st.write(f"Annual Fuel Cost: ${new_annual:,.0f}")

        if pd.notna(new_vehicle["combE"]):
            st.write(
                f"Electric Consumption: "
                f"{new_vehicle['combE']} kWh/100 miles"
            )

# ==================================================
# TAB 4 - EPA DATASET
# ==================================================

with tab4:

    st.header("EPA Dataset Explorer")
    st.caption(
        "Filter the EPA vehicle data to inspect the most relevant fields in a table."
    )

    dataset_df = filtered_df.copy()

    dataset_df = dataset_df[
        (dataset_df["year"] >= year_range[0])
        & (dataset_df["year"] <= year_range[1])
    ]

    if search_text:

        search_text = search_text.lower()

        dataset_df = dataset_df[
            dataset_df["make"].astype(str).str.lower().str.contains(search_text)
            | dataset_df["model"].astype(str).str.lower().str.contains(search_text)
        ]

    column_map = {
        "year": "year",
        "make": "make",
        "model": "model",
        "fuelType1": "fuelType1",
        "comb08": "comb08",
        "combE": "combE"
    }

    available_columns = {}
    for source_name, target_name in column_map.items():
        if target_name in dataset_df.columns:
            available_columns[source_name] = target_name

    for required_name in ["year", "make", "model", "fuelType1", "comb08", "combE"]:
        if required_name not in available_columns:
            available_columns[required_name] = required_name

    dataset_display = dataset_df[
        [
            available_columns["year"],
            available_columns["make"],
            available_columns["model"],
            available_columns["fuelType1"],
            available_columns["comb08"],
            available_columns["combE"]
        ]
    ].copy()

    dataset_display.columns = [
        "Year",
        "Make",
        "Model",
        "Fuel Type",
        "Combined MPG",
        "Combined kWh/100mi"
    ]

    dataset_display = dataset_display.fillna({
        "Combined MPG": "N/A",
        "Combined kWh/100mi": "N/A"
    })

    st.dataframe(
        dataset_display,
        width="stretch",
        height=500
    )