chrome.runtime.onMessage.addListener((message, _sender, sendResponse) => {
  if (!message || message.type !== 'CHASEOS_CAPTURE_PAGE') {
    return false;
  }
  captureActiveTab().then(sendResponse).catch(error => {
    sendResponse({ ok: false, error: String(error && error.message ? error.message : error) });
  });
  return true;
});

async function captureActiveTab() {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  if (!tab || !tab.id) {
    throw new Error('No active tab is available.');
  }
  if (!/^https?:\/\//i.test(tab.url || '')) {
    throw new Error('Capture to Markdown only exports http or https pages.');
  }
  const [result] = await chrome.scripting.executeScript({
    target: { tabId: tab.id },
    files: ['content_script.js']
  });
  const artifact = result && result.result;
  if (!artifact || !artifact.text_content) {
    throw new Error('The page did not expose readable text.');
  }
  const json = JSON.stringify(artifact, null, 2);
  const dataUrl = 'data:application/json;charset=utf-8,' + encodeURIComponent(json);
  const filename = `chaseos-capture-${safeTimestamp()}-${safeSlug(artifact.title || 'page')}.json`;
  const downloadId = await chrome.downloads.download({
    url: dataUrl,
    filename,
    saveAs: true,
    conflictAction: 'uniquify'
  });
  return {
    ok: true,
    download_id: downloadId,
    filename,
    title: artifact.title || '',
    source_url: artifact.source_url || '',
    capture_scope: artifact.capture_scope || '',
    text_length: String(artifact.text_content || '').length
  };
}

function safeTimestamp() {
  return new Date().toISOString().replace(/[^0-9A-Za-z]+/g, '').slice(0, 15);
}

function safeSlug(value) {
  return String(value || 'page').toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '').slice(0, 48) || 'page';
}
