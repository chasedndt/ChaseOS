---
title: ChaseOS Website Admin Panel Spec
created: 2026-05-31
status: DRAFT / ADMIN SPEC / NO BACKEND IMPLEMENTED
type: website-spec
---

# ChaseOS Website Admin Panel Spec

The website admin panel is not ChaseOS Studio. It is the public-site/business admin surface for launch operations.

## Admin may manage

- waitlist signups;
- beta applicants;
- creator submissions;
- pack suggestions;
- support messages;
- invite status;
- manual notes;
- future licenses/entitlements;
- future credit balances.

## Admin must not manage

- users' private local vaults;
- users' local graphs;
- users' local API keys;
- users' private project memory;
- users' local runtime logs.

## V0

Use Supabase dashboard, Airtable/Notion, or a simple protected `/admin` page. V0 actions: view signups, filter by persona/status, mark qualified/invited, export CSV, view creator submissions, and add private notes.

## V1 protected page

A future `/admin` page may include dashboard metrics, signup detail pages, creator submissions, beta invite queue, support inbox, manual email checklist, export, and admin audit log.

Security requirements: authentication, allowlisted admin emails, Row Level Security if Supabase, no raw secrets in browser, no provider API keys, no local-vault data upload, and no hidden production sends without explicit admin action.
