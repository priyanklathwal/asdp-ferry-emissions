"""
Merak-Bakauheni RoPax voyage energy and emissions model, v2.

Method follows the activity-based, phase-resolved approach of the Third and Fourth IMO GHG
Studies as implemented and documented by Olmer et al. (2017) for the ICCT, adapted to
port-to-port AIS event data rather than hourly positional tracks.

What changed from v1, and why
-----------------------------
1. Auxiliary power is now the IMO/ICCT published kW value for the ferry ro-pax class by
   size bin (105 kW under 2,000 GT, 710 kW above), not a guessed percentage of installed
   main engine power. Boilers are zero for this class, also per the published table.
2. CO2 comes from energy-based emission factors in g/kWh (ICCT Appendix E and G), not from
   an invented specific-fuel-consumption table multiplied by a carbon factor.
3. Low-load operation is handled by the IMO SFOC load curve, 0.455L^2 - 0.710L + 1.28, plus
   the published low-load adjustment factors for the non-CO2 pollutants. The arbitrary
   "minimum 15% of MCR" floor from v1 is gone.
4. Voyage time is split into steaming, manoeuvring and waiting. Main engines are off while
   waiting, which is the IMO/ICCT convention for the anchor phase. Waiting time is
   identified per vessel as the excess over that vessel's own 10th-percentile crossing
   time. This is what actually resolves the "slow steaming or queueing for a berth"
   ambiguity that dominated v1's uncertainty.
5. Hull fouling is computed from ship age via the Townsin roughness relation; the weather
   factor and the ro-pax draught adjustment factor are applied separately, all with
   published values, rather than rolled into one round number.
6. CH4, N2O and black carbon are estimated, so results are reported as CO2 and as
   CO2-equivalent on 20- and 100-year horizons. NOx, SOx and PM are estimated for the local
   air quality case, which matters on a corridor whose terminals sit inside two towns.

Run:  python src/run.py --workbook <path.xlsx>
"""

import argparse
import json
import os
import sys
from datetime import datetime, timezone

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import config as C          # noqa: E402
import factors as F         # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "outputs")
DOCS = os.path.join(ROOT, "docs")
POLLUTANTS = ["CO2", "NOx", "SOx", "PM", "CO", "CH4", "N2O", "BC"]


# ======================================================================================
# LOAD AND CLEAN
# ======================================================================================
def load_workbook(path):
    inv = pd.read_excel(path, sheet_name="ASDP list of vessels")
    moves = pd.concat([pd.read_excel(path, sheet_name="Merak to B"),
                       pd.read_excel(path, sheet_name="B to Merak")], ignore_index=True)
    moves = moves[moves["IMO"].notna()].copy()
    moves["IMO"] = moves["IMO"].astype(np.int64)
    for c in ["First Seen In Origin Port", "Last Seen In Origin Port",
              "First Seen In Dest. Port", "Last Seen In Dest. Port"]:
        moves[c] = pd.to_datetime(moves[c])
    return inv, moves


def clean_inventory(inv):
    df = pd.DataFrame({
        "imo": inv["IMO"].astype("Int64"),
        "name": inv["Ship Name"].astype(str).str.title(),
        "type": inv["List.Type"],
        "owner": inv["List.Corporate Owner"],
        "company": inv["List.Company"],
        "gt": pd.to_numeric(inv["List.GT"], errors="coerce"),
        "dwt": pd.to_numeric(inv["List.DWT"], errors="coerce"),
        "built": pd.to_numeric(inv["List.Built"], errors="coerce"),
        "status": inv["List.Status"],
        "speed_kn": pd.to_numeric(inv["List.Speed (knots)"], errors="coerce"),
        "beam_m": pd.to_numeric(inv["List.Beam Mld (m)"], errors="coerce"),
        "draft_m": pd.to_numeric(inv["List.Draft (m)"], errors="coerce"),
        "loa_m": pd.to_numeric(inv["List.LOA (m)"], errors="coerce"),
        "engine_fuel_raw": inv["List.Main Engine Fuel Type"],
        "power_type": inv["List.Power Type"],
    })
    df = df.dropna(subset=["imo"]).drop_duplicates(subset=["imo"], keep="first")
    df["imo"] = df["imo"].astype(np.int64)

    own = df["owner"].fillna("").str.upper() + " " + df["company"].fillna("").str.upper()
    df["is_asdp"] = own.str.contains("ASDP|INDONESIA FERRY", regex=True)

    df["engine_family"] = np.where(
        df["power_type"].fillna("").str.contains("2-Stroke"), "SSD", "MSD")

    fuel = df["engine_fuel_raw"].fillna("")
    df["fuel"] = np.select(
        [fuel.str.contains("IFO"), fuel.str.contains("MDO|MGO", regex=True)],
        ["residual", "distillate"],
        default=np.where(df["gt"].fillna(0) >= 2000, "residual", "distillate"))
    df["fuel_imputed"] = fuel.eq("")

    df["ship_class"] = df["type"].map(F.ship_class_of)
    df["age"] = C.REFERENCE_YEAR - df["built"]
    df["hff"] = df["age"].map(F.hull_fouling_factor)
    df["nox_tier"] = df["built"].map(F.nox_tier)
    df["rpm"] = np.where(df["engine_family"] == "SSD", C.ASSUMED_RPM["SSD"],
                         C.ASSUMED_RPM["MSD"])
    return df


