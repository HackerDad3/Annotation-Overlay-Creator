import os
import re
import json
import pandas as pd

def parse_annotation_data(annotation_str, user_filter=None, note_regex=None):
    """
    Get a list of highlights from the annotation JSON string.
    If "Highlights" is a string, split it by '\u0013'.
    If a user_filter (list of usernames) is given, only return highlights whose "user" is in that list.
    If note_regex is provided, only return highlights where at least one note's text matches the regex.
    """
    try:
        annotation = json.loads(annotation_str)
    except Exception as e:
        print("Error parsing annotation JSON:", e)
        return []
    
    highlights = []
    if "Highlights" in annotation:
        hl_data = annotation["Highlights"]
        if isinstance(hl_data, str):
            parts = hl_data.split('\u0013')
            for part in parts:
                part = part.strip()
                if part:
                    try:
                        hl = json.loads(part)
                        highlights.append(hl)
                    except Exception as e:
                        print("Error parsing a highlight JSON part:", e)
        elif isinstance(hl_data, list):
            highlights = hl_data

    if user_filter is not None:
        if isinstance(user_filter, list):
            highlights = [hl for hl in highlights if hl.get("user") in user_filter]
        else:
            highlights = [hl for hl in highlights if hl.get("user") == user_filter]

    if note_regex is not None:
        pattern = re.compile(note_regex)
        highlights = [hl for hl in highlights if any(pattern.search(str(note.get("text", ""))) for note in hl.get("notes", []) if isinstance(note, dict))]
    
    return highlights

def canonicalize_highlight(hl):
    """
    Create a simple JSON string for the highlight using:
      - Rectangles (x, y, width, height) from "rectangles" or "rectangle"
      - Marked text from "markedText"
      - Notes text from "notes"
      - Page number from "pageNum" (if not found at top level, try inside "rectangles")
    Sorting is applied so order doesn't matter.
    """
    rects = []
    rect_data = hl.get("rectangles") or hl.get("rectangle")
    if rect_data:
        if isinstance(rect_data, dict):
            if "rectangles" in rect_data and isinstance(rect_data["rectangles"], list):
                for item in rect_data["rectangles"]:
                    if isinstance(item, dict):
                        x = item.get("x")
                        y = item.get("y")
                        width = item.get("width")
                        height = item.get("height")
                        rects.append({"x": x, "y": y, "width": width, "height": height})
            else:
                x = rect_data.get("x")
                y = rect_data.get("y")
                width = rect_data.get("width")
                height = rect_data.get("height")
                if x is not None and y is not None:
                    rects.append({"x": x, "y": y, "width": width, "height": height})
        elif isinstance(rect_data, list):
            for item in rect_data:
                if isinstance(item, dict):
                    x = item.get("x")
                    y = item.get("y")
                    width = item.get("width")
                    height = item.get("height")
                    rects.append({"x": x, "y": y, "width": width, "height": height})
    rects_sorted = sorted(rects, key=lambda r: (r.get("x", 0), r.get("y", 0), r.get("width", 0), r.get("height", 0)))
    
    marked_text = hl.get("markedText", "")
    if marked_text is None:
        marked_text = ""
    else:
        marked_text = str(marked_text).strip()
    
    notes = []
    notes_list = hl.get("notes", [])
    if isinstance(notes_list, list):
        notes = [str(note.get("text", "")).strip() for note in notes_list if isinstance(note, dict)]
    notes_sorted = sorted(notes)
    
    page_num = hl.get("pageNum")
    if page_num is None and "rectangles" in hl and isinstance(hl["rectangles"], dict):
        page_num = hl["rectangles"].get("pageNum")
    
    canon = {
        "rects": rects_sorted,
        "markedText": marked_text,
        "notes": notes_sorted,
        "pageNum": page_num
    }
    return json.dumps(canon, sort_keys=True)

def match_highlights(master_list, csv2_list):
    """
    Compare two lists (each a list of (canonical, original) tuples) for a row.
    Return two lists:
      - missing: items in master_list not found in csv2_list
      - extra: items in csv2_list not found in master_list
    """
    missing = []
    csv2_copy = csv2_list.copy()
    for (canon, orig) in master_list:
        found_index = None
        for i, (canon2, orig2) in enumerate(csv2_copy):
            if canon == canon2:
                found_index = i
                break
        if found_index is None:
            missing.append((canon, orig))
        else:
            del csv2_copy[found_index]
    extra = csv2_copy
    return missing, extra

