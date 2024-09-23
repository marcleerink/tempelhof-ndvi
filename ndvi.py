import os

import pandas as pd
from dotenv import load_dotenv
from sentinelhub import (
    CRS,
    DataCollection,
    Geometry,
    SentinelHubStatistical,
    SHConfig,
    parse_time,
)


def stats_to_df(stats_data):
    """Transform Statistical API response into a pandas.DataFrame"""
    df_data = []

    for single_data in stats_data["data"]:
        df_entry = {}
        is_valid_entry = True

        df_entry["interval_from"] = parse_time(single_data["interval"]["from"]).date()
        df_entry["interval_to"] = parse_time(single_data["interval"]["to"]).date()

        for output_name, output_data in single_data["outputs"].items():
            for band_name, band_values in output_data["bands"].items():
                band_stats = band_values["stats"]
                if band_stats["sampleCount"] == band_stats["noDataCount"]:
                    is_valid_entry = False
                    break

                for stat_name, value in band_stats.items():
                    col_name = f"{output_name}_{band_name}_{stat_name}"
                    if stat_name == "percentiles":
                        for perc, perc_val in value.items():
                            perc_col_name = f"{col_name}_{perc}"
                            df_entry[perc_col_name] = perc_val
                    else:
                        df_entry[col_name] = value

        if is_valid_entry:
            df_data.append(df_entry)

    return pd.DataFrame(df_data)


def statistical_request(
    config: SHConfig,
    evalscript: str,
    time_interval: tuple[str, str],
    geometry: Geometry,
    aggregation_interval: str,
    data_collection: DataCollection,
    resolution: int,
) -> list:
    request = SentinelHubStatistical(
        aggregation=SentinelHubStatistical.aggregation(
            evalscript=evalscript,
            time_interval=time_interval,
            aggregation_interval=aggregation_interval,
            resolution=(resolution, resolution),
        ),
        input_data=[
            SentinelHubStatistical.input_data(
                data_collection=data_collection, maxcc=0.1
            )
        ],
        config=config,
        geometry=geometry,
    )

    return request.get_data()


# Load SentinelHub credentials from .env file
load_dotenv()
config = SHConfig()
config.instance_id = os.getenv("SH_INSTANCE_ID")
config.sh_client_id = os.getenv("SH_CLIENT_ID")
config.sh_client_secret = os.getenv("SH_CLIENT_SECRET")

# Define the geometry of the area of interest (Berlin)
geojson = {
    "type": "FeatureCollection",
    "features": [
        {
            "type": "Feature",
            "properties": {},
            "geometry": {
                "coordinates": [
                    [
                        [13.394144213342685, 52.478172357231045],
                        [13.394144213342685, 52.468812826509776],
                        [13.41306078706259, 52.468812826509776],
                        [13.41306078706259, 52.478172357231045],
                        [13.394144213342685, 52.478172357231045],
                    ]
                ],
                "type": "Polygon",
            },
        }
    ],
}
geometry = Geometry(geojson["features"][0]["geometry"], crs=CRS.WGS84)


evalscript = """
//VERSION=3
function cloud_free(sample) {
  var scl = sample.SCL;
  var clm = sample.CLM;

  if (clm === 1 || clm === 255) {
    return false;
  } else if (scl === 1 || scl === 3 || scl === 8 || scl === 9 || scl === 10 || scl === 11) {
    return false;
  } else {
    return true;
  }
}

function setup() {
  return {
    input: [{
      bands: [
        "B04",
        "B08",
        "SCL",
        "CLM",
        "dataMask"
      ]
    }],
    mosaicking: "ORBIT",
    output: [
      {
        id: "data",
        bands: ["daily_max_ndvi"]
      },
      {
        id: "dataMask",
        bands: 1
      }
    ]
  };
}

function evaluatePixel(samples, scenes) {
  var max = 0;
  var hasData = 0;

  for (var i = 0; i < samples.length; i++) {
    var sample = samples[i];

    if (cloud_free(sample) && sample.dataMask == 1 && sample.B04 + sample.B08 != 0) {
      hasData = 1;
      var ndvi = (sample.B08 - sample.B04) / (sample.B08 + sample.B04);
      max = ndvi > max ? ndvi : max;
    }
  }

  return {
    data: [max],
    dataMask: [hasData]
  };
}

"""

time_interval = ("2015-01-01", "2023-01-01")


statistical_data = statistical_request(
    config=config,
    evalscript=evalscript,
    time_interval=time_interval,
    geometry=geometry,
    aggregation_interval="P1M",
    data_collection=DataCollection.SENTINEL2_L2A,
    resolution=10,
)

dfs = [stats_to_df(data) for data in statistical_data]

for i, df in enumerate(dfs):
    df.to_csv(f"ndvi_{i}.csv", index=False)
