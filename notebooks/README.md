# 分析檔怎麼讀、怎麼跑

檔名前兩位數字代表建議閱讀順序。主要方法從 **02 校準版**開始；第一版專程配送假設已移到 `archive/`。

| 分析檔 | 回答的問題 | 重跑所需資料／前置工作 | 會讀寫的主要產物 |
|---|---|---|---|
| [01_data_overview.ipynb](01_data_overview.ipynb) | 課程資料有哪些、品質與油耗基準如何？ | `data/raw/` 課程資料、其他場站及車型表；既有 `outputs/profiling/results.pkl` | 主要讀取剖析快取；部分章節會直接掃描原始 CSV |
| [02_calibrated_joint_delivery.ipynb](02_calibrated_joint_delivery.ipynb) | 保留既有幹線後，共配還能省多少？ | 原始門市主檔、瑞芳配送表、核對清單、行政界線；PyVRP | `data/cache/routing/rebuild_*.json`、OSRM 快取、`outputs/figures/calibrated_routes_comparison.png` |
| [03_candidate_store_screening.ipynb](03_candidate_store_screening.ipynb) | 哪些地區可列為共配候選？ | 全臺 OSM 門市快取、外部門市 CSV、界線；末段另用原始配送表與車型表 | 既有輸出保存在 notebook，候選數字仍受門檻與圖資限制 |
| [04_remote_route_validation.ipynb](04_remote_route_validation.ipynb) | 三場站實際路線能否支持偏遠門市推估？ | 瑞芳、林口、高雄配送表、門市主檔、全臺 OSM 快取、界線；02 產生的 `rebuild_calibrated.json` | `data/cache/routing/osrm_remote_routes.json` 及 notebook 結果 |
| [archive/01_dedicated_delivery_prototype.ipynb](archive/01_dedicated_delivery_prototype.ipynb) | 第一版專程配送的結果與偏誤從何而來？ | 門市主檔、核對清單、OSM／OSRM 快取 | 第一版快取；保留供追溯，期末主要結論請引用 02 |

## 第一次執行

1. 依 [根目錄 README](../README.md) 建立 Python 3.12 環境並安裝套件。
2. 依 [資料說明](../data/README.md) 放好原始資料，再執行 `python scripts/check_project.py --require-raw`。這只確認必要資料位置，不能替代資料品質檢查。
3. 從專案根目錄啟動 JupyterLab，確認 kernel 是已安裝套件的環境。
4. 各 notebook 由上至下執行；04 最後會讀 02 的結果，因此先確認該快取已存在。01 的剖析腳本只在原始資料有更新時才需重跑。

Notebook 儲存了既有輸出，未執行也可先閱讀。重跑會覆寫部分快取與圖；求解結果可能受種子、套件版本及公開路網服務更新影響。缺 OSRM／Overpass 快取時可能發出網路請求；03、04 使用已保存的全臺 OSM 快取，現有程式沒有完整重建該全臺資料的下載流程，請保留快取並記錄更新來源。

## 接手或新增分析

- 單一 notebook 保留「目的、輸入、假設、計算、結果解讀」；共用函式抽到 `src/`。
- 新檔用 `05_主題英文小寫.ipynb` 形式，避免再用組別、日期或 `final_v2_new` 當主要名稱。不要為了預留工作先建立空 notebook。
- 路徑使用 `from project_paths import project_path` 及 `project_path("data", "processed", ...)`。沿用現有第一個 code cell 的專案定位方式即可。
- 每個比較寫明服務範圍、每輪／每趟、分母、容量假設與排放邊界。全臺候選數不等於已驗證效益。
