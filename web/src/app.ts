import catalog from "../../data/agencies.json";
import { esc, money, people } from "./format";
import {
  bindTooltip,
  clusterLabel,
  orderedAgencies,
  rampGradient,
  renderField,
  renderSegments,
  spendRange,
  toneVars,
  totalSpend,
  visualOrder,
  type Agency,
} from "./field";
import { moneyTile } from "./format";

const agencies = catalog.agencies;

export function mountApp(root: HTMLElement): void {
  const state = { selected: agencyFromHash() };

  const [low, high] = spendRange(agencies);
  const funded = agencies.filter((agency) => agency.expendituresMillions != null).length;

  root.innerHTML = `
    <div class="backdrop" aria-hidden="true"></div>
    <div class="stage">
      <header class="mast">
        <div class="mast-copy">
          <h1>New York City agencies</h1>
          <p>Grouped by who they report to under Executive Order 23. Inside each group, the largest Fiscal 2026 expenditure comes first. Color is that amount, on one scale.</p>
        </div>
        <div class="mode" role="group" aria-label="Color theme">
          <button type="button" data-mode="light">${SUN}Light</button>
          <button type="button" data-mode="dark">${MOON}Dark</button>
        </div>
        <div class="total">
          <p class="total-value">${money(totalSpend(agencies))}</p>
          <p class="total-label">spent by ${funded} agencies in Fiscal 2026</p>
        </div>
        <div class="strip" id="strip">${renderSegments(orderedAgencies(agencies), agencies, 0.03)}</div>
        <div class="ramp">
          <span>${moneyTile(low)}</span>
          <div class="ramp-bar" aria-hidden="true"></div>
          <span>${moneyTile(high)}</span>
          <p>Color is spending on a log scale. Width in the bar above is spending as is.</p>
        </div>
      </header>
      <div class="stage-body">
        <div class="field">
          <div id="field"></div>
          ${renderColophon(funded)}
        </div>
        <aside class="card" id="card" aria-live="polite" hidden></aside>
      </div>
    </div>
  `;

  const rampBar = root.querySelector<HTMLElement>(".ramp-bar");
  rampBar?.style.setProperty("--ramp-l", rampGradient("light"));
  rampBar?.style.setProperty("--ramp-d", rampGradient("dark"));

  const modeButtons = root.querySelectorAll<HTMLButtonElement>(".mode button");
  const showMode = () => {
    const current = document.documentElement.dataset.theme === "dark" ? "dark" : "light";
    modeButtons.forEach((button) => button.setAttribute("aria-pressed", String(button.dataset.mode === current)));
  };
  modeButtons.forEach((button) =>
    button.addEventListener("click", () => {
      const mode = button.dataset.mode === "dark" ? "dark" : "light";
      document.documentElement.dataset.theme = mode;
      try {
        localStorage.setItem("theme", mode);
      } catch {
        // Private windows can refuse storage; the choice still applies for this visit.
      }
      showMode();
    }),
  );
  showMode();

  bindTooltip(root, agencies);

  const stageBody = root.querySelector<HTMLElement>(".stage-body");
  const field = root.querySelector<HTMLElement>("#field");
  const card = root.querySelector<HTMLElement>("#card");
  if (!stageBody || !field || !card) return;

  const draw = () => {
    const selected = agencies.find((agency) => agency.id === state.selected) ?? null;
    stageBody.classList.toggle("has-card", Boolean(selected));
    card.hidden = !selected;
    if (selected) {
      card.setAttribute("style", toneVars(agencies, selected.expendituresMillions, "pick", "pick-ink") ?? "");
      card.innerHTML = renderCard(selected);
    } else {
      card.innerHTML = "";
      card.removeAttribute("style");
    }
    renderField(field, agencies, catalog.portfolios, state.selected, choose);
  };

  const choose = (id: string | null) => {
    state.selected = state.selected === id ? null : id;
    const next = state.selected ? `#${state.selected}` : window.location.pathname + window.location.search;
    history.replaceState(null, "", next);
    draw();
  };

  root.querySelector("#strip")?.addEventListener("click", (event) => {
    const seg = (event.target as HTMLElement).closest<HTMLElement>(".seg");
    if (seg?.dataset.id) choose(seg.dataset.id);
  });

  card.addEventListener("click", (event) => {
    if ((event.target as HTMLElement).closest("[data-clear]")) choose(null);
  });

  window.addEventListener("hashchange", () => {
    state.selected = agencyFromHash();
    draw();
  });

  window.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && state.selected) {
      choose(null);
      return;
    }
    if (event.key !== "ArrowRight" && event.key !== "ArrowLeft" && event.key !== "ArrowDown" && event.key !== "ArrowUp") {
      return;
    }
    const target = event.target as HTMLElement;
    if (target.closest("a, button, input, textarea")) return;
    const order = visualOrder();
    if (order.length === 0) return;
    const index = order.findIndex((agency) => agency.id === state.selected);
    const step = event.key === "ArrowRight" || event.key === "ArrowDown" ? 1 : -1;
    const nextIndex = index < 0 ? 0 : (index + step + order.length) % order.length;
    event.preventDefault();
    choose(order[nextIndex].id);
  });

  new ResizeObserver(() => {
    renderField(field, agencies, catalog.portfolios, state.selected, choose);
  }).observe(field);

  draw();
}

