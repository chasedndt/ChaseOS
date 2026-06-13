---
title: ChaseOS Waitlist Data Model
created: 2026-05-31
status: DRAFT / WAITLIST SPEC / NO FORM DEPLOYED
type: website-spec
---

# ChaseOS Waitlist Data Model

## V0 recommendation

Use a form tool first if speed matters: Tally, Fillout, Typeform, ConvertKit, or Beehiiv. If building natively, use Supabase with a protected admin view.

## Required public fields

- Email
- Name optional
- Persona: AI builder, founder, developer, creator-builder, researcher, team lead, other
- Current tools: ChatGPT, Claude, Codex, Cursor, Obsidian, Notion, GitHub, agents, other
- Biggest pain ChaseOS could solve
- Use case
- Interest type: Studio beta, Forge creator access, managed agents, setup sprint
- Willingness to pay: no / maybe / £19-mo / £49-mo / team / services
- Consent to contact
- Source / UTM fields where available

## Suggested native table

```sql
waitlist_signups (
  id uuid primary key,
  created_at timestamptz not null default now(),
  email text not null unique,
  name text,
  persona text,
  role text,
  company_or_project text,
  current_tools text,
  biggest_pain text,
  use_case text,
  os_platform text,
  wants_studio_beta boolean default false,
  wants_forge_creator_access boolean default false,
  wants_managed_agents boolean default false,
  willing_to_pay text,
  consent_marketing boolean not null default false,
  consent_research_contact boolean not null default false,
  source text,
  utm_source text,
  utm_medium text,
  utm_campaign text,
  status text default 'new',
  notes text
)
```

## Qualification rule

A qualified signup has real AI-native workflow pain, uses multiple AI/project tools, wants Studio beta / Forge creator access / managed-agent future, gives a clear use case, agrees to be contacted, and optionally expresses willingness to pay or join a setup sprint.

The early-access qualification trigger means 50 qualified signups, 10 high-intent beta applicants, or 3 commercially serious setup/pilot conversations — not random emails.
