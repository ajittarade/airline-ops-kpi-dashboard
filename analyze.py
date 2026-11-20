"""Clean the raw flight data, log every fix, load into SQLite, run the SQL KPIs, export JSON for the dashboard."""
import json, sqlite3, pandas as pd
raw = pd.read_csv("data/flights_raw.csv"); log = []
df = raw.copy()
n = len(df); df = df.drop_duplicates(); log.append(("Duplicate rows removed", n - len(df)))
bad = (df.origin != df.origin.str.upper()).sum(); df["origin"] = df.origin.str.upper(); log.append(("Airport codes standardised to upper case", int(bad)))
op = df.cancelled == 0
miss = (op & df.dep_delay_min.isna()).sum(); df = df[~(op & df.dep_delay_min.isna())]; log.append(("Operated flights with missing delay removed", int(miss)))
op = df.cancelled == 0
inv = (op & ((df.pax < 0) | (df.pax > df.seats))).sum(); df = df[~(op & ((df.pax < 0) | (df.pax > df.seats)))]; log.append(("Flights with invalid passenger count removed (negative or above seats)", int(inv)))
df["dep_delay_min"] = df.dep_delay_min.astype("float")
log.append(("Rows kept", len(df)))
df.to_csv("data/flights_clean.csv", index=False)
con = sqlite3.connect(":memory:"); df.to_sql("flights", con, index=False)
q = lambda s: pd.read_sql(s, con)
blocks = [b for b in open("sql/kpi_queries.sql").read().split("\n\n") if "SELECT" in b]
res = [q("\n".join(l for l in b.splitlines() if not l.startswith("--"))) for b in blocks]
k, c, m, r, dc, h = res
out = {"kpi": {**k.iloc[0].to_dict(), **c.iloc[0].to_dict()}, "monthly": m.to_dict("list"),
       "routes": r.to_dict("records"), "causes": dc.to_dict("records"), "hours": h.to_dict("list"),
       "cleaning": [{"step": a, "count": int(b)} for a, b in log]}
json.dump(out, open("dashboard/kpis.json", "w"), indent=1, default=float)
for a, b in log: print(f"{a}: {b}")
print(json.dumps(out["kpi"]))
