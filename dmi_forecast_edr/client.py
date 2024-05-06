from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any, Union

import requests
from tenacity import retry, stop_after_attempt, wait_random

from dmi_forecast_edr.enums import Collection

class DMIForecastEDRClient:
    _base_url = "https://dmigw.govcloud.dk/{version}/{api}"

    def __init__(self, api_key: str, version: str = "v1"):
        if api_key is None:
            raise ValueError(f"Invalid value for `api_key`: {api_key}")
        if version not in ["v1"]:
            raise ValueError(f"API version {version} not supported")

        self.api_key = api_key
        self.version = version

    def base_url(self, api: str):
        if api != "forecastedr":
            raise NotImplementedError(f"Following api is not supported yet: {api}")
        return self._base_url.format(version=self.version, api=api)

    @retry(stop=stop_after_attempt(10), wait=wait_random(min=0.1, max=1.00))
    def _query(self, api: str, service: str, params: Dict[str, Any], **kwargs):
        res = requests.get(
            url=f"{self.base_url(api=api)}/{service}",
            params={
                "api-key": self.api_key,
                **params,
            },
            **kwargs,
        )
        data = res.json()
        http_status_code = data.get("http_status_code", 200)
        if http_status_code != 200:
            message = data.get("message")
            raise ValueError(
                f"Failed HTTP request with HTTP status code {http_status_code} and message: {message}"
            )
        return res.json()

    def get_forecast(
        self,
        collection: Optional[Collection] = None,
        parameter: Optional[str] = None,
        from_time: Optional[datetime] = None,
        to_time: Optional[datetime] = None,
        crs: Optional[str] = None, 
        coords: Optional[list] = None, 
        f: Optional[str] = None, 
    ) -> List[Dict[str, Any]]:
        """Get Forecast

        Args:
            collection (Optional[Collection], optional): Returns forecast for a specific model.
                Defaults to None.
            parameter (Optional[str], optional): Returns forecast for a specific parameter. See: https://opendatadocs.dmi.govcloud.dk/Data/Forecast_Data_Weather_Model_HARMONIE_DINI_IG
                Defaults to None.
            from_time (Optional[datetime], optional): Returns only objects with a "timeObserved" equal
                to or after a given timestamp. Defaults to None.
            to_time (Optional[datetime], optional): Returns only objects with a "timeObserved" before
                (not including) a given timestamp. Defaults to None.
            crs (Optional[str], optional): Coordinate reference, "native" (default) or "crs84".
                Defaults to None.
            coords (Optional[list], optional): Return forecast for a point [Lon, Lat] or square [Lon1, Lat1, Lon2, Lat2]
                Defaults to None.
            f (Optional[str], optional): Return forecast as "CoverageJSON" (default) or "GeoJSON"
                Defaults to None.

        Returns:
            List[Dict[str, Any]]: List of raw DMI observations.
        """
        service,extra_params = _construct_query(None if collection is None else collection.value, coords)
        params = {
                "crs": crs,
                "parameter-name": ','.join(parameter),
                "datetime": _construct_datetime_argument(from_time=hour_rounder(from_time), to_time=hour_rounder(to_time), instance=False),
                "f": f
            }
        params.update(extra_params)
        res = self._query(
            api="forecastedr",
            service=service,
            params=params,
        )
        return res.get("features",[]) # only works with f=GeoJSON

    def list_collection(self) -> List[Dict[str, Union[str, Collection]]]:
        """List available models.

        Returns:
            List[Dict[str, Union[str, Collection]]]: List of dictionaries
                containing information about each available models
        """
        return [
            {
                "name": collection.name,
                "value": collection.value,
                "enum": collection,
            }
            for collection in Collection
        ]

    @staticmethod
    def get_collection(collection_id: str) -> Collection:
        """Get collection enum from DMI collection id.

        Args:
            collection_id (str): Collection id found on DMI Forecast EDR API documentation.

        Returns:
            Collection: Collection enum object.
        """
        return Collection(collection_id)

# https://stackoverflow.com/questions/48937900/round-time-to-nearest-hour-python
def hour_rounder(t):
    # Rounds to nearest hour by adding a timedelta hour if minute >= 30
    if t is not None:
        return (t.replace(second=0, microsecond=0, minute=0, hour=t.hour)
               +timedelta(hours=t.minute//30))
    else:
        return None

def _construct_datetime_argument(
    from_time: Optional[datetime] = None, to_time: Optional[datetime] = None, instance = True
) -> str:
    if from_time is None and to_time is None:
        return None
    if from_time is not None and to_time is None and instance == True:
        return f"{from_time.isoformat()}Z"
    if from_time is None and to_time is not None and instance == False:
        return f"{to_time.isoformat()}Z"
    return f"{from_time.isoformat()}Z/{to_time.isoformat()}Z"

def _construct_query(
    collection: Optional[Collection] = None,
    coords: Optional[list] = None
) -> str:
    if len(coords) == 2:
        return f"collections/{collection}/position",{'coords': f'POINT({coords[0]} {coords[1]})'}
    if len(coords) == 4:
        return f"collections/{collection}/cube",{'bbox' : f'{coords[0]},{coords[1]},{coords[2]},{coords[3]}'}
    else:
        return None, None