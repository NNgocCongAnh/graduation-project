import os
import re
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn

md_path = r"d:\Work\Đồ Án Tốt Nghiệp\docs\thesis_materials\BAO_CAO_TOT_NGHIEP_HOAN_CHINH.md"
docx_path = r"d:\Work\Đồ Án Tốt Nghiệp\BAO_CAO_TOT_NGHIEP_22010201_NguyenNgocCongAnh.docx"

doc = Document()

# Set standard A4 margins (Left 3.5cm, Right 2.0cm, Top 2.5cm, Bottom 2.5cm)
sections = doc.sections
for section in sections:
    section.page_width = Inches(8.27)
    section.page_height = Inches(11.69)
    section.left_margin = Inches(1.38)   # 3.5 cm
    section.right_margin = Inches(0.79)  # 2.0 cm
    section.top_margin = Inches(0.98)    # 2.5 cm
    section.bottom_margin = Inches(0.98) # 2.5 cm

# Configure Normal style: Times New Roman, 12pt, 1.3 line spacing
style = doc.styles['Normal']
font = style.font
font.name = 'Times New Roman'
font.size = Pt(12)
font.color.rgb = RGBColor(0x11, 0x18, 0x27)
style.paragraph_format.line_spacing = 1.3
style.paragraph_format.space_after = Pt(4)

def set_cell_background(cell, fill_hex):
    tcPr = cell._tc.get_or_add_tcPr()
    tcPr.append(parse_xml(f'<w:shd {nsdecls("w")} w:fill="{fill_hex}"/>'))

def set_cell_margins(cell, top=100, bottom=100, left=150, right=150):
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = OxmlElement('w:tcMar')
    for m, val in [('top', top), ('bottom', bottom), ('left', left), ('right', right)]:
        node = OxmlElement(f'w:{m}')
        node.set(qn('w:w'), str(val))
        node.set(qn('w:type'), 'dxa')
        tcMar.append(node)
    tcPr.append(tcMar)

