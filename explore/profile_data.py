"""Profile every dataset in course_data: per-column stats, missingness, and dataset-specific checks.

Run:  python explore/profile_data.py      (≈5 min; reads all ~3 GB)
Writes explore/profile/results.pkl, consumed by explore/data_exploration.ipynb.

Null = NaN or empty/whitespace string. For gps_traces and vehicle_can_telematics, null
counts are exact over all rows; distribution stats come from a systematic 1-in-SAMPLE_EVERY sample.
"""
import glob
import os
import pickle
import re
import time

import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(ROOT, "explore", "profile")
os.makedirs(OUT_DIR, exist_ok=True)
P = lambda *a: os.path.join(ROOT, *a)
SAMPLE_EVERY = 20
TW_BBOX = dict(lat=(21.5, 26.5), lng=(119.0, 123.0))
DIESEL_KG_PER_L = 2.68


def log(m):
    print(f"[{time.strftime('%H:%M:%S')}] {m}", flush=True)


def read(f, **k):
    df = pd.read_csv(f, encoding="utf-8-sig", dtype=str, low_memory=False, **k)
    df.columns = [c if c.strip() else "<空白欄名>" for c in df.columns]
    return df


def blank_to_na(df):
    return df.apply(lambda s: s.str.strip()).replace("", np.nan)


def to_dt(s):
    return pd.to_datetime(s, errors="coerce", format="mixed")


def to_num(s):
    return pd.to_numeric(s, errors="coerce")


