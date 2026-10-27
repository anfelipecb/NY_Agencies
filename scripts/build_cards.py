"""Build agency knowledge cards from the Fiscal 2026 MMR resource snapshot.

Numbers are the FY2026 rows of NYC Open Data dataset 4qmi-txnk
(Mayor's Management Report — Agency Resources). When the sibling
NY_Efficiency download is present, this script checks every figure
against that file before writing.

Reporting lines follow Executive Order 23 (September 8, 2026).
"""

from __future__ import annotations

import csv
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SIBLING = ROOT.parent / "NY_Efficiency" / "data" / "raw" / "mmr_agency_resources.csv"
OUT_JSON = ROOT / "data" / "agencies.json"
KNOW = ROOT / "knowledge" / "agencies"

PORTFOLIOS = [
    {
        "id": "fdm",
        "label": "First Deputy Mayor",
        "blurb": "Police, public schools, correction, probation, finance, and business integrity. Liaison to CUNY, the Civilian Complaint Review Board, and the School Construction Authority.",
    },
    {
        "id": "operations",
        "label": "Deputy Mayor for Operations",
        "blurb": "Sanitation, streets, water, parks, fire, emergency management, design and construction, citywide administration, records, and technology.",
    },
    {
        "id": "hhs",
        "label": "Deputy Mayor for Health and Human Services",
        "blurb": "Health, benefits, child welfare, shelter, aging, youth, veterans, and the medical examiner. Homeless Services and HRA sit inside Social Services. Liaison to Health + Hospitals.",
    },
    {
        "id": "housing",
        "label": "Deputy Mayor for Housing and Planning",
        "blurb": "Buildings, city planning, housing preservation and development, and landmarks. Liaison to NYCHA.",
    },
    {
        "id": "economic",
        "label": "Deputy Mayor for Economic Justice",
        "blurb": "Human rights, consumer and worker protection, cultural affairs, small business, taxis, and the Economic Development Corporation. Libraries are a liaison, not a named agency.",
    },
    {
        "id": "counsel",
        "label": "Chief Counsel",
        "blurb": "Administrative hearings at OATH. Liaison to Investigation and the Law Department, whose leaders also report to the Mayor.",
    },
    {
        "id": "staff",
        "label": "Chief of Staff",
        "blurb": "Elections, as a liaison. 311 is placed here because the Mayor's Office of Operations reports to the Chief of Staff. The order does not name 311.",
    },
    {
        "id": "safety",
        "label": "Deputy Mayor for Community Safety",
        "blurb": "No chapter of its own in the Mayor's Management Report. B-HEARD is operated by Fire and Health + Hospitals.",
    },
]


def agency(**kwargs: object) -> dict:
    return kwargs


