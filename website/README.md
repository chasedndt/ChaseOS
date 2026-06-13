# ChaseOS Static Launch Site

This folder contains the repo-local static preview for the `https://chaseos.ai`
public launch surface.

Generate the site:

```powershell
python website/build_site.py
```

Run the focused smoke check:

```powershell
python website/smoke_test.py
```

Scope:
- Static pages only; no backend, deploy, DNS, email, payment, or provider calls.
- Waitlist and pack submission forms validate locally and do not store data.
- Forge is a preview JSON catalog; paid packs and untrusted installs are future.
- Admin is a noindex protected stub, not a public console.
