# app.py

import streamlit as st
import pandas as pd
import io
import openai
import os
import math

# --- Set your OpenAI API key safely ---
# You can also set it as environment variable instead of hardcoding
openai.api_key = os.getenv("OPENAI_API_KEY")  # or replace with "YOUR_API_KEY"

st.set_page_config(layout="wide", page_title="AI Item Classifier")
st.title("🛒 AI Item Classification Tool")
st.markdown(
    """
    The app automatically reads your **full items details.xlsx**, 
    analyzes `Item Name`, and classifies it into **Category** and **Sub-Category**.
    """
)

# --- Load Excel ---
file_path = "full items details.xlsx"
try:
    df = pd.read_excel(file_path)
    if 'Item Name' not in df.columns:
        st.error("🚨 Excel file must contain an 'Item Name' column.")
        st.stop()
    st.success(f"✅ Loaded file: {file_path}")
    st.subheader("Original Data Preview (First 5 Rows)")
    st.dataframe(df.head(), use_container_width=True)
except Exception as e:
    st.error(f"Error reading Excel file: {e}")
    st.stop()


# --- Function to classify a batch of items ---
def classify_batch(item_names):
    """
    Takes a list of item names and returns a list of dicts with Category and Sub-Category.
    """
    prompt = f"""
    You are an expert product classifier. 
    Classify the following items into Category and Sub-Category.
    Return **JSON array** where each item has 'Item Name', 'Category', 'Sub_Category'.

    Items: {item_names}

    Example output:
    [
      {{ "Item Name": "Example Item 1", "Category": "Category1", "Sub_Category": "Sub1" }},
      {{ "Item Name": "Example Item 2", "Category": "Category2", "Sub_Category": "Sub2" }}
    ]
    """
    
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",  # or "gpt-4"
            messages=[{"role": "user", "content": prompt}],
            temperature=0
        )
        text = response.choices[0].message.content.strip()
        # Convert JSON text to Python object
        return pd.json_normalize(eval(text))
    except Exception as e:
        st.error(f"Error during AI classification: {e}")
        return pd.DataFrame(columns=['Item Name', 'Category', 'Sub_Category'])


# --- Run classification in batches ---
batch_size = 10  # You can adjust this based on API limits
classified_list = []

with st.spinner("🚀 Classifying items using AI..."):
    num_batches = math.ceil(len(df) / batch_size)
    for i in range(num_batches):
        batch_items = df['Item Name'].iloc[i*batch_size:(i+1)*batch_size].tolist()
        batch_result = classify_batch(batch_items)
        classified_list.append(batch_result)

    classified_df = pd.concat(classified_list, ignore_index=True)
    # Merge with original dataframe
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
