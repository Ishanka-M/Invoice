import streamlit as st
import google.generativeai as genai
import pandas as pd
import json
import io
import time

# පිටුවේ සැකසුම්
st.set_page_config(page_title="Bulk Invoice Extractor", layout="wide", page_icon="🧾")

# --- API KEY ROTATION LOGIC ---
def get_model():
    """Secrets වල ඇති Keys 7 මාරුවෙන් මාරුවට පරීක්ෂා කර වැඩ කරන එකක් ලබා දෙයි"""
    if "api_keys" not in st.secrets:
        st.error("කරුණාකර Streamlit Secrets වල 'api_keys' ලැයිස්තුව ඇතුළත් කරන්න!")
        return None

    all_keys = st.secrets["api_keys"]
    
    for key in all_keys:
        try:
            genai.configure(api_key=key.strip())
            # Gemini 2.5 Flash-Lite (Free භාවිතයට ඉතා සුදුසුයි)
            model = genai.GenerativeModel('gemini-2.5-flash-lite')
            # Key එක වැඩදැයි බැලීමට කුඩා පරීක්ෂණයක්
            model.generate_content("Hi") 
            return model
        except Exception:
            continue # මෙම Key එකේ Limit ඉවර නම් ඊළඟ එකට යයි
            
    st.error("ලබා දී ඇති API Keys 7 ම දැනට වැඩ කරන්නේ නැත. කරුණාකර මද වේලාවකින් උත්සාහ කරන්න.")
    return None

# --- MAIN UI ---
st.title("📑 Bulk Invoice Data Extractor")
st.write("Invoice කිහිපයක් එකවර Upload කර Product Code, Description සහ Customer PO ඇතුළු දත්ත ලබා ගන්න.")

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
                try:
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

                    doc_content = {
                        "mime_type": uploaded_file.type,
                        "data": uploaded_file.getvalue()
                    }

                    # AI Response
                    response = model.generate_content([prompt, doc_content])
                    
                    # JSON පිරිසිදු කර ගැනීම
                    clean_json = response.text.replace('```json', '').replace('```', '').strip()
                    data = json.loads(clean_json)
                    
                    items = data.get("items", [])
                    for item in items:
                        item["Source File"] = uploaded_file.name
                        all_rows.append(item)

                except Exception as e:
                    st.warning(f"Key limit reached. Switching key for: {uploaded_file.name}")
                    # වත්මන් Key එක වැඩ නැතිනම් අලුත් එකක් ගෙන නැවත උත්සාහ කරයි
                    model = get_model()
                    if model:
                        # එම file එකම නැවත කියවීමට (Repeat the current index)
                        time.sleep(1)
                        # මෙතැනදී යම් දෝෂයක් ආවොත් මඟ හැරීමට try-except යොදා ඇත
                        try:
                            response = model.generate_content([prompt, doc_content])
                            clean_json = response.text.replace('```json', '').replace('```', '').strip()
                            data = json.loads(clean_json)
                            items = data.get("items", [])
                            for item in items:
                                item["Source File"] = uploaded_file.name
                                all_rows.append(item)
                        except:
                            st.error(f"Failed to process {uploaded_file.name} even after key switch.")
                
                progress_bar.progress((index + 1) / len(uploaded_files))
                time.sleep(0.5) # වේගය පාලනයට

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
                st.warning("කිසිදු දත්තයක් හඳුනා ගැනීමට නොහැකි විය.")

# --- FOOTER ---
st.markdown("<br><hr><p style='text-align: center; color: gray;'>Developed by Ishanka Madusanka</p>", unsafe_allow_html=True)
