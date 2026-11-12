# 資料放置與來源

`raw/` 保留課程或助教提供的原樣資料；`external/` 放外部資料；`processed/` 是整理後供分析使用的清單；`cache/` 用來避免重複查詢及求解。

## 原始資料：各組員自行取得

```text
raw/
├── delivery_plan/             # 瑞芳；含 monthly、by_vehicle、by_task_type
├── delivery_plan_other_depots/ # 助教補充；保留原壓縮包的內層同名資料夾
│   └── delivery_plan_other_depots/
│       ├── linkou_LC/
│       └── kaohsiung_YT/
├── gps_traces/
├── store_master/
├── tms_delivery_records/
├── vehicle_can_telematics/
└── vehicle_class_by_V.csv
```

上述內容已由 `.gitignore` 排除，不會隨 Git clone 取得。請把下載的資料夾直接放進 `data/raw/`，保留內部檔名與層級，**不要把逐日或逐車 CSV 攤平成同一層**。其他場站保留來源內層同名目錄，現有分析以遞迴搜尋讀取。

車型表及其他場站資料需另向組員／助教取得。只閱讀現有結果不需要下載全部原始資料。欄位解釋見 [共用字典](../src/column_dictionary.py)；資料品質、時間範圍與助教回答的查核見 [01 資料盤點](../notebooks/01_data_overview.ipynb)。

## 外部與整理後資料

| 位置 | 用途與注意事項 |
|---|---|
| `external/convenience_store_branches.csv` | 原「全國5大超商資料集.csv」；行政登記資料用於對照，不直接視為完整且仍營業的門市清單 |
| `external/town_boundaries_20250318/` | 內政部鄉鎮市區界線 1140318 版；`.shp`、`.dbf`、`.shx`、`.prj` 等配套檔一起保留 |
| [processed/ne_stores_verified.csv](processed/ne_stores_verified.csv) | 東北角分析的門市清單；`include=1` 為納入 33 家，`include=0` 為排除 4 家。組員已人工逐一官網核對；2026-11-13 是回報日期，非逐店核對日期 |
| `processed/ne_stores_candidates.csv`、`processed/ne_stores_osm.csv` | 早期候選與 OSM 整理清單，保留追溯；目前納入範圍以 verified 清單為準 |
| `cache/routing/osm_convenience_tw.json`、`osm_ne_boundaries.json` | 公開 OSM 資料的既有快取；全臺快取未提供完整自動重建流程，不能隨意刪除 |
| `cache/routing/osrm_*.json` | OSRM 道路距離、路線幾何快取 |
| `cache/routing/rebuild_*.json` | 校準版求解與地圖結果；04 會讀取 02 的 `rebuild_calibrated.json` |
| `cache/dataset_search/` | 舊外部資料搜尋紀錄；非模型輸入 |

OK 瑞芳逢甲店仍使用暫定座標。人工確認營業狀態，不代表所有座標與歷史配送日期已完成一致性驗證。

## 更新資料時

原始資料不直接改寫。清理後另存 `processed/`，在此記錄來源、取得／核對日期、清理規則、負責人與限制。新增公開資料請附來源網址及授權／使用限制；資料搜尋線索見 [外部來源筆記](../docs/research/external_data_sources.md)。

更動門市或座標後，應檢查相關距離矩陣、路線與結果快取是否仍適用，再更新分析；請勿混用不同清單產生的結果。不要載入來源不明的 pickle；專案的 `.pkl` 是既有本地分析快取。
