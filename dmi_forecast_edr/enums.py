from enum import Enum
# See https://opendataapi.dmi.dk/v1/forecastedr/collections/
class Collection(Enum):
   WamDw = "wam_dw"
   WamNsb = "wam_nsb"
   WamNatLant = "wam_natlant"
   DkssIdw = "dkss_idw"
   DkssIf = "dkss_if"
   DkssLb = "dkss_lb"
   DkssLf = "dkss_lf"
   DkssNsbs = "dkss_nsbs"
   DkssWs = "dkss_ws"
   HarmonieIgPl = "harmonie_ig_pl"
   HarmonieIgSf = "harmonie_ig_sf"
   HarmonieDiniPl = "harmonie_dini_pl"
   HarmonieDiniSf = "harmonie_dini_sf"
   HarmonieDiniEpsM = "harmonie_dini_eps_means"
   HarmonieDiniEpsPer = "harmonie_dini_eps_percentiles"
   HarmonieDiniEpsProb = "harmonie_dini_eps_propabilities"