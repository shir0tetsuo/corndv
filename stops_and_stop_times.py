import pandas as pd
import geojson
from pathlib import Path

gtfs_folder = Path("./sources/gtfs-cornwall")

stops = pd.read_csv(gtfs_folder / "stops.txt")
stop_times = pd.read_csv(gtfs_folder / "stop_times.txt")

# --- Convert numpy/pandas scalars safely ---
def to_py(v):
    if pd.isna(v):
        return None
    try:
        return v.item()
    except:
        return v

# --- Aggregate stop times per stop ---
stop_times_grouped = (
    stop_times
    .sort_values(["stop_id", "stop_sequence"])
    .groupby("stop_id")
    .apply(lambda g: [
        {
            "trip_id": to_py(row.trip_id),
            "arrival_time": to_py(row.arrival_time),
            "departure_time": to_py(row.departure_time),
            "stop_sequence": to_py(row.stop_sequence)
        }
        for row in g.itertuples()
    ])
)

stop_times_lookup = stop_times_grouped.to_dict()

# --- Build GeoJSON stop features ---
features = []

for _, stop in stops.iterrows():

    props = {
        k: to_py(stop[k])
        for k in stops.columns
        if k not in ["stop_lat", "stop_lon"]
    }

    # attach stop times
    props["stop_times"] = stop_times_lookup.get(stop["stop_id"], [])

    feature = geojson.Feature(
        geometry=geojson.Point(
            (float(stop["stop_lon"]), float(stop["stop_lat"]))
        ),
        properties=props
    )

    features.append(feature)

fc = geojson.FeatureCollection(features)

output = gtfs_folder.parent / "stops_with_times.geojson"

with open(output, "w") as f:
    geojson.dump(fc, f, indent=2)

print("GeoJSON written to:", output)