def fill_unmatched_route_vessels(moves, ships):
    known = set(ships["imo"])
    seen = moves.groupby("IMO").agg(
        name=("Name", "first"),
        band=("Detailed Vessel Type", lambda s: s.mode().iat[0])).reset_index()
    missing = seen[~seen["IMO"].isin(known)]
    band_gt = {"Passenger Ferry <10,000 GT": 3500.0,
               "Passenger Ferry 10,000 - 29,999 GT": 15000.0,
               "Passenger Ferry 30,000+ GT": 32000.0}
    default_gt = float(ships["gt"].median())
    rows = []
    for _, r in missing.iterrows():
        gt = band_gt.get(r["band"], default_gt)
        rows.append({
            "imo": int(r["IMO"]), "name": str(r["name"]).title(), "type": "Ro-ro Ferry",
            "owner": None, "company": None, "gt": gt, "dwt": np.nan,
            "built": float(C.REFERENCE_YEAR - C.ASSUMED_AGE_UNMATCHED),
            "status": "In Service", "speed_kn": np.nan, "beam_m": np.nan,
            "draft_m": np.nan, "loa_m": np.nan, "engine_fuel_raw": None,
            "power_type": "Diesel 4-Stroke", "is_asdp": False, "engine_family": "MSD",
            "fuel": "residual" if gt >= 2000 else "distillate", "fuel_imputed": True,
            "ship_class": "ferry_ropax", "age": float(C.ASSUMED_AGE_UNMATCHED),
            "hff": F.hull_fouling_factor(C.ASSUMED_AGE_UNMATCHED), "nox_tier": "Tier0",
            "rpm": C.ASSUMED_RPM["MSD"], "in_inventory": False})
    return pd.DataFrame(rows)


# ======================================================================================
# POWER
# ======================================================================================
def estimate_power(df):
    p = C.POWER
    draft = df["draft_m"].copy()
    suspect = (draft.notna() & df["beam_m"].notna()
               & (draft > p["draft_over_beam_cap"] * df["beam_m"]))
    draft[suspect] = p["draft_over_beam_cap"] * df.loc[suspect, "beam_m"]

    lpp = df["loa_m"] * p["lpp_over_loa"]
    disp = lpp * df["beam_m"] * draft * p["block_coefficient"] * p["seawater_density"]
    has_dims = disp.notna() & (disp > 0)

    fit = has_dims & df["gt"].notna() & (df["gt"] > 0)
    cd = np.polyfit(np.log(df.loc[fit, "gt"]), np.log(disp[fit]), 1)
    disp_b, disp_a = cd[0], float(np.exp(cd[1]))
    disp_r2 = float(np.corrcoef(np.log(df.loc[fit, "gt"]), np.log(disp[fit]))[0, 1] ** 2)
    fill_d = (~has_dims) & df["gt"].notna()
    disp[fill_d] = disp_a * df.loc[fill_d, "gt"] ** disp_b
    df["displacement_t"] = disp

    speed = df["speed_kn"].fillna(df["speed_kn"].median())
    raw = (disp ** (2 / 3)) * (speed ** 3) / p["admiralty_coefficient"] \
        / p["service_power_fraction_of_mcr"]
    p_mcr = raw.clip(lower=p["kw_per_gt_floor"] * df["gt"],
                     upper=p["kw_per_gt_ceiling"] * df["gt"])
    df["p_mcr_kw"] = p_mcr.clip(lower=150, upper=40000)
    df["power_method"] = np.where(has_dims, "dimensions", "gt_regression")

    meta = {"n_from_dimensions": int(has_dims.sum()),
            "n_from_gt_regression": int(fill_d.sum()),
            "n_draft_capped": int(suspect.sum()),
            "n_mcr_bounded": int((raw != p_mcr).sum()),
            "displacement_form": f"displacement (t) = {disp_a:.4f} * GT^{disp_b:.3f}",
            "displacement_r2": disp_r2,
            "median_kw_per_gt": float((df["p_mcr_kw"] / df["gt"]).median())}
    return df, meta


def propulsion_kw(disp_t, speed_kn, hff, daf, weather):
    return (disp_t ** (2 / 3)) * (speed_kn ** 3) / C.POWER["admiralty_coefficient"] \
        * hff * daf * weather


# ======================================================================================
# EMISSIONS PER ENGINE BLOCK
# ======================================================================================
def _engine_emissions(kwh, load, engine_family, fuel, tier, rpm, sulphur_pct, is_aux):
    out = {}
    if is_aux:
        ef = F.AE_EF
        co2 = kwh * ef["CO2"][fuel]
        out["CO2"] = co2
        out["fuel_g"] = co2 / F.CF_TCO2_PER_T[fuel]
        for p in ("PM", "CO", "CH4", "N2O"):
            out[p] = kwh * ef[p][fuel]
        out["SOx"] = kwh * ef["SOx_at_2p5S"][fuel] * (sulphur_pct / 2.5)
        out["NOx"] = kwh * F.AE_NOX["Tier0"][fuel]
        out["BC"] = kwh * ef["BC"][fuel]
        return out

    ef = F.ME_EF[engine_family]
    co2 = kwh * ef["CO2"][fuel] * F.sfoc_load_factor(load)
    out["CO2"] = co2
    fuel_g = co2 / F.CF_TCO2_PER_T[fuel]
    out["fuel_g"] = fuel_g
    for p in ("PM", "CO", "CH4", "N2O"):
        out[p] = kwh * ef[p][fuel] * F.llaf(load, p)
    out["SOx"] = kwh * ef["SOx_at_2p5S"][fuel] * (sulphur_pct / 2.5)
    nox_ef = (F.ME_NOX["SSD"][tier][fuel] if engine_family == "SSD"
              else F.me_nox_msd(tier, rpm, fuel))
    out["NOx"] = kwh * nox_ef * F.llaf(load, "NOx")
    out["BC"] = (fuel_g / 1000.0) * F.bc_ef(load, engine_family, fuel)
    return out


