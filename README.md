# 超商跨品牌共同配送研究

我們用課程提供的配送與車輛資料，研究超商跨品牌共同配送是否能減少繞路、油耗與排放，以及什麼條件會讓效益消失。**期末聚焦共同配送；插電待機與 HVO 留作期中歷史紀錄。**

第一次進來，可以照下面三步了解目前成果：

1. 看 [期末工作計畫](docs/planning/final_work_plan.md)：研究問題、三人分工、每週交付物與時程。
2. 看 [校準版共同配送分析](notebooks/02_calibrated_joint_delivery.ipynb)：目前模型、路線比較與主要結果。先讀文字及現有輸出即可，不必先執行程式。
3. 看 [期中問答與教授回饋](docs/feedback/midterm_qa.md)：哪些說法已修正、還有哪些限制要處理。

## 依自己的工作找入口

| 你要做什麼 | 從這裡開始 |
|---|---|
| 看分工、認領／更新進度 | [協作入口](docs/planning/README.md)、[工作計畫](docs/planning/final_work_plan.md)、[Notion 安排](docs/planning/notion_collaboration.md) |
| 了解模型怎麼算、接手路線分析 | [02 校準版](notebooks/02_calibrated_joint_delivery.ipynb)，再看 [分析執行說明](notebooks/README.md) |
| 檢查資料、油耗及全臺推估 | [01 資料盤點](notebooks/01_data_overview.ipynb) → [03 候選門市篩選](notebooks/03_candidate_store_screening.ipynb) → [04 三場站路線驗證](notebooks/04_remote_route_validation.ipynb) |
| 找實務、合作與文獻證據 | [共同配送來源整理](docs/research/joint_delivery_sources.md)、[文獻方法筆記](docs/research/practical_routing_paper.md) |
| 找簡報、問答或舊提案 | [文件導覽](docs/README.md) |
| 了解舊成果怎麼一路修正 | [研究歷程](docs/archive/project_history.md) |

