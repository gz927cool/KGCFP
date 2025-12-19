import pandas as pd
import os
from pathlib import Path

def convert_xlsx_to_csv(xlsx_path, output_dir=None):
    xlsx_path = Path(xlsx_path).resolve()
    if not xlsx_path.exists():
        print(f"File not found: {xlsx_path}")
        return

    if output_dir is None:
        output_dir = xlsx_path.parent / (xlsx_path.stem + "_csvs")
    
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Reading Excel file: {xlsx_path}")
    try:
        # Read all sheets
        xls = pd.ExcelFile(xlsx_path)
        for sheet_name in xls.sheet_names:
            print(f"Processing sheet: {sheet_name}")
            df = pd.read_excel(xls, sheet_name=sheet_name)
            
            # Sanitize sheet name for filename
            safe_name = "".join([c if c.isalnum() or c in (' ', '_', '-') else '_' for c in sheet_name]).strip()
            csv_path = output_dir / f"{safe_name}.csv"
            
            df.to_csv(csv_path, index=False, encoding='utf-8-sig')
            print(f"Saved to: {csv_path}")
            
        print(f"All sheets converted. Output directory: {output_dir}")
        
    except Exception as e:
        print(f"Error converting xlsx: {e}")

if __name__ == "__main__":
    # Default path based on user request
    # Assuming running from project root
    default_xlsx = Path("Docdb/ACCESSIBLE_DB.xlsx")
    if not default_xlsx.exists():
        # Try relative to script if running from script dir
        default_xlsx = Path(__file__).parent.parent / "Docdb/ACCESSIBLE_DB.xlsx"
        
    convert_xlsx_to_csv(default_xlsx)
