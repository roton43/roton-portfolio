const menu = document.querySelector('.menu-button');
if (menu) menu.addEventListener('click', () => {
  const open = menu.getAttribute('aria-expanded') !== 'true';
  menu.setAttribute('aria-expanded', String(open));
  document.getElementById('main-nav').classList.toggle('is-open', open);
});
document.addEventListener('keydown', event => {
  if (event.key === 'Escape' && menu) {
    menu.setAttribute('aria-expanded', 'false');
    document.getElementById('main-nav').classList.remove('is-open');
  }
});
document.getElementById('print-cv')?.addEventListener('click', () => window.print());
document.querySelectorAll('form[data-confirm]').forEach(form => {
  form.addEventListener('submit', event => {
    if (!window.confirm(form.dataset.confirm)) event.preventDefault();
  });
});
const title = document.getElementById('field-title');
const slug = document.getElementById('slug');
let slugEdited = Boolean(slug?.value);
slug?.addEventListener('input', () => { slugEdited = true; });
title?.addEventListener('input', () => {
  if (slug && !slugEdited) slug.value = title.value.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '').slice(0, 160);
});
document.getElementById('preview-button')?.addEventListener('click', async event => {
  const button = event.currentTarget;
  const preview = document.getElementById('markdown-preview');
  button.disabled = true;
  preview.hidden = false;
  preview.textContent = 'Loading preview…';
  try {
    const response = await fetch('/admin/preview', {
      method: 'POST', headers: {'Content-Type': 'application/json', 'X-CSRF-Token': document.querySelector('meta[name="csrf-token"]').content},
      body: JSON.stringify({body: document.getElementById('field-body').value})
    });
    if (!response.ok || response.redirected) throw new Error('Your session may have expired. Reload and sign in again.');
    const result = await response.json();
    // HTML is sanitized on the server before it reaches this editor preview.
    preview.innerHTML = result.html;
  } catch (error) { preview.textContent = error.message || 'Preview unavailable. Your writing is still in the editor.'; }
  finally { button.disabled = false; }
});
