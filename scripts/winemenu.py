import pandas as pd
import sys
import csv
import requests
from fpdf import FPDF
from io import StringIO
from datetime import datetime

COLUMNS = {
    "country": "Country",
    "region": "Region",
    "producer": "Producer",
    "title": "Title",
    "vintage": "Vintage",
    "price": "Purchase price",
    "grape": "Main grape",
    "stock": "Stock",
    "style": "Style"
}

PRIORITY_STYLES = ["Champagne", "Sparkling", "Sekt", "Frizzante", "White", "Rose", "Red", "Port", "Dessert"]

if len(sys.argv) < 2:
    print("Error: Missing Google Sheet ID argument.")
    sys.exit(1)

sheet_id = sys.argv[1]

def download_google_sheet_as_csv(sheet_id):
    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching Google Sheet: {e}")
        return None
    
    csv_data = response.content.decode('utf-8').strip()
    if not csv_data:
        print("Error: Downloaded CSV is empty.")
        return None
    
    return csv_data

csv_data = download_google_sheet_as_csv(sheet_id)
if csv_data is None:
    sys.exit(1)

csv_io = StringIO(csv_data)

def remove_lines_until_header(csv_io, header):
    csv_io.seek(0)
    reader = csv.reader(csv_io)
    filtered_rows = []
    header_found = False

    for row in reader:
        if header in row:
            header_found = True
            filtered_rows.append(row)
        elif header_found:
            filtered_rows.append(row)
    
    if not header_found:
        print(f"Error: Header '{header}' not found in CSV.")
        return None

    output_io = StringIO()
    writer = csv.writer(output_io)
    writer.writerows(filtered_rows)
    output_io.seek(0)
    return output_io

filtered_csv_io = remove_lines_until_header(csv_io, 'Bought Quantity')
if filtered_csv_io is None:
    sys.exit(1)

df = pd.read_csv(filtered_csv_io)

missing_cols = [col for col in COLUMNS.values() if col not in df.columns]
if missing_cols:
    print(f"Error: Missing columns in CSV: {missing_cols}")
    sys.exit(1)

df = df[df[COLUMNS["stock"]] > 0]

def style_sort_key(style):
    if style in PRIORITY_STYLES:
        return (PRIORITY_STYLES.index(style), style)
    return (len(PRIORITY_STYLES), style)

df = df.sort_values(
    by=[COLUMNS["style"], COLUMNS["country"], COLUMNS["region"]],
    key=lambda col: col.map(style_sort_key) if col.name == COLUMNS["style"] else col
)

class PDF(FPDF):
    def __init__(self):
        super().__init__()
        self._current_style = None
        self._current_country = None
        self._current_region = None

    def header(self):
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, 'Wine Menu', 0, 1, 'C')

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

    def style_title(self, style):
        self.set_font('Arial', 'B', 14)
        self.cell(0, 10, style, 0, 1, 'L')
        self.ln(2)

    def chapter_title(self, country, region):
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, f'{country} - {region}', 0, 1, 'L')
        self.ln(2)

    def chapter_body(self, name, price, stock, grape):
        self.set_font('Arial', '', 12)
        self.cell(0, 10, str(name), 0, 1, 'L')
        self.set_font('Arial', 'I', 10)
        self.cell(0, 10, f'Price: {price} NOK | Stock: {stock} | Grape: {grape}', 0, 1, 'L')
        self.ln(1)

    def add_wine(self, style, country, region, producer, name, vintage, price, stock, grape):
        if self._current_style != style:
            self.style_title(style)
            self._current_style = style
            self._current_country = None
        
        if self._current_country != country or self._current_region != region:
            self.chapter_title(country, region)
            self._current_country = country
            self._current_region = region
        
        self.chapter_body(f'{producer} - {name} {vintage}', price, stock, grape)

pdf = PDF()
pdf.add_page()

for _, row in df.iterrows():
    pdf.add_wine(
        str(row[COLUMNS["style"]]), 
        str(row[COLUMNS["country"]]), 
        str(row[COLUMNS["region"]]), 
        str(row[COLUMNS["producer"]]), 
        str(row[COLUMNS["title"]]), 
        str(row[COLUMNS["vintage"]]), 
        str(row[COLUMNS["price"]]), 
        str(row[COLUMNS["stock"]]), 
        str(row[COLUMNS["grape"]])
    )

timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
output_file = f'winemenu-{timestamp}.pdf'
pdf.output(output_file)

print(f'PDF generated successfully: {output_file}')