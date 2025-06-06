import pandas as pd
import streamlit as st

st.set_page_config(layout="wide")

st.title("BNF Code Aggregator")


# === File uploaders with headings ===
col1, col2 = st.columns([1, 1], gap="large")  # equal columns, wider spacing between

with col1:
    st.subheader("Prescribing Data")
    uploaded_file = st.file_uploader("Upload Prescribing Data", type="csv", key="prescribing_data_file")

with col2:
    st.subheader("Codelist")
    codelist_file = st.file_uploader("Upload CSV", type="csv", key="codelist_file")




if uploaded_file and codelist_file:
    df = pd.read_csv(uploaded_file)
    codelist_df = pd.read_csv(codelist_file)

    # === Convert codelist CSV into dictionary ===
    codelists = (
        codelist_df
        .groupby("Category")["BNF Prefix"]
        .apply(list)
        .to_dict()
    )

    # === Filter by Commissioner/Provider Code ===
    included_codes = [
        "84H00", "00P00", "00L00", "01H00",
        "13T00", "16C00", "99C00", "00N00"
    ]
    df = df[df["Commissioner/Provider Code"].isin(included_codes)]

    # === Get all possible combinations (to fill zeros later) ===
    all_codes = df["Commissioner/Provider Code"].unique()
    all_categories = list(codelists.keys())
    base_grid = pd.MultiIndex.from_product(
        [all_codes, all_categories], names=["Commissioner/Provider Code", "Category"]
    ).to_frame(index=False)

    # === Function to aggregate by category ===
    def aggregate_category(df, bnf_prefixes, label):
        filtered = df[df["BNF Code"].str.startswith(tuple(bnf_prefixes), na=False)]
        agg = filtered.groupby("Commissioner/Provider Code").agg({
            "Items": "sum",
            "Quantity X Items": "sum",
            "Estimated Drug Cost GBP": "sum"
        }).reset_index()
        agg["Category"] = label
        return agg

    # === Aggregate each category ===
    results = []
    for category, prefixes in codelists.items():
        results.append(aggregate_category(df, prefixes, category))

    combined = pd.concat(results, ignore_index=True)

    # === Fill in missing combinations with zeros ===
    complete = base_grid.merge(combined, on=["Commissioner/Provider Code", "Category"], how="left")
    complete.fillna({"Items": 0, "Quantity X Items": 0, "Estimated Drug Cost GBP": 0}, inplace=True)

    # === Format output for display ===
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
