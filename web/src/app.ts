import catalog from "../../data/agencies.json";
import { mountHeroField } from "./hero-field";
import { esc, money, people } from "./format";

type Agency = (typeof catalog.agencies)[number];
type PortfolioId = (typeof catalog.portfolios)[number]["id"] | "all";

const agencies = catalog.agencies;
const portfolios = catalog.portfolios;

export function mountApp(root: HTMLElement): void {
  const state = {
    portfolio: "all" as PortfolioId,
    query: "",
    selected: agencyFromHash(),
  };

  root.innerHTML = shell();
  const hero = root.querySelector<HTMLElement>(".hero");
  if (hero) mountHeroField(hero);

  const search = root.querySelector<HTMLInputElement>("#search");
  const atlas = root.querySelector<HTMLElement>("#atlas");
  const detail = root.querySelector<HTMLElement>("#detail");
  if (!search || !atlas || !detail) return;

  const draw = (scroll: boolean) => {
    paintFilters(root, state.portfolio);
    atlas.innerHTML = renderAtlas(state.portfolio, state.query, state.selected);
    detail.innerHTML = renderDetail(state.selected);
    if (scroll && state.selected) {
      detail.scrollIntoView({ behavior: "smooth", block: "start" });
    }
  };

  root.querySelector("[data-scroll='atlas']")?.addEventListener("click", () => {
    document.getElementById("atlas")?.scrollIntoView({ behavior: "smooth", block: "start" });
  });

  root.querySelector("#filters")?.addEventListener("click", (event) => {
    const button = (event.target as HTMLElement).closest<HTMLButtonElement>("[data-portfolio]");
    if (!button) return;
    state.portfolio = button.dataset.portfolio as PortfolioId;
    draw(false);
  });

  search.addEventListener("input", () => {
    state.query = search.value;
    draw(false);
  });

  atlas.addEventListener("click", (event) => {
    const button = (event.target as HTMLElement).closest<HTMLButtonElement>("[data-agency]");
    if (!button?.dataset.agency) return;
    choose(button.dataset.agency, true);
  });

  detail.addEventListener("click", (event) => {
    const target = event.target as HTMLElement;
    const agencyButton = target.closest<HTMLButtonElement>("[data-agency]");
    if (agencyButton?.dataset.agency) {
      choose(agencyButton.dataset.agency, true);
      return;
    }
    if (target.closest("[data-clear]")) choose(null, false);
  });

  window.addEventListener("hashchange", () => {
    state.selected = agencyFromHash();
    draw(Boolean(state.selected));
  });

  window.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && state.selected) choose(null, false);
  });

  draw(Boolean(state.selected));

  function choose(id: string | null, scroll: boolean) {
    state.selected = id;
    const next = id ? `#${id}` : window.location.pathname + window.location.search;
    history.replaceState(null, "", next);
    draw(scroll);
  }
}

function agencyFromHash(): string | null {
  const id = window.location.hash.replace("#", "");
  return agencies.some((agency) => agency.id === id) ? id : null;
}

