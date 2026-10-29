# 最後一哩冷鏈物流減碳:課程資料與專題工作區

這個資料夾放的是課程提供的全家**瑞芳物流中心**配送資料,以及本組專題「超商冷鏈運輸採用跨廠商合併配送的減碳潛力」從摸資料到 PoC 的所有嘗試。這份 README 給組員看:**先看哪些檔、每一步試了什麼、得到什麼結論、哪些假設後來被推翻**。

---

## 先看哪些檔:照工作順序 explore → research → poc

整個專題是照這個順序做的:**先在 `explore/` 摸清楚課程資料 → 再到 `research/` 找外部資料集與文獻 → 最後在 `poc/` 做共同配送試作**。每個資料夾先看一個檔就能掌握重點,有時間再看其他檔。

| 順序 | 資料夾 | 先看這個檔 | 看什麼 | 有時間再看 |
|---:|---|---|---|---|
| 1 | `explore/` | [data_exploration.ipynb](explore/data_exploration.ipynb) 第 0 節與第 10 節 | 每份課程資料能回答什麼、有哪些坑(第 8、9 節是助教補充的其他場站與車型表) | [idle/idle_fleet.html](explore/idle/idle_fleet.html)(怠速分析結果) |
| 2 | `research/` | [1_external_data_sources.md](research/1_external_data_sources.md) | 找了哪些外部資料、為什麼最後還是只能用課程資料 | [2_joint_delivery_sources.md](research/2_joint_delivery_sources.md)(共配文獻) |
| 3 | `poc/` | [2_a_group_rebuild.ipynb](poc/2_a_group_rebuild.ipynb) 第 8 節 | **最新的方法與數字**:共配效益為什麼從 −51% 修正成 8–43% | [3_remote_scan.ipynb](poc/3_remote_scan.ipynb)(放大到全臺)、[4_remote_routes.ipynb](poc/4_remote_routes.ipynb) 第 9 節(用三場站實際路線驗證並下修全臺估算)、[1_joint_delivery_poc.ipynb](poc/1_joint_delivery_poc.ipynb)(第一版試作) |

`research/`、`poc/` 裡檔名開頭的數字是**製作順序**,照數字讀就是當時的思路;`data/`、`cache/`、`figures/` 等子資料夾放的是 notebook 讀寫的輸入、快取與圖檔,不用打開。

想先看全貌,可以先翻三次進度報告:[1005進度報告.pdf](1005進度報告.pdf) 對應 explore 階段,[1019進度報告.pdf](1019進度報告.pdf) 對應 poc 階段,[1026進度報告.pdf](1026進度報告.pdf) 整理全家既有減碳作法、日韓中經驗,並比較三個減碳方案(四家共配、物流中心改插電、改加 HVO);提案正文是 [綠色工程專案研究POC Proposal.md](綠色工程專案研究POC%20Proposal.md)。

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
| 搜尋臺灣、日本、韓國官方與企業資料,以及 Kaggle、Hugging Face 上的資料集 | [research/1_external_data_sources.md](research/1_external_data_sources.md)、[research/dataset_search/](research/dataset_search/)(Kaggle、Hugging Face 搜尋腳本與候選清單) | **找不到公開的冷鏈配送車逐筆資料**;超商永續報告只有彙總數字;Kaggle 冷鏈資料多為模擬;最接近的美國 VED 是小客車資料,情境差很多 |
| 蒐集跨品牌共同配送的一手文獻與實證 | [research/2_joint_delivery_sources.md](research/2_joint_delivery_sources.md) | 日本三大超商 2022 年北海道函館實證:行駛距離 −22%、CO₂ −56 kg。題目定為**跨品牌共同配送** |
| 擬提案大綱與證據對照 | [research/3_proposal_notes.md](research/3_proposal_notes.md) 第一部分 | 標出哪些數字已查證、哪些還缺 |

