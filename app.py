import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Sreenidhi Budget Intelligence", layout="wide")

def clean_value(val):
    """Cleans currency strings like 'Rs. 1.1 lakhs' or '1,00,000' into floats."""
    if pd.isna(val) or str(val).strip() == "": return 0.0
    s = str(val).lower().replace('rs.', '').replace('lakhs', '').replace('lakh', '').replace(',', '').strip()
    try:
        return float(s)
    except:
        return 0.0

def process_budget_file(file):
    # Read the raw file
    df = pd.read_csv(file, encoding='ISO-8859-1', header=None)
    
    # Identify if it's a SUMMARY file or a DETAILED file
    file_content = df.to_string().lower()
    
    if "apr.-jun." in file_content or "quarter-1" in file_content:
        return "summary", handle_summary(df)
    else:
        return "detailed", handle_detailed(df)

def handle_summary(df):
    # Find the row where data starts (usually after headers)
    # We look for the row containing 'S.N.'
    start_row = 0
    for i, row in df.iterrows():
        if "s.n." in str(row[0]).lower():
            start_row = i + 1
            break
    
    data = df.iloc[start_row:].copy()
    data = data.iloc[:, :11] # Keep core columns
    data.columns = ['SN', 'Head', 'Type', 'Sub', 'Q1', 'Q2', 'Q3', 'Q4', 'Total', 'Actual', 'Remark']
    
    data['Head'] = data['Head'].ffill()
    data['Type'] = data['Type'].ffill()
    
    for col in ['Q1', 'Q2', 'Q3', 'Q4', 'Total']:
        data[col] = data[col].apply(clean_value)
    
    return data[data['Total'] > 0]

def handle_detailed(df):
    # Detailed files usually have Amount in the 7th or 8th column
    start_row = 0
    for i, row in df.iterrows():
        if "budget head" in str(row[1]).lower() or "particulars" in str(row[1]).lower():
            start_row = i + 1
            break
            
    data = df.iloc[start_row:].copy()
    # Standardize columns for detailed view
    data = data.iloc[:, [1, 2, 3, 4, 6, 7]] 
    data.columns = ['Head', 'Type', 'Sub', 'Description', 'UnitPrice', 'Amount']
    
    data['Head'] = data['Head'].ffill()
    data['Type'] = data['Type'].ffill()
    data['Amount'] = data['Amount'].apply(clean_value)
    
    return data[data['Amount'] > 0]

# --- UI ---
st.title("🏛️ Sreenidhi Departmental Budget Analyzer")
st.info("Upload any Departmental CSV (Detailed or Summary) to analyze it.")

uploaded_file = st.file_uploader("Choose a budget file...", type="csv")

if uploaded_file:
    file_type, cleaned_df = process_budget_file(uploaded_file)
    
    st.success(f"Detected Format: {file_type.upper()} View")
    
    # Sidebar Filters
    heads = cleaned_df['Head'].unique()
    selected_head = st.sidebar.multiselect("Filter by Category", heads, default=heads)
    final_df = cleaned_df[cleaned_df['Head'].isin(selected_head)]

    if file_type == "summary":
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Total Proposed Budget", f"₹{final_df['Total'].sum():,.2f} Lakhs")
            fig = px.pie(final_df, values='Total', names='Head', title="Budget by Category")
            st.plotly_chart(fig)
        with col2:
            q_data = final_df[['Q1', 'Q2', 'Q3', 'Q4']].sum().reset_index()
            q_data.columns = ['Quarter', 'Lakhs']
            fig2 = px.bar(q_data, x='Quarter', y='Lakhs', title="Quarterly Cash Flow")
            st.plotly_chart(fig2)
            
    else: # Detailed view
        st.metric("Total Expenditure", f"₹{final_df['Amount'].sum():,.2f} Lakhs")
        fig = px.treemap(final_df, path=['Head', 'Type', 'Sub'], values='Amount', title="Expenditure Breakdown")
        st.plotly_chart(fig, use_container_width=True)
        
        st.subheader("Top Expense Items")
        st.table(final_df.sort_values(by='Amount', ascending=False).head(10))

    st.subheader("Raw Processed Data")
    st.dataframe(final_df)
