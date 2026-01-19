import streamlit as st
import google.generativeai as genai
import pandas as pd
import json
from PIL import Image
import io

# Streamlit පිටුවේ සැකසුම්
st.set_page_config(page_title="Invoice Data Extractor", layout="wide")
st.title("📄 Invoice Data to Excel (Image & PDF)")

# Sidebar එකේ API Key එක ලබා ගැනීම
st.sidebar.header("Settings")
api_key = st.sidebar.text_input("Enter your Gemini API Key:", type="password")

if api_key:
    genai.configure(api_key=api_key)
    # Gemini 1.5 Flash මාදිලිය PDF සහ Images දෙකම හොඳින් හඳුනා ගනී
    model = genai.GenerativeModel('gemini-1.5-flash')

    # PDF සහ Images දෙවර්ගයම Upload කිරීමට ඉඩ ලබා දීම
    uploaded_file = st.file_uploader("Invoice රූපය හෝ PDF එක ලබා දෙන්න...", type=["jpg", "jpeg", "png", "pdf"])

    if uploaded_file is not None:
        file_type = uploaded_file.type
        st.info(f"Loaded: {uploaded_file.name}")

        if st.button("Extract Data"):
            with st.spinner("දත්ත ලබා ගනිමින් පවතී..."):
                try:
                    # AI එකට ලබා දෙන උපදෙස්
                    prompt = """
                    Extract the following details from this document and return them strictly in JSON format:
                    - Invoice No
                    - Delivery No
                    - Items (A list of objects containing: Product Code/Description, Unit of Measure, Quantity, Net Price, Amount)
                    
                    Important: If Product Code and Description are together, keep them as one string. 
                    Ensure all numbers are formatted as numbers in JSON.
                    Only return the JSON object.
                    """

                    # PDF හෝ Image එක API එකට ගැළපෙන ලෙස සකස් කිරීම
                    document_data = {
                        "mime_type": file_type,
                        "data": uploaded_file.getvalue()
                    }
                    
                    response = model.generate_content([prompt, document_data])
                    
                    # JSON පිරිසිදු කිරීම
                    json_text = response.text.replace('```json', '').replace('```', '').strip()
                    data = json.loads(json_text)
                    
                    # දත්ත වගුවකට (Table) සකස් කිරීම
                    inv_no = data.get("Invoice No", "N/A")
                    del_no = data.get("Delivery No", "N/A")
                    items_df = pd.DataFrame(data.get("Items", []))
                    
                    # අමතර විස්තර එකතු කිරීම
                    items_df.insert(0, "Invoice No", inv_no)
                    items_df.insert(1, "Delivery No", del_no)
                    
                    st.success("සාර්ථකව දත්ත ලබා ගන්නා ලදී!")
                    st.dataframe(items_df, use_container_width=True)

                    # Excel ගොනුව සෑදීම
                    output = io.BytesIO()
                    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                        items_df.to_excel(writer, index=False, sheet_name='InvoiceData')
                    
                    st.download_button(
                        label="Excel ගොනුව බාගත කරගන්න",
                        data=output.getvalue(),
                        file_name=f"Invoice_{inv_no}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
                    
                except Exception as e:
                    st.error(f"දෝෂයක් සිදු විය: {e}")
                    st.info("පිටපත පරීක්ෂා කර නැවත උත්සාහ කරන්න.")
else:
    st.warning("වැඩසටහන ආරම්භ කිරීමට වම්පස ඇති Sidebar එකට API Key එක ලබා දෙන්න.")
