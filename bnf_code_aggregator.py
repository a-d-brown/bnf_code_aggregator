import pandas as pd
import streamlit as st

st.set_page_config(layout="wide")
st.title("BNF Code Aggregator")

# === File uploaders ===
col1, col2 = st.columns([1, 1], gap="large")

with col1:
    st.subheader("Prescribing Data")
    uploaded_file = st.file_uploader("Upload Prescribing Data", type="csv", key="prescribing_data_file")

with col2:
    st.subheader("Codelist")
    codelist_file = st.file_uploader("Upload CSV", type="csv", key="codelist_file")

mo_26_27 = st.button("Use MO Workstreams 26/27")
mo_25_26 = st.button("Use MO Workstreams 25/26")

# === Toggle for alternative calculation method ===
st.markdown("### Options")
use_custom_cost = st.toggle("Apply estimate for special containers")

# === Decide on codelist source ===
if codelist_file:
    codelist_df = pd.read_csv(codelist_file)
elif mo_26_27:
    codelist_df = pd.read_csv("codelists/mo_workstreams_26_27.csv")
elif mo_25_26:
    codelist_df = pd.read_csv("codelists/mo_workstreams_25_26.csv")
else:
    codelist_df = None

# === Run main logic if both inputs are ready ===
if uploaded_file and codelist_df is not None:
    df = pd.read_csv(uploaded_file)

    # === Convert codelist CSV into dictionary ===
    codelists = (
        codelist_df
        .groupby("Category")["BNF Prefix"]
        .apply(list)
        .to_dict()
    )

    included_codes = [
        "84H00", "00P00", "00L00", "01H00", "13T00", "16C00", "99C00", "00N00"
    ]
    df = df[df["Commissioner/Provider Code"].isin(included_codes)]

    all_codes = df["Commissioner/Provider Code"].unique()
    all_categories = list(codelists.keys())

    base_grid = pd.MultiIndex.from_product(
        [all_codes, all_categories],
        names=["Commissioner/Provider Code", "Category"]
    ).to_frame(index=False)

    # === Custom cost multipliers ===
    cost_multipliers = {
        "SABAs": 3.11,
        "Triple Inhalers": 36.41,
        "Gabapentinoids": 3.02,
        "Opioids": 4.89,
        "Antibacterials": 5.71,
        "Vitamin D": 3.06,
        "PPIs": 1.69,
        "Bath Emollients": 7.28,
        "Mesalazine": 41.76,
        "Lidocaine": 70.99,
        "Gluten Free": 20.55,
        "Cosopt 20mg/ml / 5mg/ml eye dps 0.2ml ud preservative free": 33.15,
        "Dovobet gel": 50.87,
        "Ganfort 0.3mg/ml / 5mg/ml eye drops": 19.90,
        "Lumigan 100micrograms/ml eye drops": 16.00,
        "Physeptone 1mg/ml oral solution sugar free": 8.96,
        "Vagifem 10microgram vaginal tablets": 15.23,
        "Xalatan 50micrograms/ml eye drops": 19.36,
    }

    # === Function to aggregate by category ===
    def aggregate_category(df, bnf_prefixes, label):
        filtered = df[df["BNF Code"].str.startswith(tuple(bnf_prefixes), na=False)]
        agg = filtered.groupby("Commissioner/Provider Code").agg({
            "Items": "sum",
            "Quantity X Items": "sum",
            "Estimated Drug Cost GBP": "sum"
        }).reset_index()
        if use_custom_cost and label in cost_multipliers:
            agg["Estimated Drug Cost GBP"] = agg["Items"] * cost_multipliers[label]
        agg["Category"] = label
        return agg

    # === Aggregate by category ===
    results = [aggregate_category(df, prefixes, category) for category, prefixes in codelists.items()]
    combined = pd.concat(results, ignore_index=True)

    # === Fill in missing combinations with zeros ===
    complete = base_grid.merge(combined, on=["Commissioner/Provider Code", "Category"], how="left")
    complete.fillna({"Items": 0, "Quantity X Items": 0, "Estimated Drug Cost GBP": 0}, inplace=True)

    # === Format for display ===
    formatted = complete.copy()
    formatted["Items"] = formatted["Items"].apply(lambda x: f"{int(x):,}")
    formatted["Quantity X Items"] = formatted["Quantity X Items"].apply(lambda x: f"{int(x):,}")
    formatted["Estimated Drug Cost GBP"] = formatted["Estimated Drug Cost GBP"].apply(lambda x: f"£{x:,.2f}")

    # === Display and download ===
    st.subheader("Output")
    st.dataframe(formatted)
    st.download_button(
        "Download CSV",
        complete.to_csv(index=False),
        file_name="aggregated_output.csv",
        mime="text/csv"
    )