function shell(): string {
  const spent = agencies.reduce((sum, agency) => sum + (agency.expendituresMillions ?? 0), 0);
  const headcount = agencies.reduce((sum, agency) => sum + agency.positions.actual, 0);
  const filterButtons = [
    `<button class="pane-tab active" type="button" data-portfolio="all">All 45</button>`,
    ...portfolios.map(
      (portfolio) =>
        `<button class="pane-tab" type="button" data-portfolio="${portfolio.id}">${esc(shortLabel(portfolio.id))}</button>`,
    ),
  ].join("");

  return `
    <header class="hero">
      <canvas class="hero-field" aria-hidden="true"></canvas>
      <div class="hero-copy">
        <p class="eyebrow">New York City · Executive Order 23 · Fiscal 2026</p>
        <h1>NY Agencies</h1>
        <p class="lede">
          Forty-five agencies publish a budget or a headcount in the Mayor's Management Report.
          The label is the acronym. Open one for what it does, what it spent, and how many people it employs.
        </p>
        <button class="hero-scroll" type="button" data-scroll="atlas">
          <span class="hero-scroll-glow" aria-hidden="true"></span>
          Choose an agency
        </button>
      </div>
    </header>

    <nav class="pane-nav" id="filters" aria-label="Portfolios">
      <div class="filter-row">${filterButtons}</div>
      <input class="search" id="search" type="search" placeholder="Search acronym or name" aria-label="Search agencies" />
    </nav>

    <main>
      <section class="stat-grid" aria-label="Citywide picture">
        <article class="stat-card">
          <p class="stat-label">Agencies on this atlas</p>
          <p class="stat-value">45</p>
          <p class="stat-caption">Every MMR chapter with a resources row</p>
        </article>
        <article class="stat-card">
          <p class="stat-label">Expenditures, FY2026</p>
          <p class="stat-value">${money(spent)}</p>
          <p class="stat-caption">Sum of the published expenditure lines. EDC and SCA have none.</p>
        </article>
        <article class="stat-card">
          <p class="stat-label">Positions, actual</p>
          <p class="stat-value">${people(headcount)}</p>
          <p class="stat-caption">Adds each agency's headline headcount. Parks includes full-time equivalents.</p>
        </article>
      </section>
      <p class="caveat">Larger labels spent more. Totals add mayoral departments, authorities, the libraries, and CUNY. They are a map, not the adopted budget.</p>
      <div id="atlas"></div>
      <div id="detail" class="detail" aria-live="polite"></div>
      ${planSection()}
    </main>

    <footer class="site-footer">
      <p>${esc(catalog.meta.disclaimer)} ${esc(catalog.meta.source)}. ${esc(catalog.meta.order)}.</p>
      <p class="byline">Andrés Camacho · Independent reading of NYC public data</p>
    </footer>
  `;
}

function paintFilters(root: HTMLElement, active: PortfolioId): void {
  root.querySelectorAll<HTMLButtonElement>("[data-portfolio]").forEach((button) => {
    const on = button.dataset.portfolio === active;
    button.classList.toggle("active", on);
    button.setAttribute("aria-pressed", on ? "true" : "false");
  });
}

function renderAtlas(portfolio: PortfolioId, query: string, selected: string | null): string {
  const needle = query.trim().toLowerCase();
  const visible = portfolios.filter((item) => portfolio === "all" || item.id === portfolio);
  const groups = visible
    .map((item) => {
      const rows = agencies
        .filter((agency) => agency.portfolio === item.id)
        .filter((agency) => !needle || matches(agency, needle))
        .sort((a, b) => (b.expendituresMillions ?? -1) - (a.expendituresMillions ?? -1));
      return { item, rows };
    })
    .filter((group) => {
      if (group.rows.length > 0) return true;
      if (needle) return false;
      return group.item.id === "safety" || portfolio !== "all";
    });

  if (needle && groups.every((group) => group.rows.length === 0)) {
    return `<p class="empty">No agency matches “${esc(query.trim())}”.</p>`;
  }

  return groups
    .map(({ item, rows }) => {
      const buttons = rows.map((agency) => acronymButton(agency, selected)).join("");
      const safety =
        item.id === "safety"
          ? `<div class="safety-note">
              <p>The Deputy Mayor for Community Safety supervises the Office of Community Safety and B-HEARD. Neither has its own chapter in the management report.</p>
              <p>B-HEARD is a joint operation. The public headcount and spending nearest to that work are on FDNY and Health + Hospitals.</p>
              <div>
                <button class="text-button" type="button" data-agency="FDNY">Open FDNY</button>
                ·
                <button class="text-button" type="button" data-agency="NYCHH">Open H+H</button>
              </div>
            </div>`
          : "";
      if (!buttons && !safety) return "";
      return `
        <section class="group">
          <p class="eyebrow">${rows.length ? `${rows.length} ${rows.length === 1 ? "agency" : "agencies"}` : "No MMR chapter"}</p>
          <h2>${esc(item.label)}</h2>
          <p>${esc(item.blurb)}</p>
          ${buttons ? `<div class="acronym-grid">${buttons}</div>` : ""}
          ${safety}
        </section>`;
    })
    .join("");
}

