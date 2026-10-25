# 最後一哩冷鏈物流減碳:課程資料與專題工作區

這個資料夾放的是課程提供的全家**瑞芳物流中心**配送資料,以及本組專題「超商冷鏈運輸採用跨廠商合併配送的減碳潛力」從摸資料到 PoC 的所有嘗試。這份 README 給組員看:**先看哪些檔、每一步試了什麼、得到什麼結論、哪些假設後來被推翻**。

---

## 先看哪些檔:照工作順序 explore → research → poc

整個專題是照這個順序做的:**先在 `explore/` 摸清楚課程資料 → 再到 `research/` 找外部資料集與文獻 → 最後在 `poc/` 做共同配送試作**。每個資料夾先看一個檔就能掌握重點,有時間再看其他檔。

| 順序 | 資料夾 | 先看這個檔 | 看什麼 | 有時間再看 |
|---:|---|---|---|---|
| 1 | `explore/` | [data_exploration.ipynb](explore/data_exploration.ipynb) 第 0 節與第 8 節 | 每份課程資料能回答什麼、有哪些坑 | [idle/idle_fleet.html](explore/idle/idle_fleet.html)(怠速分析結果) |
| 2 | `research/` | [external_data_sources.md](research/external_data_sources.md) | 找了哪些外部資料、為什麼最後還是只能用課程資料 | [joint_delivery_sources.md](research/joint_delivery_sources.md)(共配文獻) |
| 3 | `poc/` | [a_group_rebuild.ipynb](poc/a_group_rebuild.ipynb) 第 8 節 | **最新的方法與數字**:共配效益為什麼從 −51% 修正成 8–43% | [joint_delivery_poc.ipynb](poc/joint_delivery_poc.ipynb)(第一版試作) |

想先看全貌,可以先翻兩次進度報告:[1005進度報告.pdf](1005進度報告.pdf) 對應 explore 階段,[1019進度報告.pdf](1019進度報告.pdf) 對應 poc 階段;提案正文是 [綠色工程專案研究POC Proposal.md](綠色工程專案研究POC%20Proposal.md)。

---

## 工作歷程:試了什麼、結果如何

### 1. explore/:先把課程資料摸清楚(10/3–10/5)

小組當時有三個方向:管理與轉型策略(門市卸貨緩衝空間)、政策與制度設計(碳費、補助、低碳燃料)、資料科學與 AI。這一步先盤點課程資料能支援哪些題目。

| 做了什麼 | 檔案 | 結果 |
|---|---|---|
| 剖析五組資料的每個欄位(缺失、型態、品質問題) | [explore/profile_data.py](explore/profile_data.py) → `explore/profile/` | 只有 7 輛車(V04、V06、V07、V09、V17、V18、V19)能算實測油耗;所有資料都**沒有貨量** |
| 建立實測油耗基準 | 同上 | 2025 年 2–4 月平均 **21.2 L/100km ≈ 567 g CO₂/km**,之後所有排碳試算都用這個數字 |
| 怠速油耗拆解:先用 V19 驗證方法,再擴大到 7 輛車 | [explore/idle_prototype.py](explore/idle_prototype.py)、[explore/idle_fleet.py](explore/idle_fleet.py) → [explore/idle/idle_fleet.html](explore/idle/idle_fleet.html) | 怠速佔總油耗 **23.7%**,其中必要(門市卸貨、紅燈)12.5%、技術可替代(DC 怠速)7.6%、**可避免只有 3.6%** |
| 檢驗「早到會造成門市外等候」 | 同上 | **假設被否定**:早到與準時的停靠怠速時間幾乎相同(約 3 分鐘) |
| 找個別改善點 | 同上 | V09 每晚在 DC 怠速約 2.3 小時再出發,佔它總油耗 8.3%(等裝貨或預冷,需向業者確認) |

**這一步的結論:** 只靠改變駕駛行為能減的碳很少,題目需要換一個能用資料量化、又有減碳空間的切入點。

> 10/19 補做:拿到助教的欄位 Q&A(`綠色工程專案研究POC Proposal-1.docx`)後,回到 explore 把 33 條回答逐條用資料驗證,整合進 [data_exploration.ipynb](explore/data_exploration.ipynb) 第 2 節與各章「助教說法驗證」,欄位說明寫在 [column_dictionary.py](explore/column_dictionary.py) 的 `TA_QA`。大多吻合,**四處不符**:助教的車輛 × 任務表漏了任務 05 與 A4;表訂時間並非每店固定;carkit/DVRTYPE 不是恆為 1;天眼 Temperature1 只缺約 10%。另重現了 TMS **4,073 組可疑共用時間戳**。

