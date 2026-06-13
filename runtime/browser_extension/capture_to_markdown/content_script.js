function chaseosCapturePageText() {
  const selection = String(window.getSelection ? window.getSelection() : '').trim();
  const visibleText = String(document.body ? document.body.innerText || '' : '').trim();
  const title = String(document.title || '').trim();
  return {
    schema_version: 'chaseos.capture.browser_extension.v1',
    captured_at_utc: new Date().toISOString(),
    capture_scope: selection ? 'selection' : 'visible_page_text',
    title,
    source_url: String(window.location.href || ''),
    selected_text: selection,
    visible_text: visibleText,
    text_content: selection || visibleText,
    includes_cookies: false,
    includes_browser_history: false,
    includes_browser_storage: false,
    source_app: 'chaseos-browser-extension'
  };
}

chaseosCapturePageText();