**這一步的結論:** 外部沒有能取代課程資料的逐筆資料,所以 PoC 用課程資料(油耗、全家路線)加上公開圖資(OpenStreetMap)來做。

> `research/` 裡另外兩份是做 PoC 時陸續補的:[3_proposal_notes.md](research/3_proposal_notes.md) 第二、三部分(10/9 提案初稿審閱、10/18 補充臺灣層級數據與 A 組重建的方法依據)、[4_last_mile_routing_paper.md](research/4_last_mile_routing_paper.md)(10/27 查核 Rashidi 等人 2025 年發表在 *Transportation Research Part C* 的插入法論文,全文 PDF 在 [research/papers/](research/papers/);論文可引用來支持「以實際路線為準、只做插入」的校準版,並提供「司機實際路線比最佳解多 5.9%」這個數字;它用的 Amazon 最後一哩路線資料集可免費取得,約 3.3 GB,但是美國電商包裹、沒有油耗與冷鏈,不建議下載)。

### 3. poc/:共同配送試作(10/9 起)

**第一版試作(10/9–10/13)**

| 做了什麼 | 檔案 | 結果 |
|---|---|---|
| 選東北角四區(瑞芳、貢寮、雙溪、平溪)四品牌 33 家門市;全家用門市主檔,他牌取自 OpenStreetMap 再逐一以官網核對 | `poc/data/ne_stores_*.csv`、`poc/cache/osm_*.json` | 最終清單在 `poc/data/ne_stores_verified.csv`(排除 4 家歇業店) |
| 用 OSRM 算道路距離、PyVRP 求解路線,比較 A 組(各自配送)與 B 組(共同配送) | [poc/1_joint_delivery_poc.ipynb](poc/1_joint_delivery_poc.ipynb) | 一輪配送里程 224.4 → 109.0 km(**−51%**)、趟數 5 → 2、行駛 CO₂ 每輪約 −64 kg |
| 審閱提案初稿 | [research/3_proposal_notes.md](research/3_proposal_notes.md) 第二部分 | 指出 −51% 遠高於函館的 −22%,主因是 A 組假設「各品牌**專程**進入東北角」 |

**檢驗假設、重建 A 組(10/18–10/19)**

| 做了什麼 | 檔案 | 結果 |
|---|---|---|
| 查全家東北角門市在配送計畫中實際怎麼送 | [poc/2_a_group_rebuild.ipynb](poc/2_a_group_rebuild.ipynb) 第 1 節 | **沒有一趟是專程配送**:瑞芳門市由晚班 LJ、OP 順路帶到,平溪由早班 SE 經過;貢寮不由瑞芳 DC 配送。實際每停一家東北角門市只多跑 3.8 km,PoC 假設的 8.8 km 是實際的 2.3 倍 |
| 版本一:各品牌重新最佳化 | 同上第 6 節 | 減 38–48%,但求解器又讓各品牌繞東北角一大圈,只能當上限 |
| **校準版:固定全家實際幹線,只把門市插進去(邊際里程法)** | 同上第 7 節 | 模型算出全家每店 3.4 km,與實際 3.8 km 相近,方法可信。邊際里程減 **8–43%**,路網總里程只減 **1–8%** |
| 政策與替代燃料試算 | [1019進度報告.pdf](1019進度報告.pdf) 第 6–8 頁 | 共配每年省油錢 13–23 萬元,減碳價值只有 0.3–0.6 萬元 → **碳價不是共配的推力**,障礙在協調、信任與法規;HVO 技術可行但成本高 |

**這一步的結論:** 共配效益集中在**沒有順路幹線的偏遠門市**(貢寮、雙溪 8 店的專程里程可減約一半);已經順路的瑞芳區門市,共配能省的很少。R1、R2 情境的差距來自「貢寮、雙溪由哪個物流中心配送」,這是下一步要查證的關鍵。

