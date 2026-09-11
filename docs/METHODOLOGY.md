# Methodology, v2

Activity-based, phase-resolved bottom-up model following the Third and Fourth IMO GHG Studies,
using the parameter tables as published by Olmer et al. (2017) for the ICCT, adapted to
port-to-port AIS event data rather than hourly positional tracks. The World Bank's own Pacific
Observatory maritime emissions work uses the same underlying method.

## 1. Chain of calculation

```
displacement + observed steaming speed  ->  propulsion power (Admiralty relation)
  x hull fouling x weather x draught adjustment
propulsion power x steaming hours       ->  main engine shaft energy
published aux kW by class and phase     ->  auxiliary shaft energy
shaft energy x g/kWh emission factor    ->  CO2, NOx, SOx, PM, CO, CH4, N2O
  x SFOC load curve (CO2) or low-load adjustment factor (others)
main engine fuel mass x g/kg factor     ->  black carbon
CO2 / carbon factor                     ->  fuel mass, then x LHV -> fuel energy
```

## 2. What changed from v1 and why it matters

| Element | v1 | v2 | Effect |
|---|---|---|---|
| Auxiliary power | 12% of installed MCR, guessed | IMO/ICCT published table for ferry ro-pax: 105 kW under 2,000 GT, 710 kW above, all phases; boilers zero | Auxiliary load rose to 62% of shaft energy and became the dominant finding |
| CO2 | Invented SFC table x carbon factor | Energy-based g/kWh factors from the same published tables | Removed one estimation step |
| Low load | Ad hoc "minimum 15% of MCR" floor | IMO SFOC load curve plus published low-load adjustment factors | Structural spread fell from ±15% to under 7% |
| Waiting offshore | Not distinguished from steaming | Separate phase, main engines off per the IMO anchor convention, identified per vessel | Median engine load rose from 0.15 to 0.32, steaming speed from 6.3 to 10.7 knots, both now consistent with published schedules |
| Fouling and weather | One rolled-up 1.10 factor | Fouling computed per vessel from age via Townsin; weather and ro-pax draught factors applied separately | Older hulls now carry a higher power demand, as they should |
| Pollutants | CO2 only | CO2, CH4, N2O, black carbon, NOx, SOx, PM | Black carbon is 19% of 100-year warming and half again on a 20-year view; local air quality enters the comparison |

## 3. Vessel power

The register has no installed engine power column. Displacement comes from
`LOA x 0.95 x beam x draft x 0.60 x 1.025` where the dimensions are reported (278 vessels), and
from `displacement = 2.895 x GT^0.866` (R² 0.931) where they are not (105 vessels). Drafts above
0.32 x beam were capped; the median ratio in this register is 0.21 and the 22 records above the cap
are scantling drafts or keying errors.

Installed MCR comes from the Admiralty relation at design speed divided by 0.80, bounded to
0.25-1.60 kW per GT. That bound bit on 31 vessels and exists because the design-speed field carries
several trial speeds above 22 knots. MCR is used only for the load factor, the manoeuvring floor
and battery sizing; propulsion energy at sea comes from displacement and observed speed, so the
unreliable design-speed field does not enter the fuel estimate.

## 4. Phase decomposition

The IMO/ICCT method assigns a phase to each hour from speed over ground and distance to shore.
With port-to-port events only, an equivalent split is inferred per vessel:

- **Unimpeded crossing time** is that vessel's own 10th-percentile port-to-port time, bounded to
  1-4 hours. It represents a crossing that did not queue.
- **Manoeuvring**: 0.6 hours, propulsion at the Admiralty power for 5 knots (the ICCT boundary
  between manoeuvring and cruising), floored at 8% of MCR for thruster and berthing work.
- **Steaming**: the remainder of the unimpeded time, at `15 nm / steaming hours`.
- **Waiting**: any excess over the unimpeded time. Main engines off, auxiliaries on. This is the
  IMO anchor convention.
- **Alongside**: observed gap between arrival and the vessel's next departure, capped at 6 hours.
  Main engines off, auxiliaries at berth demand.

The result is 28% of port-to-port time spent waiting, which is consistent with a corridor reported
to have about 28 berth slots against roughly 70 available ships.

## 5. Sensitivity and what still dominates

Whether main engines idle rather than shut down while queueing moves the annual total by under 7%.
Sailed distance from 15 to 19 nm moves it by about 8%. Neither is now the binding uncertainty.
Installed engine power is, and it is a data gap rather than a modelling choice.

## 6. Known limitations

1. No installed engine power in the source data. Everything downstream inherits that error.
2. AIS timestamps are hourly-binned, so a single voyage duration carries ±1 hour. Across 33,695
   voyages the mean is sound; per-voyage figures are not.
3. Sailed distance is the 15 nm port-to-port line; real tracks are longer.
4. Fuel type is inferred for 183 of 369 register rows from vessel size.
5. Cargo and passenger loading are not modelled, so nothing here is per passenger-km or per
   tonne-km. That would need ASDP's own traffic data.
6. Well-to-tank emissions of the fossil baseline are not counted, so the biofuel and electric
   comparisons are slightly conservative in the fossil case's favour.
7. Feedstock availability, certification and bunkering logistics are not modelled for the fuel
   pathways. In Indonesia, feedstock competition with the existing land-transport B40 mandate is
   likely to bind before price does.
8. Vessel capital costs are only estimated for the battery pathway, not for engine conversion.
