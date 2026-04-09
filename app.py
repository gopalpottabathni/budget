import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Sreenidhi University Budget Portal", layout="wide")

def clean_currency(val):
    """Handles everything from 'Rs. 50,000' to '1.5 Lakhs' to empty cells."""
    if pd.isna(val) or str(val).strip() == "": return 0.0
    s = str(val).lower().replace('rs.', '').replace('lakhs', '').replace('lakh', '').replace(',', '').strip()
    try:
        return float(s)
    except:
        return 0.0

def process_file(file):
    try:
        df_raw = pd.read_csv(file, encoding='ISO-8859-1', header=None)
    except:
        df_raw = pd.read_csv(file, encoding='cp1252', header=None)
    
    content = df_raw.to_string().lower()
    # Extract clean department name
    dept_name = file.name.split('.')[0].replace('Budget', '').replace('Dept', '').strip()

    # --- SUMMARY VIEW DETECTION (Quarterly) ---
    if "apr.-jun." in content or "quarter-1" in content:
        start_row = 0
        for i, row in df_raw.iterrows():
            if any(k in str(row[0]).lower() for k in ["s.n.", "particulars"]):
                start_row = i + 1
                break
        
        df = df_raw.iloc[start_row:].copy()
        # Dynamically drop empty columns to avoid length mismatch
        df = df.dropna(axis=1, how='all')
        
        # We need exactly 5 numeric columns for Q1, Q2, Q3, Q4, and Total
        # Usually these are the last few columns. We map them safely:
        df.columns = [f"Col_{i}" for i in range(len(df.columns))]
        
        # Rename the ones we know based on typical summary layout
        # (SN, Head, Type, Sub, Q1, Q2, Q3, Q4, Total...)
        mapping = {df.columns[1]: 'Head', df.columns[2]: 'Type', df.columns[-3]: 'Total'}
        df = df.rename(columns=mapping)
        
        df['Head'] = df['Head'].ffill().fillna('General')
        df['Type'] = df['Type'].ffill()
        df['Total'] = df['Total'].apply(clean_currency)
        
        df = df[df['Total'] > 0]
        df['File_Type'] = 'Summary'

    # --- DETAILED VIEW DETECTION (Itemized) ---
    else:
        start_row = 0
        for i, row in df_raw.iterrows():
            if any(k in str(row).lower() for k in ["unit price", "amount", "justification"]):
                start_row = i + 1
                break
        
        df = df_raw.iloc[start_row:].copy()
        df = df.dropna(axis=1, how='all')
        
        # Map columns by position: Head(1), Type(2), Sub(3), Item(4), Amount(Last or 2nd last)
        df.columns = [f"Col_{i}" for i in range(len(df.columns))]
        mapping = {df.columns[0]: 'Head', df.columns[1]: 'Type', df.columns[2]: 'Sub', 
                   df.columns[3]: 'Item', df.columns[-2]: 'Amount'}
        df = df.rename(columns=mapping)
        
        df['Head'] = df['Head'].ffill().fillna('General')
        df['Type'] = df['Type'].ffill()
        df['Amount'] = df['Amount'].apply(clean_currency)
        
        df = df[df['Amount'] > 0]
        df['File_Type'] = 'Detailed'

    df['Department'] = dept_name
    return df

# --- APP UI ---
st.title("🏛️ Sreenidhi Budget Intelligence Center")
st.markdown("Analyze department-specific details and overall university allocations.")

uploaded_files = st.file_uploader("Upload Department CSVs", type="csv", accept_multiple_files=True)

if uploaded_files:
    all_dfs = []
    for f in uploaded_files:
        try:
            all_dfs.append(process_file(f))
        except Exception as e:
            st.error(f"Error in {f.name}: {e}")

    if all_dfs:
        combined_df = pd.concat(all_dfs, ignore_index=True)
        
        # Filter Sidebar
        depts = sorted(combined_df['Department'].unique())
        selected_depts = st.sidebar.multiselect("Select Departments", depts, default=depts)
        final_df = combined_df[combined_df['Department'].isin(selected_depts)]

        tab1, tab2 = st.tabs(["📊 Executive View", "🔍 Itemized Breakdown"])

        with tab1:
            summaries = final_df[final_df['File_Type'] == 'Summary']
            if not summaries.empty:
                st.subheader("Total Budget by Department (Lakhs)")
                fig_bar = px.bar(summaries.groupby('Department')['Total'].sum().reset_index(), 
                                 x='Total', y='Department', orientation='h', color='Total',
                                 color_continuous_scale='Blues')
                st.plotly_chart(fig_bar, use_container_width=True)
            else:
                st.info("Upload 'Proposed Budget' files to see summaries.")

        with tab2:
            details = final_df[final_df['File_Type'] == 'Detailed']
            if not details.empty:
                st.subheader("Detailed Spending Map (Hierarchy)")
                # Treemap to visualize where the money goes
                fig_tree = px.treemap(details, path=['Department', 'Head', 'Item'], values='Amount',
                                      color='Amount', color_continuous_scale='YlOrRd')
                st.plotly_chart(fig_tree, use_container_width=True)
                
                st.subheader("Major Purchases / Expenses")
                st.dataframe(details[['Department', 'Item', 'Amount', 'Head']].sort_values(by='Amount', ascending=False))
            else:
                st.info("Upload 'Detailed Budget' files to see specific items.")
else:
    st.info("Please upload your departmental CSV files to begin.")
