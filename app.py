import streamlit as st
import google.generativeai as genai
import pandas as pd
import json
from PIL import Image
import io

# Streamlit පිටුවේ සැකසුම්
st.set_page_config(page_title="Invoice Data Extractor", layout="wide")
st.title("📄 Invoice Data to Excel Converter")

# API Key එක ඇතුළත් කිරීම (Streamlit Secrets වල මෙය තැබීම වඩාත් සුදුසුයි)
api_key = st.sidebar.text_input("AIzaSyARd94pl1WioxV4s--9VIus02l6yQuqTTI:", type="password")

if api_key:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')

    uploaded_file = st.file_uploader("Invoice රූපය මෙතැනට ලබා දෙන්න...", type=["jpg", "jpeg", "png"])

    if uploaded_file is not None:
        image = Image.open(uploaded_file)
        st.image(image, caption="Uploaded Invoice", width=400)
        
        if st.button("Extract Data"):
            with st.spinner("දත්ත ලබා ගනිමින් පවතී..."):
                # AI එකට ලබා දෙන උපදෙස් (Prompt)
                prompt = """
                Extract the following details from this invoice image and return them strictly in JSON format:
                - Invoice No
                - Delivery No
                - Items (A list of objects containing: Product Code/Description, Unit of Measure, Quantity, Net Price, Amount)
                
                Only return the JSON object.
                """
                
                response = model.generate_content([prompt, image])
                
                try:
                    # JSON දත්ත පිරිසිදු කර ගැනීම
                    json_text = response.text.replace('```json', '').replace('```', '').strip()
                    data = json.loads(json_text)
                    
                    # Header දත්ත
                    inv_no = data.get("Invoice No", "N/A")
                    del_no = data.get("Delivery No", "N/A")
                    
                    # Table දත්ත DataFrame එකකට ගැනීම
                    items_df = pd.DataFrame(data.get("Items", []))
                    
                    # අමතර දත්ත එකතු කිරීම
                    items_df.insert(0, "Invoice No", inv_no)
                    items_df.insert(1, "Delivery No", del_no)
                    
                    st.success("සාර්ථකව දත්ත ලබා ගන්නා ලදී!")
                    st.dataframe(items_df)

                    # Excel එකක් ලෙස Download කිරීමට සකස් කිරීම
                    output = io.BytesIO()
                    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                        items_df.to_excel(writer, index=False, sheet_name='InvoiceData')
                    
                    st.download_button(
                        label="Excel ගොනුව බාගත කරගන්න (Download)",
                        data=output.getvalue(),
                        file_name=f"Invoice_{inv_no}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
                    
                except Exception as e:
                    st.error(f"දත්ත සැකසීමේදී දෝෂයක් ඇති විය: {e}")
                    st.write(response.text) # දෝෂය හඳුනා ගැනීමට AI ප්‍රතිචාරය පෙන්වීම
else:
    st.warning("කරුණාකර වැඩසටහන ක්‍රියාත්මක කිරීමට Gemini API Key එකක් ඇතුළත් කරන්න.")
