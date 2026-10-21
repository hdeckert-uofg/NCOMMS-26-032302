import sys
import subprocess
import importlib
import os
import tkinter as tk
from tkinter import filedialog, messagebox
import threading
import pandas as pd
import numpy as np
import shutil
import datetime
import re  



# Auto install dependencies
required_libs = ["pandas", "numpy", "openpyxl"]
for lib in required_libs:
    try:
        importlib.import_module(lib)
    except ImportError:
        subprocess.check_call([sys.executable, "-m", "pip", "install", lib])

# Define numerics
DECIMALS = 6
STEP = 10 ** (-DECIMALS)
INT_TOL = STEP / 2
NUDGE = STEP * 10

def _off_integer(x: float) -> float:
    nearest = round(x)
    if abs(x - nearest) < INT_TOL:
        x = nearest - NUDGE
    return x

def build_counter_for_shorter(current_len: int, max_len: int, decimals: int = DECIMALS):
    n_ins = max_len - current_len
    if n_ins <= 0:
        base = [float(i) for i in range(1, max_len + 1)]
        return [round(x, decimals) for x in base], []

    factor = current_len / n_ins
    inserted = []
    for k in range(1, n_ins + 1):
        pos = k * factor
        if pos >= current_len - 1e-9:
            break
        pos = _off_integer(pos)
        inserted.append(pos)

    base = [float(i) for i in range(1, current_len + 1)]
    counter = sorted(base + inserted)
    if counter[-1] != float(current_len):
        counter = [x for x in counter if x < current_len - 1e-6]
        counter.append(float(current_len))

    while len(counter) < max_len:
        counter.insert(-1, counter[-2] - 1e-6)
    if len(counter) > max_len:
        counter = counter[:max_len]

    counter = [round(x, decimals) for x in counter]
    inserted = [x for x in counter if abs(x - round(x)) > 1e-6]
    return counter, inserted


def read_excel_with_title(file_path):
    """Read Excel preserving title row separately from data"""
    titles = {}
    data_sheets = {}
    
    # Read title row (first row, no header)
    title_dfs = pd.read_excel(file_path, sheet_name=None, nrows=1, header=None)
    
    # Read data starting from row 1 (skip title, use row 1 as header)
    data_dfs = pd.read_excel(file_path, sheet_name=None, skiprows=1)
    
    for sheet_name in data_dfs.keys():
        titles[sheet_name] = title_dfs.get(sheet_name, pd.DataFrame())
        data_sheets[sheet_name] = data_dfs[sheet_name]
    
    return titles, data_sheets


def write_excel_with_title(output_path, titles, data_sheets):
    """Write Excel with title row preserved"""
    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        for sheet_name, df in data_sheets.items():
            title_df = titles.get(sheet_name, pd.DataFrame())
            
            if not title_df.empty:
                # Write title row first (no header, no index)
                title_df.to_excel(writer, sheet_name=sheet_name, index=False, header=False)
                # Write data starting from row 1 (with header, no index)
                df.to_excel(writer, sheet_name=sheet_name, index=False, startrow=1)
            else:
                # No title, just write data normally
                df.to_excel(writer, sheet_name=sheet_name, index=False)


def is_processed_file(df):
    """Check if file has already been processed (has Counter and data_N columns)"""
    if df.empty:
        return False
    
    has_counter = 'Counter' in df.columns
    has_data_cols = any(str(col).startswith('data_') for col in df.columns)
    
    return has_counter and has_data_cols


