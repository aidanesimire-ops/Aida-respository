# Engineering Firm Contacts — Methodology & Caveats

Companion to **`engineering_contacts_enriched.csv`** (20 firms, generated 2026-07-02).

## ⚠️ Read this before using the list

**Direct website access was blocked in this session.** The organization's egress
network policy denied outbound HTTPS (`403` on CONNECT) to every firm website —
`cgasolutions.com`, `keithteam.com`, `usanova.com`, `bermelloajamil.com`,
LinkedIn, even Wikipedia. Per the proxy's own policy this was not routed around.

As a result, the firms' Contact / Team / Leadership pages could **not** be
rendered and visually confirmed. What *did* work was web search, so every finding
comes from **search-indexed page content plus third-party aggregators**
(RocketReach, ZoomInfo, LeadIQ, TheOrg) and public municipal documents.

What this means for the two `source` values in the CSV:

- **`published`** = the address (or contact form / general mailbox) appeared
  **verbatim** in a search-surfaced source — usually the firm's own indexed page,
  a municipal planholder list, or a trade publication. It was **not** visually
  confirmed on the live page.
- **`inferred`** = built from an email **pattern** that was confirmed from a real
  published address at that same domain (e.g. `flast@`, `first.last@`,
  `first-name@`). No individual `inferred` address was seen verbatim.

**No addresses were fabricated.** Where a pattern was genuinely ambiguous, no
personal address is asserted (see Nutting, KEITH-Dodie, Globe).

👉 **Recommendation:** treat `medium`/`low` rows as *leads to confirm* — verify by
a quick call to the firm's main line, or run the `inferred` addresses through an
email-verification API before any outreach. The `high`-confidence `published`
rows are the safest starting points.

## Roster corrections found during research

| Roster said | Correction |
|---|---|
| KEITH — Dodie Keith-Lazowick, President/CEO | **Alex Lazowick** is now President/CEO; Dodie is **Chairman** |
| Craven Thompson — "Robert Cole, PE" | **Unverifiable** — no source ties a Robert Cole to CTA. Use **Patrick Gibney** (VP Civil) and **Tom McDonald** (President) |
| GFA International — *(confirm domain)* | Merged into **UES / Universal Engineering Sciences** (Jan 2020); no standalone GFA domain — now **teamues.com** |
| Nutting Engineers — Boca Raton, *(confirm domain)* | Website **nuttingengineers.com**; general email **info@nutting.biz**; HQ is **Boynton Beach**, not Boca |
| Caulfield & Wheeler — cwi-assoc.com | Website is `cwi-assoc.com` (hyphen) but the **email domain is `cwiassoc.com` — NO hyphen** |
| Bermello Ajamil — *(confirm domain)* | `bermelloajamil.com` **confirmed**; firm **acquired by Woolpert (Jan 2024)** — BD may route through Woolpert |
| Globe Engineering — civil-engineer.us | **Confirmed** (a look-alike `globeeng.com` is a *different* firm — avoid) |
| Miller Legg — Fort Lauderdale | HQ **moved to Sunrise** in 2023 |
| Stantec — Fort Lauderdale office | No Stantec FTL office exists; nearest are **Deerfield Beach, Coral Gables, Miami** |

## Strongest verified entry points (best-confidence, published)

- **Miller Legg** — Cara Pasquale, Director of BD — `cpasquale@millerlegg.com`
- **Coastal Protection Eng.** — Thomas Pierro `tpierro@` / Lindino Benedet `lbenedet@coastalprotectioneng.com`
- **Caulfield & Wheeler** — David Lindley — `dave@cwiassoc.com`
- **NOVA** — Audra Sabin (marketing) — `asabin@usanova.com`
- **CGA** — `marketing@` / `info@cgasolutions.com`
- **Simmons & White** — `info@simmonsandwhite.com`

## Confirmed email patterns (from a real published address)

| Firm | Pattern |
|---|---|
| NOVA | `flast@usanova.com` |
| Miller Legg | `flast@millerlegg.com` |
| Chen Moore | `flast@chenmoore.com` |
| Caulfield & Wheeler | `firstname@cwiassoc.com` |
| Simmons & White | `firstname@simmonsandwhite.com` |
| Kimley-Horn | `first.last@kimley-horn.com` |
| CPE | `flast@coastalprotectioneng.com` |

Patterns for WGI, Bermello Ajamil, Geosyntec, Moffatt & Nichol, Stantec, AECOM,
UES/GFA are **aggregator-derived** (well-established but not confirmed from a
first-party published address) — lower confidence.

## Cold-outreach hygiene

Per the brief: identify yourself, use a real reply-to, offer an easy opt-out, and
stick to published business contacts. For the gated national firms (Kimley-Horn,
Stantec, AECOM, Intertek), the office contact form / main line is the compliant
route until you confirm a named local principal.