### 4. 助教補充資料:其他場站與車型表(10/25 收到,10/27 分析)

兩份新資料已補進 [data_exploration.ipynb](explore/data_exploration.ipynb) 第 8、9 節(欄位說明在 [column_dictionary.py](explore/column_dictionary.py) 的 `DICT["other_depots"]`、`DICT["vehicle_class"]`)。

| 檔案 | 內容 | 發現 |
|---|---|---|
| `delivery_plan_other_depots/` | 林口 LC(2024-01 ~ 2025-12)、高雄 YT(2024-01 ~ 2026-10)的配送紀錄,含**全部任務類型**(瑞芳的 TMS 只有任務 12) | ① **容量假設有依據了**:5t 車每趟大約 25 店到頂(林口晚班 99% 為 27 店、高雄 25 店),共配試作的「每趟上限 25 店」合理;30 店以上只有 9.5t 大車 V02 跑過。② **兩個場站都沒有東北角門市**,全家貢寮門市由哪裡配送仍然不知道。③ 林口與瑞芳共用 11 台車,但 9 台主要在瑞芳跑;CAN 期間只有 V13(3 天)、V14(2 天)跑過林口,算油耗時要排除。④ 高雄門市不在門市主檔,無法定位 |
| `vehicle_class_by_V.csv` | V01–V23 的車型、噸數、排放期別、冷凍機型號、可否插電制冷、各任務趟數 | ① **有實測油耗的 7 輛車全是 5t 14 尺六期**,油耗基準 21.2 L/100km 只代表這個車型;五期 11 尺車與 9.5t 車沒有油耗資料。② 15 台可插電制冷,只有 V02、V10 不行(1026 報告方案 B 已採用)。③ 「趟數」欄只有配送計畫推算值的約 4–10 成,期間與定義不明,不要用 |

**這兩份資料不在 GitHub 上**(見 `.gitignore`),助教已上傳到課程網站,請從課程網站下載。

### 5. 放大到全臺:回應老師「比較基準要一致」(10/27)

| 做了什麼 | 檔案 | 結果 |
|---|---|---|
| 用 OpenStreetMap 抓全臺四大超商門市,以經濟部商業署分公司登記資料核對各鄉鎮家數 | [poc/3_remote_scan.ipynb](poc/3_remote_scan.ipynb) 第 1 節 | OSM 四品牌 11,860 家(約全國 83%),偏遠鄉鎮涵蓋率約 98% |
| 以「離第 5 近的同品牌門市 ≥ 5 km,且 2 km 內有他牌」找出像貢寮、雙溪的門市 | 同上第 2–3 節 | 全臺 **717 家**(6%)、153 個鄉鎮;OK 有 23% 門市屬於這類,7-Eleven 只有 3% |
| 用東北角校準版的每店效益放大,三方案放到同一基準 | 同上第 4–5 節 | 共配約 830 公噸/年(64–1,250),和改插電(470–730)同一量級;改加 HVO 約 12,000(示意)。**10/29 已依三場站實際路線下修,見第 6 步** |

### 6. 用三個物流中心的實際路線驗證偏遠門市(10/29)

把 `2_a_group_rebuild` 第 1、3 節「東北角全家怎麼送」的檢驗,擴大到瑞芳、林口、高雄三個物流中心的所有偏遠受益型門市。