def process_sheets_dynamic(data_sheets: dict) -> dict:
    """Process raw data sheets to align columns"""
    processed = {}

    for sheet_name, df in data_sheets.items():
        # Skip if already processed
        if is_processed_file(df):
            print(f"Sheet '{sheet_name}' already processed, skipping...")
            processed[sheet_name] = df.copy()
            continue
        
        # Find numeric column headers (1, 2, 3, etc.)
        numeric_cols = [c for c in df.columns if str(c).strip().isdigit()]
        if not numeric_cols:
            continue

        # Calculate actual data length for each column (ignoring zeros and NaN)
        actual_lengths = {}
        for col in numeric_cols:
            series = pd.to_numeric(df[col], errors="coerce")
            series = series.replace(0, pd.NA)
            non_na_idx = series.dropna().index
            length = non_na_idx[-1] + 1 if len(non_na_idx) > 0 else 0
            actual_lengths[col] = length

        if not actual_lengths:
            continue

        # Find longest column
        longest_col = max(actual_lengths, key=actual_lengths.get)
        max_length = actual_lengths[longest_col]
        if max_length == 0:
            continue

        # Align all columns to max_length
        aligned_data = {}
        for col in numeric_cols:
            current_len = actual_lengths[col]
            series = pd.to_numeric(df[col].iloc[:current_len], errors="coerce")

            if col == longest_col:
                # Longest column: keep as-is, pad if needed
                data = series.copy()
                if len(data) < max_length:
                    data = pd.concat([data, pd.Series([np.nan] * (max_length - len(data)))], ignore_index=True)
                aligned_data[col] = list(data)
            else:
                # Shorter columns: insert NaN rows proportionally
                n_ins = max_length - current_len
                if current_len > 0 and n_ins > 0:
                    new_counter, _ = build_counter_for_shorter(current_len, max_length, DECIMALS)
                    new_data = []
                    data_idx = 0
                    for val in new_counter:
                        if abs(val - round(val)) < INT_TOL and data_idx < len(series):
                            new_data.append(series.iloc[data_idx])
                            data_idx += 1
                        else:
                            new_data.append(np.nan)
                    aligned_data[col] = new_data
                else:
                    aligned_data[col] = list(series) + [np.nan] * (max_length - len(series))

        # Create output DataFrame with Counter column
        output = pd.DataFrame({"Counter": range(1, max_length + 1)})
        for col in sorted(numeric_cols, key=lambda x: int(x)):
            vals = aligned_data[col]
            if len(vals) < max_length:
                vals = vals + [np.nan] * (max_length - len(vals))
            output[f"data_{col}"] = vals

        processed[sheet_name] = output

    return processed


# Averaging + formula application

def _normalize_sheet_name(name: str) -> str:
    """
    Normalize a sheet name for matching: lowercase, strip whitespace, and
    collapse '_' to '-' so 'Frame-1', 'frame-1', ' Frame-1 ', 'Frame_1'
    all normalize to the same key: 'frame-1'.
    """
    return str(name).strip().lower().replace('_', '-')


def compute_frame1_column_averages(df: pd.DataFrame) -> list:
    """
    Compute the average of each data column in the reference sheet (Frame-1),
    IN COLUMN ORDER: data_1, data_2, data_3, ... (sorted numerically by the
    column's suffix, not alphabetically).

    Zeros and NaNs are treated as padding/missing and excluded from the
    average, same convention already used elsewhere in this script.

    Returns an ORDERED list of (column_name, average) tuples.
    """
    candidates = []
    for col in df.columns:
        col_str = str(col).strip()
        if col_str.startswith('data_'):
            try:
                n = int(col_str.split('_', 1)[1])
            except ValueError:
                continue
        elif col_str.isdigit():
            n = int(col_str)
        else:
            continue
        candidates.append((n, col))

    candidates.sort(key=lambda x: x[0])  # numeric sort: 1, 2, 3, ... 10, 11...

    averages = []
    for n, col in candidates:
        numeric_col = pd.to_numeric(df[col], errors='coerce')
        numeric_col = numeric_col.replace(0, pd.NA)
        mean_val = numeric_col.mean(skipna=True)
        averages.append((col, float(mean_val) if pd.notna(mean_val) else None))

    return averages


