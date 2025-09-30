import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import numpy as np
from excel_reader import CashFlowReader, get_excel_sheets, smart_column_mapping, prepare_data_with_mapping

# Page configuration
st.set_page_config(
    page_title="Cash Flow Dashboard",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
    .insight-box {
        background-color: #e8f4fd;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

def main():
    st.markdown('<h1 class="main-header">💰 Cash Flow Dashboard</h1>', unsafe_allow_html=True)
    
    # Sidebar
    st.sidebar.title("📊 Dashboard Controls")
    
    # File upload
    uploaded_file = st.sidebar.file_uploader(
        "Upload Excel File",
        type=['xlsx', 'xls'],
        help="Upload an Excel file containing your cash flow data. The app will intelligently detect columns and allow you to map them correctly."
    )
    
    if uploaded_file is not None:
        # Process the uploaded file with intelligent detection
        data, column_mapping = process_uploaded_file(uploaded_file)
        
        if data is not None:
            # Initialize reader with processed data
            reader = CashFlowReader("temp_cashflow.xlsx")
            reader.data = data
            
            # Display dashboard
            display_dashboard(reader, data)
        else:
            st.error("Failed to process the uploaded file. Please check your data format and try again.")
    
    else:
        # Show instructions when no file is uploaded
        show_instructions()

def display_dashboard(reader, data):
    """Display the main dashboard"""
    
    # Get insights
    insights = reader.get_insights()
    project_summary = reader.get_project_summary()
    monthly_summary = reader.get_monthly_summary()
    
    # Key Metrics Row
    st.subheader("📈 Key Metrics")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="Total Cash In",
            value=f"${insights.get('total_cash_in', 0):,.2f}",
            delta=None
        )
    
    with col2:
        st.metric(
            label="Total Cash Out",
            value=f"${insights.get('total_cash_out', 0):,.2f}",
            delta=None
        )
    
    with col3:
        net_flow = insights.get('total_net_cash_flow', 0)
        st.metric(
            label="Net Cash Flow",
            value=f"${net_flow:,.2f}",
            delta=f"{'Positive' if net_flow > 0 else 'Negative'}"
        )
    
    with col4:
        st.metric(
            label="Total Projects",
            value=insights.get('total_projects', 0),
            delta=None
        )
    
    # Charts Row
    st.subheader("📊 Visualizations")
    
    # Create tabs for different views
    tab1, tab2, tab3, tab4 = st.tabs(["Cash Flow Over Time", "Project Analysis", "Monthly Trends", "Raw Data"])
    
    with tab1:
        # Cash flow over time
        if 'Cumulative_Cash_Flow' in data.columns:
            fig = px.line(
                data, 
                x='Date', 
                y='Cumulative_Cash_Flow',
                title='Cumulative Cash Flow Over Time',
                color='Project'
            )
            fig.update_layout(height=500)
            st.plotly_chart(fig, use_container_width=True)
        
        # Net cash flow by month
        if monthly_summary is not None:
            fig2 = px.bar(
                monthly_summary,
                x='Year_Month',
                y='Net_Cash_Flow',
                title='Monthly Net Cash Flow',
                color='Net_Cash_Flow',
                color_continuous_scale=['red', 'yellow', 'green']
            )
            fig2.update_layout(height=400)
            st.plotly_chart(fig2, use_container_width=True)
    
    with tab2:
        # Project analysis
        if project_summary is not None:
            col1, col2 = st.columns(2)
            
            with col1:
                # Project profitability
                fig3 = px.bar(
                    project_summary,
                    x='Project',
                    y='Total_Net_Cash_Flow',
                    title='Project Profitability',
                    color='Total_Net_Cash_Flow',
                    color_continuous_scale=['red', 'yellow', 'green']
                )
                fig3.update_layout(height=400)
                st.plotly_chart(fig3, use_container_width=True)
            
            with col2:
                # Cash in vs Cash out by project
                fig4 = go.Figure()
                fig4.add_trace(go.Bar(
                    name='Cash In',
                    x=project_summary['Project'],
                    y=project_summary['Total_Cash_In'],
                    marker_color='green'
                ))
                fig4.add_trace(go.Bar(
                    name='Cash Out',
                    x=project_summary['Project'],
                    y=project_summary['Total_Cash_Out'],
                    marker_color='red'
                ))
                fig4.update_layout(
                    title='Cash In vs Cash Out by Project',
                    barmode='group',
                    height=400
                )
                st.plotly_chart(fig4, use_container_width=True)
            
            # Project summary table
            st.subheader("Project Summary Table")
            st.dataframe(project_summary, use_container_width=True)
    
    with tab3:
        # Monthly trends
        if monthly_summary is not None:
            col1, col2 = st.columns(2)
            
            with col1:
                # Monthly cash in/out
                fig5 = go.Figure()
                fig5.add_trace(go.Scatter(
                    x=monthly_summary['Year_Month'],
                    y=monthly_summary['Cash_In'],
                    mode='lines+markers',
                    name='Cash In',
                    line=dict(color='green')
                ))
                fig5.add_trace(go.Scatter(
                    x=monthly_summary['Year_Month'],
                    y=monthly_summary['Cash_Out'],
                    mode='lines+markers',
                    name='Cash Out',
                    line=dict(color='red')
                ))
                fig5.update_layout(
                    title='Monthly Cash In vs Cash Out Trends',
                    height=400
                )
                st.plotly_chart(fig5, use_container_width=True)
            
            with col2:
                # Monthly net cash flow pie chart (positive vs negative months)
                positive_months = len(monthly_summary[monthly_summary['Net_Cash_Flow'] > 0])
                negative_months = len(monthly_summary[monthly_summary['Net_Cash_Flow'] < 0])
                
                fig6 = px.pie(
                    values=[positive_months, negative_months],
                    names=['Positive Months', 'Negative Months'],
                    title='Positive vs Negative Cash Flow Months',
                    color_discrete_sequence=['green', 'red']
                )
                fig6.update_layout(height=400)
                st.plotly_chart(fig6, use_container_width=True)
            
            # Monthly summary table
            st.subheader("Monthly Summary Table")
            st.dataframe(monthly_summary, use_container_width=True)
    
    with tab4:
        # Raw data
        st.subheader("Raw Data")
        st.dataframe(data, use_container_width=True)
        
        # Download processed data
        csv = data.to_csv(index=False)
        st.download_button(
            label="Download Processed Data as CSV",
            data=csv,
            file_name="processed_cash_flow_data.csv",
            mime="text/csv"
        )
    
    # Insights section
    st.subheader("🔍 Key Insights")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(f"""
        <div class="insight-box">
        <h4>📊 Financial Overview</h4>
        <ul>
        <li><strong>Most Profitable Project:</strong> {insights.get('most_profitable_project', 'N/A')}</li>
        <li><strong>Least Profitable Project:</strong> {insights.get('least_profitable_project', 'N/A')}</li>
        <li><strong>Analysis Period:</strong> {insights.get('date_range', {}).get('start', 'N/A')} to {insights.get('date_range', {}).get('end', 'N/A')}</li>
        </ul>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="insight-box">
        <h4>📈 Performance Metrics</h4>
        <ul>
        <li><strong>Positive Cash Flow Periods:</strong> {insights.get('positive_cash_flow_months', 0)}</li>
        <li><strong>Negative Cash Flow Periods:</strong> {insights.get('negative_cash_flow_months', 0)}</li>
        <li><strong>Overall Performance:</strong> {'Profitable' if insights.get('total_net_cash_flow', 0) > 0 else 'Loss-making'}</li>
        </ul>
        </div>
        """, unsafe_allow_html=True)

def process_uploaded_file(uploaded_file):
    """Process uploaded Excel file with intelligent detection"""
    try:
        # Save uploaded file temporarily
        with open("temp_cashflow.xlsx", "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        # Get available sheets
        sheets = get_excel_sheets("temp_cashflow.xlsx")
        
        # Sheet selection
        if len(sheets) > 1:
            st.subheader("📋 Sheet Selection")
            selected_sheet = st.selectbox(
                "Select the Excel sheet to analyze:",
                sheets,
                help="Choose the sheet that contains your cash flow data"
            )
        else:
            selected_sheet = sheets[0]
            st.info(f"Using sheet: **{selected_sheet}**")
        
        # Load and analyze data
        reader = CashFlowReader("temp_cashflow.xlsx", selected_sheet)
        if not reader.read_excel_file():
            st.error("Failed to read the Excel file")
            return None
        column_mapping = reader.analyze_structure()
        
        # Display detected structure
        st.subheader("🔍 Detected Data Structure")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Available Columns:**")
            st.write(list(reader.data.columns))
            
            if column_mapping.get('formulas'):
                st.write("**Detected Formulas:**")
                formula_df = pd.DataFrame(column_mapping['formulas'])
                if not formula_df.empty:
                    st.dataframe(formula_df[['cell', 'formula', 'is_sum', 'is_total']], height=150)
        
        with col2:
            st.write("**Intelligent Detection Results:**")
            st.write(f"📊 **Project columns:** {column_mapping.get('project_columns', [])}")
            st.write(f"📅 **Date columns:** {column_mapping.get('date_columns', [])}")
            st.write(f"💰 **Cash In columns:** {column_mapping.get('cash_in_columns', [])}")
            st.write(f"💸 **Cash Out columns:** {column_mapping.get('cash_out_columns', [])}")
        
        # Column mapping interface
        st.subheader("🎯 Column Mapping")
        st.write("Verify or adjust the column mappings below:")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            project_col = st.selectbox(
                "Project/Category Column:",
                options=[None] + list(reader.data.columns),
                index=0 if not column_mapping.get('project_columns') else list(reader.data.columns).index(column_mapping['project_columns'][0]) + 1,
                help="Column containing project names or categories"
            )
        
        with col2:
            date_col = st.selectbox(
                "Date Column:",
                options=[None] + list(reader.data.columns),
                index=0 if not column_mapping.get('date_columns') else list(reader.data.columns).index(column_mapping['date_columns'][0]) + 1,
                help="Column containing dates"
            )
        
        with col3:
            cash_in_cols = st.multiselect(
                "Cash In Columns:",
                options=list(reader.data.columns),
                default=column_mapping.get('cash_in_columns', []),
                help="Columns representing money coming in (positive values)"
            )
        
        with col4:
            cash_out_cols = st.multiselect(
                "Cash Out Columns:",
                options=list(reader.data.columns),
                default=column_mapping.get('cash_out_columns', []),
                help="Columns representing money going out (expenses)"
            )
        
        # Validation
        if not project_col or not date_col:
            st.error("⚠️ Please select both Project and Date columns to continue.")
            return None, None
        
        if not cash_in_cols and not cash_out_cols:
            st.error("⚠️ Please select at least one Cash In or Cash Out column.")
            return None, None
        
        # Process data with selected columns
        try:
            processed_df = prepare_data_with_mapping(
                df, column_mapping, project_col, date_col, cash_in_cols, cash_out_cols
            )
            
            # Clean and prepare final data
            final_df = reader.clean_and_prepare_data(processed_df)
            
            if final_df is not None:
                st.success("✅ Data processed successfully!")
                
                # Show data preview
                with st.expander("📊 Data Preview", expanded=False):
                    st.dataframe(final_df.head(10))
                
                return final_df, column_mapping
            else:
                st.error("❌ Error processing data. Please check your column selections.")
                return None, None
                
        except Exception as e:
            st.error(f"❌ Error processing data: {str(e)}")
            return None, None
            
    except Exception as e:
        st.error(f"❌ Error reading file: {str(e)}")
        return None, None

def show_instructions():
    """Show instructions when no file is uploaded"""
    st.info("👆 Please upload an Excel file to get started!")
    
    st.subheader("📋 Instructions")
    st.markdown("""
    ### How to use this dashboard:
    
    1. **Prepare your Excel file** with the following columns:
       - `Project`: Name of the project
       - `Date`: Date of the cash flow entry
       - `Cash_In`: Money coming in
       - `Cash_Out`: Money going out
    
    2. **Upload your file** using the file uploader in the sidebar
    
    3. **Explore the dashboard** with interactive charts and insights
    
    ### Sample Data Format:
    """)
    
    # Show sample data format
    sample_data = pd.DataFrame({
        'Project': ['Project A', 'Project A', 'Project B', 'Project B'],
        'Date': ['2024-01-01', '2024-02-01', '2024-01-15', '2024-02-15'],
        'Cash_In': [10000, 15000, 8000, 12000],
        'Cash_Out': [7000, 9000, 6000, 8000]
    })
    
    st.dataframe(sample_data, use_container_width=True)
    
    st.markdown("""
    ### Features:
    - 🧠 **Intelligent Detection**: Automatically detects and maps columns
    - 📊 **Interactive Charts**: Visualize cash flow trends over time
    - 📈 **Project Analysis**: Compare profitability across projects
    - 📅 **Monthly Trends**: Track monthly performance
    - 🔍 **Key Insights**: Automated analysis and recommendations
    - 💾 **Data Export**: Download processed data
    - 📋 **Multi-sheet Support**: Handle Excel files with multiple sheets
    - 🎯 **Flexible Mapping**: Manual override for column assignments
    """)

if __name__ == "__main__":
    main()