import os
import re

def markdown_to_html(md_text: str) -> str:
    lines = md_text.splitlines()
    html_out = []
    in_table = False
    in_code = False
    in_list = False

    for line in lines:
        stripped = line.strip()

        # Code block
        if stripped.startswith("```"):
            if in_code:
                html_out.append("</code></pre>")
                in_code = False
            else:
                lang = stripped[3:].strip()
                html_out.append(f'<pre><code class="language-{lang}">')
                in_code = True
            continue

        if in_code:
            html_out.append(line.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))
            continue

        # Tables
        if "|" in line:
            if not in_table:
                html_out.append('<div class="table-wrap"><table>')
                in_table = True
            if "---" in line:
                continue  # Header divider
            parts = [p.strip() for p in line.split("|")[1:-1]]
            tag = "th" if ("Metric" in line or "Category" in line or "Timestamp" in line or "Cases" in line) else "td"
            row_html = "".join(f"<{tag}>{p}</{tag}>" for p in parts)
            html_out.append(f"<tr>{row_html}</tr>")
            continue
        else:
            if in_table:
                html_out.append("</table></div>")
                in_table = False

        # Headings
        if stripped.startswith("# "):
            html_out.append(f"<h1>{stripped[2:]}</h1>")
        elif stripped.startswith("## "):
            html_out.append(f"<h2>{stripped[3:]}</h2>")
        elif stripped.startswith("### "):
            html_out.append(f"<h3>{stripped[4:]}</h3>")
        elif stripped.startswith("---"):
            html_out.append("<hr>")
        elif stripped.startswith("- "):
            if not in_list:
                html_out.append("<ul>")
                in_list = True
            item_text = stripped[2:]
            # Format bold & inline code
            item_text = re.sub(r"\*\*(.*?)\*\*", r"<strong>\1</strong>", item_text)
            item_text = re.sub(r"`([^`]+)`", r"<code>\1</code>", item_text)
            html_out.append(f"<li>{item_text}</li>")
        else:
            if in_list and not stripped.startswith("- "):
                html_out.append("</ul>")
                in_list = False

            if stripped:
                p_text = stripped
                p_text = re.sub(r"\*\*(.*?)\*\*", r"<strong>\1</strong>", p_text)
                p_text = re.sub(r"`([^`]+)`", r"<code>\1</code>", p_text)
                p_text = re.sub(r"\[(.*?)\]\((.*?)\)", r'<a href="\2" target="_blank">\1</a>', p_text)
                html_out.append(f"<p>{p_text}</p>")

    if in_table:
        html_out.append("</table></div>")
    if in_list:
        html_out.append("</ul>")

    return "\n".join(html_out)

def create_report_html():
    report_md_path = os.path.join(os.path.dirname(__file__), "docs", "PROJECT_REPORT.md")
    report_html_path = os.path.join(os.path.dirname(__file__), "docs", "PROJECT_REPORT.html")

    with open(report_md_path, "r", encoding="utf-8") as f:
        md_content = f.read()

    body_html = markdown_to_html(md_content)

    html_template = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>OmniTech AI — Capstone Project Report</title>
  <style>
    @page {{
      size: A4;
      margin: 20mm;
    }}
    body {{
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
      color: #1e293b;
      line-height: 1.6;
      font-size: 10.5pt;
      margin: 0;
      padding: 30px;
      max-width: 900px;
      margin: 0 auto;
    }}
    h1 {{
      font-size: 20pt;
      color: #0f172a;
      border-bottom: 2px solid #e2e8f0;
      padding-bottom: 8px;
      margin-top: 0;
    }}
    h2 {{
      font-size: 14pt;
      color: #1e293b;
      border-bottom: 1px solid #e2e8f0;
      padding-bottom: 4px;
      margin-top: 24px;
    }}
    h3 {{
      font-size: 11.5pt;
      color: #334155;
      margin-top: 16px;
    }}
    p {{
      margin: 8px 0;
    }}
    ul {{
      margin: 8px 0 8px 24px;
    }}
    li {{
      margin-bottom: 4px;
    }}
    code {{
      font-family: Consolas, Monaco, "Courier New", monospace;
      background: #f1f5f9;
      padding: 2px 5px;
      border-radius: 4px;
      font-size: 9.5pt;
    }}
    pre {{
      background: #f8fafc;
      border: 1px solid #e2e8f0;
      padding: 12px;
      border-radius: 6px;
      overflow-x: auto;
      font-size: 9pt;
      line-height: 1.4;
    }}
    .table-wrap {{
      margin: 14px 0;
      overflow-x: auto;
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      font-size: 9.5pt;
    }}
    th, td {{
      border: 1px solid #cbd5e1;
      padding: 7px 10px;
      text-align: left;
    }}
    th {{
      background: #f1f5f9;
      font-weight: 600;
    }}
    tr:nth-child(even) {{
      background: #f8fafc;
    }}
    hr {{
      border: none;
      border-top: 1px solid #e2e8f0;
      margin: 20px 0;
    }}
    .print-banner {{
      background: #eff6ff;
      border: 1px solid #bfdbfe;
      color: #1e40af;
      padding: 10px 14px;
      border-radius: 6px;
      margin-bottom: 20px;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }}
    @media print {{
      .print-banner {{ display: none; }}
      body {{ padding: 0; }}
      h1, h2, h3 {{ page-break-after: avoid; }}
      table, pre {{ page-break-inside: avoid; }}
    }}
  </style>
</head>
<body>
  <div class="print-banner">
    <span>📄 <strong>Capstone Report Ready:</strong> Press <strong>Ctrl + P</strong> (or <strong>Cmd + P</strong>) in your browser and select <em>"Save as PDF"</em> to export.</span>
    <button onclick="window.print()" style="padding:6px 12px; cursor:pointer; background:#2563eb; color:#fff; border:none; border-radius:4px; font-weight:600;">Print to PDF</button>
  </div>
  {body_html}
</body>
</html>"""

    with open(report_html_path, "w", encoding="utf-8") as f:
        f.write(html_template)

    print(f"Report HTML successfully generated at: {report_html_path}")

if __name__ == "__main__":
    create_report_html()
