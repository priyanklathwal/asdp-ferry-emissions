<div align="center">

# Sunda Strait Ferry Emissions

**A bottom-up energy and emissions model for the Merak–Bakauheni RoPax corridor — Indonesia's busiest ferry crossing, and one of the busiest in the world.**

[![Live dashboard](https://img.shields.io/badge/dashboard-live-0f766e?style=flat-square)](https://priyanklathwal.github.io/asdp-ferry-emissions/)
[![Method](https://img.shields.io/badge/method-IMO%20%2F%20ICCT%20bottom--up-1f6feb?style=flat-square)](docs/METHODOLOGY.md)
[![Checks](https://img.shields.io/badge/sanity%20checks-9%2F9%20passing-2da44e?style=flat-square)](outputs/sanity_checks.csv)
[![Python](https://img.shields.io/badge/python-3.10%2B-3776ab?style=flat-square)](requirements.txt)
[![Status](https://img.shields.io/badge/status-working%20draft-d4552c?style=flat-square)](#limitations)

[Dashboard](https://priyanklathwal.github.io/asdp-ferry-emissions/) · [Methodology](docs/METHODOLOGY.md) · [Sources](docs/SOURCES.md) · [Results](outputs/)

</div>

---

## The answer

**Decarbonising this crossing is a power-sector decision, not a shipping one.**

Every option that takes fuel off these ships moves the emissions onto Indonesia's grid. At today's grid intensity that is a worse trade on carbon and a much better one on cost. Nothing about the vessels themselves is the binding constraint.

Three findings carry that conclusion.

**1 · Hotel load, not propulsion, is where the energy goes.**
`62%` of shaft energy is auxiliary generators. A crossing takes 1.4 hours; the queueing and turnaround around it take 5.8. Ships sitting still draw `63 GWh` a year, which shore power could displace without touching a propulsion system.

**2 · The grid is the constraint.**
Full electrification saves `$30M` a year and raises CO₂ by `41%`. Break-even sits at `0.60 tCO₂/MWh`; Indonesia's grid runs 0.75–0.90. On a 100-year CO₂e basis, once black carbon counts, break-even rises to `0.74` and the trade is close to neutral. On a 20-year basis (`1.09`) electrification wins outright.

**3 · Only drop-in biofuel cuts emissions today.**
B100 removes 80% with no capital works at roughly `$180/tCO₂e`. Everything cheaper raises emissions; everything cleaner needs new vessels or a cleaner grid.

## Baseline

| | |
|---|---|
| CO₂ | **176 kt/yr** |
| CO₂e (100-yr) | 218 kt/yr |
| CO₂e (20-yr) | 317 kt/yr |
| Fuel burned | 56 kt/yr |
| Fuel energy | 631 GWh/yr |
| Shore electricity if electrified | 292 GWh/yr |
| Observed crossings | 33,695 over 200 days |

Black carbon is `19%` of 100-year warming here — four-stroke engines on residual fuel at part load — which is why the CO₂ and CO₂e figures diverge so sharply.

## Pathways

| Pathway | kt CO₂/yr | Δ | Δ cost | $/tCO₂e |
|---|---:|---:|---:|---:|
| Baseline | 176 | — | — | — |
| B40 drop-in biodiesel | 134 | +24% | +$36M | $690 |
| B100 / HVO drop-in | 35 | +80% | +$30M | $180 |
| Bio-methanol (engine conversion) | 26 | +85% | +$60M | $320 |
| Shore power at berth and anchorage | 188 | -7% | −$8M | — |
| Battery-electric, PLN grid | 249 | -41% | −$30M | — |
| Battery-electric, dedicated RE | 12 | +93% | −$30M | −$150 |

## A caveat about the input data

The vessel register supplied is not the fleet on this route, and it is not an ASDP fleet.

- `108` of `360` registered vessels carry an ASDP owner or operator
- only `46` of the `69` vessels seen on the corridor appear in the register
- ASDP-flagged vessels account for `12%` of observed crossings

Fleet replacement and corridor decarbonisation are therefore two different questions. On replacement, age decides it: 160 of 360 hulls are past thirty years old.

## Method

Activity-based, phase-resolved bottom-up model following the Third and Fourth IMO GHG Studies, using the parameter tables published by [Olmer et al. (2017)](https://theicct.org/publication/greenhouse-gas-emissions-from-global-shipping-2013-2015/) for the ICCT.

```
displacement + observed steaming speed  →  propulsion power (Admiralty)
  × hull fouling × weather × draught adjustment
+ published auxiliary kW by class and phase
  × energy-based emission factors (g/kWh)
  × SFOC load curve and low-load adjustment factors
→  CO₂, CH₄, N₂O, BC, NOₓ, SOₓ, PM
```

Voyages are split into steaming, manoeuvring, waiting and alongside. Main engines are off while waiting, per the IMO anchor convention; waiting time is identified per vessel as the excess over that vessel's own 10th-percentile crossing. Full detail in [`docs/METHODOLOGY.md`](docs/METHODOLOGY.md).

### Validation

Nine model outputs are compared against benchmarks from outside the model — engine manufacturer data, published ferry schedules, port operating reports, and the ranges the inventory literature reports for this ship class. All pass.

| Check | Model | Expected |
|---|---:|---:|
| Implied main engine SFC | 242 g fuel/kWh | 190–260 |
| Implied fuel-to-shaft efficiency | 38.5 % | 33–45 |
| Median installed power | 0.676 kW/GT | 0.35–1.1 |
| Median steaming speed | 10.7 knots | 7–14 |
| Fuel per crossing | 0.129 t fuel per 1,000 GT | 0.03–0.2 |
| CO2 intensity of transport supply | 26 g CO2 / GT-nm | 3–30 |
| Auxiliary share of shaft energy | 61.8 % | 20–70 |
| Black carbon share of CO2e-100 | 18.5 % | 2–30 |
| Share of port-to-port time spent waiting | 28 % | 5–55 |

## Quick start

```bash
git clone https://github.com/priyanklathwal/asdp-ferry-emissions.git
cd asdp-ferry-emissions
pip install -r requirements.txt

python src/run.py --workbook Port-Port_Moves_Merak_to_B_with_ASDP_routes.xlsx
python src/build_dashboard.py
open docs/index.html
```

The input workbook is not distributed with this repository. See [data availability](#data-availability).

## Repository layout

```
src/
├── config.py             analyst assumptions, each carrying a source tag
├── factors.py            IMO/ICCT emission factors and power tables, transcribed
├── run.py                the model
├── template.html         dashboard template
└── build_dashboard.py    inlines results into a self-contained page
docs/
├── index.html            the dashboard (GitHub Pages serves this directory)
├── data.json             model output
├── METHODOLOGY.md        derivation of every number
└── SOURCES.md            full source list
outputs/                  results as CSV
```

Assumptions live in `config.py` and are tagged `[ASSUM]`, `[LIT]`, `[MKT]` or `[GOV]`. Anything in `factors.py` is transcribed from a published table and is never analyst judgement.

## Limitations

This is a working draft, not an audited inventory.

- **Installed engine power is estimated, not observed.** The register has no kW field, so power is derived from hull dimensions. This is the single largest error bar and is fixable with one data request.
- **The grid emission factor is not sourced.** A 0.75–0.90 tCO₂/MWh range is used. The entire electrification conclusion turns on it, and it should be replaced with the current MEMR/ESDM decree value before this is cited.
- **AIS timestamps are hourly-binned**, so a single voyage carries ±1 hour. Across 33,695 voyages the mean is sound; per-voyage figures are not.
- **Fuel type is inferred** for roughly half the register from vessel size.
- **No cargo or passenger loading**, so nothing here is per passenger-km or per tonne-km.
- **Capital costs are estimated only for the battery pathway**, not for engine conversion.
- **Feedstock availability is not modelled.** In Indonesia, competition with the existing land-transport B40 mandate is likely to bind before price does.

### What would most improve this

| Gap | Effect | Source |
|---|---|---|
| Installed main engine power (kW) | Collapses the largest error bar | Re-pull the register with the field included |
| Positional AIS instead of port-to-port events | Replaces the inferred phase split with observed speeds | Same AIS provider |
| AIS for ASDP's other routes | Nothing scales to the fleet without it | Same AIS provider |
| ASDP bunker records | Validates the whole model in one step | ASDP directly |
| Official grid emission factor | Decides the headline conclusion | MEMR / ESDM |

## Currency

All monetary figures are in US dollars. Indonesian domestic prices — Pertamina industrial fuel and the PLN tariff — are converted at the mid-market rate of Rp 17,900 per dollar on 11 September 2026. The rupiah has moved within a 16,100–18,200 band over the past year, so a ±6% swing in the domestic fuel and electricity lines is well within normal.

## Data availability

The commercial ship register this analysis was built from is licensed and is **not** redistributed here, and neither are the vessel particulars derived from it. `outputs/vessels_derived.csv` carries only IMO number, name, gross tonnage, age and estimated power.

## Sources

Method and parameters from the [ICCT detailed methodology](https://theicct.org/publication/greenhouse-gas-emissions-from-global-shipping-2013-2015/) (Olmer, Comer, Roy, Mao & Rutherford, 2017), the Third and Fourth IMO GHG Studies, and [IMO Resolution MEPC.281(70)](https://wwwcdn.imo.org/localresources/en/KnowledgeCentre/IndexofIMOResolutions/MEPCDocuments/MEPC.281(70).pdf) for carbon conversion factors. Abatement costs are read against Corbett, Wang & Winebrake (2009) on speed reduction, and the approach to a ferry fleet against Winebrake, Corbett, Wang, Farrell & Woods (2005). Full list in [`docs/SOURCES.md`](docs/SOURCES.md).

---

<div align="center">
<sub>Prepared for the World Bank East Asia and Pacific transport team · working draft</sub>
</div>
