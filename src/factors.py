"""
Emission factors, auxiliary power demand and correction factors, transcribed from the
published inventory literature.

Primary source
--------------
Olmer, N., Comer, B., Roy, B., Mao, X., & Rutherford, D. (2017). "Greenhouse gas emissions
from global shipping, 2013-2015: Detailed methodology." ICCT.
https://theicct.org/sites/default/files/Global-shipping-GHG-emissions-2013-2015_Methodology_17102017_vF.pdf

That document is itself the bridge between the Third IMO GHG Study 2014 (Smith et al.) and
the Fourth IMO GHG Study 2020 (Faber et al.), and it publishes the auxiliary power and
emission factor tables in full, which the IMO studies do not do in an easily citable form.

Everything in this file is transcribed from a published table. Analyst assumptions live in
config.py, not here.
"""

# ======================================================================================
# ENERGY-BASED EMISSION FACTORS, g per kWh of engine output
# ICCT Appendix E (main engines) and Appendix G (auxiliary engines).
#
# Using energy-based CO2 factors rather than SFC x carbon factor removes one estimation
# step. The implied SFC is recoverable: 670 / 3.114 = 215 g/kWh for a medium-speed engine
# on residual fuel, which is the Third and Fourth IMO GHG Study baseline value.
# ======================================================================================

# fuel keys: "residual" (HFO/IFO), "distillate" (MDO/MGO), "eca" (0.1% S distillate)
ME_EF = {
    # engine family -> pollutant -> fuel -> g/kWh
    "SSD": {
        "CO2": {"residual": 607, "distillate": 593, "eca": 593},
        "PM":  {"residual": 1.42, "distillate": 0.20, "eca": 0.19},
        "CO":  {"residual": 0.54, "distillate": 0.54, "eca": 0.54},
        "CH4": {"residual": 0.01, "distillate": 0.01, "eca": 0.01},
        "N2O": {"residual": 0.03, "distillate": 0.03, "eca": 0.03},
        # SOx at 2.5% S; scaled linearly to actual sulphur content in the model
        "SOx_at_2p5S": {"residual": 10.29, "distillate": 10.29, "eca": 10.29},
    },
    "MSD": {
        "CO2": {"residual": 670, "distillate": 658, "eca": 658},
        "PM":  {"residual": 1.43, "distillate": 0.20, "eca": 0.19},
        "CO":  {"residual": 0.54, "distillate": 0.54, "eca": 0.54},
        "CH4": {"residual": 0.01, "distillate": 0.01, "eca": 0.01},
        "N2O": {"residual": 0.03, "distillate": 0.03, "eca": 0.03},
        "SOx_at_2p5S": {"residual": 11.35, "distillate": 11.35, "eca": 11.35},
    },
}

AE_EF = {
    "CO2": {"residual": 707, "distillate": 696, "eca": 696},
    "PM":  {"residual": 1.44, "distillate": 0.20, "eca": 0.19},
    "CO":  {"residual": 0.54, "distillate": 0.54, "eca": 0.54},
    "CH4": {"residual": 0.01, "distillate": 0.01, "eca": 0.01},
    "N2O": {"residual": 0.04, "distillate": 0.03, "eca": 0.03},
    "SOx_at_2p5S": {"residual": 11.98, "distillate": 11.98, "eca": 11.98},
    "BC": {"residual": 0.12, "distillate": 0.06, "eca": 0.06},  # g/kWh, ICCT App G
}

# NOx, g/kWh. ICCT Appendix E. Tier from build year (MARPOL Annex VI Reg. 13).
# For 130-1,999 rpm engines the standard is rpm-dependent; evaluated in the model.
ME_NOX = {
    "SSD": {"Tier0": {"residual": 18.10, "distillate": 17.01},
            "TierI": {"residual": 17.00, "distillate": 15.98},
            "TierII": {"residual": 14.40, "distillate": 13.54}},
    # MSD/HSD Tier 0 is a flat value; Tiers I and II follow the rpm formulas
    "MSD": {"Tier0": {"residual": 14.00, "distillate": 13.16}},
}
AE_NOX = {"Tier0": {"residual": 14.70, "distillate": 13.82}}


def me_nox_msd(tier, rpm, fuel):
    """MARPOL Tier I/II NOx limits for 130-1,999 rpm engines, per ICCT Appendix E."""
    if tier == "Tier0":
        return ME_NOX["MSD"]["Tier0"][fuel]
    if tier == "TierI":
        v = 0.94 * 45 * rpm ** -0.2
    else:
        v = 0.94 * 44 * rpm ** -0.23
    # the table's distillate values sit about 6% below residual
    return v * (1.0 if fuel == "residual" else 0.94)


def nox_tier(built):
    if built is None or built != built:
        return "Tier0"
    if built < 2000:
        return "Tier0"
    if built <= 2010:
        return "TierI"
    return "TierII"


