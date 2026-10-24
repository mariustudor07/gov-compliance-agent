import {
  CATEGORY_LABEL,
  SEVERITY_LABEL,
  formatDate,
  groupBySeverity,
  legalBasis,
  severityReason,
} from "./format";

// A4 in points.
const PAGE_W = 595.28;
const PAGE_H = 841.89;
const MARGIN = 48;
const CONTENT_W = PAGE_W - MARGIN * 2;

const INK = [17, 19, 26];
const DIM = [91, 95, 107];
const FAINT = [107, 112, 128];
const RULE = [230, 232, 236];
const BRAND = [79, 70, 229];
const SEVERITY_RGB = {
  critical: [220, 38, 38],
  high: [194, 65, 12],
  medium: [161, 98, 7],
  low: [14, 116, 144],
  pass: [21, 128, 61],
};

const MAX_EVIDENCE_CHARS = 400;

/** jsPDF's built-in fonts only cover Latin-1, so swap the typographic
 * characters our copy uses for plain equivalents and drop anything else. */
function clean(value) {
  return String(value ?? "")
    .replace(/[\u2018\u2019]/g, "'")
    .replace(/[\u201C\u201D]/g, '"')
    .replace(/[\u2013\u2014]/g, "-")
    .replace(/\u2192/g, "->")
    .replace(/\u2026/g, "...")
    .replace(/[^\t\n\r\x20-\x7E\u00A0-\u00FF]/g, "");
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

/** Builds the report as a text-based PDF (selectable, small) and downloads it.
 * jsPDF is imported here, not at the top of the app, so it only loads when
 * someone actually asks for a PDF. */
export async function downloadReportPdf(result, { usingMock = false } = {}) {
  const { jsPDF } = await import("jspdf");
  const doc = new jsPDF({ unit: "pt", format: "a4" });
  const { url, scanned_at, scores = {}, findings = [], summary } = result;
  let y = MARGIN;

  function ensureSpace(height) {
    if (y + height > PAGE_H - MARGIN - 20) {
      doc.addPage();
      y = MARGIN;
    }
  }

  function write(str, { size = 10, style = "normal", font = "helvetica", color = INK, indent = 0, gap = 4 } = {}) {
    doc.setFont(font, style);
    doc.setFontSize(size);
    doc.setTextColor(...color);
    const lineHeight = size * 1.4;
    for (const line of doc.splitTextToSize(clean(str), CONTENT_W - indent)) {
      ensureSpace(lineHeight);
      doc.text(line, MARGIN + indent, y + size);
      y += lineHeight;
    }
    y += gap;
  }

  function rule(gap = 10) {
    ensureSpace(gap * 2);
    y += gap;
    doc.setDrawColor(...RULE);
    doc.setLineWidth(0.75);
    doc.line(MARGIN, y, PAGE_W - MARGIN, y);
    y += gap;
  }

  // Header
  write("GovCheck compliance report", { size: 20, style: "bold", color: BRAND, gap: 6 });
  write(url, { size: 12, style: "bold", gap: 2 });
  write(`Scanned ${formatDate(scanned_at)}`, { size: 9, color: FAINT, gap: 0 });
  if (usingMock) {
    write("Example data: this report was generated without the live scanner connected.", {
      size: 9,
      color: SEVERITY_RGB.medium,
      gap: 0,
    });
  }
  rule(12);

  // Scores, each with the law it's judged against
  write("Scores", { size: 13, style: "bold", gap: 6 });
  const rows = [["overall", "Overall"], ...Object.entries(CATEGORY_LABEL)];
  for (const [key, label] of rows) {
    const score = scores[key];
    ensureSpace(34);
    doc.setFont("helvetica", "bold");
    doc.setFontSize(11);
    doc.setTextColor(...INK);
    doc.text(clean(label), MARGIN, y + 11);
    const scoreText = typeof score === "number" ? `${Math.round(score)}/100` : "N/A";
    doc.text(scoreText, PAGE_W - MARGIN, y + 11, { align: "right" });
    y += 16;
    write(legalBasis(key, score).law, { size: 8.5, color: FAINT, gap: 6 });
  }

  if (summary) {
    rule(8);
    write("Summary", { size: 13, style: "bold", gap: 6 });
    write(summary, { size: 10, color: DIM, gap: 2 });
  }

  // Findings, most severe first
  for (const group of groupBySeverity(findings)) {
    rule(12);
    write(`${SEVERITY_LABEL[group.severity]} (${group.findings.length})`, {
      size: 13,
      style: "bold",
      color: SEVERITY_RGB[group.severity],
      gap: 8,
    });

    for (const f of group.findings) {
      ensureSpace(60);
      write(`${CATEGORY_LABEL[f.category] ?? f.category}`.toUpperCase(), {
        size: 8,
        style: "bold",
        color: FAINT,
        gap: 1,
      });
      write(f.title, { size: 11, style: "bold", gap: 3 });

      if (f.severity !== "pass") {
        const reason = severityReason(f).text;
        if (reason) write(`Why ${SEVERITY_LABEL[f.severity]}: ${reason}`, { size: 9.5, color: DIM, gap: 3 });
      }
      if (f.page) write(`Page: ${f.page}`, { size: 8.5, color: FAINT, gap: 3 });
      if (f.evidence) {
        const evidence =
          f.evidence.length > MAX_EVIDENCE_CHARS ? `${f.evidence.slice(0, MAX_EVIDENCE_CHARS)}...` : f.evidence;
        write(`Evidence: ${evidence}`, { size: 8, font: "courier", color: DIM, indent: 8, gap: 3 });
      }
      if (f.fix) write(`Fix: ${f.fix}`, { size: 9.5, gap: 3 });
      if (f.regulation) write(`Regulation: ${f.regulation}`, { size: 8.5, style: "italic", color: FAINT, gap: 3 });
      y += 8;
    }
  }

  // Footer on every page
  const pages = doc.getNumberOfPages();
  for (let i = 1; i <= pages; i++) {
    doc.setPage(i);
    doc.setFont("helvetica", "normal");
    doc.setFontSize(8);
    doc.setTextColor(...FAINT);
    doc.text("GovCheck  |  Not legal advice: an automated first pass.", MARGIN, PAGE_H - 28);
    doc.text(`Page ${i} of ${pages}`, PAGE_W - MARGIN, PAGE_H - 28, { align: "right" });
  }

  doc.save(fileName(url, scanned_at));
}
