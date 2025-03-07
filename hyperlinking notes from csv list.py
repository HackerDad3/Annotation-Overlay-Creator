import pandas as pd
import os
import json
import re
import datetime

# Define user_email
user_email = "trial.solutions@advancediscovery.io"

# --- User Inputs for file paths ---
existing_annotation_csv_file = input("Paste CSV file path of existing annotations: ").strip().strip('"')
existing_annotation_csv_file = os.path.normpath(existing_annotation_csv_file)

regex_report_csv_file = input("Paste CSV file path of the regex report: ").strip().strip('"')
regex_report_csv_file = os.path.normpath(regex_report_csv_file)

# Output updated annotations CSV in the same folder as the existing annotations.
parent_dir = os.path.dirname(existing_annotation_csv_file)
date_prefix = datetime.datetime.now().strftime("%Y%m%d")
output_csv_file = os.path.join(parent_dir, f"{date_prefix}_updated_annotation_output.csv")

# --- User Input for which sections to include ---
# Options: referenced in / referred to / transcript / all
section_choice = input("Enter which sections to include (referenced in / referred to / transcript / all): ").strip().lower()

# Set header/footer and key_mode based on user's choice.
# For "referenced in" or "transcript", the output rows’ key will be the Matched Text.
# For "referred to", the key remains the Bates (document).
if section_choice == "referred to":
    header = "<b>Refers to:</b> <br> "
    footer = ""
    key_mode = "bates"
elif section_choice == "referenced in":
    header = "<b>Referenced In:</b> <br> "
    footer = ""
    key_mode = "matched"
elif section_choice == "transcript":
    header = "<b>Transcript:</b> <br> "
    footer = ""
    key_mode = "matched"
elif section_choice == "all":
    key_mode = "both"
    header = "<b>Referenced In:</b> <br> "
    footer = ""
else:
    header = "<b>Referenced In:</b> <br> "
    footer = " <br><b>Referenced In:</b> <br><b>Transcript:</b> <br>"
    key_mode = "both"

# --- Load existing annotation data ---
delimiter = '\t' if existing_annotation_csv_file.endswith('.txt') else ','
existing_df = pd.read_csv(existing_annotation_csv_file, delimiter=delimiter)
existing_annotations = {}
for index, row in existing_df.iterrows():
    bates = str(row['Bates/Control #']).strip()
    json_str = row['Annotation Data']
    try:
        obj = json.loads(json_str)
    except Exception:
        obj = {}
    existing_annotations[bates] = obj

# --- Load the regex report CSV ---
# Expected CSV columns: "Document", "Page", "Matched Text" (Page is 1-based)
report_df = pd.read_csv(regex_report_csv_file, delimiter=delimiter)
# Remove file extension from Document so that it matches Bates.
report_df["Document"] = report_df["Document"].apply(lambda x: os.path.splitext(str(x).strip())[0])
# Only keep rows whose Document exists in the existing annotations.
report_df = report_df[report_df["Document"].isin(existing_annotations.keys())]

# --- Aggregate new occurrences ---
# agg_ref_in: key = (bates, matched_text); value = list of occurrence strings
#   Format: "[Matched Text] is referenced in [bates] on page ####"
# agg_refers: key = bates; value = list of occurrence strings
#   Format: "[bates] refers to [Matched Text] on page ####"
agg_ref_in = {}
agg_refers = {}

for _, row in report_df.iterrows():
    bates = str(row["Document"]).strip()
    matched = str(row["Matched Text"]).strip()
    page = int(row["Page"])
    occ_ref_in = f"{matched} is referenced in {bates} on page {str(page).zfill(4)}"
    occ_refers = f"{bates} refers to {matched} on page {str(page).zfill(4)}"
    key = (bates, matched)
    if key not in agg_ref_in:
        agg_ref_in[key] = []
    if occ_ref_in not in agg_ref_in[key]:
        agg_ref_in[key].append(occ_ref_in)
    if bates not in agg_refers:
        agg_refers[bates] = []
    if occ_refers not in agg_refers[bates]:
        agg_refers[bates].append(occ_refers)

# Also, group all occurrences by Bates for merging.
agg_by_bates = {}
for _, row in report_df.iterrows():
    bates = str(row["Document"]).strip()
    matched = str(row["Matched Text"]).strip()
    page = int(row["Page"])
    occ_ref_in = f"{matched} is referenced in {bates} on page {str(page).zfill(4)}"
    occ_refers = f"{bates} refers to {matched} on page {str(page).zfill(4)}"
    if bates not in agg_by_bates:
        agg_by_bates[bates] = []
    if occ_ref_in not in agg_by_bates[bates]:
        agg_by_bates[bates].append(occ_ref_in)
    if occ_refers not in agg_by_bates[bates]:
        agg_by_bates[bates].append(occ_refers)

# --- Create updated annotation data by merging new occurrences with existing AttyNotes ---
updated_annotations = []  # list of dicts with keys: "Bates/Control #" and "Annotation Data"

