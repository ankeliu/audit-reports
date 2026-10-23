// Node harness for tests/test_site_parity.py: reads JSON jobs on stdin, prints parse/validate results.
const fs = require("fs");
const path = require("path");
const root = path.resolve(__dirname, "..");
const read = (p) => JSON.parse(fs.readFileSync(path.join(root, p), "utf8"));
const AuditBank = require(path.join(root, "site/auditbank.js"));
const ab = AuditBank.create({
  rules: read("schema/parse-rules.json"),
  vocab: read("schema/vocab.json"),
  schema: read("schema/report-schema.json"),
  yaml: require(path.join(root, "site/vendor/js-yaml-4.1.0.min.js")),
  Ajv: require(path.join(root, "site/vendor/ajv2020-8.17.1.bundle.min.js")).default,
});
const jobs = JSON.parse(fs.readFileSync(0, "utf8"));
const out = jobs.map((job) => {
  if (job.kind === "parse") {
    try {
      return { report: ab.parse(job.text) };
    } catch (e) {
      return { error: e.message };
    }
  }
  if (job.kind === "validate_report") return { problems: ab.validateReport(job.report, job.today) };
  return { problems: ab.validateText(job.text, job.today).problems };
});
process.stdout.write(JSON.stringify(out));
