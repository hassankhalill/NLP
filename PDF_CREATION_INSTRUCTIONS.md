# PDF Report Creation Instructions

## Option 1: Export Jupyter Notebook to PDF (Easiest)

### Method A: Using Jupyter Interface
1. Open `NLP_ABSA_Complete_Analysis.ipynb` in Jupyter
2. Click: File → Download as → PDF via LaTeX (.pdf)
3. Wait for conversion (may take 2-3 minutes)
4. PDF will download automatically

**Note:** Requires LaTeX installation on system.

### Method B: Using Command Line
```bash
# Install nbconvert if not already installed
pip install nbconvert

# Convert notebook to PDF
jupyter nbconvert --to pdf NLP_ABSA_Complete_Analysis.ipynb

# Output: NLP_ABSA_Complete_Analysis.pdf
```

### Method C: Using nbconvert with Pandoc
```bash
# Install pandoc first
# Windows: choco install pandoc
# Or download from https://pandoc.org/installing.html

# Convert
jupyter nbconvert --to pdf NLP_ABSA_Complete_Analysis.ipynb --pdf-engine=pdflatex
```

---

## Option 2: Convert REPORT_PDF_Content.md to PDF

### Method A: Using Pandoc (Recommended)
```bash
# Install pandoc (if not installed)
# Windows: choco install pandoc
# Or download from https://pandoc.org/

# Basic conversion
pandoc REPORT_PDF_Content.md -o REPORT_Final.pdf

# With better formatting
pandoc REPORT_PDF_Content.md -o REPORT_Final.pdf --pdf-engine=pdflatex --toc --number-sections

# With custom styling
pandoc REPORT_PDF_Content.md -o REPORT_Final.pdf \
  --pdf-engine=pdflatex \
  --toc \
  --number-sections \
  --highlight-style=tango \
  -V geometry:margin=1in \
  -V fontsize=11pt
```

### Method B: Using Visual Studio Code
1. Install "Markdown PDF" extension
2. Open `REPORT_PDF_Content.md`
3. Right-click in editor → "Markdown PDF: Export (pdf)"
4. PDF saves in same directory

### Method C: Using Python (markdown2pdf)
```bash
# Install required packages
pip install markdown2pdf

# Convert
python -c "from markdown2pdf import convert; convert('REPORT_PDF_Content.md', 'REPORT_Final.pdf')"
```

### Method D: Using Online Converter
1. Go to https://www.markdowntopdf.com/
2. Upload `REPORT_PDF_Content.md`
3. Click "Convert"
4. Download PDF

---

## Option 3: Create Custom PDF with Python

```python
# Save as create_pdf_report.py

from fpdf import FPDF
import markdown

class PDFReport(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 16)
        self.cell(0, 10, 'NLP Analysis of Google Reviews - Saudi Arabian Sites', 0, 1, 'C')
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

# Read markdown content
with open('REPORT_PDF_Content.md', 'r', encoding='utf-8') as f:
    content = f.read()

# Create PDF
pdf = PDFReport()
pdf.add_page()
pdf.set_font('Arial', '', 11)

# Convert markdown sections to PDF
# (This is simplified - full implementation would parse markdown properly)
lines = content.split('\n')
for line in lines:
    if line.startswith('# '):
        pdf.set_font('Arial', 'B', 16)
        pdf.cell(0, 10, line[2:], 0, 1)
        pdf.set_font('Arial', '', 11)
    elif line.startswith('## '):
        pdf.set_font('Arial', 'B', 14)
        pdf.cell(0, 8, line[3:], 0, 1)
        pdf.set_font('Arial', '', 11)
    elif line:
        pdf.multi_cell(0, 5, line)

pdf.output('REPORT_Final.pdf')
print("PDF created: REPORT_Final.pdf")
```

Run with:
```bash
pip install fpdf
python create_pdf_report.py
```

---

## Option 4: Use Microsoft Word (Most Control)

1. **Import Markdown:**
   - Open Microsoft Word
   - Install "Writage" plugin (supports markdown import)
   - File → Open → Select `REPORT_PDF_Content.md`

2. **Or Copy/Paste:**
   - Open `REPORT_PDF_Content.md` in text editor
   - Copy all content
   - Paste into Word
   - Apply styles manually

