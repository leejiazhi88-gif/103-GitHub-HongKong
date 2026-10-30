"""Validate identities, currencies, dates and broker medians before any sheet update."""
import argparse
import datetime
import json
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CURRENCIES = {'人民币': 'CNY', '港元': 'HKD', '美元': 'USD', '澳元': 'AUD',
              '加元': 'CAD', '欧元': 'EUR', '日圆': 'JPY', '日元': 'JPY'}


def number(value):
    try:
        return float(str(value).replace(',', '').replace('(', '-').replace(')', ''))
    except (ValueError, TypeError):
        return None


def validate(record, as_of):
    header = record.get('unit_header', '')
    currency = next((v for k, v in CURRENCIES.items() if k in header), None)
    identity = record.get('title', '').startswith(record['code'])
    out = []
    for forecast in record.get('forecasts', []):
        year = forecast['year']
        amount = number(forecast['profit'])
        brokers, issues = [], []
        if not identity: issues.append('证券身份未核验')
        if not currency or '百万' not in header: issues.append('预测币种/单位未列明')
        if amount is None: issues.append('纯利不是有效数字')
        for broker in record.get('brokers', []):
            if broker['year'] != year: continue
            value = number(broker['profit'])
            if value is None: continue
            try:
                date = datetime.datetime.strptime(broker['updated'], '%d/%m/%Y').date()
            except ValueError:
                issues.append('券商日期无效')
                continue
            if date > as_of:
                issues.append('券商日期晚于核验日')
                continue
            brokers.append((value, date))
        if not brokers:
            issues.append('缺可核验券商明细')
        elif amount is not None:
            median = statistics.median(v for v, d in brokers)
            if abs(median-amount) > max(.011, abs(amount)*.000001):
                issues.append('综合值与券商中位数不一致')
            if (as_of-max(d for v,d in brokers)).days > 180:
                issues.append('最近券商预测超过180天')
        out.append({'code': record['code'], 'year': year, 'profit_million_original': amount,
                    'currency': currency, 'broker_count': len(brokers), 'issues': issues,
                    'source': record.get('source'), 'usable': not issues})
    return out


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--input', type=Path, default=ROOT/'work/forecast/etnet_results.json')
    p.add_argument('--as-of', required=True, type=datetime.date.fromisoformat)
    a = p.parse_args()
    result = [v for r in json.loads(a.input.read_text()) for v in validate(r, a.as_of)]
    path = ROOT/'work/forecast/validated.json'
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result, ensure_ascii=False, indent=2))
    print(json.dumps({'annual_rows':len(result),'usable':sum(r['usable'] for r in result)},ensure_ascii=False))
