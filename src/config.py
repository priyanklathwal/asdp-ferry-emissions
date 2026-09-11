"""
Central assumptions register for the ASDP / Indonesia RoPax energy and emissions model.

EVERY number that is not read from the input workbook lives here, with a source tag.
Source tags:
  [IMO]      International Maritime Organization instrument or GHG study
  [MKT]      Market price observation, dated
  [GOV]      Indonesian government / regulated tariff
  [LIT]      Peer-reviewed or grey literature
  [ASSUM]    Analyst assumption. NOT sourced. Must be reviewed before any external use.
"""

# ----------------------------------------------------------------------------------
# 1. ROUTE GEOMETRY
# ----------------------------------------------------------------------------------
ROUTE = {
    "name": "Merak (Java) - Bakauheni (Sumatra)",
    "distance_nm": 15.0,
    "distance_nm_source": "[LIT] Indonesian ferry-operations literature consistently states the "
                          "Bakauheni-Merak crossing as 15 miles (nautical), with scheduled sailing "
                          "times of 90-120 minutes depending on berth. Great-circle distance between "
                          "the two port coordinates is 15.1 nm, which corroborates this.",
    # Vessels do not sail the great-circle line. Sensitivity range used in the dashboard.
    "distance_nm_low": 15.0,
    "distance_nm_high": 19.0,
}

# ----------------------------------------------------------------------------------
# 2. FUEL CARBON FACTORS (tonnes CO2 per tonne fuel burned, tank-to-wake)
#    [IMO] Resolution MEPC.281(70), Table 1 - CF conversion factors.
# ----------------------------------------------------------------------------------
CF = {
    "MDO": 3.206,      # Diesel / Gas Oil, ISO 8217 DMX-DMB
    "MGO": 3.206,
    "HFO": 3.114,      # Heavy Fuel Oil, ISO 8217 RME-RMK
    "LFO": 3.151,
    "LNG": 2.750,
    "METHANOL": 1.375,
}

# Lower heating values, MJ/kg. [IMO] MEPC.281(70) Table 1.
LHV_MJ_PER_KG = {
    "MDO": 42.7,
    "MGO": 42.7,
    "HFO": 40.2,
    "LFO": 41.2,
    "METHANOL": 19.9,
}

# Fuel densities, kg/litre. [ASSUM] typical ISO 8217 grades at 15 C.
DENSITY_KG_PER_L = {
    "MDO": 0.86,
    "MGO": 0.86,
    "HFO": 0.98,
    "B40": 0.86,
}

# ----------------------------------------------------------------------------------
# 3. EMISSION FACTORS AND ENGINE BEHAVIOUR
#    Moved to src/factors.py in v2. Everything there is transcribed from a published
#    table (ICCT Olmer et al. 2017 detailed methodology, which reproduces the Third IMO
#    GHG Study tables in citable form). Nothing in factors.py is analyst judgement.
# ----------------------------------------------------------------------------------
REFERENCE_YEAR = 2026

# Engine speed is not in the register. Needed only to evaluate the rpm-dependent MARPOL
# Tier I and Tier II NOx limits, which do not affect CO2 at all.
ASSUMED_RPM = {"SSD": 120, "MSD": 750}        # [ASSUM]

ASSUMED_AGE_UNMATCHED = 26                     # [ASSUM] for route vessels absent from the register

# Fuel sulphur content, mass percent. Drives SOx and part of PM.
# The IMO 0.50% global cap has applied since 2020 and Indonesia is a party to MARPOL
# Annex VI. Note however that Pertamina's published domestic price list still sells
# "MFO High Sulphur" more cheaply than "MFO Low Sulphur", which suggests real-world
# compliance on domestic ferry routes is worth checking. Sensitivity to 2.5% is reported.
SULPHUR_PCT = {"residual": 0.50, "distillate": 0.10}   # [GOV/ASSUM]

# ----------------------------------------------------------------------------------
# 4. POWER ESTIMATION
# ----------------------------------------------------------------------------------
POWER = {
    "block_coefficient": 0.60,      # [ASSUM] typical RoPax / car-ferry monohull
    "admiralty_coefficient": 450.0, # [LIT] Admiralty constant, ferry range roughly 400-500
    "seawater_density": 1.025,
    "lpp_over_loa": 0.95,           # [ASSUM]
    "service_power_fraction_of_mcr": 0.80,  # [ASSUM] service speed at ~80% MCR
    "kw_per_gt_floor": 0.25,        # [ASSUM] plausibility bound on installed MCR
    "kw_per_gt_ceiling": 1.60,      # [ASSUM] plausibility bound on installed MCR
    "draft_over_beam_cap": 0.32,    # [ASSUM] median in this register is 0.21
    "note": "Displacement from LOA x beam x draft x Cb where reported, else from a log-log "
            "fit of displacement on GT. Propulsion power at sea uses the Admiralty relation "
            "at the OBSERVED steaming speed with the ICCT correction factors (hull fouling, "
            "weather, draught) applied multiplicatively, so the register's unreliable "
            "design-speed field does not propagate into the fuel estimate. Installed MCR is "
            "estimated at design speed and used only for the load factor, the manoeuvring "
            "floor and battery sizing.",
}