# ======================================================================================
# VOYAGE MODEL
# ======================================================================================
def build_voyages(moves, ships, distance_nm=None, waiting_engines_off=True):
    o = C.OPS
    d_nm = distance_nm if distance_nm is not None else C.ROUTE["distance_nm"]

    v = moves.copy()
    v["hours"] = (v["First Seen In Dest. Port"] - v["Last Seen In Origin Port"]
                  ).dt.total_seconds() / 3600.0
    v = v[v["hours"].notna()].copy()
    v["hours"] = v["hours"].clip(*o["voyage_hours_clip"])

    s = ships.set_index("imo")
    for col in ["p_mcr_kw", "displacement_t", "gt", "engine_family", "fuel", "name",
                "is_asdp", "ship_class", "hff", "nox_tier", "rpm"]:
        v[col] = v["IMO"].map(s[col])
    v = v[v["p_mcr_kw"].notna() & v["displacement_t"].notna()].copy()

    free = v.groupby("IMO")["hours"].quantile(o["free_running_percentile"])
    v["t_free"] = v["IMO"].map(free).clip(*o["t_free_clip"])
    v["t_manoeuvre"] = np.minimum(o["manoeuvre_hours_per_voyage"], 0.4 * v["t_free"])
    v["t_steam"] = (v["t_free"] - v["t_manoeuvre"]).clip(lower=0.4)
    v["t_wait"] = (v["hours"] - v["t_free"]).clip(lower=0.0)
    v["v_steam_kn"] = d_nm / v["t_steam"]

    daf, w = F.DAF_FERRY_ROPAX, F.WEATHER_FACTOR_COASTAL
    v["p_steam_kw"] = np.minimum(
        propulsion_kw(v["displacement_t"], v["v_steam_kn"], v["hff"], daf, w),
        v["p_mcr_kw"] * o["max_load"])
    v["p_manoeuvre_kw"] = np.clip(
        propulsion_kw(v["displacement_t"], o["manoeuvre_speed_kn"], v["hff"], daf, w),
        v["p_mcr_kw"] * o["manoeuvre_load_floor"], v["p_mcr_kw"] * 0.40)
    v["load"] = (v["p_steam_kw"] / v["p_mcr_kw"]).clip(0.02, o["max_load"])
    v["manoeuvre_load"] = (v["p_manoeuvre_kw"] / v["p_mcr_kw"]).clip(0.02, 0.40)

    v["e_me_kwh"] = v["p_steam_kw"] * v["t_steam"] + v["p_manoeuvre_kw"] * v["t_manoeuvre"]
    if not waiting_engines_off:
        v["e_me_kwh"] = v["e_me_kwh"] + v["p_manoeuvre_kw"] * v["t_wait"]

    aux_c = np.array([F.aux_kw(sc, gt, "cruise") for sc, gt in zip(v["ship_class"], v["gt"])])
    aux_a = np.array([F.aux_kw(sc, gt, "anchor") for sc, gt in zip(v["ship_class"], v["gt"])])
    boil = np.array([F.boiler_kw(sc, "cruise") for sc in v["ship_class"]])
    v["aux_kw"] = aux_c
    v["e_ae_kwh"] = aux_c * (v["t_steam"] + v["t_manoeuvre"]) + aux_a * v["t_wait"]
    v["e_bo_kwh"] = boil * (v["t_steam"] + v["t_manoeuvre"])

    recs = []
    for r in v.itertuples(index=False):
        sul = C.SULPHUR_PCT[r.fuel]
        wait_kwh = r.p_manoeuvre_kw * r.t_wait if not waiting_engines_off else 0.0
        me1 = _engine_emissions(r.p_steam_kw * r.t_steam, r.load, r.engine_family, r.fuel,
                                r.nox_tier, r.rpm, sul, False)
        me2 = _engine_emissions(r.p_manoeuvre_kw * r.t_manoeuvre + wait_kwh,
                                r.manoeuvre_load, r.engine_family, r.fuel, r.nox_tier,
                                r.rpm, sul, False)
        ae = _engine_emissions(r.e_ae_kwh + r.e_bo_kwh, 0.75, r.engine_family, r.fuel,
                               r.nox_tier, r.rpm, sul, True)
        rec = {}
        for k in POLLUTANTS + ["fuel_g"]:
            rec[k + "_me"] = me1.get(k, 0.0) + me2.get(k, 0.0)
            rec[k + "_ae"] = ae.get(k, 0.0)
            rec[k] = rec[k + "_me"] + rec[k + "_ae"]
        recs.append(rec)
    v = pd.concat([v, pd.DataFrame(recs, index=v.index)], axis=1)

    v["fuel_t"] = v["fuel_g"] / 1e6
    v["co2_t"] = v["CO2"] / 1e6
    v["fuel_energy_mwh"] = v["fuel_t"] * 1000 * v["fuel"].map(F.LHV_MJ_PER_KG) / 3600.0
    v["shaft_energy_mwh"] = (v["e_me_kwh"] + v["e_ae_kwh"] + v["e_bo_kwh"]) / 1000.0
    v["propulsion_mwh"] = v["e_me_kwh"] / 1000.0
    for h in (20, 100):
        v[f"co2e{h}_t"] = sum(v[p] * F.GWP[h][p] for p in ("CO2", "CH4", "N2O", "BC")) / 1e6
    return v


