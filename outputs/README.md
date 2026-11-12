# 分析產物

| 資料夾 | 放什麼 | 從哪裡產生 |
|---|---|---|
| `figures/` | 路線比較靜態圖、原始路線參考圖 | [02 校準版](../notebooks/02_calibrated_joint_delivery.ipynb) 輸出 `calibrated_routes_comparison.png`；`prototype_*.png` 為第一版歷史圖，`actual_familymart_routes.png` 為既有路線參考圖 |
| `profiling/` | 欄位／檔案品質 CSV、`results.pkl`、執行紀錄 | [profile_data.py](../scripts/profile_data.py)；供 [01 資料盤點](../notebooks/01_data_overview.ipynb) 讀取 |
| `idle/` | 單車與車隊怠速 HTML、彙整快取及紀錄 | [單車腳本](../scripts/analyze_idle_vehicle.py)、[車隊腳本](../scripts/analyze_idle_fleet.py)；`fleet_findings.html` 是既有人工解讀片段 |

圖表及報告要由來源分析更新，避免只在圖上修改數字。新增圖請在對應 notebook 記錄情境、參數與解讀；第一版圖不能直接當作目前校準版的結果。

`results.pkl` 等舊快取內可能保留整理前的相對路徑；共用讀取工具會在記憶體轉換剖析表的路徑，沒有改動既有數值或 pickle。舊執行紀錄保留當時的路徑與執行情況。

互動 HTML 用瀏覽器開啟，Plotly 元件從 CDN 載入，需要網路。`legacy_workspace/` 若存在，僅暫存整理時保留的本機編譯快取，已排除版本管理。
