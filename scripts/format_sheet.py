"""Apply configured category background colors, row height and dated sheet title."""
from feishu_client import Sheet, arguments

p = arguments(__doc__)
p.add_argument('--apply', action='store_true', help='Apply; otherwise only report planned changes')
a = p.parse_args()
sheet = Sheet(a.env_file)
meta = sheet.metadata()
count = meta['grid_properties']['row_count']
before = sheet.read(f'A1:E{count}')
by_category = {k: [] for k in sheet.config['colors']}
for rn, row in enumerate(before, 1):
    if len(row) >= 4 and isinstance(row[3], str) and row[3].endswith('.HK'):
        if row[1] not in by_category:
            raise ValueError(f'Unknown category in row {rn}')
        by_category[row[1]].append(f'{sheet.sid}!A{rn}:E{rn}')
print({k: len(v) for k, v in by_category.items()})
if a.apply:
    for cat, ranges in by_category.items():
        if ranges:
            sheet.call('PUT', '/styles_batch_update', {'data': [{
                'ranges': ranges, 'style': {'backColor': sheet.config['colors'][cat]}}]})
    sheet.call('PUT', '/dimension_range', {
        'dimension': {'sheetId': sheet.sid, 'majorDimension': 'ROWS', 'startIndex': 1, 'endIndex': count},
        'dimensionProperties': {'fixedSize': sheet.config['row_height_px']}})
    sheet.call('POST', '/sheets_batch_update', {'requests': [{'updateSheet': {'properties': {
        'sheetId': sheet.sid, 'title': sheet.config['sheet_title']}}}]})
    assert sheet.read(f'A1:E{count}') == before, 'Values changed during formatting'
    assert sheet.metadata()['title'] == sheet.config['sheet_title']
    print('Formatting complete; values unchanged; title verified.')
