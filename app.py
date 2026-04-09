import streamlit as st
import pandas as pd
import plotly.express as px

# Set Page Config
st.set_page_config(page_title="University Budget Analytics 2026-27", layout="wide")

# --- DATA CLEANING FUNCTION ---
def load_and_clean_data(file_path):
    # Based on the uploaded CSV structure
    df = pd.read_csv(file_path, skiprows=3)
    cols = ['SN', 'Department', 'Type', 'Subcategory', 'Q1', 'Q2', 'Q3', 'Q4', 'Total', 'Actual_Prev', 'Remark']
    df.columns = cols
    
    # Clean and forward-fill names
    df['Department'] = df['Department'].ffill()
    df['Type'] = df['Type'].ffill()
    
    # Convert numeric columns
    for col in ['Q1', 'Q2', 'Q3', 'Q4', 'Total']:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    
    # Filter out rows that aren't actual budget entries
    df = df[df['Total'] > 0]
    return df

# --- APP LAYOUT ---
st.title("📊 University Budget Analytics 2026-27")
st.markdown("Dashboard for analyzing departmental allocations and quarterly spending.")

# Load Data (Assuming the file is in the same directory)
try:
    df = load_and_clean_data('data.csv')
    
    # Sidebar Filters
    st.sidebar.header("Filters")
    dept_filter = st.sidebar.multiselect("Select Department", options=df['Department'].unique(), default=df['Department'].unique())
    type_filter = st.sidebar.multiselect("Select Budget Type", options=df['Type'].unique(), default=df['Type'].unique())

    # Apply Filters
    filtered_df = df[(df['Department'].isin(dept_filter)) & (df['Type'].isin(type_filter))]

    # --- TOP METRICS ---
    m1, m2, m3 = st.columns(3)
    total_budget = filtered_df['Total'].sum()
    recurring = filtered_df[filtered_df['Type'] == 'Recurring']['Total'].sum()
    non_recurring = filtered_df[filtered_df['Type'] == 'Non-Recurring']['Total'].sum()

    m1.metric("Total Proposed Budget", f"₹{total_budget:,.2f} Lakhs")
    m2.metric("Total Recurring", f"₹{recurring:,.2f} Lakhs")
    m3.metric("Total Non-Recurring", f"₹{non_recurring:,.2f} Lakhs")

    # --- VISUALIZATIONS ---
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Budget by Department")
        dept_sum = filtered_df.groupby('Department')['Total'].sum().sort_values(ascending=False).reset_index()
        fig_dept = px.bar(dept_sum, x='Total', y='Department', orientation='h', 
                          title="Departmental Allocation", color='Total', color_continuous_scale='Viridis')
        st.plotly_chart(fig_dept, use_container_width=True)

    with col2:
        st.subheader("Recurring vs Non-Recurring")
        fig_pie = px.pie(filtered_df, values='Total', names='Type', 
                         title="Expenditure Distribution", hole=0.4, color_discrete_sequence=px.colors.qualitative.Pastel)
        st.plotly_chart(fig_pie, use_container_width=True)

    # --- QUARTERLY ANALYSIS ---
    st.subheader("Quarterly Spending Projection")
    q_data = filtered_df[['Q1', 'Q2', 'Q3', 'Q4']].sum().reset_index()
    q_data.columns = ['Quarter', 'Amount']
    fig_q = px.line(q_data, x='Quarter', y='Amount', markers=True, title="Cash Flow Projection by Quarter")
    st.plotly_chart(fig_q, use_container_width=True)

    # --- DATA TABLE ---
    st.subheader("Detailed Budget Items")
    st.dataframe(filtered_df[['Department', 'Type', 'Subcategory', 'Total']], use_container_width=True)

except Exception as e:
    st.error(f"Error loading data: {e}")
    st.info("Please ensure the data file is in the same folder as app.py")
