"""Read the live sheet. Save full data locally and a reviewed summary in config/."""
import collections
import datetime
import json
from feishu_client import ROOT, Sheet, arguments

p = arguments(__doc__)
p.add_argument('--update-state', action='store_true', help='Update non-sensitive summary in config/')
a = p.parse_args()
sheet = Sheet(a.env_file)
meta = sheet.metadata()
rows = []
for start in range(1, meta['grid_properties']['row_count'] + 1, 100):
    end = min(start + 99, meta['grid_properties']['row_count'])
    rows.extend(sheet.read(f'A{start}:BZ{end}'))
stocks = [r for r in rows if len(r) > 50 and isinstance(r[3], str) and r[3].endswith('.HK')]
assert len({r[3] for r in stocks}) == len(stocks), 'Duplicate codes'
assert all(isinstance(r[50], (int, float)) and r[50] >= sheet.config['threshold_hkd_100m'] for r in stocks)
assert all(r[5] == r[50] for r in stocks), 'F and AY market cap must both use HKD'
assert rows[0][5] == '市值(亿港元)'
path = ROOT / 'work/current_sheet.json'
path.parent.mkdir(exist_ok=True)
path.write_text(json.dumps(rows, ensure_ascii=False, indent=2))
state = {'verified_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
         'sheet_title': meta['title'], 'data_date': sheet.config['data_date'],
         'company_count': len(stocks), 'counts_by_category': dict(collections.Counter(r[1] for r in stocks)),
         'threshold_hkd_100m': sheet.config['threshold_hkd_100m'],
         'market_cap_unit': '亿港元', 'forecast_company_count': sum('经济通综合预测' in str(r[74]) for r in stocks),
         'sheet_url': f'https://my.feishu.cn/wiki/{sheet.config["wiki_token"]}?sheet={sheet.sid}',
         'snapshot_scope': 'API values verified; no refresh of market/financial source data'}
if a.update_state:
    (ROOT / 'config/current_state.json').write_text(json.dumps(state, ensure_ascii=False, indent=2) + '\n')
print(json.dumps(state, ensure_ascii=False, indent=2))
