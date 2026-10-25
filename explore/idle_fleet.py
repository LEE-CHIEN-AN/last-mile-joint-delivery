"""對 7 輛有實測油耗的車各跑一次 idle_prototype.py,彙整成 explore/idle/idle_fleet.html。

Run:  python explore/idle_fleet.py      (約 5–8 分鐘)
每輛車的明細報告另存 explore/idle/idle_V##.html。
"""
import html
import os
import pickle
import runpy
import sys

import numpy as np
import pandas as pd
import plotly.graph_objects as go

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from column_dictionary import TERMS_HTML  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "idle", "idle_fleet.html")
CACHE = os.path.join(HERE, "idle", "fleet_results.pkl")
VEHS = ["V04", "V06", "V07", "V09", "V17", "V18", "V19"]
TIERS = {"必要": "#2a78d6", "技術可替代": "#1baf7a", "可避免候選": "#eb6834"}
DIESEL = 2.68

rows, cats, sens_all, dwell_all, dstop_all = [], [], [], [], []
if os.path.exists(CACHE) and "--rerun" not in sys.argv:
    rows, cats, sens_all, dwell_all, dstop_all = pickle.load(open(CACHE, "rb"))
else:
    for v in VEHS:
        print(f"== {v}", flush=True)
        sys.argv = ["idle_prototype.py", v]
        g = runpy.run_path(os.path.join(HERE, "idle_prototype.py"))
        bc, dp, d = g["by_cat"], g["dp"], g["d"]
        tier = bc.groupby("tier")["fuel"].sum()
        mix = dp["TaskType_id"].value_counts(normalize=True)
        rows.append(dict(
            車輛=v, 天數=g["days"], km=g["km"], 總油耗L=g["fuel_total_cnt"], L100=g["fuel_total_cnt"] / g["km"] * 100,
            怠速油耗L=g["idle_fuel_int"], 怠速佔比=g["idle_fuel_int"] / g["fuel_total_int"],
            怠速佔比_計數器=g["idle_fuel_cnt"] / g["fuel_total_cnt"],
            必要=tier.get("必要", 0) / g["fuel_total_int"], 技術可替代=tier.get("技術可替代", 0) / g["fuel_total_int"],
            可避免候選=tier.get("可避免候選", 0) / g["fuel_total_int"],
            必要L=tier.get("必要", 0), 技術可替代L=tier.get("技術可替代", 0), 可避免候選L=tier.get("可避免候選", 0),
            怠速油耗差=g["idle_fuel_int"] / g["idle_fuel_cnt"] - 1, 怠速時數差=g["idle_h_int"] / g["idle_h_cnt"] - 1,
            輪速覆蓋=d["v_wheel"].notna().mean(), 門市座標對到=dp["lat"].notna().mean(), 停靠數=len(dp),
            任務組成=" ".join(f"{k}:{p:.0%}" for k, p in mix.head(3).items()),
        ))
        c = bc.reset_index().rename(columns={"cat": "類別", "index": "類別"})
        c["車輛"] = v
        c["佔總油耗"] = c["fuel"] / g["fuel_total_int"]
        cats.append(c)
        s = g["sens"].copy()
        s["車輛"] = v
        sens_all.append(s)
        dw = g["dwell"].reset_index()
        dw["車輛"] = v
        dwell_all.append(dw)
        dsp = g["dwell_stop"].reset_index()
        dsp["車輛"] = v
        dstop_all.append(dsp)
        del g
    pickle.dump((rows, cats, sens_all, dwell_all, dstop_all), open(CACHE, "wb"))

R = pd.DataFrame(rows)
C = pd.concat(cats, ignore_index=True)
S = pd.concat(sens_all, ignore_index=True)
D = pd.concat(dwell_all, ignore_index=True)
DS = pd.concat(dstop_all, ignore_index=True)

