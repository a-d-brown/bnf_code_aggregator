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
        "Gabapentinoids": ["0408010AE", "0408010G0"],
        "Triple Inhalers": [
        "0302000W0", "0302000Z0", "0302000AA", "0301011AB", "0302000Y0AAAAAA",
        "0302000Y0BB", "0301020R0AAAAAA", "0301020Q0BDAAAA", "0301020Q0BCAAAD",
        "0301020R0BBAAAA", "0301020S0AAAAAA", "0301020T0BBAAAA", "0301020S0BBAAAA",
        "0301020Q0BBAAAA", "0301020Q0BBABAB", "0301020Q0BBACAC", "0301020Q0BBADAE",
        "0301020Q0BEABAB", "0301020Q0BEAAAA", "0301020Q0AAACAC", "0301020Q0AAADAD",
        "0301020Q0AAAAAA", "0301020Q0AAABAB", "0301020Q0AAAEAE", "0301020T0AAAAAA",
        "0302000N0BGABBF", "0302000N0BGACBG", "0302000N0BGAAAZ", "0302000C0AABYBY",
        "0302000C0AABXBX", "0302000C0AACACA", "0302000C0AABZBZ", "0302000K0AABCBC",
        "0302000K0AAALAL", "0302000K0AAAMAM", "0302000K0AABBBB", "0302000K0AAAUAU",
        "0302000K0BHAAAM", "0302000K0BHABAU", "0302000N0AABFBF", "0302000N0AABJBJ",
        "0302000N0AABPBP", "0302000N0AABGBG", "0302000N0AABKBK", "0302000N0AABLBL",
        "0302000N0AABEBE", "0302000N0AABQBQ", "0302000N0AABRBR", "0302000N0AAAXAX",
        "0302000N0AABSBS", "0302000N0AAAYAY", "0302000N0AAAZAZ", "0302000N0BDAABJ",
        "0302000N0BDABBK", "0302000N0BDACBL", "0302000N0BDADBP", "0302000N0BDAEBQ",
        "0302000C0BQAABX", "0302000C0BQABBZ", "0302000C0BRAABY", "0302000C0BRABCA",
        "0302000V0BBAAAA", "0302000V0BBABAB", "0302000N0BCAAAX", "0302000N0BCAEBF",
        "0302000N0BCABAY", "0302000N0BCAFBG", "0302000N0BCADBE", "0302000N0BCACAZ",
        "0302000N0BFAABF", "0302000N0BFABBG", "0302000K0BDAAAL", "0302000K0BDAEBC",
        "0302000K0BDABAM", "0302000K0BDADBB", "0302000K0BDACAU", "0302000N0BJAABF",
        "0302000N0BJABBG", "0302000X0BBABAB", "0302000X0BBACAC", "0302000X0BBAAAA",
        "0302000N0BPABBF", "0302000N0BPACBG", "0302000N0BPAABE", "0302000C0BWAABX",
        "0302000C0BWABBZ", "0302000N0BLABBF", "0302000N0BLACBG", "0302000N0BLAABE",
        "0302000N0BNACAX", "0302000N0BNABAY", "0302000N0BNAAAZ", "0302000K0BIABAM",
        "0302000K0BIAAAU", "0302000N0BKAAAY", "0302000N0BKABAZ", "0302000K0BKAAAM",
        "0302000K0BKABAU", "0302000C0BUAABX", "0302000C0BUABBZ", "0302000N0BIAABF",
        "0302000N0BIABBG", "0302000N0BIACAY", "0302000N0BIADAZ", "0302000N0BMAAAZ",
        "0302000K0BJAAAM", "0302000K0BJABAU"
        ]
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
