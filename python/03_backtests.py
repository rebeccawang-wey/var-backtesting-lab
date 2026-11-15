import duckdb
import numpy as np
import pandas as pd
from scipy.stats import chi2

P = 0.05

def _xlogx(x, n):
    return 0.0 if x == 0 else x * np.log(x / n)

def kupiec(breaches, p=P):
    x = int(breaches.sum())
    T = len(breaches)
    ll_null = x * np.log(p) + (T - x) * np.log(1 - p)
    ll_alt = _xlogx(x, T) + _xlogx(T - x, T)
    lr = -2 * (ll_null - ll_alt)
    return lr, 1 - chi2.cdf(lr, 1)

def christofferson(breaches): 
    b = np.asarray(breaches, dtype=int)
    n00 = int(((b[:-1] == 0) & (b[1:] == 0)).sum())
    n01 = int(((b[:-1] == 0) & (b[1:] == 1)).sum())
    n10 = int(((b[:-1] == 1) & (b[1:] == 0)).sum())
    n11 = int(((b[:-1] == 1) & (b[1:] == 1)).sum())

    if (n00 + n01) == 0 or (n10 + n11) == 0:
        return np.nan, np.nan, np.nan, np.nan
    pi = (n01 + n11) / (n00 + n01 + n10 + n11)
    pi0 = n01 / (n00 + n01)
    pi1 = n11 / (n10 + n11)

    ll_null = (n00 + n10) * np.log(1 - pi) + (n01 + n11) * np.log(pi)
    ll_alt = (n00 * np.log(1 - pi0) if n00 else 0.0) \
             + (n01 * np.log(pi0) if n01 else 0.0) \
             + (n10 * np.log(1 - pi1) if n10 else 0.0) \
             + (n11 * np.log(pi1) if n11 else 0.0)
    lr_ind = -2 * (ll_null - ll_alt)
    lr_pof, _ = kupiec(breaches)
    lr_cc = lr_pof + lr_ind
    return lr_ind, 1 - chi2.cdf(lr_ind, 1), lr_cc, 1 - chi2.cdf(lr_cc, 2)


con = duckdb.connect("data/market.duckdb")

df = con.execute("""
    WITH nxt AS (
        SELECT instrument_id, date,
               LEAD(log_ret) OVER (
                   PARTITION BY instrument_id ORDER BY date) AS next_ret
        FROM v_returns
    )
    SELECT f.instrument_id, f.date, f.model, f.var95, n.next_ret
    FROM var_forecasts f
    JOIN nxt n USING (instrument_id, date)
""").fetchdf()

df = df.dropna(subset=["var95", "next_ret"]).copy()

cutoffs = {iid: sorted(g["date"].unique())[250]
           for iid, g in df.groupby("instrument_id")}
cut = pd.DataFrame({"instrument_id": list(cutoffs),
                    "cutoff_date": list(cutoffs.values())})
df = df.merge(cut, on="instrument_id")
df = df[df["date"] >= df["cutoff_date"]].drop(columns="cutoff_date")


df["breach"] = (-df["next_ret"] > df["var95"]).astype(int)

rows = []
for (iid, model), g in df.groupby(["instrument_id", "model"]):
    g = g.sort_values("date")
    lr_pof, p_pof = kupiec(g["breach"])
    lr_ind, p_ind, lr_cc, p_cc = christofferson(g["breach"])
    rows.append({
        "instrument_id": iid, "model": model,
        "T": len(g), "breaches": int(g["breach"].sum()),
        "breach_rate": round(float(g["breach"].mean()), 4),
        "expected": round(P * len(g), 1), 
        "LR_pof": round(float(lr_pof), 2), "p_pof": round(float(p_pof), 4),
        "pof_verdict": "REJECT" if p_pof < 0.05 else "pass", 
        "LR_ind": None if np.isnan(lr_ind) else round(float(lr_ind), 2), 
        "p_ind": None if np.isnan(p_ind) else round(float(p_ind), 4),
        "LR_cc": None if np.isnan(lr_cc) else round(float(lr_cc), 2),
        "p_cc": None if np.isnan(p_cc) else round(float(p_cc), 4),
    })
out = pd.DataFrame(rows).sort_values(["instrument_id", "model"])
print(out.to_string(index=False))
con.close()