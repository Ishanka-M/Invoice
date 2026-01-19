import streamlit as st
import google.generativeai as genai
import pandas as pd
import json
import io
import time

# පිටුවේ සැකසුම්
st.set_page_config(page_title="Invoice Data Extractor", layout="wide", page_icon="🧾")

# --- SIDEBAR ---
with st.sidebar:
    st.title("⚙️ Configuration")
    api_key = st.text_input("Enter Gemini API Key:", type="password")
    st.markdown("---")
    st.info("නොමිලේ භාවිතා කළ හැකි Gemini 2.5 Flash-Lite මෙහි භාවිතා වේ.")

# --- MAIN UI ---
st.title("📑 Professional Invoice to Excel Converter")
st.write("Invoice කිහිපයක් එකවර තෝරා සියලු දත්ත Excel එකට ලබා ගන්න.")

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
                    # AI Prompt - Customer PO එකත් ලබා ගැනීමට උපදෙස් දී ඇත
                    prompt = """
                    Extract data from this invoice image and format it as JSON.
                    Ensure you capture the following fields:
                    - "Invoice No"
                    - "Delivery No"
                    - "Customer PO" (Look for Customer Purchase Order number)
                    - "Product Code / Description"
                    - "Unit of Measure"
                    - "Quantity"
                    - "Net Price"
                    - "Amount"

                    Return ONLY a JSON object with a key called "items" which is a list of these objects.
                    Example: {"items": [{"Invoice No": "...", "Customer PO": "...", "Product Code / Description": "...", "Quantity": 10, ...}]}
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
                        item["Source File"] = uploaded_file.name
                        all_rows.append(item)

                except Exception as e:
                    st.error(f"Error processing {uploaded_file.name}: {e}")
                
                progress_bar.progress((index + 1) / len(uploaded_files))

            # DataFrame එක සෑදීම
            if all_rows:
                df = pd.DataFrame(all_rows)
                
                # තීරු පිළිවෙළට සකස් කිරීම (Customer PO ඇතුළත්ව)
                cols_order = ["Source File", "Invoice No", "Delivery No", "Customer PO", "Product Code / Description", "Unit of Measure", "Quantity", "Net Price", "Amount"]
                
                # Column එකක් නැතිනම් එය හිස්ව පෙන්වීමට
                for col in cols_order:
                    if col not in df.columns:
                        df[col] = "N/A"
                
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

# --- FOOTER SECTION ---
st.markdown("---")
st.markdown(
    """
    <style>
    .footer {
        position: fixed;
        left: 0;
        bottom: 0;
        width: 100%;
        background-color: transparent;
        color: gray;
        text-align: center;
        padding: 10px;
        font-size: 14px;
    }
    </style>
    <div class="footer">
        <p>Developed by Ishanka Madusanka</p>
    </div>
    """,
    unsafe_allow_html=True
)

else:
    st.warning("කරුණාකර API Key එක ඇතුළත් කරන්න.")
    # Sidebar එක නැති වෙලාවටත් යටින් නම පෙන්වීමට
    st.markdown("<br><br><p style='text-align: center; color: gray;'>Developed by Ishanka Madusanka</p>", unsafe_allow_html=True)
