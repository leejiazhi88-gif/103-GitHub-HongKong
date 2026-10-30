# 103-GitHub-HongKong

港股筛选、盈利预测核验与飞书研究表维护。用户指定本仓库作为当前工作区后续每次迭代的同步仓库。

在线交付：[港股投研_2026-10-29](https://my.feishu.cn/wiki/DQvWwTlZoiq5FwkLIm0ccRbhnxh?sheet=u5nSmy)。数据日期与执行日期分别记录。

## 当前版本

- 门槛：总市值 ≥280 亿港元；292 家公司，删除此前低于门槛的443家。
- 分类：H股148家、国资境外红筹30家、P-chip 64家、香港本地34家、国际海外16家。
- F及AY列为亿港元；年度净利润仍为亿美元，PE统一币种后计算。
- A:E按B列五类设底色；待核验/预估保留红字；行高29px。
- 行情快照2026-10-29。A+H市值沿用港股价×总股数，不是A/H分别定价加总。预托证券、非H股控制人归属等待核验项已标红。

## 来源与局限

港股基础池来自Tushare及东方财富证券清单，行情为腾讯API，财务为东方财富原币利润表，汇率为ExchangeRate-API公开日快照。

年度预估使用开源项目 [AKShare](https://github.com/akfamily/akshare) 的 `stock_hk_profit_forecast_et` 对应经济通公开页面，保留综合纯利、原始币种/单位、年份、券商数及更新日期，并与明细中位数勾稽。GitHub提供取数代码，数据来自上游。代码能运行不代表全部公司有预测。

没有原币单位不折算；没有单季数据不均摊年度；公司已公布的全年实际值不被预测覆盖。历史归母利润与券商预测的调整口径可能不同，相关增长率需复核。Yahoo路径此前返回403/限流，未据此认定港股预测整体不可获取。

## 本地配置与使用

Python 3；curl；预测页面解析需要`pip install -r requirements.txt`。飞书应用需要目标文档访问及表格读写权限。复制`.env.example`为本地`.env`并设置凭据，或传`--env-file`指定本地文件；不提交真实凭据。

```sh
python3 scripts/export_sheet.py --update-state
python3 scripts/format_sheet.py              # 预览分类数量
python3 scripts/format_sheet.py --apply      # 应用名称、底色及29px行高
python3 scripts/collect_forecasts.py --symbols 00700 00939
python3 scripts/validate_forecasts.py --as-of 2026-10-29
```

不传`--symbols`时，预测采集器读取`work/current_sheet.json`中的全部港股代码。原始响应保存在`work/forecast/etnet/`；命中缓存时保留原抓取时间。需刷新时先将旧缓存移至本地归档。预测采集/核验命令不会自动写飞书；应审查校验结果、财年和币种后定向更新并回读。

本次同步提供可独立运行的在线表导出、格式维护、年度预测采集及核验脚本；此前全市场历史构建过程与原始缓存保留本地`work/`。新克隆可读取获授权的在线当前版本，不宣称从零一键重建全部历史数据。

## 迭代同步

规则见`AGENTS.md`。每次迭代完成后更新变更记录、检查、提交并推送，核验远端提交；回复附飞书链接和同步结果。代码、规则、来源说明和已筛查的运行摘要入库；凭据、完整表格、原始市场响应和依赖缓存不自动入库。这里没有创建后台定时同步。
