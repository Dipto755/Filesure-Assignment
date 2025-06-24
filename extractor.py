import fitz  # PyMuPDF
import json
from datetime import datetime
import os
from dotenv import load_dotenv
import google.generativeai as genai


# Load environment variables
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError("❌ GEMINI_API_KEY not found in .env file!")


# Open the PDF
doc = fitz.open("Form ADT-1-29092023_signed.pdf")

# Collect all blocks
all_blocks = []
for page in doc:
    blocks = page.get_text("blocks")
    blocks.sort(key=lambda b: (round(b[1]), round(b[0])))  # top-to-bottom, then left-to-right
    all_blocks.extend(blocks)

# Extract only the text part
texts = [block[4].strip() for block in all_blocks if block[4].strip()]

# print("--------------text: ", texts)

# Define label → field map
field_map = {
    "Name of the company": "company_name",
    "Corporate identity number (CIN) of company": "cin",
    "Address of the registered office": "registered_office",
    "Date of appointment": "appointment_date",
    "Name of the auditor or auditor's firm": "auditor_name",
    "Address of the Auditor": "auditor_address",
    "Membership Number of auditor or auditor's firm's registration number": "auditor_frn_or_membership",
    "Nature of appointment": "appointment_type",
}

# Initialize result dictionary
data = {value: "" for value in field_map.values()}

# Extract values (check before and after the label block)
for i, text in enumerate(texts):
    for label, field in field_map.items():
        if label.lower() in text.lower():
            # Special handling for CIN → always take the previous block
            if field == "cin" and i - 1 >= 0:
                prev_val = texts[i - 1]
                if not any(lbl.lower() in prev_val.lower() for lbl in field_map.keys()):
                    data[field] = prev_val.strip().split("\n")[-1].strip()
                continue  # Skip rest of this iteration

            # For all other fields: check next, fallback to previous
            if i + 1 < len(texts):
                next_val = texts[i + 1]
                if not any(lbl.lower() in next_val.lower() for lbl in field_map.keys()):
                    data[field] = next_val.strip()
                    continue
            if i - 1 >= 0:
                prev_val = texts[i - 1]
                if not any(lbl.lower() in prev_val.lower() for lbl in field_map.keys()):
                    data[field] = prev_val.strip()

# Format date if needed
try:
    data["appointment_date"] = datetime.strptime(data["appointment_date"], "%d/%m/%Y").strftime("%Y-%m-%d")
except:
    pass  # leave as-is if parsing fails

# Save
with open("output.json", "w") as f:
    json.dump(data, f, indent=2)

print("✅ Structured data saved to output.json")


# Configure Gemini
genai.configure(api_key=api_key)
model = genai.GenerativeModel("gemini-2.0-flash")

# Load extracted data
with open("output.json", "r") as f:
    data = json.load(f)

# Create prompt
prompt = f"""
Generate a plain-English summary in 2 to 5 lines of the following Form ADT-1 data. Be concise and clear.
For reference here is and example: “XYZ Pvt Ltd has appointed M/s Rao & Associates as its statutory auditor for FY 2023–24, effective from 1 July 2023. The appointment has been disclosed via Form ADT-1, with all supporting documents submitted.”

Company Name: {data['company_name']}
CIN: {data['cin']}
Auditor Name: {data['auditor_name']}
Auditor FRN: {data['auditor_frn_or_membership']}
Auditor Address: {data['auditor_address']}
Appointment Date: {data['appointment_date']}
Appointment Type: {data['appointment_type']}
"""

# Generate summary
response = model.generate_content(prompt)

# Save summary
with open("summary.txt", "w") as f:
    f.write(response.text.strip())

print("✅ summary.txt generated using Gemini.")
