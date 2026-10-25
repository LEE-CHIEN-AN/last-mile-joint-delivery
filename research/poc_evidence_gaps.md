# POC 提案與 A 組重建:補充證據

> 查詢日期:2026-10-18。每個數字都已開啟原始網頁核對;文獻沿用 `joint_delivery_sources.md` 已以 Crossref 確認 DOI 的條目。
> 用途:(1) 提案第一節「為什麼值得解決」的臺灣層級數據;(2) `poc/a_group_rebuild.ipynb` 的方法依據與比較基準。

---

## 1. 臺灣層級背景數據

| 項目 | 數字 | 年度 / 時點 | 出處 | 核對 |
|---|---|---|---|---|
| 運輸部門溫室氣體排放量 | 約 35.517 百萬公噸 CO₂e | 2024 年 | 環境部氣候變遷署「氣候公民對話平臺:運輸部門」,引用《國家溫室氣體排放清冊報告(2026 年版)》 https://www.cca.gov.tw/climatetalks/emission-and-reduction/sectoral/transportation/1877.html | 已核對頁面原文 |
| 運輸部門佔全國排放 | 約 13.00% | 2024 年 | 同上;頁面說明排放「主要來自公路運輸(如:汽機車用油)」,未列公路運輸佔比 | 已核對 |
| 全國總排放量 | 約 273.161 百萬公噸 CO₂e(扣除碳匯後淨排放 251.404) | 2024 年 | 《國家溫室氣體排放清冊報告(2026 年版)》,氣候變遷署出版品頁 https://www.cca.gov.tw/information-service/publications/national-ghg-inventory-report/34874.html | 僅見搜尋摘要,**未開啟原文**,引用前請核對 |
| 全臺便利商店店數 | 14,236 家(年增 3.0%) | 2025 年 8 月 | 經濟部統計處新聞稿〈我國便利商店營業額穩定成長,2025年可望續創新高〉(2025-10-16),資料來源標示「流通快訊統計」 https://www.moea.gov.tw/MNS/populace/news/News.aspx?kind=1&menu_id=40&news_id=120778 | 已核對 |
| 每家便利商店服務人口 | 臺灣 1,659 人/店;日本 2,180 人/店 | 2025 年 7 月 | 同上 | 已核對 |
| 便利商店營業額 | 4,235 億元(2024 年);2,920 億元(2025 年 1–8 月,年增 4.3%) | 2024–2025 | 同上 | 已核對 |

**可直接用於提案第一節的句子:**

> 運輸部門是臺灣第三大溫室氣體排放來源之一,2024 年排放約 35.5 百萬公噸 CO₂e,佔全國約 13%,且主要來自公路運輸(環境部氣候變遷署,2026)。便利商店是高度依賴公路配送的通路:全臺 2025 年 8 月已有 14,236 家,平均每 1,659 人就有一家,密度高於日本(經濟部統計處,2025)。

(「第三大」這個排名未經核對,若要使用請另查清冊各部門數字;保守寫法可刪去排名。)

---

## 2. A 組重建的方法依據(文獻)

| 用在 notebook 的哪裡 | 文獻 | 重點 |
|---|---|---|
| 綜效的定義:各自配送成本加總 − 共同配送成本 | Cruijssen, F., Bräysy, O., Dullaert, W., Fleuren, H., & Salomon, M. (2007). Joint route planning under varying market conditions. *IJPDLM*, 37(4), 287–304. DOI: 10.1108/09600030710752514 | 多家業者訂單合併排路線,與各自配送比較;摘要指出綜效可達約 30% |
| B 組屬於哪一類合作 | Gansterer, M., & Hartl, R. F. (2018). Collaborative vehicle routing: A survey. *EJOR*, 268(1), 1–12. DOI: 10.1016/j.ejor.2017.10.023 | 合作路線分三類;B 組把所有業者門市合在一起解一個路線問題,屬「集中式合作規劃」 |
| CO₂ 效益量級 | Ballot, E., & Fontane, F. (2010). Reducing transportation CO₂ emissions through pooling of supply networks. *Production Planning & Control*, 21(6), 640–650. DOI: 10.1080/09537287.2010.489276 | 法國零售供應網路 pooling,CO₂ 至少可減 25% |
| 便利商店情境的量級 | Zhang 等 (2024). Optimization of multi-temperature joint distribution paths for convenience store chains. *Tehnički vjesnik*, 31(5). DOI: 10.17559/TV-20230812000875 | 同一連鎖內多溫層共配,總成本優化 26.35%(非跨品牌) |
| 成本或利益分攤 | Krajewska 等 (2008), *JORS*, 59(11), 1483–1491, DOI: 10.1057/palgrave.jors.2602489;Guajardo & Rönnqvist (2016), *ITOR*, 23(3), 371–392, DOI: 10.1111/itor.12205 | Shapley value 分配合作節省;分攤方法回顧 |
| 求解器 | Wouda, N. A., Lan, L., & Kool, W. (2024). PyVRP: A high-performance VRP solver package. *INFORMS Journal on Computing*, 36(4), 943–955. DOI: 10.1287/ijoc.2023.0055 | 本分析使用的路線求解器 |
| 跨品牌超商實證 | 日本全家等(2022-10-17)新聞稿,函館西南部 7 店共配:距離 −22%、時間 −20%、CO₂ −36.2 kg | 見 `joint_delivery_sources.md` J2-② |

**比較時要注意口徑:** 文獻的 25–30% 多以「整個配送網路」或總成本計算;本分析的「邊際里程減幅」只算服務東北角門市多跑的那一段,分母小,比例自然偏高;「路網總里程減幅」才與文獻口徑接近。函館 −22% 是兩品牌、7 家偏遠門市區內段的實測,介於兩者之間。

---

## 3. 找不到或未核對

- 2025 年版清冊的 2023 年運輸部門數字(36.294 百萬公噸、13.03%)只見於搜尋摘要,未開啟原文;本文件改用已核對的 2026 年版 2024 年數字。
- 公路貨運(貨車)佔運輸部門排放的比例:氣候變遷署頁面未列,未找到第一手數字。
- 運輸部門在全國各部門的排名:未核對。
