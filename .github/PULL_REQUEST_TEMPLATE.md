## Report

- **File:** `reports/<slug>/<slug>--<firm>--<YYYY-MM-DD>.md`
- **Authoritative report (PDF / firm page):**
- **Conversion method:** firm-native / AI-converted (needs firm sign-off)

## Firm sign-off checklist (FILLING_INSTRUCTIONS.md Step 8)

- [ ] All frontmatter fields filled, `"withheld"`, or `null`, and `disclosure_status` consistent with any withheld/redacted content
- [ ] `findings_summary` counts match the finding blocks exactly
- [ ] Every finding has all eight required table fields (Difficulty / likelihood may be null) plus Description, Impact, Recommendation
- [ ] Every Critical/High finding has a Proof / attack path or an explicit `Withheld pending remediation`
- [ ] Every finding has both a unified severity and the firm's own rating verbatim
- [ ] `Resolved` status appears only where `Remediation verified by: firm`
- [ ] Disclaimer and license section present; license stated in frontmatter
- [ ] `conversion_method` accurate; if AI-converted, a firm engineer has reviewed and signed off
- [ ] No confidential client information beyond what the client approved for publication
- [ ] Valid markdown, valid YAML frontmatter (`auditbank validate` passes)
- [ ] Every `CONVERSION-NOTE` resolved (proposed severities, inferred categories/locations, dates, license)

## Coordinator checks

- [ ] Corresponds to an Audit Bank engagement
- [ ] Submitting account belongs to the firm
- [ ] Client publication approval exists