每人每週以 2–4 小時與 AI 協作產出，各人自檢自己的內容；週一 14:00 前繳簡報、14:30–15:00 與教授助教開會。日常進度在 [課程 Notion](https://app.notion.com/p/3ee3ba51f1c380e4b1e7e5b1ebabe2e0?source=copy_link) 維護。麗賢可直接貼文字、來源與表格；彥谷協助檔案及格式整合，不另設組員交叉查核。

## 資料夾怎麼分

```text
course_data/
├── README.md                 # 全專案入口
├── requirements.txt          # 現有分析環境的套件版本
├── notebooks/                # 按閱讀順序編號的主要分析
│   └── archive/              # 第一版試作，供追溯
├── scripts/                  # 可從命令列獨立執行的工作
├── src/                      # 共用路徑工具、欄位字典
├── data/
│   ├── raw/                  # 課程／助教原始資料，不進 Git
│   ├── external/             # 外部門市資料、行政區界線
│   ├── processed/            # 清理與人工確認後的門市清單
│   └── cache/                # 路網、求解與搜尋快取
├── outputs/
│   ├── figures/              # 可放簡報的圖
│   ├── profiling/            # 資料品質統計及剖析快取
│   └── idle/                 # 既有怠速分析報告及快取
└── docs/
    ├── planning/             # 分工、時程、任務追蹤
    ├── feedback/             # 問答、教師與同學回饋
    ├── research/             # 資料來源與文獻筆記
    ├── references/papers/    # 已取得的文獻 PDF
    ├── presentations/        # 歷次簡報 PDF
    ├── proposals/            # 原始提案
    └── archive/              # 舊規劃與研究歷程
```

各資料夾另有 README：[分析](notebooks/README.md)・[腳本](scripts/README.md)・[共用程式](src/README.md)・[資料](data/README.md)・[產物](outputs/README.md)・[文件](docs/README.md)。舊檔名對照及新檔命名見 [檔案整理規則](docs/project_layout.md)。

## 目前做到哪裡

- 東北角四區納入 **33 家門市**，已由組員至四大超商官網人工逐一核對，另排除 4 家歇業店。使用 [人工核對清單](data/processed/ne_stores_verified.csv)；OK 瑞芳逢甲店已補入組員提供的新座標，定位來源待補。
- 主要模型已改為沿既有幹線插入門市。**只有全家幹線來自課程實際配送資料；其他品牌幹線仍是假設。** 每店暫以 1 單位需求表示，完整貨量、時窗與溫層限制尚待期末補強。
- **新座標版本**的校準版 Q=25、偏遠門市由瑞芳專程服務的情境，四品牌一輪合計「服務這批門市額外增加的里程」約 **206.8 → 132.1 km，減少 74.7 km（36.1%）**；含幹線的路網總里程約 **1,179.7 → 1,105.0 km（減 6.3%）**。這不是整個車隊總里程下降 36.1%，也不是每一輛車每趟省 74.7 km。[新舊數字與重算方法](docs/feedback/midterm_qa.md#東北角回答時採用的數字)
- 若把另由其他場站服務的偏遠門市排除，研究範圍會不同，不能把兩種情境當作同一服務範圍的上下界。詳細比較見 02 與問答文件。
- 已做全臺候選門市篩選及瑞芳、林口、高雄三場站的路線檢查。**717 家是距離門檻篩出的候選門市，早期 830 噸是情境推估**，不是逐條全臺路線驗證後的實際效益。

接下來依 [工作計畫](docs/planning/final_work_plan.md) 補容量、服務條件、油耗差異及新增作業成本門檻。後續公告時程為 **12/14 期末發表、12/21 書面繳交**。

## 怎麼開啟與執行

**只看成果：** 直接閱讀 Markdown、notebook 現有輸出、PDF 或下載 Excel。`outputs/idle/` 的 HTML 可下載後以瀏覽器開啟，互動圖的 Plotly 元件需要網路。

**要重跑分析：** 建議 Python 3.12，在專案根目錄開啟終端機：

```powershell
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe scripts/check_project.py
.venv\Scripts\python.exe -m jupyterlab
```

在 JupyterLab 開啟 `notebooks/`，選取剛建立環境的 kernel，依 [分析執行說明](notebooks/README.md) 執行。若 `python` 開啟 Microsoft Store，請先選擇已安裝的 Python 執行檔。

課程原始資料需另行取得並放在 `data/raw/`，位置見 [資料說明](data/README.md)。只 clone 專案不會取得這些原始資料，但仍可閱讀已儲存的 notebook 輸出。既有快取可減少重算；缺少路網快取時，部分分析會呼叫公開 OSRM／Overpass 服務。

通常不用重跑約 3 GB 的完整資料剖析；`outputs/profiling/results.pkl` 已提供既有剖析結果。需要更新時才執行：

```powershell
python scripts/profile_data.py
```

檢查指令 `python scripts/check_project.py` 會檢查資料夾、連結、Python 與 notebook 語法，以及現有清單／快取的一致性；不會下載資料或重新求解路線。它不代表模型的研究假設已被驗證。

## 新成果放哪裡

1. 新增分析放 `notebooks/`，例如 `05_service_constraints.ipynb`；可重用函式放 `src/`，獨立批次工作放 `scripts/`。
2. 原始資料留在 `data/raw/`；確認後的輸入表放 `data/processed/`，在 [資料說明](data/README.md) 記錄來源、日期、整理方法及限制。
3. 圖放 `outputs/figures/`，文件放 `docs/` 對應子資料夾；每個結論附分析檔、情境、單位、負責人與本人自檢紀錄。
4. 完成任務時，在 Notion 更新狀態、成果連結及本人的 AI 使用紀錄。請勿只改圖上的數字，應從來源分析更新。

路徑由 `src/project_paths.py` 統一定位。Notebook 可從專案根目錄或其子資料夾執行，避免寫死個人電腦的絕對路徑。原始課程資料由 `.gitignore` 排除；提交前仍須檢查文件與輸出是否含個資。
