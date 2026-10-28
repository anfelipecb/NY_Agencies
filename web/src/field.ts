import * as d3 from "d3";
import catalog from "../../data/agencies.json";
import { esc, moneyTile } from "./format";
import { INK_LIGHT, PALETTES, type Mode } from "./palette";

export type Agency = (typeof catalog.agencies)[number];


function relLum(hex: string): number {
  const color = d3.color(hex)?.rgb();
  if (!color) return 0;
  const channel = (value: number) => {
    const s = value / 255;
    return s <= 0.03928 ? s / 12.92 : ((s + 0.055) / 1.055) ** 2.4;
  };
  return 0.2126 * channel(color.r) + 0.7152 * channel(color.g) + 0.0722 * channel(color.b);
}

function contrastRatio(fill: string, ink: string): number {
  const lighter = Math.max(relLum(fill), relLum(ink));
  const darker = Math.min(relLum(fill), relLum(ink));
  return (lighter + 0.05) / (darker + 0.05);
}

export const RAMP_STOPS = [0, 0.28, 0.52, 0.76, 1];

const MODES: Mode[] = ["light", "dark"];

const ramps = Object.fromEntries(
  MODES.map((mode) => [
    mode,
    d3.scaleLinear<string>().domain(RAMP_STOPS).range(PALETTES[mode].ramp).interpolate(d3.interpolateLab),
  ]),
) as Record<Mode, d3.ScaleLinear<string, string>>;

export function rampColor(t: number, mode: Mode): string {
  return ramps[mode](Math.min(1, Math.max(0, t)));
}

export function rampGradient(mode: Mode): string {
  return `linear-gradient(90deg, ${RAMP_STOPS.map((t) => `${rampColor(t, mode)} ${t * 100}%`).join(", ")})`;
}

export function displayMillions(agency: Agency): number | null {
  return agency.expendituresMillions ?? agency.adoptedMillions ?? null;
}

export function orderedAgencies(agencies: Agency[]): Agency[] {
  return [...agencies].sort((a, b) => {
    const left = displayMillions(a);
    const right = displayMillions(b);
    if (left == null && right == null) return a.acronym.localeCompare(b.acronym);
    if (left == null) return 1;
    if (right == null) return -1;
    return right - left;
  });
}

export function spendRange(agencies: Agency[]): [number, number] {
  const values = agencies
    .map((agency) => agency.expendituresMillions)
    .filter((value): value is number => value != null && value > 0);
  return [Math.min(...values), Math.max(...values)];
}

export function toneFor(agencies: Agency[], spend: number | null, mode: Mode): string | null {
  if (spend == null || spend <= 0) return null;
  const [min, max] = spendRange(agencies);
  if (min === max) return rampColor(1, mode);
  const t = (Math.log10(spend) - Math.log10(min)) / (Math.log10(max) - Math.log10(min));
  return rampColor(t, mode);
}

export function inkFor(fill: string, mode: Mode): string {
  const dark = PALETTES[mode].inkDark;
  return contrastRatio(fill, dark) > contrastRatio(fill, INK_LIGHT) ? dark : INK_LIGHT;
}

// Fill and ink for both palettes as CSS custom properties, so switching modes needs no re-render.
// The stylesheet picks the -l or -d pair for the active mode.
export function toneVars(agencies: Agency[], spend: number | null, name = "tone", ink = "ink"): string | null {
  const parts: string[] = [];
  for (const mode of MODES) {
    const tone = toneFor(agencies, spend, mode);
    if (!tone) return null;
    const key = mode === "light" ? "l" : "d";
    parts.push(`--${name}-${key}:${tone}`, `--${ink}-${key}:${inkFor(tone, mode)}`);
  }
  return parts.join(";");
}

export type Portfolio = { id: string; label: string; blurb: string };

export function clusterLabel(id: string): string {
  return CLUSTER_NAME[id] ?? id;
}

const CLUSTER_NAME: Record<string, string> = {
  fdm: "First Deputy Mayor",
  operations: "Operations",
  hhs: "Health and human services",
  housing: "Housing and planning",
  economic: "Economic justice",
  counsel: "Chief Counsel",
  staff: "Chief of Staff",
  comms: "Communications",
  safety: "Community safety",
  mayor: "Office of the Mayor",
};

export function markedAmount(agency: Agency): string {
  if (agency.figure === "included") return "Not separate*";
  if (agency.figure === "adopted") return `${moneyTile(agency.adoptedMillions)}*`;
  return moneyTile(agency.expendituresMillions);
}

let readingOrder: Agency[] = [];

export function visualOrder(): Agency[] {
  return readingOrder;
}

export function totalSpend(agencies: Agency[]): number {
  return agencies.reduce((sum, agency) => sum + (agency.expendituresMillions ?? 0), 0);
}

export function renderSegments(members: Agency[], agencies: Agency[], labelShare = 1): string {
  const city = totalSpend(agencies);
  return members
    .filter((agency) => agency.expendituresMillions != null)
    .map((agency) => {
      const spend = agency.expendituresMillions ?? 0;
      const vars = toneVars(agencies, spend) ?? "";
      const share = spend / city;
      const label = share >= labelShare ? `<span>${esc(agency.acronym)}</span>` : "";
      return `<button type="button" class="seg" tabindex="-1" data-id="${esc(agency.id)}" aria-label="${esc(`${agency.acronym}, ${moneyTile(spend)}`)}"
        style="flex-grow:${spend};${vars}">${label}</button>`;
    })
    .join("");
}

