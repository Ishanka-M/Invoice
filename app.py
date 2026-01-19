import streamlit as st
import google.generativeai as genai
import pandas as pd
import json
from PIL import Image
import io

# පිටුවේ සැකසුම්
st.set_page_config(page_title="Gemini 2.5 Invoice Extractor", layout="wide", page_icon="🧾")

# --- SIDEBAR ---
with st.sidebar:
    st.title("⚙️ Configuration")
    user_api_key = st.text_input("Gemini API Key:", type="password", help="Get your key from https://aistudio.google.com/")
    st.markdown("---")
    st.info("මෙම පද්ධතිය Gemini 2.5 Flash මාදිලිය භාවිතා කරයි.")

# --- MAIN UI ---
st.title("📄 AI Invoice Data Extractor")
st.write("Invoice එකක රූපයක් හෝ PDF එකක් ලබා දී තත්පර කිහිපයකින් Excel ගොනුව ලබා ගන්න.")

if user_api_key:
    try:
        # API එක සක්‍රීය කිරීම
        genai.configure(api_key=user_api_key.strip())
        
        # අලුත්ම Gemini 2.5 Flash මාදිලිය භාවිතා කිරීම
        model = genai.GenerativeModel('gemini-2.5-flash')

        uploaded_file = st.file_uploader("Upload Invoice (JPG, PNG, PDF)", type=["jpg", "jpeg", "png", "pdf"])

        if uploaded_file:
            if st.button("දත්ත ලබා ගන්න (Extract Data)"):
                with st.spinner("Gemini 2.5 මගින් දත්ත පරීක්ෂා කරමින් පවතී..."):
                    try:
                        # Prompt එක
                        prompt = """
                        Analyze this invoice and extract data into a JSON format with these keys:
                        - "Invoice No": string
                        - "Delivery No": string
                        - "Items": list of objects (Product Code / Description, Unit of Measure, Quantity, Net Price, Amount)
                        Return ONLY raw JSON code.
                        """

                        # File එක සකස් කිරීම
                        doc_content = {
                            "mime_type": uploaded_file.type,
                            "data": uploaded_file.getvalue()
                        }

                        # AI Response එක ලබා ගැනීම
                        response = model.generate_content([prompt, doc_content])
                        
                        # JSON පිරිසිදු කිරීම
                        clean_json = response.text.replace('```json', '').replace('```', '').strip()
                        extracted_data = json.loads(clean_json)

                        # Header විස්තර
                        inv_no = extracted_data.get("Invoice No", "N/A")
                        del_no = extracted_data.get("Delivery No", "N/A")
                        
                        st.subheader(f"Invoice: {inv_no}")
                        
                        # Table එක සෑදීම
                        df = pd.DataFrame(extracted_data.get("Items", []))
                        df.insert(0, "Invoice No", inv_no)
                        df.insert(1, "Delivery No", del_no)

                        # පෙන්වීම
                        st.dataframe(df, use_container_width=True)

                        # Excel එක සාදා Download බොත්තම ලබා දීම
                        excel_io = io.BytesIO()
                        with pd.ExcelWriter(excel_io, engine='xlsxwriter') as writer:
                            df.to_excel(writer, index=False, sheet_name='ExtractedData')
                        
                        st.download_button(
                            label="📥 Download Excel File",
                            data=excel_io.getvalue(),
                            file_name=f"Invoice_{inv_no}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        )

                    except Exception as e:
                        st.error(f"දෝෂයක් සිදු විය: {str(e)}")
                        st.info("API Key එක හෝ Model එක අලුත් දැයි පරීක්ෂා කරන්න.")

    except Exception as e:
        st.error(f"API Configuration Error: {str(e)}")
else:
    st.warning("කරුණාකර වම් පස ඇති තීරුවේ API Key එක ඇතුළත් කරන්න.")
