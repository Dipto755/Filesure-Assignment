import fitz  # PyMuPDF
import json
from datetime import datetime

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

print("--------------text: ", texts)

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
            # Check the next block
            if i + 1 < len(texts):
                next_val = texts[i + 1]
                if not any(lbl.lower() in next_val.lower() for lbl in field_map.keys()):
                    data[field] = next_val.strip()
                    continue
            # Check the previous block
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
