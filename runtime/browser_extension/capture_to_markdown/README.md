# ChaseOS Capture to Markdown Browser Extension

This unpacked browser extension exports the current `http` or `https` page as a local ChaseOS capture artifact.

The extension writes a JSON download with schema `chaseos.capture.browser_extension.v1`. ChaseOS Studio imports that file through the `Browser extension capture` source card after the collector is enabled in Settings.

The artifact contains selected text when text is selected, otherwise visible page text. It does not include cookies, browser history, browser storage, passwords, profile data, or session data.