# ======================================================================================
# BLACK CARBON, g per kg of fuel, by engine stroke, fuel and main engine load.
# ICCT Table F-3 (central estimate). Load-dependent, which matters here because these
# ferries run at low load.
# ======================================================================================
BC_G_PER_KG_FUEL = {
    # load fraction -> (2-stroke residual, 4-stroke residual, 2-stroke dist, 4-stroke dist)
    0.05: (0.44, 4.52, 0.10, 3.48),
    0.10: (0.34, 2.31, 0.08, 1.60),
    0.15: (0.30, 1.56, 0.07, 1.01),
    0.20: (0.27, 1.18, 0.06, 0.73),
    0.25: (0.25, 0.95, 0.05, 0.57),
    0.30: (0.23, 0.80, 0.05, 0.46),
    0.35: (0.22, 0.69, 0.05, 0.39),
    0.40: (0.21, 0.60, 0.04, 0.34),
    0.45: (0.20, 0.54, 0.04, 0.29),
    0.50: (0.19, 0.49, 0.04, 0.26),
    0.60: (0.18, 0.41, 0.04, 0.21),
    0.70: (0.17, 0.35, 0.04, 0.18),
    0.80: (0.16, 0.31, 0.03, 0.15),
    0.90: (0.16, 0.28, 0.03, 0.14),
    1.00: (0.15, 0.25, 0.03, 0.12),
}


def bc_ef(load, engine_family, fuel):
    keys = sorted(BC_G_PER_KG_FUEL)
    k = min(keys, key=lambda x: abs(x - max(0.05, min(1.0, load))))
    two_r, four_r, two_d, four_d = BC_G_PER_KG_FUEL[k]
    if engine_family == "SSD":
        return two_r if fuel == "residual" else two_d
    return four_r if fuel == "residual" else four_d


# ======================================================================================
# LOW LOAD ADJUSTMENT FACTORS, applied when main engine load < 20%.
# ICCT Appendix I (from the Third IMO GHG Study 2014).
# Note the CO2 column is 1.00 throughout: the IMO studies handle the fuel penalty at low
# load through the SFOC load curve below, not through an LLAF.
# ======================================================================================
LLAF = {
    0.02: {"PM": 7.29, "NOx": 4.63, "CO": 9.70, "CH4": 21.18, "N2O": 4.63},
    0.05: {"PM": 2.44, "NOx": 1.83, "CO": 3.90, "CH4": 5.61, "N2O": 1.83},
    0.08: {"PM": 1.61, "NOx": 1.35, "CO": 2.45, "CH4": 2.95, "N2O": 1.35},
    0.10: {"PM": 1.38, "NOx": 1.22, "CO": 1.97, "CH4": 2.18, "N2O": 1.22},
    0.12: {"PM": 1.24, "NOx": 1.14, "CO": 1.64, "CH4": 1.76, "N2O": 1.14},
    0.15: {"PM": 1.11, "NOx": 1.06, "CO": 1.32, "CH4": 1.36, "N2O": 1.06},
    0.18: {"PM": 1.04, "NOx": 1.02, "CO": 1.11, "CH4": 1.11, "N2O": 1.02},
    0.20: {"PM": 1.00, "NOx": 1.00, "CO": 1.00, "CH4": 1.00, "N2O": 1.00},
}


def llaf(load, pollutant):
    if load >= 0.20 or pollutant in ("CO2", "SOx", "BC"):
        return 1.0
    keys = sorted(LLAF)
    k = min(keys, key=lambda x: abs(x - load))
    return LLAF[k].get(pollutant, 1.0)


def sfoc_load_factor(load):
    """
    Specific fuel consumption as a function of engine load, normalised to 1.0 at the
    engine's most efficient point.

        f(l) = 0.455 l^2 - 0.710 l + 1.28

    Third IMO GHG Study 2014, carried into the Fourth. The ICCT methodology reproduces
    this with a leading coefficient of 0.405, which places the curve's minimum at 0.97
    rather than 1.00; 0.455 is used here because it puts the minimum at exactly 1.00 at
    78% load, which is the intended construction.

    At 15% load this returns 1.18, an 18% fuel penalty. That penalty is the mechanism by
    which the IMO method handles low-load operation, and it replaces the ad hoc minimum
    load floor used in the first pass of this analysis.
    """
    load = max(0.02, min(1.0, load))
    return 0.455 * load ** 2 - 0.710 * load + 1.28


