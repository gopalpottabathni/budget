import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Sreenidhi University Budget Center", layout="wide")

def clean_currency(val):
    if pd.isna(val) or str(val).strip() == "": return 0.0
    # Removes text like 'Rs.', 'Lakhs', commas, and hidden spaces
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
    # Extract department name from the filename
    dept_name = file.name.split('.')[0].replace('Budget', '').replace('Dept', '').strip()

    if "apr.-jun." in content or "quarter-1" in content:
        # --- SUMMARY FILE PROCESSING ---
        start_row = 0
        for i, row in df_raw.iterrows():
            if "s.n." in str(row[0]).lower() or "particulars" in str(row[0]).lower():
                start_row = i + 1
                break
        
        # Library and some others have data in different column offsets
        df = df_raw.iloc[start_row:].copy()
        
        # Standardize to 11 columns; find the columns containing 'Total'
        df = df.dropna(axis=1, how='all').iloc[:, :11]
        df.columns = ['SN', 'Head', 'Type', 'Sub', 'Q1', 'Q2', 'Q3', 'Q4', 'Total', 'Actual', 'Remark']
        
        df['Head'] = df['Head'].ffill().fillna('General')
        df['Type'] = df['Type'].ffill().fillna('Uncategorized')
        
        for col in ['Q1', 'Q2', 'Q3', 'Q4', 'Total']:
            df[col] = df[col].apply(clean_currency)
        
        df = df[df['Total'] > 0]
        df['File_Type'] = 'Summary'
    else:
        # --- DETAILED FILE PROCESSING ---
        start_row = 0
        for i, row in df_raw.iterrows():
            if any(k in str(row).lower() for k in ["specifications", "unit price", "amount"]):
                start_row = i + 1
                break
        
        # Identify columns for Detailed view (Head, Type, Sub, Item, Amount)
        df = df_raw.iloc[start_row:].copy()
        df = df.dropna(axis=1, how='all').iloc[:, [0, 1, 2, 3, 6]]
        df.columns = ['Head', 'Type', 'Sub', 'Item', 'Amount']
        
        df['Head'] = df['Head'].ffill().fillna('General')
        df['Type'] = df['Type'].ffill().fillna('Uncategorized')
        df['Amount'] = df['Amount'].apply(clean_currency)
        df = df[df['Amount'] > 0]
        df['File_Type'] = 'Detailed'

    df['Department'] = dept_name
    return df

# --- UI ---
st.title("🏛️ Sreenidhi University Budget Intelligence")
st.markdown("Upload your departmental CSVs to analyze allocations and spending.")

uploaded_files = st.file_uploader("Upload Department Budget CSVs", type="csv", accept_multiple_files=True)

if uploaded_files:
    all_data = []
    for f in uploaded_files:
        try:
            all_data.append(process_file(f))
        except Exception as e:
            st.error(f"Could not read {f.name}: {e}")

    if all_data:
        summaries = [d for d in all_data if d['File_Type'].iloc[0] == 'Summary']
        details = [d for d in all_data if d['File_Type'].iloc[0] == 'Detailed']

        tab1, tab2 = st.tabs(["📊 Executive View", "🔍 Itemized Details"])

        with tab1:
            if summaries:
                sum_df = pd.concat(summaries)
                depts = sorted(sum_df['Department'].unique())
                sel_depts = st.multiselect("Filter Departments", depts, default=depts, key="sum_filter")
                
                # FIXED: Corrected the variable name here
                filtered_sum = sum_df[sum_df['Department'].isin(sel_depts)]

                if not filtered_sum.empty:
                    c1, c2, c3 = st.columns(3)
                    c1.metric("Total Budget", f"₹{filtered_sum['Total'].sum():,.2f} L")
                    c2.metric("Departments", len(sel_depts))
                    c3.metric("Q1 Total", f"₹{filtered_sum['Q1'].sum():,.2f} L")

                    st.subheader("Budget Allocation by Department")
                    fig_bar = px.bar(filtered_sum.groupby('Department')['Total'].sum().reset_index(), 
                                     x='Total', y='Department', orientation='h', color='Total',
                                     color_continuous_scale='Viridis')
                    st.plotly_chart(fig_bar, use_container_width=True)
                else:
                    st.warning("No data found for selected departments.")
            else:
                st.info("Upload 'Proposed Budget' files to see the Executive Summary.")

        with tab2:
            if details:
                det_df = pd.concat(details)
                depts_det = sorted(det_df['Department'].unique())
                sel_depts_det = st.multiselect("Filter Departments", depts_det, default=depts_det, key="det_filter")
                filtered_det = det_df[det_df['Department'].isin(sel_depts_det)].copy()

                if not filtered_det.empty:
                    # Fix Treemap Hierarchy
                    filtered_det['H1'] = "Dept: " + filtered_det['Department']
                    filtered_det['H2'] = "Cat: " + filtered_det['Head']
                    
                    st.subheader("Expenditure Breakdown")
                    fig_tree = px.treemap(filtered_det, path=['H1', 'H2', 'Item'], values='Amount',
                                          color='Amount', color_continuous_scale='RdBu')
                    st.plotly_chart(fig_tree, use_container_width=True)
