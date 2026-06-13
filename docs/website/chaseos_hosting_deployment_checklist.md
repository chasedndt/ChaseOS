---
title: ChaseOS Hosting and Deployment Checklist
created: 2026-05-31
status: DRAFT / HOSTING PLAN / NO DEPLOYMENT PERFORMED
type: website-checklist
primary_domain: https://chaseos.ai
---

# ChaseOS Hosting and Deployment Checklist

## Recommended V1 stack

- DNS: Cloudflare DNS if possible.
- Hosting: Cloudflare Pages for static/mostly-static site; Vercel is acceptable if the site is Next.js.
- Waitlist: form tool first, Supabase only if native form/admin is needed.
- Email: configure aliases only when needed; add SPF/DKIM/DMARC before sending.
- Payments: deferred.
- Managed agents/accounts/licensing: deferred.

## DNS/hosting steps after operator action

1. Confirm registrar ownership and RDAP record.
2. Enable registrar 2FA and auto-renew.
3. Point nameservers to Cloudflare if selected.
4. Add apex `chaseos.ai` and `www` redirect.
5. Enable HTTPS/cert automation.
6. Add security headers.
7. Add `robots.txt`, `sitemap.xml`, favicon, and social preview.
8. Add email records only before sending mail.
9. Keep `/admin` protected and unlinked.
10. Host `/forge/index.json` only after static index generation, upload, digest verification, and approval packet.

No DNS mutation, deployment, upload, or external publication was performed by this documentation pass.


## 2026-05-31 AI domain override

`https://chaseos.ai` is the current primary public launch domain. Prior `chaseos.systems` primary-domain planning is superseded; `chaseos.systems` may remain a future secondary redirect, standards/ecosystem alias, or defensive domain if purchased later.