| 做了什麼 | 檔案 | 結果 |
|---|---|---|
| 在三場站配送計畫中找出偏遠受益型全家門市(高雄門市不在主檔,改用 OSM 店名、電話與鄉鎮估計定位;高雄物流中心位置由出車時間反推,落在岡山) | [poc/4_remote_routes.ipynb](poc/4_remote_routes.ipynb) 第 1–3 節 | 共 **67 家**(瑞芳 14、林口 3、高雄 50),對到全臺 215 家中的 62 家;雲林、嘉義、南投、花蓮等地不在這三個場站。有送的日子幾乎都是**一天一次**,「每日一輪」成立 |
| 看含偏遠店的 2,700 多趟怎麼排 | 同上第 4 節 | **沒有專程趟次**:偏遠店一律和 6–24 家一般門市同趟。瑞芳排在趟次最後(坪林、烏來、平溪),高雄多排在前段、中段 |
| 用 OSRM 道路距離算邊際里程(先做最短路徑修正,避免「最快路線」造成負的邊際里程) | 同上第 5–6 節 | 每停一家偏遠店平均多跑 **9.5 km**(瑞芳 13.1、林口 10.7、高雄 6.9),是東北角 3.8 km 的 2.5 倍,同趟一般門市只有 0.2–0.5 km。最極端的是坪林順益店(每趟約 24 km) |
| 用實測邊際里程 × 校準版共配節省比例(專程型 51%、順路型 8%)重算全臺 | 同上第 8 節 | 共配每年約 **600 公噸**(110–700),比原本的 830(64–1,250)低約 3 成、範圍變窄,仍和改插電同一量級 |

**這一步的結論:** 東北角的「順路、不專程」在其他地方也成立,但順路不等於便宜。偏遠店常成群排在幹線尾端,要多繞 10–25 km,這些「門市群」(坪林、烏來、北海岸、麻豆—玉井、屏東山腳)才是共配最值得試辦的地方。

---

## 被推翻或修正過的假設

| 原本的假設 | 後來發現 | 影響 |
|---|---|---|
| 早到會造成門市外等候、多耗油 | 早到與準時的停靠怠速時間相同 | 不再從準點切入 |
| 怠速有很大的行為改善空間 | 可避免怠速只佔總油耗 3.6% | 題目轉向共同配送 |
| 各品牌都**專程**進入東北角(PoC A 組) | 全家全部是順路配送 | PoC 的 −51% 只能當上限,改用校準版 8–43% |
| GPS「燃料」可以算油耗 | 是油箱油位 %,行駛晃動誤差大(助教確認) | 油耗一律用車載 CAN |
| 任務代碼有官方定義 | 助教說是後端 API 回傳值,沒有定義 | 任務用途在報告中要寫明是推測 |
| 每趟上限可以設到 30 店 | 三個場站的 5t 車每趟大約 25 店到頂,30 店以上只有 9.5t 大車做得到 | 校準版的 Q30 情境要標成「需改派大車」 |

## 目前還沒解決的問題

1. 貢寮、雙溪門市(全家與他牌)實際由哪個物流中心配送?決定採 R1 或 R2 情境。林口、高雄的資料都沒有這些門市,答案在第三個物流中心。雲林、嘉義、南投、花蓮等地的偏遠門市也一樣,不在三個場站的資料裡(`4_remote_routes.ipynb` 第 3 節)。
2. ~~各店每日被送幾次?~~ 已由 `4_remote_routes.ipynb` 第 3 節回答:常態配送的偏遠門市,有送的日子幾乎都是一天一次。
3. 沒有貨量(箱數、籠車數),容量只能用「每趟最多停靠店數」代替;三個場站的實際停靠數支持「5t 車約 25 店」的上限。
4. 時間窗與溫層相容性還沒納入共配模型。
5. V09 夜間 DC 怠速的原因:車型表顯示 V09 **可以插電制冷**,所以不是設備做不到,原因仍需向業者確認。
6. 油耗基準只代表 5t 14 尺六期車;五期 11 尺車與 9.5t 車的排放要用外部係數或假設。
7. 1026 報告方案 A 的「可省 38–48%」是版本一(上限);校準版是 8–43%,依偏遠門市由誰配送而定。

---

## 資料夾地圖

依工作順序排列。

