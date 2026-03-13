import pandas as pd
import geojson
from pathlib import Path

gtfs_folder = Path("./sources/gtfs-cornwall")

# Load GTFS CSVs
stops = pd.read_csv(gtfs_folder / "stops.txt")
routes = pd.read_csv(gtfs_folder / "routes.txt")
trips = pd.read_csv(gtfs_folder / "trips.txt")
stop_times = pd.read_csv(gtfs_folder / "stop_times.txt")
shapes = pd.read_csv(gtfs_folder / "shapes.txt")
calendar_dates = pd.read_csv(gtfs_folder / "calendar_dates.txt")

# Helper: convert values to Python types safely
def to_python_types(value):
    if pd.isna(value):
        return None
    try:
        return value.item()  # numpy scalar → Python scalar
    except AttributeError:
        return value

# --- STOPS: convert to GeoJSON points ---
stop_features = []
for _, stop in stops.iterrows():
    props = {k: to_python_types(stop[k]) for k in stops.columns if k not in ["stop_lat", "stop_lon"]}
    feature = geojson.Feature(
        geometry=geojson.Point((float(stop["stop_lon"]), float(stop["stop_lat"]))),
        properties=props
    )
    stop_features.append(feature)

stops_fc = geojson.FeatureCollection(stop_features)

# --- ROUTES/TRIPS: convert shapes to GeoJSON lines ---
route_features = []

for shape_id, shape_group in shapes.groupby("shape_id"):
    shape_group = shape_group.sort_values("shape_pt_sequence")
    coords = list(zip(shape_group["shape_pt_lon"].astype(float), shape_group["shape_pt_lat"].astype(float)))
    
    trips_for_shape = trips[trips["shape_id"] == shape_id]
    
    for _, trip in trips_for_shape.iterrows():
        # Select the route as a single row
        route_row = routes[routes["route_id"] == trip["route_id"]]
        if len(route_row) == 0:
            continue  # skip if route not found
        route_row = route_row.iloc[0]
        
        # Get exceptions for this trip
        exceptions = calendar_dates[calendar_dates["service_id"] == trip["service_id"]]
        exception_list = [ {k: to_python_types(v) for k, v in r.items()} for r in exceptions.to_dict(orient="records") ]
        
        feature_props = {
            "trip_id": to_python_types(trip["trip_id"]),
            "route_id": to_python_types(trip["route_id"]),
            "route_short_name": to_python_types(route_row.get("route_short_name")),
            "route_long_name": to_python_types(route_row.get("route_long_name")),
            "route_type": to_python_types(route_row.get("route_type")),
            "service_exceptions": exception_list
        }
        
        feature = geojson.Feature(
            geometry=geojson.LineString(coords),
            properties=feature_props
        )
        route_features.append(feature)

routes_fc = geojson.FeatureCollection(route_features)

# --- Save to GeoJSON files ---
geojson_folder = gtfs_folder.parent #/ "geojson"
geojson_folder.mkdir(exist_ok=True)

with open(geojson_folder / "stops.geojson", "w") as f:
    geojson.dump(stops_fc, f, indent=2)

with open(geojson_folder / "routes.geojson", "w") as f:
    geojson.dump(routes_fc, f, indent=2)

print(f"Saved stops to {geojson_folder / 'stops.geojson'}")
print(f"Saved routes to {geojson_folder / 'routes.geojson'}")