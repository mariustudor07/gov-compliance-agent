import {
  CATEGORY_COLOR,
  CATEGORY_LABEL,
  SEVERITY_LABEL,
  SEVERITY_ORDER,
  countBySeverity,
  formatDate,
  groupBySeverity,
  legalBasis,
  scoreTier,
  severityReason,
} from "./format";
import { planFor, planIntro } from "./improve";

// Draws the report to look like the web version (score rings, severity donut,
// improvement timeline, finding cards), as vector shapes and real text so the
// PDF stays sharp, small and selectable.

const PAGE_W = 595.28; // A4, points
const PAGE_H = 841.89;
const M = 40;
const W = PAGE_W - M * 2;
const BOTTOM = PAGE_H - M - 24; // leave room for the footer

const INK = [17, 19, 26];
const DIM = [91, 95, 107];
const FAINT = [107, 112, 128];
const BORDER = [230, 232, 236];
const RAISED = [248, 249, 251];
const TRACK = [238, 240, 244];
const BRAND = [79, 70, 229];
const WHITE = [255, 255, 255];
const AMBER = [180, 83, 9];
const SEV = {
  critical: [220, 38, 38],
  high: [194, 65, 12],
  medium: [161, 98, 7],
  low: [14, 116, 144],
  pass: [21, 128, 61],
};
const TIER = { good: [21, 128, 61], ok: [180, 83, 9], bad: [220, 38, 38], unknown: [148, 163, 184] };

const MAX_EVIDENCE_CHARS = 400;

const hexRgb = (hex) => [1, 3, 5].map((i) => parseInt(hex.slice(i, i + 2), 16));
const tint = (rgb, amount) => rgb.map((c) => Math.round(c * amount + 255 * (1 - amount)));
const catRgb = (category) => hexRgb(CATEGORY_COLOR[category] || CATEGORY_COLOR.overall);

// jsPDF's built-in fonts only cover Latin-1: swap the typographic characters
// our copy uses for plain ones, and drop anything else.
const ch = (code) => String.fromCharCode(code);
const REPLACEMENTS = [
  [ch(0x2018), "'"],
  [ch(0x2019), "'"],
  [ch(0x201c), '"'],
  [ch(0x201d), '"'],
  [ch(0x2013), "-"],
  [ch(0x2014), "-"],
  [ch(0x2192), "->"],
  [ch(0x2026), "..."],
  [ch(0x2022), "-"],
];

function clean(value) {
  let text = String(value ?? "");
  for (const [from, to] of REPLACEMENTS) text = text.split(from).join(to);
  return Array.from(text)
    .filter((c) => {
      const code = c.charCodeAt(0);
      return code === 9 || code === 10 || code === 13 || (code >= 32 && code <= 126) || (code >= 160 && code <= 255);
    })
    .join("");
}

function fileName(url, scannedAt) {
  let host = "site";
  try {
    host = new URL(url).hostname.replace(/^www\./, "");
  } catch {
    // keep the fallback
  }
  const date = (scannedAt || new Date().toISOString()).slice(0, 10);
  return `govcheck-${host}-${date}.pdf`;
}

/** Builds and downloads the PDF. jsPDF is imported here rather than at the top
 * of the app, so it only loads when someone actually asks for a PDF. */