def apply_oxdrgfp2_formula(df: pd.DataFrame, r_red_map: dict, R_ox: float, I_ratio: float) -> pd.DataFrame:
    """
    Apply the OxDrGFP2 formula to all data columns (data_1, data_2, etc.) in
    this sheet. r_red_map is keyed by COLUMN NAME (e.g. 'data_1', 'data_2'),
    derived once from Frame-1 and reused for the matching column name in
    every sheet (including Frame-1 itself).
    """
    df_result = df.copy()

    for col in df.columns:
        if str(col).startswith('data_') or (str(col).strip().isdigit() and col != 'Counter'):
            if col not in r_red_map or r_red_map[col] is None:
                print(f"No R_red available for column '{col}' "
                      f"(missing/invalid average on Frame-1); left unchanged.")
                continue

            R_red = r_red_map[col]
            numeric_col = pd.to_numeric(df[col], errors='coerce')
            df_result[col] = numeric_col.apply(
                lambda R, _R_red=R_red: (R - _R_red) / ((I_ratio * (R_ox - R)) + (R - _R_red))
                if pd.notna(R) else np.nan
            )

    return df_result


def process_single_file(file_path, output_folder):
    """Process a single Excel file"""
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = os.path.join(output_folder, f"processed_single_{ts}.xlsx")
    
    # Read with title preservation
    titles, data_sheets = read_excel_with_title(file_path)
    
    # Process sheets
    processed = process_sheets_dynamic(data_sheets)
    
    # Write with title preservation
    write_excel_with_title(output_path, titles, processed)
    
    return output_path


def merge_and_process_files(file1_path, file2_path, output_folder):
    """Merge two Excel files and process them"""
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = os.path.join(output_folder, f"merged_processed_{ts}.xlsx")
    
    # Read both files with titles
    titles1, data1 = read_excel_with_title(file1_path)
    titles2, data2 = read_excel_with_title(file2_path)
    
    all_sheets = sorted(set(data1.keys()) | set(data2.keys()))
    merged_data = {}
    merged_titles = {}

    for sheet in all_sheets:
        df1 = data1.get(sheet, pd.DataFrame()).copy()
        df2 = data2.get(sheet, pd.DataFrame()).copy()
        
        # Get titles
        t1 = titles1.get(sheet, pd.DataFrame())
        t2 = titles2.get(sheet, pd.DataFrame())

        # Remove Counter columns from both dataframes
        def drop_counter_cols(df):
            cols_to_keep = [c for c in df.columns if not str(c).strip().lower().startswith("count")]
            return df[cols_to_keep].copy() if cols_to_keep else pd.DataFrame()

        df1 = drop_counter_cols(df1)
        df2 = drop_counter_cols(df2)

        if df1.empty and df2.empty:
            continue

        # Merge side-by-side
        merged = pd.concat([df1, df2], axis=1)
        
        # Renumber columns as 1, 2, 3, etc.
        merged.columns = [str(i) for i in range(1, len(merged.columns) + 1)]
        
        merged_data[sheet] = merged
        
        # Merge titles side-by-side
        if not t1.empty or not t2.empty:
            merged_titles[sheet] = pd.concat([t1, t2], axis=1)
        else:
            merged_titles[sheet] = pd.DataFrame()

    # Process the merged data
    processed = process_sheets_dynamic(merged_data)
    
    # Write with title preservation
    write_excel_with_title(output_path, merged_titles, processed)
    
    return output_path