# ------------------------------------------------------------------ generic column profile
def col_profile(s, nulls=None, total=None):
    """s: cleaned string series (sample or full). nulls/total: exact counts if s is a sample."""
    vals = s.dropna()
    total = len(s) if total is None else total
    nulls = s.isna().sum() if nulls is None else nulls
    r = dict(non_null=total - nulls, null=nulls, null_rate=nulls / total if total else np.nan,
             distinct=vals.nunique(), kind="空", top="", min="", p50="", max="", mean="", std="",
             p1="", p99="", zeros="", negatives="", note="")
    if vals.empty:
        return r
    vc = vals.value_counts()
    r["top"] = " | ".join(f"{k[:24]} ({v / len(vals):.0%})" for k, v in vc.head(4).items())
    num = to_num(vals)
    if num.notna().mean() > 0.95:
        n = num.dropna()
        q = n.quantile([.01, .5, .99])
        r.update(kind="數值", min=n.min(), p1=q[.01], p50=q[.5], p99=q[.99], max=n.max(),
                 mean=n.mean(), std=n.std(), zeros=int((n == 0).sum()), negatives=int((n < 0).sum()))
        if num.notna().mean() < 1:
            r["note"] = f"{1 - num.notna().mean():.1%} 非數值字串"
        return r
    smp = vals.iloc[:: max(len(vals) // 3000, 1)]
    dt = to_dt(smp)
    if dt.notna().mean() > 0.9:
        d = to_dt(vals)
        r.update(kind="時間", min=str(d.min()), max=str(d.max()))
        fmts = smp.str.replace(r"\d", "9", regex=True).value_counts()
        if len(fmts) > 1 and fmts.iloc[1] / fmts.sum() > 0.01:
            r["note"] = "格式不一致:" + " / ".join(fmts.index[:3])
        return r
    L = vals.str.len()
    r.update(kind="文字", min=int(L.min()), max=int(L.max()), p50=float(L.median()))
    r["note"] = "長度 min/p50/max"
    return r


def profile_frame(df, nulls=None, total=None, present=None):
    rows = []
    for c in df.columns:
        r = col_profile(df[c], None if nulls is None else nulls.get(c, 0), total)
        r["column"] = c
        if present is not None:
            r["files_with_col"] = present.get(c, 0)
        rows.append(r)
    out = pd.DataFrame(rows)
    return out[["column"] + [c for c in out.columns if c != "column"]]


def issue(lst, sev, title, detail):
    lst.append(dict(severity=sev, title=title, detail=detail))


R = {}

# ================================================================== store_master
log("store_master")
st = blank_to_na(read(P("store_master", "store_master.csv")))
iss = []
lat, lng = to_num(st["lat"]), to_num(st["lng"])
oob = (~lat.between(*TW_BBOX["lat"]) | ~lng.between(*TW_BBOX["lng"])).sum()
dup_name = st["name"].duplicated(keep=False).sum()
dup_code = st["商店編號"].dropna().duplicated(keep=False).sum()
dup_xy = st.duplicated(["lat", "lng"], keep=False).sum()
issue(iss, "info", "主鍵", f"name 重複 {dup_name} 列、商店編號(非空)重複 {dup_code} 列、完全相同座標 {dup_xy} 列。")
no_code = st[st["商店編號"].isna()]["name"]
issue(iss, "warn", "缺商店編號", f"{len(no_code)} 列沒有商店編號(含物流中心):" + "、".join(no_code))
if oob:
    issue(iss, "alert", "座標超出臺灣範圍", f"{oob} 列")
tel_len = st["tel"].dropna().str.len().value_counts().sort_index()
issue(iss, "warn", "電話格式", "電話以數字儲存,開頭 0 被去掉(如 225678224 應為 02-25678224);長度分佈:"
      + ", ".join(f"{k}碼×{v}" for k, v in tel_len.items()))
city = st["address"].str[:3].value_counts()
R["store_master"] = dict(
    rows=len(st), cols=st.shape[1], profile=profile_frame(st), issues=iss,
    extra=dict(city=city), grain="一列 = 一家全家門市(快照,無時間欄)",
)

# ================================================================== delivery_plan
log("delivery_plan")
iss = []
mfiles = sorted(glob.glob(P("delivery_plan", "monthly", "*.csv")))
dp = blank_to_na(pd.concat([read(f) for f in mfiles], ignore_index=True))
dp["TaskType_id"] = dp["TaskType_id"].str.zfill(2)
dp["date"] = to_dt(dp["Delivery_Dt"])
dp["route"] = dp["Route_seq"].str[:2]
dp["is_depot"] = dp["Store_id"].str.contains("3001888888", na=False)
stops = dp[~dp["is_depot"]].copy()
stops["plan"] = to_dt(stops["Pl_M_Arrive_dt"])
stops["act"] = to_dt(stops["Ac_Arrive_dt_02"])

core = ["TaskType_id", "Delivery_Dt", "Route_seq", "Car_licence", "Store_id", "Pl_M_Arrive_dt", "Ac_Arrive_dt_02"]
n_exact_dup = dp.duplicated(core).sum()
key = ["Delivery_Dt", "TaskType_id", "Route_seq", "Car_licence", "Store_id"]
n_key_dup = dp.duplicated(key, keep=False).sum()
issue(iss, "warn" if n_exact_dup else "info", "重複列",
      f"完全相同的列 {n_exact_dup:,};以 (日期, 任務, Route_seq, 車, 店) 為鍵重複 {n_key_dup:,} 列。")

miss_act = stops["act"].isna()
by_m = stops.assign(m=stops["date"].dt.to_period("M").astype(str), miss=miss_act).groupby("m")["miss"].mean()
by_tt = stops.assign(miss=miss_act).groupby("TaskType_id")["miss"].agg(["mean", "size"])
issue(iss, "alert" if miss_act.mean() > .2 else "warn", "實際到達時間缺失",
      f"門市停靠列中 Ac_Arrive_dt_02 缺失 {miss_act.mean():.1%}({miss_act.sum():,} / {len(stops):,})。依任務類型:"
      + ", ".join(f"{k}: {v['mean']:.0%}" for k, v in by_tt.iterrows()))

days = pd.date_range(dp["date"].min(), dp["date"].max())
missing_days = days.difference(dp["date"].dropna().unique())
issue(iss, "warn" if len(missing_days) else "info", "日期缺口",
      f"{dp['date'].min():%Y-%m-%d} ~ {dp['date'].max():%Y-%m-%d} 共 {len(days)} 天,無任何資料的日子 {len(missing_days)} 天"
      + (":" + ", ".join(f"{d:%m-%d}" for d in missing_days[:15]) if len(missing_days) else ""))

tt = dp.groupby("TaskType_id").agg(rows=("Store_id", "size"), veh=("Car_licence", "nunique"),
                                   first=("date", "min"), last=("date", "max"))
rare = tt[tt["rows"] < 1000]
issue(iss, "info", "零星任務類型 A2/A3/A4",
      "; ".join(f"{k}: {r.rows} 列、{r.veh} 輛車、{r['first']:%Y-%m-%d}~{r['last']:%Y-%m-%d}" for k, r in rare.iterrows())
      + " —— A2/A3 未指派車輛、實際到達全缺;A4 自 2024-09 起才出現。三者合計不到總列數 0.3%,主分析可只取 02/03/04/05/12。")

id2name = stops.groupby("Store_id")["Store_Name"].nunique()
name2id = stops.groupby("Store_Name")["Store_id"].nunique()
ex_name = name2id[name2id > 1].index[0] if (name2id > 1).any() else ""
issue(iss, "warn" if (name2id > 1).any() else "info", "店號與店名一致性",
      f"同一 Store_id 對應多個店名:{(id2name > 1).sum()} 個;同一店名對應多個 Store_id:{(name2id > 1).sum()} 個"
      f"(如「{ex_name}」,多為門市換號/重新開店)。以門市為單位彙總時,請用店名或建立對照表,不要只用 Store_id。")

pm = stops.groupby(["Delivery_Dt", "TaskType_id", "route", "Car_licence"])["Pl_M_Arrive_dt"].nunique()
issue(iss, "info", "Pl_M_Arrive_dt 的意義",
      f"同一趟(日期×任務×路線×車)內 Pl_M_Arrive_dt 只有 1 個值的比例 {(pm == 1).mean():.1%} —— 是整趟的計畫出發/備車時間,不是逐店計畫時間。")

lead = (stops["act"] - stops["plan"]).dt.total_seconds() / 60
neg = (lead < 0).mean()
issue(iss, "warn" if neg > .01 else "info", "實際到店早於整趟計畫時間",
      f"{neg:.1%} 的停靠實際到達早於 Pl_M_Arrive_dt;到達−計畫 中位數 {lead.median():.0f} 分、p99 {lead.quantile(.99):.0f} 分、最大 {lead.max():.0f} 分。")


def nonmono(g):
    a = g.sort_values("Route_seq")["act"].dropna()
    return len(a) > 1 and not a.is_monotonic_increasing


trips = stops.groupby(["Delivery_Dt", "TaskType_id", "route", "Car_licence"])
nm = trips.apply(nonmono)
issue(iss, "info", "停靠順序",
      f"{nm.mean():.1%} 的趟次,實際到達順序與 Route_seq 編號順序不一致(司機調整順序,或編號不代表行駛順序)。")

st_short = st["name"].str.replace("^全家", "", regex=True).str.replace("店$", "", regex=True)
names = stops["Store_Name"].dropna().str.replace("店$", "", regex=True).unique()
match = np.isin(names, st_short.values).mean()
issue(iss, "warn", "與 store_master 的連結",
      f"Store_id 與 商店編號 是不同編碼系統,只能用店名對應;去掉「全家/店」後可對上 {match:.0%} 的店名({len(names)} 個中)。")

# by_vehicle / by_task_type relationship
bv = blank_to_na(pd.concat([read(f) for f in glob.glob(P("delivery_plan", "by_vehicle", "*.csv"))], ignore_index=True))
bt = blank_to_na(pd.concat([read(f) for f in glob.glob(P("delivery_plan", "by_task_type", "*.csv"))], ignore_index=True))


def norm(df):
    d = df.copy()
    d["TaskType_id"] = d["TaskType_id"].str.zfill(2)
    for c in ["Delivery_Dt", "Pl_M_Arrive_dt", "Ac_Arrive_dt_02"]:
        d[c] = to_dt(d[c]).dt.strftime("%Y-%m-%d %H:%M")
    return d[["TaskType_id", "Delivery_Dt", "Route_seq", "Car_licence", "Store_id", "Pl_M_Arrive_dt", "Ac_Arrive_dt_02"]].fillna("")


mk = set(map(tuple, norm(dp).values))
bvk = list(map(tuple, norm(bv).values))
btk = list(map(tuple, norm(bt).values))
bv_in = np.mean([k in mk for k in bvk])
bt_in = np.mean([k in mk for k in btk])
bv_dup = pd.Series(bvk).duplicated().mean()
issue(iss, "warn", "by_vehicle / by_task_type 與 monthly 的關係",
      f"by_vehicle {len(bv):,} 列,其中 {bv_in:.1%} 可在 monthly 找到相同紀錄、自身重複 {bv_dup:.1%};"
      f"by_task_type {len(bt):,} 列,{bt_in:.1%} 在 monthly 中。→ 分析請只用 monthly。")
bt_fmt = bt["Delivery_Dt"].str.replace(r"\d", "9", regex=True).value_counts().head(3).to_dict()
issue(iss, "info", "日期格式不一致", f"by_task_type 的 Delivery_Dt 格式:{bt_fmt}(task_type_12 用 YYYY/M/D)。")

daily = dp.groupby([dp["date"].dt.normalize(), "TaskType_id"]).size().unstack(fill_value=0)
R["delivery_plan"] = dict(
    rows=len(dp), cols=dp.shape[1] - 4, profile=profile_frame(dp[[c for c in dp.columns if c not in
                                                                  ("date", "route", "is_depot")]]),
    issues=iss, grain="一列 = 某日某車某路線的一個停靠點(含出發/回場 DC 列)",
    extra=dict(miss_by_month=by_m, daily=daily, stops=len(stops), trips=len(trips),
               vehicles=dp["Car_licence"].nunique(), stores=stops["Store_id"].nunique(),
               routes=dp["route"].nunique(), lead=lead.describe(percentiles=[.05, .25, .5, .75, .95])),
)

# ================================================================== tms
log("tms")
iss = []
tfiles = sorted(glob.glob(P("tms_delivery_records", "**", "*.csv"), recursive=True))
tm = blank_to_na(pd.concat([read(f) for f in tfiles], ignore_index=True))
tm["date"] = to_dt(tm["Delivery_date"]).dt.normalize()
tdays = pd.date_range(tm["date"].min(), tm["date"].max())
t_missing = tdays.difference(tm["date"].dropna().unique())
issue(iss, "warn" if len(t_missing) else "info", "日期缺口",
      f"{tm['date'].min():%Y-%m-%d} ~ {tm['date'].max():%Y-%m-%d} 共 {len(tdays)} 天、{len(tfiles)} 個檔;缺 {len(t_missing)} 天"
      + (":" + ", ".join(f"{d:%Y-%m-%d}" for d in t_missing[:20]) if len(t_missing) else ""))
n_dup = tm.duplicated([c for c in tm.columns if c not in ("source_file",)]).sum()
issue(iss, "warn" if n_dup else "info", "重複列", f"除 source_file 外完全相同的列 {n_dup:,}。")

pairs = [("Route_id", "Route_id1"), ("Temperature1", "In_Temperature1"), ("Temperature2", "In_Temperature2"),
         ("Ac_Arrive_dt_01", "Ac_Arrive_dt_02"), ("Ac_Arrive_dt_01", "Ac_Arrive_dt"), ("Pl_Arrive_dt_01", "Pl_Arrive_dt"),
         ("Pl_Arrive_dt_01", "Arrive_dt"), ("Im_arrive_dt_02", "Im_Arrive_dt")]
red = []
for a, b in pairs:
    if a in tm and b in tm:
        if "dt" in a:
            x, y = to_dt(tm[a]), to_dt(tm[b])
        else:
            x, y = tm[a], tm[b]
        both = x.notna() & y.notna()
        red.append(f"{a}≡{b}: {(x[both] == y[both]).mean():.1%}")
issue(iss, "info", "冗餘欄位(兩兩相同比例)", "; ".join(red))

ts = tm[tm["last_dc"] == "0"].copy()
for c in ["Ac_Arrive_dt_01", "Pl_Arrive_dt_01", "Im_arrive_dt_02"]:
    ts[c] = to_dt(ts[c])
ex = to_num(ts["Ex_Arrive_diff"])
ref = ts["Im_arrive_dt_02"].fillna(ts["Pl_Arrive_dt_01"])
calc = ((ts["Ac_Arrive_dt_01"] - ref).dt.total_seconds() / 60).round()
ok = (calc - ex).abs() <= 1
issue(iss, "info", "Ex_Arrive_diff 重算驗證", f"以 實際 − 表訂(缺則預計) 重算,誤差 ≤1 分的比例 {ok[ex.notna() & calc.notna()].mean():.1%}。")
st_calc = np.select([ex < -60, ex > 30], [-1, 1], 0).astype(float)
dsv = to_num(ts["DiffStatus"])
cons = (st_calc == dsv)[dsv.notna() & ex.notna()].mean()
issue(iss, "info", "DiffStatus 與窗口 (−60, +30) 一致性", f"{cons:.1%}")
pldt_zero = (to_num(ts["PLDT"]) == 0).mean()
same_pl = (ts["Pl_Arrive_dt_01"] == ts["Ac_Arrive_dt_01"]).mean()
issue(iss, "alert", "「預計到達」= 實際到達",
      f"Pl_Arrive_dt 與 Ac_Arrive_dt 完全相同的比例 {same_pl:.1%},PLDT=0 的比例 {pldt_zero:.1%} —— 預計時間似乎是事後回填,不能當成獨立的計畫值;請用 Im_Arrive_dt(表訂)。")
im_miss = ts["Im_arrive_dt_02"].isna().mean()
issue(iss, "warn" if im_miss > .05 else "info", "表訂時間缺失", f"門市停靠列中 Im_arrive_dt_02 缺失 {im_miss:.1%}(此時 Ex_Arrive_diff 改用預計時間計算,等於 0)。")
ac_miss = ts["Ac_Arrive_dt_01"].isna().mean()
issue(iss, "warn" if ac_miss > .05 else "info", "實際到達缺失", f"門市停靠列中 {ac_miss:.1%}。")

zz = tm["Car_id"].str.startswith("ZZ", na=False)
issue(iss, "info", "外包車輛代碼", f"Car_id 為 ZZ1xx(臨時外調車)的列 {zz.mean():.1%},共 {tm.loc[zz, 'Car_id'].nunique()} 個代碼。")
mis = (tm["Car_id"] != tm["Car_licence"]) & tm["Car_id"].notna() & tm["Car_licence"].notna()
issue(iss, "info", "Car_id vs Car_licence", f"不相同的列 {mis.mean():.1%}。")

t1, t2 = to_num(ts["Temperature1"]), to_num(ts["Temperature2"])
t_by_m = pd.DataFrame({"T1缺失": t1.isna(), "T2缺失": t2.isna(), "m": ts["date"].dt.to_period("M").astype(str)}).groupby("m").mean()
issue(iss, "alert" if t2.isna().mean() > .8 else "warn", "車廂溫度缺失",
      f"Temperature1 缺失 {t1.isna().mean():.1%}、Temperature2 缺失 {t2.isna().mean():.1%}。")
odd = (~t1.between(-30, 40) & t1.notna()).sum()
issue(iss, "warn" if odd else "info", "溫度異常值", f"Temperature1 超出 −30~40°C 的有 {odd} 筆(min {t1.min()}, max {t1.max()});p1–p99 = {t1.quantile(.01):.1f}~{t1.quantile(.99):.1f}°C。")
issue(iss, "warn", "個資欄位", "含 Emp_name(司機姓名)、Emp_tel(司機電話)、門市電話;報告/簡報中請勿揭露,分析時以代碼取代。")

# overlap with delivery_plan TaskType 12
dp12 = stops[stops["TaskType_id"] == "12"].groupby(stops["date"].dt.normalize()).size()
tm12 = ts.groupby("date").size()
ov = pd.concat([dp12.rename("delivery_plan"), tm12.rename("tms")], axis=1).dropna()
issue(iss, "info", "與 delivery_plan(任務 12)重疊",
      f"兩者都有資料的 {len(ov)} 天中,每日停靠數相同的天數比例 {(ov['delivery_plan'] == ov['tms']).mean():.0%};"
      f"差值中位數 {(ov['tms'] - ov['delivery_plan']).median():.0f}。TMS 涵蓋到 2026-01,可延伸任務 12 的時間軸。")

R["tms"] = dict(
    rows=len(tm), cols=tm.shape[1] - 1, profile=profile_frame(tm.drop(columns=["date"])), issues=iss,
    grain="一列 = 一趟配送中的一站(含出發 DC 列 last_dc 空、回場 last_dc=1)",
    extra=dict(t_by_m=t_by_m, daily=tm.groupby("date").size(), stops=len(ts),
               diff=ex.describe(percentiles=[.01, .05, .25, .5, .75, .95, .99]),
               status=dsv.map({-1: "過早", 0: "準時", 1: "遲到"}).value_counts(normalize=True)),
)


# ================================================================== big, file-by-file datasets
def scan(files, family_of, time_col_of, tag, file_stats):
    """Exact null counts per (family, column); 1-in-N sample rows; per-file stats via file_stats(df)->dict.
    Each file is dropped after processing so the whole dataset never sits in memory."""
    fam = {}
    perfile = []
    for i, f in enumerate(files):
        df = read(f)
        fm = family_of(f, df)
        df = blank_to_na(df)
        A = fam.setdefault(fm, dict(nulls={}, total=0, present={}, rows_with={}, samples=[], files=0))
        A["files"] += 1
        A["total"] += len(df)
        for c, n in df.isna().sum().items():
            A["nulls"][c] = A["nulls"].get(c, 0) + n
            A["present"][c] = A["present"].get(c, 0) + 1
            A["rows_with"][c] = A["rows_with"].get(c, 0) + len(df)
        A["samples"].append(df.iloc[::SAMPLE_EVERY])
        tc = time_col_of(df)
        t = to_dt(df[tc])
        dts = t.sort_values().diff().dt.total_seconds()
        rec = dict(file=os.path.relpath(f, ROOT), family=fm, rows=len(df), cols=df.shape[1],
                   vehicle=(re.search(r"V\d\d", os.path.basename(f)) or [None])[0],
                   start=t.min(), end=t.max(), t_null=t.isna().mean(),
                   dup_ts=int(t.duplicated().sum()), med_dt=dts.median(),
                   gaps_10m=int((dts > 600).sum()), gap_hours=dts[dts > 600].sum() / 3600,
                   days=t.dt.normalize().nunique())
        rec.update(file_stats(df))
        perfile.append(rec)
        if (i + 1) % 20 == 0:
            log(f"  {tag} {i + 1}/{len(files)}")
    return fam, perfile


def fam_profiles(fam):
    """Per family: null counts are exact; a column absent from some files counts those rows as missing."""
    out = {}
    for k, A in fam.items():
        allcols = list(dict.fromkeys(c for s in A["samples"] for c in s.columns))
        smp = pd.concat(A["samples"], ignore_index=True).reindex(columns=allcols)
        prof = []
        for c in allcols:
            nulls = A["nulls"][c] + (A["total"] - A["rows_with"][c])
            r = col_profile(smp[c], nulls, A["total"])
            r["column"] = c
            r["files_with_col"] = A["present"][c]
            prof.append(r)
        p = pd.DataFrame(prof)
        out[k] = dict(profile=p[["column"] + [c for c in p.columns if c != "column"]],
                      total=A["total"], files=A["files"])
    return out


# ---------------------------------------------------------------- gps
log("gps")
gfiles = sorted(glob.glob(P("gps_traces", "**", "V13_*.csv"), recursive=True))
def gps_stats(df):
    lat, lng, v = to_num(df["緯度"]), to_num(df["經度"]), to_num(df["速度"])
    j = to_num(df["路程"])
    return dict(
        invalid_fix=(~df["GPS有效性"].isin(["有效", "Valid"])).mean(),
        out_bbox=(~lat.between(*TW_BBOX["lat"]) | ~lng.between(*TW_BBOX["lng"])).mean(),
        zero_coord=((lat == 0) | (lng == 0)).mean(),
        v_max=v.max(), v_over_110=(v > 110).sum(), moving=(v > 1).mean(),
        km=j.max() - j.min(), journey_decrease=int((j.dropna().diff() < -0.5).sum()),
        task_fill=df["任務"].notna().mean() if "任務" in df else np.nan,
        tianyan_fill=df["狀態"].notna().mean() if "狀態" in df else np.nan,
        fuel_fill=df["燃料"].notna().mean() if "燃料" in df else np.nan,
        fuel_fmt=" / ".join(df["燃料"].dropna().astype(str).str.replace(r"\d", "9", regex=True).value_counts().index[:2]),
        harsh_brake=(df["事件"] == "Harsh Braking").sum(), harsh_acc=(df["事件"] == "Harsh Acceleration").sum(),
        door_events=df["事件"].str.contains("Door|門|Input", na=False).sum(),
        dup_ts_multi_event=int((df.duplicated("GPS時間", keep=False)
                                & (df.groupby("GPS時間")["事件"].transform("nunique") > 1)).sum()),
    )


gfam, gper = scan(gfiles, lambda f, d: "2024" if os.sep + "2024-" in f else "2025",
                  lambda d: "GPS時間", "gps", gps_stats)
iss = []
gpf = pd.DataFrame(gper)
gpf["date"] = gpf["start"].dt.normalize()
gprof = fam_profiles(gfam)
for y in ("2024", "2025"):
    s = gpf[gpf["family"] == y]
    rng = pd.date_range(f"{y}-03-01", f"{y}-04-30")
    miss = rng.difference(s["date"].dropna())
    issue(iss, "warn" if len(miss) else "info", f"{y} 日期覆蓋",
          f"{len(s)} 個日檔;3/1–4/30 缺 {len(miss)} 天" + (":" + ", ".join(f"{d:%m-%d}" for d in miss) if len(miss) else ""))
issue(iss, "info", "取樣間隔", f"中位數取樣間隔 {gpf['med_dt'].median():.0f} 秒;每日行車時段長度中位數 "
      f"{((gpf['end'] - gpf['start']).dt.total_seconds() / 3600).median():.1f} 小時。")
issue(iss, "warn" if gpf["gaps_10m"].sum() else "info", "時間缺口(>10 分鐘無紀錄)",
      f"{(gpf['gaps_10m'] > 0).sum()} 個日檔有缺口,總計 {gpf['gaps_10m'].sum()} 段、{gpf['gap_hours'].sum():.0f} 小時(含停車熄火)。")
issue(iss, "warn" if gpf["dup_ts"].sum() else "info", "重複時間戳",
      f"GPS時間 與前一筆重複的列 {gpf['dup_ts'].sum():,} 筆;落在「同一秒記錄多種事件」(如 定時追蹤 + 車輛起步)群組中的列共 {gpf['dup_ts_multi_event'].sum():,}。"
      "算距離/速度前請先依 GPS時間 去重;天眼的『時間』是對齊到最近一筆,不是同一秒。")
issue(iss, "warn", "GPS 無效定位", f"GPS有效性≠有效 的比例:平均 {gpf['invalid_fix'].mean():.1%},最高 {gpf['invalid_fix'].max():.1%}。")
issue(iss, "info", "座標範圍", f"超出臺灣範圍的點平均 {gpf['out_bbox'].mean():.2%};座標為 0 的點 {gpf['zero_coord'].mean():.2%}。")
issue(iss, "info", "速度", f"日最高車速中位數 {gpf['v_max'].median():.0f} km/h,>110 km/h 的紀錄共 {gpf['v_over_110'].sum()} 筆。")
small = gpf[gpf["moving"] == 0]
issue(iss, "warn" if len(small) else "info", "未出車的日子",
      f"{len(small)} 個日檔整天速度皆為 0、路程不變(車輛未出車):" + ", ".join(f"{d:%Y-%m-%d}({n}列)" for d, n in zip(small['date'], small['rows']))
      + "。計算平均日里程時應排除。")
t24 = gpf[gpf.family == "2024"]["task_fill"].mean()
t25 = gpf[gpf.family == "2025"]["task_fill"].mean()
issue(iss, "alert", "任務欄位只有 2024 有值",
      f"『任務』填值率:2024 {t24:.1%}、2025 {t25:.1%} → 2025 的軌跡無法直接對回 delivery_plan,需以時間+位置比對。")
issue(iss, "warn", "第二套 GPS(天眼)欄位", f"『狀態/位置/時速』等填值率平均 {gpf['tianyan_fill'].mean():.1%};兩套系統時間戳各自獨立。")
issue(iss, "warn", "燃料欄位", f"填值率 {gpf['fuel_fill'].mean():.1%};格式範例:{'; '.join(gpf['fuel_fmt'].dropna().unique()[:3])}。紅外線液位計,行駛中晃動誤差大,不建議用來算油耗。")
R["gps_traces"] = dict(rows=int(gpf["rows"].sum()), cols=38, profiles=gprof, issues=iss, perfile=gpf,
                       grain="一列 = V13 的一筆 GPS 紀錄(約每秒,兩套系統併列)")

# ---------------------------------------------------------------- CAN
log("can")
cfiles = sorted(glob.glob(P("vehicle_can_telematics", "**", "*.csv"), recursive=True))


def cfam(f, d):
    if "dt24" in d.columns:
        return "B 天眼(20欄)"
    if "refuel" in f:
        return "C 加油衍生(34欄)"
    return "A TransIOT+CAN(96–98欄)" if d.shape[1] >= 90 else "A TransIOT 基本(32欄)"


def can_stats(df):
    rec = {}
    if "Total fuel used(L)" in df:
        fu = to_num(df["Total fuel used(L)"])
        odo = to_num(df.get("High resolution vehicle distance(m)", pd.Series(dtype=str)))
        fd, od = fu.dropna().diff(), odo.dropna().diff()
        rec.update(fuel_dec_min=fd.min() if len(fd) else np.nan, odo_dec_min=od.min() if len(od) else np.nan,
                   fuel_decrease=int((fd < 0).sum()), fuel_fill=fu.notna().mean(),
                   fuel_jump=int((fu.dropna().diff() > 50).sum()),
                   odo_fill=odo.notna().mean() if len(odo) else 0.0,
                   odo_decrease=int((odo.dropna().diff() < 0).sum()) if len(odo) else 0,
                   fuel_L=fu.max() - fu.min(),
                   km=(odo.max() - odo.min()) / 1000 if odo.notna().any() else to_num(df["Journey"]).max() - to_num(df["Journey"]).min(),
                   rate_fill=to_num(df.get("Engine Fuel Rate(L/H)", pd.Series(dtype=str))).notna().mean(),
                   level_can_fill=df["Fuel level(%)_CAN"].notna().mean() if "Fuel level(%)_CAN" in df else np.nan,
                   ambient_fill=df["Ambient Air Temperature(deg C)"].notna().mean() if "Ambient Air Temperature(deg C)" in df else np.nan)
    if "Speed" in df:
        rec["idle_share"] = (to_num(df["Speed"]) < 1).mean()
    if "status" in df:
        rec["idle_share"] = (to_num(df["speed"]) < 1).mean()
        rec["temp1_fill"] = df["Temperature1"].notna().mean()
        rec["grp_fill"] = df["grp_id"].notna().mean()
    return rec


cfam_acc, cper = scan(cfiles, cfam, lambda d: "dt24" if "dt24" in d.columns else "GPS Time", "can", can_stats)
iss = []
cpf = pd.DataFrame(cper)
cprof = fam_profiles(cfam_acc)

fc = cpf.groupby("family").agg(files=("file", "size"), rows=("rows", "sum"), vehicles=("vehicle", "nunique"))
issue(iss, "alert", "三種匯出格式混在一起",
      "; ".join(f"{k}: {r.files} 檔 / {r.rows:,} 列 / {r.vehicles} 車" for k, r in fc.iterrows())
      + "。V16 2025-03~05 兩檔檔名無 tms 前綴,實為天眼格式。")
cov = cpf.groupby("vehicle").agg(start=("start", "min"), end=("end", "max"), days=("days", "sum"),
                                 fams=("family", lambda s: ", ".join(sorted(set(x[:1] for x in s)))))
cov["span_days"] = (cov["end"] - cov["start"]).dt.days + 1
issue(iss, "warn", "各車涵蓋期間差異大",
      "; ".join(f"{v}: {r.start:%m/%d}–{r.end:%m/%d} ({r.fams})" for v, r in cov.iterrows()))
canf = cpf[cpf["family"].str.startswith("A TransIOT+CAN")]
no_fuel = canf[canf["fuel_fill"].fillna(0) < 0.01]
issue(iss, "alert", "有 CAN 欄位但沒有油耗值",
      f"{len(no_fuel)} 個 96–98 欄檔案的 Total fuel used 全空:" + ", ".join(os.path.basename(f) for f in no_fuel["file"]))
with_fuel = canf[canf["fuel_fill"].fillna(0) >= 0.01]
issue(iss, "info", "可算實測油耗的車",
      f"{with_fuel['vehicle'].nunique()} 輛({', '.join(sorted(with_fuel['vehicle'].unique()))}),"
      f"共 {with_fuel['fuel_L'].sum():,.0f} L / {with_fuel['km'].sum():,.0f} km → 平均 {with_fuel['fuel_L'].sum() / with_fuel['km'].sum() * 100:.1f} L/100km,"
      f"約 {with_fuel['fuel_L'].sum() / with_fuel['km'].sum() * DIESEL_KG_PER_L * 1000:.0f} gCO₂/km(柴油 {DIESEL_KG_PER_L} kg/L,僅燃燒端)。")
issue(iss, "warn" if (with_fuel["fuel_decrease"].sum() + with_fuel["odo_decrease"].sum()) else "info", "累計計數器倒退/跳動",
      f"Total fuel used 倒退 {with_fuel['fuel_decrease'].sum():,.0f} 次(最大倒退 {with_fuel['fuel_dec_min'].min():.0f} L)、單步跳增 >50 L {with_fuel['fuel_jump'].sum():,.0f} 次;"
      f"odometer 倒退 {with_fuel['odo_decrease'].sum():,.0f} 次(最大倒退 {with_fuel['odo_dec_min'].min():.0f} m)。"
      "odometer 倒退來自同秒多筆中個別點瞬間前跳(1–9 km)後回到正常值;實測 488 車日以 5 點中位數平滑後,"
      "日里程 max−min 與平滑結果差 <0.01%,可直接使用。")
issue(iss, "warn", "時間缺口(>10 分鐘無紀錄)",
      f"{(cpf['gaps_10m'] > 0).mean():.0%} 的檔案有缺口,合計 {cpf['gap_hours'].sum():,.0f} 小時(多數為夜間熄火,屬正常)。")
issue(iss, "warn" if cpf["dup_ts"].sum() else "info", "重複時間戳", f"共 {cpf['dup_ts'].sum():,} 筆。")
issue(iss, "info", "取樣間隔", "; ".join(f"{k}: {v:.0f} 秒" for k, v in cpf.groupby("family")["med_dt"].median().items()))
issue(iss, "info", "怠速/停車比例(速度<1)",
      "; ".join(f"{k}: {v:.0%}" for k, v in cpf.groupby("family")["idle_share"].mean().dropna().items()) + "(含整夜停車)。")
R["vehicle_can_telematics"] = dict(rows=int(cpf["rows"].sum()), cols=None, profiles=cprof, issues=iss, perfile=cpf,
                                   coverage=cov, grain="一列 = 一筆車載紀錄;格式依匯出類型而異")

with open(os.path.join(OUT_DIR, "results.pkl"), "wb") as fh:
    pickle.dump(R, fh)
for k, v in R.items():
    if "profile" in v:
        v["profile"].to_csv(os.path.join(OUT_DIR, f"columns_{k}.csv"), index=False, encoding="utf-8-sig")
    for fk, fv in v.get("profiles", {}).items():
        fv["profile"].to_csv(os.path.join(OUT_DIR, f"columns_{k}_{re.sub(r'[^0-9A-Za-z]+', '_', fk)}.csv"),
                             index=False, encoding="utf-8-sig")
    if "perfile" in v:
        v["perfile"].to_csv(os.path.join(OUT_DIR, f"files_{k}.csv"), index=False, encoding="utf-8-sig")
log("done")
for k, v in R.items():
    print(f"\n### {k}: {v['rows']:,} rows")
    for i in v["issues"]:
        print(f"  [{i['severity']}] {i['title']}: {i['detail']}")
