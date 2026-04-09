import streamlit as st
import pandas as pd
import plotly.express as px

# Set Page Config
st.set_page_config(page_title="Sreenidhi University Budget Portal", layout="wide")

def load_and_clean_data(file_path):
    # 1. Load the file with flexible encoding
    try:
        df = pd.read_csv(file_path, skiprows=3, encoding='ISO-8859-1', low_memory=False)
    except:
        df = pd.read_csv(file_path, skiprows=3, encoding='cp1252', low_memory=False)
    
    # 2. Slice to the core 11 columns (SN, Dept, Type, Sub, Q1, Q2, Q3, Q4, Total, Actual, Remark)
    df = df.iloc[:, :11]
    cols = ['SN', 'Department', 'Type', 'Subcategory', 'Q1', 'Q2', 'Q3', 'Q4', 'Total', 'Actual_Prev', 'Remark']
    df.columns = cols

    # 3. Clean strings and handle the "Merged Cell" problem
    # Remove rows that are completely empty
    df = df.dropna(subset=['Department', 'Type', 'Q1', 'Q2', 'Q3', 'Q4', 'Total'], how='all')
    
    # Fill down Department and SN so every row knows which dept it belongs to
    df['Department'] = df['Department'].ffill()
    df['Type'] = df['Type'].ffill()

    # 4. Clean Numeric Data (Crucial for Quarter-wise view)
    num_cols = ['Q1', 'Q2', 'Q3', 'Q4', 'Total']
    for col in num_cols:
        # Convert to string to handle replacement, then to numeric
        df[col] = df[col].astype(str).str.replace(',', '').str.replace('₹', '').str.strip()
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

    # 5. Filter out junk rows (like headers repeating or empty totals)
    # We keep rows where at least one quarter has a value > 0
    df = df[(df['Q1'] > 0) | (df['Q2'] > 0) | (df['Q3'] > 0) | (df['Q4'] > 0) | (df['Total'] > 0)]
    
    # Remove specific "Total" or header-like rows that aren't real data
    df = df[~df['Department'].str.contains('SREENIDHI|University|Total|S.N.', case=False, na=False)]
    
    return df

# --- APP INTERFACE ---
st.title("🏛️ Sreenidhi University Budget Analytics")
st.markdown("### Financial Year 2026-27 | Comprehensive Departmental View")

try:
    df = load_and_clean_data('data.csv')

    # Sidebar Navigation
    st.sidebar.header("Navigation Controls")
    view_type = st.sidebar.radio("Select View", ["Executive Summary", "Department Deep-Dive"])
    
    all_depts = sorted(df['Department'].unique())
    selected_depts = st.sidebar.multiselect("Filter Departments", all_depts, default=all_depts)
    
    # Apply Filter
    filtered_df = df[df['Department'].isin(selected_depts)]

    if view_type == "Executive Summary":
        # TOP KPI METRICS
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Total Budget", f"₹{filtered_df['Total'].sum():,.2f} L")
        m2.metric("Q1 Projected", f"₹{filtered_df['Q1'].sum():,.2f} L")
        m3.metric("Q2 Projected", f"₹{filtered_df['Q2'].sum():,.2f} L")
        m4.metric("Departments", len(selected_depts))

        # CHART: Department wise total
        st.subheader("Total Budget Distribution by Department")
        dept_chart_data = filtered_df.groupby('Department')['Total'].sum().sort_values(ascending=True).reset_index()
        fig_dept = px.bar(dept_chart_data, x='Total', y='Department', orientation='h', 
                          color='Total', color_continuous_scale='Viridis', height=600)
        st.plotly_chart(fig_dept, use_container_width=True)

    else:
        # DEPARTMENT DEEP-DIVE (Shows Quarter wise breakdown)
        st.subheader("Quarter-wise Analysis by Section")
        for dept in selected_depts:
            with st.expander(f"📂 {dept} Detail Breakdown"):
                dept_data = filtered_df[filtered_df['Department'] == dept]
                
                # Show a mini chart for this department's quarters
                q_summary = dept_data[['Q1', 'Q2', 'Q3', 'Q4']].sum().reset_index()
                q_summary.columns = ['Quarter', 'Lakhs']
                fig_q = px.line(q_summary, x='Quarter', y='Lakhs', markers=True, title=f"{dept} Spending Timeline")
                st.plotly_chart(fig_q, use_container_width=True)
                
                # Show the raw table for this department
                st.table(dept_data[['Type', 'Subcategory', 'Q1', 'Q2', 'Q3', 'Q4', 'Total']])

    # DOWNLOAD DATA
    st.sidebar.markdown("---")
    csv = filtered_df.to_csv(index=False).encode('utf-8')
    st.sidebar.download_button("📥 Download Cleaned Data", data=csv, file_name="cleaned_budget.csv", mime="text/csv")

except Exception as e:
    st.error(f"Error processing data: {e}")
    st.info("Ensure your file on GitHub is named 'data.csv' and is the Summary sheet format.")