# fleet pooled
tot = R[["總油耗L", "怠速油耗L", "必要L", "技術可替代L", "可避免候選L", "km"]].sum()
pooled = {k: tot[f"{k}L"] / tot["總油耗L"] for k in TIERS}
pooled_idle = tot["怠速油耗L"] / tot["總油耗L"]
srng = S.groupby("車輛")["佔總油耗"].agg(["min", "median", "max"])
dwell_cmp = D.pivot_table(index="車輛", columns="DiffStatus", values="med_min", aggfunc="first")
dwell_n = D.pivot_table(index="車輛", columns="DiffStatus", values="stops", aggfunc="first")
print(R.round(3).to_string())
print(srng.round(3).to_string())
print(dwell_cmp.round(2).to_string())

# ------------------------------------------------------------------ charts
LAYOUT = dict(paper_bgcolor="#fcfcfb", plot_bgcolor="#fcfcfb",
              font=dict(family="Noto Sans TC, Microsoft JhengHei", size=12, color="#0b0b0b"),
              margin=dict(t=48, b=40, l=60, r=20), hoverlabel=dict(bgcolor="#ffffff", font_color="#0b0b0b"))
first = [True]


def fh(fig, h=380):
    fig.update_layout(height=h, **LAYOUT)
    fig.update_xaxes(gridcolor="#ebebea", linecolor="#c9c8c4")
    fig.update_yaxes(gridcolor="#ebebea", linecolor="#c9c8c4")
    inc = "cdn" if first[0] else False
    first[0] = False
    return fig.to_html(full_html=False, include_plotlyjs=inc, config={"displaylogo": False})


order = R.sort_values("怠速佔比")["車輛"].tolist() + ["全車隊"]
Rp = pd.concat([R, pd.DataFrame([{"車輛": "全車隊", **pooled}])], ignore_index=True).set_index("車輛").loc[order]
f = go.Figure()
for t_, col in TIERS.items():
    f.add_bar(y=Rp.index, x=Rp[t_], name=t_, orientation="h", marker=dict(color=col, line=dict(color="#fcfcfb", width=2)),
              text=[f"{x:.1%}" for x in Rp[t_]], textposition="inside", insidetextanchor="middle",
              hovertemplate="%{y} · " + t_ + " %{x:.1%}<extra></extra>")
f.update_layout(barmode="stack", title="各車怠速油耗佔總油耗(依層級堆疊)", legend=dict(orientation="h", y=1.1), bargap=0.3)
f.update_xaxes(tickformat=".0%", title="佔總油耗")
ch_tier = fh(f, 420)

f = go.Figure()
sr = srng.loc[[v for v in order if v in srng.index]]
for v, r in sr.iterrows():
    f.add_scatter(x=[r["min"], r["max"]], y=[v, v], mode="lines", line=dict(color="#c9c8c4", width=6), showlegend=False,
                  hoverinfo="skip")
f.add_scatter(x=sr["median"], y=sr.index, mode="markers", marker=dict(size=11, color=TIERS["可避免候選"],
              line=dict(color="#fcfcfb", width=2)), name="27 組門檻的中位數",
              customdata=np.stack([sr["min"], sr["max"]], axis=1),
              hovertemplate="%{y}<br>中位數 %{x:.1%}<br>範圍 %{customdata[0]:.1%} ~ %{customdata[1]:.1%}<extra></extra>")
f.update_layout(title="可避免候選佔總油耗:27 組門檻組合的範圍(灰條)與中位數", showlegend=False)
f.update_xaxes(tickformat=".0%", rangemode="tozero")
ch_sens = fh(f, 380)

cat_order = ["路途短停", "門市卸貨", "DC 怠速(≤門檻)", "DC 長時間怠速", "路途長停", "到店前等候", "門市久停"]
cat_col = {"路途短停": "#2a78d6", "門市卸貨": "#1baf7a", "DC 怠速(≤門檻)": "#eda100", "DC 長時間怠速": "#eb6834",
           "路途長停": "#e87ba4", "到店前等候": "#4a3aa7", "門市久停": "#e34948"}
Cp = C.pivot_table(index="車輛", columns="類別", values="佔總油耗", aggfunc="sum").reindex(order[:-1])
f = go.Figure()
for c in cat_order:
    if c in Cp:
        f.add_bar(y=Cp.index, x=Cp[c], name=c, orientation="h", marker=dict(color=cat_col[c], line=dict(color="#fcfcfb", width=2)),
                  hovertemplate="%{y} · " + c + " %{x:.1%}<extra></extra>")
