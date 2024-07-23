# Winecellar

Use this repository to create a PDF in the style of a winemenu from a Google Sheet.

The pipeline takes a google sheet id as input. The google sheet must be shared with anonymous read access to anyone with the link.
After the PDF is generated, it is commited in the root directory with the name `winemenu-{datetime}.pdf`.


Local usage:
```bash
pip install -r requirements.txt
python3 scripts/winemenu.py {sheet_id}
PDF generated successfully: winemenu-{datetime}.pdf
```

See this [Google Sheet template](https://docs.google.com/spreadsheets/d/1CCW7SGLAcLqTrh_vO-J_kypsePX1WYj682pjJodXAog/edit?usp=sharing) for the winecellar it is based on.