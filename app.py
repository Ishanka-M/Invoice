import streamlit as st
import google.generativeai as genai
import pandas as pd
import json
import io
import time

# පිටුවේ සැකසුම්
st.set_page_config(page_title="Invoice Data Extractor", layout="wide")

# --- SIDEBAR ---
with st.sidebar:
    st.title("⚙️ Configuration")
    api_key = st.text_input("Enter Gemini API Key:", type="password")
    st.markdown("---")
    st.info("නොමිලේ භාවිතා කළ හැකි Gemini 2.5 Flash-Lite මෙහි භාවිතා වේ.")

# --- MAIN UI ---
st.title("📑 Professional Invoice to Excel Converter")
st.write("Invoice කිහිපයක් එකවර තෝරා Product Code සහ Description ඇතුළු සියලු දත්ත Excel එකට ගන්න.")

if api_key:
    genai.configure(api_key=api_key.strip())
    model = genai.GenerativeModel('gemini-2.5-flash-lite')

    uploaded_files = st.file_uploader("Invoice Files (Images/PDFs) තෝරන්න...", type=["jpg", "jpeg", "png", "pdf"], accept_multiple_files=True)

    if uploaded_files:
        if st.button("Extract All Data"):
            all_rows = []
            progress_bar = st.progress(0)
            
            for index, uploaded_file in enumerate(uploaded_files):
                try:
                    # AI Prompt - මෙහිදී Product Code / Description එකම තීරුවක ඇති බව පවසා ඇත
                    prompt = """
                    Extract data from this invoice image and format it as JSON.
                    For the items table, ensure you capture:
                    - "Invoice No"
                    - "Delivery No"
                    - "Product Code / Description" (Extract the full text in that column)
                    - "Unit of Measure"
                    - "Quantity"
                    - "Net Price"
                    - "Amount"

                    Return ONLY a JSON object with a key called "items" which is a list of these objects.
                    Example format: {"items": [{"Invoice No": "...", "Product Code / Description": "...", "Quantity": 10, ...}]}
                    """

                    doc_content = {
                        "mime_type": uploaded_file.type,
                        "data": uploaded_file.getvalue()
                    }

                    response = model.generate_content([prompt, doc_content])
                    
                    # JSON Extract කරගැනීම
                    clean_json = response.text.replace('```json', '').replace('```', '').strip()
                    data = json.loads(clean_json)
                    
                    items = data.get("items", [])
                    for item in items:
                        item["Source File"] = uploaded_file.name # කුමන File එකෙන්ද ආවේ කියා හඳුනා ගැනීමට
                        all_rows.append(item)

                except Exception as e:
                    st.error(f"Error processing {uploaded_file.name}: {e}")
                
                progress_bar.progress((index + 1) / len(uploaded_files))

            # DataFrame එක සෑදීම
            if all_rows:
                df = pd.DataFrame(all_rows)
                
                # තීරු පිළිවෙළට සකස් කිරීම
                cols_order = ["Source File", "Invoice No", "Delivery No", "Product Code / Description", "Unit of Measure", "Quantity", "Net Price", "Amount"]
                df = df[cols_order]

                st.subheader("Extracted Data Preview")
                st.dataframe(df, use_container_width=True)

                # Excel Download
                excel_buffer = io.BytesIO()
                with pd.ExcelWriter(excel_buffer, engine='xlsxwriter') as writer:
                    df.to_excel(writer, index=False, sheet_name='Invoices')
                
                st.download_button(
                    label="📥 සියලුම දත්ත Excel ලෙස බාගත කරගන්න",
                    data=excel_buffer.getvalue(),
                    file_name="Invoice_Data_Summary.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            else:
                st.warning("දත්ත හඳුනා ගැනීමට නොහැකි විය.")
else:
    st.warning("කරුණාකර API Key එක ඇතුළත් කරන්න.")
