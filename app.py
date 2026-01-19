import streamlit as st
import google.generativeai as genai
import pandas as pd
import json
from PIL import Image
import io

# පිටුවේ සැකසුම්
st.set_page_config(page_title="Invoice Data Extractor", layout="wide", page_icon="📝")

# --- SIDEBAR (Settings) ---
with st.sidebar:
    st.title("⚙️ සැකසුම් (Settings)")
    st.markdown("---")
    # API Key එක ලබා ගැනීම සහ දෙපස හිස්තැන් ඉවත් කිරීම
    user_api_key = st.text_input("Gemini API Key එක ඇතුළත් කරන්න:", type="password")
    st.markdown("---")
    st.write("💡 **උදවු:** Google AI Studio එකෙන් ගත් API Key එක මෙතැනට ලබා දෙන්න.")

# --- MAIN UI ---
st.title("📊 Invoice to Excel Converter")
st.info("Invoice එකක Image එකක් හෝ PDF එකක් ලබා දී තත්පර කිහිපයකින් Excel ගොනුව ලබා ගන්න.")

if user_api_key:
    try:
        # Gemini API එක සකස් කිරීම
        genai.configure(api_key=user_api_key.strip())
        
        # 404 Error එක මඟහරවා ගැනීමට වඩාත් සුදුසු Model එක තෝරා ගැනීම
        model = genai.GenerativeModel('gemini-1.5-flash-latest')

        # ගොනු ලබා ගැනීම (Image & PDF)
        uploaded_file = st.file_uploader("ඔබේ Invoice එක මෙතැනට Upload කරන්න...", type=["jpg", "jpeg", "png", "pdf"])

        if uploaded_file is not None:
            st.success(f"File එක සම්බන්ධයි: {uploaded_file.name}")
            
            if st.button("දත්ත ලබා ගන්න (Extract Data)"):
                with st.spinner("AI මගින් දත්ත පරීක්ෂා කරමින් පවතී..."):
                    try:
                        # AI එකට ලබා දෙන උපදෙස් (Prompt)
                        prompt = """
                        Look at this invoice and extract the following details. 
                        Format the output as a valid JSON object with these exact keys:
                        {
                          "Invoice No": "string",
                          "Delivery No": "string",
                          "Items": [
                            {
                              "Product Code / Description": "string",
                              "Unit of Measure": "string",
                              "Quantity": number,
                              "Net Price": number,
                              "Amount": number
                            }
                          ]
                        }
                        If any detail is missing, put "N/A". Return ONLY the JSON.
                        """

                        # ගොනුවේ දත්ත සකස් කිරීම
                        doc_data = {
                            "mime_type": uploaded_file.type,
                            "data": uploaded_file.getvalue()
                        }

                        # AI ප්‍රතිචාරය ලබා ගැනීම
                        response = model.generate_content([prompt, doc_data])
                        
                        # JSON කොටස පමණක් වෙන් කර ගැනීම
                        raw_response = response.text.replace('```json', '').replace('```', '').strip()
                        data = json.loads(raw_response)

                        # ප්‍රධාන විස්තර පෙන්වීම
                        inv_no = data.get("Invoice No", "N/A")
                        del_no = data.get("Delivery No", "N/A")
                        
                        col1, col2 = st.columns(2)
                        col1.info(f"**Invoice No:** {inv_no}")
                        col2.info(f"**Delivery No:** {del_no}")

                        # වගුව (Table) සකස් කිරීම
                        df = pd.DataFrame(data.get("Items", []))
                        
                        # පළමු තීරු ලෙස Invoice/Delivery No එකතු කිරීම (Excel එකේ ලෙහෙසියට)
                        df.insert(0, "Invoice No", inv_no)
                        df.insert(1, "Delivery No", del_no)

                        # වගුව Screen එකේ පෙන්වීම
                        st.dataframe(df, use_container_width=True)

                        # Excel ගොනුව සෑදීම
                        output = io.BytesIO()
                        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                            df.to_excel(writer, index=False, sheet_name='Data')
                        
                        st.download_button(
                            label="📥 Excel ගොනුව බාගත කරගන්න",
                            data=output.getvalue(),
                            file_name=f"Invoice_{inv_no}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        )

                    except Exception as e:
                        st.error(f"දත්ත කියවීමේදී දෝෂයක් ඇති විය: {str(e)}")
                        st.warning("සටහන: ඔබගේ API Key එකට Gemini 1.5 Flash පහසුකම ලැබී ඇත්දැයි බලන්න.")

    except Exception as e:
        st.error(f"සම්බන්ධතාවයේ දෝෂයකි: {str(e)}")
else:
    st.warning("අඛණ්ඩව වැඩ කිරීමට කරුණාකර වම් පස ඇති Sidebar එකට API Key එක ලබා දෙන්න.")