3. **Format:**
   - Apply heading styles
   - Insert table of contents
   - Add page numbers
   - Adjust fonts and spacing
   - Insert visualizations from notebook

4. **Export to PDF:**
   - File → Save As → PDF
   - Choose "Standard" or "High Quality"
   - Check "Create bookmarks using Headings"

---

## Option 5: Combine Notebook + Report Content

### Method: Create Comprehensive PDF

1. **Export Notebook to PDF** (contains all visualizations)
2. **Create Report PDF** from `REPORT_PDF_Content.md`
3. **Merge PDFs** using:

```python
# Save as merge_pdfs.py
from PyPDF2 import PdfMerger

merger = PdfMerger()

# Add cover page (if created separately)
# merger.append('cover.pdf')

# Add notebook (has all code and visualizations)
merger.append('NLP_ABSA_Complete_Analysis.pdf')

# Add report (has detailed methodology and recommendations)
merger.append('REPORT_Final.pdf')

# Output
merger.write('COMPLETE_SUBMISSION.pdf')
merger.close()

print("Complete PDF created: COMPLETE_SUBMISSION.pdf")
```

Run with:
```bash
pip install PyPDF2
python merge_pdfs.py
```

---

## Recommended Approach

**For Assignment Submission:**

1. **Primary PDF:** Export Jupyter Notebook
   ```bash
   jupyter nbconvert --to pdf NLP_ABSA_Complete_Analysis.ipynb
   ```
   - Contains all code, visualizations, and explanations
   - Shows technical implementation
   - Demonstrates programming skills

2. **Secondary PDF (Optional but Impressive):** Create separate report
   ```bash
   pandoc REPORT_PDF_Content.md -o Executive_Report.pdf --pdf-engine=pdflatex --toc --number-sections
   ```
   - Professional executive-style report
   - Focus on findings and recommendations
   - Business-oriented presentation

3. **Submission Package:**
   - `NLP_ABSA_Complete_Analysis.pdf` (main deliverable)
   - `Executive_Report.pdf` (optional, shows extra effort)
   - All `.py` modules
   - README.md
   - Docker files

---

## Quick Commands (Copy-Paste Ready)

### If you have Jupyter installed:
```bash
cd "c:\Users\hassan.khalil\Desktop\NLP"
jupyter nbconvert --to pdf NLP_ABSA_Complete_Analysis.ipynb
```

### If you have Pandoc installed:
```bash
cd "c:\Users\hassan.khalil\Desktop\NLP"
pandoc REPORT_PDF_Content.md -o Executive_Report.pdf --pdf-engine=pdflatex --toc --number-sections
```

### If you have neither:
1. Use online converter: https://www.markdowntopdf.com/
2. Or open notebook in Jupyter and use File → Download as → PDF

---

## Troubleshooting

### Issue: "No module named 'nbconvert'"
```bash
pip install nbconvert
```

### Issue: "LaTeX not found"
```bash
# Windows
choco install miktex

# Or use HTML first, then print to PDF:
jupyter nbconvert --to html NLP_ABSA_Complete_Analysis.ipynb
# Then open HTML in browser and Print to PDF
```

### Issue: "Pandoc not found"
```bash
# Windows
choco install pandoc

# Or download installer from https://pandoc.org/installing.html
```

### Issue: Too large / images not showing
- Reduce image quality in notebook before conversion
- Use HTML intermediate: notebook → HTML → PDF via browser
- Split into multiple PDFs and merge

---

## Verification Checklist

Before submitting PDF, verify:

- [ ] All sections are present (Methodology, Findings, Recommendations)
- [ ] Visualizations are visible and clear
- [ ] Tables are formatted correctly
- [ ] Page numbers are present
- [ ] Table of contents works (clickable links)
- [ ] No text is cut off at margins
- [ ] File size is reasonable (<50MB)
- [ ] PDF opens correctly on different viewers

---

## Final Note

**Minimum Requirement (Quick):**
```bash
jupyter nbconvert --to pdf NLP_ABSA_Complete_Analysis.ipynb
```
This single command creates the required PDF report.

**Maximum Impact (Extra Effort):**
Create both notebook PDF + executive report PDF to show:
1. Technical depth (notebook)
2. Business acumen (executive report)
3. Professionalism (comprehensive submission package)

Choose based on your time constraints and grading rubric!
