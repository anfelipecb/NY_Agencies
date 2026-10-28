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
        "id": "mayor",
        "label": "Office of the Mayor",
        "blurb": "The Mayor's own appropriation. An asterisk with no dollar is an office the order names and the budget does not price. It is not an extra amount on top of this one.",
    },
    {
        "id": "fdm",
        "label": "First Deputy Mayor",
        "blurb": "Police, public schools, correction, probation, finance, business integrity, budget, labor relations, and criminal justice. Child care, antisemitism, and the borough-based jails transition are named in the order and have no separate amount. Liaison to CUNY, the Civilian Complaint Review Board, the School Construction Authority, and the Board of Correction.",
    },
    {
        "id": "operations",
        "label": "Deputy Mayor for Operations",
        "blurb": "Sanitation, streets, water, parks, fire, emergency management, design and construction, citywide administration, records, technology, and contract services.",
    },
    {
        "id": "hhs",
        "label": "Deputy Mayor for Health and Human Services",
        "blurb": "Health, benefits, child welfare, shelter, aging, youth, veterans, the medical examiner, and the office for people with disabilities. Homeless Services and HRA sit inside Social Services. Liaison to Health + Hospitals.",
    },
    {
        "id": "housing",
        "label": "Deputy Mayor for Housing and Planning",
        "blurb": "Buildings, city planning, housing preservation and development, and landmarks. Liaison to NYCHA.",
    },
    {
        "id": "economic",
        "label": "Deputy Mayor for Economic Justice",
        "blurb": "Human rights, consumer and worker protection, cultural affairs, small business, taxis, racial equity, and the Economic Development Corporation. Libraries are a liaison, not a named agency.",
    },
    {
        "id": "counsel",
        "label": "Chief Counsel",
        "blurb": "Administrative hearings at OATH. Liaison to Investigation, the Law Department, and the Conflicts of Interest Board. Investigation and the Law Department also report to the Mayor.",
    },
    {
        "id": "staff",
        "label": "Chief of Staff",
        "blurb": "The Mayor's Office of Operations, which publishes the Management Report, and 311. Several other offices the order names here have no separate amount. Liaison to Elections and the Campaign Finance Board. The order does not name 311.",
    },
    {
        "id": "comms",
        "label": "Director of Communications",
        "blurb": "Communications, ethnic and community media, and the press office. The adopted budget names communications inside the Office of the Mayor and does not price the pieces separately.",
    },
    {
        "id": "safety",
        "label": "Deputy Mayor for Community Safety",
        "blurb": "The order names an Office of Community Safety. The adopted budget does not price that office on its own. It does place the office to combat domestic violence inside the Office of the Mayor. B-HEARD is operated by Fire and Health + Hospitals.",
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

# Offices Executive Order 23 names that have no MMR chapter.
# Dollars are Fiscal 2026 adopted personal service plus other than personal service,
# in millions. Positions are the adopted full-time count on the personal-service unit.
# Source: Expense, Revenue, Contract Budget, Adopted FY2026 (erc6-25.pdf).
ADOPTED = [
    agency(
        id="OMB",
        acronym="OMB",
        name="Office of Management and Budget",
        portfolio="fdm",
        tie="supervise",
        one="Prepares the expense, revenue, and capital budgets and watches what agencies spend.",
        about="The First Deputy Mayor supervises the Office of Management and Budget. It has no chapter in the Mayor's Management Report. These figures are its own office, not the city budget it writes.",
        adopted=66.747,
        positions=455,
        units="Mayoralty units 040 and 041",
        watch="Personal service is $55.4 million and other than personal service is $11.3 million. Fringe benefits are appropriated in the miscellaneous budget, not in this unit. Do not compare this adopted appropriation with an agency's MMR expenditure.",
    ),
    agency(
        id="OLR",
        acronym="OLR",
        name="Office of Labor Relations",
        portfolio="fdm",
        tie="supervise",
        one="Negotiates city labor agreements and administers employee benefit funds.",
        about="The First Deputy Mayor supervises the Office of Labor Relations. It sits inside the Mayoralty in the adopted budget and has no MMR chapter.",
        adopted=23.539,
        positions=173,
        units="Mayoralty units 061 and 062",
        watch="Personal service is $16.9 million and other than personal service is $6.7 million. The cost of the contracts this office negotiates is not in this unit.",
    ),
    agency(
        id="MOCJ",
        acronym="MOCJ",
        name="Mayor's Office of Criminal Justice",
        portfolio="fdm",
        tie="supervise",
        one="Coordinates criminal justice policy, and pays for indigent defense and alternatives to incarceration.",
        about="Executive Order 23 says the First Deputy Mayor supervises the Mayor's Office of Criminal Justice, including the Office of Special Enforcement. The adopted budget publishes it as agency 128, the Office of Criminal Justice.",
        adopted=868.318,
        positions=74,
        units="Agency 128, units 001 through 006",
        watch="The office itself is $9.3 million, with 68 positions, and Special Enforcement is $2.2 million, with 6 positions. Indigent defense is $525.0 million and criminal justice programs are $331.8 million. Those two contract lines are most of the tile.",
    ),
    agency(
        id="BOC",
        acronym="BOC",
        name="Board of Correction",
        portfolio="fdm",
        tie="liaison",
        one="Sets and enforces minimum standards for people in city jails.",
        about="The First Deputy Mayor maintains a liaison with the Board of Correction. It is a city agency with its own adopted budget and no MMR chapter.",
        adopted=4.086,
        positions=33,
        units="Agency 073, units 001 and 002",
        watch="Personal service is $3.8 million and other than personal service is $0.3 million. A liaison is not day-to-day supervision.",
    ),
    agency(
        id="MOCS",
        acronym="MOCS",
        name="Mayor's Office of Contract Services",
        portfolio="operations",
        tie="supervise",
        one="Oversees city procurement and the public record of contracts.",
        about="The Deputy Mayor for Operations supervises the Mayor's Office of Contract Services. It is a Mayoralty unit, not an MMR agency.",
        adopted=49.076,
        positions=246,
        units="Mayoralty units 090 and 091",
        watch="Personal service is $26.4 million and other than personal service is $22.7 million. The contracts it oversees are spent in the agencies that sign them.",
    ),
    agency(
        id="MOPD",
        acronym="MOPD",
        name="Mayor's Office for People with Disabilities",
        portfolio="hhs",
        tie="supervise",
        one="City policy and advocacy for disabled New Yorkers.",
        about="The Deputy Mayor for Health and Human Services supervises the Mayor's Office for People with Disabilities. It is a small Mayoralty unit with no MMR chapter.",
        adopted=0.679,
        positions=6,
        units="Mayoralty units 260 and 261",
        watch="Personal service is $656,000 and other than personal service is $23,000. Six full-time positions are in the adopted budget.",
    ),
    agency(
        id="ORE",
        acronym="ORE",
        name="Mayor's Office of Racial Equity",
        portfolio="economic",
        tie="supervise",
        one="Coordinates the city's racial equity plans and goals.",
        about="The Deputy Mayor for Economic Justice supervises the Mayor's Office of Racial Equity. The order says the office also includes the Commission on Gender Equity, which the budget keeps as a separate Mayoralty unit.",
        adopted=7.277,
        positions=38,
        units="Agency 213, units 001 and 002",
        watch="This tile is agency 213 only. The Commission on Gender Equity is Mayoralty units 350 and 351, $0.8 million and 7 positions, and is not included in the $7.3 million.",
    ),
    agency(
        id="CORE",
        acronym="CORE",
        name="Commission on Racial Equity",
        portfolio="economic",
        tie="liaison",
        one="A community commission that reviews the city's racial equity plans.",
        about="The Deputy Mayor for Economic Justice maintains a liaison with the Commission on Racial Equity. It is a separate agency from the Mayor's Office of Racial Equity.",
        adopted=4.828,
        positions=16,
        units="Agency 215, units 001 and 002",
        watch="Personal service is $1.8 million and other than personal service is $3.1 million. A liaison is not day-to-day supervision.",
    ),
    agency(
        id="OPS",
        acronym="OPS",
        name="Mayor's Office of Operations",
        portfolio="staff",
        tie="supervise",
        one="Publishes the Mayor's Management Report and tracks agency performance.",
        about="The Chief of Staff supervises the Mayor's Office of Operations. 311 is a separate agency in the Management Report. This unit is the office that produces that report.",
        adopted=6.629,
        positions=55,
        units="Mayoralty units 380 and 381",
        watch="Personal service is $6.5 million and other than personal service is $0.1 million. The 311 expenditure on its own card is not part of this unit.",
    ),
    agency(
        id="CFB",
        acronym="CFB",
        name="Campaign Finance Board",
        portfolio="staff",
        tie="liaison",
        one="Runs the city's public campaign-finance program and the voter guide.",
        about="The Chief of Staff maintains a liaison with the Campaign Finance Board. It is an independent city agency with no MMR chapter.",
        adopted=109.481,
        positions=258,
        units="Agency 004, units 001, 002, and 003",
        watch="Of the adopted total, $22.2 million is the election matching fund. The rest is the board. A liaison is not day-to-day supervision.",
    ),
    agency(
        id="COIB",
        acronym="COIB",
        name="Conflicts of Interest Board",
        portfolio="counsel",
        tie="liaison",
        one="Interprets the city's ethics law for officers and employees.",
        about="The Chief Counsel maintains a liaison with the Conflicts of Interest Board. It is an independent city agency with no MMR chapter.",
        adopted=2.861,
        positions=22,
        units="Agency 312, units 001 and 002",
        watch="Personal service is $2.7 million and other than personal service is $0.1 million. A liaison is not day-to-day supervision.",
    ),
    agency(
        id="MAYOR",
        acronym="MAYOR",
        name="Office of the Mayor",
        portfolio="mayor",
        tie="supervise",
        one="The Mayor's own staff and the offices the budget does not price on their own.",
        about="This is Mayoralty units 020 and 021. It is the appropriation for the Office of the Mayor, not the $196.1 million Mayoralty agency total. OMB, Labor Relations, Contract Services, Operations, and People with Disabilities are other units of that agency and have their own tiles.",
        adopted=44.754,
        positions=319,
        units="Mayoralty units 020 and 021",
        watch="Personal service is $40.5 million and other than personal service is $4.2 million, with 319 full-time positions. The budget says this unit includes the Mayor's executive staff, the deputy mayors, Gracie Mansion, counsel, scheduling, correspondence, the action center, special projects and events, fiscal and administrative management, the Albany and Washington offices, the committee on the judiciary, communications, the speech office, the office to combat domestic violence, and the Office of Immigrant Affairs. A tile with an asterisk and no dollar is not an additional amount.",
    ),
    agency(
        id="CGE",
        acronym="CGE",
        name="Commission on Gender Equity",
        portfolio="economic",
        tie="supervise",
        one="Advises the Mayor on gender equity. The order places it inside the Office of Racial Equity.",
        about="Executive Order 23 says the Office of Racial Equity consists of this commission, along with LGBTQIA+ affairs, NYC Her Future, the Pay Equity Cabinet, the Taskforce on Racial Inclusion and Equity, and the Young Men's Initiative. The adopted budget keeps the commission as its own Mayoralty units.",
        adopted=0.836,
        positions=7,
        units="Mayoralty units 350 and 351",
        watch="Personal service is $684,000 and other than personal service is $152,000. This is not part of the Office of the Mayor's $44.8 million, and it is not part of the Office of Racial Equity's $7.3 million. The other pieces of that office have no separate amount.",
    ),
    agency(
        id="MOME",
        acronym="MOME",
        name="Mayor's Office of Media and Entertainment",
        portfolio="economic",
        tie="supervise",
        one="NYC Media, film and theatre permits, and the city's media office.",
        about="The Deputy Mayor for Economic Justice supervises the Mayor's Office of Media and Entertainment. The adopted budget publishes it inside the Office of Technology and Innovation, not as its own agency.",
        adopted=23.629,
        positions=107,
        units="Office of Technology and Innovation units 009 and 010",
        watch="Personal service is $9.8 million, with 107 positions, and other than personal service is $13.8 million. NYC Media, the Office of Film, Theatre, and Broadcasting, and the press credentials unit are inside this appropriation. The Management Report expenditure for Technology and Innovation already includes this work, so this tile is not an additional city dollar. The budget text also names the Office of Nightlife here. Executive Order 23 places Nightlife inside Small Business Services.",
    ),
]

# Offices Executive Order 23 names that the adopted budget does not price.
# inside == "MAYOR" only when the Office of the Mayor unit text names that office.
INCLUDED = [
    agency(
        id="MOIA",
        acronym="MOIA",
        name="Mayor's Office of Immigrant Affairs",
        portfolio="economic",
        tie="supervise",
        inside="MAYOR",
        one="City policy and programs for immigrant New Yorkers.",
        about="The Deputy Mayor for Economic Justice supervises the Mayor's Office of Immigrant Affairs. The Office of the Mayor unit lists it. The budget does not give it a dollar of its own.",
        watch="The adopted budget names this office inside Mayoralty units 020 and 021. That unit is $44.8 million and 319 positions for the whole Office of the Mayor, not for this office. The asterisk means no separate amount is published. Do not add this tile to the $44.8 million.",
    ),
    agency(
        id="GRACIE",
        acronym="GRACIE",
        name="Gracie Mansion",
        portfolio="staff",
        tie="supervise",
        inside="MAYOR",
        one="The Mayor's official residence and its staff.",
        about="The Chief of Staff supervises Gracie Mansion. The Office of the Mayor unit includes Gracie Mansion staff and does not price them separately.",
        watch="The adopted budget names Gracie Mansion staff inside Mayoralty units 020 and 021. That unit is $44.8 million and 319 positions for the whole Office of the Mayor, not for the mansion alone. The asterisk means no separate amount is published.",
    ),
    agency(
        id="CORR",
        acronym="CORR",
        name="Mayor's Office of Correspondence",
        portfolio="staff",
        tie="supervise",
        inside="MAYOR",
        one="The Mayor's correspondence.",
        about="The Chief of Staff supervises the Mayor's Office of Correspondence. The Office of the Mayor unit includes correspondence services and does not price them separately.",
        watch="The adopted budget names correspondence services inside Mayoralty units 020 and 021. That unit is $44.8 million and 319 positions for the whole Office of the Mayor. The asterisk means no separate amount is published. Do not add this tile to the $44.8 million.",
    ),
    agency(
        id="SPECIAL",
        acronym="SPECIAL",
        name="Mayor's Office of Special Projects and Community Events",
        portfolio="staff",
        tie="supervise",
        inside="MAYOR",
        one="Special projects and community events for the Mayor's Office.",
        about="The Chief of Staff supervises this office. The Office of the Mayor unit names special projects and events together and does not split them.",
        watch="The adopted budget names special projects and events inside Mayoralty units 020 and 021, without a split. That unit is $44.8 million and 319 positions for the whole Office of the Mayor. The asterisk means no separate amount is published.",
    ),
    agency(
        id="JUD",
        acronym="JUD",
        name="Mayor's Advisory Committee on the Judiciary",
        portfolio="counsel",
        tie="supervise",
        inside="MAYOR",
        one="Advises the Mayor on judicial appointments.",
        about="The Chief Counsel supervises the Mayor's Advisory Committee on the Judiciary. The Office of the Mayor unit names the committee and does not price it separately.",
        watch="The adopted budget names the committee on the judiciary inside Mayoralty units 020 and 021. That unit is $44.8 million and 319 positions for the whole Office of the Mayor. The asterisk means no separate amount is published.",
    ),
    agency(
        id="COMM",
        acronym="COMM",
        name="Office of Communications",
        portfolio="comms",
        tie="supervise",
        inside="MAYOR",
        one="The Mayor's communications staff, press office, and ethnic and community media.",
        about="The Director of Communications supervises ethnic and community media, creative communications, and the press secretary. The Office of the Mayor unit names an office of communications and a speech office, and does not split them.",
        watch="The adopted budget does not publish a separate amount for communications, the speech office, ethnic and community media, or the press secretary. It names communications and the speech office inside the Office of the Mayor unit, which is $44.8 million and 319 positions for that whole unit. This tile is those roles together. The asterisk means they are not four budgets.",
    ),
    agency(
        id="CCEE",
        acronym="CCEE",
        name="Mayor's Office of Child Care and Early Childhood Education",
        portfolio="fdm",
        tie="supervise",
        one="City policy for child care and early childhood education.",
        about="The First Deputy Mayor supervises this office. The Fiscal 2026 adopted budget does not give it a unit of appropriation.",
        watch="Executive Order 23 names this office. The adopted expense budget does not publish a separate amount, and this chart does not assign it a share of the Office of the Mayor or of the Department of Education. The asterisk means the amount is not published. It does not mean the office spent nothing.",
    ),
    agency(
        id="MOCA",
        acronym="MOCA",
        name="Mayor's Office to Combat Antisemitism",
        portfolio="fdm",
        tie="supervise",
        one="City policy to combat antisemitism.",
        about="The First Deputy Mayor supervises this office. The Fiscal 2026 adopted budget does not give it a unit of appropriation.",
        watch="Executive Order 23 names this office. The adopted expense budget does not publish a separate amount, and this chart does not assign it a share of another office's dollar. The asterisk means the amount is not published. It does not mean the office spent nothing.",
    ),
    agency(
        id="BBJ",
        acronym="BBJ",
        name="Office for Coordination of the Transition to Borough-Based Jails",
        portfolio="fdm",
        tie="supervise",
        one="Coordinates the city's plan to close Rikers and open borough jails.",
        about="The First Deputy Mayor supervises this office. The Fiscal 2026 adopted budget does not give it a unit of appropriation.",
        watch="Executive Order 23 names this office. The adopted expense budget does not publish a separate amount. Correction's tile is the department, not this transition office. The asterisk means the amount is not published.",
    ),
    agency(
        id="OCS",
        acronym="OCS",
        name="Office of Community Safety",
        portfolio="safety",
        tie="supervise",
        one="Community safety policy, including victim services, neighborhood safety, and hate-crime prevention.",
        about="The Deputy Mayor for Community Safety supervises this office. The order says it includes the office to end domestic and gender-based violence, community mental health, crime victim services, neighborhood safety and gun-violence prevention, and the prevention of hate crimes.",
        watch="The adopted budget does not price this office. It does name the office to combat domestic violence inside the Office of the Mayor unit, which is $44.8 million and 319 positions for that whole unit, not for community safety alone. B-HEARD is operated by Fire and Health + Hospitals. The asterisk means no separate amount is published.",
    ),
    agency(
        id="OPP",
        acronym="OPP",
        name="Mayor's Office for Economic Opportunity",
        portfolio="economic",
        tie="supervise",
        one="Tests and tracks programs aimed at reducing poverty.",
        about="The Deputy Mayor for Economic Justice supervises this office. The Fiscal 2026 adopted budget does not give it a unit of appropriation.",
        watch="Executive Order 23 names this office. The adopted expense budget does not publish a separate amount, and this chart does not assign it a share of another office's dollar. The asterisk means the amount is not published. It does not mean the office spent nothing.",
    ),
    agency(
        id="MWBE",
        acronym="MWBE",
        name="Mayor's Office of Minority and Women-Owned Business Enterprises",
        portfolio="economic",
        tie="supervise",
        one="City policy for minority and women-owned business contracting.",
        about="The Deputy Mayor for Economic Justice supervises this office. The Fiscal 2026 adopted budget does not give it a unit of its own. Small Business Services has a contract-compliance unit for the same goal. That unit stays on the SBS card.",
        watch="Executive Order 23 names this office. The adopted expense budget does not publish a separate amount for it. Do not read the Small Business Services tile as this office's budget. The asterisk means the amount is not published.",
    ),
    agency(
        id="TALENT",
        acronym="TALENT",
        name="Mayor's Office of Talent and Workforce Development",
        portfolio="economic",
        tie="supervise",
        one="City workforce and talent policy.",
        about="The Deputy Mayor for Economic Justice supervises this office. The Fiscal 2026 adopted budget does not give it a unit of appropriation.",
        watch="Executive Order 23 names this office. The adopted expense budget does not publish a separate amount, and this chart does not assign it a share of Small Business Services or another office. The asterisk means the amount is not published.",
    ),
    agency(
        id="MOFP",
        acronym="MOFP",
        name="Mayor's Office of Food Policy",
        portfolio="hhs",
        tie="supervise",
        one="Coordinates the city's food policy.",
        about="The Deputy Mayor for Health and Human Services supervises this office. The Fiscal 2026 adopted budget does not give it a unit of appropriation.",
        watch="Executive Order 23 names this office. The adopted expense budget does not publish a separate amount, and this chart does not assign it a share of Health or another agency. The asterisk means the amount is not published.",
    ),
    agency(
        id="MONS",
        acronym="MONS",
        name="Mayor's Office of Nonprofit Services",
        portfolio="hhs",
        tie="supervise",
        one="The city's point of contact for nonprofit contractors.",
        about="The Deputy Mayor for Health and Human Services supervises this office. The Fiscal 2026 adopted budget does not give it a unit of appropriation.",
        watch="Executive Order 23 names this office. The adopted expense budget does not publish a separate amount. Contract Services oversees procurement citywide and is a different tile. The asterisk means the amount is not published.",
    ),
    agency(
        id="HRO",
        acronym="HRO",
        name="Mayor's Office of Housing Recovery Operations",
        portfolio="housing",
        tie="supervise",
        one="Coordinates rebuilding after disasters.",
        about="The Deputy Mayor for Housing and Planning supervises this office. The Fiscal 2026 adopted budget does not give it a unit of appropriation.",
        watch="Executive Order 23 names this office. The adopted expense budget does not publish a separate amount, and this chart does not assign it a share of Housing Preservation and Development. The asterisk means the amount is not published.",
    ),
    agency(
        id="MOPT",
        acronym="MOPT",
        name="Mayor's Office to Protect Tenants",
        portfolio="housing",
        tie="supervise",
        one="Coordinates the city's tenant-protection work.",
        about="The Deputy Mayor for Housing and Planning supervises this office. The Fiscal 2026 adopted budget does not give it a unit of appropriation.",
        watch="Executive Order 23 names this office. The adopted expense budget does not publish a separate amount, and this chart does not assign it a share of Housing Preservation and Development. The asterisk means the amount is not published.",
    ),
    agency(
        id="PDC",
        acronym="PDC",
        name="Public Design Commission",
        portfolio="housing",
        tie="supervise",
        one="Reviews public art, architecture, and the design of city projects.",
        about="The Deputy Mayor for Housing and Planning supervises the Public Design Commission. The Fiscal 2026 adopted budget does not give it a unit of appropriation.",
        watch="Executive Order 23 names this commission. The adopted expense budget does not publish a separate amount. The asterisk means the amount is not published. It does not mean the commission spent nothing.",
    ),
    agency(
        id="CPD",
        acronym="CPD",
        name="Mayor's Office of Capital Project Development",
        portfolio="operations",
        tie="supervise",
        one="Coordinates development of city capital projects.",
        about="The Deputy Mayor for Operations supervises this office. The Fiscal 2026 adopted budget does not give it a unit of appropriation.",
        watch="Executive Order 23 names this office. The adopted expense budget does not publish a separate amount. Design and Construction's tile is that department, not this office. The asterisk means the amount is not published.",
    ),
    agency(
        id="CEJ",
        acronym="CEJ",
        name="Mayor's Office of Climate and Environmental Justice",
        portfolio="operations",
        tie="supervise",
        one="City climate policy and environmental justice.",
        about="The Deputy Mayor for Operations supervises this office. The Fiscal 2026 adopted budget does not give it a unit of appropriation.",
        watch="Executive Order 23 names this office. The adopted expense budget does not publish a separate amount, and this chart does not assign it a share of Environmental Protection. The asterisk means the amount is not published.",
    ),
    agency(
        id="MOEC",
        acronym="MOEC",
        name="Mayor's Office of Environmental Coordination",
        portfolio="operations",
        tie="supervise",
        one="Coordinates city environmental review.",
        about="The Deputy Mayor for Operations supervises this office. The Fiscal 2026 adopted budget does not give it a unit of appropriation.",
        watch="Executive Order 23 names this office. The adopted expense budget does not publish a separate amount. The asterisk means the amount is not published. It does not mean the office spent nothing.",
    ),
    agency(
        id="OER",
        acronym="OER",
        name="Mayor's Office of Environmental Remediations",
        portfolio="operations",
        tie="supervise",
        one="City programs for cleaning contaminated land.",
        about="The Deputy Mayor for Operations supervises this office. The Fiscal 2026 adopted budget does not give it a unit of appropriation.",
        watch="Executive Order 23 names this office. The adopted expense budget does not publish a separate amount, and this chart does not assign it a share of Environmental Protection. The asterisk means the amount is not published.",
    ),
    agency(
        id="ADMIN",
        acronym="ADMIN",
        name="Mayor's Office of Administrative Services",
        portfolio="staff",
        tie="supervise",
        one="Administrative services for the Mayor's Office.",
        about="The Chief of Staff supervises this office. The Fiscal 2026 adopted budget does not give it a unit of appropriation. The Office of the Mayor unit mentions fiscal and administrative management without a split.",
        watch="Executive Order 23 names this office. The adopted budget does not publish a separate amount. It mentions fiscal and administrative management inside the Office of the Mayor unit and does not say that sentence is this office alone. The asterisk means the amount is not published.",
    ),
    agency(
        id="APPT",
        acronym="APPT",
        name="Mayor's Office of Appointments",
        portfolio="staff",
        tie="supervise",
        one="Mayoral appointments to boards and offices.",
        about="The Chief of Staff supervises this office. The Fiscal 2026 adopted budget does not give it a unit of appropriation.",
        watch="Executive Order 23 names this office. The adopted expense budget does not publish a separate amount. The asterisk means the amount is not published. It does not mean the office spent nothing.",
    ),
    agency(
        id="EVENTS",
        acronym="EVENTS",
        name="Mayor's Office of Citywide Event Coordination and Management",
        portfolio="staff",
        tie="supervise",
        one="Permits and coordination for events in public space.",
        about="The Chief of Staff supervises this office. The Fiscal 2026 adopted budget does not give it a unit of appropriation.",
        watch="Executive Order 23 names this office. The adopted expense budget does not publish a separate amount. Special projects and events inside the Office of the Mayor unit are a different line in the budget text, and this chart does not merge the two. The asterisk means the amount is not published.",
    ),
    agency(
        id="IGA",
        acronym="IGA",
        name="Mayor's Office of Intergovernmental Affairs",
        portfolio="staff",
        tie="supervise",
        one="The Mayor's relations with other governments.",
        about="The Chief of Staff supervises this office. The Fiscal 2026 adopted budget does not give it a unit of appropriation. The Office of the Mayor unit names Albany and Washington offices without a split.",
        watch="Executive Order 23 names this office. The adopted budget names Albany and Washington offices inside the Office of the Mayor unit and does not say those offices are this one. No separate amount is published. The asterisk means that.",
    ),
    agency(
        id="INTL",
        acronym="INTL",
        name="Mayor's Office of International Affairs",
        portfolio="staff",
        tie="supervise",
        one="The city's relations with consulates and international organizations.",
        about="The Chief of Staff supervises this office. The Fiscal 2026 adopted budget does not give it a unit of appropriation. The Commission for the United Nations and the Consular Corps is a different Mayoralty unit and is not this office.",
        watch="Executive Order 23 names this office. The adopted expense budget does not publish a separate amount for it. The asterisk means the amount is not published. It does not mean the office spent nothing.",
    ),
    agency(
        id="MASS",
        acronym="MASS",
        name="Mayor's Office of Mass Engagement",
        portfolio="staff",
        tie="supervise",
        one="NYC Service, the census, faith-based partnerships, and the Public Engagement Unit.",
        about="The Chief of Staff supervises this office. The order says it includes NYC Service, the Office of the Census, the Office of Faith-Based and Community Partnerships, and the Public Engagement Unit. The adopted budget does not price them.",
        watch="Executive Order 23 names this office and those four pieces. The adopted expense budget does not publish a separate amount for any of them. This tile is the office, not four budgets. The asterisk means the amount is not published.",
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
    if item["id"] == "MAYOR":
        return "This is the Mayor's own appropriation. Executive Order 23 does not assign it to a deputy mayor."
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
        "figure": "mmr",
        "includedIn": None,
        "expendituresMillions": item.get("exp"),
        "authorizedMillions": item.get("auth"),
        "adoptedMillions": None,
        "positions": positions,
        "overtime": overtime,
        "revenueMillions": item.get("revenue"),
        "capitalMillions": item.get("capital"),
        "capitalLabel": item.get("capital_label", "Capital commitments" if item.get("capital") is not None else None),
        "contractMillions": item.get("contracts"),
        "watch": item["watch"],
        "gaps": gaps_for(item, positions, overtime),
    }


def build_adopted(item: dict) -> dict:
    headcount = int(item["positions"])
    return {
        "id": item["id"],
        "acronym": item["acronym"],
        "name": item["name"],
        "portfolio": item["portfolio"],
        "tie": item["tie"],
        "assignment": "named",
        "reportsToMayor": False,
        "parent": None,
        "oneLiner": item["one"],
        "about": item["about"],
        "reportingNote": reporting_note(item),
        "figure": "adopted",
        "includedIn": None,
        "expendituresMillions": None,
        "authorizedMillions": None,
        "adoptedMillions": item["adopted"],
        "positions": {
            "actual": headcount,
            "authorized": headcount,
            "lines": [],
            "note": f"Full-time positions in the Fiscal 2026 adopted budget, {item['units']}. Not an MMR actual.",
            "comparable": False,
        },
        "overtime": None,
        "revenueMillions": None,
        "capitalMillions": None,
        "capitalLabel": None,
        "contractMillions": None,
        "watch": item["watch"],
        "gaps": [
            "Keep this adopted appropriation next to an MMR expenditure only with the asterisk visible. They are different objects.",
        ],
    }


def build_included(item: dict) -> dict:
    return {
        "id": item["id"],
        "acronym": item["acronym"],
        "name": item["name"],
        "portfolio": item["portfolio"],
        "tie": item["tie"],
        "assignment": "named",
        "reportsToMayor": False,
        "parent": None,
        "oneLiner": item["one"],
        "about": item["about"],
        "reportingNote": reporting_note(item),
        "figure": "included",
        "includedIn": item.get("inside"),
        "expendituresMillions": None,
        "authorizedMillions": None,
        "adoptedMillions": None,
        "positions": {
            "actual": None,
            "authorized": None,
            "lines": [],
            "note": "No headcount is published for this office on its own.",
            "comparable": False,
        },
        "overtime": None,
        "revenueMillions": None,
        "capitalMillions": None,
        "capitalLabel": None,
        "contractMillions": None,
        "watch": item["watch"],
        "gaps": [
            "A separate amount would require a unit of appropriation. Do not split another office's dollar to fill this tile.",
        ],
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
            "## Fiscal 2026, not published separately" if card["figure"] == "included" else "## Fiscal 2026, from the adopted budget" if card["figure"] == "adopted" else "## Fiscal 2026, from the MMR resources table",
            "",
            "- No separate amount is published. The asterisk on the site marks that." if card["figure"] == "included" else f"- Adopted budget: {money_phrase(card['adoptedMillions'])}" if card["figure"] == "adopted" else f"- Expenditures: {money_phrase(card['expendituresMillions'])}",
            *([] if card["figure"] == "included" else [
                f"- Full-time positions in that budget: {people_phrase(card['positions']['actual'])}" if card["figure"] == "adopted" else f"- Authorized budget in the same row: {money_phrase(card['authorizedMillions'])}",
            ]),
            *([] if card["figure"] != "mmr" else [
                f"- Positions, actual: {people_phrase(card['positions']['actual'])}",
                f"- Positions, authorized: {people_phrase(card['positions']['authorized'])}",
            ]),
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
            *(
                [
                    "- [Fiscal 2026 adopted expense budget](https://www.nyc.gov/assets/omb/downloads/pdf/adopt25/erc6-25.pdf). "
                    + (
                        "This office has no unit of its own in that book."
                        if card["figure"] == "included"
                        else "The unit of appropriation is named on this card."
                    ),
                ]
                if card["figure"] in {"adopted", "included"}
                else [
                    "- [Fiscal 2026 Mayor's Management Report](https://www.nyc.gov/assets/operations/downloads/pdf/mmr2026/2026_mmr.pdf), agency resources chapter for this agency.",
                    "- [MMR Agency Resources on NYC Open Data](https://data.cityofnewyork.us/City-Government/Mayor-s-Management-Report-Agency-Resources/4qmi-txnk) (`4qmi-txnk`), reporting fiscal year 2026.",
                ]
            ),
            "- [Executive Order 23](https://www.nyc.gov/mayors-office/news/2026/09/executive-order-no--23), September 8, 2026, for the reporting line.",
            "",
            f"Portfolio: {labels[card['portfolio']]}.",
            "",
        ]
        (KNOW / f"{card['id'].lower()}.md").write_text("\n".join(lines), encoding="utf-8")

    index = [
        "# Agency knowledge cards",
        "",
        "One card per agency in the Fiscal 2026 Mayor's Management Report that publishes a resources row, plus offices Executive Order 23 names. An adopted-budget card is that office's own unit. A card with no separate amount is marked that way and is not given a share of another office's dollar.",
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
    extra_ids = {item["id"] for item in ADOPTED} | {item["id"] for item in INCLUDED}
    if extra_ids & {item["id"] for item in AGENCIES} or len(extra_ids) != len(ADOPTED) + len(INCLUDED):
        raise SystemExit("An added office reuses an id")
    cards = (
        [build_agency(item) for item in AGENCIES]
        + [build_adopted(item) for item in ADOPTED]
        + [build_included(item) for item in INCLUDED]
    )
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