def apply_formula_to_file(input_file, output_folder, constants):
    """
    Apply OxDrGFP2 formula to an Excel file (processed or unprocessed).

    R_red is derived, not typed in directly:
      - User provides 'a', 'b', 'R_ox', 'I_ratio'.
      - The sheet named 'Frame-1' is the reference sheet. For each of its
        data columns (data_1, data_2, data_3, ...), compute the average.
      - R_red for column 'data_N' = a * ln(average of Frame-1's data_N) + b.
      - That R_red is then applied to the SAME-NAMED column (data_N) in
        EVERY sheet of the workbook, including Frame-1 itself.
    """
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = os.path.join(output_folder, f"calculated_{ts}.xlsx")

    titles, data_sheets = read_excel_with_title(input_file)
    sheet_names = list(data_sheets.keys())

    try:
        a_coef = float(constants.get("a"))
        b_coef = float(constants.get("b"))
        R_ox = float(constants.get("R_ox"))
        I_ratio = float(constants.get("I_ratio"))
    except (TypeError, ValueError):
        write_excel_with_title(output_path, titles, data_sheets)
        return output_path

    if not sheet_names:
        write_excel_with_title(output_path, titles, data_sheets)
        return output_path

    # Find the sheet named 'Frame-1', tolerant of case / '_' vs '-' / whitespace.
    normalized_lookup = {_normalize_sheet_name(name): name for name in data_sheets.keys()}
    reference_key = normalized_lookup.get(_normalize_sheet_name("Frame-1"))
    if reference_key is None:
        print("WARNING: no sheet matching 'Frame-1' found; "
              "cannot compute reference averages. All sheets left unchanged.")
        write_excel_with_title(output_path, titles, data_sheets)
        return output_path

    reference_df = data_sheets[reference_key]
    column_averages = compute_frame1_column_averages(reference_df)  # ordered [(col_name, avg), ...]

    # Build the per-column-name R_red map: R_red for 'data_N' = a*ln(avg_N) + b
    r_red_map = {}
    for col_name, avg in column_averages:
        if avg is None or avg <= 0:
            print(f"Reference column '{col_name}' average is not positive ({avg}); "
                  f"skipping ln() - no R_red for this column.")
            r_red_map[col_name] = None
        else:
            r_red_map[col_name] = a_coef * np.log(avg) + b_coef

    # check print
    print(f"\n=== R_red check (reference sheet: '{reference_key}') ===")
    print(f"a = {a_coef}, b = {b_coef}")
    for col_name, avg in column_averages:
        r_red = r_red_map[col_name]
        if r_red is None:
            print(f"  {col_name}: avg = N/A  ->  R_red = N/A")
        else:
            print(f"  {col_name}: avg = {avg:.6f}  ->  R_red = a*ln(avg)+b = {r_red:.6f}")
    print(f"This R_red per column is applied to that same column name (e.g. 'data_1')")
    print(f"across ALL sheets: {sheet_names}")
    print("================================================================\n")
    # end check print

    calculated = {}
    for sheet_name, df in data_sheets.items():
        calculated[sheet_name] = apply_oxdrgfp2_formula(df, r_red_map, R_ox, I_ratio)

    write_excel_with_title(output_path, titles, calculated)

    return output_path

