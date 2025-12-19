import sys
from pathlib import Path
from docx import Document
from docx.document import Document as _Document
from docx.oxml.text.paragraph import CT_P
from docx.oxml.table import CT_Tbl
from docx.table import _Cell, Table
from docx.text.paragraph import Paragraph

def iter_block_items(parent):
    """
    Yield each paragraph and table child within *parent*, in document order.
    Each returned value is an instance of either Table or Paragraph. *parent*
    would most commonly be a reference to a main Document object, but
    also works for a _Cell object, which itself can contain paragraphs and tables.
    """
    if isinstance(parent, _Document):
        parent_elm = parent.element.body
    elif isinstance(parent, _Cell):
        parent_elm = parent._tc
    else:
        raise ValueError("something's not right")

    for child in parent_elm.iterchildren():
        if isinstance(child, CT_P):
            yield Paragraph(child, parent)
        elif isinstance(child, CT_Tbl):
            yield Table(child, parent)

def convert_table_to_md(table):
    md_lines = []
    # Get headers from first row
    headers = [cell.text.strip().replace('\n', ' ') for cell in table.rows[0].cells]
    md_lines.append("| " + " | ".join(headers) + " |")
    md_lines.append("| " + " | ".join(["---"] * len(headers)) + " |")
    
    # Get data
    for row in table.rows[1:]:
        row_data = [cell.text.strip().replace('\n', '<br>') for cell in row.cells]
        md_lines.append("| " + " | ".join(row_data) + " |")
    
    return "\n".join(md_lines)

def convert_docx_to_md(docx_path, output_path=None):
    docx_path = Path(docx_path).resolve()
    if not docx_path.exists():
        print(f"File not found: {docx_path}")
        return

    if output_path is None:
        output_path = docx_path.with_suffix('.md')
    
    print(f"Reading Docx file: {docx_path}")
    try:
        document = Document(docx_path)
        md_content = []
        
        for block in iter_block_items(document):
            if isinstance(block, Paragraph):
                text = block.text.strip()
                if not text:
                    continue
                
                style_name = block.style.name
                if 'Heading 1' in style_name:
                    md_content.append(f"# {text}")
                elif 'Heading 2' in style_name:
                    md_content.append(f"## {text}")
                elif 'Heading 3' in style_name:
                    md_content.append(f"### {text}")
                elif 'List Bullet' in style_name:
                    md_content.append(f"- {text}")
                elif 'List Number' in style_name:
                    md_content.append(f"1. {text}") # Simple approximation
                else:
                    md_content.append(text)
                
                md_content.append("") # Add newline after paragraph
                
            elif isinstance(block, Table):
                md_content.append(convert_table_to_md(block))
                md_content.append("")

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("\n".join(md_content))
            
        print(f"Converted to Markdown: {output_path}")
        
    except Exception as e:
        print(f"Error converting docx: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Default path based on user request
    # Assuming running from project root
    default_docx = Path("Docdb/中国人物画知识图谱数据结构.docx")
    if not default_docx.exists():
        # Try relative to script if running from script dir
        default_docx = Path(__file__).parent.parent / "Docdb/中国人物画知识图谱数据结构.docx"

    convert_docx_to_md(default_docx)
