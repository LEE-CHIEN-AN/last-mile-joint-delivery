"""抓 Kaggle 候選資料集的公開說明(不需登入),標出合成/模擬資料。

Run:  python research/dataset_search/kaggle_check.py
Writes research/dataset_search/kaggle_candidates.json
"""
import json
import os
import re
import time
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
CANDIDATES = [
    # 冷鏈 / 溫度
    "skarin/cold-chain-shipment-silent-failure-dataset",
    "u201411546/data-sets-cold-chain-milk",
    "datasetengineer/logistics-and-supply-chain-dataset",
    "ziya07/smart-logistics-supply-chain-dataset",
    # 車載 / 油耗 / 怠速
    "ankitp013/automobile-telematics-dataset",
    "imtkaggleteam/fleet-vehicles-fuel-consumption",
    "yashdev01/vehicle-energy-and-telemetry-dataset",
    "eron93br/obd2data",
    "pedro2025/obd2-panel-opel-2012",
    "tejalaveti2306/vehicle-maintenance-telemetry-data",
    "syednaveed05/logistics-fleet-data",
    "datasetengineer/logistics-vehicle-maintenance-history-dataset",
    # 最後一哩 / 路線 / 排放
    "karpzilla/indian-quick-commerce-last-mile-dataset",
    "paulkamande/lade-last-mile-delivery-dataset-shanghai-subset",
    "dataworld199/carbon-emission-fleet-dataset",
    "meissydanjiah/last-mile-delivery",
    "kundanbedmutha/delivery-logistics-dataset-india-multi-partner",
    "sujalsuthar/amazon-delivery-dataset",
    "ramakrishnanthiyagu/delivery-truck-trips-data",
    "yogape/logistics-operations-database",
    "programmer3/logistics-operations-and-risk-dataset",
    "ziya07/ev-energy-consumption-dataset",
]
SYN = re.compile(r"synthetic|simulat|generated|fictional|fictitious|artificial|faker|mock|hypothetical", re.I)


def get(ref):
    url = f"https://www.kaggle.com/api/v1/datasets/view/{ref}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


out = []
for ref in CANDIDATES:
    try:
        j = get(ref)
        desc = j.get("descriptionNullable") or ""
        out.append(dict(
            ref=ref, url=f"https://www.kaggle.com/datasets/{ref}", title=j.get("titleNullable"),
            subtitle=j.get("subtitleNullable"), license=j.get("licenseNameNullable"),
            mb=round((j.get("totalBytesNullable") or 0) / 1e6, 1), updated=j.get("lastUpdated"),
            usability=j.get("usabilityRatingNullable"), downloads=j.get("downloadCount"),
            synthetic_hits=sorted(set(m.lower() for m in SYN.findall(desc))), description=desc[:2500]))
        print(f"ok  {ref}  syn={out[-1]['synthetic_hits']}")
    except Exception as e:  # noqa: BLE001
        out.append(dict(ref=ref, error=str(e)))
        print(f"ERR {ref}: {e}")
    time.sleep(1)
json.dump(out, open(os.path.join(HERE, "kaggle_candidates.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
