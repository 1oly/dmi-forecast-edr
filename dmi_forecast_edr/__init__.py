"""Python interface to DMI forecast data API"""

__version__ = "0.0.3"

from dmi_forecast_edr.enums import Collection
from dmi_forecast_edr.client import DMIForecastEDRClient

__all__ = [
    "DMIForecastEDRClient",
    "Collection",
]
