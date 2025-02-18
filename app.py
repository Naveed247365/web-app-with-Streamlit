import streamlit as st
import pandas as pd
import os
from io import BytesIO
from streamlit.runtime.uploaded_file_manager import UploadedFile

# Configure the Streamlit app
st.set_page_config(
    page_title="Data Sweeper Pro",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Enhanced custom CSS with dark mode
st.markdown("""
<style>
    [data-testid="stAppViewContainer"] {
        background-color: #1a1a1a;
        color: #ffffff;
    }
    .stDataFrame {
        background-color: #2d2d2d !important;
    }
    .stSelectbox, .stMultiselect, .stRadio > div {
        background-color: #333333 !important;
    }
    .file-section {
        background-color: #262626;
        border-radius: 10px;
        padding: 1.5rem;
        margin-bottom: 1.5rem;
    }
</style>
""", unsafe_allow_html=True)

def process_file(file: UploadedFile) -> pd.DataFrame:
    """Process uploaded file and return DataFrame"""
    try:
        if file.name.endswith('.csv'):
            return pd.read_csv(file)
        elif file.name.endswith('.xlsx'):
            return pd.read_excel(file)
        else:
            st.error(f"Unsupported file type: {file.name}")
            return None
    except Exception as e:
        st.error(f"Error processing {file.name}: {str(e)}")
        return None

def handle_data_cleaning(df: pd.DataFrame, key_suffix: str) -> pd.DataFrame:
    """Handle data cleaning operations"""
    with st.expander("🛠️ Advanced Data Cleaning", expanded=False):
        col1, col2 = st.columns(2)
        with col1:
            if st.button(f"Remove Duplicates ({key_suffix})"):
                df = df.drop_duplicates()
                st.session_state[f'df_{key_suffix}'] = df
                st.success("Duplicates removed!")
        
        with col2:
            missing_strategy = st.selectbox(
                f"Missing Values Strategy ({key_suffix})",
                ['None', 'Mean', 'Median', 'Mode', 'Drop Rows'],
                key=f'missing_{key_suffix}'
            )
            
            if missing_strategy != 'None':
                numeric_cols = df.select_dtypes(include='number').columns
                if numeric_cols.empty:
                    st.warning("No numeric columns to fill!")
                else:
                    for col in numeric_cols:
                        if missing_strategy == 'Mean':
                            df[col].fillna(df[col].mean(), inplace=True)
                        elif missing_strategy == 'Median':
                            df[col].fillna(df[col].median(), inplace=True)
                        elif missing_strategy == 'Mode':
                            df[col].fillna(df[col].mode()[0], inplace=True)
                    if missing_strategy == 'Drop Rows':
                        df = df.dropna(subset=numeric_cols)
                    st.session_state[f'df_{key_suffix}'] = df
    return df

def main():
    st.title("📊 Data Sweeper Pro")
    st.markdown("Advanced data processing and transformation toolkit")

    uploaded_files = st.file_uploader(
        "Upload Files (CSV/XLSX)",
        type=["csv", "xlsx"],
        accept_multiple_files=True
    )

    if not uploaded_files:
        st.info("👆 Upload files to get started")
        return

    for file in uploaded_files:
        file_key = hash(file.name)  # Unique key for session state
        
        with st.expander(f"📁 {file.name}", expanded=True):
            # Initialize session state for each file
            if f'df_{file_key}' not in st.session_state:
                st.session_state[f'df_{file_key}'] = process_file(file)
            
            df = st.session_state[f'df_{file_key}']
            if df is None:
                continue

            st.subheader("File Overview")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Rows", df.shape[0])
            with col2:
                st.metric("Columns", df.shape[1])
            with col3:
                st.metric("Missing Values", df.isna().sum().sum())

            # Data cleaning section
            df = handle_data_cleaning(df, file_key)

            # Column selection
            selected_cols = st.multiselect(
                f"Select Columns ({file.name})",
                df.columns,
                default=list(df.columns),
                key=f'cols_{file_key}'
            )
            df = df[selected_cols]

            # Visualization
            with st.expander("📈 Data Visualization", expanded=False):
                if not selected_cols:
                    st.warning("Select columns to visualize")
                else:
                    chart_type = st.selectbox(
                        f"Chart Type ({file.name})",
                        ['Bar', 'Line', 'Scatter', 'Histogram'],
                        key=f'chart_{file_key}'
                    )
                    x_axis = st.selectbox("X Axis", selected_cols)
                    y_axis = st.selectbox("Y Axis", selected_cols) if len(selected_cols) > 1 else x_axis
                    
                    if chart_type == 'Bar':
                        st.bar_chart(df[[x_axis, y_axis]])
                    elif chart_type == 'Line':
                        st.line_chart(df[[x_axis, y_axis]])
                    elif chart_type == 'Scatter':
                        st.write("Scatter plots require numeric columns")
                        if pd.api.types.is_numeric_dtype(df[x_axis]) and pd.api.types.is_numeric_dtype(df[y_axis]):
                            st.scatter_chart(df[[x_axis, y_axis]])
                    elif chart_type == 'Histogram':
                        st.pyplot(df[x_axis].hist().figure)

            # Conversion
            with st.expander("🔄 File Conversion", expanded=False):
                target_format = st.radio(
                    f"Convert to ({file.name})",
                    ['CSV', 'Excel'],
                    key=f'format_{file_key}'
                )
                
                buffer = BytesIO()
                if target_format == 'CSV':
                    df.to_csv(buffer, index=False)
                    mime_type = "text/csv"
                    ext = ".csv"
                else:
                    df.to_excel(buffer, index=False, engine='openpyxl')
                    mime_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    ext = ".xlsx"
                
                st.download_button(
                    f"Download {target_format}",
                    data=buffer.getvalue(),
                    file_name=f"converted_{file.name.split('.')[0]}{ext}",
                    mime=mime_type,
                    key=f'dl_{file_key}'
                )

if __name__ == "__main__":
    main()
# task complete