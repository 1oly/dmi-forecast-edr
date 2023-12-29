from enum import Enum

# See https://confluence.govcloud.dk/pages/viewpage.action?pageId=53086314
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
   HarmonieIgbMl = "harmonie_igb_ml"
   HarmonieIgbPl = "harmonie_igb_pl"
   HarmonieIgbSf = "harmonie_igb_sf"
   HarmonieNeaMl = "harmonie_nea_ml"
   HarmonieNeaPl = "harmonie_nea_pl"
   HarmonieNeaSf = "harmonie_nea_sf"