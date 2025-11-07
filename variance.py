# app.py

import streamlit as st
import pandas as pd
import io
import math
import json
from openai import OpenAI

# --- Initialize OpenAI client using Streamlit secrets ---
# Make sure to add your OpenAI API key in Streamlit Secrets:
# OPENAI_API_KEY="your_openai_api_key_here"
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# --- Streamlit Page Config ---
st.set_page_config(layout="wide", page_title="AI Item Classification Tool")
st.title("🛒 AI Item Classification Tool")
st.markdown("""
Upload your **full items details.xlsx** file. The AI will analyze `Item Name` 
and automatically classify each item into **Category** and **Sub_Category**.
""")

# --- File Uploader ---
uploaded_file = st.file_uploader("📂 Choose your Excel file", type=['xlsx'])

if uploaded_file is not None:
    try:
        df = pd.read_excel(uploaded_file)
        
        if 'Item Name' not in df.columns:
            st.error("🚨 Excel file must contain an 'Item Name' column.")
            st.stop()
        
        st.success(f"✅ File loaded successfully: {uploaded_file.name}")
        st.subheader("Original Data Preview (First 5 Rows)")
        st.dataframe(df.head(), use_container_width=True)
        
    except Exception as e:
        st.error(f"Error reading Excel file: {e}")
        st.stop()
    
    # --- AI Classification Function ---
    def classify_batch(item_names):
        """
        Classify a list of item names into Category and Sub_Category using OpenAI.
        Returns a pandas DataFrame.
        """
        prompt = f"""
You are an expert product classifier.
Classify the following items into Category and Sub_Category.
Return a JSON array where each item has 'Item Name', 'Category', 'Sub_Category'.

Items: {item_names}

Example output:
[
  {{ "Item Name": "Example Item 1", "Category": "Category1", "Sub_Category": "Sub1" }},
  {{ "Item Name": "Example Item 2", "Category": "Category2", "Sub_Category": "Sub2" }}
]
"""
        try:
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                temperature=0
            )
            text = response.choices[0].message.content.strip()
            classified_data = json.loads(text)
            return pd.json_normalize(classified_data)
        except Exception as e:
            st.error(f"Error during AI classification: {e}")
            return pd.DataFrame(columns=['Item Name', 'Category', 'Sub_Category'])
    
    # --- Run Classification in Batches ---
    batch_size = 10  # Adjust for large datasets
    classified_list = []
    
    if st.button("🚀 Run AI Classification"):
        with st.spinner("Classifying items using AI..."):
            num_batches = math.ceil(len(df) / batch_size)
            for i in range(num_batches):
                batch_items = df['Item Name'].iloc[i*batch_size:(i+1)*batch_size].tolist()
                batch_result = classify_batch(batch_items)
                classified_list.append(batch_result)
            
            classified_df = pd.concat(classified_list, ignore_index=True)
            # Merge with original DataFrame
            final_df = df.merge(classified_df, on='Item Name', how='left')
            
            st.success("✅ AI Classification complete!")
            st.subheader("Classified Items Preview")
            st.dataframe(final_df.head(), use_container_width=True)
            
            # --- Download Option ---
            @st.cache_data
            def convert_df_to_excel(df_to_convert):
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    df_to_convert.to_excel(writer, index=False, sheet_name='Classified_Items')
                return output.getvalue()
            
            excel_data = convert_df_to_excel(final_df)
            st.download_button(
                label="📥 Download Classified Data",
                data=excel_data,
                file_name='classified_items_output.xlsx',
                mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