| 路徑 | 內容 |
|---|---|
| **1. explore/:課程資料探索與怠速分析** | |
| `data_exploration.ipynb` | 資料盤點、欄位說明、七步驟探索、助教 Q&A 驗證、資料品質總表;第 8、9 節為其他場站與車型表 |
| `column_dictionary.py` | 中文欄位說明(`DICT`)、助教 Q&A(`TA_QA`)、代碼對照 |
| `profile_data.py` → `profile/` | 全資料剖析,產生 `profile/results.pkl` 供 notebook 使用 |
| `idle_prototype.py`、`idle_fleet.py` → `idle/` | 怠速分析;`idle/idle_fleet.html` 是 7 車總報告,`idle_V##.html` 是單車明細 |
| **2. research/:外部資料集與文獻** | |
| `1_external_data_sources.md` | 外部公開資料調查(結論:沒有可用的逐筆冷鏈資料) |
| `2_joint_delivery_sources.md` | 共同配送文獻與實證,標明一手、二手、未驗證 |
| `3_proposal_notes.md` | 寫 10/13 提案時的三份筆記合併:第一部分大綱與證據對照、第二部分初稿審閱、第三部分補充證據 |
| `4_last_mile_routing_paper.md` | 插入法論文(Rashidi 等,2025)的查核筆記,以及 Amazon 最後一哩資料集能否取得 |
| `papers/` | 論文全文 PDF(`Rashidi2025_last-mile_insertion_heuristic.pdf`) |
| `dataset_search/` | Kaggle、Hugging Face 資料集的搜尋腳本(`kaggle_check.py`)與候選清單 JSON,`1_external_data_sources.md` 的原始紀錄 |
| **3. poc/:共同配送試作** | |
| `1_joint_delivery_poc.ipynb` | 第一版試作(專程假設,−51%) |
| `2_a_group_rebuild.ipynb` | A 組重建與校準版(最新結果) |
| `3_remote_scan.ipynb` | 全臺有多少「像東北角」的偏遠門市,並把三個減碳方案放大到全臺同一基準比較(10/27) |
| `4_remote_routes.ipynb` | 三個物流中心(瑞芳、林口、高雄)實際路線中的偏遠受益型門市:專程或順路、邊際里程、放大估算下修(10/29) |
| `data/` | 東北角四品牌門市清單 `ne_stores_*.csv`:`osm` 是 OSM 原始抓取、`candidates` 是自動產生的候選、**`verified` 是逐店核對後的最終版**(模型只用這份) |
| `cache/` | OpenStreetMap、OSRM 查詢與求解結果的快取(`osm_*`、`osrm_*`、`rebuild_*`,以及全臺門市 `osm_convenience_tw.json`;`osrm_remote_routes.json` 是三場站偏遠趟次的距離矩陣);重跑 notebook 不會重新連網,刪掉才會重查 |
| `figures/` | 投影片用圖:`poc_v1_A_routes.png`、`poc_v1_B_routes.png`(第一版 A、B 組路線)、`calibrated_routes_3panel.png`(校準版三格直排,`2_a_group_rebuild.ipynb` 第 7.3 節產生)、`全家實際怎麼送東北角.png` |
| **根目錄** | |
| `1005進度報告.pdf`、`1019進度報告.pdf`、`1026進度報告.pdf` | 三次進度報告投影片 |
| `綠色工程專案研究POC Proposal.md` | POC 提案正文 |
| `綠色工程專案研究POC Proposal-1.docx` | 助教對各資料夾欄位問題的回答 |
| `vehicle_class_by_V.csv`、`delivery_plan_other_depots/` | 助教 10/25 補充的車型表與林口、高雄配送紀錄,分析見 `explore/data_exploration.ipynb` 第 8、9 節(不在 GitHub 上,助教已上傳到課程網站) |
| `全國5大超商資料集.csv` | 經濟部商業署 5 大超商分公司登記資料(只有地址;7-Eleven、萊爾富接近完整,全家、OK 缺加盟店),`3_remote_scan.ipynb` 用來核對 OSM 漏標 |
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