# Positions are (source label, display label, actual, authorized).
# Overtime is ("M", millions) or ("K", thousands) as published.
AGENCIES = [
    agency(
        id="DOE",
        acronym="DOE",
        name="New York City Public Schools",
        portfolio="fdm",
        tie="supervise",
        reports_to_mayor=True,
        mayor_official="Chancellor",
        one="The city school system. Executive Order 23 calls it New York City Public Schools and says that is officially the Department of Education.",
        about="It runs public schools from pre-K through high school, plus central offices that hire teachers, buy services, and move students. It is the largest agency in the city on both spending and headcount.",
        exp=37709.6,
        auth=36897.6,
        positions=[("Personnel", "Personnel", 152698, 155238)],
        ot=("M", 21.8),
        revenue=26.7,
        contracts=2443.5,
        watch="Almost every other agency is a rounding error next to this one. A single citywide total hides the difference between schools and the central office.",
    ),
    agency(
        id="HRA",
        acronym="HRA",
        name="Human Resources Administration",
        portfolio="hhs",
        tie="supervise",
        parent="Department of Social Services",
        one="Cash assistance, SNAP, and Medicaid administration for New Yorkers who qualify.",
        about="HRA is the benefits side of the Department of Social Services. The work is eligibility, case processing, and payments, much of it through contracts and other governments' rules.",
        exp=14685.9,
        auth=14204.5,
        positions=[("Personnel", "Personnel", 10747, 12525)],
        ot=("M", 41.6),
        revenue=72.7,
        capital=48.2,
        contracts=1128.2,
        watch="Second-largest expenditure line in the report, with 10,747 positions against 12,525 authorized. Most of the dollars are benefits, not city payroll.",
    ),
    agency(
        id="NYCHH",
        acronym="H+H",
        name="NYC Health + Hospitals",
        portfolio="hhs",
        tie="liaison",
        one="The public hospital and clinic system, including the system's role in B-HEARD mental-health responses.",
        about="Health + Hospitals is a public benefit corporation, not a mayoral department. The Deputy Mayor for Health and Human Services keeps the liaison. Spending here is the system's own books.",
        exp=13189.9,
        auth=12092.1,
        positions=[("Personnel", "Personnel", 47236, 46917)],
        ot=("M", 291.4),
        revenue=13973.8,
        capital=259.6,
        watch="Reported spending is $13.2 billion against a $12.1 billion authorized figure, with $291 million in overtime. Patient revenue, not tax levy, is most of the money.",
    ),
    agency(
        id="NYPD",
        acronym="NYPD",
        name="New York City Police Department",
        portfolio="fdm",
        tie="supervise",
        reports_to_mayor=True,
        mayor_official="Commissioner",
        one="Patrol, investigations, and the police response to 911.",
        about="The First Deputy Mayor supervises the department, and Section 12 of the same order says the commissioner reports directly to the Mayor. Uniformed and civilian staff are published as separate rows.",
        exp=6909.1,
        auth=6893.3,
        positions=[
            ("Personnel (uniformed)", "Uniformed", 34018, 35025),
            ("Personnel (civilian)", "Civilian", 14326, 15548),
        ],
        ot=("M", 965.7),
        revenue=94.0,
        capital=379.3,
        watch="Overtime was $966 million, about 14 percent of expenditures. That is one number for the whole department. It does not say whether the cost sits in patrol, investigations, or events.",
    ),
    agency(
        id="NYCHA",
        acronym="NYCHA",
        name="New York City Housing Authority",
        portfolio="housing",
        tie="liaison",
        one="Public housing and the city's Section 8 voucher program.",
        about="NYCHA is an authority. The Deputy Mayor for Housing and Planning reviews it. The Deputy Mayor does not supervise it the way a commissioner is supervised. Federal subsidy is inside these figures.",
        exp=5600.9,
        auth=5568.8,
        positions=[("Personnel", "Personnel", 11612, 12265)],
        ot=("M", 195.7),
        revenue=5559.5,
        capital=755.1,
        watch="Spending and revenue are almost the same size, about $5.6 billion, with $196 million in overtime. City tax-levy money is only a slice of that.",
    ),
    agency(
        id="DHS",
        acronym="DHS",
        name="Department of Homeless Services",
        portfolio="hhs",
        tie="supervise",
        parent="Department of Social Services",
        one="Shelter and rehousing for people who are homeless.",
        about="DHS is the shelter side of the Department of Social Services, paired with HRA in Executive Order 23. The department's own headcount is small relative to the shelter system it pays for.",
        exp=4480.3,
        auth=4420.9,
        positions=[("Personnel", "Personnel", 1620, 2206)],
        ot=("M", 13.8),
        capital=39.5,
        contracts=4081.3,
        watch="Human-services contracts are $4.1 billion of $4.5 billion in expenditures. Headcount is 1,620 against 2,206 authorized. The cost driver is the shelter system, not city payroll.",
    ),
    agency(
        id="ACS",
        acronym="ACS",
        name="Administration for Children's Services",
        portfolio="hhs",
        tie="supervise",
        one="Child protection, foster care, juvenile justice, and a large share of early child care.",
        about="ACS investigates abuse and neglect, places children in foster care, and runs juvenile justice. Contracted providers do much of the day-to-day care.",
        exp=4431.0,
        auth=3832.1,
        positions=[("Personnel", "Personnel", 6514, 7114)],
        ot=("M", 39.2),
        revenue=8.8,
        capital=92.1,
        contracts=2962.3,
        watch="Spending of $4.4 billion sits well above the $3.8 billion authorized figure in the same table. Read both before calling either one the budget.",
    ),
    agency(
        id="FDNY",
        acronym="FDNY",
        name="Fire Department",
        portfolio="operations",
        tie="supervise",
        one="Firefighting and emergency medical response, including the Fire side of B-HEARD.",
        about="The department sits with Operations. B-HEARD, the mental-health response that pairs Fire EMTs with Health + Hospitals clinicians, is coordinated by the Deputy Mayor for Community Safety.",
        exp=2842.8,
        auth=2821.6,
        positions=[
            ("Personnel (uniformed)", "Uniformed", 10888, 11294),
            ("Personnel (civilian)", "Civilian", 6029, 6321),
        ],
        ot=("M", 564.0),
        revenue=134.7,
        capital=171.8,
        watch="Overtime was $564 million, about 20 percent of expenditures. That share is the number to understand before treating the department as a flat headcount story.",
    ),
    agency(
        id="DOHMH",
        acronym="DOHMH",
        name="Department of Health and Mental Hygiene",
        portfolio="hhs",
        tie="supervise",
        one="Disease control, restaurant inspections, mental health, and the city's vital records.",
        about="The department is the public-health authority. Clinics and hospitals are mostly Health + Hospitals. This agency sets rules, runs programs, and contracts for care.",
        exp=2840.2,
        auth=2907.9,
        positions=[("Personnel", "Personnel", 6418, 7435)],
        ot=("M", 21.0),
        revenue=36.4,
        capital=308.5,
        contracts=1301.8,
        watch="About $1.3 billion of the $2.8 billion is the human-services contract budget. Authorized positions are 7,435 against 6,418 filled in this table.",
    ),
    agency(
        id="DSNY",
        acronym="DSNY",
        name="Department of Sanitation",
        portfolio="operations",
        tie="supervise",
        one="Trash and recycling collection, street cleaning, and snow removal.",
        about="Sanitation is the most visible daily operation in the Operations portfolio. Uniformed sanitation workers and civilian staff are separate rows.",
        exp=2361.1,
        auth=2249.0,
        positions=[
            ("Personnel (uniformed)", "Uniformed", 8403, 7957),
            ("Personnel (civilian)", "Civilian", 1700, 1946),
        ],
        ot=("M", 322.7),
        revenue=21.1,
        capital=395.8,
        watch="Overtime was $323 million, about 14 percent of spending. Uniformed actual headcount, 8,403, is above the 7,957 authorized uniformed figure. That is not a vacancy.",
    ),
    agency(
        id="HPD",
        acronym="HPD",
        name="Department of Housing Preservation and Development",
        portfolio="housing",
        tie="supervise",
        one="Code enforcement, preservation of existing housing, and financing of new affordable homes.",
        about="HPD is the city's housing agency. The expense budget pays staff and programs. The homes themselves show up mainly as capital commitments and as deals with private and nonprofit partners.",
        exp=2041.8,
        auth=2023.1,
        positions=[("Personnel", "Personnel", 2498, 2891)],
        ot=("M", 4.3),
        revenue=160.5,
        capital=3129.4,
        watch="Capital commitments are $3.1 billion, larger than the $2.0 billion expense line. An expense-only card understates what the agency is doing.",
    ),
    agency(
        id="DCAS",
        acronym="DCAS",
        name="Department of Citywide Administrative Services",
        portfolio="operations",
        tie="supervise",
        one="City buildings, the fleet, civil-service exams, and shared goods and services for other agencies.",
        about="A large share of this budget is spent on behalf of the rest of government: leases, energy, supplies, and vehicles. It is not the cost of a back office alone.",
        exp=1981.4,
        auth=1845.9,
        positions=[("Personnel", "Personnel", 2139, 2598)],
        ot=("M", 23.3),
        revenue=69.3,
        capital=106.9,
        watch="Spending is $2.0 billion with 2,139 positions. Treat the dollars as citywide shared services until the units of appropriation are split out.",
    ),
    agency(
        id="DEP",
        acronym="DEP",
        name="Department of Environmental Protection",
        portfolio="operations",
        tie="supervise",
        one="Drinking water, sewers, and wastewater treatment.",
        about="DEP runs the water system from the upstate watershed to the treatment plants. Water and sewer charges, which pay for most of the system, are not the small revenue figure that appears under a stray indicator name in this file, so that figure is left off the card.",
        exp=1911.9,
        auth=1890.3,
        positions=[("Personnel", "Personnel", 5811, 6547)],
        ot=("M", 48.2),
        capital=2859.1,
        watch="Capital commitments are $2.9 billion, above the $1.9 billion expense line. The operating card is the staff and the plants, not the construction program.",
    ),
    agency(
        id="CUNY",
        acronym="CUNY",
        name="City University of New York",
        portfolio="fdm",
        tie="liaison",
        one="The city's public university system. Community colleges are a city relationship. Senior colleges are also a state one.",
        about="Executive Order 23 gives the First Deputy Mayor a liaison, not supervision. The MMR expenditure is the city's reported support, not CUNY's full budget.",
        exp=1643.6,
        auth=1627.8,
        positions=[("Personnel", "Personnel", 8148, 9379)],
        ot=("M", 4.2),
        revenue=249.4,
        watch="The table shows $1.6 billion and 8,148 positions. State funds and tuition sit outside this city line.",
    ),
    agency(
        id="DOT",
        acronym="DOT",
        name="Department of Transportation",
        portfolio="operations",
        tie="supervise",
        one="Streets, bridges, sidewalks, ferries, and the city's side of bus lanes and Vision Zero.",
        about="DOT controls the street. The MTA runs the subways and most buses. Paving, signals, and bridges are largely capital work, so the expense line is only part of the agency.",
        exp=1583.8,
        auth=1569.6,
        positions=[("Personnel", "Personnel", 5905, 6260)],
        ot=("M", 64.8),
        revenue=471.4,
        capital=2096.6,
        watch="Capital commitments are $2.1 billion, above $1.6 billion of expense. Revenue in the table is $471 million, mostly parking and concessions, not a farebox.",
    ),
    agency(
        id="DYCD",
        acronym="DYCD",
        name="Department of Youth and Community Development",
        portfolio="hhs",
        tie="supervise",
        one="After-school, summer, and community programs, mostly delivered by nonprofits.",
        about="DYCD designs and pays for youth programs. It does not employ the instructors in those programs. That is why the budget is large and the city headcount is not.",
        exp=1525.8,
        auth=1548.3,
        positions=[("Personnel", "Personnel", 711, 753)],
        ot=("K", 153),
        contracts=1311.8,
        watch="Human-services contracts are $1.3 billion of $1.5 billion in spending, with 711 city positions. Efficiency here is contract design, not overtime.",
    ),
    agency(
        id="DOC",
        acronym="DOC",
        name="Department of Correction",
        portfolio="fdm",
        tie="supervise",
        one="City jails, including Rikers Island, during the long move to borough-based jails.",
        about="The First Deputy Mayor supervises Correction. A separate office coordinates the borough-based jails transition. That office has no MMR chapter of its own.",
        exp=1379.9,
        auth=1400.5,
        positions=[
            ("Personnel (uniformed)", "Uniformed", 5702, 7060),
            ("Personnel (civilian)", "Civilian", 1659, 1833),
        ],
        ot=("M", 369.1),
        revenue=12.8,
        capital=2153.3,
        watch="Overtime was $369 million, about 27 percent of expenditures. Uniformed staff are 5,702 against 7,060 authorized. Capital commitments for the jail program are $2.2 billion, larger than the expense budget.",
    ),
    agency(
        id="OTI",
        acronym="OTI",
        name="Office of Technology and Innovation",
        portfolio="operations",
        tie="supervise",
        one="Citywide technology, cybersecurity, and the systems behind 311 and many agency applications.",
        about="OTI consolidates what used to be separate technology shops. Its budget buys staff, vendors, and licenses that other agencies use.",
        exp=982.6,
        auth=967.2,
        positions=[("Personnel", "Personnel", 1499, 1580)],
        ot=("K", 2724),
        revenue=131.4,
        watch="Overtime is published in thousands of dollars, $2.7 million, not millions. Reading the raw 2,724 as millions would invent a crisis.",
    ),
    agency(
        id="DPR",
        acronym="DPR",
        name="Department of Parks and Recreation",
        portfolio="operations",
        tie="supervise",
        one="Parks, playgrounds, recreation centers, and the street trees the city plants and prunes.",
        about="Parks work is seasonal. The MMR headcount therefore mixes full-time staff with full-time equivalents, including part-year jobs.",
        exp=724.2,
        auth=709.9,
        positions=[
            ("Personnel (Total FT and FTE)", "Full-time and FTE", 7271, 8144),
            ("Full-time equivalent (FTE) personnel", "Of which, FTE", 2429, 3002),
        ],
        position_mode="dpr",
        ot=("M", 18.4),
        revenue=92.9,
        capital=660.9,
        watch="The headline headcount, 7,271, includes full-time equivalents. Do not rank it against a full-time-only agency. Capital commitments are $661 million, close to the whole expense budget.",
    ),
    agency(
        id="DFTA",
        acronym="DFTA",
        name="Department for the Aging",
        portfolio="hhs",
        tie="supervise",
        one="Senior centers, home-delivered meals, and case management for older adults.",
        about="DFTA funds a network of providers. City staff plan and monitor. The meals and the centers are mostly contracted.",
        exp=609.8,
        auth=620.2,
        positions=[("Personnel", "Personnel", 320, 383)],
        revenue=1.3,
        capital=9.2,
        contracts=521.1,
        watch="Contracts are $521 million of $610 million in spending, with 320 city positions. The card to improve is the provider network, not the headcount.",
    ),
    agency(
        id="LIBS",
        acronym="LIBS",
        name="Public Libraries",
        portfolio="economic",
        tie="liaison",
        assignment="inferred",
        one="The New York Public Library, Brooklyn Public Library, and Queens Public Library, reported as one chapter.",
        about="The three systems are independent nonprofits with their own boards. The city appropriates their operating support. Executive Order 23 does not name them as an agency. It tells Economic Justice to keep a liaison with cultural organizations, including libraries. This card uses that sentence.",
        exp=539.8,
        auth=527.3,
        positions=[("Personnel", "Personnel", 4272, 4311)],
        capital=163.3,
        watch="One MMR row covers three systems and 4,272 positions. A useful next card splits the appropriation by system.",
    ),
    agency(
        id="DOF",
        acronym="DOF",
        name="Department of Finance",
        portfolio="fdm",
        tie="supervise",
        one="Property tax, business taxes, parking tickets, and the collection of money owed to the city.",
        about="Finance is a revenue agency under the First Deputy Mayor. What it collects is not the cost of running it. The two numbers belong on the same card and should not be swapped.",
        exp=375.4,
        auth=387.6,
        positions=[("Personnel", "Personnel", 1794, 2066)],
        ot=("K", 1994),
        revenue=1256.7,
        watch="The expense line is $375 million. Revenue reported in the same table is $1.3 billion. Overtime is in thousands: about $2.0 million.",
    ),
    agency(
        id="SBS",
        acronym="SBS",
        name="Department of Small Business Services",
        portfolio="economic",
        tie="supervise",
        one="Workforce programs, services for small businesses, and the Office of Nightlife.",
        about="SBS sits with Economic Justice. Workforce contracts and commercial-district work are the bulk of the budget. The department's own staff is a few hundred people.",
        exp=331.3,
        auth=366.7,
        positions=[("Personnel", "Personnel", 318, 433)],
        ot=("K", 92),
        revenue=0.3,
        contracts=59.5,
        watch="318 positions against 433 authorized, the widest relative gap among the mid-size agencies on this list. The human-services contract line is only $60 million, so most of the $331 million is other than that contract category.",
    ),
    agency(
        id="LAW",
        acronym="LAW",
        name="Law Department",
        portfolio="counsel",
        tie="liaison",
        reports_to_mayor=True,
        mayor_official="Corporation Counsel",
        one="The city's lawyers. The Corporation Counsel represents the city in court and advises agencies.",
        about="Section 12 says the Corporation Counsel reports to the Mayor. Executive Order 23 also gives the Chief Counsel a liaison with the department. Both are true, and they are not the same relationship.",
        exp=329.9,
        auth=327.0,
        positions=[("Personnel", "Personnel", 1544, 1687)],
        ot=("K", 2457),
        revenue=45.9,
        watch="Overtime is published in thousands, about $2.5 million. Judgment and settlement costs are not this expense line.",
    ),
    agency(
        id="DCLA",
        acronym="DCLA",
        name="Department of Cultural Affairs",
        portfolio="economic",
        tie="supervise",
        one="City funding for museums, theaters, and other cultural organizations, plus a small staff to run the programs.",
        about="Cultural Affairs is a grantmaker. The institutions it funds employ their own staff. The department's headcount is the people who administer that support.",
        exp=300.1,
        auth=300.7,
        positions=[("Personnel", "Personnel", 63, 71)],
        capital=350.7,
        watch="Sixty-three positions administer $300 million of expense and $351 million of capital commitments. The card is about the cultural network, not a large city workforce.",
    ),
    agency(
        id="BOE",
        acronym="BOE",
        name="Board of Elections",
        portfolio="staff",
        tie="liaison",
        one="Runs city elections. A board created by state law, not a mayoral agency.",
        about="The Chief of Staff maintains the liaison. The Mayor does not appoint the commissioners the way agency heads are appointed. Election calendars swing the budget from year to year.",
        exp=273.8,
        auth=214.4,
        positions=[("Personnel", "Personnel", 890, 652)],
        ot=("M", 8.3),
        watch="Spending of $274 million is above the $214 million authorized figure, and actual positions, 890, are above 652 authorized. Poll-worker and election-year costs do not behave like a steady agency.",
    ),
    agency(
        id="DOB",
        acronym="DOB",
        name="Department of Buildings",
        portfolio="housing",
        tie="supervise",
        one="Building permits, inspections, and construction safety.",
        about="Buildings decides what can be built and whether a site is safe. Fee revenue is large relative to the department's own spending, because applicants pay for the permits.",
        exp=202.3,
        auth=233.1,
        positions=[("Personnel", "Personnel", 1695, 1883)],
        ot=("M", 3.0),
        revenue=481.3,
        watch="Revenue in the table is $481 million, more than double the $202 million expense line. The department can look small on spending and large on the construction market it regulates.",
    ),
    agency(
        id="DDC",
        acronym="DDC",
        name="Department of Design and Construction",
        portfolio="operations",
        tie="supervise",
        one="Designs and builds public buildings and infrastructure for other agencies.",
        about="DDC is a client-service agency. Its own expense budget pays its staff. The projects it manages are capital, booked for the agencies that will own them.",
        exp=175.8,
        auth=178.9,
        positions=[("Personnel", "Personnel", 1165, 1217)],
        ot=("M", 1.1),
        capital=4196.3,
        capital_label="Capital commitments managed for other agencies",
        watch="The expense line is $176 million. Capital commitments managed for client agencies are $4.2 billion. Using the expense line alone makes the agency look like a small shop.",
    ),
    agency(
        id="OCME",
        acronym="OCME",
        name="Office of Chief Medical Examiner",
        portfolio="hhs",
        tie="supervise",
        one="Forensic pathology, death investigation, and the city's DNA laboratory.",
        about="OCME determines cause and manner of death in cases that fall under its jurisdiction. It is a health-and-human-services agency with a public-safety workload.",
        exp=123.7,
        auth=127.9,
        positions=[("Personnel", "Personnel", 773, 906)],
        ot=("M", 7.1),
        watch="Overtime is $7.1 million on a $124 million budget, about 6 percent. The lab and the morgue do not scale down when caseloads spike.",
    ),
    agency(
        id="DOP",
        acronym="DOP",
        name="Department of Probation",
        portfolio="fdm",
        tie="supervise",
        one="Supervision in the community for people sentenced to probation.",
        about="Probation is the alternative to jail for the cases the courts assign to it. It reports through the First Deputy Mayor, beside Correction and the police.",
        exp=119.6,
        auth=116.0,
        positions=[("Personnel", "Personnel", 833, 1095)],
        ot=("K", 2995),
        watch="833 positions against 1,095 authorized. Overtime is published in thousands, about $3.0 million, not $3 billion.",
    ),
    agency(
        id="NYCEM",
        acronym="NYCEM",
        name="New York City Emergency Management",
        portfolio="operations",
        tie="supervise",
        one="Plans for emergencies and coordinates the city when one is underway.",
        about="The order calls it the Office of Emergency Management. The MMR uses New York City Emergency Management. It is a coordination agency. Other departments bring the trucks, the hospital beds, and the officers.",
        exp=85.4,
        auth=89.3,
        positions=[("Personnel", "Personnel", 238, 246)],
        ot=("K", 872),
        watch="A small standing staff, 238 people and an $85 million budget. The cost of a response shows up in the agencies that execute it.",
    ),
    agency(
        id="DCWP",
        acronym="DCWP",
        name="Department of Consumer and Worker Protection",
        portfolio="economic",
        tie="supervise",
        one="Licenses businesses and enforces consumer and workplace laws, including paid safe and sick leave.",
        about="DCWP is the regulator for a long list of licenses and for worker-protection rules that used to sit in several places. It sits with Economic Justice.",
        exp=83.9,
        auth=85.5,
        positions=[("Personnel", "Personnel", 430, 485)],
        ot=("K", 118),
        revenue=20.3,
        watch="430 positions on an $84 million budget. License revenue is $20 million in this table, so the agency is not self-financing.",
    ),
    agency(
        id="OATH",
        acronym="OATH",
        name="Office of Administrative Trials and Hearings",
        portfolio="counsel",
        tie="supervise",
        one="The city's administrative court for summonses and for hearings that city employees and licensees are entitled to.",
        about="OATH, including the Environmental Control Board, is the one agency the Chief Counsel supervises directly. Most city enforcement ends in a hearing here rather than in state court.",
        exp=75.3,
        auth=81.8,
        positions=[("Personnel", "Personnel", 490, 595)],
        ot=("K", 10),
        revenue=189.8,
        watch="Revenue of $190 million is more than double the $75 million expense line. Fines collected are not the cost of the tribunal.",
    ),
    agency(
        id="DOI",
        acronym="DOI",
        name="Department of Investigation",
        portfolio="counsel",
        tie="liaison",
        reports_to_mayor=True,
        mayor_official="Commissioner",
        one="Investigates corruption and misconduct by city employees, contractors, and people who do business with the city.",
        about="Section 12 says the commissioner reports to the Mayor. The Chief Counsel maintains a liaison. DOI is independent in statute in ways a normal mayoral agency is not. This card does not try to settle that tension.",
        exp=65.6,
        auth=64.1,
        positions=[("Personnel", "Personnel", 282, 314)],
        ot=("K", 107),
        revenue=4.1,
        watch="A $66 million agency with 282 positions. Its effect is the cases, which the expenditure line does not measure.",
    ),
    agency(
        id="311",
        acronym="311",
        name="311 Customer Service Center",
        portfolio="staff",
        tie="liaison",
        assignment="inferred",
        one="The phone, app, and web front door for non-emergency city services.",
        about="311 takes the request and sends it to the agency that does the work. Executive Order 23 does not name 311. It places the Mayor's Office of Operations, which publishes the MMR, under the Chief of Staff. This card follows that placement and labels it as inferred.",
        exp=64.2,
        auth=66.3,
        positions=[("Personnel", "Personnel", 309, 394)],
        ot=("K", 239),
        watch="309 positions against 394 authorized, on a $64 million budget. The service requests themselves are answered by other agencies.",
    ),
    agency(
        id="TLC",
        acronym="TLC",
        name="Taxi and Limousine Commission",
        portfolio="economic",
        tie="supervise",
        one="Licenses and regulates yellow cabs, green cabs, and for-hire vehicles and their drivers.",
        about="TLC sets the rules for the vehicles that are not the MTA. License and summons revenue is a real part of the agency's public numbers.",
        exp=61.8,
        auth=62.0,
        positions=[("Personnel", "Personnel", 468, 580)],
        ot=("K", 809),
        revenue=70.2,
        watch="Revenue of $70 million exceeds the $62 million expense line. Authorized positions are 580 against 468 filled.",
    ),
    agency(
        id="DCP",
        acronym="DCP",
        name="Department of City Planning",
        portfolio="housing",
        tie="supervise",
        one="Zoning, land-use review, and the city's official demographic and planning data.",
        about="City Planning staffs the City Planning Commission. A rezoning changes what can be built. The department's own budget is small next to the private investment those decisions unlock.",
        exp=52.6,
        auth=58.2,
        positions=[("Personnel", "Personnel", 324, 388)],
        ot=("K", 32),
        revenue=4.1,
        watch="324 positions and a $53 million budget. The housing numbers people quote from rezonings are not in this expense line.",
    ),
    agency(
        id="CCRB",
        acronym="CCRB",
        name="Civilian Complaint Review Board",
        portfolio="fdm",
        tie="liaison",
        one="Investigates civilian complaints of misconduct by police officers.",
        about="CCRB is independent of the police department. The First Deputy Mayor's relationship in Executive Order 23 is a liaison. The board's jurisdiction and the commissioner's discipline power are different steps.",
        exp=29.4,
        auth=29.4,
        positions=[("Personnel", "Personnel", 245, 273)],
        ot=("K", 415),
        watch="A $29 million agency. Its output is investigations and findings, which this resources table does not carry. Those live in the performance chapter.",
    ),
    agency(
        id="DORIS",
        acronym="DORIS",
        name="Department of Records and Information Services",
        portfolio="operations",
        tie="supervise",
        one="The municipal archives and the rules for how agencies keep records.",
        about="DORIS preserves the historical record and sets retention schedules. It is a small operations agency with a citywide rule to enforce.",
        exp=16.5,
        auth=16.1,
        positions=[("Personnel", "Personnel", 55, 53)],
        watch="Fifty-five positions and a $16 million budget. Actual headcount is slightly above the authorized figure in this edition.",
    ),
    agency(
        id="CCHR",
        acronym="CCHR",
        name="City Commission on Human Rights",
        portfolio="economic",
        tie="supervise",
        one="Enforces the city human-rights law against discrimination in work, housing, and public places.",
        about="The commission investigates complaints and can order remedies. It sits with Economic Justice, next to worker protection, because the order treats discrimination as an economic question as well as a legal one.",
        exp=13.3,
        auth=15.4,
        positions=[("Personnel", "Personnel", 109, 145)],
        ot=("K", 4),
        watch="109 positions against 145 authorized, on a $13 million budget. Caseload, not spending, is the performance question.",
    ),
    agency(
        id="BIC",
        acronym="BIC",
        name="Business Integrity Commission",
        portfolio="fdm",
        tie="supervise",
        one="Regulates private trash hauling, the public wholesale markets, and shipboard gambling.",
        about="BIC licenses industries with a history of organized-crime influence. It is one of the smaller agencies the First Deputy Mayor supervises directly.",
        exp=9.2,
        auth=9.2,
        positions=[("Personnel", "Personnel", 67, 73)],
        ot=("K", 96),
        revenue=13.0,
        watch="Spending is $9.2 million. License revenue in the same table is $13.0 million. The agency is small and, on these figures, more than covers its expense line.",
    ),
    agency(
        id="LPC",
        acronym="LPC",
        name="Landmarks Preservation Commission",
        portfolio="housing",
        tie="supervise",
        one="Designates landmarks and historic districts and reviews changes to them.",
        about="LPC decides what is protected and then permits alterations. It sits with Housing and Planning because landmark rules shape what can be built.",
        exp=9.0,
        auth=9.0,
        positions=[("Personnel", "Personnel", 73, 81)],
        ot=("K", 7),
        revenue=11.4,
        watch="A $9 million agency whose decisions move private construction costs that never appear in its budget. Permit revenue in the table is $11 million.",
    ),
    agency(
        id="DVS",
        acronym="DVS",
        name="Department of Veterans' Services",
        portfolio="hhs",
        tie="supervise",
        one="Connects veterans and their families to benefits, housing help, and city services.",
        about="DVS is a navigation agency. The benefits themselves are mostly federal, or sit in HRA, HPD, and other departments. The department's job is to get people to those doors.",
        exp=7.3,
        auth=7.7,
        positions=[("Personnel", "Personnel", 45, 50)],
        watch="The smallest expenditure line in the report: $7.3 million and 45 positions. Impact depends on other agencies' programs.",
    ),
    agency(
        id="EDC",
        acronym="EDC",
        name="New York City Economic Development Corporation",
        portfolio="economic",
        tie="supervise",
        one="The nonprofit that does the city's economic-development deals, asset management, and many capital projects.",
        about="Executive Order 23 says the Deputy Mayor for Economic Justice supervises EDC as provided in the contracts between the city and EDC. The MMR publishes headcount and capital commitments, and does not publish an expenditures row.",
        positions=[("Personnel", "Personnel", 599, 625)],
        capital=341.0,
        watch="599 positions are in the table. There is no expenditures line to put beside them. EDC's own financial statements are the missing budget.",
    ),
    agency(
        id="SCA",
        acronym="SCA",
        name="School Construction Authority",
        portfolio="fdm",
        tie="liaison",
        one="Builds and renovates public school buildings.",
        about="SCA is an authority. The First Deputy Mayor's relationship is a liaison, listed alongside CUNY. The MMR publishes headcount and a large capital-commitment line, not an operating-expenditure row.",
        positions=[("Personnel", "Personnel", 977, 1059)],
        capital=3931.0,
        watch="Capital commitments are $3.9 billion. Headcount is 977. Without the capital line, the authority looks like a mid-size office.",
    ),
]