def build_berth(moves, ships):
    o = C.OPS
    m = moves.sort_values(["IMO", "Last Seen In Origin Port"]).copy()
    m["next_dep"] = m.groupby("IMO")["Last Seen In Origin Port"].shift(-1)
    m["berth_h"] = (m["next_dep"] - m["Last Seen In Dest. Port"]).dt.total_seconds() / 3600.0
    m = m[m["berth_h"].notna() & (m["berth_h"] > 0)].copy()
    m["berth_h"] = m["berth_h"].clip(upper=o["berth_hours_cap"])

    s = ships.set_index("imo")
    for col in ["p_mcr_kw", "fuel", "name", "is_asdp", "ship_class", "gt",
                "engine_family", "nox_tier", "rpm"]:
        m[col] = m["IMO"].map(s[col])
    m = m[m["p_mcr_kw"].notna()].copy()

    aux = np.array([F.aux_kw(sc, gt, "berth") for sc, gt in zip(m["ship_class"], m["gt"])])
    boil = np.array([F.boiler_kw(sc, "berth") for sc in m["ship_class"]])
    m["e_ae_kwh"] = aux * m["berth_h"]
    m["e_bo_kwh"] = boil * m["berth_h"]

    recs = []
    for r in m.itertuples(index=False):
        ae = _engine_emissions(r.e_ae_kwh + r.e_bo_kwh, 0.75, r.engine_family, r.fuel,
                               r.nox_tier, r.rpm, C.SULPHUR_PCT[r.fuel], True)
        recs.append({k: ae.get(k, 0.0) for k in POLLUTANTS + ["fuel_g"]})
    m = pd.concat([m, pd.DataFrame(recs, index=m.index)], axis=1)

    m["fuel_t"] = m["fuel_g"] / 1e6
    m["co2_t"] = m["CO2"] / 1e6
    m["fuel_energy_mwh"] = m["fuel_t"] * 1000 * m["fuel"].map(F.LHV_MJ_PER_KG) / 3600.0
    m["shaft_energy_mwh"] = (m["e_ae_kwh"] + m["e_bo_kwh"]) / 1000.0
    m["propulsion_mwh"] = 0.0
    for h in (20, 100):
        m[f"co2e{h}_t"] = sum(m[p] * F.GWP[h][p] for p in ("CO2", "CH4", "N2O", "BC")) / 1e6
    return m


# ======================================================================================
# SCENARIOS
# ======================================================================================
def scenario_table(tot, prices, grid_ef):
    e = C.ELECTRIC
    rows = []
    fuel_t, fuel_mwh = tot["fuel_t"], tot["fuel_energy_mwh"]
    shaft_mwh, co2, co2e100 = tot["shaft_energy_mwh"], tot["co2_t"], tot["co2e100_t"]

    p_res = (prices["mfo_hs_idr_per_litre"] / C.DENSITY_KG_PER_L["HFO"]
             / C.FX_IDR_PER_USD * 1000)
    p_dis = (prices["b40_hsd_idr_per_litre"] / C.DENSITY_KG_PER_L["MDO"]
             / C.FX_IDR_PER_USD * 1000)
    p_blend = tot["residual_share"] * p_res + (1 - tot["residual_share"]) * p_dis
    base_cost = fuel_t * p_blend

    shore_mwh = shaft_mwh / (e["motor_drive_efficiency"] * e["onboard_distribution"]
                             * e["charging_efficiency"])
    elec_cost = shore_mwh * 1000 * (prices["pln_i3_idr_per_kwh"] / C.FX_IDR_PER_USD)
    meoh_t = fuel_mwh * 3600 / 19.9 / 1000

    def add(key, co2_out, co2e_out, energy, cost, note, local_removed=0.0):
        rows.append({"pathway": key, "label": C.PATHWAYS[key]["label"],
                     "co2_t": co2_out, "co2_saved_t": co2 - co2_out,
                     "co2_saved_pct": (co2 - co2_out) / co2 * 100,
                     "co2e100_t": co2e_out, "co2e100_saved_t": co2e100 - co2e_out,
                     "co2e100_saved_pct": (co2e100 - co2e_out) / co2e100 * 100,
                     "energy_in_mwh": energy,
                     "energy_saved_pct": (fuel_mwh - energy) / fuel_mwh * 100,
                     "annual_cost_usd": cost, "cost_delta_usd": cost - base_cost,
                     "local_pollutant_removed_pct": local_removed, "note": note})

    add("baseline", co2, co2e100, fuel_mwh, base_cost,
        "Fuel burn as observed, priced at Indonesian domestic industrial rates.")
    add("b40", co2 * 0.76, co2e100 * 0.76, fuel_mwh, fuel_t * p_dis,
        "Drop-in, no vessel modification. Already the mandated blend on land.")
    add("b100", co2 * 0.20, co2e100 * 0.22, fuel_mwh, fuel_t * prices["b100_usd_per_tonne"],
        "Drop-in after fuel-system checks. Near-zero sulphur and lower black carbon.",
        local_removed=40.0)
    add("bio_methanol", co2 * 0.15, co2e100 * 0.13, fuel_mwh,
        meoh_t * prices["bio_methanol_usd_per_tonne"],
        "Engine conversion or newbuild plus bunkering at both terminals.", local_removed=95.0)
    # Shore power / cold ironing. Only the stationary block is displaced; the ship keeps
    # its engines for the crossing. No battery, no repowering, no new vessel.
    sp_mwh = tot["stationary_mwh"] / e["shore_connection_efficiency"]
    sp_share = tot["stationary_mwh"] / shaft_mwh
    sp_co2 = co2 * (1 - sp_share * tot["aux_fuel_fraction_of_co2"]) + sp_mwh * grid_ef
    sp_co2e = co2e100 * (1 - sp_share * tot["aux_fuel_fraction_of_co2"]) + sp_mwh * grid_ef
    sp_cost = (base_cost * (1 - sp_share * tot["aux_fuel_fraction_of_co2"])
               + sp_mwh * 1000 * (prices["pln_i3_idr_per_kwh"] / C.FX_IDR_PER_USD))
    add("shore_power", sp_co2, sp_co2e,
        fuel_mwh * (1 - sp_share * tot["aux_fuel_fraction_of_co2"]) + sp_mwh, sp_cost,
        "Cold ironing at both terminals plus a connection for vessels queueing offshore. "
        "Displaces only the stationary hotel load, but that is the single largest block of "
        "energy on this corridor and it needs no change to the ships' propulsion.",
        local_removed=float(sp_share * 100))

    add("electric_grid", shore_mwh * grid_ef, shore_mwh * grid_ef, shore_mwh, elec_cost,
        "Shore energy at the industrial tariff. Ship-side CO2 follows the grid; all "
        "ship-side NOx, SOx, PM and black carbon go to zero at the two terminals.",
        local_removed=100.0)
    add("electric_re", shore_mwh * grid_ef * 0.05, shore_mwh * grid_ef * 0.05, shore_mwh,
        elec_cost, "Same energy from dedicated renewables plus storage at the terminals.",
        local_removed=100.0)

    df = pd.DataFrame(rows)
    df["abatement_cost_usd_per_tco2"] = np.where(
        df["co2_saved_t"] > 0, df["cost_delta_usd"] / df["co2_saved_t"], np.nan)
    df["abatement_cost_usd_per_tco2e"] = np.where(
        df["co2e100_saved_t"] > 0, df["cost_delta_usd"] / df["co2e100_saved_t"], np.nan)
    df["baseline_cost_usd"] = base_cost
    df["blended_fuel_price_usd_per_t"] = p_blend
    return df, shore_mwh