function acronymButton(agency: Agency, selected: string | null): string {
  const size = sizeClass(agency);
  const pressed = agency.id === selected;
  return `<button class="acronym ${size}${pressed ? " is-selected" : ""}" type="button" data-agency="${agency.id}" aria-pressed="${pressed ? "true" : "false"}">${esc(agency.acronym)}</button>`;
}

function sizeClass(agency: Agency): string {
  const spent = agency.expendituresMillions;
  if (spent == null) return "sm";
  if (spent >= 5000) return "xl";
  if (spent >= 1000) return "lg";
  if (spent >= 200) return "md";
  return "sm";
}

function matches(agency: Agency, needle: string): boolean {
  return [agency.acronym, agency.id, agency.name].join(" ").toLowerCase().includes(needle);
}

function renderDetail(selected: string | null): string {
  if (!selected) {
    return `
      <section class="prompt" id="agency">
        <p class="eyebrow">Agency card</p>
        <h2>Open an acronym</h2>
        <p>Each card has the Fiscal 2026 expenditure, the authorized figure beside it, and the published headcount. Where the report gives overtime, contract spending, capital commitments, or revenue, those are on the card too.</p>
      </section>`;
  }
  const agency = agencies.find((item) => item.id === selected);
  if (!agency) return "";
  const portfolio = portfolios.find((item) => item.id === agency.portfolio);
  const stats = statCards(agency);
  const about =
    agency.about !== agency.oneLiner
      ? `<article class="knowledge-card"><h3>What it does</h3><p>${esc(agency.about)}</p></article>`
      : "";
  const lines = agency.positions.lines
    .map(
      (line) =>
        `<li>${esc(line.label)}: ${people(line.actual)} actual, ${people(line.authorized)} authorized</li>`,
    )
    .join("");

  return `
    <section id="agency">
      <div class="detail-head">
        <div>
          <p class="eyebrow">${esc(agency.acronym)} · ${esc(portfolio?.label ?? "")}</p>
          <h2>${esc(agency.name)}</h2>
        </div>
        <button class="text-button" type="button" data-clear>Close</button>
      </div>
      <div class="badge-row">
        <span class="badge">${agency.tie === "supervise" ? "Supervised" : "Liaison"}</span>
        ${agency.assignment === "inferred" ? `<span class="badge gold">Placement inferred</span>` : ""}
        ${agency.reportsToMayor ? `<span class="badge gold">Also reports to the Mayor</span>` : ""}
        ${agency.parent ? `<span class="badge">${esc(agency.parent)}</span>` : ""}
      </div>
      <p class="lede">${esc(agency.oneLiner)}</p>
      <div class="stat-grid">${stats}</div>
      <div class="card-grid">
        <article class="knowledge-card">
          <h3>Where it sits</h3>
          <p>${esc(agency.reportingNote)}</p>
        </article>
        ${about}
        <article class="knowledge-card">
          <h3>How to read the numbers</h3>
          <p>${esc(agency.watch)}</p>
          ${lines ? `<ul>${lines}</ul>` : ""}
          ${agency.positions.note ? `<p class="stat-caption">${esc(agency.positions.note)}</p>` : ""}
          <p class="stat-caption">Expenditures are the FY2026 projected actual. The authorized figure is the other column in the same row. Neither one is the adopted budget, and both can mix city, state, and federal funds.</p>
          ${
            agency.overtime?.publishedAs === "thousands"
              ? `<p class="stat-caption">Overtime for this agency is published in thousands of dollars. It is converted to millions here so it can sit next to the others.</p>`
              : ""
          }
        </article>
        <article class="knowledge-card">
          <h3>What would make this card better</h3>
          <ul>${agency.gaps.map((gap) => `<li>${esc(gap)}</li>`).join("")}</ul>
        </article>
      </div>
      <p class="sources">
        <a href="https://www.nyc.gov/assets/operations/downloads/pdf/mmr2026/2026_mmr.pdf">Fiscal 2026 Mayor's Management Report</a>
        · <a href="https://data.cityofnewyork.us/City-Government/Mayor-s-Management-Report-Agency-Resources/4qmi-txnk">Agency resources on NYC Open Data</a>
        · <a href="https://www.nyc.gov/mayors-office/news/2026/09/executive-order-no--23">Executive Order 23</a>
      </p>
    </section>`;
}