def money_phrase(millions: float | None) -> str:
    if millions is None:
        return "not published in this table"
    if millions >= 1000:
        return f"${millions / 1000:.1f} billion"
    if millions >= 100:
        return f"${millions:.0f} million"
    return f"${millions:.1f} million"


def people_phrase(value: int) -> str:
    return f"{value:,}"


def parse_number(value: str | None) -> float | None:
    if value is None:
        return None
    text = value.strip()
    if text in {"", "*", "NA", "N/A", "-"}:
        return None
    text = re.sub(r"[$,%]", "", text).replace(",", "")
    try:
        return float(text)
    except ValueError:
        return None


def load_sibling() -> dict[str, dict[str, tuple[float | None, float | None]]]:
    if not SIBLING.exists():
        print(f"Sibling MMR file not found, skipped check: {SIBLING}")
        return {}
    tables: dict[str, dict[str, tuple[float | None, float | None]]] = {}
    with SIBLING.open(newline="") as handle:
        for row in csv.DictReader(handle):
            if row["reporting_fiscal_year"] != "2026":
                continue
            agency_id = row["agency"]
            tables.setdefault(agency_id, {})[row["resource_indicators"]] = (
                parse_number(row["current_fy_projected_actual"]),
                parse_number(row["current_fy_authorized_budget"]),
            )
    return tables