def update_annotation_data(original_annotation, missing_highlights, delimiter='\u0013'):
    """
    Update the original annotation JSON (from CSV2 unfiltered) by adding the missing highlights.
    Preserve the original format (string with delimiter or list) of "Highlights".
    """
    try:
        ann_obj = json.loads(original_annotation)
    except Exception as e:
        print("Error parsing annotation data for update:", e)
        return original_annotation
    if "Highlights" not in ann_obj:
        ann_obj["Highlights"] = missing_highlights
    else:
        orig_val = ann_obj["Highlights"]
        if isinstance(orig_val, str):
            parts = orig_val.split(delimiter)
            orig_highlights = []
            for part in parts:
                part = part.strip()
                if part:
                    try:
                        hl = json.loads(part)
                        orig_highlights.append(hl)
                    except Exception as e:
                        print("Error parsing existing highlight:", e)
            new_highlights = orig_highlights + missing_highlights
            new_highlights_str = delimiter.join(json.dumps(hl, ensure_ascii=False) for hl in new_highlights)
            ann_obj["Highlights"] = new_highlights_str
        elif isinstance(orig_val, list):
            new_highlights = orig_val + missing_highlights
            ann_obj["Highlights"] = new_highlights
    return json.dumps(ann_obj, ensure_ascii=False)

def get_readable_fields(hl):
    """
    Return a dict with just the fields for the report:
      - Page Number (from pageNum, plus 1 for human readability),
      - Highlighted Text (from markedText),
      - Notes,
      - Username.
    If pageNum is not at the top level, try checking inside "rectangles".
    """
    page = hl.get("pageNum")
    if page is None and "rectangles" in hl and isinstance(hl["rectangles"], dict):
        page = hl["rectangles"].get("pageNum")
    if page is None:
        page_val = ""
    else:
        try:
            page_val = int(page) + 1
        except (ValueError, TypeError):
            page_val = page

    marked_text = hl.get("markedText", "")
    if marked_text is None:
        marked_text = ""
    else:
        marked_text = str(marked_text).strip()
    
    notes_list = hl.get("notes", [])
    notes = ""
    if isinstance(notes_list, list):
        notes = ", ".join(str(note.get("text", "")).strip() for note in notes_list if isinstance(note, dict))
    user = hl.get("user", "")
    return {
        "Page Number": page_val,
        "Highlighted Text": marked_text,
        "Notes": notes,
        "Username": user
    }

def read_key_file(key_filepath):
    """
    Read the key CSV file (the edited differences report) and build a dictionary
    mapping each identifier to a list of annotation JSON strings to add.
    The key CSV is expected to have at least two columns: "Identifier" and "Annotation".
    """
    try:
        df_key = pd.read_csv(key_filepath, encoding='utf-8')
    except Exception as e:
        print("Error reading key file:", e)
        return {}
    
    key_dict = {}
    for index, row in df_key.iterrows():
        ident = row.get("Identifier")
        annotation = row.get("Annotation")
        if pd.notna(ident) and pd.notna(annotation):
            annotation_str = str(annotation)
            if ident in key_dict:
                key_dict[ident].append(annotation_str)
            else:
                key_dict[ident] = [annotation_str]
    return key_dict

