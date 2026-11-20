"""Generate a SIMULATED airline flight-operations dataset (no real airline data).
Deliberately includes messy records so the cleaning step has real work to do."""
import numpy as np, pandas as pd
rng = np.random.default_rng(42)
N = 12000
routes = {("DXB","LHR"):(7,320),("DXB","DEL"):(3.5,300),("DXB","BOM"):(3.3,300),
          ("DXB","SIN"):(7.2,280),("DXB","JED"):(3,220),("DXB","CDG"):(7.5,300),
          ("DXB","BKK"):(6.2,280),("DXB","CAI"):(3.7,220)}
keys = list(routes)
idx = rng.integers(0, len(keys), N)
dates = pd.to_datetime("2025-01-01") + pd.to_timedelta(rng.integers(0, 365, N), unit="D")
hour = rng.choice(range(5,24), N, p=np.array([2,4,6,7,7,6,5,5,5,5,6,6,6,6,5,4,3,2,1])/np.array([2,4,6,7,7,6,5,5,5,5,6,6,6,6,5,4,3,2,1]).sum())
month = dates.month
# delay model: evening hours, summer + winter peaks add delay
base = rng.gamma(1.4, 9, N) - 4
base += (hour >= 17) * rng.gamma(1.5, 6, N)
base += np.isin(month, [7,8,12]) * rng.gamma(1.5, 5, N)
delay = np.round(base).astype(int)
cancel = rng.random(N) < 0.022
causes = ["Weather","Technical","Crew","Air traffic control","Ground handling","Late inbound aircraft"]
cause = np.where(delay > 15, rng.choice(causes, N, p=[.14,.17,.12,.15,.16,.26]), "None")
seats = np.array([routes[keys[i]][1] for i in idx])
lf = np.clip(rng.normal(0.80, 0.09, N) + np.isin(month,[7,8,12])*0.05, 0.4, 1.0)
pax = np.round(seats * lf).astype(int)
fare = np.array([routes[keys[i]][0] for i in idx]) * 55 * rng.normal(1, .12, N)
df = pd.DataFrame({
 "flight_id": [f"SA{1000+i}" for i in range(N)],
 "flight_date": dates.strftime("%Y-%m-%d"),
 "origin": [keys[i][0] for i in idx], "dest": [keys[i][1] for i in idx],
 "sched_dep_hour": hour, "dep_delay_min": delay,
 "delay_cause": cause, "cancelled": cancel.astype(int),
 "seats": seats, "pax": pax, "avg_fare_usd": np.round(fare, 2)})
# --- inject data-quality problems ---
df.loc[rng.choice(N, 180, replace=False), "dep_delay_min"] = np.nan      # missing delay
df.loc[rng.choice(N, 90, replace=False), "origin"] = df["origin"].str.lower()  # inconsistent case
df.loc[rng.choice(N, 40, replace=False), "pax"] = -1                      # invalid pax
df.loc[rng.choice(N, 35, replace=False), "pax"] = df["seats"] + 30       # pax > seats
df = pd.concat([df, df.sample(60, random_state=1)])                       # duplicate rows
df.loc[df.cancelled == 1, ["dep_delay_min","pax"]] = [np.nan, 0]
df.sample(frac=1, random_state=7).to_csv("data/flights_raw.csv", index=False)
print("raw rows:", len(df))