### 2. research/:找外部資料集與文獻(10/5–10/9)

| 做了什麼 | 檔案 | 結果 |
|---|---|---|
| 搜尋臺灣、日本、韓國官方與企業資料,以及 Kaggle、Hugging Face 上的資料集 | [research/external_data_sources.md](research/external_data_sources.md)、`research/kaggle_check.py`、`research/kaggle_candidates.json`、`research/hf_*.json` | **找不到公開的冷鏈配送車逐筆資料**;超商永續報告只有彙總數字;Kaggle 冷鏈資料多為模擬;最接近的美國 VED 是小客車資料,情境差很多 |
| 蒐集跨品牌共同配送的一手文獻與實證 | [research/joint_delivery_sources.md](research/joint_delivery_sources.md) | 日本三大超商 2022 年北海道函館實證:行駛距離 −22%、CO₂ −56 kg。題目定為**跨品牌共同配送** |
| 擬提案大綱與證據對照 | [research/poc_proposal_outline.md](research/poc_proposal_outline.md) | 標出哪些數字已查證、哪些還缺 |

**這一步的結論:** 外部沒有能取代課程資料的逐筆資料,所以 PoC 用課程資料(油耗、全家路線)加上公開圖資(OpenStreetMap)來做。

> `research/` 裡另外兩份是做 PoC 時陸續補的:[poc_draft_review.md](research/poc_draft_review.md)(10/9 提案初稿審閱)、[poc_evidence_gaps.md](research/poc_evidence_gaps.md)(10/18 補充臺灣層級數據與 A 組重建的方法依據)。

### 3. poc/:共同配送試作(10/9 起)

**第一版試作(10/9–10/13)**

| 做了什麼 | 檔案 | 結果 |
|---|---|---|
| 選東北角四區(瑞芳、貢寮、雙溪、平溪)四品牌 33 家門市;全家用門市主檔,他牌取自 OpenStreetMap 再逐一以官網核對 | `poc/ne_stores_*.csv`、`poc/osm_*.json` | 最終清單在 `poc/ne_stores_verified.csv`(排除 4 家歇業店) |
| 用 OSRM 算道路距離、PyVRP 求解路線,比較 A 組(各自配送)與 B 組(共同配送) | [poc/joint_delivery_poc.ipynb](poc/joint_delivery_poc.ipynb) | 一輪配送里程 224.4 → 109.0 km(**−51%**)、趟數 5 → 2、行駛 CO₂ 每輪約 −64 kg |
| 審閱提案初稿 | [research/poc_draft_review.md](research/poc_draft_review.md) | 指出 −51% 遠高於函館的 −22%,主因是 A 組假設「各品牌**專程**進入東北角」 |

**檢驗假設、重建 A 組(10/18–10/19)**

| 做了什麼 | 檔案 | 結果 |
|---|---|---|
| 查全家東北角門市在配送計畫中實際怎麼送 | [poc/a_group_rebuild.ipynb](poc/a_group_rebuild.ipynb) 第 1 節 | **沒有一趟是專程配送**:瑞芳門市由晚班 LJ、OP 順路帶到,平溪由早班 SE 經過;貢寮不由瑞芳 DC 配送。實際每停一家東北角門市只多跑 3.8 km,PoC 假設的 8.8 km 是實際的 2.3 倍 |
| 版本一:各品牌重新最佳化 | 同上第 6 節 | 減 38–48%,但求解器又讓各品牌繞東北角一大圈,只能當上限 |
| **校準版:固定全家實際幹線,只把門市插進去(邊際里程法)** | 同上第 7 節 | 模型算出全家每店 3.4 km,與實際 3.8 km 相近,方法可信。邊際里程減 **8–43%**,路網總里程只減 **1–8%** |
| 政策與替代燃料試算 | [1019進度報告.pdf](1019進度報告.pdf) 第 6–8 頁 | 共配每年省油錢 13–23 萬元,減碳價值只有 0.3–0.6 萬元 → **碳價不是共配的推力**,障礙在協調、信任與法規;HVO 技術可行但成本高 |

**這一步的結論:** 共配效益集中在**沒有順路幹線的偏遠門市**(貢寮、雙溪 8 店的專程里程可減約一半);已經順路的瑞芳區門市,共配能省的很少。R1、R2 情境的差距來自「貢寮、雙溪由哪個物流中心配送」,這是下一步要查證的關鍵。

### 之後:10/25 新增資料,尚未分析

