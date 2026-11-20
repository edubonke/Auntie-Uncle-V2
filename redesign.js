/* Presentation-only enhancements. Booking data and authorization stay in backend.js. */
(() => {
  'use strict';
  const byId = id => document.getElementById(id);
  const heroService = byId('hero-service');
  const heroLocation = byId('hero-location');
  const directoryService = byId('helper-category');
  const directoryLocation = byId('helper-area');
  function search() {
    directoryService.value = heroService.value;
    directoryLocation.value = heroLocation.value.trim();
    directoryService.dispatchEvent(new Event('change', { bubbles: true }));
    directoryLocation.dispatchEvent(new Event('input', { bubbles: true }));
    byId('browse').scrollIntoView({ block: 'start' });
    byId('browse-title').setAttribute('tabindex', '-1');
    byId('browse-title').focus({ preventScroll: true });
  }
  byId('hero-search').addEventListener('submit', event => {
    event.preventDefault();
    search();
  });
  document.querySelectorAll('[data-suburb]').forEach(button => {
    button.addEventListener('click', () => {
      heroLocation.value = button.dataset.suburb;
      search();
    });
  });
  const rate = byId('rate-slider');
  const hours = byId('hours-slider');
  const currency = new Intl.NumberFormat('en-ZA', { style: 'currency', currency: 'ZAR', maximumFractionDigits: 0 });
  function updateEstimate() {
    const weekly = Number(rate.value) * Number(hours.value);
    byId('rate-value').textContent = currency.format(Number(rate.value)) + '/hr';
    byId('hours-value').textContent = hours.value + ' hrs/week';
    byId('weekly-total').textContent = currency.format(weekly);
    byId('monthly-total').textContent = currency.format(weekly * 52 / 12);
    byId('annual-total').textContent = currency.format(weekly * 52);
  }
  rate.addEventListener('input', updateEstimate);
  hours.addEventListener('input', updateEstimate);
  updateEstimate();

  const palette = byId('palette-dialog');
  const choices = [...palette.querySelectorAll('[data-theme]')];
  const allowed = new Set(choices.map(choice => choice.dataset.theme));
  const storageKey = 'auntie-ui-palette-v2';
  function applyTheme(theme, remember = false) {
    if (!allowed.has(theme)) theme = 'protea';
    document.documentElement.dataset.palette = theme;
    choices.forEach(choice => choice.setAttribute('aria-pressed', String(choice.dataset.theme === theme)));
    if (remember) {
      // Only this non-sensitive presentation preference is stored, never booking or profile data.
      try { localStorage.setItem(storageKey, theme); } catch { /* Storage may be disabled. */ }
    }
  }
  let saved = 'protea';
  try { saved = localStorage.getItem(storageKey) || saved; } catch { /* Optional preference. */ }
  applyTheme(saved);
  choices.forEach(choice => choice.addEventListener('click', () => applyTheme(choice.dataset.theme, true)));
  byId('palette-open').addEventListener('click', () => {
    const toggle = byId('menu-toggle');
    if (toggle.getAttribute('aria-expanded') === 'true') toggle.click();
    palette.showModal();
    (palette.querySelector('[aria-pressed="true"]') || byId('palette-close')).focus();
  });
  byId('palette-close').addEventListener('click', () => palette.close());
  palette.addEventListener('click', event => { if (event.target === palette) palette.close(); });
  palette.addEventListener('close', () => {
    const opener = byId('palette-open');
    if (opener.getClientRects().length) opener.focus();
    else byId('menu-toggle').focus();
  });
})();
