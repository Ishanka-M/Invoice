import streamlit as st
import google.generativeai as genai
import pandas as pd
import json
import io
import time

# පිටුවේ සැකසුම්
st.set_page_config(page_title="Auto-Rotate Invoice Extractor", layout="wide")

# --- API KEY ROTATION FUNCTION ---
def get_working_model():
    # Streamlit Secrets වලින් Keys ලැයිස්තුව ලබා ගැනීම
    if "api_keys" not in st.secrets:
        st.error("Secrets වල API Keys ඇතුළත් කර නැත!")
        return None

    keys = st.secrets["api_keys"]
    
    for key in keys:
        try:
            genai.configure(api_key=key.strip())
            model = genai.GenerativeModel('gemini-2.5-flash-lite')
            # පොඩි ටෙස්ට් එකක් කරලා බලනවා Key එක වැඩද කියලා
            model.generate_content("test") 
            return model # වැඩ කරන පළමු Key එක ලබා දෙයි
        except Exception:
            continue # මේ Key එක වැඩ නැත්නම් ඊළඟ එකට යනවා
            
    return None

# --- MAIN UI ---
st.title("📑 Bulk Invoice Extractor (Multi-Key Support)")

# වැඩ කරන Model එක ලබා ගැනීම
model = get_working_model()

if model:
    uploaded_files = st.file_uploader("Invoices තෝරන්න...", type=["jpg", "png", "pdf"], accept_multiple_files=True)

    if uploaded_files and st.button("Extract Data"):
        all_rows = []
        for uploaded_file in uploaded_files:
            try:
                prompt = "Extract Invoice No, Delivery No, Customer PO, Product Code / Description, Unit of Measure, Quantity, Net Price, Amount as JSON."
                
                doc_content = {"mime_type": uploaded_file.type, "data": uploaded_file.getvalue()}
                response = model.generate_content([prompt, doc_content])
                
                data = json.loads(response.text.replace('```json', '').replace('```', '').strip())
                items = data.get("items", [])
                for item in items:
                    item["Source File"] = uploaded_file.name
                    all_rows.append(item)
                
                time.sleep(1) # Rate limit එක ගැන සැලකිලිමත් වීමට
            except Exception as e:
                # මෙතැනදී limit එක ඉවර වුණොත් නැවත අලුත් Key එකක් ගන්න උත්සාහ කළ හැක
                st.warning(f"Error with current key: {e}. Retrying with next key...")
                model = get_working_model()

        if all_rows:
            df = pd.DataFrame(all_rows)
            st.dataframe(df)
            
            excel_buffer = io.BytesIO()
            df.to_excel(excel_buffer, index=False)
            st.download_button("📥 Download Excel", excel_buffer.getvalue(), "Invoices.xlsx")

# --- FOOTER ---
st.markdown("<br><br><p style='text-align: center; color: gray;'>Developed by Ishanka Madusanka</p>", unsafe_allow_html=True)
