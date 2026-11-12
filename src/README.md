# 共用程式

| 模組 | 用途 |
|---|---|
| [project_paths.py](project_paths.py) | 以模組所在位置定位專案；`project_path()` 組合路徑；`load_profile_results()` 讀取剖析快取並在記憶體調整舊輸入路徑 |
| [column_dictionary.py](column_dictionary.py) | 課程欄位說明、助教 Q&A 與分析報告使用的術語表 |

Notebook 第一個 code cell 會找到 `src/project_paths.py`，再將 `src/` 加入模組搜尋路徑。新 notebook 沿用該段設定，不必依靠 `cd ..` 或自己電腦的絕對路徑。

共用函式放這裡，獨立執行的入口放 `scripts/`，情境比較與結果解讀留在 `notebooks/`。新增模組時避免在 import 時就掃描原始資料或連網。