def run_processing(input_file1, input_file2, output_folder, status_label):
    """Main processing function with decoupled operations"""
    try:
        os.makedirs(output_folder, exist_ok=True)
        output_folder = os.path.abspath(output_folder)

        mode = merge_mode_var.get()
        do_process = process_var.get()
        do_calculate = calculate_var.get()

        # Validate constants if calculation is selected
        constants = {
            "a": a_var.get(),
            "b": b_var.get(),
            "R_ox": rox_var.get(),
            "I_ratio": iratio_var.get()
        }
        constants_ok = True
        if do_calculate:
            try:
                float(constants["a"])
                float(constants["b"])
                float(constants["R_ox"])
                float(constants["I_ratio"])
            except (TypeError, ValueError):
                constants_ok = False
                messagebox.showwarning(
                    "Invalid Formula Values",
                    "Formula constants are missing or invalid.\nCalculation will be skipped."
                )

        if not do_process and not do_calculate:
            messagebox.showinfo("Nothing to Do", "Please select at least one action.")
            return

        processed_path = None

        # Proceessing and merging
        if do_process:
            if mode == "no_merge":
                if not input_file1:
                    messagebox.showwarning("Missing File", "Please select an Excel file.")
                    return
                
                status_label.config(text="Processing single file...")
                processed_path = process_single_file(input_file1, output_folder)
                messagebox.showinfo("Processing Complete", f"Processed file saved:\n{processed_path}")

            elif mode == "merge":
                if not input_file1 or not input_file2:
                    messagebox.showwarning("Missing Files", "Please select both Excel files for merging.")
                    return
                
                status_label.config(text="Merging and processing files...")
                processed_path = merge_and_process_files(input_file1, input_file2, output_folder)
                messagebox.showinfo("Merging Complete", f"Merged file saved:\n{processed_path}")

        # Calculation (can be done independently)
        if do_calculate and constants_ok:
            # Determine which file to apply formula to
            if processed_path:
                # Apply to just-processed file
                calc_input = processed_path
            else:
                # Apply to original file (calculation only mode)
                if mode == "no_merge" and input_file1:
                    calc_input = input_file1
                elif mode == "merge" and input_file1:
                    # For merge mode without processing, user should process first
                    messagebox.showwarning(
                        "No File to Calculate",
                        "Please process files first or switch to single file mode."
                    )
                    return
                else:
                    messagebox.showwarning("No File Selected", "Please select a file.")
                    return

            status_label.config(text="Applying formula...")
            calc_output = apply_formula_to_file(calc_input, output_folder, constants)
            messagebox.showinfo("Calculation Complete", f"Formula applied successfully.\nSaved as:\n{calc_output}")

        status_label.config(text="✅ All tasks complete.")

    except Exception as e:
        import traceback
        error_msg = f"An error occurred:\n{str(e)}\n\n{traceback.format_exc()}"
        messagebox.showerror("Error", error_msg)
        status_label.config(text="❌ Error occurred.")


def select_first_file():
    file_path = filedialog.askopenfilename(filetypes=[("Excel files", "*.xlsx")])
    if file_path:
        input_file1_var.set(file_path)

def select_second_file():
    file_path = filedialog.askopenfilename(filetypes=[("Excel files", "*.xlsx")])
    if file_path:
        input_file2_var.set(file_path)

def select_output_folder():
    folder = filedialog.askdirectory(title="Select Output Folder")
    if folder:
        output_path_var.set(folder)

def start_process():
    file1 = input_file1_var.get()
    file2 = input_file2_var.get()
    out_folder = output_path_var.get()
    
    if not out_folder:
        messagebox.showwarning("Missing Folder", "Please select an output folder.")
        return
    
    # Check if at least one file is selected
    mode = merge_mode_var.get()
    if mode == "merge" and (not file1 or not file2):
        messagebox.showwarning("Missing Files", "Please select both files for merge mode.")
        return
    elif mode == "no_merge" and not file1:
        messagebox.showwarning("Missing File", "Please select a file.")
        return
    
    threading.Thread(
        target=run_processing,
        args=(file1, file2, out_folder, status_label),
        daemon=True
    ).start()


# GUI Setup
root = tk.Tk()
root.title("Excel Processor & Merger")
root.geometry("620x760")
root.resizable(False, False)
root.configure(bg="#0a0f14")

# Custom Styles
ACCENT = "#00ffc3"
FG_COLOR = "#e8f0ff"
BG_DARK = "#0a0f14"
BG_FRAME = "#111820"
FONT_MAIN = ("Segoe UI", 11)
FONT_TITLE = ("Segoe UI Semibold", 16)
FONT_LABEL = ("Segoe UI", 10)

def on_enter(e):
    e.widget["background"] = ACCENT
    e.widget["foreground"] = "#000000"

def on_leave(e):
    e.widget["background"] = "#1f2937"
    e.widget["foreground"] = FG_COLOR

# Main scrollable container
main_canvas = tk.Canvas(root, bg=BG_DARK, highlightthickness=0)
scrollbar = tk.Scrollbar(root, orient="vertical", command=main_canvas.yview)
scrollable_frame = tk.Frame(main_canvas, bg=BG_DARK)

scrollable_frame.bind(
    "<Configure>",
    lambda e: main_canvas.configure(scrollregion=main_canvas.bbox("all"))
)

