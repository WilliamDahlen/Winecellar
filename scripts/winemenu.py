import pandas as pd
import sys
import csv
import requests
from fpdf import FPDF
from io import StringIO
from datetime import datetime

sheet_id = sys.argv[1]

def download_google_sheet_as_csv(sheet_id):
    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"
    response = requests.get(url)
    
    if response.status_code == 200:
        return response.content.decode('utf-8')
    else:
        print(f"Failed to download file. HTTP Status code: {response.status_code}")
        return None

csv_data = download_google_sheet_as_csv(sheet_id)

if csv_data is None:
    sys.exit(1)

# Read the CSV data
csv_io = StringIO(csv_data)

def remove_lines_until_header(csv_io, header):
    csv_io.seek(0)  # Reset IO pointer to the beginning
    reader = csv.reader(csv_io)
    header_found = False
    filtered_rows = []

    for row in reader:
        if header_found:
            filtered_rows.append(row)
        elif row and row[0] == header:
            header_found = True
            filtered_rows.append(row)
        
    if not header_found:
        print(f"Header '{header}' not found in the file.")
        return None

    output_io = StringIO()
    writer = csv.writer(output_io)
    writer.writerows(filtered_rows)
    output_io.seek(0)
    return output_io

clean_until = 'Bought Quantity'
filtered_csv_io = remove_lines_until_header(csv_io, clean_until)

if filtered_csv_io is None:
    sys.exit(1)

df = pd.read_csv(filtered_csv_io)

# Column names based on the CSV inspection
country_col = 'Country'
region_col = 'Region'
producer_col = 'Producer'
name_col = 'Title'
vintage_col = 'Vintage'
price_col = 'Purchase price'
grape_col = 'Main grape'
stock_col = 'Stock'
style_col = 'Style'

# Filter rows with positive stock
df = df[df[stock_col] > 0]

# Sort by style, then by country and region for structured output
df = df.sort_values(by=[style_col, country_col, region_col])

class PDF(FPDF):
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
        self.cell(0, 10, f'Price: {price} | Stock: {stock} | Grape: {grape}', 0, 1, 'L')
        self.ln(1)

    def add_wine(self, style, country, region, producer, name, vintage, price, stock, grape):
        if not hasattr(self, '_current_style') or self._current_style != style:
            self.style_title(style)
            self._current_style = style
            self._current_country = None  # Reset current country and region when the style changes
        if not hasattr(self, '_current_country') or self._current_country != country or self._current_region != region:
            self.chapter_title(country, region)
            self._current_country = country
            self._current_region = region
        self.chapter_body(f'{producer} - {name} {vintage}', price, stock, grape)

# Create PDF
pdf = PDF()
pdf.add_page()

# Iterate through the DataFrame and add wines to the PDF
for index, row in df.iterrows():
    pdf.add_wine(str(row[style_col]), str(row[country_col]), str(row[region_col]), str(row[producer_col]), str(row[name_col]), str(row[vintage_col]), str(row[price_col]), str(row[stock_col]), str(row[grape_col]))

# Output the PDF to a file
timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
output_file = f'winemenu-{timestamp}.pdf'

pdf.output(output_file)

print(f'PDF generated successfully: {output_file}')