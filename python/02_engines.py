import duckdb
import numpy as np
import pandas as pd
from scipy.stats import norm, t as student_t
from arch import arch_model

con = duckdb.connect("data/market.duckdb")

rets = con.execute(
    "SELECT instrument_id, date, log_ret FROM v_returns ORDER BY instrument_id, date"
).fetchdf()
rets["date"] = pd.to_datetime(rets["date"])

WINDOW = 250
Z95 = norm.ppf(0.05)
NU = 5
LAM = 0.94
T95 = student_t.ppf(0.05, NU)


def garch_vol_series(r, window = 250, refit_every=252):
    rp = r * 100.0
    n = len(r)
    vols = pd.Series(np.nan, index = r.index)
    t = window
    while t < n: 
        train = rp.iloc[1:t+1].dropna()
        res = arch_model(train, mean="Zero", vol="Garch", p=1, q=1,
                         dist="normal").fit(disp="off")
        omega = res.params["omega"]
        alpha = res.params["alpha[1]"]
        beta = res.params["beta[1]"]
        var = res.conditional_volatility.iloc[-1] ** 2
        end = min(t + refit_every, n)
        for s in range(t, end): 
            var = omega + alpha * rp.iloc[s] ** 2 + beta * var
            vols.iloc[s] = np.sqrt(var) / 100.0
        t = end
    return vols



frames = []
for iid, g in rets.groupby("instrument_id"):
    g = g.reset_index(drop=True)
    r = g["log_ret"]
    mu = r.rolling(WINDOW).mean()
    sigma = r.rolling(WINDOW).std()
    ewma_vol = np.sqrt(r.ewm(alpha=1 - LAM, adjust = False).var())
    garch_vol = garch_vol_series(r)
    var_norm = -(mu + Z95 * sigma)
    var_hs = -r.rolling(WINDOW).quantile(0.05)
    var_t = -(mu + T95 * sigma)
    var_ewma = -(Z95 * ewma_vol)
    var_garch = -(Z95 * garch_vol)
    frames.append(pd.DataFrame({"instrument_id": iid, "date": g["date"],
                                "model": "param_normal", "var95": var_norm}))
    frames.append(pd.DataFrame({"instrument_id": iid, "date": g["date"],
                                "model": "hs_pandas", "var95": var_hs}))
    frames.append(pd.DataFrame({"instrument_id": iid, "date": g["date"],
                                "model": "param_t", "var95": var_t}))
    frames.append(pd.DataFrame({"instrument_id": iid, "date": g["date"],
                                "model": "ewma", "var95": var_ewma}))
    frames.append(pd.DataFrame({"instrument_id": iid, "date": g["date"],
                                "model": "garch", "var95": var_garch}))

forecasts = pd.concat(frames, ignore_index = True)
forecasts["date"] = forecasts["date"].dt.date
con.execute("CREATE OR REPLACE TABLE var_forecasts AS SELECT * FROM forecasts")
print("rows written:", con.execute("SELECT COUNT(*) FROM var_forecasts").fetchone()[0])

sql_hs = con.execute("SELECT instrument_id, date, var95_hs FROM v_hs_var").fetchdf()
sql_hs["date"] = pd.to_datetime(sql_hs["date"]).dt.date
merged = forecasts[forecasts["model"] == "hs_pandas"].merge(sql_hs, on=["instrument_id", "date"])
print("max |pandas HS - SQL HS| =", (merged["var95"] - merged["var95_hs"]).abs().max())

print(con.execute(
    "SELECT * FROM var_forecasts WHERE instrument_id = 1 AND date = '2026-10-02' "
    "ORDER BY model").fetchdf().to_string())
con.close()