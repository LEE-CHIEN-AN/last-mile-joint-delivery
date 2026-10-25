"""單車試算:把怠速切段、依地點與時間分類,估計「必要 / 技術可替代 / 可避免」怠速油耗。

Run:  python explore/idle_prototype.py [V19]
Writes explore/idle_prototype.html

怠速定義:引擎轉速 > 300 rpm 且車速 < 1 km/h。油耗 = 瞬時油耗率 (L/h) × 取樣間隔,
間隔 > 60 秒視為斷訊不計。分類門檻見 PARAMS,報告附敏感度分析。
"""
import glob
import html
import os
import sys

import numpy as np
import pandas as pd
import plotly.graph_objects as go

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from column_dictionary import TERMS_HTML  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = lambda *a: os.path.join(ROOT, *a)
VEH = sys.argv[1] if len(sys.argv) > 1 else "V19"
MONTHS = ["202502", "202503"]  # delivery_plan 只到 2025-03
OUT = P("explore", "idle", f"idle_{VEH}.html")
os.makedirs(os.path.dirname(OUT), exist_ok=True)

DC = (25.104573, 121.773384)  # 瑞芳 DC(store_master「瑞芳ＤＣ」);腹地大,半徑取 700 m,最近門市在 1.9 km 外
PARAMS = dict(
    rpm_on=300,          # 引擎運轉門檻
    v_stop=1.0,          # 視為靜止的車速 km/h
    max_gap_s=60,        # 取樣間隔超過即斷段
    dc_radius_m=700,     # 在 DC 範圍內
    store_radius_m=150,  # 在當趟門市範圍內
    any_store_radius_m=80,
    short_stop_min=3,    # 路途短停(號誌/塞車)上限
    dc_long_min=60,      # DC 怠速超過即列「可避免候選」
    unload_max_min=30,   # 門市卸貨超過即列「可避免候選」
    pre_arrival_min=5,   # 結束時間早於報到時間超過此值 → 到店前等候
    stop_window_h=3,     # 找當趟門市:報到時間 ±3 小時
)
DIESEL = 2.68  # kg CO2 / L(燃燒端)

# 類別 → (層級, 顏色)。類別色依 dataviz 預設類別色序;層級色用前三個槽位(地圖為 all-pairs)
CATS = {
    "路途短停": ("必要", "#2a78d6"),
    "門市卸貨": ("必要", "#1baf7a"),
    "DC 怠速(≤門檻)": ("技術可替代", "#eda100"),
    "DC 長時間怠速": ("可避免候選", "#eb6834"),
    "路途長停": ("可避免候選", "#e87ba4"),
    "到店前等候": ("可避免候選", "#4a3aa7"),
    "門市久停": ("可避免候選", "#e34948"),
}
TIERS = {"必要": "#2a78d6", "技術可替代": "#1baf7a", "可避免候選": "#eb6834"}


def log(m):
    print(m, flush=True)


