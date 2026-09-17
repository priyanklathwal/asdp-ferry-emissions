# Design system

Editorial long-form, in the register of a NYT Upshot or Bloomberg Graphics piece. The page is an
argument that happens to have charts in it, not a dashboard that happens to have text.

## Principles

1. **One idea per screen.** Each section makes one claim in its headline. Everything in the section
   exists to support that claim. If a chart supports a second idea, it belongs in a second section.
2. **The chart title states the finding.** Never "CO2 by pathway." Always "Electrifying raises
   emissions at today's grid." The axis labels carry the units.
3. **Prose is narrow, evidence is wide.** Text sits in a 640px measure. Figures break out to 920px.
   The eye reads down a column and pauses on something wider.
4. **Restraint.** Gray is the default colour. One accent means "the intervention," one means "worse
   than doing nothing." Nothing else is coloured. No animation.
5. **Direct labels, not legends.** Every mark is labelled where it sits.
6. **Whitespace is structure.** Sections are separated by space, not boxes. A hairline rule at most.

## Type

| Role | Face | Size | Leading | Notes |
|---|---|---|---|---|
| Headline | Serif display | 54px | 1.08 | −0.02em tracking, max 18 words |
| Deck | Serif | 22px | 1.45 | Light weight, secondary ink |
| Kicker | Sans | 12px | — | +0.14em tracking, uppercase, accent colour |
| Section head | Serif | 34px | 1.2 | Full sentence, the finding |
| Body | Serif | 19px | 1.65 | 640px measure, 18px on mobile |
| Figure title | Sans | 16px | 1.35 | Weight 600, the finding |
| Figure subtitle | Sans | 13px | 1.4 | Units, period, scope |
| Figure source | Sans | 12px | 1.4 | Secondary ink, below the figure |
| Axis and labels | Sans | 12px | — | Tabular numerals |
| Table | Sans | 14px | 1.5 | Tabular numerals, right-aligned figures |

Serif stack: Charter, "Iowan Old Style", Georgia, serif.
Sans stack: -apple-system, "Segoe UI", Helvetica, Arial, sans-serif.

## Space

Vertical rhythm on an 8px grid. Section gap 112px. Headline to deck 20px. Deck to body 40px.
Paragraph to figure 40px. Figure to caption 12px. Caption to next paragraph 48px.

## Colour

| Token | Value | Job |
|---|---|---|
| paper | #FBFAF7 | page |
| ink | #171717 | headlines, body, primary marks |
| ink-2 | #5F5F5F | deck, captions, secondary marks |
| ink-3 | #9A9A9A | axis ticks, gridlines, source lines |
| rule | #E4E2DC | hairlines |
| panel | #F3F1EB | control panel background |
| accent | #1B6F8C | the intervention; observed data series |
| hot | #C2461F | worse than the baseline |
| accent-soft | #CFE0E8 | de-emphasised bars |

Baseline reference lines are ink, dashed. Highlighted bar is accent. Everything else is accent-soft
or ink-3. Hot appears only when a value is worse than the baseline.

## Chart grammar

- Title above in sans 600, then subtitle, then the chart, then a source line.
- Horizontal bars for category comparison; value label at bar end.
- Time on the x-axis, always left to right, no vertical gridlines.
- Reference lines dashed ink with a label at the top.
- Annotations as short sans text with a 1px leader.
- Axis lines: baseline only. Gridlines: hairline, three or four at most.

## Review protocol

Before each release, five passes in this order, each with one brief and one written finding:

1. **Model and data.** Re-run the model. All sanity checks must pass. Every number that appears in
   static prose is checked against the model output; numbers that can be generated from the data
   should be, so they cannot drift.
2. **Writing.** Read every tab as a policymaker. Flag jargon on the Context, Key messages and
   Implications tabs; technical terms are allowed on Methodology and Data. Remove hedges and tics.
   No em dashes in prose.
3. **Design.** No CSS classes defined but unused; no colour outside the token set; every chart has
   a title stating its finding, a subtitle with units, and a source line.
4. **Consistency.** README, METHODOLOGY and the page agree on every headline number and on the tab
   structure. Every repository link resolves. Every tab button has a section.
5. **Release.** Build, render-test, push, confirm the Pages build, record the commit.