# ======================================================================================
# SANITY CHECKS
# ======================================================================================
def sanity_checks(voy, berth, ships, tot):
    checks = []

    def chk(name, value, lo, hi, unit, basis):
        checks.append({"check": name, "value": float(value), "expected_low": lo,
                       "expected_high": hi, "unit": unit,
                       "pass": bool(lo <= value <= hi), "basis": basis})

    chk("Implied main engine SFC", voy["fuel_g_me"].sum() / voy["e_me_kwh"].sum(),
        190, 260, "g fuel/kWh",
        "IMO baseline SFC for medium-speed engines is 205-215 g/kWh, rising about 18% at "
        "the low loads seen on this crossing.")

    chk("Implied fuel-to-shaft efficiency",
        tot["shaft_energy_mwh"] / tot["fuel_energy_mwh"] * 100, 33, 45, "%",
        "Marine four-stroke diesels convert 40-45% of fuel energy to shaft work at design "
        "load, less at part load.")

    chk("Median installed power", float((ships["p_mcr_kw"] / ships["gt"]).median()),
        0.35, 1.10, "kW/GT",
        "Ro-pax ferries typically carry 0.4-1.0 kW per GT depending on service speed.")

    chk("Median steaming speed", float(voy["v_steam_kn"].median()), 7.0, 14.0, "knots",
        "Published Merak-Bakauheni schedules give 15 nm in 90-120 minutes: 7.5-10 knots "
        "on the regular berths, up to 15 knots on the executive service.")

    chk("Fuel per crossing", float((voy["fuel_t"] / (voy["gt"] / 1000)).median()),
        0.03, 0.20, "t fuel per 1,000 GT",
        "A 5,000 GT ferry on a 2-3 hour crossing would be expected to burn roughly "
        "0.2-1.0 t, i.e. 0.04-0.20 t per 1,000 GT.")

    chk("CO2 intensity of transport supply",
        voy["CO2"].sum() / (voy["gt"] * C.ROUTE["distance_nm"]).sum(), 3.0, 30.0,
        "g CO2 / GT-nm",
        "Ro-pax is among the least efficient classes per GT-nm: it carries volume rather "
        "than mass on short high-frequency services. A 15 nm crossing sits high in the "
        "range ICCT reports for this class.")

    aux_e = voy["e_ae_kwh"].sum() + berth["e_ae_kwh"].sum()
    chk("Auxiliary share of shaft energy",
        aux_e / (voy["e_me_kwh"].sum() + aux_e) * 100, 20, 70, "%",
        "For ro-pax on very short crossings with long turnarounds, hotel and vehicle-deck "
        "ventilation load is a large share of total energy; the Fourth IMO GHG Study finds "
        "auxiliary demand comparable to propulsion for some passenger classes.")

    chk("Black carbon share of CO2e-100",
        voy["BC"].sum() * F.GWP[100]["BC"] / (voy["co2e100_t"].sum() * 1e6) * 100,
        2, 30, "%",
        "Black carbon is a meaningful but not dominant share of 100-year warming from "
        "residual-fuel four-stroke engines at low load. It is larger on a 20-year horizon.")

    chk("Share of port-to-port time spent waiting",
        voy["t_wait"].sum() / voy["hours"].sum() * 100, 5, 55, "%",
        "The corridor has roughly 28 berth slots against about 70 available ships, and "
        "vessels are reported queueing at anchor for hours at peak.")

    return checks


