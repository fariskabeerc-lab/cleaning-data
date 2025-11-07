import streamlit as st
import pandas as pd
import io

st.set_page_config(layout="wide", page_title="AI-Free Item Classifier")
st.title("🛒 Item Classification Tool (No OpenAI Needed)")
st.markdown("""
This app reads your **full items details.xlsx** and classifies items into **Category** and **Sub-Category**
based on **keywords** in the Item Name.
""")

# --- Upload Excel File ---
uploaded_file = st.file_uploader("Upload Excel file", type=['xlsx'])
if uploaded_file:
    try:
        df = pd.read_excel(uploaded_file)
        if 'Item Name' not in df.columns:
            st.error("🚨 Excel file must contain an 'Item Name' column.")
            st.stop()
        st.success(f"✅ Loaded file: {uploaded_file.name}")
        st.subheader("Original Data Preview (First 5 Rows)")
        st.dataframe(df.head(), use_container_width=True)
    except Exception as e:
        st.error(f"Error reading Excel file: {e}")
        st.stop()
else:
    st.info("Please upload an Excel file to start.")
    st.stop()

# --- Rule-based classification function ---
def classify_item(item_name):
    name = item_name.lower()
    if any(x in name for x in ["sugar", "jaggery"]):
        return "Grocery", "Sugar"
    elif any(x in name for x in ["soap", "shampoo", "toothpaste"]):
        return "Personal Care", "Hygiene"
    elif any(x in name for x in ["milk", "cheese", "butter"]):
        return "Dairy", "Milk Products"
    elif any(x in name for x in ["rice", "wheat", "flour"]):
        return "Grocery", "Grains"
    elif any(x in name for x in ["pen", "notebook", "marker"]):
        return "Stationery", "Writing Materials"
    else:
        return "Others", "Misc"

# --- Apply classification ---
with st.spinner("Classifying items locally..."):
    df['Category'], df['Sub_Category'] = zip(*df['Item Name'].map(classify_item))

st.success("✅ Classification complete!")
st.subheader("Classified Items Preview")
st.dataframe(df.head(), use_container_width=True)

# --- Download Option ---
@st.cache_data
def convert_df_to_excel(df_to_convert):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df_to_convert.to_excel(writer, index=False, sheet_name='Classified_Items')
    return output.getvalue()

excel_data = convert_df_to_excel(df)
st.download_button(
    label="📥 Download Classified Data",
    data=excel_data,
    file_name='classified_items_output.xlsx',
    mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
)
