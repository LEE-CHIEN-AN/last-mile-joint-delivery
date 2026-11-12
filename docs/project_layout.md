# 檔案整理與命名規則

整理日期：2026-11-13。這次依用途重整檔案及路徑，保留原始資料、人工核對清單、求解快取、圖與 PDF 的內容。模型算法與數值假設沒有在本次整理中修改。

## 從舊位置找新位置

| 原位置 | 新位置 |
|---|---|
| `explore/data_exploration.ipynb` | `notebooks/01_data_overview.ipynb` |
| `poc/2_a_group_rebuild.ipynb` | `notebooks/02_calibrated_joint_delivery.ipynb` |
| `poc/3_remote_scan.ipynb` | `notebooks/03_candidate_store_screening.ipynb` |
| `poc/4_remote_routes.ipynb` | `notebooks/04_remote_route_validation.ipynb` |
| `poc/1_joint_delivery_poc.ipynb` | `notebooks/archive/01_dedicated_delivery_prototype.ipynb` |
| `explore/profile_data.py` | `scripts/profile_data.py` |
| `explore/idle_prototype.py`、`explore/idle_fleet.py` | `scripts/analyze_idle_vehicle.py`、`scripts/analyze_idle_fleet.py` |
| `explore/column_dictionary.py` | `src/column_dictionary.py` |
| `research/dataset_search/kaggle_check.py` | `scripts/search_kaggle.py` |
| `poc/data/` | `data/processed/` |
| `poc/cache/` | `data/cache/routing/` |
| `research/dataset_search/*.json` | `data/cache/dataset_search/` |
| 根目錄的課程原始資料夾與車型表 | `data/raw/`，保留來源內部層級 |
| `全國5大超商資料集.csv` | `data/external/convenience_store_branches.csv` |
| `鄉(鎮、市、區)界線1140318/` | `data/external/town_boundaries_20250318/` |
| `explore/profile/`、`explore/idle/` | `outputs/profiling/`、`outputs/idle/` |
| `poc/figures/` | `outputs/figures/`，圖名依用途改為英文 |
| `research/1_*.md`、`2_*.md`、`4_*.md` | `docs/research/`，取消製作順序編號 |
| `research/3_proposal_notes.md` | `docs/archive/proposal_notes.md` |
| `research/5_midterm_qa_baseline.md` | `docs/feedback/midterm_qa.md` |
| `research/papers/` | `docs/references/papers/` |
| `planning/期末分工與時程.md`、`期末任務追蹤.xlsx` | `docs/planning/final_work_plan.md`、`final_task_tracker.xlsx` |
| 根目錄進度／期中簡報 PDF | `docs/presentations/YYYY-MM-DD_主題.pdf` |
| 根目錄回饋 PDF | `docs/feedback/2026-11-09_video_feedback.pdf` |
| 根目錄 `綠色工程專案研究POC Proposal.md` | `docs/proposals/initial_poc_proposal.md` |
| 整理前的 README | `docs/archive/project_history.md` |

11/09 回饋 PDF 因正被其他程式開啟，新位置使用內容相同的副本；根目錄原檔暫留本機並由 `.gitignore` 排除，關閉檔案後可自行移除。請使用 `docs/feedback/` 的版本。

## 命名與責任

- 資料夾與程式檔：英文小寫、底線分詞，名稱說明用途；文件正文使用中文。
- Notebook：`兩位閱讀順序_分析主題.ipynb`。只有 notebook 使用順序編號，文獻與共用程式不編號。
- 定期簡報或會議記錄：`YYYY-MM-DD_主題.ext`。日期需能從來源確認，不自填取得日期。
- 資料集內部原始檔名保持原樣。人工整理資料命名說明內容與狀態，例如 `ne_stores_verified.csv`。
- 舊方案放對應 `archive/` 並標出歷史用途；不要複製出多個 `final`、`new`、`最新版`。
- 程式引用專案根目錄的相對路徑，透過 `src/project_paths.py` 定位；Markdown 連結則相對於該文件所在位置。

根 README 負責導航；各資料夾 README 負責操作與來源；完整研究結果留在分析檔。新增成果後同步更新對應入口，讓其他組員不需要搜尋作者的個人檔名。

## 本次整理的檢查範圍

- 5 份 notebook 通過格式與 code cell 編譯檢查；各檔的初始化都能從根目錄、`notebooks/`、`notebooks/archive/` 找到專案。
- 檢查所有 Markdown 與 notebook 文字中的本地檔案連結；Excel 追蹤表的 7 個工作表可讀，6 個公式保留。
- 執行 02 的資料載入與既有快取計算，重現 Q=25 的 R1／R2 數字；03 的資料載入及篩選重現 717 家；04 檢查至三場站資料載入與門市定位比對，未重跑其物流中心位置推測及完整分析。
- 第一版封存 notebook 可讀取既有門市與路網矩陣；車隊怠速腳本可從新位置讀取 7 車快取並產生 HTML。
- 搬移前後 1,081 份原始／外部輸入檔案的大小一致；26 份既有 JSON、pickle、圖、PDF 及核對清單的 SHA-256 一致。沒有重新求解或更新公開圖資。

日後可用 `python scripts/check_project.py --require-raw` 執行基本檢查。這次未重做全量資料剖析、完整路線求解或全新環境安裝；上述檢查確認搬移後的可讀取性與既有結果一致性，不代表所有研究假設已驗證。
