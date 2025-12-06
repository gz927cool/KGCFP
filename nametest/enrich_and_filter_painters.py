import csv
import re

def load_csv(filename):
    with open(filename, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        return list(reader)

def save_csv(data, filename, fieldnames):
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)

def is_figure_work(work_title):
    keywords = ['像', '人', '仕女', '童', '叟', '仙', '佛', '罗汉', '观音', '鬼', '神', '客', '女', '男', '僧', '道', '真', '天王', '力士', '菩萨']
    for kw in keywords:
        if kw in work_title:
            return True
    return False

def main():
    # Load data
    full_painters = load_csv('song_dynasty_painters_full.csv')
    extracted_works = load_csv('ancient_text_works_extracted.csv')
    
    # Create a dictionary for extracted works for faster lookup
    # Key: Painter Name, Value: List of works
    works_map = {}
    for row in extracted_works:
        name = row['Painter']
        works = row['Works']
        source = f"{row['Book']} 卷{row['Volume']}"
        
        if name not in works_map:
            works_map[name] = []
        works_map[name].append({'works': works, 'source': source})

    # Process full painters list
    updated_painters = []
    figure_painters = []
    
    for painter in full_painters:
        name = painter.get('Name')
        if not name:
            continue
        
        # Check if we have extracted works for this painter
        # We might need to handle partial matches or exact matches. 
        # For now, exact match on Name.
        
        extracted_info = []
        is_figure = False
        evidence = []
        
        if name in works_map:
            for entry in works_map[name]:
                extracted_info.append(f"[{entry['source']}] {entry['works']}")
                
                # Check for figure painting evidence in these works
                work_list = entry['works'].split('; ')
                for w in work_list:
                    if is_figure_work(w):
                        is_figure = True
                        evidence.append(f"Work '{w}' found in {entry['source']}")

        # Update painter record
        # We'll add a column 'Ancient_Text_Works'
        painter['Ancient_Text_Works'] = '; '.join(extracted_info)
        
        # Check if already identified as figure painter from previous steps
        # (We don't have the 'Is_Figure_Painter' column in full list usually, but let's check)
        # Actually, let's look at the figure_painters.csv to see who was already there.
        
        # If newly identified as figure painter
        if is_figure:
            painter['Is_Figure_Painter'] = 'Yes'
            painter['Figure_Painting_Evidence'] = '; '.join(evidence)
            figure_painters.append(painter)
        elif painter.get('Is_Figure_Painter') == 'Yes':
             figure_painters.append(painter)
        
        updated_painters.append(painter)

    # Save updated full list
    fieldnames = list(updated_painters[0].keys())
    if 'Ancient_Text_Works' not in fieldnames:
        fieldnames.append('Ancient_Text_Works')
    if 'Is_Figure_Painter' not in fieldnames:
        fieldnames.append('Is_Figure_Painter')
    if 'Figure_Painting_Evidence' not in fieldnames:
        fieldnames.append('Figure_Painting_Evidence')
        
    save_csv(updated_painters, 'song_dynasty_painters_enriched_v2.csv', fieldnames)
    
    # Save figure painters list (subset)
    # We might want to merge with the existing song_dynasty_figure_painters.csv to keep Wikidata info
    # But for now, let's just save this new view which focuses on Ancient Text evidence
    save_csv(figure_painters, 'song_dynasty_figure_painters_v2.csv', fieldnames)
    
    print(f"Processed {len(updated_painters)} painters.")
    print(f"Identified {len(figure_painters)} figure painters (based on ancient texts + existing flags).")

if __name__ == "__main__":
    main()