main_canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
main_canvas.configure(yscrollcommand=scrollbar.set)
main_canvas.pack(side="left", fill="both", expand=True)
scrollbar.pack(side="right", fill="y")

container = scrollable_frame

# Title
title = tk.Label(
    container,
    text="⚙️ Excel Processor & Merger",
    font=FONT_TITLE,
    fg=ACCENT,
    bg=BG_DARK
)
title.pack(pady=(15, 10))

subtitle = tk.Label(
    container,
    text="Align • Merge • Process • Calculate",
    font=("Segoe UI", 10, "italic"),
    fg="#9aa6b2",
    bg=BG_DARK
)
subtitle.pack(pady=(0, 10))

# Mode selection
merge_mode_var = tk.StringVar(value="no_merge")
mode_frame = tk.LabelFrame(
    container,
    text="File Mode",
    padx=10, pady=5,
    bg=BG_FRAME, fg=ACCENT, font=FONT_LABEL
)
mode_frame.pack(pady=8, fill="x", padx=20)

tk.Radiobutton(
    mode_frame,
    text="Single File Mode (process one file)",
    variable=merge_mode_var, value="no_merge",
    bg=BG_FRAME, fg=FG_COLOR,
    selectcolor=BG_DARK, activebackground=BG_FRAME
).pack(anchor="w")

tk.Radiobutton(
    mode_frame,
    text="Merge Mode (combine two files)",
    variable=merge_mode_var, value="merge",
    bg=BG_FRAME, fg=FG_COLOR,
    selectcolor=BG_DARK, activebackground=BG_FRAME
).pack(anchor="w")

# Independent Action Selection
process_var = tk.BooleanVar(value=True)
calculate_var = tk.BooleanVar(value=False)

action_frame = tk.LabelFrame(
    container,
    text="Select Actions (Independent)",
    padx=10, pady=5,
    bg=BG_FRAME, fg=ACCENT, font=FONT_LABEL
)
action_frame.pack(pady=8, fill="x", padx=20)

tk.Checkbutton(
    action_frame,
    text="Process / Merge Files (align columns)",
    variable=process_var,
    bg=BG_FRAME, fg=FG_COLOR,
    selectcolor=BG_DARK, activebackground=BG_FRAME
).pack(anchor="w")

tk.Checkbutton(
    action_frame,
    text="Apply OxDrGFP2 Formula (can be done separately)",
    variable=calculate_var,
    bg=BG_FRAME, fg=FG_COLOR,
    selectcolor=BG_DARK, activebackground=BG_FRAME
).pack(anchor="w")

# Formula coefficients (a, b)
formula_frame = tk.LabelFrame(
    container,
    text="OxDrGFP2 Formula Constants",
    padx=10, pady=8,
    bg=BG_FRAME, fg=ACCENT, font=FONT_LABEL
)
formula_frame.pack(pady=8, fill="x", padx=20)

tk.Label(
    formula_frame,
    text="a:",
    bg=BG_FRAME, fg=FG_COLOR
).grid(row=0, column=0, sticky="e", padx=5, pady=3)
a_var = tk.StringVar()
tk.Entry(
    formula_frame,
    textvariable=a_var, width=15,
    bg="#1c2530", fg=FG_COLOR,
    insertbackground=FG_COLOR, relief="flat"
).grid(row=0, column=1, padx=5, pady=3)

tk.Label(
    formula_frame,
    text="b:",
    bg=BG_FRAME, fg=FG_COLOR
).grid(row=1, column=0, sticky="e", padx=5, pady=3)
b_var = tk.StringVar()
tk.Entry(
    formula_frame,
    textvariable=b_var, width=15,
    bg="#1c2530", fg=FG_COLOR,
    insertbackground=FG_COLOR, relief="flat"
).grid(row=1, column=1, padx=5, pady=3)