def close(left: float | None, right: float | None) -> bool:
    if left is None or right is None:
        return left is None and right is None
    return abs(left - right) < 0.05


def check_against_source(tables: dict[str, dict[str, tuple[float | None, float | None]]]) -> None:
    if not tables:
        return
    problems: list[str] = []
    seen = set()
    for item in AGENCIES:
        agency_id = str(item["id"])
        seen.add(agency_id)
        rows = tables.get(agency_id)
        if rows is None:
            problems.append(f"{agency_id}: missing from source")
            continue
        exp_row = rows.get("Expenditures ($000,000)")
        exp = item.get("exp")
        auth = item.get("auth")
        if exp is None and exp_row is not None and exp_row[0] is not None:
            problems.append(f"{agency_id}: source has expenditures {exp_row[0]}")
        if exp is not None:
            if exp_row is None or not close(exp_row[0], float(exp)) or not close(exp_row[1], float(auth)):
                problems.append(f"{agency_id}: expenditures {exp}/{auth} vs {exp_row}")
        for label, _display, actual, authorized in item["positions"]:
            row = rows.get(label)
            if row is None or not close(row[0], float(actual)) or not close(row[1], float(authorized)):
                problems.append(f"{agency_id}: {label} {actual}/{authorized} vs {row}")
        ot = item.get("ot")
        if ot:
            kind, raw = ot
            label = "Overtime paid ($000,000)" if kind == "M" else "Overtime paid ($000)"
            row = rows.get(label)
            if row is None or not close(row[0], float(raw)):
                problems.append(f"{agency_id}: overtime {raw} vs {row}")
        for field, label in (
            ("revenue", "Revenues ($000,000)"),
            ("contracts", "Human services contract budget ($000,000)"),
        ):
            expected = item.get(field)
            row = rows.get(label)
            if expected is None:
                continue
            if row is None or not close(row[0], float(expected)):
                problems.append(f"{agency_id}: {field} {expected} vs {row}")
        capital = item.get("capital")
        if capital is not None:
            label = (
                "Capital commitments (capital projects managed for client agencies) ($000,000)"
                if agency_id == "DDC"
                else "Capital commitments ($000,000)"
            )
            row = rows.get(label)
            if row is None or not close(row[0], float(capital)):
                problems.append(f"{agency_id}: capital {capital} vs {row}")
    extra = sorted(set(tables) - seen)
    if extra:
        problems.append("in source but not in cards: " + ", ".join(extra))
    if problems:
        raise SystemExit("MMR check failed:\n" + "\n".join(problems))
    print(f"Checked {len(AGENCIES)} agencies against {SIBLING.name}")