function renderCluster(portfolio: Portfolio, members: Agency[], agencies: Agency[]): string {
  const total = totalSpend(members);
  const share = (total / totalSpend(agencies)) * 100;
  const count = members.length === 1 ? "1 agency" : `${members.length} agencies`;
  const label = CLUSTER_NAME[portfolio.id] ?? portfolio.label;

  const tiles = members
    .map((agency, index) => {
      const shown = displayMillions(agency);
      const vars = toneVars(agencies, agency.expendituresMillions ?? shown);
      const style = vars ? ` style="${vars}"` : "";
      const amount = markedAmount(agency);
      return `
        <button type="button" class="tile${vars ? "" : " is-empty"}${index === 0 && (agency.expendituresMillions ?? 0) >= 10000 ? " is-major" : ""}" role="listitem" data-id="${esc(agency.id)}"
          aria-label="${esc(`${agency.acronym}, ${agency.name}, ${amount}`)}"${style}>
          <span class="mark">${esc(agency.acronym)}</span>
          <span class="amount">${esc(amount)}</span>
        </button>`;
    })
    .join("");

  return `
    <section class="cluster${members.length ? "" : " is-empty-cluster"}" aria-label="${esc(label)}">
      <header class="cluster-head">
        <h2>${esc(label)}</h2>
        <p class="cluster-meta">
          ${members.length ? `<span>${count}</span>${total > 0 ? `<span>${esc(moneyTile(total))}</span><span>${share < 1 ? "<1" : Math.round(share)}% of city spending</span>` : ""}` : ""}
        </p>
        ${total > 0 ? `<div class="share" aria-hidden="true"><div class="share-fill" style="width:${share}%">${renderSegments(members, agencies, 2)}</div></div>` : ""}
        <p class="cluster-blurb">${esc(members.length ? portfolio.blurb : `No agency chapter of its own. ${portfolio.blurb}`)}</p>
      </header>
      ${members.length ? `<div class="tiles" role="list">${tiles}</div>` : ""}
    </section>`;
}

export function renderField(
  host: HTMLElement,
  agencies: Agency[],
  portfolios: Portfolio[],
  selectedId: string | null,
  onSelect: (id: string) => void,
): void {
  if (!host.dataset.built) {
    const groups = portfolios.map((portfolio) => ({
      portfolio,
      members: orderedAgencies(agencies.filter((agency) => agency.portfolio === portfolio.id)),
    }));
    readingOrder = groups.flatMap((group) => group.members);
    host.innerHTML = `<div class="field-flow">${groups
      .map((group) => renderCluster(group.portfolio, group.members, agencies))
      .join("")}</div>`;
    host.dataset.built = "true";

    host.querySelectorAll<HTMLElement>(".tile").forEach((tile, index) => {
      tile.style.setProperty("--i", String(index));
    });

    host.addEventListener("click", (event) => {
      const node = (event.target as HTMLElement).closest<HTMLElement>(".tile, .seg");
      if (node?.dataset.id) onSelect(node.dataset.id);
    });

  }

  document.querySelectorAll<HTMLElement>(".tile, .seg").forEach((node) => {
    const current = node.dataset.id === selectedId;
    node.classList.toggle("is-selected", current);
    if (!node.classList.contains("tile")) return;
    if (current) node.setAttribute("aria-current", "true");
    else node.removeAttribute("aria-current");
  });
  host.classList.toggle("has-selection", Boolean(selectedId));

  if (selectedId) {
    host.querySelector<HTMLElement>(`.tile[data-id="${CSS.escape(selectedId)}"]`)?.scrollIntoView({ block: "nearest" });
  }
}

export function bindTooltip(host: HTMLElement, agencies: Agency[]): void {
  const tip = document.createElement("div");
  tip.className = "tip";
  tip.setAttribute("aria-hidden", "true");
  document.body.append(tip);

  const show = (tile: HTMLElement) => {
    const agency = agencies.find((item) => item.id === tile.dataset.id);
    if (!agency) return;
    const shown = displayMillions(agency);
    tip.setAttribute("style", toneVars(agencies, agency.expendituresMillions ?? shown) ?? "");
    tip.innerHTML = `<strong>${esc(agency.name)}</strong><em>${esc(markedAmount(agency))}</em><span>${esc(agency.oneLiner)}</span>`;
    const box = tile.getBoundingClientRect();
    tip.classList.add("is-on");
    const width = tip.offsetWidth;
    const left = Math.min(Math.max(12, box.left + box.width / 2 - width / 2), window.innerWidth - width - 12);
    const above = box.top - tip.offsetHeight - 10;
    tip.style.left = `${left}px`;
    tip.style.top = `${above > 8 ? above : box.bottom + 10}px`;
  };
  const hide = () => tip.classList.remove("is-on");

  const fine = window.matchMedia("(hover: hover)");
  host.addEventListener("pointerover", (event) => {
    if (!fine.matches) return;
    const tile = (event.target as HTMLElement).closest<HTMLElement>(".tile, .seg");
    if (tile) show(tile);
  });
  host.addEventListener("pointerout", (event) => {
    const next = (event.relatedTarget as HTMLElement | null)?.closest(".tile, .seg");
    if (!next) hide();
  });
  host.addEventListener("focusin", (event) => {
    const tile = (event.target as HTMLElement).closest<HTMLElement>(".tile");
    if (tile?.matches(":focus-visible")) show(tile);
  });
  host.addEventListener("focusout", hide);
  host.addEventListener("scroll", hide, { passive: true, capture: true });
}