# ----------------------------------------------------------------------------------
# 5. OPERATING PROFILE
# ----------------------------------------------------------------------------------
OPS = {
    # Phase split. The IMO/ICCT method assigns phases from instantaneous speed over ground;
    # with port-to-port events only, waiting is identified as the excess of a crossing over
    # that vessel's own fastest crossings.
    "free_running_percentile": 0.10,      # [ASSUM] the vessel's own p10 crossing time
    "t_free_clip": (1.0, 4.0),            # [ASSUM] hours, bounds on the unimpeded crossing
    "manoeuvre_hours_per_voyage": 0.60,   # [ASSUM] 0.3 h at each end, inside the AIS polygons
    "manoeuvre_speed_kn": 5.0,            # [LIT] ICCT phase boundary between manoeuvre and cruise
    "manoeuvre_load_floor": 0.08,         # [ASSUM] thrusters and berthing work
    "max_load": 0.98,                     # [LIT] ICCT caps load factor at 0.98 of MCR
    "voyage_hours_clip": (0.5, 8.0),
    "berth_hours_cap": 6.0,               # [ASSUM] longer gaps treated as lay-up
}

# ----------------------------------------------------------------------------------
# 6. PRICES
# ----------------------------------------------------------------------------------
FX_IDR_PER_USD = 17900.0
FX_SOURCE = "[MKT] Mid-market USD/IDR 17,900 on 11 September 2026 (50-day average 17,927; " \
            "52-week range 16,095 to 18,180)."

PRICES = {
    # Indonesian domestic, ex-VAT/PBBKB, Region 1 (Sumatra, Java, Bali, Madura)
    "b40_hsd_idr_per_litre": 23050.0,
    "mfo_hs_idr_per_litre": 14900.0,
    "mfo_ls_idr_per_litre": 16850.0,
    "domestic_fuel_source": "[MKT] Pertamina non-subsidised industrial 'harga keekonomian', "
                            "15-31 March 2026 period, as reported by fuel distributors. "
                            "This was an oil-price spike fortnight (Brent above USD 100) and is "
                            "NOT a good annual planning number. Verify against ASDP's own "
                            "bunker invoices before use.",

    # International benchmarks, Singapore
    "vlsfo_usd_per_tonne": 800.0,
    "mgo_usd_per_tonne": 1150.0,
    "intl_fuel_source": "[MKT] Singapore VLSFO ranged roughly USD 780-850/t and MGO USD 1,100-1,220/t "
                        "through August 2026; VLSFO briefly exceeded USD 1,000/t in March 2026.",

    # Biofuel
    "b30_vlsfo_premium_usd_per_tonne": 231.0,
    "b100_usd_per_tonne": 1390.0,
    "biofuel_source": "[MKT] Singapore B30-VLSFO premium over conventional VLSFO reported at "
                      "USD 231/t (late Aug 2026). Rotterdam B100 around USD 1,387/t (late Jul 2026).",

    # Electricity, PLN
    "pln_i3_idr_per_kwh": 1114.74,   # medium industry / B-3 medium voltage, >200 kVA
    "pln_i4_idr_per_kwh": 996.74,    # large industry, high voltage, >30,000 kVA
    "pln_source": "[GOV] PLN non-subsidised tariff schedule; rates frozen through Q3 2026.",

    # Methanol
    "bio_methanol_usd_per_tonne": 950.0,
    "methanol_source": "[ASSUM] indicative; bio-methanol is thinly traded and site-specific.",
}

# ----------------------------------------------------------------------------------
# 7. GRID AND FUEL-SWITCHING PATHWAYS
# ----------------------------------------------------------------------------------
GRID = {
    "ef_tco2_per_mwh": 0.85,
    "ef_low": 0.70,
    "ef_high": 0.90,
    "source": "[ASSUM] Indonesian grid emission factors for the JAMALI and Sumatra systems are "
              "commonly quoted in the 0.75-0.90 tCO2/MWh range. NOT VERIFIED against a current "
              "MEMR/ESDM decree. Must be replaced with the official grid emission factor for the "
              "relevant system year before publication.",
}

