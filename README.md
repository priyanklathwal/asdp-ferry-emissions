# Merak-Bakauheni RoPax energy and emissions

Screening analysis of voyage energy use, emissions and fuel-switching options for the roll-on
roll-off passenger fleet crossing the Sunda Strait, built from a vessel register and six and a
half months of AIS port-to-port movements.

Method follows the activity-based, phase-resolved approach of the Third and Fourth IMO GHG
Studies, using the parameter tables as published by Olmer et al. (2017) for the ICCT. See
[`docs/METHODOLOGY.md`](docs/METHODOLOGY.md) and [`docs/SOURCES.md`](docs/SOURCES.md).

**Status: v2, for internal discussion.** All nine sanity checks pass. Installed engine power is
still estimated rather than observed, and that remains the largest error bar.

Dashboard: `docs/index.html`.

---

## What the analysis found

**1. The corridor emits about 176 kt CO2 a year, or 218 kt
CO2e on a 100-year basis and 317 kt on a 20-year basis.**
It burns 56 kt of fuel, 631 GWh of fuel energy.
The gap between the CO2 and CO2e figures is black carbon, which is
19% of 100-year warming here because these are four-stroke
engines on residual fuel running at part load.

**2. 62% of shaft energy is auxiliary load, not
propulsion.** This is the most consequential result and it only appeared once auxiliary power was
taken from the IMO ro-pax table (a flat 710 kW above 2,000 GT, in every phase) rather than guessed
as a share of engine size. The ships spend 28% of
port-to-port time queueing and a median 4.8 hours
alongside between crossings, all with hotel and vehicle-deck ventilation running. About
63 GWh a year is drawn by ships sitting still.

**3. That makes shore power a real option, and it was missing from the first pass.** Cold ironing
at both terminals plus a connection for vessels at anchor saves roughly USD 8.5M a year in fuel
without touching a propulsion system. On CO2 it is close to a wash at the current grid, because
marine auxiliary generators emit about 707 g CO2 per kWh and the grid is not much better.

**4. Battery-electric halves primary energy and cuts costs by 60%, and its carbon case turns
entirely on the grid and on which climate metric is used.** Break-even grid intensity is
0.60 tCO2/MWh on CO2 alone,
0.74 on 100-year CO2e, and
1.09 on 20-year CO2e. Indonesia's grid sits around 0.75-0.90. So
electrification is worse than diesel on CO2, roughly neutral on 100-year CO2e once black carbon is
counted, and better on a 20-year view. Local air quality improves unambiguously: all ship-side NOx,
SOx, PM and black carbon go to zero at two terminals that sit inside populated areas.

**5. Drop-in biofuel remains the only pathway that cuts emissions now with no capital works.**
B100/HVO cuts about 80% at roughly USD 160/tCO2e at current spreads. For reference, Corbett, Wang
and Winebrake (2009) put speed-reduction abatement in the container fleet at USD 30-200/tCO2, so
this sits at the top of that range.

**6. The register is not the corridor fleet and is not an ASDP fleet.** Of
360 register vessels, 108
carry an ASDP owner or operator. Only 46 of the
69 vessels on the corridor appear in the register, and ASDP-flagged
vessels account for 12%
of observed crossings. 160 of 360 hulls are over thirty years old, which is what actually drives a
replacement case.

---

## Sanity checks

Nine model outputs are compared against figures from outside the model. All currently pass.

| Check | Model | Expected |
|---|---|---|
| Implied main engine SFC | 242.10 g fuel/kWh | 190 to 260 |
| Implied fuel-to-shaft efficiency | 38.46 % | 33 to 45 |
| Median installed power | 0.68 kW/GT | 0.35 to 1.1 |
| Median steaming speed | 10.71 knots | 7.0 to 14.0 |
| Fuel per crossing | 0.13 t fuel per 1,000 GT | 0.03 to 0.2 |
| CO2 intensity of transport supply | 25.95 g CO2 / GT-nm | 3.0 to 30.0 |
| Auxiliary share of shaft energy | 61.84 % | 20 to 70 |
| Black carbon share of CO2e-100 | 18.53 % | 2 to 30 |
| Share of port-to-port time spent waiting | 27.99 % | 5 to 55 |

Full basis for each expected range is in `outputs/sanity_checks.csv` and on the dashboard.

---

## What is missing, and what to ask for

| Gap | Why it matters | Where to get it |
|---|---|---|
| **Installed main engine power (kW)** | Not in the supplied register. Now the single largest uncertainty, and it is a standard field in the same commercial register the tabs came from. | Re-pull with the engine power field. |
| **Positional AIS rather than port-to-port events** | Would replace the inferred phase split with observed speeds, and separate steaming from queueing directly. | Same AIS provider. |
| **AIS for ASDP's other routes** | The corridor is one of about 300 ASDP routes. Nothing scales to the fleet without observed activity elsewhere. | Same AIS provider. |
| **ASDP's own bunker records** | Would validate the whole bottom-up model in one step and replace assumed fuel prices with what ASDP pays. | ASDP directly. |
| **Official grid emission factor** | The electrification conclusion turns on it. The value used is a plausible range, not a sourced figure. | MEMR/ESDM grid emission factor for the JAMALI and Sumatra systems. |
| **Actual fuel sulphur** | Pertamina's domestic list still sells high-sulphur MFO more cheaply than low-sulphur. SOx and part of PM scale directly with it. | ASDP bunker delivery notes. |

---

## Repository layout

```
src/config.py           analyst assumptions, each with a source tag
src/factors.py          emission factors and power tables, all transcribed from published sources
src/run.py              the model: parse, estimate power, phase-resolve voyages, run scenarios
src/template.html       dashboard template
src/build_dashboard.py  inlines model output into a self-contained HTML file
src/run_v1.py.bak       the first-pass model, kept for comparison
docs/index.html         the dashboard
docs/METHODOLOGY.md     how each number is derived
docs/SOURCES.md         full source list
outputs/                CSVs: per-vessel, per-scenario, fleet, monthly, sanity checks
```

## Reproducing

```bash
pip install pandas numpy openpyxl
python src/run.py --workbook "Port-Port_Moves_Merak_to_B_with_ASDP_routes.xlsx"
python src/build_dashboard.py
```

The input workbook is not committed. See `.gitignore`.

## Publishing

Laid out for GitHub Pages (`main` branch, `/docs` folder). Pages on a private repository needs a
Team or Enterprise plan; if the repository must stay private, `docs/index.html` is fully
self-contained and can be emailed or dropped in SharePoint as one file.
