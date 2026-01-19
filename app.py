import streamlit as st
import google.generativeai as genai
import pandas as pd
import json
import io
import time

# පිටුවේ සැකසුම්
st.set_page_config(page_title="Bulk Invoice Extractor", layout="wide")

# --- SIDEBAR (සැකසුම්) ---
with st.sidebar:
    st.title("⚙️ සැකසුම්")
    api_key = st.text_input("Gemini API Key එක ලබා දෙන්න:", type="password")
    st.markdown("---")
    st.info("මෙමගින් Invoice කිහිපයක් එකවර පරීක්ෂා කර තනි Excel ගොනුවක් සාදා දෙයි.")

# --- MAIN UI ---
st.title("📑 Bulk Invoice to Excel Converter")
st.write("Invoice කිහිපයක් (Images/PDFs) එකවර තෝරන්න (Select Multiple Files).")

if api_key:
    genai.configure(api_key=api_key.strip())
    model = genai.GenerativeModel('gemini-2.5-flash-lite')

    # Multiple File Uploader (මෙතැන 'accept_multiple_files=True' ලෙස සකසා ඇත)
    uploaded_files = st.file_uploader("Invoice Files තෝරන්න...", type=["jpg", "jpeg", "png", "pdf"], accept_multiple_files=True)

    if uploaded_files:
        st.success(f"ගොනු {len(uploaded_files)} ක් හඳුනා ගන්නා ලදී.")
        
        if st.button("සියලුම දත්ත ලබා ගන්න (Extract All)"):
            all_extracted_data = [] # සියලුම Invoice වල දත්ත ගබඩා කිරීමට ලැයිස්තුවක්
            
            progress_bar = st.progress(0)
            status_text = st.empty()

            for index, uploaded_file in enumerate(uploaded_files):
                status_text.text(f"කියවමින් පවතී: {uploaded_file.name} ({index+1}/{len(uploaded_files)})")
                
                try:
                    # AI Prompt
                    prompt = """
                    Extract the following from this invoice and return ONLY raw JSON:
                    - "Invoice No": string
                    - "Date": string
                    - "Vendor Name": string
                    - "Total Amount": number
                    - "Items": list of objects (Description, Quantity, Price)
                    """

                    doc_content = {
                        "mime_type": uploaded_file.type,
                        "data": uploaded_file.getvalue()
                    }

                    # AI එකෙන් Response එක ලබා ගැනීම
                    response = model.generate_content([prompt, doc_content])
                    
                    # JSON පිරිසිදු කිරීම
                    clean_json = response.text.replace('```json', '').replace('```', '').strip()
                    data = json.loads(clean_json)

                    # දත්ත වගුවකට ගැලපෙන සේ සැකසීම
                    inv_no = data.get("Invoice No", "N/A")
                    inv_date = data.get("Date", "N/A")
                    vendor = data.get("Vendor Name", "N/A")
                    
                    # Items තිබේ නම් ඒවා එකින් එක DataFrame එකට එකතු කිරීම
                    items = data.get("Items", [])
                    if items:
                        for item in items:
                            item.update({
                                "File Name": uploaded_file.name,
                                "Invoice No": inv_no,
                                "Date": inv_date,
                                "Vendor": vendor
                            })
                            all_extracted_data.append(item)
                    else:
                        # Item විස්තර නැතිනම් මූලික දත්ත පමණක් එක් කිරීම
                        all_extracted_data.append({
                            "File Name": uploaded_file.name,
                            "Invoice No": inv_no,
                            "Date": inv_date,
                            "Vendor": vendor,
                            "Total Amount": data.get("Total Amount", 0)
                        })

                    # Free API එකේ Rate Limit එක ඉක්මවා නොයෑමට තත්පරයක විරාමයක් (Optional)
                    time.sleep(1) 

                except Exception as e:
                    st.error(f"Error in {uploaded_file.name}: {e}")
                
                # Progress Bar එක යාවත්කාලීන කිරීම
                progress_bar.progress((index + 1) / len(uploaded_files))

            status_text.text("සියලුම දත්ත ලබා ගැනීම අවසන්!")

            # සම්පූර්ණ දත්ත Pandas DataFrame එකකට හැරවීම
            if all_extracted_data:
                final_df = pd.DataFrame(all_extracted_data)
                
                st.subheader("සම්පූර්ණ දත්ත වගුව")
                st.dataframe(final_df, use_container_width=True)

                # Excel ගොනුව සෑදීම
                excel_buffer = io.BytesIO()
                with pd.ExcelWriter(excel_buffer, engine='xlsxwriter') as writer:
                    final_df.to_excel(writer, index=False, sheet_name='All_Invoices')
                
                st.download_button(
                    label="📥 සියලුම දත්ත Excel ලෙස බාගත කරගන්න",
                    data=excel_buffer.getvalue(),
                    file_name="All_Invoices_Summary.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

else:
    st.warning("⚠️ කරුණාකර වම් පස ඇති Sidebar එකට API Key එක ලබා දෙන්න.")
