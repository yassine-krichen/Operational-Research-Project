import markdown
from weasyprint import HTML, CSS
from pathlib import Path

# Read the markdown file
md_file = Path("Rapport_Inspection.md")
with open(md_file, 'r', encoding='utf-8') as f:
    md_content = f.read()

# Convert markdown to HTML
html_content = markdown.markdown(md_content, extensions=['tables', 'fenced_code'])

# Add CSS styling for better formatting
css_style = """
    body {
        font-family: 'Segoe UI', Arial, sans-serif;
        font-size: 11pt;
        line-height: 1.4;
        margin: 1.5cm 2cm;
        color: #333;
    }
    h1 {
        font-size: 18pt;
        color: #1a1a1a;
        border-bottom: 2px solid #0066cc;
        padding-bottom: 8px;
        margin-top: 0;
        margin-bottom: 12pt;
    }
    h2 {
        font-size: 14pt;
        color: #0066cc;
        margin-top: 14pt;
        margin-bottom: 8pt;
    }
    h3 {
        font-size: 12pt;
        color: #333;
        margin-top: 10pt;
        margin-bottom: 6pt;
    }
    table {
        border-collapse: collapse;
        width: 100%;
        margin: 8pt 0;
        font-size: 10pt;
    }
    th, td {
        border: 1px solid #ddd;
        padding: 4pt 6pt;
        text-align: left;
    }
    th {
        background-color: #0066cc;
        color: white;
        font-weight: bold;
    }
    tr:nth-child(even) {
        background-color: #f9f9f9;
    }
    code {
        background-color: #f4f4f4;
        padding: 2px 4px;
        border-radius: 3px;
        font-family: 'Courier New', monospace;
        font-size: 10pt;
    }
    pre {
        background-color: #f4f4f4;
        padding: 8pt;
        border-radius: 4px;
        overflow-x: auto;
        font-size: 9pt;
    }
    strong {
        color: #0066cc;
    }
    hr {
        border: none;
        border-top: 1px solid #ddd;
        margin: 10pt 0;
    }
    ul, ol {
        margin: 6pt 0;
        padding-left: 20pt;
    }
    li {
        margin: 3pt 0;
    }
    @page {
        size: A4;
        margin: 1.5cm 2cm;
    }
"""

# Create full HTML document
full_html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Planification des Inspections de Sécurité et de Qualité</title>
</head>
<body>
    {html_content}
</body>
</html>
"""

# Convert to PDF
output_pdf = "Rapport_Inspection.pdf"
HTML(string=full_html).write_pdf(
    output_pdf,
    stylesheets=[CSS(string=css_style)]
)

print(f"✅ PDF generated successfully: {output_pdf}")
