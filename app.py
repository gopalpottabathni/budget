import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Sreenidhi University Budget Center", layout="wide")

def clean_currency(val):
    """Deep cleans currency, handling 'Lakhs', 'Rs.', commas, and empty cells."""
    if pd.isna(val) or str(val).strip() == "": return 0.0
    s = str(val).lower().replace('rs.', '').replace('lakhs', '').replace('lakh', '').replace(',', '').replace('~', '').strip()
    try:
        return float(s)
    except:
        return 0.0

def process_file(file):
    """Detects file type and returns a cleaned dataframe with a 'Dept_Source' column."""
    try:
        df_raw = pd.read_csv(file, encoding='ISO-8859-1', header=None)
    except:
        df_raw = pd.read_csv(file, encoding='cp1252', header=None)
    
    content = df_raw.to_string().lower()
    dept_name = file.name.split('.')[0].split('-')[0].replace('Budget', '').strip()

    # --- DETECTION LOGIC ---
    if "apr.-jun." in content or "quarter-1" in content:
        # It's a Summary (Quarterly) File
        start_row = 0
        for i, row in df_raw.iterrows():
            if "s.n." in str(row[0]).lower():
                start_row = i + 1
                break
        df = df_raw.iloc[start_row:, :11].copy()
        df.columns = ['SN', 'Head', 'Type', 'Sub', 'Q1', 'Q2', 'Q3', 'Q4', 'Total', 'Actual', 'Remark']
        df['Head'] = df['Head'].ffill().fillna('General')
        df['Type'] = df['Type'].ffill().fillna('Uncategorized')
        for col in ['Q1', 'Q2', 'Q3', 'Q4', 'Total']:
            df[col] = df[col].apply(clean_currency)
        df = df[df['Total'] > 0]
        df['File_Type'] = 'Summary'
    else:
        # It's a Detailed (Itemized) File
        start_row = 0
        for i, row in df_raw.iterrows():
            if any(k in str(row[1]).lower() for k in ["budget head", "particulars"]):
                start_row = i + 1
                break
        df = df_raw.iloc[start_row:, [1, 2, 3, 4, 7]].copy()
        df.columns = ['Head', 'Type', 'Sub', 'Item', 'Amount']
        df['Head'] = df['Head'].ffill().fillna('General')
        df['Type'] = df['Type'].ffill().fillna('Uncategorized')
        df['Sub'] = df['Sub'].fillna('General')
        df['Amount'] = df['Amount'].apply(clean_currency)
        df = df[df['Amount'] > 0]
        df['File_Type'] = 'Detailed'

    df['Department'] = dept_name
    return df

# --- UI START ---
st.title("🏛️ Sreenidhi University Budget Intelligence")
st.markdown("Upload all department CSVs (Detailed or Summary) to see the full picture.")

uploaded_files = st.file_uploader("Upload Department Budget CSVs", type="csv", accept_multiple_files=True)

if uploaded_files:
    all_data = [process_file(f) for f in uploaded_files]
    
    # Split data into Summaries and Detailed lists
    summaries = [d for d in all_data if d['File_Type'].iloc[0] == 'Summary']
    details = [d for d in all_data if d['File_Type'].iloc[0] == 'Detailed']

    tab1, tab2 = st.tabs(["📊 Executive View (Summaries)", "🔍 Itemized View (Details)"])

    with tab1:
        if summaries:
            sum_df = pd.concat(summaries)
            depts = sum_df['Department'].unique()
            sel_depts = st.multiselect("Filter Departments", depts, default=depts)
            filtered_sum = sum_