def hav_m(lat1, lon1, lat2, lon2):
    lat1, lon1, lat2, lon2 = map(np.radians, (lat1, lon1, lat2, lon2))
    a = np.sin((lat2 - lat1) / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin((lon2 - lon1) / 2) ** 2
    return 2 * 6371000 * np.arcsin(np.sqrt(a))


# ------------------------------------------------------------------ load CAN
cols = ["GPS Time", "Speed", "Latitude", "Longitude", "Fix", "Engine speed(rpm)", "Engine Fuel Rate(L/H)",
        "Total fuel used(L)", "发动机总闲置燃油消耗(L)", "Vehicle speed (wheel based)(km/h)", "发动机总空闲时间(h)", "High resolution vehicle distance(m)"]
files = sorted(f for m in MONTHS for f in glob.glob(P("vehicle_can_telematics", VEH, f"{VEH}_{m}*.csv")))
log(f"{VEH}: {len(files)} files")
d = pd.concat([pd.read_csv(f, encoding="utf-8-sig", usecols=lambda c: c in cols, low_memory=False) for f in files])
d = d.rename(columns={"GPS Time": "t", "Speed": "v", "Latitude": "lat", "Longitude": "lon", "Engine speed(rpm)": "rpm",
                      "Engine Fuel Rate(L/H)": "rate", "Total fuel used(L)": "fuel_cum",
                      "发动机总闲置燃油消耗(L)": "idle_fuel_cum", "发动机总空闲时间(h)": "idle_h_cum",
                      "High resolution vehicle distance(m)": "odo", "Vehicle speed (wheel based)(km/h)": "v_wheel"})
d["t"] = pd.to_datetime(d["t"], errors="coerce")
for c in ["v", "v_wheel", "lat", "lon", "rpm", "rate", "fuel_cum", "idle_fuel_cum", "idle_h_cum", "odo"]:
    d[c] = pd.to_numeric(d[c], errors="coerce")
d = d.dropna(subset=["t"]).sort_values("t").drop_duplicates("t").reset_index(drop=True)
# GPS 車速在失去定位(隧道)時會變 0,誤把行駛當怠速 → 優先用 CAN 輪速
d["v_gps"] = d["v"]
d["v"] = d["v_wheel"].fillna(d["v_gps"])
d.loc[d["Fix"].astype(str) != "Valid", ["lat", "lon"]] = np.nan
d[["lat", "lon"]] = d[["lat", "lon"]].ffill(limit=12)  # 短暫失效(≤約 2 分鐘)沿用前一個有效座標
d["dt"] = d["t"].shift(-1).sub(d["t"]).dt.total_seconds()
d["gap"] = d["dt"] > PARAMS["max_gap_s"]
d["dt_c"] = d["dt"].where(~d["gap"], 0).fillna(0)
d["fuel_i"] = d["rate"].fillna(0) * d["dt_c"] / 3600
d["on"] = d["rpm"] > PARAMS["rpm_on"]
d["idle"] = d["on"] & (d["v"] < PARAMS["v_stop"])

# ------------------------------------------------------------------ episodes
brk = (d["idle"] != d["idle"].shift()) | d["gap"].shift(fill_value=False)
d["seg"] = brk.cumsum()
ep = d[d["idle"]].groupby("seg").agg(start=("t", "min"), end=("t", "max"), dur_s=("dt_c", "sum"),
                                     fuel=("fuel_i", "sum"), lat=("lat", "median"), lon=("lon", "median"),
                                     rpm=("rpm", "median"), n=("t", "size")).reset_index(drop=True)
ep["dur_min"] = ep["dur_s"] / 60
ep = ep[ep["dur_s"] > 0].copy()
log(f"idle episodes: {len(ep):,}")

# ------------------------------------------------------------------ stops & stores
st = pd.read_csv(P("store_master", "store_master.csv"), encoding="utf-8-sig")
st["key"] = st["name"].str.replace("^全家", "", regex=True).str.replace("店$", "", regex=True)
st = st.drop_duplicates("key")
dp = pd.concat([pd.read_csv(f, encoding="utf-8-sig", dtype=str)
                for f in glob.glob(P("delivery_plan", "monthly", "2025-0[23]*.csv"))])
dp = dp[(dp["Car_licence"] == VEH) & ~dp["Store_id"].str.contains("3001888888", na=False)].copy()
dp["TaskType_id"] = dp["TaskType_id"].str.zfill(2)
dp["arr"] = pd.to_datetime(dp["Ac_Arrive_dt_02"], errors="coerce")
dp["key"] = dp["Store_Name"].str.replace("店$", "", regex=True)
dp = dp.merge(st[["key", "lat", "lng"]], on="key", how="left").dropna(subset=["arr"])
log(f"stops: {len(dp):,}, with coords {dp['lat'].notna().mean():.0%}")

# TMS 表訂與早到旗標(任務 12)
tm = pd.concat([pd.read_csv(f, encoding="utf-8-sig", dtype=str,
                            usecols=["Car_id", "last_dc", "Store_id", "Ac_Arrive_dt_01", "Im_arrive_dt_02", "Ex_Arrive_diff", "DiffStatus"])
                for f in glob.glob(P("tms_delivery_records", "RF", "2025", "0[23]", "*.csv"))])
tm = tm[(tm["Car_id"] == VEH) & (tm["last_dc"] == "0")].copy()
tm["arr"] = pd.to_datetime(tm["Ac_Arrive_dt_01"], errors="coerce")
tm["Ex_Arrive_diff"] = pd.to_numeric(tm["Ex_Arrive_diff"], errors="coerce")
dp = dp.merge(tm[["Store_id", "arr", "Ex_Arrive_diff", "DiffStatus"]], on=["Store_id", "arr"], how="left")

# ------------------------------------------------------------------ classify
stop_arr = dp["arr"].values.astype("datetime64[s]").astype(np.int64)
stop_lat, stop_lng = dp["lat"].values, dp["lng"].values
win = PARAMS["stop_window_h"] * 3600


def classify(e):
    if np.isnan(e["lat"]):
        return "無定位", None
    if hav_m(e["lat"], e["lon"], *DC) <= PARAMS["dc_radius_m"]:
        return ("DC 怠速(≤門檻)" if e["dur_min"] <= PARAMS["dc_long_min"] else "DC 長時間怠速"), None
    s = np.datetime64(e["start"], "s").astype(np.int64)
    cand = np.where((np.abs(stop_arr - s) <= win) & ~np.isnan(stop_lat))[0]
    if len(cand):
        dist = hav_m(e["lat"], e["lon"], stop_lat[cand], stop_lng[cand])
        j = cand[np.argmin(dist)]
        if dist.min() <= PARAMS["store_radius_m"]:
            end = np.datetime64(e["end"], "s").astype(np.int64)
            if stop_arr[j] - end > PARAMS["pre_arrival_min"] * 60:
                return "到店前等候", j
            return ("門市卸貨" if e["dur_min"] <= PARAMS["unload_max_min"] else "門市久停"), j
    near = hav_m(e["lat"], e["lon"], st["lat"].values, st["lng"].values).min()
    if near <= PARAMS["any_store_radius_m"]:
        return ("門市卸貨" if e["dur_min"] <= PARAMS["unload_max_min"] else "門市久停"), None
    return ("路途短停" if e["dur_min"] < PARAMS["short_stop_min"] else "路途長停"), None


res = ep.apply(classify, axis=1, result_type="expand")
ep["cat"], ep["stop_idx"] = res[0], res[1]
ep["tier"] = ep["cat"].map(lambda c: CATS.get(c, ("無定位",))[0])
ep["day"] = ep["start"].dt.date

# ------------------------------------------------------------------ totals & validation
days = d["t"].dt.date.nunique()
km = (d["odo"].max() - d["odo"].min()) / 1000
fuel_total_cnt = d["fuel_cum"].max() - d["fuel_cum"].min()
idle_fuel_cnt = d["idle_fuel_cum"].max() - d["idle_fuel_cum"].min()
idle_h_cnt = d["idle_h_cum"].max() - d["idle_h_cum"].min()
fuel_total_int = d["fuel_i"].sum()
idle_fuel_int = ep["fuel"].sum()
idle_h_int = ep["dur_s"].sum() / 3600
by_cat = ep.groupby("cat").agg(episodes=("fuel", "size"), hours=("dur_s", lambda s: s.sum() / 3600),
                               fuel=("fuel", "sum"), med_min=("dur_min", "median")).reindex(list(CATS) + ["無定位"]).dropna(how="all")
by_cat["tier"] = [CATS.get(c, ("無定位",))[0] for c in by_cat.index]
by_cat["share_idle"] = by_cat["fuel"] / idle_fuel_int
by_cat["share_total"] = by_cat["fuel"] / fuel_total_int
by_tier = by_cat.groupby("tier")["fuel"].sum()
log(by_cat.round(2).to_string())
log(f"km {km:.0f}, fuel(counter) {fuel_total_cnt:.0f} L, fuel(integrated) {fuel_total_int:.0f} L; "
    f"idle fuel counter {idle_fuel_cnt:.0f} L vs integrated {idle_fuel_int:.0f} L; idle h counter {idle_h_cnt:.0f} vs {idle_h_int:.0f}")


# ------------------------------------------------------------------ sensitivity
def avoidable_share(short_min, dc_min, unload_min):
    c = ep["cat"].copy()
    at_dc = c.isin(["DC 怠速(≤門檻)", "DC 長時間怠速"])
    at_store = c.isin(["門市卸貨", "門市久停"])
    on_road = c.isin(["路途短停", "路途長停"])
    avoid = (at_dc & (ep["dur_min"] > dc_min)) | (at_store & (ep["dur_min"] > unload_min)) \
        | (on_road & (ep["dur_min"] >= short_min)) | (c == "到店前等候")
    return ep.loc[avoid, "fuel"].sum()


sens = []
for s_m in (2, 3, 5):
    for dc_m in (30, 60, 120):
        for u_m in (20, 30, 45):
            a = avoidable_share(s_m, dc_m, u_m)
            sens.append(dict(短停門檻=s_m, DC門檻=dc_m, 卸貨門檻=u_m, 可避免L=a, 佔怠速=a / idle_fuel_int, 佔總油耗=a / fuel_total_int))
sens = pd.DataFrame(sens)

# early arrival vs dwell (TMS task 12)
st_ep = ep.dropna(subset=["stop_idx"]).copy()
st_ep["DiffStatus"] = st_ep["stop_idx"].astype(int).map(dp["DiffStatus"])
st_ep["ex"] = st_ep["stop_idx"].astype(int).map(dp["Ex_Arrive_diff"])
dwell = st_ep.dropna(subset=["DiffStatus"]).groupby("DiffStatus").agg(
    stops=("dur_min", "size"), med_min=("dur_min", "median"), p90_min=("dur_min", lambda s: s.quantile(.9)),
    fuel=("fuel", "sum"))
# 每次停靠的怠速總時間:同一停靠的各段相加;無怠速記 0;對不到座標的停靠無法判斷,排除
per_stop = st_ep.groupby(st_ep["stop_idx"].astype(int))["dur_min"].sum()
judged = dp[dp["lat"].notna() & dp["DiffStatus"].notna()].copy()
judged["idle_total_min"] = per_stop.reindex(judged.index).fillna(0)
dwell_stop = judged.groupby("DiffStatus")["idle_total_min"].agg(
    stops="size", med_min="median", mean_min="mean", p90_min=lambda s: s.quantile(.9),
    zero_share=lambda s: (s == 0).mean())

# ------------------------------------------------------------------ charts
first = [True]
LAYOUT = dict(paper_bgcolor="#fcfcfb", plot_bgcolor="#fcfcfb", font=dict(family="Noto Sans TC, Microsoft JhengHei", size=12, color="#0b0b0b"),
              margin=dict(t=48, b=40, l=60, r=20), hoverlabel=dict(bgcolor="#ffffff", font_color="#0b0b0b"))


def fh(fig, h=380):
    fig.update_layout(height=h, **LAYOUT)
    fig.update_xaxes(gridcolor="#ebebea", linecolor="#c9c8c4")
    fig.update_yaxes(gridcolor="#ebebea", linecolor="#c9c8c4")
    inc = "cdn" if first[0] else False
    first[0] = False
    return fig.to_html(full_html=False, include_plotlyjs=inc, config={"displaylogo": False})


bc = by_cat.reset_index().rename(columns={"index": "cat"}).sort_values("fuel")
bc = bc[bc["cat"] != "無定位"]
f = go.Figure(go.Bar(x=bc["fuel"], y=bc["cat"], orientation="h",
                     marker=dict(color=[CATS[c][1] for c in bc["cat"]], cornerradius=4),
                     text=[f"{v:,.0f} L · {s:.0%}" for v, s in zip(bc["fuel"], bc["share_idle"])], textposition="outside",
                     customdata=np.stack([bc["tier"], bc["hours"], bc["episodes"], bc["med_min"]], axis=1),
                     hovertemplate="%{y}<br>層級:%{customdata[0]}<br>油耗 %{x:,.0f} L<br>時數 %{customdata[1]:,.0f} h"
                                   "<br>段數 %{customdata[2]:,}<br>單段中位數 %{customdata[3]:.1f} 分<extra></extra>"))
f.update_layout(title="各類怠速油耗(L,標示佔怠速油耗比例)", showlegend=False, bargap=0.35)
f.update_xaxes(title="L", range=[0, bc["fuel"].max() * 1.3])
ch_cat = fh(f, 360)

dd = ep[ep["cat"] != "無定位"].groupby(["day", "cat"])["dur_s"].sum().div(3600).unstack(fill_value=0)
f = go.Figure()
for c in CATS:
    if c in dd:
        f.add_bar(x=dd.index.astype(str), y=dd[c], name=c, marker=dict(color=CATS[c][1], line=dict(color="#fcfcfb", width=1)),
                  hovertemplate=c + " %{y:.1f} h<extra>%{x}</extra>")
f.update_layout(barmode="stack", title="每日怠速時數(依類別堆疊)", legend=dict(orientation="h", y=-0.2), bargap=0.25)
f.update_yaxes(title="小時")
ch_day = fh(f, 420)

mp = ep.dropna(subset=["lat"])
f = go.Figure()
for t_, col in TIERS.items():
    s = mp[mp["tier"] == t_]
    f.add_trace(go.Scattermapbox(lat=s["lat"], lon=s["lon"], mode="markers", name=t_,
                                 marker=dict(size=np.clip(np.sqrt(s["fuel"]) * 9, 5, 26), color=col, opacity=.75),
                                 text=[f"{c}<br>{a:%m-%d %H:%M} · {m:.0f} 分 · {fu:.2f} L" for c, a, m, fu in
                                       zip(s["cat"], s["start"], s["dur_min"], s["fuel"])],
                                 hovertemplate="%{text}<extra></extra>"))
f.update_layout(mapbox=dict(style="white-bg", center=dict(lat=25.08, lon=121.70), zoom=10,
                            layers=[dict(below="traces", sourcetype="raster", sourceattribution="Tiles © Esri",
                                         source=["https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}"])]),
                legend=dict(orientation="h", y=1.04), margin=dict(t=30, b=0, l=0, r=0))
ch_map = fh(f, 560)

# one typical day timeline
day_fuel = ep.groupby("day")["fuel"].sum()
pick = day_fuel.sort_values().index[len(day_fuel) // 2]
dday = d[d["t"].dt.date == pick]
f = go.Figure()
f.add_scatter(x=dday["t"], y=dday["v"], mode="lines", line=dict(color="#52514e", width=1.5), name="車速",
              hovertemplate="%{x|%H:%M:%S} · %{y:.0f} km/h<extra></extra>")
for _, e in ep[ep["day"] == pick].iterrows():
    if e["cat"] in CATS and e["dur_min"] >= 1:
        f.add_vrect(x0=e["start"], x1=e["end"], fillcolor=CATS[e["cat"]][1], opacity=.35, line_width=0)
for c in CATS:  # legend proxies
    f.add_scatter(x=[None], y=[None], mode="markers", marker=dict(size=10, color=CATS[c][1], symbol="square"), name=c)
f.update_layout(title=f"{pick} 一日時間軸(灰線=車速;色塊=≥1 分鐘的怠速段)", legend=dict(orientation="h", y=-0.25))
f.update_yaxes(title="km/h")
ch_tl = fh(f, 420)


# ------------------------------------------------------------------ html
def tbl(df, fmt):
    h = "<table><thead><tr>" + "".join(f"<th>{html.escape(str(c))}</th>" for c in df.columns) + "</tr></thead><tbody>"
    for _, r in df.iterrows():
        h += "<tr>" + "".join(f"<td class='num'>{fmt.get(c, '{}').format(r[c])}</td>" for c in df.columns) + "</tr>"
    return h + "</tbody></table>"


avoid = by_tier.get("可避免候選", 0)
tech = by_tier.get("技術可替代", 0)
need = by_tier.get("必要", 0)
kpi = f"""<div class='kpis'>
<div><b>{days}</b>天 · {km:,.0f} km</div>
<div><b>{fuel_total_cnt:,.0f} L</b>總油耗(ECU 計數器)</div>
<div><b>{idle_fuel_int / fuel_total_int:.0%}</b>怠速油耗佔比<br><small>{idle_fuel_int:,.0f} L · {idle_h_int:,.0f} h</small></div>
<div class='t1'><b>{need / fuel_total_int:.1%}</b>必要<br><small>{need:,.0f} L</small></div>
<div class='t2'><b>{tech / fuel_total_int:.1%}</b>技術可替代<br><small>{tech:,.0f} L</small></div>
<div class='t3'><b>{avoid / fuel_total_int:.1%}</b>可避免候選<br><small>{avoid:,.0f} L ≈ {avoid * DIESEL:,.0f} kg CO₂</small></div>
</div>"""

cat_tbl = by_cat.reset_index().rename(columns={"cat": "類別", "index": "類別"})
cat_tbl = cat_tbl[["類別", "tier", "episodes", "hours", "med_min", "fuel", "share_idle", "share_total"]]
cat_tbl.columns = ["類別", "層級", "段數", "時數 h", "單段中位數 分", "油耗 L", "佔怠速", "佔總油耗"]
cat_html = tbl(cat_tbl, {"段數": "{:,.0f}", "時數 h": "{:,.1f}", "單段中位數 分": "{:.1f}", "油耗 L": "{:,.1f}",
                         "佔怠速": "{:.1%}", "佔總油耗": "{:.1%}"})
sens_html = tbl(sens, {"可避免L": "{:,.0f}", "佔怠速": "{:.1%}", "佔總油耗": "{:.1%}"})
dw = dwell.reset_index()
dw["DiffStatus"] = pd.to_numeric(dw["DiffStatus"]).map({-1: "早到(< 表訂−60 分)", 0: "準時", 1: "遲到"})
dw.columns = ["TMS 判定", "怠速段數", "單段長度中位數 分", "單段長度 p90 分", "油耗 L"]
dwell_html = tbl(dw, {"怠速段數": "{:,.0f}", "單段長度中位數 分": "{:.1f}", "單段長度 p90 分": "{:.1f}", "油耗 L": "{:,.1f}"})
ds = dwell_stop.reset_index()
ds["DiffStatus"] = pd.to_numeric(ds["DiffStatus"]).map({-1: "早到(< 表訂−60 分)", 0: "準時", 1: "遲到"})
ds.columns = ["TMS 判定", "停靠數", "每次停靠怠速總時間 中位數 分", "平均 分", "p90 分", "完全沒怠速的比例"]
dwell_stop_html = tbl(ds, {"停靠數": "{:,.0f}", "每次停靠怠速總時間 中位數 分": "{:.1f}", "平均 分": "{:.1f}",
                           "p90 分": "{:.1f}", "完全沒怠速的比例": "{:.0%}"})

val = (f"<ul><li>總油耗:ECU 累計計數器 {fuel_total_cnt:,.0f} L,油耗率積分 {fuel_total_int:,.0f} L(差 {fuel_total_int / fuel_total_cnt - 1:+.1%})。</li>"
       f"<li>怠速油耗:ECU 怠速計數器 {idle_fuel_cnt:,.0f} L,本試算切段積分 {idle_fuel_int:,.0f} L(差 {idle_fuel_int / idle_fuel_cnt - 1:+.1%});"
       f"怠速時數:計數器 {idle_h_cnt:,.0f} h,試算 {idle_h_int:,.0f} h。</li>"
       f"<li>無定位(GPS 無效)的怠速段佔怠速油耗 {by_cat['share_idle'].get('無定位', 0):.1%},未分類。</li>"
       f"<li>當趟門市可對到座標的停靠比例 {dp['lat'].notna().mean():.0%};對不到的門市改用「任一門市 {PARAMS['any_store_radius_m']} m 內」判斷。</li></ul>")

params_html = "".join(f"<tr><td>{k}</td><td class='num'>{v}</td></tr>" for k, v in PARAMS.items())

page = f"""<!doctype html><html lang="zh-Hant"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>怠速切段試算</title>
<style>
:root{{--fg:#0b0b0b;--mut:#52514e;--bd:#e3e2de;--bg:#f4f4f2;--card:#fcfcfb;--acc:#1f6f54}}
body{{font-family:'Noto Sans TC','Microsoft JhengHei',sans-serif;max-width:1180px;margin:0 auto;padding:16px 20px;color:var(--fg);background:var(--bg);line-height:1.65}}
h1{{color:var(--acc);margin-bottom:2px}}h2{{border-left:5px solid var(--acc);padding-left:10px;margin-top:6px}}
.card{{background:var(--card);border:1px solid var(--bd);border-radius:10px;padding:10px 22px 18px;margin:18px 0}}
.mut{{color:var(--mut)}}table{{border-collapse:collapse;width:100%;font-size:13px;margin:8px 0}}
th,td{{border-bottom:1px solid var(--bd);padding:5px 8px;text-align:left}}th{{background:#efeeeb}}.num{{font-variant-numeric:tabular-nums}}
.kpis{{display:flex;flex-wrap:wrap;gap:10px;margin:10px 0}}.kpis div{{flex:1 1 140px;background:#efeeeb;border-radius:8px;padding:8px 12px;color:var(--mut);font-size:13px;border-top:4px solid #c9c8c4}}
.kpis b{{display:block;font-size:22px;color:var(--fg)}}.kpis .t1{{border-top-color:{TIERS['必要']}}}.kpis .t2{{border-top-color:{TIERS['技術可替代']}}}.kpis .t3{{border-top-color:{TIERS['可避免候選']}}}
.tw{{max-height:360px;overflow:auto}}
</style></head><body>
<h1>怠速切段試算 · {VEH}</h1>
<p class='mut'>2025-02 ~ 2025-03 · 瑞芳 DC · 由 explore/idle_prototype.py 產生。怠速 = 引擎轉速 &gt; {PARAMS['rpm_on']} rpm 且車速 &lt; {PARAMS['v_stop']} km/h。</p>
{TERMS_HTML}
<div class='card'><h2>結果</h2>{kpi}{ch_cat}
<h3>分類規則與層級</h3>
<table><thead><tr><th>類別</th><th>判斷方式</th><th>層級</th><th>理由</th></tr></thead><tbody>
<tr><td>路途短停</td><td>不在 DC/門市,單段 &lt; {PARAMS['short_stop_min']} 分</td><td>必要</td><td>號誌、塞車、讓車</td></tr>
<tr><td>門市卸貨</td><td>在當趟門市 {PARAMS['store_radius_m']} m 內、報到後,單段 ≤ {PARAMS['unload_max_min']} 分</td><td>必要</td><td>卸貨時冷機需運轉</td></tr>
<tr><td>DC 怠速(≤門檻)</td><td>DC {PARAMS['dc_radius_m']} m 內,單段 ≤ {PARAMS['dc_long_min']} 分</td><td>技術可替代</td><td>推測為裝貨/預冷;DC 岸電或電動冷機可取代引擎供冷</td></tr>
<tr><td>DC 長時間怠速</td><td>DC 內,單段 &gt; {PARAMS['dc_long_min']} 分</td><td>可避免候選</td><td>長時間待命未熄火(若為預冷需求則應改列技術可替代,待確認)</td></tr>
<tr><td>路途長停</td><td>不在 DC/門市,單段 ≥ {PARAMS['short_stop_min']} 分</td><td>可避免候選</td><td>休息、等候未熄火</td></tr>
<tr><td>到店前等候</td><td>在當趟門市旁,但結束時間早於報到時間 {PARAMS['pre_arrival_min']} 分以上</td><td>可避免候選</td><td>早到、等收貨</td></tr>
<tr><td>門市久停</td><td>在門市旁,單段 &gt; {PARAMS['unload_max_min']} 分</td><td>可避免候選</td><td>超出一般卸貨時間</td></tr>
</tbody></table>
<div class='tw'>{cat_html}</div></div>
<div class='card'><h2>怠速發生在哪裡</h2><p class='mut'>點的大小 = 該段油耗;顏色 = 層級。</p>{ch_map}</div>
<div class='card'><h2>每日分佈</h2>{ch_day}{ch_tl}</div>
<div class='card'><h2>早到會造成等候嗎?(TMS 任務 12)</h2>
<p class='mut'>比較 TMS 判定為早到 / 準時的停靠。主要指標是<b>每次停靠的怠速總時間</b>(同一停靠的各段怠速相加,無怠速記 0;對不到門市座標的停靠不列入)。</p>{dwell_stop_html}
<p class='mut'>輔助:門市旁每一段怠速的長度(一次停靠常切成好幾段)。</p>{dwell_html}</div>
<div class='card'><h2>敏感度:門檻改變時,可避免候選佔多少?</h2>
<p class='mut'>「可避免」= 路途停等 ≥ 短停門檻 + DC 怠速 &gt; DC 門檻 + 門市停留 &gt; 卸貨門檻 + 到店前等候。</p><div class='tw'>{sens_html}</div></div>
<div class='card'><h2>驗證與限制</h2>{val}
<ul><li>沒有冷藏機(TRU)或 PTO 訊號,無法直接判斷怠速是否在供冷;「必要/可替代/可避免」是依地點與時長的推論。</li>
<li>只有一輛車、兩個月;結果需在其他 6 輛車上重做才能推廣。</li>
<li>碳排僅計燃燒端(柴油 {DIESEL} kg CO₂/L)。</li></ul>
<h3>參數</h3><table>{params_html}</table></div>
</body></html>"""
open(OUT, "w", encoding="utf-8").write(page)
log(f"wrote {OUT}")