for bates, existing_obj in existing_annotations.items():
    # Only update if there are new occurrences for this Bates.
    if bates not in agg_by_bates:
        continue
    # For merging new occurrences:
    if section_choice in ["referenced in", "transcript"]:
        # Use all new occurrences for this Bates from agg_by_bates (which contains both formats)
        new_occurrences = agg_by_bates.get(bates, [])
    elif section_choice == "referred to":
        new_occurrences = agg_refers.get(bates, [])
    elif section_choice == "all":
        new_occurrences = agg_by_bates.get(bates, [])
    else:
        new_occurrences = agg_by_bates.get(bates, [])
    
    if section_choice == "transcript":
        new_occurrences = [f"Transcript: {occ}" for occ in new_occurrences]
    
    # Retrieve any existing AttyNotes from the JSON.
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
    
    # Extract old occurrences from the existing AttyNotes text.
    old_occurrences = []
    if "text" in old_atty:
        txt = old_atty["text"]
        if section_choice in ["referenced in", "transcript"]:
            if txt.startswith(header) and txt.endswith(footer) and len(txt) > len(header) + len(footer):
                middle = txt[len(header):-len(footer)]
                old_occurrences = [x.strip() for x in middle.split("<br>") if x.strip()]
            elif txt:
                old_occurrences = [txt]
        elif section_choice == "referred to":
            if txt.startswith(header) and txt.endswith(footer) and len(txt) > len(header) + len(footer):
                middle = txt[len(header):-len(footer)]
                old_occurrences = [x.strip() for x in middle.split("<br>") if x.strip()]
            elif txt:
                old_occurrences = [txt]
        elif section_choice == "all":
            if txt:
                old_occurrences = [txt]
    
    merged_occurrences = list(dict.fromkeys(old_occurrences + new_occurrences))
    
    # Build new AttyNotes text.
    if section_choice in ["referenced in", "referred to", "transcript"]:
        new_atty_text = header + " <br> ".join(merged_occurrences) + footer if merged_occurrences else ""
    elif section_choice == "all":
        new_atty_text = " <br> ".join(merged_occurrences) if merged_occurrences else ""
    else:
        new_atty_text = " <br> ".join(merged_occurrences)
    
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
    
    final_obj = existing_obj.copy()
    final_obj["AttyNotes"] = json.dumps(merged_atty)
    combined_json = json.dumps(final_obj)
    
    # Produce output rows based on key_mode.
    if key_mode == "bates":
        # "referred to" mode: one row per Bates.
        updated_annotations.append({
            "Bates/Control #": bates,
            "Annotation Data": combined_json
        })
    elif key_mode == "matched":
        # "referenced in" mode: one row per unique Matched Text for this Bates.
        keys = [key for key in agg_ref_in if key[0] == bates]
        if keys:
            for key in keys:
                matched_text = key[1]
                occ_list = agg_ref_in.get(key, [])
                note_text = header + " <br> ".join(occ_list) + footer if occ_list else ""
                atty_obj_new = {
                    "text": note_text,
                    "created": int(datetime.datetime.now().timestamp() * 1000),
                    "updated": None,
                    "parentType": "Document",
                    "parentId": 0,
                    "id": 0,
                    "user": user_email,
                    "unit": "point"
                }
                temp_obj = final_obj.copy()
                temp_obj["AttyNotes"] = json.dumps(atty_obj_new)
                # Only output a row for this Matched Text if it exists in the original annotations.
                if matched_text in existing_annotations:
                    updated_annotations.append({
                        "Bates/Control #": matched_text,
                        "Annotation Data": json.dumps(temp_obj)
                    })
                else:
                    updated_annotations.append({
                        "Bates/Control #": matched_text,
                        "Annotation Data": json.dumps({"AttyNotes": json.dumps(atty_obj_new)})
                    })
        else:
            updated_annotations.append({
                "Bates/Control #": bates,
                "Annotation Data": combined_json
            })
    elif key_mode == "both":
        # Produce two rows: one keyed by Bates and one for each unique Matched Text.
        updated_annotations.append({
            "Bates/Control #": bates,
            "Annotation Data": combined_json
        })
        keys = [key for key in agg_ref_in if key[0] == bates]
        if keys:
            for key in keys:
                matched_text = key[1]
                occ_list = agg_ref_in.get(key, [])
                note_text = header + " <br> ".join(occ_list) + footer if occ_list else ""
                atty_obj_new = {
                    "text": note_text,
                    "created": int(datetime.datetime.now().timestamp() * 1000),
                    "updated": None,
                    "parentType": "Document",
                    "parentId": 0,
                    "id": 0,
                    "user": user_email,
                    "unit": "point"
                }
                temp_obj = final_obj.copy()
                temp_obj["AttyNotes"] = json.dumps(atty_obj_new)
                if matched_text in existing_annotations:
                    updated_annotations.append({
                        "Bates/Control #": matched_text,
                        "Annotation Data": json.dumps(temp_obj)
                    })
                else:
                    updated_annotations.append({
                        "Bates/Control #": matched_text,
                        "Annotation Data": json.dumps({"AttyNotes": json.dumps(atty_obj_new)})
                    })
        else:
            updated_annotations.append({
                "Bates/Control #": bates,
                "Annotation Data": json.dumps(final_obj)
            })
    else:
        updated_annotations.append({
            "Bates/Control #": bates,
            "Annotation Data": combined_json
        })

# --- Write the updated annotation CSV ---
df_updated = pd.DataFrame(updated_annotations)
df_updated.to_csv(output_csv_file, index=False, encoding='utf-8')
print(f"Updated Annotation CSV written to: {output_csv_file}")
