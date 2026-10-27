/**
 * Point field behind the hero, in the same spirit as the NY Efficiency scan.
 * Points drift and link to their neighbors. A still field is drawn when the
 * user prefers reduced motion.
 */

interface Node {
  x: number;
  y: number;
  vx: number;
  vy: number;
  r: number;
}

const LINK_DISTANCE = 130;
const POINTER_REACH = 220;

export function mountHeroField(hero: HTMLElement): void {
  const canvas = hero.querySelector<HTMLCanvasElement>(".hero-field");
  const context = canvas?.getContext("2d");
  if (!canvas || !context) return;

  const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  const state = {
    width: 0,
    height: 0,
    nodes: [] as Node[],
    pointer: null as { x: number; y: number } | null,
    frame: 0,
  };

  const resize = () => {
    const rect = hero.getBoundingClientRect();
    const ratio = Math.min(window.devicePixelRatio || 1, 2);
    state.width = rect.width;
    state.height = rect.height;
    canvas.width = Math.round(state.width * ratio);
    canvas.height = Math.round(state.height * ratio);
    context.setTransform(ratio, 0, 0, ratio, 0, 0);
    state.nodes = seed(state.width, state.height);
    if (reduced) paint(context, state);
  };

  resize();
  if (reduced) {
    new ResizeObserver(resize).observe(hero);
    return;
  }

  hero.addEventListener("pointermove", (event) => {
    const rect = hero.getBoundingClientRect();
    state.pointer = { x: event.clientX - rect.left, y: event.clientY - rect.top };
  });
  hero.addEventListener("pointerleave", () => {
    state.pointer = null;
  });
  new ResizeObserver(resize).observe(hero);

  const tick = () => {
    state.frame = requestAnimationFrame(tick);
    if (document.hidden) return;
    drift(state.nodes, state.width, state.height, state.pointer);
    paint(context, state);
  };
  state.frame = requestAnimationFrame(tick);
}

function seed(width: number, height: number): Node[] {
  const count = Math.round(Math.min(140, Math.max(40, (width * height) / 14000)));
  return Array.from({ length: count }, () => ({
    x: Math.random() * width,
    y: Math.random() * height,
    vx: (Math.random() - 0.5) * 0.35,
    vy: (Math.random() - 0.5) * 0.35,
    r: Math.random() < 0.15 ? 2.4 : 1.4,
  }));
}

function drift(
  nodes: Node[],
  width: number,
  height: number,
  pointer: { x: number; y: number } | null,
): void {
  for (const node of nodes) {
    if (pointer) {
      const dx = pointer.x - node.x;
      const dy = pointer.y - node.y;
      const dist = Math.hypot(dx, dy);
      if (dist < POINTER_REACH && dist > 0.5) {
        const pull = ((POINTER_REACH - dist) / POINTER_REACH) * 0.11;
        node.vx += (dx / dist) * pull;
        node.vy += (dy / dist) * pull;
      }
    }
    node.vx *= 0.985;
    node.vy *= 0.985;
    const speed = Math.hypot(node.vx, node.vy);
    if (speed > 1.6) {
      node.vx = (node.vx / speed) * 1.6;
      node.vy = (node.vy / speed) * 1.6;
    }
    node.x += node.vx;
    node.y += node.vy;
    if (node.x < -20) node.x = width + 20;
    if (node.x > width + 20) node.x = -20;
    if (node.y < -20) node.y = height + 20;
    if (node.y > height + 20) node.y = -20;
  }
}

function paint(
  context: CanvasRenderingContext2D,
  state: { nodes: Node[]; width: number; height: number; pointer: { x: number; y: number } | null },
): void {
  const { nodes, width, height, pointer } = state;
  context.clearRect(0, 0, width, height);

  const glow = context.createRadialGradient(width * 0.78, height * 0.12, 0, width * 0.78, height * 0.12, width * 0.5);
  glow.addColorStop(0, "rgba(14, 116, 144, 0.6)");
  glow.addColorStop(1, "rgba(14, 116, 144, 0)");
  context.fillStyle = glow;
  context.fillRect(0, 0, width, height);

  for (let i = 0; i < nodes.length; i += 1) {
    for (let j = i + 1; j < nodes.length; j += 1) {
      const dx = nodes[i].x - nodes[j].x;
      const dy = nodes[i].y - nodes[j].y;
      const dist = Math.hypot(dx, dy);
      if (dist > LINK_DISTANCE) continue;
      const nearPointer = pointer
        ? Math.min(
            Math.hypot(pointer.x - nodes[i].x, pointer.y - nodes[i].y),
            Math.hypot(pointer.x - nodes[j].x, pointer.y - nodes[j].y),
          )
        : POINTER_REACH;
      const boost = nearPointer < POINTER_REACH ? 0.35 * (1 - nearPointer / POINTER_REACH) : 0;
      context.strokeStyle = `rgba(186, 230, 253, ${((1 - dist / LINK_DISTANCE) * 0.5 + boost).toFixed(3)})`;
      context.lineWidth = 1;
      context.beginPath();
      context.moveTo(nodes[i].x, nodes[i].y);
      context.lineTo(nodes[j].x, nodes[j].y);
      context.stroke();
    }
  }

  for (const node of nodes) {
    context.fillStyle = node.r > 2 ? "rgba(255, 255, 255, 0.92)" : "rgba(186, 230, 253, 0.85)";
    context.beginPath();
    context.arc(node.x, node.y, node.r, 0, Math.PI * 2);
    context.fill();
  }
}