| 檔案 | 內容 | 可能用途 |
|---|---|---|
| `vehicle_class_by_V.csv` | V01–V23 的車型、噸數、品牌、排放期別、冷凍機型號、可否插電製冷、各任務趟數 | 補上先前「車型、噸數全缺」的限制;回答「冷藏設備怎麼驅動、能否用岸電」 |
| `delivery_plan_other_depots/` | 高雄 YT、林口 LC 兩個場站的配送紀錄,含**全部任務類型**(瑞芳的 TMS 只有任務 12) | 跨場站比較;林口與瑞芳共用 11 輛車,`V##` 可直接串接 |

`delivery_plan_other_depots.zip` 是同一份資料的壓縮檔。**這兩份資料不在 GitHub 上**(見 `.gitignore`),助教已上傳到課程網站,請從課程網站下載。

---

## 被推翻或修正過的假設

| 原本的假設 | 後來發現 | 影響 |
|---|---|---|
| 早到會造成門市外等候、多耗油 | 早到與準時的停靠怠速時間相同 | 不再從準點切入 |
| 怠速有很大的行為改善空間 | 可避免怠速只佔總油耗 3.6% | 題目轉向共同配送 |
| 各品牌都**專程**進入東北角(PoC A 組) | 全家全部是順路配送 | PoC 的 −51% 只能當上限,改用校準版 8–43% |
| GPS「燃料」可以算油耗 | 是油箱油位 %,行駛晃動誤差大(助教確認) | 油耗一律用車載 CAN |
| 任務代碼有官方定義 | 助教說是後端 API 回傳值,沒有定義 | 任務用途在報告中要寫明是推測 |

## 目前還沒解決的問題

1. 貢寮、雙溪門市(全家與他牌)實際由哪個物流中心配送?決定採 R1 或 R2 情境。
2. 各店每日被送幾次?用來把每輪減碳量年化。
3. 沒有貨量(箱數、籠車數),容量只能用「每趟最多停靠店數」代替。
4. 時間窗與溫層相容性還沒納入共配模型。
5. 冷藏設備的驅動方式與 V09 夜間 DC 怠速的原因(可先查 `vehicle_class_by_V.csv` 的冷凍機型號與 `插電制冷` 欄)。

---

## 資料夾地圖

依工作順序排列。

| 路徑 | 內容 |
|---|---|
| **1. explore/:課程資料探索與怠速分析** | |
| `data_exploration.ipynb` | 資料盤點、欄位說明、七步驟探索、助教 Q&A 驗證、資料品質總表 |
| `column_dictionary.py` | 中文欄位說明(`DICT`)、助教 Q&A(`TA_QA`)、代碼對照 |
| `profile_data.py` → `profile/` | 全資料剖析,產生 `profile/results.pkl` 供 notebook 使用 |
| `idle_prototype.py`、`idle_fleet.py` → `idle/` | 怠速分析;`idle/idle_fleet.html` 是 7 車總報告,`idle_V##.html` 是單車明細 |
| **2. research/:外部資料集與文獻** | |
| `external_data_sources.md` | 外部公開資料調查(結論:沒有可用的逐筆冷鏈資料) |
| `kaggle_check.py`、`kaggle_candidates.json`、`hf_*.json` | Kaggle、Hugging Face 資料集的搜尋腳本與候選清單 |
| `joint_delivery_sources.md` | 共同配送文獻與實證,標明一手、二手、未驗證 |
| `poc_proposal_outline.md`、`poc_draft_review.md`、`poc_evidence_gaps.md` | 提案大綱、初稿審閱、補充證據 |
| **3. poc/:共同配送試作** | |
| `joint_delivery_poc.ipynb` | 第一版試作(專程假設,−51%) |
| `a_group_rebuild.ipynb` | A 組重建與校準版(最新結果) |
| `ne_stores_*.csv` | 東北角四品牌門市清單(`verified` 為最終版) |
| `osm_*.json`、`osrm_*.json`、`rebuild_*.json` | OpenStreetMap、OSRM 查詢與求解結果的快取;重跑 notebook 不會重新連網,刪掉才會重查 |
| `a.png`、`b.png` | 第一版試作的 A 組、B 組路線圖 |
| **根目錄** | |
| `1005進度報告.pdf`、`1019進度報告.pdf` | 兩次進度報告投影片 |
| `綠色工程專案研究POC Proposal.md` | POC 提案正文(`poc/` 裡有一份較早的副本,以根目錄這份為準) |
| `綠色工程專案研究POC Proposal-1.docx` | 助教對各資料夾欄位問題的回答 |
| `vehicle_class_by_V.csv`、`delivery_plan_other_depots/` | 10/25 新增資料,尚未分析(不在 GitHub 上,助教已上傳到課程網站) |
| `鄉(鎮、市、區)界線1140318/` | 內政部鄉鎮市區界線圖資,畫地圖與篩選東北角四區用 |