tk.Label(
    formula_frame,
    text="R_ox:",
    bg=BG_FRAME, fg=FG_COLOR
).grid(row=2, column=0, sticky="e", padx=5, pady=3)
rox_var = tk.StringVar()
tk.Entry(
    formula_frame,
    textvariable=rox_var, width=15,
    bg="#1c2530", fg=FG_COLOR,
    insertbackground=FG_COLOR, relief="flat"
).grid(row=2, column=1, padx=5, pady=3)

tk.Label(
    formula_frame,
    text="I_ratio (I_456min / I_456max):",
    bg=BG_FRAME, fg=FG_COLOR
).grid(row=3, column=0, sticky="e", padx=5, pady=3)
iratio_var = tk.StringVar()
tk.Entry(
    formula_frame,
    textvariable=iratio_var, width=15,
    bg="#1c2530", fg=FG_COLOR,
    insertbackground=FG_COLOR, relief="flat"
).grid(row=3, column=1, padx=5, pady=3)

tk.Label(
    formula_frame,
    text="R_red = a·ln(avg) + b, computed per column from Sheet 1",
    font=("Segoe UI", 8, "italic"),
    fg="#9aa6b2", bg=BG_FRAME
).grid(row=4, column=0, columnspan=2, pady=(6, 2))

# File Selection
frame = tk.LabelFrame(
    container,
    text="Files & Output",
    padx=10, pady=10,
    bg=BG_FRAME, fg=ACCENT, font=FONT_LABEL
)
frame.pack(pady=8, fill="x", padx=20)

input_file1_var = tk.StringVar()
input_file2_var = tk.StringVar()
output_path_var = tk.StringVar()

def style_button(btn):
    btn.config(
        bg="#1f2937", fg=FG_COLOR,
        relief="flat", font=FONT_MAIN,
        activebackground=ACCENT, activeforeground="#000"
    )
    btn.bind("<Enter>", on_enter)
    btn.bind("<Leave>", on_leave)

tk.Label(frame, text="First Excel File:", bg=BG_FRAME, fg=FG_COLOR).grid(
    row=0, column=0, sticky="e", padx=5, pady=5
)
tk.Entry(
    frame, textvariable=input_file1_var, width=45,
    bg="#1c2530", fg=FG_COLOR,
    insertbackground=FG_COLOR, relief="flat"
).grid(row=0, column=1, padx=5)
btn1 = tk.Button(frame, text="Browse", command=select_first_file)
style_button(btn1)
btn1.grid(row=0, column=2, padx=5)

tk.Label(frame, text="Second Excel File:", bg=BG_FRAME, fg=FG_COLOR).grid(
    row=1, column=0, sticky="e", padx=5, pady=5
)
tk.Entry(
    frame, textvariable=input_file2_var, width=45,
    bg="#1c2530", fg=FG_COLOR,
    insertbackground=FG_COLOR, relief="flat"
).grid(row=1, column=1, padx=5)
btn2 = tk.Button(frame, text="Browse", command=select_second_file)
style_button(btn2)
btn2.grid(row=1, column=2, padx=5)

tk.Label(frame, text="Output Folder:", bg=BG_FRAME, fg=FG_COLOR).grid(
    row=2, column=0, sticky="e", padx=5, pady=5
)
tk.Entry(
    frame, textvariable=output_path_var, width=45,
    bg="#1c2530", fg=FG_COLOR,
    insertbackground=FG_COLOR, relief="flat"
).grid(row=2, column=1, padx=5)
btn3 = tk.Button(frame, text="Browse", command=select_output_folder)
style_button(btn3)
btn3.grid(row=2, column=2, padx=5)

# Start Button
start_btn = tk.Button(
    container,
    text="▶ Start Processing",
    command=start_process,
    width=25, height=1,
    font=("Segoe UI", 12, "bold")
)
style_button(start_btn)
start_btn.pack(pady=20)

# Status Label
status_label = tk.Label(
    container,
    text="Ready to process...",
    fg="#9aa6b2", bg=BG_DARK,
    font=("Segoe UI", 10)
)
status_label.pack(pady=5)

root.mainloop()