# ======================================================================================
# AUXILIARY ENGINE AND BOILER POWER DEMAND, kW, by ship class, size bin and phase.
# ICCT Appendix C and D, identical to the Third IMO GHG Study 2014.
#
# This replaces the "auxiliary load is some percentage of installed MCR" assumption used
# in the first pass. For ro-pax ferries the IMO figure is a flat kW value that does not
# scale with main engine size, and it is the same in every phase, which reflects the fact
# that a ferry's hotel and vehicle-deck ventilation load runs continuously.
# ======================================================================================
AUX_KW = {
    # class -> list of (upper capacity bound, {phase: kW})
    "ferry_ropax": [(2000, {"cruise": 105, "manoeuvre": 105, "berth": 105, "anchor": 105}),
                    (1e9, {"cruise": 710, "manoeuvre": 710, "berth": 710, "anchor": 710})],
    "ferry_pax":   [(2000, {"cruise": 186, "manoeuvre": 186, "berth": 186, "anchor": 186}),
                    (1e9, {"cruise": 524, "manoeuvre": 524, "berth": 524, "anchor": 524})],
    "roro":        [(5000, {"cruise": 600, "manoeuvre": 1700, "berth": 800, "anchor": 800}),
                    (1e9, {"cruise": 950, "manoeuvre": 2720, "berth": 1200, "anchor": 1200})],
    "vehicle":     [(1e9, {"cruise": 500, "manoeuvre": 1125, "berth": 800, "anchor": 800})],
    "general_cargo": [(5000, {"cruise": 60, "manoeuvre": 90, "berth": 120, "anchor": 60}),
                      (10000, {"cruise": 170, "manoeuvre": 250, "berth": 330, "anchor": 170}),
                      (1e9, {"cruise": 490, "manoeuvre": 730, "berth": 970, "anchor": 490})],
    "tug":         [(1e9, {"cruise": 50, "manoeuvre": 50, "berth": 50, "anchor": 50})],
}

# Boiler demand, ICCT Appendix D. Ferry ro-pax and ferry pax-only are zero in every phase.
BOILER_KW = {
    "ferry_ropax": 0.0, "ferry_pax": 0.0, "tug": 0.0,
    "roro": {"cruise": 0, "manoeuvre": 200, "berth": 200, "anchor": 200},
    "vehicle": {"cruise": 0, "manoeuvre": 268, "berth": 268, "anchor": 268},
    "general_cargo": {"cruise": 0, "manoeuvre": 75, "berth": 75, "anchor": 75},
}


def aux_kw(ship_class, capacity, phase):
    bins = AUX_KW.get(ship_class, AUX_KW["ferry_ropax"])
    cap = capacity if capacity == capacity else 0.0
    for upper, phases in bins:
        if cap < upper:
            return phases[phase]
    return bins[-1][1][phase]


def boiler_kw(ship_class, phase):
    b = BOILER_KW.get(ship_class, 0.0)
    if isinstance(b, dict):
        return b[phase]
    return b


# Map the register's vessel type strings onto ICCT/IMO ship classes.
CLASS_MAP = {
    "Ro-ro Ferry": "ferry_ropax",
    "Passenger Ro-ro Cargo": "ferry_ropax",
    "Car Ferry": "ferry_ropax",
    "Pass./Car Ferry": "ferry_ropax",
    "Passenger Vessel": "ferry_pax",
    "Ferry": "ferry_pax",
    "Landing Craft": "ferry_ropax",
    "Ro-ro Cargo": "roro",
    "Pure Car Carrier": "vehicle",
    "General Cargo": "general_cargo",
    "Tug": "tug",
}


def ship_class_of(vessel_type):
    return CLASS_MAP.get(vessel_type, "ferry_ropax")


# ======================================================================================
# HULL FOULING. ICCT section 2.4.2.2, after Townsin (2000, 2003) and Willsher (2007).
#   HFF = 1.02 + 0.044 * [ (kf/L)^(1/3) - (k0/L)^(1/3) ] / (0.018 * L^(-1/3))
# with average hull roughness kf set by ship age, k0 = 120 micron for a new hull.
# The L terms cancel, leaving HFF = 1.02 + 2.444 * (kf^(1/3) - k0^(1/3)) with k in metres.
# ======================================================================================
AHR_MICRON = [(1, 120), (5, 150), (10, 200), (15, 300), (20, 400), (1e9, 500)]


def hull_fouling_factor(age_years):
    if age_years is None or age_years != age_years:
        age_years = 20
    kf = next(v for upper, v in AHR_MICRON if age_years <= upper)
    k0 = 120.0
    return 1.02 + (0.044 / 0.018) * ((kf * 1e-6) ** (1 / 3) - (k0 * 1e-6) ** (1 / 3))


# Weather factor. ICCT section 2.4.2.3, following the Third IMO GHG Study: +10% power
# demand for coastal shipping within 5 nm of shore. The Sunda Strait crossing is entirely
# coastal, so the coastal value applies throughout.
WEATHER_FACTOR_COASTAL = 1.10

# Draught adjustment factor for ferry ro-pax. ICCT Table 13, 2015 value. Ferries run close
# to their design draught, unlike bulkers and tankers.
DAF_FERRY_ROPAX = 0.9459

# Global warming potentials. ICCT Table 15: CH4 and N2O from IPCC AR4, BC from Bond et al.
# (2013). Reported on both horizons because black carbon's weight depends heavily on which
# is used, and BC is a large share of the warming from a low-load, residual-fuelled fleet.
GWP = {
    20:  {"CO2": 1, "CH4": 72, "N2O": 289, "BC": 3200},
    100: {"CO2": 1, "CH4": 25, "N2O": 298, "BC": 900},
}

LHV_MJ_PER_KG = {"residual": 40.2, "distillate": 42.7}
CF_TCO2_PER_T = {"residual": 3.114, "distillate": 3.206}
