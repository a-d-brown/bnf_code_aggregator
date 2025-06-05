import pandas as pd
import streamlit as st

st.title("BNF Code Aggregator")

uploaded_file = st.file_uploader("Upload CSV", type="csv")

if uploaded_file:
    df = pd.read_csv(uploaded_file)

    # Define Commissioner/Provider Codes of interest
    included_codes = [
        "84H00", "00P00", "00L00", "01H00",
        "13T00", "16C00", "99C00", "00N00"
    ]

    # Apply provider filter once
    df = df[df['Commissioner/Provider Code'].isin(included_codes)]

    # Define BNF codelist dictionary
    codelists = {
        "Antibacterials": ["0501"],
        "SABAs": ["0301011R0", "0301011V0"],
        "Riluzole": ["0409030R0"],
        "Opioids": ["040702"],
        "Gabapentinoids": ["0408010AE", "0408010G0"]
    }

    # Aggregation helper
    def aggregate_category(df, bnf_prefixes, category_label):
        filtered = df[df['BNF Code'].str.startswith(tuple(bnf_prefixes), na=False)]
        aggregated = filtered.groupby(['Commissioner/Provider Code']).agg({
            'Items': 'sum',
            'Quantity X Items': 'sum',
            'Estimated Drug Cost GBP': 'sum'
        }).reset_index()
        aggregated['Category'] = category_label
        return aggregated

    # Aggregate each category
    category_frames = [
        aggregate_category(df, prefixes, category)
        for category, prefixes in codelists.items()
    ]
    combined = pd.concat(category_frames, ignore_index=True)

    # Create full grid of all Commissioner × Category combinations
    commissioner_codes = df['Commissioner/Provider Code'].unique()
    categories = list(codelists.keys())
    full_index = pd.MultiIndex.from_product(
        [commissioner_codes, categories],
        names=['Commissioner/Provider Code', 'Category']
    ).to_frame(index=False)

    # Merge and fill zeros
    complete = full_index.merge(
        combined,
        on=['Commissioner/Provider Code', 'Category'],
        how='left'
    )
    complete[['Items', 'Quantity X Items', 'Estimated Drug Cost GBP']] = complete[
        ['Items', 'Quantity X Items', 'Estimated Drug Cost GBP']
    ].fillna(0)

    ### FORMATTING ---
    # Copy and format display columns
    formatted = complete.copy()

    # Format integer-based columns
    formatted['Items'] = formatted['Items'].apply(lambda x: f"{int(x):,}")
    formatted['Quantity X Items'] = formatted['Quantity X Items'].apply(lambda x: f"{int(x):,}")

    # Format cost column with £ and commas
    formatted['Estimated Drug Cost GBP'] = formatted['Estimated Drug Cost GBP'].apply(
        lambda x: f"£{x:,.2f}"
    )

    # Display and download
    st.subheader("Output")
    st.dataframe(formatted)



    st.download_button(
        "Download CSV",
        formatted.to_csv(index=False),
        file_name="aggregated_output.csv",
        mime="text/csv"
    )
