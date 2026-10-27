# How the agency cards get better

The current cards are a first reading. They answer who the agency is, who Executive Order 23 assigns it to, what the Fiscal 2026 Mayor's Management Report says it spent, and how many people it employs. They are enough to stop mixing agencies up. They are not enough to talk about whether the agency is working.

Do these in order. Each one makes the next conversation more specific.

## 1. Name the offices the report leaves out

Executive Order 23 assigns offices that have no chapter of their own: Management and Budget, Labor Relations, Contract Services, Immigrant Affairs, Media and Entertainment, the Office of Community Safety, Child Care, and others. Their money sits inside the Mayoralty or inside a parent agency.

Pull the adopted budget's units of appropriation for those offices. Give each one a card with the same shape: what it does, who it reports to, personal-service dollars, and headcount. Until that exists, the org chart on the site is the MMR's chart, not City Hall's.

## 2. Split the funds

An expenditure line mixes city tax levy with state and federal categorical funds. Personal service and other-than-personal-service are also mixed, except where a human-services contract row happens to be published.

Next cut, for every agency that has an expenditure:

- City funds versus categorical funds
- Personal service versus other than personal service
- The five largest units of appropriation, named

The adopted expense budget is the source. The MMR row stays as the headline so the two vintages can be compared.

## 3. Add results, not just resources

Each MMR chapter has performance indicators, a target, and a desired direction. A card that only shows spending cannot say whether the agency is doing the thing it exists to do.

Add up to five critical indicators per agency. Keep the desired direction on the card. Note when the latest report restated an earlier year. Desired direction is not optional: up is good for some indicators and bad for others.

## 4. Read authorities on their own books

EDC and the School Construction Authority publish headcount and capital commitments and no expenditure line. Health + Hospitals, NYCHA, and CUNY publish an expenditure line that is not the same object as a mayoral department's budget. City tax levy, federal subsidy, patient revenue, and tuition are different kinds of money.

For each authority, attach the latest public financial statement and label which number is the city's contribution. Do not rank an authority against a department on the MMR expenditure alone.

## 5. Join the efficiency scan

The NY Efficiency project already compares overtime growth with budget growth, and spending growth with outcome trends. A card should be able to say, from that public work, whether overtime outpaced the budget and whether the agency landed in the "spent more, results flat" group.

Link the agency id to those tables. Keep the caveat that public data produces questions, not findings. When a new MMR is released, rerun `scripts/build_cards.py` against the new resources file before trusting a card.

## What not to add yet

Commissioner names, org charts below the commissioner, and internal program budgets go stale fast and are easy to get wrong from the outside. Add them when a dated public source is in hand, and put the date on the card.