f.update_layout(barmode="stack", title="各車怠速油耗(依類別)", legend=dict(orientation="h", y=-0.18), bargap=0.3)
f.update_xaxes(tickformat=".0%", title="佔總油耗")
ch_cat = fh(f, 440)


# ------------------------------------------------------------------ tables
def tbl(df, fmt, idx=False):
    df = df.reset_index() if idx else df
    h = "<table><thead><tr>" + "".join(f"<th>{html.escape(str(c))}</th>" for c in df.columns) + "</tr></thead><tbody>"
    for _, r in df.iterrows():
        h += "<tr>" + "".join(
            f"<td class='num'>{fmt.get(c, '{}').format(r[c]) if not (isinstance(r[c], float) and np.isnan(r[c])) else '—'}</td>"
            for c in df.columns) + "</tr>"
    return h + "</tbody></table>"


main = R[["車輛", "天數", "km", "L100", "停靠數", "任務組成", "怠速佔比", "怠速佔比_計數器", "必要", "技術可替代", "可避免候選"]].copy()
main.columns = ["車輛", "天數", "km", "L/100km", "停靠數", "任務組成(前三)", "怠速佔比(試算)", "怠速佔比(ECU)", "必要", "技術可替代", "可避免候選"]
pct = "{:.1%}"
main_html = tbl(main, {"km": "{:,.0f}", "L/100km": "{:.1f}", "停靠數": "{:,.0f}", "怠速佔比(試算)": pct, "怠速佔比(ECU)": pct,
                       "必要": pct, "技術可替代": pct, "可避免候選": pct})
qa = R[["車輛", "怠速油耗差", "怠速時數差", "輪速覆蓋", "門市座標對到"]].copy()
qa.columns = ["車輛", "怠速油耗:試算 vs ECU", "怠速時數:試算 vs ECU", "CAN 輪速覆蓋", "門市座標對到"]
qa_html = tbl(qa, {"怠速油耗:試算 vs ECU": "{:+.1%}", "怠速時數:試算 vs ECU": "{:+.1%}", "CAN 輪速覆蓋": pct, "門市座標對到": pct})
dwc = pd.DataFrame({"早到 單段長度中位數(分)": dwell_cmp.get("-1"), "準時 單段長度中位數(分)": dwell_cmp.get("0"),
                    "早到 怠速段數": dwell_n.get("-1"), "準時 怠速段數": dwell_n.get("0")}).reindex(VEHS)
ps_med = DS.pivot_table(index="車輛", columns="DiffStatus", values="med_min", aggfunc="first")
ps_mean = DS.pivot_table(index="車輛", columns="DiffStatus", values="mean_min", aggfunc="first")
ps_n = DS.pivot_table(index="車輛", columns="DiffStatus", values="stops", aggfunc="first")
psc = pd.DataFrame({"早到 中位數(分)": ps_med.get("-1"), "準時 中位數(分)": ps_med.get("0"),
                    "早到 平均(分)": ps_mean.get("-1"), "準時 平均(分)": ps_mean.get("0"),
                    "早到 停靠數": ps_n.get("-1"), "準時 停靠數": ps_n.get("0")}).reindex(VEHS)
print(psc.round(2).to_string())
ps_html = tbl(psc, {"早到 中位數(分)": "{:.1f}", "準時 中位數(分)": "{:.1f}", "早到 平均(分)": "{:.1f}", "準時 平均(分)": "{:.1f}",
                    "早到 停靠數": "{:,.0f}", "準時 停靠數": "{:,.0f}"}, idx=True)
dw_html = tbl(dwc, {"早到 單段長度中位數(分)": "{:.1f}", "準時 單段長度中位數(分)": "{:.1f}", "早到 怠速段數": "{:,.0f}", "準時 怠速段數": "{:,.0f}"}, idx=True)

FIND = os.path.join(HERE, "idle", "fleet_findings.html")
findings = open(FIND, encoding="utf-8").read() if os.path.exists(FIND) else ""

