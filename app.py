import streamlit as st
import google.generativeai as genai
import pandas as pd
import json
import io
import time

# පිටුවේ සැකසුම්
st.set_page_config(page_title="Bulk Invoice Extractor", layout="wide", page_icon="🧾")

# --- API KEY & MODEL ROTATION LOGIC ---
def get_model():
    """Secrets වල ඇති Keys සහ දැනට වැඩ කරන Models මාරුවෙන් මාරුවට පරීක්ෂා කරයි"""
    if "api_keys" not in st.secrets:
        st.error("කරුණාකර Streamlit Secrets වල 'api_keys' ලැයිස්තුව ඇතුළත් කරන්න!")
        return None

    all_keys = st.secrets["api_keys"]
    
    # දැනට පවතින හොඳම Models ලැයිස්තුව
    models_to_try = [
        'gemini-3-flash-preview', 
        'gemini-2.5-flash-lite', 
        'gemini-2.5-flash'
    ]
    
    for model_name in models_to_try:
        for key in all_keys:
            try:
                genai.configure(api_key=key.strip())
                model = genai.GenerativeModel(model_name)
                # Key එක සහ Model එක වැඩදැයි බැලීමට කුඩා පරීක්ෂණයක්
                model.generate_content("Hi", generation_config={"max_output_tokens": 1}) 
                return model
            except Exception:
                continue # දෝෂයක් ආවොත් ඊළඟ Key එකට හෝ Model එකට යයි
            
    st.error("සියලුම API Keys හෝ Models දැනට කාර්යබහුලයි (Limit Reached). කරුණාකර මද වේලාවකින් උත්සාහ කරන්න.")
    return None

# --- MAIN UI ---
st.title("📑 Bulk Invoice Data Extractor")
st.write("Invoice කිහිපයක් එකවර Upload කර දත්ත ලබා ගන්න. (Gemini 3 & 2.5 Supported)")

# වැඩ කරන Model එක ලබා ගැනීම
model = get_model()

if model:
    uploaded_files = st.file_uploader("Invoice Files (Images/PDFs) තෝරන්න...", type=["jpg", "jpeg", "png", "pdf"], accept_multiple_files=True)

    if uploaded_files:
        if st.button("Extract All Data"):
            all_rows = []
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            for index, uploaded_file in enumerate(uploaded_files):
                status_text.text(f"දත්ත කියවමින් පවතී: {uploaded_file.name} ({index+1}/{len(uploaded_files)})")
                
                # AI එකට දෙන උපදෙස්
                prompt = """
                Extract data from this invoice and format it as JSON.
                Capture:
                - "Invoice No"
                - "Delivery No"
                - "Customer PO"
                - "Product Code / Description"
                - "Unit of Measure"
                - "Quantity"
                - "Net Price"
                - "Amount"

                Return ONLY a JSON object with a key 'items' containing a list of these objects.
                """

                try:
                    doc_content = {
                        "mime_type": uploaded_file.type,
                        "data": uploaded_file.getvalue()
                    }

                    # AI Response ලබා ගැනීම
                    response = model.generate_content([prompt, doc_content])
                    
                    # JSON පිරිසිදු කර ගැනීම
                    clean_json = response.text.replace('```json', '').replace('```', '').strip()
                    data = json.loads(clean_json)
                    
                    items = data.get("items", [])
                    for item in items:
                        item["Source File"] = uploaded_file.name
                        all_rows.append(item)

                except Exception as e:
                    # Limit එක පැමිණියහොත් වෙනත් Key එකකට හෝ Model එකකට මාරු වීම
                    st.warning(f"Limit reached. Retrying with a new key for: {uploaded_file.name}")
                    model = get_model() # අලුත් Model/Key එකක් ලබා ගැනීම
                    if model:
                        time.sleep(2) # පොඩි විවේකයක් ලබා දීම
                        try:
                            response = model.generate_content([prompt, doc_content])
                            clean_json = response.text.replace('```json', '').replace('```', '').strip()
                            data = json.loads(clean_json)
                            items = data.get("items", [])
                            for item in items:
                                item["Source File"] = uploaded_file.name
                                all_rows.append(item)
                        except:
                            st.error(f"Failed to process {uploaded_file.name} after retry.")
                
                progress_bar.progress((index + 1) / len(uploaded_files))
                time.sleep(1) # API Rate limits පාලනයට

            if all_rows:
                df = pd.DataFrame(all_rows)
                
                # තීරු පිළිවෙළට සකස් කිරීම
                cols_order = ["Source File", "Invoice No", "Delivery No", "Customer PO", "Product Code / Description", "Unit of Measure", "Quantity", "Net Price", "Amount"]
                for col in cols_order:
                    if col not in df.columns: df[col] = "N/A"
                df = df[cols_order]

                st.subheader("Extracted Data Preview")
                st.dataframe(df, use_container_width=True)

                # Excel සෑදීම
                excel_buffer = io.BytesIO()
                with pd.ExcelWriter(excel_buffer, engine='xlsxwriter') as writer:
                    df.to_excel(writer, index=False, sheet_name='Invoices')
                
                st.download_button(
                    label="📥 සියලු දත්ත Excel ලෙස බාගත කරගන්න",
                    data=excel_buffer.getvalue(),
                    file_name="Invoice_Data_Summary.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            else:
                st.error("දත්ත කිසිවක් හඳුනා ගැනීමට නොහැකි විය. කරුණාකර නැවත උත්සාහ කරන්න.")

# --- FOOTER ---
st.markdown("<br><hr><p style='text-align: center; color: gray;'>Developed by Ishanka Madusanka</p>", unsafe_allow_html=True)