def position_block(item: dict) -> dict:
    lines = [
        {"label": display, "sourceLabel": source, "actual": actual, "authorized": authorized}
        for source, display, actual, authorized in item["positions"]
    ]
    if item.get("position_mode") == "dpr":
        headline = lines[0]
        note = (
            "The headline is the MMR row Personnel (Total FT and FTE). "
            "The FTE row is included in that total, not added to it."
        )
        return {
            "actual": headline["actual"],
            "authorized": headline["authorized"],
            "lines": lines[1:],
            "note": note,
            "comparable": False,
        }
    actual = sum(line["actual"] for line in lines)
    authorized = sum(line["authorized"] for line in lines)
    note = None
    if len(lines) > 1:
        note = "Headline adds the civilian and uniformed rows."
    return {
        "actual": actual,
        "authorized": authorized,
        "lines": lines if len(lines) > 1 else [],
        "note": note,
        "comparable": True,
    }


def overtime_block(item: dict) -> dict | None:
    ot = item.get("ot")
    if not ot:
        return None
    kind, raw = ot
    if raw == 0:
        return None
    millions = float(raw) if kind == "M" else float(raw) / 1000
    return {"millions": round(millions, 3), "publishedAs": "millions" if kind == "M" else "thousands"}


def reporting_note(item: dict) -> str:
    portfolio = next(p for p in PORTFOLIOS if p["id"] == item["portfolio"])
    label = portfolio["label"]
    if item.get("assignment") == "inferred":
        return str(item["about"])
    if item["tie"] == "supervise":
        sentence = f"Executive Order 23 says the {label} supervises and coordinates this agency."
    else:
        sentence = (
            f"Executive Order 23 says the {label} maintains a liaison with this agency. "
            "A liaison is not day-to-day supervision."
        )
    if item.get("parent"):
        sentence += (
            f" The order names the {item['parent']}, and says that department includes "
            "Homeless Services and the Human Resources Administration."
        )
    if item.get("reports_to_mayor"):
        official = item.get("mayor_official", "agency head")
        sentence += f" Section 12 also says the {official} reports directly to the Mayor."
    if item["id"] == "EDC":
        sentence += " The order ties that supervision to the contracts between the city and EDC."
    return sentence


