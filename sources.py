import os
import geopandas as gpd
import pandas as pd
from pathlib import Path
sources = [Path(os.path.join('./sources/'+n)) for n in next(os.walk('./sources/'))[2]]
datasets = {
    src.stem: gpd.read_file(str(src.resolve())).to_crs(epsg=4326)
    for src in sources
    if src.suffix == '.geojson'
}

def to_pd(gdf:gpd.GeoDataFrame) -> pd.DataFrame:
    df = gdf.copy()
    df["geometry"] = df.geometry.to_wkt()
    return df