---

## 課程資料集

| 資料夾 | 檔案數 | 時間範圍 | 一列代表 | 筆數 | 說明 |
|---|---:|---|---|---:|---|
| `store_master/` | 1 | 快照 | 一家全家門市 | 1,569 | 門市名稱、地址、經緯度。`X`、`Y` 是前人自訂座標,單位不明,**可忽略**(助教) |
| `delivery_plan/monthly/` | 15 | 2024-01 ~ 2025-03 | 某日某車某路線的一個停靠點 | 34.7 萬 | ★配送計畫主檔:任務類型、路線站序、車號、門市、實際到店時間 |
| `delivery_plan/by_vehicle/` | 23 | 同上 | 同上 | — | `monthly` 依車輛分檔,約 59% 重複,不需另外使用 |
| `delivery_plan/by_task_type/` | 5 | 同上 | 同上 | — | `monthly` 的部分子集(沒有 A2/A3/A4),不需另外使用 |
| `tms_delivery_records/` | 744 | 2024-01 ~ 2026-01 | 一趟配送中的一站 | 22.1 萬 | **只有任務 12**:表訂/預計/實際到店時間、準點判定、車廂溫度 |
| `gps_traces/` | 116 | 2024 與 2025 年的 3–4 月 | V13 的一筆定位(約每秒) | 259.6 萬 | **只有 V13 一輛車**;只有這兩段是因為來源網站資料有時效性,當時手動爬取(助教) |
| `vehicle_can_telematics/` | 90 | 2025-01 ~ 2025-07 | 一筆車載紀錄 | 555.2 萬 | 14 輛車、4 種匯出格式;只有 7 輛車有引擎 CAN 實測油耗 |

各資料集沒有共用主鍵:配送計畫與 TMS 用(日期、站序、車號、門市)對應;門市主檔只能用店名對應;GPS 與車載資料用車號加時間對回配送計畫。

### 使用資料前要知道的事

- **油耗只能用車載 CAN 的 `Total fuel used(L)`**。GPS 的「燃料」是油箱油位,不是油耗。
- **準點用 TMS 的 `Ex_Arrive_diff`(實際 − 表訂)或 `DiffStatus`**,允收時窗為表訂前 60 分到後 30 分。不要用「預計到達」`Pl_Arrive_dt`,它停靠完成後常被回填成實際時間。
- **TMS 有 4,073 組可疑的共用時間戳**(同一趟不相鄰的門市共用同一秒),算行駛或停留時間前要先排除。
- **表訂時間會隨期間變動**,同一家店常有 2–3 種時刻,時間窗要分期間建立。
- **車輛分工以 `delivery_plan/monthly` 為準**,助教整理的車輛 × 任務表漏了任務 05 與 A4。
- TMS 的 `_01`、`_02`、`In_`、`Route_id1`、`Arrive_dt` 都是重複欄,擇一使用。
- 司機姓名、電話已去識別化,但仍不要在報告或圖表中顯示。

---

## 從 GitHub clone 下來之後

課程原始資料太大(約 3 GB),**沒有放進 GitHub**。clone 之後,請把從課程下載的五個資料夾直接放在 repo 根目錄,和 `explore/`、`poc/` 同一層:

```
(repo 根目錄)/
├── delivery_plan/
├── gps_traces/
├── store_master/
├── tms_delivery_records/
├── vehicle_can_telematics/
├── explore/
├── poc/
└── research/
```

10/25 新增的 `vehicle_class_by_V.csv` 與 `delivery_plan_other_depots/` 也一樣從課程網站下載,放在 repo 根目錄。這些資料都已寫在 `.gitignore`,放進來也不會被 commit。只看 notebook 的結果不需要放資料;要重跑才需要。

## 執行環境

- Python 3.12(本機使用 WinPython `C:\Users\a0903\WPy64-31241\python-3.12.4.amd64`),需要 `pandas`、`numpy`、`matplotlib`、`plotly`、`opencc`;PoC 另需 `pyvrp`。
- 執行 notebook 時請選 **WinPython 3.12** kernel。預設的 `python3` kernel 指向 Windows 市集的 `python` 捷徑,會無法啟動。
- `data_exploration.ipynb` 的全資料統計讀 `explore/profile/results.pkl`;原始資料有變動時,先跑 `python explore/profile_data.py`(約 5–15 分鐘)再重跑 notebook。
- PoC 的道路距離與路線都有快取,不連網也能重跑。
- 車載資料的原始欄名多為簡體字,notebook 顯示時一律轉為臺灣正體;程式中引用欄位仍須用原始欄名。