const SUN = `<svg viewBox="0 0 16 16" width="14" height="14" aria-hidden="true"><circle cx="8" cy="8" r="3" fill="currentColor"/><path d="M8 1v2M8 13v2M1 8h2M13 8h2M3 3l1.4 1.4M11.6 11.6L13 13M3 13l1.4-1.4M11.6 4.4L13 3" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"/></svg>`;
const MOON = `<svg viewBox="0 0 16 16" width="14" height="14" aria-hidden="true"><path d="M13.5 10.2A6 6 0 0 1 5.8 2.5a6 6 0 1 0 7.7 7.7z" fill="currentColor"/></svg>`;

function agencyFromHash(): string | null {
  const id = window.location.hash.replace("#", "");
  return agencies.some((agency) => agency.id === id) ? id : null;
}

const SOURCES = {
  data: "https://data.cityofnewyork.us/City-Government/Mayor-s-Management-Report-Agency-Resources/4qmi-txnk",
  report: "https://www.nyc.gov/assets/operations/downloads/pdf/mmr2026/2026_mmr.pdf",
  order: "https://www.nyc.gov/mayors-office/news/2026/09/executive-order-no--23",
};

const GITHUB = "https://github.com/anfelipecb";

const GITHUB_MARK = `<svg viewBox="0 0 16 16" width="18" height="18" aria-hidden="true"><path fill="currentColor" d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0016 8c0-4.42-3.58-8-8-8z"/></svg>`;

function link(href: string, text: string): string {
  return `<a href="${href}" target="_blank" rel="noopener">${text}</a>`;
}