export async function downloadReportPdf(result, { usingMock = false } = {}) {
  const { jsPDF } = await import("jspdf");
  const doc = new jsPDF({ unit: "pt", format: "a4" });
  const { url, scanned_at, scores = {}, findings = [], summary } = result;
  let y = M;

  // ---------- drawing helpers ----------

  const lineHeight = (size) => size * 1.4;

  function font(size, style = "normal", color = INK, family = "helvetica") {
    doc.setFont(family, style);
    doc.setFontSize(size);
    doc.setTextColor(...color);
  }

  function wrap(text, width, size, style = "normal", family = "helvetica") {
    doc.setFont(family, style);
    doc.setFontSize(size);
    return doc.splitTextToSize(clean(text), width);
  }

  /** Draws pre-wrapped lines with their top at `top`; returns the height used. */
  function drawLines(lines, x, top, size, style = "normal", color = INK, family = "helvetica") {
    font(size, style, color, family);
    lines.forEach((line, i) => doc.text(line, x, top + size + i * lineHeight(size)));
    return lines.length * lineHeight(size);
  }

  function need(height) {
    if (y + height > BOTTOM) {
      doc.addPage();
      y = M;
    }
  }

  function card(x, top, width, height, fill = WHITE) {
    doc.setFillColor(...fill);
    doc.setDrawColor(...BORDER);
    doc.setLineWidth(0.75);
    doc.roundedRect(x, top, width, height, 6, 6, "FD");
  }

  function stripe(x, top, height, color) {
    doc.setFillColor(...color);
    doc.roundedRect(x, top, 3, height, 1.5, 1.5, "F");
  }

  /** Arc clockwise from `start` degrees (0 = 12 o'clock), as short segments. */
  function arc(cx, cy, r, start, sweep, color, width, cap = "round") {
    if (sweep <= 0) return;
    doc.setDrawColor(...color);
    doc.setLineWidth(width);
    doc.setLineCap(cap);
    const point = (deg) => {
      const rad = ((deg - 90) * Math.PI) / 180;
      return [cx + r * Math.cos(rad), cy + r * Math.sin(rad)];
    };
    const steps = Math.max(2, Math.ceil(sweep / 3));
    let [px, py] = point(start);
    for (let i = 1; i <= steps; i++) {
      const [nx, ny] = point(start + (sweep * i) / steps);
      doc.line(px, py, nx, ny);
      px = nx;
      py = ny;
    }
    doc.setLineCap("butt");
  }

  /** Solid donut slice (an annular sector), so slices have no seams. */
  function sector(cx, cy, rOuter, rInner, start, sweep, color) {
    if (sweep <= 0) return;
    const point = (r, deg) => {
      const rad = ((deg - 90) * Math.PI) / 180;
      return [cx + r * Math.cos(rad), cy + r * Math.sin(rad)];
    };
    const steps = Math.max(2, Math.ceil(sweep / 3));
    const points = [];
    for (let i = 0; i <= steps; i++) points.push(point(rOuter, start + (sweep * i) / steps));
    for (let i = steps; i >= 0; i--) points.push(point(rInner, start + (sweep * i) / steps));
    const [x0, y0] = points[0];
    const deltas = points.slice(1).map(([x, py], i) => [x - points[i][0], py - points[i][1]]);
    doc.setFillColor(...color);
    doc.lines(deltas, x0, y0, [1, 1], "F", true);
  }

  function ring(cx, cy, r, width) {
    doc.setDrawColor(...TRACK);
    doc.setLineWidth(width);
    doc.circle(cx, cy, r, "S");
  }

  /** Rounded pill with centred text; returns its width. */
  function pill(text, x, top, color, { size = 7.5, align = "left" } = {}) {
    font(size, "bold", color);
    const width = doc.getTextWidth(clean(text)) + 12;
    const left = align === "right" ? x - width : x;
    doc.setFillColor(...tint(color, 0.12));
    doc.roundedRect(left, top, width, 13, 6.5, 6.5, "F");
    doc.text(clean(text), left + width / 2, top + 9.2, { align: "center" });
    return width;
  }

  function heading(text, color = INK, gapBefore = 18) {
    need(gapBefore + 24);
    y += gapBefore;
    font(13, "bold", color);
    doc.text(clean(text), M, y + 13);
    y += 22;
  }

  // ---------- header ----------

  font(10, "bold", BRAND);
  doc.text("GovCheck", M, y + 10);
  font(8, "normal", FAINT);
  doc.text("Compliance report", PAGE_W - M, y + 10, { align: "right" });
  y += 18;
  doc.setDrawColor(...BORDER);
  doc.setLineWidth(0.75);
  doc.line(M, y, PAGE_W - M, y);
  y += 16;

  y += drawLines(wrap(url, W, 17, "bold"), M, y, 17, "bold");
  y += drawLines([`Scanned ${formatDate(scanned_at)}`], M, y, 9, "normal", FAINT) + 10;

  if (usingMock) {
    const lines = wrap("Example data: this report was generated without the live scanner connected.", W - 24, 9);
    const height = lines.length * lineHeight(9) + 14;
    card(M, y, W, height, tint(AMBER, 0.1));
    drawLines(lines, M + 12, y + 7, 9, "normal", INK);
    y += height + 12;
  }

  // ---------- score rings ----------

  const tiles = [["overall", "Overall"], ...Object.entries(CATEGORY_LABEL)];
  const gap = 8;
  const tileW = (W - gap * (tiles.length - 1)) / tiles.length;
  const tileH = 100;
  need(tileH + 10);
  tiles.forEach(([key, label], i) => {
    const x = M + i * (tileW + gap);
    const score = scores[key];
    const color = TIER[scoreTier(score)];
    const cx = x + tileW / 2;
    const cy = y + 40;
    const r = key === "overall" ? 27 : 24;
    card(x, y, tileW, tileH);
    ring(cx, cy, r, 5);
    if (typeof score === "number") arc(cx, cy, r, 0, (Math.max(0, Math.min(score, 100)) / 100) * 359.9, color, 5);
    font(key === "overall" ? 18 : 16, "bold", color);
    doc.text(typeof score === "number" ? String(Math.round(score)) : "N/A", cx, cy + 6, { align: "center" });
    font(8.5, "normal", DIM);
    const labelW = doc.getTextWidth(label);
    doc.setFillColor(...catRgb(key));
    doc.circle(cx - labelW / 2 - 4, y + 82.5, 2.2, "F");
    doc.text(label, cx + 3, y + 85, { align: "center" });
  });
  y += tileH + 10;

  // What each score is judged against (the web page shows this on tap)
  for (const [key, label] of tiles) {
    const lines = wrap(`${label}: ${legalBasis(key, scores[key]).law}`, W, 7.5);
    need(lines.length * lineHeight(7.5));
    y += drawLines(lines, M, y, 7.5, "normal", FAINT);
  }

  // ---------- summary callout ----------

  if (summary) {
    const lines = wrap(summary, W - 30, 9.5);
    const height = lines.length * lineHeight(9.5) + 20;
    need(height + 16);
    y += 14;
    card(M, y, W, height, RAISED);
    stripe(M + 1, y + 1, height - 2, BRAND);
    drawLines(lines, M + 16, y + 10, 9.5);
    y += height;
  }

  // ---------- severity donut ----------

  const counts = countBySeverity(findings);
  const total = SEVERITY_ORDER.reduce((sum, key) => sum + counts[key], 0);
  if (total > 0) {
    const height = 112;
    need(height + 16);
    y += 14;
    card(M, y, W, height);
    const cx = M + 72;
    const cy = y + height / 2;
    ring(cx, cy, 36, 12);
    let start = 0;
    for (const key of SEVERITY_ORDER) {
      if (!counts[key]) continue;
      const sweep = (counts[key] / total) * 360;
      sector(cx, cy, 42, 30, start + 1, sweep - 2, SEV[key]);
      start += sweep;
    }
    font(17, "bold", INK);
    doc.text(String(total), cx, cy + 3, { align: "center" });
    font(6.5, "normal", FAINT);
    doc.text("CHECKS", cx, cy + 13, { align: "center" });

    const present = SEVERITY_ORDER.filter((key) => counts[key]);
    let ly = cy - ((present.length - 1) * 15) / 2 + 3;
    for (const key of present) {
      doc.setFillColor(...SEV[key]);
      doc.circle(M + 150, ly - 3, 3.5, "F");
      font(9.5, "normal", DIM);
      doc.text(`${counts[key]} ${SEVERITY_LABEL[key]}`, M + 160, ly);
      ly += 15;
    }
    y += height;
  }

  // ---------- how to improve ----------

  const plan = planFor(findings, scores);
  const introLines = wrap(planIntro(plan), W, 9.5);
  const cardX = M + 32;
  const cardW = W - 32;
  const innerW = cardW - 24;
  const stepCards = plan.steps.map((step) => {
    const actionLines = wrap(step.action, innerW, 10, "bold");
    const fixesLines = wrap(`Fixes: ${step.findings.map((f) => f.title).join("; ")}`, innerW, 8.5);
    const height = 12 + 13 + 6 + actionLines.length * lineHeight(10) + 3 + fixesLines.length * lineHeight(8.5) + 10;
    return { step, actionLines, fixesLines, height };
  });

  // Keep the heading on the same page as the intro and the first step.
  need(18 + 22 + introLines.length * lineHeight(9.5) + 6 + (stepCards[0]?.height ?? 0));
  heading("How to improve your score");
  y += drawLines(introLines, M, y - 4, 9.5, "normal", DIM) + 6;

  stepCards.forEach(({ step, actionLines, fixesLines, height }, i) => {
    need(height + 10);

    if (i < plan.steps.length - 1) {
      doc.setDrawColor(...BORDER);
      doc.setLineWidth(1);
      doc.line(M + 12, y + 12, M + 12, y + height + 10);
    }
    doc.setFillColor(...SEV[step.severity]);
    doc.circle(M + 12, y + 13, 12, "F");
    font(9, "bold", WHITE);
    doc.text(String(i + 1), M + 12, y + 16.2, { align: "center" });

    card(cardX, y, cardW, height);
    font(7.5, "bold", catRgb(step.category));
    doc.text((CATEGORY_LABEL[step.category] ?? step.category).toUpperCase(), cardX + 12, y + 21);
    if (plan.showGains && step.overallGain > 0) {
      pill(
        `+${step.categoryGain} ${CATEGORY_LABEL[step.category]}  |  +${step.overallGain} overall`,
        cardX + cardW - 12,
        y + 11,
        SEV.pass,
        { align: "right" }
      );
    } else {
      pill(SEVERITY_LABEL[step.severity], cardX + cardW - 12, y + 11, SEV[step.severity], { align: "right" });
    }
    let top = y + 12 + 13 + 6;
    top += drawLines(actionLines, cardX + 12, top, 10, "bold") + 3;
    drawLines(fixesLines, cardX + 12, top, 8.5, "normal", FAINT);
    y += height + 10;
  });

  // ---------- findings ----------

  /** Measures a finding card and returns its height plus a draw() that renders it at the current y. */
  function findingCard(f) {
    const innerFindW = W - 30;
    const titleLines = wrap(f.title, innerFindW, 10.5, "bold");
    const reason = f.severity !== "pass" ? severityReason(f).text : "";
    const whyLines = reason ? wrap(`Why ${SEVERITY_LABEL[f.severity]}: ${reason}`, innerFindW, 9) : [];
    const pageLines = f.page ? wrap(f.page, innerFindW, 8) : [];
    const evidenceText = f.evidence
      ? f.evidence.length > MAX_EVIDENCE_CHARS
        ? `${f.evidence.slice(0, MAX_EVIDENCE_CHARS)}...`
        : f.evidence
      : "";
    const evidenceLines = evidenceText ? wrap(evidenceText, innerFindW - 16, 7.5, "normal", "courier") : [];
    const fixLines = f.fix ? wrap(`Fix: ${f.fix}`, innerFindW, 9.5) : [];
    const regLines = f.regulation ? wrap(f.regulation, innerFindW, 8, "italic") : [];

    const block = (lines, size, extra = 4) => (lines.length ? lines.length * lineHeight(size) + extra : 0);
    const evidenceH = evidenceLines.length ? evidenceLines.length * lineHeight(7.5) + 12 : 0;
    const height =
      12 + 13 + 7 +
      block(titleLines, 10.5) +
      block(whyLines, 9) +
      block(pageLines, 8) +
      (evidenceH ? evidenceH + 6 : 0) +
      block(fixLines, 9.5) +
      block(regLines, 8, 0) +
      10;

    function draw() {
      card(M, y, W, height);
      stripe(M + 1, y + 1, height - 2, catRgb(f.category));
      const x = M + 16;
      const badgeW = pill(SEVERITY_LABEL[f.severity], x, y + 11, SEV[f.severity]);
      font(7.5, "bold", catRgb(f.category));
      doc.text((CATEGORY_LABEL[f.category] ?? f.category).toUpperCase(), x + badgeW + 8, y + 20.5);

      let top = y + 12 + 13 + 7;
      top += drawLines(titleLines, x, top, 10.5, "bold") + 4;
      if (whyLines.length) top += drawLines(whyLines, x, top, 9, "normal", DIM) + 4;
      if (pageLines.length) top += drawLines(pageLines, x, top, 8, "normal", FAINT) + 4;
      if (evidenceH) {
        doc.setFillColor(...RAISED);
        doc.setDrawColor(...BORDER);
        doc.setLineWidth(0.5);
        doc.roundedRect(x, top, innerFindW, evidenceH, 4, 4, "FD");
        drawLines(evidenceLines, x + 8, top + 6, 7.5, "normal", DIM, "courier");
        top += evidenceH + 6;
      }
      if (fixLines.length) top += drawLines(fixLines, x, top, 9.5) + 4;
      if (regLines.length) drawLines(regLines, x, top, 8, "italic", FAINT);
    }

    return { height, draw };
  }

  for (const group of groupBySeverity(findings)) {
    const cards = group.findings.map(findingCard);
    // Keep each severity heading on the same page as its first card.
    need(14 + 22 + cards[0].height + 10);
    heading(`${SEVERITY_LABEL[group.severity]} (${group.findings.length})`, SEV[group.severity], 14);
    for (const c of cards) {
      need(c.height + 10);
      c.draw();
      y += c.height + 10;
    }
  }

  // ---------- footer on every page ----------

  const pages = doc.getNumberOfPages();
  for (let i = 1; i <= pages; i++) {
    doc.setPage(i);
    doc.setDrawColor(...BORDER);
    doc.setLineWidth(0.75);
    doc.line(M, PAGE_H - 40, PAGE_W - M, PAGE_H - 40);
    font(7.5, "normal", FAINT);
    doc.text("GovCheck  |  Not legal advice: an automated first pass.", M, PAGE_H - 28);
    doc.text(`Page ${i} of ${pages}`, PAGE_W - M, PAGE_H - 28, { align: "right" });
  }

  doc.save(fileName(url, scanned_at));
}
