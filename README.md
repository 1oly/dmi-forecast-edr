# DMI Forecast EDR API
Python interface to the The Danish Meteorological Institute's (DMI) Open Data Forecast EDR API. This repo is a copy of [DMI-Open-Data](https://github.com/LasseRegin/dmi-open-data) with the one modification that it taps into the [Forecast EDR API](https://opendatadocs.dmi.govcloud.dk/en/APIs/Forecast_Data_EDR_API) instead.

The status is work-in-progress. There are many combinations of forecast models and parameters which have not been properly tested...

**NOTE:** The forecast models "NEA" and "IGB" will expire and transition to "DINI" and "IG" in May 2024. Read more [here.](https://opendatadocs.dmi.govcloud.dk/Guides/Forecast-Model-Announcement) This has some consequences for the API in this repo, but the new models should work.

## Requirements

- Python 3.6+
- API Key for [**Forecast EDR v1**](https://opendatadocs.dmi.govcloud.dk/en/Authentication)

## Installation

```bash
$ pip install git+https://github.com/1oly/dmi-forecast-edr
```

## Example

```python
import os
from datetime import datetime
from dmi_forecast_edr import DMIForecastEDRClient, Collection

client = DMIForecastEDRClient(api_key=os.getenv('DMI_FORECAST_API_KEY'))

dtnow = datetime.now()

forecasts = client.get_forecast(
    collection = Collection.HarmonieDiniSf,
    parameter = ['wind-speed','wind-dir'],
    crs = 'crs84',
    to_time = dtnow,
    f = 'GeoJSON',
    coords = [12.5692,55.6757],
)
```
Parameters can be found in the [documentation](https://opendatadocs.dmi.govcloud.dk/en/Data/Forecast_Data_Weather_Model_HARMONIE_EDR).