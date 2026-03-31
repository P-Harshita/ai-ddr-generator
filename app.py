import streamlit as st
import ollama
import json
import re
import time
from utils import extract_text_from_pdf, extract_images_from_pdf
from fpdf import FPDF

st.set_page_config(page_title="AI DDR Generator")
st.title("🏗️ AI DDR Report Generator (Final - Ollama)")

inspection_file = st.file_uploader("Upload Inspection Report (PDF)", type="pdf")
thermal_file = st.file_uploader("Upload Thermal Report (PDF)", type="pdf")


# 🔹 Clean JSON text
def clean_json(text):
    text = re.sub(r"#.*", "", text)
    text = re.sub(r",\s*}", "}", text)
    text = re.sub(r",\s*]", "]", text)
    return text


# 🔹 Extract JSON safely
def extract_json(text):
    try:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            cleaned = clean_json(match.group())
            return json.loads(cleaned)
        return None
    except:
        return None


# 🔹 Generate AI output
def generate_ddr_json(prompt):
    response = ollama.chat(
        model="phi3:mini",  # faster + stable
        messages=[{"role": "user", "content": prompt}]
    )
    return response["message"]["content"]


# 🔹 Generate PDF
def generate_pdf(text):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=10)

    for line in text.split("\n"):
        pdf.multi_cell(0, 8, line)

    pdf.output("DDR_Report.pdf")


if st.button("Generate DDR Report"):

    if not inspection_file or not thermal_file:
        st.warning("Upload both PDFs")
        st.stop()

    with st.spinner("⏳ Generating DDR Report... (20-40 sec)"):

        inspection_text = extract_text_from_pdf(inspection_file)
        thermal_text = extract_text_from_pdf(thermal_file)

        inspection_images = extract_images_from_pdf(inspection_file, "inspection")
        thermal_images = extract_images_from_pdf(thermal_file, "thermal")
        all_images = inspection_images + thermal_images

        combined_text = f"""
        INSPECTION REPORT:
        {inspection_text[:2500]}

        THERMAL REPORT:
        {thermal_text[:2500]}
        """

        # 🔥 FINAL PROMPT
        prompt = f"""
Return STRICT JSON ONLY.

NO comments
NO explanations
NO trailing commas

FORMAT:

{{
  "summary": "string",
  "observations": [
    {{
      "area": "string",
      "observation": "string",
      "thermal": "string",
      "image_page": 1
    }}
  ],
  "root_cause": "string",
  "severity": "string",
  "recommendations": "string",
  "notes": "string",
  "missing": "string"
}}

Rules:
- Use simple text only
- If missing → "Not Available"

DATA:
{combined_text}
"""

        start = time.time()

        raw_output = generate_ddr_json(prompt)
        data = extract_json(raw_output)

        # retry once
        if not data:
            raw_output = generate_ddr_json(prompt)
            data = extract_json(raw_output)

        end = time.time()

    st.write(f"⏱️ Time taken: {round(end-start,2)} sec")

    if not data:
        st.error("❌ AI failed. Showing raw output:")
        st.text(raw_output)
        st.stop()

    st.success("DDR Generated Successfully!")

    st.subheader("📄 DDR Report")

    # 1 Summary
    st.markdown("### 1. Property Issue Summary")
    st.write(data.get("summary", "Not Available"))

    # 2 Observations + images
    st.markdown("### 2. Area-wise Observations")

    report_text = "1. Property Issue Summary\n" + data.get("summary", "") + "\n\n2. Area-wise Observations\n"

    for obs in data.get("observations", []):
        st.markdown(f"#### 📍 {obs.get('area', 'Area')}")

        st.write("**Observation:**", obs.get("observation", "Not Available"))
        st.write("**Thermal Finding:**", obs.get("thermal", "Not Available"))

        page = obs.get("image_page")

        matched = False
        for p, img in all_images:
            if p == page:
                st.image(img, caption=f"Page {p}")
                matched = True

        if not matched:
            st.write("Image Not Available")

        report_text += f"""
Area: {obs.get('area')}
Observation: {obs.get('observation')}
Thermal: {obs.get('thermal')}
"""

    # Remaining sections
    st.markdown("### 3. Probable Root Cause")
    st.write(data.get("root_cause", "Not Available"))

    st.markdown("### 4. Severity Assessment")
    st.write(data.get("severity", "Not Available"))

    st.markdown("### 5. Recommended Actions")
    st.write(data.get("recommendations", "Not Available"))

    st.markdown("### 6. Additional Notes")
    st.write(data.get("notes", "Not Available"))

    st.markdown("### 7. Missing or Unclear Information")
    st.write(data.get("missing", "Not Available"))

    # Add to PDF
    report_text += f"""

3. Probable Root Cause
{data.get("root_cause")}

4. Severity Assessment
{data.get("severity")}

5. Recommended Actions
{data.get("recommendations")}

6. Additional Notes
{data.get("notes")}

7. Missing or Unclear Information
{data.get("missing")}
"""

    generate_pdf(report_text)

    with open("DDR_Report.pdf", "rb") as f:
        st.download_button("📥 Download DDR PDF", f, file_name="DDR_Report.pdf")