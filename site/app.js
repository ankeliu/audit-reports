/* Submission page. Moving the repo (e.g. to stellar/audit-reports) only changes REPO below. */
(function () {
  "use strict";

  const REPO = "ankeliu/audit-reports";
  const BRANCH = "main";
  const GITHUB = `https://github.com/${REPO}`;
  const ISSUE_TEMPLATE = "submit-report.yml";
  const PR_VALUE_LIMIT = 8000; // GitHub's /new?value= prefill breaks on long URLs
  const CONVERTIBLE = {
    HAL: (u) => u.hostname.endsWith("halborn.com") && u.pathname.startsWith("/audits/"),
    RV: (u) => u.hostname.endsWith("runtimeverification.com"),
    VER: (u) => u.hostname.endsWith("veridise.com"),
  };

  const $ = (id) => document.getElementById(id);
  let ab = null;
  let vocab = null;
  let pdfFile = null;

  async function fetchJSON(path) {
    // Deployed: schema/ and reports/ sit next to the page. Local preview from the repo root: one level up.
    for (const prefix of ["", "../"]) {
      try {
        const res = await fetch(prefix + path, { cache: "no-cache" });
        if (res.ok) return await res.json();
      } catch (_) {
        /* try the next location */
      }
    }
    throw new Error(`could not load ${path}`);
  }

  function el(tag, attrs, ...children) {
    const node = document.createElement(tag);
    for (const [k, v] of Object.entries(attrs || {})) {
      if (k === "class") node.className = v;
      else node.setAttribute(k, v);
    }
    for (const child of children) node.append(child instanceof Node ? child : document.createTextNode(String(child)));
    return node;
  }

  const slugify = (s) => String(s || "").toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-+|-+$/g, "");
  const firmOption = (abbrev) => `${vocab.firms[abbrev]} (${abbrev})`;

  function issueUrl(fields) {
    const params = new URLSearchParams({ template: ISSUE_TEMPLATE, title: `Report submission: ${fields.title || ""}` });
    for (const [k, v] of Object.entries(fields)) if (v && k !== "title") params.set(k, v);
    return `${GITHUB}/issues/new?${params}`;
  }

  // ------------------------------------------------------------------ check

  async function init() {
    try {
      const [rules, schema, v] = await Promise.all([
        fetchJSON("schema/parse-rules.json"),
        fetchJSON("schema/report-schema.json"),
        fetchJSON("schema/vocab.json"),
      ]);
      vocab = v;
      ab = AuditBank.create({ rules, vocab, schema, yaml: jsyaml, Ajv: ajv2020.default });
      $("loading").textContent = "";
    } catch (e) {
      $("loading").textContent = `Could not load the schema (${e.message}).`;
      $("check-btn").disabled = true;
    }
    setupMarked();
    setupConvertForm();
    setupReference();
    loadArchive();
  }

  function setupMarked() {
    const escape = (s) => s.replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]);
    const safeHref = (href) => /^(https?:|mailto:|#|\/|\.{0,2}\/)/i.test(href || "") ? href : "#";
    marked.use({
      gfm: true,
      renderer: {
        html: (token) => escape(token.text || token.raw || ""),
        link(token) {
          const text = this.parser.parseInline(token.tokens);
          return `<a href="${escape(safeHref(token.href))}" rel="noopener nofollow">${text}</a>`;
        },
        image: (token) => escape(`[image: ${token.text || token.href}]`),
      },
    });
  }

  function runCheck() {
    if (!ab) return;
    const text = $("report-text").value;
    if (!text.trim()) return;
    const { report, problems } = ab.validateText(text);
    const errors = problems.filter((p) => p.level === "error").length;
    const warnings = problems.length - errors;

    const verdict = $("verdict");
    verdict.className = "verdict " + (errors ? "fail" : warnings ? "warn" : "ok");
    verdict.textContent = errors
      ? `Failed: ${errors} error(s), ${warnings} warning(s)`
      : warnings
        ? `Passed with ${warnings} warning(s)`
        : "Passed: no problems found";

    const tbody = $("problems").querySelector("tbody");
    tbody.replaceChildren(
      ...problems.map((p) =>
        el("tr", {},
          el("td", {}, el("span", { class: `level ${p.level}` }, p.level)),
          el("td", {}, el("code", {}, p.code)),
          el("td", {}, el("code", {}, p.path)),
          el("td", {}, p.message)),
      ),
    );
    $("problems-wrap").hidden = !problems.length;

    const notes = report ? collectNotes(report) : [];
    $("notes-wrap").hidden = !notes.length;
    $("notes-summary").textContent = `${notes.length} CONVERSION-NOTE(s) for the firm reviewer`;
    $("notes").replaceChildren(...notes.map((n) => el("li", {}, n)));

    renderPreview(text);
    renderSubmit(report, errors, text);
    $("result").hidden = false;
  }

  function collectNotes(report) {
    const notes = [...(report.conversion_notes || [])];
    for (const f of report.findings || []) for (const n of f.conversion_notes || []) notes.push(`${f.id}: ${n}`);
    return notes;
  }

  function renderPreview(text) {
    const body = text.replace(/^﻿?---\n[\s\S]*?\n---[ \t]*\n?/, "");
    $("preview").innerHTML = marked.parse(body); // raw HTML is escaped and links are restricted in setupMarked
  }

  function renderSubmit(report, errors, text) {
    const box = $("submit-md");
    if (!report || errors) {
      box.hidden = true;
      return;
    }
    const meta = report.report || {};
    const abbrev = ab.firmAbbrev(meta.audit_firm);
    const slug = slugify(meta.client);
    const file = `${slug}--${(abbrev || "firm").toLowerCase()}--${meta.report_date}.md`;
    $("submit-issue").href = issueUrl({
      title: `${meta.client} (${meta.audit_firm})`,
      firm: abbrev ? firmOption(abbrev) : "",
      project_slug: slug,
    });
    const prParams = new URLSearchParams({ filename: `reports/${slug}/${file}`, value: text });
    const prUrl = `${GITHUB}/new/${BRANCH}?${prParams}`;
    const fits = prUrl.length <= PR_VALUE_LIMIT;
    $("submit-pr").hidden = !fits;
    if (fits) $("submit-pr").href = prUrl;
    $("submit-hint").textContent =
      `In the issue, drag ${file} into the Attachment field (links can't carry files).` +
      (fits ? "" : " This report is too large to prefill a PR, so use the issue.");
    box.hidden = false;
  }

  const isPdf = (file) => file.type === "application/pdf" || /\.pdf$/i.test(file.name);

  function loadFile(file) {
    if (!file) return;
    if (isPdf(file)) {
      // A PDF needs converting: hand it to the submit form instead of parsing it as markdown.
      setPdf(file);
      $("submit").scrollIntoView({ behavior: "smooth" });
      return;
    }
    const reader = new FileReader();
    reader.onload = () => {
      $("report-text").value = reader.result;
      runCheck();
    };
    reader.readAsText(file);
  }

  // ---------------------------------------------------------------- convert

  function detectFromName(name) {
    if (/^VAR-/i.test(name)) return "VER";
    if (/_report_/i.test(name)) return "RV";
    return "";
  }

  function shortName(link) {
    try {
      const parts = new URL(link).pathname.split("/").filter(Boolean);
      return parts[0] === "audits" && parts[1] ? parts[1] : decodeURIComponent(parts.pop() || link);
    } catch (_) {
      return link;
    }
  }

  function applyDetection(firm, label) {
    if (!firm) return;
    $("firm").value = firm;
    $("detected").textContent = `Detected ${vocab ? vocab.firms[firm] : firm} from the ${label}.`;
  }

  function setPdf(file) {
    pdfFile = file;
    $("source-url").value = "";
    $("pdf-label").replaceChildren(el("strong", {}, file.name), " selected · choose another");
    $("pdf-name").textContent = file.name;
    $("pdf-next").hidden = false;
    $("convert-btn").textContent = "Open issue to attach the PDF";
    const firm = detectFromName(file.name);
    $("detected").textContent = "";
    applyDetection(firm, "file name");
  }

  function setupConvertForm() {
    const select = $("firm");
    select.replaceChildren(el("option", { value: "" }, "Select…"));
    for (const abbrev of Object.keys(CONVERTIBLE)) select.append(el("option", { value: abbrev }, vocab ? firmOption(abbrev) : abbrev));

    $("source-url").addEventListener("input", () => {
      let url;
      try {
        url = new URL($("source-url").value);
      } catch (_) {
        $("detected").textContent = "";
        return;
      }
      if (pdfFile) {
        pdfFile = null;
        $("pdf-file").value = "";
        $("pdf-label").replaceChildren(el("strong", {}, "Choose the PDF"), " or drop it here");
        $("pdf-next").hidden = true;
        $("convert-btn").textContent = "Convert and submit";
      }
      const match = Object.keys(CONVERTIBLE).find((k) => CONVERTIBLE[k](url));
      if (match) applyDetection(match, "link");
      else $("detected").textContent = "Unrecognized site: pick the firm below. Other firms submit a standard .md.";
    });

    $("pdf-file").addEventListener("change", (e) => e.target.files[0] && setPdf(e.target.files[0]));
    const drop = $("pdf-drop");
    for (const ev of ["dragenter", "dragover"]) drop.addEventListener(ev, (e) => { e.preventDefault(); drop.classList.add("dragover"); });
    for (const ev of ["dragleave", "drop"]) drop.addEventListener(ev, () => drop.classList.remove("dragover"));
    drop.addEventListener("drop", (e) => {
      e.preventDefault();
      const file = e.dataTransfer.files[0];
      if (file && isPdf(file)) setPdf(file);
      else $("detected").textContent = "That isn't a PDF. Standard .md files go in the checker below.";
    });

    $("convert-form").addEventListener("submit", (e) => {
      e.preventDefault();
      const url = $("source-url").value.trim();
      const abbrev = select.value;
      const problem = !url && !pdfFile ? "Give the report link or choose the PDF." : !abbrev ? "Pick the audit firm." : "";
      if (problem) {
        $("detected").textContent = problem;
        return;
      }
      window.open(
        issueUrl({
          title: `${pdfFile ? pdfFile.name : shortName(url)} (${vocab ? vocab.firms[abbrev] : abbrev})`,
          firm: vocab ? firmOption(abbrev) : abbrev,
          source_url: pdfFile ? "" : url,
          attachment: pdfFile ? `Replace this line by dragging ${pdfFile.name} here, and wait for its link to appear.` : "",
        }),
        "_blank",
        "noopener",
      );
    });
  }

  // ---------------------------------------------------------------- archive

  async function loadArchive() {
    const status = $("archive-status");
    let index;
    try {
      index = await fetchJSON("reports/index.json");
    } catch (e) {
      status.textContent = "Could not load the archive index.";
      return;
    }
    const reports = index.reports || [];
    if (!reports.length) {
      status.replaceChildren(
        "No reports yet. Until firms approve the converters, ",
        el("a", { href: `${GITHUB}/tree/${BRANCH}/examples` }, "example conversions"),
        " show what an archive entry looks like.",
      );
      return;
    }
    status.textContent = `${reports.length} report(s). Each links to the firm's authoritative original.`;
    const tbody = $("archive-table").querySelector("tbody");
    tbody.replaceChildren(
      ...reports.map((r) => {
        const links = el("td", {}, el("a", { href: `${GITHUB}/blob/${BRANCH}/${r.path}` }, "standard file"));
        const source = r.pdf_url || r.firm_report_url;
        if (source) links.append(" · ", el("a", { href: source, rel: "noopener" }, "firm original"));
        return el("tr", {},
          el("td", {}, r.client || r.project_slug),
          el("td", {}, r.audit_firm),
          el("td", {}, r.report_date),
          el("td", { class: "num" }, (r.findings_summary || {}).total ?? ""),
          links);
      }),
    );
    $("archive-table").hidden = false;
  }

  function setupReference() {
    const items = [
      ["Report template", `${GITHUB}/blob/${BRANCH}/AUDIT_REPORT_TEMPLATE.md`],
      ["Filling instructions", `${GITHUB}/blob/${BRANCH}/FILLING_INSTRUCTIONS.md`],
      ["JSON Schema (parsed report)", "schema/report-schema.json"],
      ["Controlled vocabularies", "schema/vocab.json"],
      ["Validate locally: auditbank CLI", `${GITHUB}/tree/${BRANCH}/tools`],
      ["Repository", GITHUB],
    ];
    $("reference-links").replaceChildren(...items.map(([label, href]) => el("li", {}, el("a", { href }, label))));
  }

  // ------------------------------------------------------------------ wire

  document.addEventListener("DOMContentLoaded", () => {
    $("check-btn").addEventListener("click", runCheck);
    $("clear-btn").addEventListener("click", () => {
      $("report-text").value = "";
      $("result").hidden = true;
    });
    $("file").addEventListener("change", (e) => loadFile(e.target.files[0]));
    const drop = $("drop");
    for (const ev of ["dragenter", "dragover"]) drop.addEventListener(ev, (e) => { e.preventDefault(); drop.classList.add("dragover"); });
    for (const ev of ["dragleave", "drop"]) drop.addEventListener(ev, () => drop.classList.remove("dragover"));
    drop.addEventListener("drop", (e) => {
      e.preventDefault();
      loadFile(e.dataTransfer.files[0]);
    });
    init();
  });
})();
