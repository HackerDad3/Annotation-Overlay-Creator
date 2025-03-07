import pandas as pd
import os
import json
import re
import datetime

# Define user_email at the top
user_email = "trial.solutions@advancediscovery.io"

# --- User Inputs for file paths ---
existing_annotation_csv_file = input("Paste CSV file path of existing annotations: ").strip().strip('"')
existing_annotation_csv_file = os.path.normpath(existing_annotation_csv_file)

regex_report_csv_file = input("Paste CSV file path of the regex report: ").strip().strip('"')
regex_report_csv_file = os.path.normpath(regex_report_csv_file)

# We'll output the updated annotations CSV in the same folder as the existing annotations.
parent_dir = os.path.dirname(existing_annotation_csv_file)
date_prefix = datetime.datetime.now().strftime("%Y%m%d")
output_csv_file = os.path.join(parent_dir, f"{date_prefix}_updated_annotation_output.csv")

# --- User Input for which sections to include ---
# Options: referenced in / referred to / transcript / all
section_choice = input("Enter which sections to include (referenced in / referred to / transcript / all): ").strip().lower()

if section_choice == "referred to":
    header = "<b>Refers to:</b> <br> "
    footer = ""
elif section_choice == "referenced in":
    header = "<b>Referenced In:</b> <br> "
    footer = ""
elif section_choice == "transcript":
    header = "<b>Transcript:</b> <br> "
    footer = ""
elif section_choice == "all":
    header = "<b>Refers to:</b> <br> "
    footer = " <br><b>Referenced In:</b> <br><b>Transcript:</b> <br>"
else:
    # Default to all if invalid input
    header = "<b>Refers to:</b> <br> "
    footer = " <br><b>Referenced In:</b> <br><b>Transcript:</b> <br>"

# --- Load existing annotation data ---
# Expected CSV columns: "Bates/Control #" and "Annotation Data"
delimiter = '\t' if existing_annotation_csv_file.endswith('.txt') else ','
existing_df = pd.read_csv(existing_annotation_csv_file, delimiter=delimiter)

# Create a dictionary mapping Bates to the parsed JSON from "Annotation Data"
existing_annotations = {}
for index, row in existing_df.iterrows():
    bates = str(row['Bates/Control #'])
    json_str = row['Annotation Data']
    try:
        obj = json.loads(json_str)
    except Exception:
        obj = {}
    existing_annotations[bates] = obj

# --- Load the regex report CSV ---
# Expected CSV columns: "Bates/Control #", "Found Text", "Page" (Page is 1-based)
report_df = pd.read_csv(regex_report_csv_file, delimiter=delimiter)

# --- Aggregate new occurrences per Bates ---
# Each occurrence is formatted as "Found Text at ####"
agg_occurrences = {}
for _, row in report_df.iterrows():
    bates = str(row['Bates/Control #'])
    found_text = row['Found Text']
    page = row['Page']
    occ = f"{found_text} at {str(int(page)).zfill(4)}"
    if bates not in agg_occurrences:
        agg_occurrences[bates] = []
    if occ not in agg_occurrences[bates]:
        agg_occurrences[bates].append(occ)

# --- Create updated annotation data by merging new occurrences with existing AttyNotes ---
updated_annotations = []  # list of dicts with keys: "Bates/Control #" and "Annotation Data"

# Loop through each Bates from the existing annotations
for bates, existing_obj in existing_annotations.items():
    # Get new occurrences for this Bates from the regex report
    new_occurrences = agg_occurrences.get(bates, [])
    
    # Get any existing AttyNotes from the existing annotation JSON.
    # We expect the AttyNotes key to be stored as a JSON string.
    old_atty = {}
    if "AttyNotes" in existing_obj:
        atty_value = existing_obj["AttyNotes"]
        if isinstance(atty_value, str):
            try:
                old_atty = json.loads(atty_value)
            except Exception:
                old_atty = {}
        elif isinstance(atty_value, dict):
            old_atty = atty_value
    
    # Extract old occurrences from the existing AttyNotes text, if available.
    old_occurrences = []
    if "text" in old_atty:
        txt = old_atty["text"]
        if txt.startswith(header) and txt.endswith(footer):
            middle = txt[len(header):-len(footer)]
            old_occurrences = [x.strip() for x in middle.split("<br>") if x.strip()]
        elif txt:
            old_occurrences = [txt]
    
    # Merge new and old occurrences without duplicates.
    merged_occurrences = list(dict.fromkeys(old_occurrences + new_occurrences))
    
    # Build the new AttyNotes text using the header and footer.
    if merged_occurrences:
        new_atty_text = header + " <br> ".join(merged_occurrences) + footer
    else:
        new_atty_text = ""
    
    # Create a new AttyNotes object.
    merged_atty = {
        "text": new_atty_text,
        "created": old_atty.get("created", int(datetime.datetime.now().timestamp() * 1000)),
        "updated": None,
        "parentType": "Document",
        "parentId": 0,
        "id": 0,
        "user": user_email,
        "unit": "point"
    }
    
    # Create a copy of the existing annotation JSON and update (or add) the AttyNotes key.
    final_obj = existing_obj.copy()
    final_obj["AttyNotes"] = json.dumps(merged_atty)
    
    # Save the updated data for this Bates.
    updated_annotations.append({
        "Bates/Control #": bates,
        "Annotation Data": json.dumps(final_obj)
    })

# --- Write the updated annotation CSV ---
df_updated = pd.DataFrame(updated_annotations)
df_updated.to_csv(output_csv_file, index=False, encoding='utf-8')
print(f"Updated Annotation CSV written to: {output_csv_file}")