def main():
    # Get file paths for master (CSV1) and CSV2.
    master_csv = input("Enter the file path for the master (CSV1) annotations CSV: ").strip().strip('"')
    master_csv = os.path.normpath(master_csv)
    csv2_path = input("Enter the file path for CSV2 annotations CSV: ").strip().strip('"')
    csv2_path = os.path.normpath(csv2_path)
    
    # Ask if we want to filter on username. If yes, get comma-separated usernames.
    filter_choice = input("Do you want to filter on username? (y/n): ").strip().lower()
    if filter_choice == 'y':
        username_input = input("Enter the username(s) (comma separated): ").strip()
        username_filter = [u.strip() for u in username_input.split(",") if u.strip()]
    else:
        username_filter = None

    # Ask if we want to filter on note pattern. If yes, get a regex.
    note_filter_choice = input("Do you want to filter on note pattern? (y/n): ").strip().lower()
    if note_filter_choice == 'y':
        note_regex = input("Enter the regex pattern for notes: ").strip()
    else:
        note_regex = None

    try:
        df_master = pd.read_csv(master_csv, encoding='utf-8')
        df_csv2 = pd.read_csv(csv2_path, encoding='utf-8')
    except Exception as e:
        print("Error reading CSV files:", e)
        return
    
    if "Annotation Data" not in df_master.columns or "Annotation Data" not in df_csv2.columns:
        print("One or both CSV files are missing the 'Annotation Data' column.")
        return
    
    # Use "Bates/Control #" as identifier if available; otherwise, use row index.
    id_col = "Bates/Control #"
    if id_col not in df_master.columns or id_col not in df_csv2.columns:
        print(f"Identifier column '{id_col}' not found. Using row index.")
        id_col = None

    # Build dictionaries mapping each row's identifier to its filtered highlights.
    master_dict = {}
    for idx, row in df_master.iterrows():
        identifier = row[id_col] if id_col else idx
        ann_str = row.get("Annotation Data")
        highlights = []
        if pd.notna(ann_str):
            highlights = parse_annotation_data(ann_str, user_filter=username_filter, note_regex=note_regex)
        hl_list = []
        for hl in highlights:
            canon = canonicalize_highlight(hl)
            hl_list.append((canon, hl))
        master_dict[identifier] = hl_list

    csv2_dict = {}
    for idx, row in df_csv2.iterrows():
        identifier = row[id_col] if id_col else idx
        ann_str = row.get("Annotation Data")
        highlights = []
        if pd.notna(ann_str):
            highlights = parse_annotation_data(ann_str, user_filter=username_filter, note_regex=note_regex)
        hl_list = []
        for hl in highlights:
            canon = canonicalize_highlight(hl)
            hl_list.append((canon, hl))
        csv2_dict[identifier] = hl_list

    # Compare the filtered highlights between CSV1 and CSV2.
    diff_results = []
    fix_missing = {}  # Store missing highlights (from master) to add to CSV2.
    
    for identifier, master_hl_list in master_dict.items():
        if identifier not in csv2_dict:
            for (canon, orig) in master_hl_list:
                details = get_readable_fields(orig)
                details["Annotation"] = json.dumps(orig, ensure_ascii=False)
                diff_results.append({
                    "Identifier": identifier,
                    "Issue": "Row missing in CSV2",
                    **details
                })
        else:
            csv2_hl_list = csv2_dict[identifier]
            missing, _ = match_highlights(master_hl_list, csv2_hl_list)
            if missing:
                fix_missing[identifier] = [json.dumps(orig, ensure_ascii=False) for (canon, orig) in missing]
            for (canon, orig) in missing:
                details = get_readable_fields(orig)
                details["Annotation"] = json.dumps(orig, ensure_ascii=False)
                diff_results.append({
                    "Identifier": identifier,
                    "Issue": "Missing (in CSV2)",
                    **details
                })
    # We ignore extra items in CSV2.
    
    # Write out the differences report.
    if diff_results:
        diff_df = pd.DataFrame(diff_results)
        report_filepath = os.path.join(os.path.dirname(master_csv), "AnnotationDiffReport.csv")
        diff_df.to_csv(report_filepath, index=False, encoding='utf-8')
        print("Diff report saved to:", report_filepath)
    else:
        print("No differences found.")
    
    # Ask if the user wants to supply an edited key file.
    key_choice = input("Do you want to use an edited key file for corrections? (y/n): ").strip().lower()
    if key_choice == 'y':
        key_filepath = input("Enter the file path for the key CSV file: ").strip().strip('"')
        key_filepath = os.path.normpath(key_filepath)
        key_dict = read_key_file(key_filepath)
        fix_missing = key_dict
        print("Using key file for corrections.")
    else:
        print("Using all missing highlights for corrections.")
    
    # Ask if the user wants to fix CSV2.
    if diff_results:
        fix_choice = input("Do you want to fix the differences in CSV2? (y/n): ").strip().lower()
        if fix_choice == 'y':
            df_csv2_fixed = df_csv2.copy()
            for idx, row in df_csv2_fixed.iterrows():
                row_id = row[id_col] if id_col else idx
                if row_id in fix_missing:
                    original_annotation = row["Annotation Data"]
                    missing_highlights = [json.loads(a) for a in fix_missing[row_id]]
                    updated_annotation = update_annotation_data(original_annotation, missing_highlights)
                    df_csv2_fixed.at[idx, "Annotation Data"] = updated_annotation
            fix_filepath = os.path.join(os.path.dirname(csv2_path), "CSV2_Fixed.csv")
            df_csv2_fixed.to_csv(fix_filepath, index=False, encoding='utf-8')
            print("Fixed CSV2 saved to:", fix_filepath)

if __name__ == '__main__':
    main()