kpi = f"""<div class='kpis'>
<div><b>{len(R)}</b>輛車 · {tot['km']:,.0f} km · {tot['總油耗L']:,.0f} L</div>
<div><b>{pooled_idle:.1%}</b>怠速油耗佔比(全車隊)</div>
<div class='t1'><b>{pooled['必要']:.1%}</b>必要</div>
<div class='t2'><b>{pooled['技術可替代']:.1%}</b>技術可替代</div>
<div class='t3'><b>{pooled['可避免候選']:.1%}</b>可避免候選<br><small>門檻敏感度 {S['佔總油耗'].min():.1%} ~ {S['佔總油耗'].max():.1%}</small></div>
</div>"""

page = f"""<!doctype html><html lang="zh-Hant"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>怠速拆解 · 七車比較</title>
<style>
:root{{--fg:#0b0b0b;--mut:#52514e;--bd:#e3e2de;--bg:#f4f4f2;--card:#fcfcfb;--acc:#1f6f54}}
body{{font-family:'Noto Sans TC','Microsoft JhengHei',sans-serif;max-width:1180px;margin:0 auto;padding:16px 20px;color:var(--fg);background:var(--bg);line-height:1.65}}
h1{{color:var(--acc);margin-bottom:2px}}h2{{border-left:5px solid var(--acc);padding-left:10px;margin-top:6px}}
.card{{background:var(--card);border:1px solid var(--bd);border-radius:10px;padding:10px 22px 18px;margin:18px 0}}
.mut{{color:var(--mut)}}table{{border-collapse:collapse;width:100%;font-size:13px;margin:8px 0}}
th,td{{border-bottom:1px solid var(--bd);padding:5px 8px;text-align:left}}th{{background:#efeeeb}}.num{{font-variant-numeric:tabular-nums}}
.kpis{{display:flex;flex-wrap:wrap;gap:10px;margin:10px 0}}.kpis div{{flex:1 1 150px;background:#efeeeb;border-radius:8px;padding:8px 12px;color:var(--mut);font-size:13px;border-top:4px solid #c9c8c4}}
.kpis b{{display:block;font-size:22px;color:var(--fg)}}.kpis .t1{{border-top-color:{TIERS['必要']}}}.kpis .t2{{border-top-color:{TIERS['技術可替代']}}}.kpis .t3{{border-top-color:{TIERS['可避免候選']}}}
a{{color:var(--acc)}}
</style></head><body>
<h1>怠速拆解 · 七車比較</h1>
<p class='mut'>2025-02 ~ 2025-03 · 有 CAN 實測油耗的 7 輛車 · 由 explore/idle_fleet.py 產生 · 各車明細:
{' · '.join(f"<a href='idle_{v}.html'>{v}</a>" for v in VEHS)}</p>
{TERMS_HTML}
<div class='card'><h2>全車隊</h2>{kpi}{findings}</div>
<div class='card'><h2>各車比較</h2>{ch_tier}{main_html}</div>
<div class='card'><h2>怠速類別</h2>{ch_cat}</div>
<div class='card'><h2>結論對門檻敏不敏感</h2>
<p class='mut'>每輛車都用 27 組門檻組合重算(路途短停 2/3/5 分 × DC 長時間 30/60/120 分 × 卸貨 20/30/45 分)。</p>{ch_sens}</div>
<div class='card'><h2>早到會造成等候嗎?</h2><p class='mut'>TMS(任務 12)判定早到 vs 準時的停靠。主要指標:<b>每次停靠的怠速總時間</b>(同一停靠的各段怠速相加,無怠速記 0;對不到門市座標的停靠不列入)。</p>{ps_html}
<p class='mut'>輔助:門市旁每一段怠速的長度中位數(分鐘;一次停靠常切成好幾段)。</p>{dw_html}</div>
<div class='card'><h2>資料品質檢查</h2><p class='mut'>試算以「油耗率 × 取樣間隔」積分,和車上電腦(ECU)的怠速累計計數器比對。</p>{qa_html}</div>
</body></html>"""
open(OUT, "w", encoding="utf-8").write(page)
print(f"wrote {OUT}")
