const button = document.getElementById('capture');
const status = document.getElementById('status');

button.addEventListener('click', async () => {
  button.disabled = true;
  status.textContent = 'Preparing capture artifact...';
  try {
    const response = await chrome.runtime.sendMessage({ type: 'CHASEOS_CAPTURE_PAGE' });
    if (!response || !response.ok) {
      throw new Error(response && response.error ? response.error : 'Capture failed.');
    }
    status.textContent = `Saved ${response.filename}. Import it in ChaseOS Studio Capture.`;
  } catch (error) {
    status.textContent = String(error && error.message ? error.message : error);
  } finally {
    button.disabled = false;
  }
});
