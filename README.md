# DMI Forecast EDR API
Python interface to the The Danish Meteorological Institute's (DMI) Open Data Forecast EDR API. This repo is a copy of [DMI-Open-Data](https://github.com/LasseRegin/dmi-open-data) with the one modification that it taps into the [Forecast EDR API](https://www.dmi.dk/friedata/dokumentation/forecast-data-edr-api) instead.

The status is work-in-progress. There are many combinations of forecast models and parameters which have not been properly tested...

## Requirements

- Python 3.10+

## Installation

```bash
$ pip install git+https://github.com/1oly/dmi-forecast-edr
```

## Example

```python
import os
from datetime import datetime
from dmi_forecast_edr import DMIForecastEDRClient, Collection

client = DMIForecastEDRClient()

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
Parameters can be found in the [documentation](https://opendataapi.dmi.dk/v1/forecastedr/collections/).