ELECTRIC = {
    "motor_drive_efficiency": 0.92,     # [ASSUM] converter + motor + gearbox
    "onboard_distribution": 0.97,       # [ASSUM]
    "charging_efficiency": 0.93,        # [ASSUM] shore converter + battery round trip
    "battery_usable_dod": 0.80,
    "shore_connection_efficiency": 0.95,   # [ASSUM] shore transformer and cable losses         # [ASSUM]
    "battery_cost_usd_per_kwh_newbuild": 500.0,
    "battery_cost_usd_per_kwh_retrofit": 900.0,
    "battery_cost_source": "[LIT] Marine battery systems reported at USD 800-1,000/kWh for "
                           "retrofits and around USD 500/kWh for newbuilds (DNV, via "
                           "sustainable-ships.org, 2025). Cell prices have fallen further since; "
                           "treat as an upper bound.",
    "shore_charger_usd_per_mw": 900000.0,  # [ASSUM] high-power DC charging berth, installed
}

# Well-to-wake GHG saving of each pathway relative to the fossil baseline it displaces.
PATHWAYS = {
    "baseline":        {"label": "Baseline (as operated)",            "wtw_saving": 0.00},
    "b40":             {"label": "B40 drop-in biodiesel",             "wtw_saving": 0.24},
    "b100":            {"label": "B100 / HVO drop-in",                "wtw_saving": 0.80},
    "bio_methanol":    {"label": "Bio-methanol (engine conversion)",  "wtw_saving": 0.85},
    "shore_power":     {"label": "Shore power at berth and anchorage", "wtw_saving": None},
    "electric_grid":   {"label": "Battery-electric, PLN grid",        "wtw_saving": None},  # computed
    "electric_re":     {"label": "Battery-electric, dedicated RE",    "wtw_saving": 0.95},
}
FLEET = {
    "operating_days_per_year": 300,
    "steaming_hours_per_day": 8.0,
    "mean_sea_load": 0.35,
    "note": "[ASSUM] Activity is assumed, not observed. Obtaining AIS for the other ASDP "
            "routes is the single highest-value next data step.",
}

METHOD_SOURCES = {
    "primary": "Olmer, N., Comer, B., Roy, B., Mao, X., & Rutherford, D. (2017). Greenhouse "
               "gas emissions from global shipping, 2013-2015: Detailed methodology. ICCT. "
               "Auxiliary power by class and phase (App. C), boiler power (App. D), main "
               "and auxiliary engine emission factors (App. E, G), black carbon factors "
               "(App. F), low-load adjustment factors (App. I), draught adjustment factors "
               "(Table 13), hull fouling after Townsin (2000, 2003), weather factor.",
    "imo": "Third IMO GHG Study 2014 (Smith et al.) and Fourth IMO GHG Study 2020 (Faber "
           "et al.): activity-based bottom-up structure, SFOC load curve, low-load factors.",
    "cf": "IMO Resolution MEPC.281(70) Table 1: carbon conversion factors and heating values.",
    "gwp": "IPCC AR4 for CH4 and N2O; Bond et al. (2013) for black carbon.",
    "corbett": "Corbett, Wang & Winebrake (2009), Transp. Res. D 14(8): speed reduction "
               "abatement costs, USD 30-200 per tonne CO2 for the container fleet, used "
               "here as a reference point for judging the abatement costs reported below. "
               "Winebrake, Corbett, Wang, Farrell & Woods (2005), JAWMA 55(4): fleetwide "
               "emissions reduction optimisation for passenger ferries, the closest "
               "published analogue to this task.",
    "wb": "World Bank Pacific Observatory, Greenhouse Gas Emissions from Maritime Traffic: "
          "the Bank's own implementation of the same IMO method on AIS data.",
}

PATHWAY_SOURCE = (
    "[LIT/ASSUM] B40: 40% FAME by volume, biogenic CO2 counted zero tank-to-wake, and the "
    "bio fraction assigned a 60% well-to-wake saving, giving about 24% overall. B100/HVO: 80% "
    "well-to-wake saving, typical of waste-oil feedstocks under RED II style accounting. "
    "Bio-methanol: 85%. Electric-on-grid is computed from the grid emission factor, not assumed. "
    "Feedstock availability and certification are NOT modelled and are the binding constraint "
    "in practice."
)

# Note for the client on terminology.
TERMINOLOGY_NOTE = (
    "SAF (sustainable aviation fuel) is an aviation product and is not used in shipping. "
    "The marine equivalents modelled here are FAME biodiesel (B40, which Indonesia already "
    "mandates on land), HVO/B100 renewable diesel, and bio- or e-methanol."
)
