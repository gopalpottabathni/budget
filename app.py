import streamlit as st
import pandas as pd
import plotly.express as px

# Set Page Config
st.set_page_config(page_title="University Budget Analytics 2026-27", layout="wide")

# --- DATA CLEANING FUNCTION ---
def load_and_clean_data(file_path):
    try:
        # Load the file - using low_memory=False to handle mixed types
        df = pd.read_csv(file_path, skiprows=3, encoding='ISO-8859-1', low_memory=False)
    except Exception:
        df = pd.read_csv(file_path, skiprows=3, encoding='cp1252', low_memory=False)
    
    # FIX: The summary CSV has ~33 columns. We only want the first 11 meaningful ones.
    # We slice the first 11 columns to match our names list.
    df = df.iloc[:, :11]
    
    cols = ['SN', 'Department', 'Type', 'Subcategory', 'Q1', 'Q2', 'Q3', 'Q4', 'Total', 'Actual_Prev', 'Remark']
    df.columns = cols
    
    # Clean and forward-fill names
    df['Department'] = df['Department'].ffill()
    df['Type'] = df['Type'].ffill()
    
    # Convert numeric columns
    for col in ['Q1', 'Q2', 'Q3', 'Q4', 'Total']:
        if df[col].dtype == 'object':
            df[col] = df[col].str.replace(',', '').str.replace('₹', '').str.strip()
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    
    # Filter out total rows or empty rows
    df = df[df['Total'] > 0]
    # Remove rows where Department is 'Total' (the grand total row)
    df = df[~df['Department'].str.contains('Total', case=False, na=False)]
    
    return df

# --- APP LAYOUT ---
st.title("📊 University Budget Analytics 2026-27")
st.markdown("Dashboard for analyzing departmental allocations and quarterly spending.")

try:
    df = load_and_clean_data('data.csv')
    
    # Sidebar Filters
    st.sidebar.header("Data Filters")
    dept_list = sorted(df['Department'].unique())
    dept_filter = st.sidebar.multiselect("Select Department", options=dept_list, default=dept_list)
    
    type_list = df['Type'].unique()
    type_filter = st.sidebar.multiselect("Select Budget Type", options=type_list, default=type_list)

    # Apply Filters
    filtered_df = df[(df['Department'].isin(dept_filter)) & (df['Type'].isin(type_filter))]

    # --- TOP METRICS ---
    m1, m2, m3 = st.columns(3)
    total_budget = filtered_df['Total'].sum()
    
    # Logic to separate Recurring vs Non-Recurring based on text
    rec_mask = filtered_df['Type'].str.contains('Recurring', case=False, na=False) & ~filtered_df['Type'].str.contains('Non', case=False, na=False)
    non_rec_mask = filtered_df['Type'].str.contains('Non-Recurring', case=False, na=False)
    
    recurring = filtered_df[rec_mask]['Total'].sum()
    non_recurring = filtered_df[non_rec_mask]['Total'].sum()

    m1.metric("Total Proposed Budget", f"₹{total_budget:,.2f} Lakhs")
    m2.metric("Total Recurring", f"₹{recurring:,.2f} Lakhs")
    m3.metric("Total Non-Recurring", f"₹{non_recurring:,.2f} Lakhs")

    # --- VISUALIZATIONS ---
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Budget by Department")
        dept_sum = filtered_df.groupby('Department')['Total'].sum().sort_values(ascending=True).reset_index()
        fig_dept = px.bar(dept_sum, x='Total', y='Department', orientation='h', 
                          color='Total', color_continuous_scale='Reds')
        st.plotly_chart(fig_dept, use_container_width=True)

    with col2:
        st.subheader("Quarterly Allocation")
        q_totals = filtered_df[['Q1', 'Q2', 'Q3', 'Q4']].sum().reset_index()
        q_totals.columns = ['Quarter', 'Lakhs']
        fig_pie = px.pie(q_totals, values='Lakhs', names='Quarter', hole=0.4)
        st.plotly_chart(fig_pie, use_container_width=True)

    # --- QUARTERLY TIMELINE ---
    st.subheader("Cash Flow Projection")
    fig_line = px.line(q_totals, x='Quarter', y='Lakhs', markers=True, text='Lakhs')
    fig_line.update_traces(textposition="top center")
    st.plotly_chart(fig_line, use_container_width=True)

    # --- DATA TABLE ---
    st.subheader("Detailed Items View")
    st.dataframe(filtered_df[['Department', 'Type', 'Subcategory', 'Total', 'Remark']], use_container_width=True)

except Exception as e:
    st.error(f"Error loading data: {e}")