function statCards(agency: Agency): string {
  const cards: string[] = [];
  cards.push(stat("Expenditures, FY2026", money(agency.expendituresMillions), "Projected actual"));
  cards.push(stat("Authorized in the same row", money(agency.authorizedMillions), "Not a separate budget"));
  const positionNote =
    agency.positions.authorized > agency.positions.actual
      ? `${people(agency.positions.authorized - agency.positions.actual)} below the authorized count`
      : agency.positions.actual > agency.positions.authorized
        ? "Actual is above the authorized count"
        : "Matches the authorized count";
  cards.push(stat("Positions, actual", people(agency.positions.actual), positionNote));
  cards.push(stat("Positions, authorized", people(agency.positions.authorized), "Published headcount, not a vacancy study"));
  if (agency.overtime) {
    const share = overtimeShare(agency.overtime.millions, agency.expendituresMillions);
    cards.push(stat("Overtime", money(agency.overtime.millions), share));
  }
  if (agency.contractMillions != null) {
    cards.push(stat("Human-services contracts", money(agency.contractMillions), "Separate MMR resource row"));
  }
  if (agency.capitalMillions != null) {
    cards.push(stat(agency.capitalLabel ?? "Capital commitments", money(agency.capitalMillions), "Not part of the expense line"));
  }
  if (agency.revenueMillions != null) {
    cards.push(stat("Revenue in this table", money(agency.revenueMillions), "Not the same as the budget"));
  }
  return cards.join("");
}

function overtimeShare(overtime: number, expenditures: number | null): string {
  if (!expenditures || expenditures <= 0) return "Published overtime";
  const pct = (overtime / expenditures) * 100;
  if (pct < 1) return "Under 1% of expenditures";
  return `${Math.round(pct)}% of expenditures`;
}

function stat(label: string, value: string, caption: string): string {
  return `
    <article class="stat-card">
      <p class="stat-label">${esc(label)}</p>
      <p class="stat-value">${esc(value)}</p>
      <p class="stat-caption">${esc(caption)}</p>
    </article>`;
}

function shortLabel(id: string): string {
  const labels: Record<string, string> = {
    fdm: "First Deputy",
    operations: "Operations",
    hhs: "Health and human services",
    housing: "Housing",
    economic: "Economic justice",
    counsel: "Counsel",
    staff: "Chief of Staff",
    safety: "Community safety",
  };
  return labels[id] ?? id;
}

function planSection(): string {
  const steps = [
    ["01", "Name the offices", "Executive Order 23 assigns OMB, Labor Relations, Contract Services, Immigrant Affairs, and Community Safety. They have no MMR chapter. Add them from the adopted budget's units of appropriation."],
    ["02", "Split the funds", "An expenditure line mixes city, state, and federal money. The next cut is city funds versus categorical funds, then personal service versus other than personal service."],
    ["03", "Add the results", "Each chapter has critical indicators and a direction they are supposed to move. Put five of those on the card so spending is not the only fact."],
    ["04", "Authorities on their own books", "EDC and the School Construction Authority have headcount and no expenditure line. Health + Hospitals, NYCHA, and CUNY need their own financial statements beside the MMR row."],
    ["05", "Join the efficiency scan", "Attach overtime growth and the cost-versus-outcome quadrant from the NY Efficiency project, so a card can say whether spending rose while results did not."],
  ];
  return `
    <section class="plan" id="plan">
      <p class="eyebrow">How this gets better</p>
      <h2>A first reading, then a sharper one</h2>
      <p>These cards are the public layer: who the agency is, who it reports to, what it spent, and how many people it employs. The useful version is the one that can survive a conversation with the agency.</p>
      <div class="plan-grid">
        ${steps
          .map(
            ([num, title, body]) => `
            <article class="plan-step">
              <p class="plan-num">${num}</p>
              <h3>${title}</h3>
              <p>${body}</p>
            </article>`,
          )
          .join("")}
      </div>
    </section>`;
}