# ======================================================================================
# MAIN
# ======================================================================================
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workbook", required=True)
    args = ap.parse_args()
    os.makedirs(OUT, exist_ok=True)
    os.makedirs(DOCS, exist_ok=True)

    inv, moves = load_workbook(args.workbook)
    ships = clean_inventory(inv)
    ships["in_inventory"] = True
    ships_all = pd.concat([ships, fill_unmatched_route_vessels(moves, ships)],
                          ignore_index=True)
    ships_all, pmeta = estimate_power(ships_all)

    voy = build_voyages(moves, ships_all)
    berth = build_berth(moves, ships_all)

    span_days = (voy["Last Seen In Origin Port"].max()
                 - voy["Last Seen In Origin Port"].min()).total_seconds() / 86400.0
    scale = 365.0 / span_days

    def agg(col):
        return float(voy[col].sum() + berth[col].sum())

    tot = {"fuel_t": agg("fuel_t") * scale, "co2_t": agg("co2_t") * scale,
           "co2e20_t": agg("co2e20_t") * scale, "co2e100_t": agg("co2e100_t") * scale,
           "fuel_energy_mwh": agg("fuel_energy_mwh") * scale,
           "shaft_energy_mwh": agg("shaft_energy_mwh") * scale,
           "propulsion_mwh": agg("propulsion_mwh") * scale}
    for p in POLLUTANTS:
        tot[p.lower() + "_t"] = agg(p) * scale / 1e6
    res = float(voy.loc[voy["fuel"] == "residual", "fuel_t"].sum()
                + berth.loc[berth["fuel"] == "residual", "fuel_t"].sum())
    tot["residual_share"] = res / agg("fuel_t")
    # Energy that a ship draws while stationary: alongside, plus queueing at anchor with
    # main engines already off. This is the block that shore power and a charging buoy or
    # cold-ironing berth can displace without touching the propulsion system at all.
    berth_kwh = float(berth["e_ae_kwh"].sum() + berth["e_bo_kwh"].sum())
    wait_kwh = float((voy["aux_kw"] * voy["t_wait"]).sum())
    tot["stationary_mwh"] = (berth_kwh + wait_kwh) / 1000.0 * scale
    tot["berth_mwh"] = berth_kwh / 1000.0 * scale
    tot["stationary_share_pct"] = tot["stationary_mwh"] / tot["shaft_energy_mwh"] * 100

    tot["aux_fuel_fraction_of_co2"] = (
        float(voy["CO2_ae"].sum() + berth["CO2"].sum())
        / float(voy["CO2"].sum() + berth["CO2"].sum())) / (
        (float(voy["e_ae_kwh"].sum() + berth["e_ae_kwh"].sum()))
        / float(voy["e_me_kwh"].sum() + voy["e_ae_kwh"].sum() + berth["e_ae_kwh"].sum()))
    scen, shore_mwh = scenario_table(tot, C.PRICES, C.GRID["ef_tco2_per_mwh"])
    checks = sanity_checks(voy, berth, ships_all, tot)

    per = voy.groupby(["IMO", "name", "is_asdp"]).agg(
        voyages=("IMO", "size"), hours=("hours", "sum"), wait_h=("t_wait", "sum"),
        fuel_t=("fuel_t", "sum"), co2_t=("co2_t", "sum"), co2e100_t=("co2e100_t", "sum"),
        shaft_mwh=("shaft_energy_mwh", "sum"), propulsion_mwh=("propulsion_mwh", "sum"),
        mean_load=("load", "mean"), v_steam=("v_steam_kn", "median")).reset_index()
    per = per.merge(ships_all[["imo", "gt", "built", "p_mcr_kw", "aux_kw", "power_method",
                               "fuel", "in_inventory"]]
                    if "aux_kw" in ships_all.columns else
                    ships_all[["imo", "gt", "built", "p_mcr_kw", "power_method", "fuel",
                               "in_inventory"]],
                    left_on="IMO", right_on="imo", how="left").drop(columns=["imo"])
    per["co2_per_voyage_t"] = per["co2_t"] / per["voyages"]
    per = per.sort_values("co2_t", ascending=False)

    grid_sens = [{"ef": ef, "co2_t": shore_mwh * ef,
                  "saving_pct": (tot["co2_t"] - shore_mwh * ef) / tot["co2_t"] * 100}
                 for ef in [0.0, 0.2, 0.4, 0.5, 0.6, 0.7, 0.8, 0.85, 0.9, 1.0]]
    dist_sens = []
    for d in [15.0, 16.0, 17.0, 18.0, 19.0]:
        vv = build_voyages(moves, ships_all, distance_nm=d)
        dist_sens.append({"distance_nm": d,
                          "co2_t_annual": (float(vv["co2_t"].sum())
                                           + float(berth["co2_t"].sum())) * scale})
    vv_on = build_voyages(moves, ships_all, waiting_engines_off=False)
    waiting_sens = [
        {"case": "Main engines off while waiting (IMO anchor convention)",
         "co2_t_annual": tot["co2_t"]},
        {"case": "Main engines idling at manoeuvring load while waiting",
         "co2_t_annual": (float(vv_on["co2_t"].sum())
                          + float(berth["co2_t"].sum())) * scale}]

    # ---- narrative visuals: real observed activity, not schematics ----
    busiest = int(voy.groupby("IMO").size().idxmax())
    tl = voy[voy["IMO"] == busiest].sort_values("Last Seen In Origin Port").copy()
    tl_name = str(tl["name"].iat[0])
    t0 = tl["Last Seen In Origin Port"].min().normalize()
    win = tl[(tl["Last Seen In Origin Port"] >= t0)
             & (tl["Last Seen In Origin Port"] < t0 + pd.Timedelta(days=7))]
    timeline = []
    for _, r in win.iterrows():
        h0 = (r["Last Seen In Origin Port"] - t0).total_seconds() / 3600.0
        timeline.append({"start_h": float(h0), "manoeuvre": float(r["t_manoeuvre"]),
                         "steam": float(r["t_steam"]), "wait": float(r["t_wait"]),
                         "dir": str(r["Origin Port"])[:5], "load": float(r["load"])})
    activity = {"vessel": tl_name, "imo": busiest, "day0": str(t0.date()),
                "days": 7, "voyages": timeline,
                "note": "Every crossing this vessel made in one week, drawn to scale on a "
                        "168-hour axis. The gaps are time alongside."}

    # fleet: one mark per vessel, size by GT, position by age and estimated power
    fleet_marks = [{"gt": float(r["gt"]), "age": float(r["age"]),
                    "kw": float(r["p_mcr_kw"]), "asdp": bool(r["is_asdp"])}
                   for _, r in ships_all[ships_all["in_inventory"]
                                         & ships_all["gt"].notna()
                                         & ships_all["age"].notna()].iterrows()]

    voy["month"] = voy["Last Seen In Origin Port"].dt.to_period("M").astype(str)
    monthly = voy.groupby("month").agg(voyages=("IMO", "size"), co2_t=("co2_t", "sum"),
                                       fuel_t=("fuel_t", "sum")).reset_index()

    sizing = []
    for _, r in per.head(12).iterrows():
        e_voy = r["shaft_mwh"] / r["voyages"]
        pack = e_voy / (C.ELECTRIC["motor_drive_efficiency"]
                        * C.ELECTRIC["onboard_distribution"]) \
            / C.ELECTRIC["battery_usable_dod"]
        sizing.append({"name": r["name"], "gt": r["gt"], "p_mcr_kw": r["p_mcr_kw"],
                       "voyages_period": int(r["voyages"]),
                       "energy_per_voyage_mwh": e_voy,
                       "battery_pack_mwh_2_crossings": pack * 2,
                       "capex_newbuild_musd": pack * 2 * 1000
                       * C.ELECTRIC["battery_cost_usd_per_kwh_newbuild"] / 1e6,
                       "capex_retrofit_musd": pack * 2 * 1000
                       * C.ELECTRIC["battery_cost_usd_per_kwh_retrofit"] / 1e6})

    act = ships_all[(ships_all["status"].fillna("") == "In Service")
                    & (ships_all["in_inventory"])].copy()
    hrs = C.FLEET["operating_days_per_year"] * C.FLEET["steaming_hours_per_day"]
    idle = C.FLEET["operating_days_per_year"] * (24 - C.FLEET["steaming_hours_per_day"])
    act["aux_kw"] = [F.aux_kw(sc, gt, "cruise")
                     for sc, gt in zip(act["ship_class"], act["gt"])]
    e_me = act["p_mcr_kw"] * C.FLEET["mean_sea_load"] * hrs
    e_ae = act["aux_kw"] * (hrs + idle)
    me_ef = act.apply(lambda r: F.ME_EF[r["engine_family"]]["CO2"][r["fuel"]], axis=1) \
        * F.sfoc_load_factor(C.FLEET["mean_sea_load"])
    ae_ef = act["fuel"].map(lambda f: F.AE_EF["CO2"][f])
    act["co2_t_yr"] = (e_me * me_ef + e_ae * ae_ef) / 1e6
    act["fuel_t_yr"] = act["co2_t_yr"] / act["fuel"].map(F.CF_TCO2_PER_T)
    fleet = {"n_vessels_in_service": int(len(act)),
             "n_asdp_flagged": int(act["is_asdp"].sum()),
             "installed_mcr_mw": float(act["p_mcr_kw"].sum() / 1000),
             "fuel_t_yr": float(act["fuel_t_yr"].sum()),
             "co2_t_yr": float(act["co2_t_yr"].sum()), "assumptions": C.FLEET}
    act[["imo", "name", "p_mcr_kw", "fuel_t_yr", "co2_t_yr"]].sort_values(
        "co2_t_yr", ascending=False).to_csv(
        os.path.join(OUT, "fleet_indicative_annual.csv"), index=False)

    age = ships[ships["built"].notna()].copy()
    bands = pd.cut(age["age"], [-1, 10, 20, 30, 40, 200],
                   labels=["0-10", "11-20", "21-30", "31-40", "40+"])
    age_profile = age.groupby(bands, observed=True).agg(
        vessels=("imo", "size"), gt=("gt", "sum")).reset_index()
    age_profile.columns = ["age_band", "vessels", "total_gt"]

    # The full register dump is deliberately NOT written to outputs/. It reproduces the
    # licensed commercial ship register (owner, GT, DWT, dimensions, build year, engine
    # type) almost verbatim, which must not be redistributed. Derived results only.
    _vd = ships_all[["imo", "name", "gt", "age", "p_mcr_kw", "power_method", "fuel",
                     "in_inventory"]].copy()
    _vd["p_mcr_kw"] = (_vd["p_mcr_kw"] / 50).round() * 50      # estimated, not measured
    _vd.round({"gt": 0, "age": 0}).to_csv(
        os.path.join(OUT, "vessels_derived.csv"), index=False)
    per.round(2).to_csv(os.path.join(OUT, "per_vessel_route_totals.csv"), index=False)
    scen.round(2).to_csv(os.path.join(OUT, "scenarios_annual.csv"), index=False)
    monthly.round(1).to_csv(os.path.join(OUT, "monthly_profile.csv"), index=False)
    pd.DataFrame(checks).round(3).to_csv(os.path.join(OUT, "sanity_checks.csv"), index=False)

    payload = {
        "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "route": C.ROUTE["name"], "method_version": "v2, ICCT/IMO phase-resolved",
        "window": {"start": str(voy["Last Seen In Origin Port"].min().date()),
                   "end": str(voy["Last Seen In Origin Port"].max().date()),
                   "span_days": round(span_days, 1),
                   "annualisation_factor": round(scale, 4)},
        "coverage": {"inventory_vessels": int(len(ships)),
                     "inventory_asdp_flagged": int(ships["is_asdp"].sum()),
                     "route_vessels": int(voy["IMO"].nunique()),
                     "route_vessels_in_inventory": int(per["in_inventory"].sum()),
                     "voyages_observed": int(len(voy)),
                     "voyages_by_asdp_flagged": int(voy["is_asdp"].sum())},
        "power_model": pmeta, "totals_annual": tot,
        "energy_split": {"propulsion_mwh": tot["propulsion_mwh"],
                         "auxiliary_mwh": tot["shaft_energy_mwh"] - tot["propulsion_mwh"],
                         "auxiliary_share_pct":
                         (tot["shaft_energy_mwh"] - tot["propulsion_mwh"])
                         / tot["shaft_energy_mwh"] * 100},
        "voyage_stats": {"median_hours": float(voy["hours"].median()),
                         "median_wait_hours": float(voy["t_wait"].median()),
                         "median_steam_speed_kn": float(voy["v_steam_kn"].median()),
                         "median_load": float(voy["load"].median()),
                         "median_co2_per_voyage_t": float(voy["co2_t"].median()),
                         "berth_hours_median": float(berth["berth_h"].median()),
                         "wait_share_pct": float(voy["t_wait"].sum()
                                                 / voy["hours"].sum() * 100)},
        "scenarios": scen.replace({np.nan: None}).to_dict(orient="records"),
        "per_vessel": per.head(30).replace({np.nan: None}).to_dict(orient="records"),
        "monthly": monthly.to_dict(orient="records"),
        "grid_sensitivity": grid_sens,
        "breakeven_grid_ef_tco2_per_mwh": tot["co2_t"] / shore_mwh,
        "breakeven_grid_ef_co2e100": tot["co2e100_t"] / shore_mwh,
        "breakeven_grid_ef_co2e20": tot["co2e20_t"] / shore_mwh,
        "shore_energy_mwh_annual": shore_mwh,
        "distance_sensitivity": dist_sens, "waiting_sensitivity": waiting_sens,
        "battery_sizing": sizing, "fleet_indicative": fleet,
        "activity_week": activity, "fleet_marks": fleet_marks,
        "phase_geometry": {
            "manoeuvre_h": float(voy["t_manoeuvre"].median()),
            "steam_h": float(voy["t_steam"].median()),
            "wait_h": float(voy["t_wait"].median()),
            "berth_h": float(berth["berth_h"].median()),
            "wait_p75_h": float(voy["t_wait"].quantile(0.75)),
            "wait_p95_h": float(voy["t_wait"].quantile(0.95)),
            "aux_kw_median": float(voy["aux_kw"].median()),
            "steam_kw_median": float(voy["p_steam_kw"].median())},
        "age_profile": age_profile.to_dict(orient="records"),
        "sanity_checks": checks,
        "assumptions": {"me_ef": F.ME_EF, "ae_ef": F.AE_EF,
                        "aux_kw_ropax": {"under_2000_GT": 105, "over_2000_GT": 710},
                        "gwp": F.GWP, "cf": F.CF_TCO2_PER_T, "lhv": F.LHV_MJ_PER_KG,
                        "sulphur_pct": C.SULPHUR_PCT,
                        "weather_factor": F.WEATHER_FACTOR_COASTAL,
                        "daf": F.DAF_FERRY_ROPAX,
                        "hull_fouling_range": [F.hull_fouling_factor(1),
                                               F.hull_fouling_factor(40)],
                        "ops": {k: str(v) for k, v in C.OPS.items()},
                        "power": {k: str(v) for k, v in C.POWER.items()},
                        "prices": C.PRICES, "fx": C.FX_IDR_PER_USD,
                        "fx_source": C.FX_SOURCE, "grid": C.GRID, "electric": C.ELECTRIC,
                        "pathway_source": C.PATHWAY_SOURCE,
                        "terminology": C.TERMINOLOGY_NOTE, "route_distance": C.ROUTE,
                        "method_sources": C.METHOD_SOURCES}}
    _vp = voy.groupby("IMO").agg(name=("name", "first"), crossings=("IMO", "size")) \
        .reset_index().sort_values("crossings", ascending=False)
    payload["vessel_picker"] = [{"imo": int(r["IMO"]), "name": str(r["name"]),
                                 "crossings": int(r["crossings"])} for _, r in _vp.iterrows()]
    _dp = os.path.join(OUT, "dataset_profile.json")
    if os.path.exists(_dp):
        payload["dataset"] = json.load(open(_dp))
    for path in (os.path.join(DOCS, "data.json"), os.path.join(OUT, "dashboard_data.json")):
        with open(path, "w") as f:
            json.dump(payload, f, indent=1, default=float)

    print(f"window {payload['window']['start']} -> {payload['window']['end']} "
          f"({span_days:.0f} d), x{scale:.2f}")
    print(f"power: {pmeta['displacement_form']} R2={pmeta['displacement_r2']:.3f} "
          f"median {pmeta['median_kw_per_gt']:.2f} kW/GT")
    print(f"voyages {len(voy):,}  vessels {voy['IMO'].nunique()}  "
          f"steam {voy['v_steam_kn'].median():.1f} kn  load {voy['load'].median():.2f}  "
          f"wait {payload['voyage_stats']['wait_share_pct']:.0f}%")
    print(f"ANNUAL fuel {tot['fuel_t']:,.0f} t | CO2 {tot['co2_t']:,.0f} t | "
          f"CO2e100 {tot['co2e100_t']:,.0f} t | CO2e20 {tot['co2e20_t']:,.0f} t")
    print(f"       NOx {tot['nox_t']:,.0f} | SOx {tot['sox_t']:,.0f} | "
          f"PM {tot['pm_t']:,.0f} | BC {tot['bc_t']:,.1f} t")
    print(f"       fuel energy {tot['fuel_energy_mwh']/1000:,.0f} GWh | shaft "
          f"{tot['shaft_energy_mwh']/1000:,.0f} GWh "
          f"(aux {payload['energy_split']['auxiliary_share_pct']:.0f}%) | shore "
          f"{shore_mwh/1000:,.0f} GWh")
    print(f"       breakeven grid EF {payload['breakeven_grid_ef_tco2_per_mwh']:.3f} "
          f"tCO2/MWh")
    print("\nSANITY CHECKS")
    for c in checks:
        print(f"  [{'ok  ' if c['pass'] else 'FLAG'}] {c['check']:<42} "
              f"{c['value']:>8.2f} {c['unit']:<26} expected "
              f"{c['expected_low']}-{c['expected_high']}")
    print()
    print(scen[["label", "co2_t", "co2_saved_pct", "annual_cost_usd", "cost_delta_usd",
                "abatement_cost_usd_per_tco2e"]].to_string(index=False))
    print("\nwaiting sensitivity:",
          [(w["case"][:40], round(w["co2_t_annual"])) for w in waiting_sens])


if __name__ == "__main__":
    main()
