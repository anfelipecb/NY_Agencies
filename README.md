# NY Agencies

A public reading of New York City's agencies. The label is the acronym. Open one and the card shows what the agency does, where Executive Order 23 places it, what it spent in Fiscal 2026, and how many people it employs.

The Mayor's Management Report covers **45 agencies**, not 23. Executive Order 23 (September 8, 2026) is the org chart that assigns them to a deputy mayor or a senior staffer. This atlas includes every agency with a resources row in that report. Two placements, 311 and the libraries, are inferred from the order and marked that way. Mayor's offices that the order names but the report does not chapter — OMB, Labor Relations, Contract Services, Community Safety, and others — are the first item in the plan to go deeper.

Figures are checked against the Fiscal 2026 MMR agency-resources file when that file is available beside this repo.

## What a card holds

- One-line description and a short account of the work
- Reporting line under Executive Order 23: supervised, liaison, or inferred
- FY2026 expenditures and the authorized figure in the same row
- Actual and authorized positions, with uniformed and civilian split where the report publishes one
- Overtime, human-services contracts, capital commitments, and table revenue, where those rows exist

Expenditures are the report's projected actual, in millions of dollars. They are not the adopted budget, and they mix city, state, and federal funds. Parks headcount includes full-time equivalents. EDC and the School Construction Authority have headcount and capital commitments and no expenditure line.

## Develop

```bash
npm install
npm run dev
```

Regenerate the cards after editing the catalog:

```bash
npm run cards
```

`scripts/build_cards.py` writes `data/agencies.json` and `knowledge/agencies/`. If `../NY_Efficiency/data/raw/mmr_agency_resources.csv` is present, the script refuses to write when a figure does not match that file.

## Deploy

The site is a static Vite build. From this directory:

```bash
npm run build
vercel --prod
```

No environment variables. The data is in the repository.

## Sources

- [Fiscal 2026 Mayor's Management Report](https://www.nyc.gov/assets/operations/downloads/pdf/mmr2026/2026_mmr.pdf)
- [MMR Agency Resources](https://data.cityofnewyork.us/City-Government/Mayor-s-Management-Report-Agency-Resources/4qmi-txnk) (`4qmi-txnk`)
- [Executive Order 23](https://www.nyc.gov/mayors-office/news/2026/09/executive-order-no--23)

## Author

Andrés Camacho · [afcamachob@uchicago.edu](mailto:afcamachob@uchicago.edu)
