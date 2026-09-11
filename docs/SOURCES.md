# Sources

## Method
- **Olmer, N., Comer, B., Roy, B., Mao, X., & Rutherford, D. (2017). "Greenhouse gas emissions from
  global shipping, 2013-2015: Detailed methodology." ICCT.** The primary parameter source for v2.
  Publishes, in citable form, the Third IMO GHG Study tables that the IMO reports themselves do not
  reproduce: auxiliary engine power by ship class, size bin and phase (Appendix C); boiler power
  (Appendix D); main and auxiliary engine emission factors in g/kWh (Appendices E and G); black
  carbon emission factors as a function of engine stroke, fuel and load (Appendix F); low-load
  adjustment factors (Appendix I); draught adjustment factors by ship class (Table 13); the hull
  fouling relation after Townsin (2000, 2003) and Willsher (2007); and the weather factor.
  https://theicct.org/sites/default/files/Global-shipping-GHG-emissions-2013-2015_Methodology_17102017_vF.pdf
- **Corbett, J.J., Wang, H., & Winebrake, J.J. (2009). "The effectiveness and costs of speed
  reductions on emissions from international shipping." Transportation Research Part D 14(8),
  593-598.** Used as the reference point for judging the abatement costs reported here: that paper
  puts speed-reduction abatement in the container fleet at USD 30-200 per tonne CO2.
- **Winebrake, J.J., Corbett, J.J., Wang, C., Farrell, A.E., & Woods, P. (2005). "Optimal fleetwide
  emissions reductions for passenger ferries." Journal of the Air & Waste Management Association
  55(4), 458-466.** The closest published analogue to this task: a mixed-integer optimisation of
  emissions-reduction options across a passenger ferry fleet.
- **Fourth IMO GHG Study 2020.** Bottom-up structure: power demanded from speed and draught,
  SFC by engine type/fuel/build year, low-load correction factors, and separate main engine,
  auxiliary and boiler accounting. https://www.imo.org/en/ourwork/Environment/Pages/Fourth-IMO-Greenhouse-Gas-Study-2020.aspx
- **World Bank Pacific Observatory, Greenhouse Gas Emissions from Maritime Traffic.** The Bank's own
  implementation of the same method on AIS data, adapted by Cherryl Chico. Useful precedent for how
  this kind of work has been framed internally.
  https://worldbank.github.io/pacific-observatory/ais/ais_emissions.html

## Emission factors
- **IMO Resolution MEPC.281(70)**, Table 1. Carbon conversion factors C_F: diesel/gas oil 3.206,
  light fuel oil 3.151, heavy fuel oil 3.114, LNG 2.750, methanol 1.375, ethanol 1.913; with lower
  heating values. https://wwwcdn.imo.org/localresources/en/KnowledgeCentre/IndexofIMOResolutions/MEPCDocuments/MEPC.281(70).pdf

## Route
- Indonesian ferry-operations literature gives the Bakauheni–Merak crossing as 15 miles with
  scheduled sailing times of 90–120 minutes depending on berth, and 60–72 minutes port time.
  Great-circle distance between the two port coordinates is 15.1 nm.
  https://www.atlantis-press.com/article/126002121.pdf
- Route operates 24 hours with roughly one departure every 12 minutes; around 70 ships available and
  28–33 operating per day, against about 28 berth slots, which produces offshore queueing.

## Prices
- **Indonesian domestic fuel.** Pertamina non-subsidised industrial economic prices, 15–31 March 2026,
  Region 1 (Sumatra, Java, Bali, Madura), excluding VAT and PBBKB: B40 industrial diesel
  Rp 23,050/litre, MFO high-sulphur Rp 14,900/litre, MFO low-sulphur Rp 16,850/litre.
  Reported by fuel distributors, not read from a Pertamina publication.
  https://www.mdscorp.co.id/2026/03/update-harga-solar-industri-b40-mfo-15.html
  *This was an oil-spike fortnight. Verify against ASDP's own bunker invoices.*
- **International bunkers.** Singapore VLSFO traded roughly USD 780–850/t and MGO USD 1,100–1,220/t
  through August 2026; VLSFO briefly passed USD 1,000/t in March 2026 for the first time in five
  years. https://shipandbunker.com/prices/apac/sea/sg-sin-singapore
- **Biofuel.** Singapore B30-VLSFO premium over conventional VLSFO around USD 231/t in late August
  2026; Rotterdam B100 around USD 1,387/t in late July 2026.
  https://www.indexbox.io/blog/biofuel-bunker-prices-rotterdam-gibraltar-singapore-trends-aug-2026/
- **Electricity.** PLN non-subsidised tariffs, frozen through Q3 2026: I-3 medium industry above
  200 kVA Rp 1,114.74/kWh; I-4 large industry above 30,000 kVA Rp 996.74/kWh.
- **Exchange rate.** Rp 16,959/USD was the Q3-2026 tariff-setting parameter published by MEMR; spot
  was around Rp 17,700 in late August 2026. Rp 17,000 used as a planning rate.

## Electrification
- Marine battery systems reported at USD 800–1,000/kWh for retrofits and around USD 500/kWh for
  newbuilds (DNV, via sustainable-ships.org, 2025). Cell-level LFP prices have fallen substantially
  since; treat these as upper bounds.
  https://www.sustainable-ships.org/stories/2025/htd-containership-power-barge
- ASDP is installing large-capacity solar at both Merak and Bakauheni as part of a green-port
  programme, alongside wastewater and hazardous-waste facilities.
  https://en.antaranews.com/amp/news/379725/asdp-turns-merak-and-bakauheni-ports-into-green-energy-hubs

## Not sourced
The following are analyst assumptions and carry no citation. They are flagged `[ASSUM]` in
`src/config.py` and in the dashboard's assumptions register.

- Specific fuel consumption values. Structure follows the Fourth IMO GHG Study; the numbers are
  rounded representatives inside its ranges, not transcriptions of its tables. **Replace before
  publication.**
- Indonesian grid emission factor. 0.85 tCO₂/MWh used, 0.70–0.90 range. Commonly quoted for the
  JAMALI system but not verified against a current MEMR/ESDM decree. **The electrification
  conclusion turns entirely on this number.**
- Block coefficient 0.60, Admiralty coefficient 450, service power 80% of MCR, kW/GT bounds.
- Auxiliary load fractions (12% at sea, 15% manoeuvring and alongside).
- Minimum propulsion load floor of 15% of MCR.
- Well-to-wake savings by pathway (B40 24%, B100 80%, bio-methanol 85%, dedicated RE 95%).
- Drivetrain and charging efficiencies.
- The fleet-wide activity assumption (300 operating days, 8 steaming hours per day, 35% mean load).
