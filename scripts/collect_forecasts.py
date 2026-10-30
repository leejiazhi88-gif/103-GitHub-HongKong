"""AKShare ET Net provider path for HK annual profit forecasts.
Source reference: akfamily/akshare stock_hk_profit_forecast_et.
Retains raw headers and broker details; does not invent missing currencies.
"""
import json,time,subprocess,concurrent.futures,datetime,re,statistics
from pathlib import Path
from lxml import html as lh
OUT=Path(__file__).resolve().parents[1]/'work/forecast'
OUT.mkdir(parents=True,exist_ok=True)
(OUT/'etnet').mkdir(exist_ok=True)

def fetch(code):
 p=OUT/'etnet'/f'{code}.html';u='https://www.etnet.com.hk/www/sc/stocks/realtime/quote_profit.php?code='+str(int(code))
 if not p.exists():
  t=time.monotonic();r=subprocess.run(['curl','-sSL','--max-time','25','-A','Mozilla/5.0',u],capture_output=True)
  if r.returncode==0:p.write_bytes(r.stdout)
  else:return {'code':code,'error':'HTTP transport '+str(r.returncode)}
  time.sleep(max(0,.8-(time.monotonic()-t)))
 try:
  html=p.read_text();s=lh.fromstring(html);tables=s.xpath('//table');result={'code':code,'source':u,'fetched_at':datetime.datetime.fromtimestamp(p.stat().st_mtime,datetime.timezone.utc).isoformat(),'title':''.join(s.xpath('//title/text()')), 'forecasts':[], 'brokers':[]}
  def rows(t):return [[re.sub(r'\s+',' ',' '.join(c.itertext())).strip() for c in r.xpath('./td|./th')] for r in t.xpath('.//tr')]
  for t in tables:
   rr=rows(t)
   if not rr:continue
   head=rr[0]
   if len(head)==7 and head[0]=='财政年度' and '纯利' in head[1] and '最高' in head[5]:
    result['unit_header']=head[1];result['summary_headers']=head
    for r in rr[1:]:
     if len(r)==7 and re.fullmatch(r'20\d\d',r[0]):result['forecasts'].append(dict(zip(['year','profit','eps','dps','bps','high','low'],r)))
   if len(head)>=8 and head[0]=='财政年度' and any('更新日期' in v for v in head):
    result['broker_headers']=head
    for r in rr[1:]:
     if len(r)>=8 and re.fullmatch(r'20\d\d',r[0]):result['brokers'].append({'year':r[0],'profit':r[1],'broker':r[4],'updated':r[-1]})
  if not result['forecasts']:
   text=' '.join(s.itertext());result['no_forecast_reason']='无预测表' if any(x in text for x in ['暂无','未有','不适用','没有','无相关']) else '未返回可解析预测表'
  return result
 except Exception as e:return {'code':code,'error':str(e)}

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--symbols', nargs='+', help='Five-digit HK codes; absent: read local exported sheet')
    parser.add_argument('--sheet-json', type=Path, default=Path(__file__).resolve().parents[1]/'work/current_sheet.json')
    args = parser.parse_args()
    if args.symbols:
        codes = [str(int(code)).zfill(5) for code in args.symbols]
    else:
        rows = json.loads(args.sheet_json.read_text())
        codes = [r[3][:5] for r in rows if len(r)>3 and isinstance(r[3],str) and r[3].endswith('.HK')]
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        for i, result in enumerate(pool.map(fetch, codes), 1):
            results.append(result)
            (OUT/'etnet'/f"{result['code']}.json").write_text(json.dumps(result, ensure_ascii=False, indent=2))
            if i % 50 == 0: print('Completed', i, flush=True)
    (OUT/'etnet_results.json').write_text(json.dumps(results, ensure_ascii=False, indent=2))
    print(json.dumps({'requested':len(codes),'with_forecasts':sum(bool(r.get('forecasts')) for r in results)},ensure_ascii=False))
