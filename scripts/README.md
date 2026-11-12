# 可獨立執行的腳本

以下指令均從專案根目錄執行，使用已安裝 `requirements.txt` 的 Python 環境。

| 指令 | 用途 | 讀取／輸出與注意事項 |
|---|---|---|
| `python scripts/check_project.py` | 檢查檔案架構、文件連結、語法、清單及快取 | 不重算、不下載；加 `--require-raw` 可檢查原始資料是否就位 |
| `python scripts/profile_data.py` | 全量資料品質剖析 | 讀 `data/raw/`，寫 `outputs/profiling/`；約讀取 3 GB，通常數分鐘，依電腦而異 |
| `python scripts/analyze_idle_vehicle.py V19` | 重跑單車怠速分析 | 需 CAN、配送表、TMS 及門市資料；寫 `outputs/idle/idle_V19.html` |
| `python scripts/analyze_idle_fleet.py` | 產生 7 車怠速彙整報告 | 優先讀 `outputs/idle/fleet_results.pkl`，寫同資料夾 HTML；`--rerun` 才重跑各車（數分鐘以上） |
| `python scripts/search_kaggle.py` | 重做既有 Kaggle 外部資料搜尋 | 會連網，搜尋結果寫入 `data/cache/dataset_search/`；非共同配送主流程 |

怠速分析保留供油耗基準與研究歷程參考。小組已停止擴充插電待機、HVO 方案，這些腳本執行完成不代表完成期末共同配送任務。

新批次工作用小寫英文動詞命名，例如 `validate_store_data.py`。可被多個分析使用的函式放 `src/`；不要把可重用函式做成執行即讀完所有資料的腳本。