def gaps_for(item: dict, positions: dict, overtime: dict | None) -> list[str]:
    gaps = [
        "Add the critical performance indicators from this agency's MMR chapter, with the direction each one is supposed to move.",
    ]
    exp = item.get("exp")
    contracts = item.get("contracts")
    capital = item.get("capital")
    if exp and contracts and contracts / exp >= 0.4:
        gaps.append("Split the human-services contract budget by program. The total is too large to be the last word.")
    elif capital and (exp is None or capital > exp):
        gaps.append("Show capital projects beside expense, by who the project is for.")
    elif overtime and exp and overtime["millions"] / exp >= 0.1:
        gaps.append("Break overtime out by unit before treating it as one department-wide number.")
    elif item["id"] in {"NYCHH", "NYCHA", "EDC", "SCA", "CUNY"}:
        gaps.append("Bring in the authority's own financial statement. This MMR row is not the whole enterprise.")
    else:
        gaps.append("Separate city funds from state and federal funds inside the expenditure line.")
    if not positions["comparable"]:
        gaps.append("Publish a full-time-only headcount so Parks can be compared with other agencies.")
    if item.get("assignment") == "inferred":
        gaps.append("Confirm the reporting line against the current org chart. This placement is inferred from the order, not named in it.")
    return gaps[:3]


