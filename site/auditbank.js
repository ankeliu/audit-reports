/*
 * Browser/Node port of tools/auditbank/parse.py and validate.py.
 * Regexes come from schema/parse-rules.json; enums and structure from schema/report-schema.json.
 * Problem codes and paths match the Python validator (tests/test_site_parity.py keeps them in sync).
 */
(function (root, factory) {
  if (typeof module === "object" && module.exports) module.exports = factory();
  else root.AuditBank = factory();
})(typeof self !== "undefined" ? self : this, function () {
  "use strict";

  const SEVERITY_ORDER = ["Critical", "High", "Moderate", "Low", "Informational"];
  const FINDING_KEYS = [
    "id", "title", "unified_severity", "firm_severity_rating", "difficulty_likelihood", "status",
    "remediation_verified_by", "category", "location", "resolved_in", "redacted",
    "description", "impact", "proof", "recommendation", "remediation_notes", "conversion_notes",
  ];
  const NULLABLE_FIELDS = new Set(["difficulty_likelihood", "location", "resolved_in"]);
  const NULLABLE_LEADS = new Set(["proof", "remediation_notes"]);
  const WITHHELD_PROOF = "withheld pending remediation";
  const DISCLAIMER_TERMS = [["point-in-time", "snapshot"], ["warranty"], ["authoritative"]];

  function create({ rules, vocab, schema, yaml, Ajv }) {
    const rx = {};
    for (const [key, value] of Object.entries(rules)) {
      if (typeof value !== "string" || key.startsWith("$")) continue;
      const global = key === "comment" || key === "optional_marker";
      rx[key] = new RegExp(value, (key === "conversion_note" ? "" : "m") + (global ? "g" : ""));
    }
    const ajv = new Ajv({ allErrors: true, strict: false });
    const validateSchema = ajv.compile(schema);

    // ------------------------------------------------------------------ parse

    function normalizeScalars(value) {
      if (value instanceof Date) return value.toISOString().slice(0, 10);
      if (Array.isArray(value)) return value.map(normalizeScalars);
      if (value && typeof value === "object") {
        const out = {};
        for (const [k, v] of Object.entries(value)) out[k] = normalizeScalars(v);
        return out;
      }
      return value;
    }

    const isNull = (t) =>
      t == null || ["", "null", "none", "n/a", "—", "-"].includes(String(t).trim().toLowerCase());

    function extractNotes(text) {
      const notes = [];
      const out = text.replace(rx.comment, (_, inner) => {
        const m = rx.conversion_note.exec(inner);
        if (m) notes.push(m[1].split(/\s+/).filter(Boolean).join(" "));
        return "";
      });
      return [out, notes];
    }

    const clean = (t) => t.replace(/\n{3,}/g, "\n\n").trim();

    function split(lines, pattern) {
      const chunks = [[null, []]];
      let inFence = false;
      for (const line of lines) {
        if (rx.fence.test(line)) inFence = !inFence;
        const m = inFence ? null : pattern.exec(line);
        if (m) chunks.push([m, []]);
        else chunks[chunks.length - 1][1].push(line);
      }
      return chunks;
    }

    function sectionKey(heading) {
      const name = heading.replace(rx.optional_marker, "").trim().toLowerCase();
      for (const [prefix, key] of rules.sections) if (name.startsWith(prefix)) return key;
      return null;
    }

    function parseRedacted(text) {
      text = text.trim();
      if (text.toLowerCase() === "false") return { value: false, reason: null };
      const m = rx.redacted_true.exec(text);
      if (m) return { value: true, reason: m[1].trim() };
      if (text.toLowerCase() === "true") return { value: true, reason: null };
      return { value: text, reason: null };
    }

    function parseFinding(match, lines) {
      const [block, notes] = extractNotes(lines.join("\n"));
      const blockLines = block.split("\n");
      while (blockLines.length && (!blockLines[blockLines.length - 1].trim() || rx.hr.test(blockLines[blockLines.length - 1])))
        blockLines.pop();
      const finding = { id: match[1].trim(), title: match[2].trim() };
      const parts = split(blockLines, rx.lead);
      for (const line of parts[0][1]) {
        const row = rx.table_row.exec(line);
        if (!row) continue;
        const key = rules.fields[row[1].trim()];
        if (!key) continue;
        const value = row[2].replace(/\\\|/g, "|").trim();
        if (key === "redacted") finding[key] = parseRedacted(value);
        else if (key === "location") finding[key] = isNull(value) ? null : value.replace(/`/g, "");
        else if (key === "resolved_in") finding[key] = isNull(value) ? null : value.replace(/^`+|`+$/g, "");
        else if (NULLABLE_FIELDS.has(key) && isNull(value)) finding[key] = null;
        else finding[key] = value;
      }
      for (const [lead, body] of parts.slice(1)) {
        const key = rules.leads[lead[1]];
        const text = clean([lead[2], ...body].join("\n"));
        finding[key] = NULLABLE_LEADS.has(key) && isNull(text) ? null : text;
      }
      finding.conversion_notes = notes;
      const out = {};
      for (const k of FINDING_KEYS) if (k in finding) out[k] = finding[k];
      return out;
    }

    function parse(text) {
      text = text.replace(/\r\n/g, "\n").replace(/^﻿/, "");
      const fm = rx.frontmatter.exec(text);
      if (!fm || fm.index !== 0) throw new Error("no YAML frontmatter: the file must start with a '---' fenced block");
      let frontmatter;
      try {
        frontmatter = yaml.load(fm[1]);
      } catch (e) {
        throw new Error(`invalid YAML frontmatter: ${e.message}`);
      }
      if (!frontmatter || typeof frontmatter !== "object" || Array.isArray(frontmatter))
        throw new Error("YAML frontmatter must be a mapping");
      const report = normalizeScalars(frontmatter);
      const bodyLines = text.slice(fm[0].length).split("\n");

      let heading = null;
      const body = [];
      for (const [m, chunk] of split(bodyLines, rx.h1)) {
        if (m && heading === null) heading = m[1].trim();
        else if (m) body.push(m[0]);
        body.push(...chunk);
      }

      let reportNotes = [];
      const sections = {};
      let findings = [];
      for (const [m, lines] of split(body, rx.h2)) {
        const key = m ? sectionKey(m[1]) : null;
        if (key === "findings") {
          const chunks = split(lines, rx.finding_heading);
          reportNotes = reportNotes.concat(extractNotes(chunks[0][1].join("\n"))[1]);
          findings = chunks.slice(1).map(([fm2, chunk]) => parseFinding(fm2, chunk));
          continue;
        }
        const [t, notes] = extractNotes(lines.join("\n"));
        reportNotes = reportNotes.concat(notes);
        if (key && key !== "severity_definitions") sections[key] = clean(t) || null;
      }
      for (const optional of ["methodology", "appendix"]) if (!(optional in sections)) sections[optional] = null;
      report.heading = heading;
      report.conversion_notes = reportNotes;
      report.findings = findings;
      report.sections = sections;
      return report;
    }

    // --------------------------------------------------------------- validate

    const problem = (level, code, path, message) => ({ level, code, path, message });
    const firmAbbrev = (name) => Object.keys(vocab.firms).find((k) => vocab.firms[k] === name) || null;
    const findingsOf = (r) => (Array.isArray(r.findings) ? r.findings.filter((f) => f && typeof f === "object") : []);
    const idNumber = (id) => {
      const m = /-(\d+)$/.exec(id || "");
      return m ? parseInt(m[1], 10) : 0;
    };
    const sevRank = (s) => (SEVERITY_ORDER.includes(s) ? SEVERITY_ORDER.indexOf(s) : SEVERITY_ORDER.length);
    const isInt = (v) => Number.isInteger(v);
    const repr = (v) => (v === undefined || v === null ? "None" : typeof v === "string" ? `'${v}'` : String(v));

    function toPath(instancePath) {
      let out = "$";
      for (const part of instancePath.split("/").slice(1)) {
        const p = part.replace(/~1/g, "/").replace(/~0/g, "~");
        out += /^\d+$/.test(p) ? `[${p}]` : `.${p}`;
      }
      return out;
    }

    function schemaErrors(report) {
      if (validateSchema(report)) return [];
      const errors = validateSchema.errors;
      // ajv reports every failed anyOf branch; jsonschema reports the anyOf once. Keep only the anyOf error.
      const anyOfAt = new Set(errors.filter((e) => e.keyword === "anyOf").map((e) => e.schemaPath));
      const insideFailedAnyOf = (e) => [...anyOfAt].some((sp) => e.schemaPath.startsWith(sp + "/"));
      const out = [];
      for (const e of errors) {
        if (insideFailedAnyOf(e)) continue;
        let message = e.message;
        if (e.instancePath === "/report" && e.keyword === "anyOf")
          message = "at least one of report.pdf_url / report.firm_report_url must be a URL";
        else if (e.keyword === "anyOf") message = `${JSON.stringify(e.data)} is not valid under any of the given schemas`;
        else if (e.keyword === "required") message = `'${e.params.missingProperty}' is a required property`;
        else if (e.keyword === "additionalProperties")
          message = `additional property '${e.params.additionalProperty}' is not allowed`;
        else if (e.keyword === "enum") message = `${JSON.stringify(e.data)} is not one of ${JSON.stringify(e.params.allowedValues)}`;
        out.push(problem("error", "SCHEMA", toPath(e.instancePath), message));
      }
      const seen = new Set();
      return out.filter((p) => {
        const k = p.path + "|" + p.message;
        if (seen.has(k)) return false;
        seen.add(k);
        return true;
      });
    }

    function checkCounts(r) {
      const summary = r.findings_summary || {};
      const findings = findingsOf(r);
      const out = [];
      for (const sev of SEVERITY_ORDER) {
        const key = sev.toLowerCase();
        const actual = findings.filter((f) => f.unified_severity === sev).length;
        if (summary[key] !== actual)
          out.push(problem("error", "COUNTS", `$.findings_summary.${key}`,
            `findings_summary.${key} is ${repr(summary[key])} but there are ${actual} ${sev} findings`));
      }
      const parts = SEVERITY_ORDER.map((s) => summary[s.toLowerCase()]);
      const sum = parts.every(isInt) ? parts.reduce((a, b) => a + b, 0) : null;
      if (sum !== null && summary.total !== sum)
        out.push(problem("error", "COUNTS", "$.findings_summary.total",
          `findings_summary.total is ${repr(summary.total)} but the severity counts sum to ${sum}`));
      if (summary.total !== findings.length)
        out.push(problem("error", "COUNTS", "$.findings_summary.total",
          `findings_summary.total is ${repr(summary.total)} but the report has ${findings.length} findings`));
      return out;
    }

    function checkOrder(r) {
      const f = findingsOf(r);
      const key = (x) => [sevRank(x.unified_severity), idNumber(x.id)];
      for (let i = 1; i < f.length; i++) {
        const [a0, a1] = key(f[i]);
        const [b0, b1] = key(f[i - 1]);
        if (a0 < b0 || (a0 === b0 && a1 < b1))
          return [problem("error", "ORDER", `$.findings[${i}]`,
            `${f[i].id} is out of order: findings must run Critical -> Informational, then by ID within a severity`)];
      }
      return [];
    }

    function checkIds(r) {
      const out = [];
      const seen = new Set();
      const expected = firmAbbrev((r.report || {}).audit_firm);
      findingsOf(r).forEach((f, i) => {
        if (seen.has(f.id)) out.push(problem("error", "IDS_UNIQUE", `$.findings[${i}].id`, `duplicate finding ID ${f.id}`));
        seen.add(f.id);
        const parts = (f.id || "").split("-");
        if (expected && parts.length === 3 && parts[1] !== expected)
          out.push(problem("error", "ID_FIRM_MATCH", `$.findings[${i}].id`,
            `${f.id} uses firm abbreviation ${parts[1]} but report.audit_firm maps to ${expected}`));
      });
      return out;
    }

    function checkRemediation(r) {
      const out = [];
      findingsOf(r).forEach((f, i) => {
        if (f.status === "Resolved" && f.remediation_verified_by !== "firm")
          out.push(problem("error", "RESOLVED_NEEDS_FIRM", `$.findings[${i}].status`,
            `${f.id}: 'Resolved' requires remediation_verified_by 'firm' (use 'Fixed - Not Verified' for unverified client claims)`));
        if (f.remediation_verified_by === "client-reported" && !["Fixed - Not Verified", "Partially Resolved"].includes(f.status))
          out.push(problem("error", "CLIENT_CLAIM", `$.findings[${i}].status`,
            `${f.id}: client-reported remediation must use status 'Fixed - Not Verified' or 'Partially Resolved'`));
      });
      return out;
    }

    function checkPoc(r) {
      const out = [];
      findingsOf(r).forEach((f, i) => {
        if (["Critical", "High"].includes(f.unified_severity) && !f.proof)
          out.push(problem("error", "POC_REQUIRED", `$.findings[${i}].proof`,
            `${f.id}: ${f.unified_severity} findings need a Proof / attack path (or 'Withheld pending remediation')`));
      });
      return out;
    }

    function withheldItems(r) {
      const w = vocab.withheld;
      const items = [];
      const scope = r.scope || {};
      (scope.repositories || []).forEach((repo, i) => {
        for (const key of ["url", "commit_start"])
          if (repo && typeof repo === "object" && repo[key] === w) items.push(`$.scope.repositories[${i}].${key}`);
      });
      if (scope.in_scope_paths === w) items.push("$.scope.in_scope_paths");
      findingsOf(r).forEach((f, i) => {
        if (f.location === w) items.push(`$.findings[${i}].location`);
        if ((f.redacted || {}).value === true) items.push(`$.findings[${i}].redacted`);
        if ((f.proof || "").trim().replace(/\.+$/, "").toLowerCase() === WITHHELD_PROOF) items.push(`$.findings[${i}].proof`);
      });
      return items;
    }

    function checkRedaction(r) {
      const status = (r.publication || {}).disclosure_status;
      const items = withheldItems(r);
      if (items.length && !["redacted", "embargoed"].includes(status))
        return [problem("error", "REDACTION_CONSISTENT", "$.publication.disclosure_status",
          `disclosure_status is ${repr(status)} but content is withheld/redacted at ${items.join(", ")}; use 'redacted' or 'embargoed'`)];
      if (status === "redacted" && !items.length)
        return [problem("error", "REDACTION_CONSISTENT", "$.publication.disclosure_status",
          "disclosure_status is 'redacted' but nothing is withheld or redacted")];
      return [];
    }

    function checkEmbargo(r, today) {
      const pub = r.publication || {};
      if (pub.disclosure_status !== "embargoed") return [];
      if (!pub.embargo_until)
        return [problem("error", "EMBARGO_DATE", "$.publication.embargo_until", "embargoed reports need embargo_until")];
      if (!/^\d{4}-\d{2}-\d{2}$/.test(String(pub.embargo_until))) return [];
      if (String(pub.embargo_until) <= today)
        return [problem("warning", "EMBARGO_DATE", "$.publication.embargo_until",
          `embargo_until ${pub.embargo_until} has passed; set disclosure_status to 'public' (or 'redacted')`)];
      return [];
    }

    function checkCommitFinal(r) {
      const types = (r.audit || {}).type || [];
      const firmVerified = findingsOf(r).some((f) => f.remediation_verified_by === "firm");
      const out = [];
      ((r.scope || {}).repositories || []).forEach((repo, i) => {
        if (repo && typeof repo === "object" && repo.commit_final && !types.includes("fix-review") && !firmVerified)
          out.push(problem("warning", "COMMIT_FINAL_NEEDS_FIX_REVIEW", `$.scope.repositories[${i}].commit_final`,
            "commit_final is set but no fix review is recorded (add 'fix-review' to audit.type, or set commit_final to null)"));
      });
      return out;
    }

    function checkDisclaimer(r) {
      const text = ((r.sections || {}).disclaimer || "").toLowerCase();
      const license = (r.publication || {}).license;
      if (!text.trim())
        return [problem("error", "DISCLAIMER_PRESENT", "$.sections.disclaimer", "Section 7 (Disclaimer and license) is mandatory")];
      const hasTerms = DISCLAIMER_TERMS.every((group) => group.some((t) => text.includes(t)));
      if (!hasTerms && !license)
        return [problem("error", "DISCLAIMER_PRESENT", "$.sections.disclaimer",
          "a substituted firm disclaimer requires publication.license to be stated")];
      return [];
    }

    function checkConversion(r) {
      const out = [];
      let notes = (r.conversion_notes || []).length;
      for (const f of findingsOf(r)) notes += (f.conversion_notes || []).length;
      if (notes)
        out.push(problem("warning", "CONVERSION_NOTES_OPEN", "$",
          `${notes} CONVERSION-NOTE comment(s) remain for the firm reviewer to resolve`));
      if ((r.publication || {}).conversion_method == null)
        out.push(problem("warning", "SIGNOFF_PENDING", "$.publication.conversion_method",
          "conversion_method is unset: set by the merge step once a firm engineer approves the PR"));
      return out;
    }

    function localToday() {
      const d = new Date();
      const pad = (n) => String(n).padStart(2, "0");
      return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
    }

    function validateReport(report, today) {
      today = today || localToday();
      return [
        ...schemaErrors(report),
        ...checkCounts(report),
        ...checkOrder(report),
        ...checkIds(report),
        ...checkRemediation(report),
        ...checkPoc(report),
        ...checkRedaction(report),
        ...checkEmbargo(report, today),
        ...checkCommitFinal(report),
        ...checkDisclaimer(report),
        ...checkConversion(report),
      ];
    }

    function validateText(text, today) {
      let report;
      try {
        report = parse(text);
      } catch (e) {
        return { report: null, problems: [problem("error", "PARSE", "$", e.message)] };
      }
      return { report, problems: validateReport(report, today) };
    }

    return { parse, validateReport, validateText, firmAbbrev };
  }

  return { create, SEVERITY_ORDER };
});
