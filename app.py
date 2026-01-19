import streamlit as st
import google.generativeai as genai
import pandas as pd
import json
from PIL import Image
import io

# පිටුවේ සැකසුම් (Page Config)
st.set_page_config(page_title="Invoice Data Extractor", layout="wide", page_icon="📊")

# --- SIDEBAR කොටස ---
with st.sidebar:
    st.title("⚙️ Settings")
    st.markdown("---")
    # API Key එක ලබා ගැනීම (හිස්තැන් ඉවත් කිරීමට .strip() භාවිතා කර ඇත)
    user_api_key = st.text_input("Gemini API Key එක ඇතුළත් කරන්න:", type="password", help="Google AI Studio වෙතින් ලබාගත් Key එක මෙතැනට ලබා දෙන්න.")
    st.markdown("---")
    st.info("මෙම Tool එක මගින් Invoice වල ඇති දත්ත ස්වයංක්‍රීයව හඳුනාගෙන Excel ගොනුවක් සාදා දෙයි.")

# --- ප්‍රධාන පිටුව (Main UI) ---
st.title("📄 Invoice to Excel Converter")
st.write("Invoice එකක රූපයක් (Image) හෝ PDF එකක් Upload කර පහසුවෙන් දත්ත ලබා ගන්න.")

# API Key එක ඇතුළත් කර ඇත්නම් පමණක් වැඩසටහන ක්‍රියාත්මක වේ
if user_api_key:
    try:
        # Gemini API Configure කිරීම
        genai.configure(api_key=user_api_key.strip())
        model = genai.GenerativeModel('gemini-1.5-flash')

        # File Uploader
        uploaded_file = st.file_uploader("Invoice එක තෝරන්න (JPG, PNG, PDF)...", type=["jpg", "jpeg", "png", "pdf"])

        if uploaded_file is not None:
            st.success(f"File එක සාර්ථකව සම්බන්ධ කරන ලදී: {uploaded_file.name}")
            
            # Extract Button
            if st.button("දත්ත ලබා ගන්න (Extract Data)"):
                with st.spinner("Gemini AI මගින් දත්ත කියවමින් පවතී..."):
                    try:
                        # Prompt එක සකස් කිරීම
                        prompt = """
                        Please analyze this invoice document and extract the following information. 
                        Format the output strictly as a JSON object with these keys:
                        - "Invoice No": String
                        - "Delivery No": String
                        - "Items": List of objects, each containing:
                            - "Product Code / Description": String
                            - "Unit of Measure": String
                            - "Quantity": Number
                            - "Net Price": Number
                            - "Amount": Number
                        
                        If a value is missing, use "N/A". Only return the raw JSON.
                        """

                        # ගොනුව සකස් කිරීම
                        document_content = {
                            "mime_type": uploaded_file.type,
                            "data": uploaded_file.getvalue()
                        }

                        # AI ප්‍රතිචාරය ලබා ගැනීම
                        response = model.generate_content([prompt, document_content])
                        
                        # JSON දත්ත පිරිසිදු කර Extract කිරීම
                        raw_text = response.text.replace('```json', '').replace('```', '').strip()
                        extracted_data = json.loads(raw_text)

                        # Data Display
                        inv_no = extracted_data.get("Invoice No", "N/A")
                        del_no = extracted_data.get("Delivery No", "N/A")
                        
                        st.subheader(f"Invoice විස්තර: {inv_no}")
                        col1, col2 = st.columns(2)
                        col1.metric("Invoice No", inv_no)
                        col2.metric("Delivery No", del_no)

                        # Table එක සෑදීම
                        df = pd.DataFrame(extracted_data.get("Items", []))
                        
                        # Invoice තොරතුරු Table එකට එකතු කිරීම
                        df.insert(0, "Invoice No", inv_no)
                        df.insert(1, "Delivery No", del_no)

                        # වගුව පෙන්වීම
                        st.dataframe(df, use_container_width=True)

                        # Excel එකක් ලෙස සකස් කිරීම
                        excel_buffer = io.BytesIO()
                        with pd.ExcelWriter(excel_buffer, engine='xlsxwriter') as writer:
                            df.to_excel(writer, index=False, sheet_name='Sheet1')
                        
                        st.download_button(
                            label="📥 Excel ගොනුව බාගත කරගන්න (Download)",
                            data=excel_buffer.getvalue(),
                            file_name=f"Invoice_{inv_no}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        )

                    except Exception as e:
                        st.error(f"දත්ත කියවීමේදී ගැටලුවක් ඇති විය: {e}")
                        st.info("ඔබේ API Key එක නිවැරදිද සහ අන්තර්ජාල පහසුකම් පරීක්ෂා කරන්න.")

    except Exception as e:
        st.error(f"API Configuration දෝෂයකි: {e}")
else:
    st.warning("⚠️ කරුණාකර වම් පස ඇති Sidebar එකේ ඔබේ Gemini API Key එක ඇතුළත් කරන්න.")

# Footer
st.markdown("---")
st.caption("Powered by Gemini 1.5 Flash AI")