def build_agency(item: dict) -> dict:
    positions = position_block(item)
    overtime = overtime_block(item)
    return {
        "id": item["id"],
        "acronym": item["acronym"],
        "name": item["name"],
        "portfolio": item["portfolio"],
        "tie": item["tie"],
        "assignment": item.get("assignment", "named"),
        "reportsToMayor": bool(item.get("reports_to_mayor")),
        "parent": item.get("parent"),
        "oneLiner": item["one"],
        "about": item["about"] if item.get("assignment") != "inferred" else item["one"],
        "reportingNote": reporting_note(item),
        "expendituresMillions": item.get("exp"),
        "authorizedMillions": item.get("auth"),
        "positions": positions,
        "overtime": overtime,
        "revenueMillions": item.get("revenue"),
        "capitalMillions": item.get("capital"),
        "capitalLabel": item.get("capital_label", "Capital commitments" if item.get("capital") is not None else None),
        "contractMillions": item.get("contracts"),
        "watch": item["watch"],
        "gaps": gaps_for(item, positions, overtime),
    }


def write_markdown(cards: list[dict]) -> None:
    KNOW.mkdir(parents=True, exist_ok=True)
    labels = {p["id"]: p["label"] for p in PORTFOLIOS}
    for card in cards:
        lines = [
            f"# {card['acronym']} · {card['name']}",
            "",
            f"**In one line:** {card['oneLiner']}",
            "",
            "## Where it sits",
            "",
            card["reportingNote"],
            "",
            "## What it does",
            "",
            card["about"] if card["assignment"] != "inferred" else card["oneLiner"],
            "",
            "## Fiscal 2026, from the MMR resources table",
            "",
            f"- Expenditures: {money_phrase(card['expendituresMillions'])}",
            f"- Authorized budget in the same row: {money_phrase(card['authorizedMillions'])}",
            f"- Positions, actual: {people_phrase(card['positions']['actual'])}",
            f"- Positions, authorized: {people_phrase(card['positions']['authorized'])}",
        ]
        if card["positions"]["note"]:
            lines.append(f"- Headcount note: {card['positions']['note']}")
        for line in card["positions"]["lines"]:
            lines.append(
                f"- {line['label']}: {people_phrase(line['actual'])} actual, {people_phrase(line['authorized'])} authorized"
            )
        if card["overtime"]:
            unit = "millions" if card["overtime"]["publishedAs"] == "millions" else "thousands, converted here to millions"
            lines.append(f"- Overtime: {money_phrase(card['overtime']['millions'])} (published in {unit})")
        if card["contractMillions"] is not None:
            lines.append(f"- Human-services contract budget: {money_phrase(card['contractMillions'])}")
        if card["capitalMillions"] is not None:
            lines.append(f"- {card['capitalLabel']}: {money_phrase(card['capitalMillions'])}")
        if card["revenueMillions"] is not None:
            lines.append(f"- Revenue in the resources table: {money_phrase(card['revenueMillions'])}")
        lines += [
            "",
            "## What the number is saying",
            "",
            card["watch"],
            "",
            "## What would make this card better",
            "",
        ]
        lines.extend(f"- {gap}" for gap in card["gaps"])
        lines += [
            "",
            "## Sources",
            "",
            "- [Fiscal 2026 Mayor's Management Report](https://www.nyc.gov/assets/operations/downloads/pdf/mmr2026/2026_mmr.pdf), agency resources chapter for this agency.",
            "- [MMR Agency Resources on NYC Open Data](https://data.cityofnewyork.us/City-Government/Mayor-s-Management-Report-Agency-Resources/4qmi-txnk) (`4qmi-txnk`), reporting fiscal year 2026.",
            "- [Executive Order 23](https://www.nyc.gov/mayors-office/news/2026/09/executive-order-no--23), September 8, 2026, for the reporting line.",
            "",
            f"Portfolio: {labels[card['portfolio']]}.",
            "",
        ]
        (KNOW / f"{card['id'].lower()}.md").write_text("\n".join(lines), encoding="utf-8")

    index = [
        "# Agency knowledge cards",
        "",
        "One card per agency in the Fiscal 2026 Mayor's Management Report that publishes a resources row. Reporting lines follow Executive Order 23. Inferred placements say so on the card.",
        "",
        "| Acronym | Agency | Portfolio |",
        "|---|---|---|",
    ]
    for card in cards:
        index.append(
            f"| [{card['acronym']}](agencies/{card['id'].lower()}.md) | {card['name']} | {labels[card['portfolio']]} |"
        )
    index.append("")
    index.append("The public site reads `data/agencies.json`, which this folder is generated from. Edit `scripts/build_cards.py` and rerun it. Do not edit the generated cards by hand.")
    index.append("")
    (ROOT / "knowledge" / "README.md").write_text("\n".join(index), encoding="utf-8")


def main() -> None:
    if len(AGENCIES) != 45:
        raise SystemExit(f"Expected 45 agencies, found {len(AGENCIES)}")
    ids = [item["id"] for item in AGENCIES]
    if len(ids) != len(set(ids)):
        raise SystemExit("Duplicate agency id")
    check_against_source(load_sibling())
    cards = [build_agency(item) for item in AGENCIES]
    payload = {
        "meta": {
            "fiscalYear": 2026,
            "window": "July 1, 2025 to June 30, 2026",
            "order": "Executive Order 23, September 8, 2026",
            "source": "Mayor's Management Report agency resources, NYC Open Data 4qmi-txnk",
            "disclaimer": "Public figures for a first reading. Not an audit, and not the adopted budget.",
        },
        "portfolios": PORTFOLIOS,
        "agencies": cards,
    }
    OUT_JSON.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    write_markdown(cards)
    print(f"Wrote {OUT_JSON} and {len(cards)} cards")


if __name__ == "__main__":
    main()