with open(md_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

in_table = False
table_data = []

def flush_table():
    global in_table, table_data
    if not table_data or len(table_data) < 2:
        in_table = False
        table_data = []
        return
    
    headers = table_data[0]
    rows = table_data[1:]
    
    table = doc.add_table(rows=len(rows) + 1, cols=len(headers))
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = True
    
    # Header row
    hdr_cells = table.rows[0].cells
    for i, title in enumerate(headers):
        hdr_cells[i].text = title.strip()
        set_cell_background(hdr_cells[i], "2B5C8F")
        set_cell_margins(hdr_cells[i], 120, 120, 150, 150)
        p = hdr_cells[i].paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        for run in p.runs:
            run.font.bold = True
            run.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
            run.font.name = 'Times New Roman'
            run.font.size = Pt(11)

    # Data rows
    for r_idx, row_values in enumerate(rows):
        row_cells = table.rows[r_idx + 1].cells
        bg_col = "F8FAFC" if r_idx % 2 == 1 else "FFFFFF"
        for c_idx in range(min(len(row_values), len(headers))):
            row_cells[c_idx].text = row_values[c_idx].strip()
            set_cell_background(row_cells[c_idx], bg_col)
            set_cell_margins(row_cells[c_idx], 80, 80, 120, 120)
            p = row_cells[c_idx].paragraphs[0]
            for run in p.runs:
                run.font.name = 'Times New Roman'
                run.font.size = Pt(10.5)
                
    doc.add_paragraph() # spacing after table
    in_table = False
    table_data = []

i = 0
while i < len(lines):
    line = lines[i].rstrip()
    
    # Check table delimiter or row
    if '|' in line and not line.startswith('```'):
        parts = [p.strip() for p in line.split('|')[1:-1]]
        if all(re.match(r'^:?-+:?$', p) for p in parts if p):
            i += 1
            continue # separator line
        if parts:
            if not in_table:
                in_table = True
                table_data = []
            table_data.append(parts)
            i += 1
            continue
    else:
        if in_table:
            flush_table()
            
    if not line:
        i += 1
        continue
        
    # Headings
    if line.startswith('# '):
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(16)
        p.paragraph_format.space_after = Pt(8)
        p.paragraph_format.keep_with_next = True
        run = p.add_run(line[2:])
        run.font.bold = True
        run.font.size = Pt(18)
        run.font.color.rgb = RGBColor(0x1E, 0x3A, 0x8A) # Navy blue
    elif line.startswith('## '):
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(12)
        p.paragraph_format.space_after = Pt(6)
        p.paragraph_format.keep_with_next = True
        run = p.add_run(line[3:])
        run.font.bold = True
        run.font.size = Pt(15)
        run.font.color.rgb = RGBColor(0x1F, 0x29, 0x37)
    elif line.startswith('### '):
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(10)
        p.paragraph_format.space_after = Pt(4)
        p.paragraph_format.keep_with_next = True
        run = p.add_run(line[4:])
        run.font.bold = True
        run.font.size = Pt(13)
        run.font.color.rgb = RGBColor(0x37, 0x41, 0x51)
    elif line.startswith('#### '):
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(8)
        p.paragraph_format.space_after = Pt(2)
        p.paragraph_format.keep_with_next = True
        run = p.add_run(line[5:])
        run.font.bold = True
        run.font.size = Pt(12)
        run.font.italic = True
    elif line.startswith('---'):
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(6)
        p.paragraph_format.space_after = Pt(6)
        run = p.add_run('—' * 35)
        run.font.color.rgb = RGBColor(0x9C, 0xA3, 0xAF)
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    elif line.startswith('> '):
        p = doc.add_paragraph()
        p.paragraph_format.left_indent = Inches(0.4)
        p.paragraph_format.space_after = Pt(6)
        run = p.add_run(line[2:])
        run.font.italic = True
        run.font.color.rgb = RGBColor(0x4B, 0x55, 0x63)
    elif line.startswith('- ') or line.startswith('* '):
        p = doc.add_paragraph(style='List Bullet')
        p.paragraph_format.space_after = Pt(3)
        # Parse inline bold
        text = line[2:]
        parts = re.split(r'(\*\*.*?\*\*)', text)
        for part in parts:
            if part.startswith('**') and part.endswith('**'):
                r = p.add_run(part[2:-2])
                r.font.bold = True
            else:
                p.add_run(part)
    elif re.match(r'^\d+\.\s', line):
        p = doc.add_paragraph(style='List Number')
        p.paragraph_format.space_after = Pt(3)
        text = re.sub(r'^\d+\.\s', '', line)
        parts = re.split(r'(\*\*.*?\*\*)', text)
        for part in parts:
            if part.startswith('**') and part.endswith('**'):
                r = p.add_run(part[2:-2])
                r.font.bold = True
            else:
                p.add_run(part)
    elif line.startswith('```'):
        # Code or block
        code_lines = []
        i += 1
        while i < len(lines) and not lines[i].startswith('```'):
            code_lines.append(lines[i].rstrip())
            i += 1
        p = doc.add_paragraph()
        p.paragraph_format.left_indent = Inches(0.3)
        p.paragraph_format.right_indent = Inches(0.3)
        p.paragraph_format.space_before = Pt(4)
        p.paragraph_format.space_after = Pt(6)
        run = p.add_run('\n'.join(code_lines))
        run.font.name = 'Consolas'
        run.font.size = Pt(9.5)
        run.font.color.rgb = RGBColor(0x1F, 0x29, 0x37)
    else:
        p = doc.add_paragraph()
        parts = re.split(r'(\*\*.*?\*\*)', line)
        for part in parts:
            if part.startswith('**') and part.endswith('**'):
                r = p.add_run(part[2:-2])
                r.font.bold = True
            else:
                p.add_run(part)
    i += 1

if in_table:
    flush_table()

# Embed figures if available
figures_dir = r"d:\Work\Đồ Án Tốt Nghiệp\thesis_latex\figures"
if os.path.exists(figures_dir):
    doc.add_page_break()
    p = doc.add_paragraph()
    r = p.add_run("PHỤ LỤC: HỆ THỐNG BIỂU ĐỒ VÀ HÌNH ẢNH MINH HỌA THỰC NGHIỆM")
    r.font.bold = True
    r.font.size = Pt(16)
    r.font.color.rgb = RGBColor(0x1E, 0x3A, 0x8A)
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER

    chart_files = [
        ("corkboard_ui.png", "Hình 3.4: Giao diện Bàn điều tra Corkboard 2.5D trên Unity 6 URP"),
        ("forensic_modal.png", "Hình 3.5: Báo cáo Pháp y Khám nghiệm Thi thể Tích hợp Mô hình Henssge"),
        ("architecture_overview.png", "Hình 3.1: Kiến trúc Phân tầng Hệ thống Neuro-Symbolic"),
        ("decoupled_flowchart.png", "Hình 3.2: Sơ đồ Luồng Phân tách giữa Tầng Quy tắc và Tầng LLM"),
        ("chart_pass_rate.png", "Hình 4.1: Biểu đồ Đối sánh Tỷ lệ Hợp lệ Schema và Pass Rate Logic"),
        ("chart_latency.png", "Hình 4.2: Biểu đồ Phân bố Thời gian Phản hồi P50 và P95"),
        ("henssge_curves.png", "Hình 2.1: Đồ thị Hạ Thân nhiệt Thi thể Theo Mô hình Henssge"),
        ("bipartite_graph.png", "Hình 2.2: Sơ đồ Đồ thị Hai Phía Giữa Nghi phạm và Chứng cứ"),
        ("error_taxonomy.png", "Hình 4.3: Biểu đồ Tròn Phân bố Các Dạng Lỗi Logic Phổ biến")
    ]
    for cfile, caption in chart_files:
        cpath = os.path.join(figures_dir, cfile)
        if os.path.exists(cpath):
            p_img = doc.add_paragraph()
            p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p_img.paragraph_format.space_before = Pt(10)
            doc.add_picture(cpath, width=Inches(6.0))
            p_cap = doc.add_paragraph()
            p_cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p_cap.paragraph_format.space_after = Pt(16)
            rcap = p_cap.add_run(caption)
            rcap.font.italic = True
            rcap.font.size = Pt(10)
            rcap.font.color.rgb = RGBColor(0x4B, 0x55, 0x63)

doc.save(docx_path)
print(f"Word document generated successfully: {docx_path}")