function renderColophon(funded: number): string {
  const { meta } = catalog;
  const empty = agencies.filter((agency) => agency.expendituresMillions == null).map((agency) => agency.acronym);
  const inferred = agencies.filter((agency) => agency.assignment === "inferred").map((agency) => agency.name);
  return `
    <footer class="colophon">
      <details class="method">
        <summary>
          <span>About the data</span>
          <span class="method-hint">Sources, definitions, and what is left out</span>
        </summary>
        <div class="method-body">
          <section>
            <h3>Source</h3>
            <p>Every figure comes from the agency resources table of the Fiscal ${meta.fiscalYear} ${link(SOURCES.report, "Mayor's Management Report")} (MMR), published by the Mayor's Office of Operations. The same table is on NYC Open Data as ${link(SOURCES.data, "Mayor's Management Report Agency Resources, dataset 4qmi-txnk")}. Fiscal ${meta.fiscalYear} runs ${esc(meta.window)}.</p>
          </section>
          <section>
            <h3>Spending</h3>
            <p>Spending is the MMR row Expenditures ($000,000), column “current fiscal year projected actual,” shown in dollars. It is not the adopted budget, and it includes all funds: city, state, and federal. The authorized figure on each card is the same row's current-year authorized budget. The ${money(totalSpend(agencies))} total adds the ${funded} agencies that publish an expenditure row. ${empty.join(" and ")} publish headcount and capital commitments but no expenditure row, so they have no color and are not in the total.</p>
          </section>
          <section>
            <h3>Headcount and other rows</h3>
            <p>Positions are the MMR personnel rows, actual against authorized. Where the report publishes uniformed and civilian rows separately, the card adds them. Parks reports full-time staff and full-time equivalents together, so its headcount is not comparable with full-time-only agencies. Overtime, human-services contracts, capital commitments, and revenue appear only where the agency's table has that row.</p>
          </section>
          <section>
            <h3>Reporting lines</h3>
            <p>Groups follow ${link(SOURCES.order, esc(meta.order))}, which assigns agencies to deputy mayors and senior staff either to supervise or to keep a liaison. Each card says which. Two placements, ${inferred.join(" and ")}, are inferred from the order rather than named in it, and their cards say so. Mayor's offices without their own MMR chapter, such as the Office of Management and Budget, are not included.</p>
          </section>
          <section>
            <h3>Color and size</h3>
            <p>Tile color places each agency's spending between the smallest and the largest on a logarithmic scale, so a $9 million commission and a $38 billion school system both stay readable. Widths in the spending band and the group bars are proportional to dollars, not logarithmic.</p>
          </section>
          <section>
            <h3>Checks and limits</h3>
            <p>When a copy of the Open Data file is available, the build script compares every figure with it and stops if any differs by more than rounding. All ${agencies.length} agencies match. ${esc(meta.disclaimer)} Agency descriptions summarize the MMR chapters and the executive order. They are written for this site and are not official text.</p>
          </section>
        </div>
      </details>
      <div class="sign">
        <p>Fiscal ${meta.fiscalYear} figures. Made with public data.</p>
        <a class="github" href="${GITHUB}" target="_blank" rel="noopener" aria-label="anfelipecb on GitHub">${GITHUB_MARK}<span>anfelipecb</span></a>
      </div>
    </footer>
  `;
}

function renderCard(agency: Agency): string {
  const facts: Array<[string, string]> = [
    ["Authorized in the same row", money(agency.authorizedMillions)],
    ["Positions", people(agency.positions.actual)],
    ["Positions authorized", people(agency.positions.authorized)],
  ];
  if (agency.overtime) facts.push(["Overtime", money(agency.overtime.millions)]);
  if (agency.contractMillions != null) facts.push(["Human-services contracts", money(agency.contractMillions)]);
  if (agency.capitalMillions != null) {
    facts.push([agency.capitalLabel ?? "Capital commitments", money(agency.capitalMillions)]);
  }
  if (agency.revenueMillions != null) facts.push(["Revenue in this table", money(agency.revenueMillions)]);

  const lines = agency.positions.lines
    .map((line) => `${esc(line.label)} ${people(line.actual)}`)
    .join(", ");

  return `
    <div class="card-top">
      <p><span class="chip">${esc(agency.acronym)}</span><span class="where">${esc(clusterLabel(agency.portfolio))}</span></p>
      <button class="close" type="button" data-clear aria-label="Close ${esc(agency.acronym)}">
        <svg viewBox="0 0 16 16" width="14" height="14" aria-hidden="true"><path d="M3.5 3.5l9 9m0-9l-9 9" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/></svg>
      </button>
    </div>
    <h2>${esc(agency.name)}</h2>
    <p class="lede">${esc(agency.oneLiner)}</p>
    <div class="headline">
      <p class="headline-label">Spent in Fiscal 2026</p>
      <p class="headline-value">${esc(money(agency.expendituresMillions))}</p>
    </div>
    <dl class="facts">
      ${facts
        .map(
          ([label, value]) => `<div><dt>${esc(label)}</dt><dd>${esc(value)}</dd></div>`,
        )
        .join("")}
    </dl>
    ${lines ? `<p class="note">${lines}. ${agency.positions.note ? esc(agency.positions.note) : ""}</p>` : ""}
    <p class="note">${esc(agency.watch)}</p>
    <p class="note">${esc(agency.reportingNote)}</p>
    <p class="sources">
      <a target="_blank" rel="noopener" href="https://data.cityofnewyork.us/City-Government/Mayor-s-Management-Report-Agency-Resources/4qmi-txnk">MMR resources, FY2026</a>
    </p>
  `;
}
