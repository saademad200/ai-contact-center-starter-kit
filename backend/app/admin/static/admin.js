/**
 * Alfalah GPT Admin Panel — JS
 * Minimal vanilla JS for forms, flash messages, and live search.
 */

// Auto-dismiss flash alerts after 4s
document.querySelectorAll('.alert').forEach((el) => {
  setTimeout(() => {
    el.style.transition = 'opacity 0.4s';
    el.style.opacity = '0';
    setTimeout(() => el.remove(), 400);
  }, 4000);
});

// Generic collapsible toggle (used by LLMOps)
function toggleSection(id) {
  const el = document.getElementById(id);
  if (el) el.classList.toggle('hidden');
}

// Confirm on all forms with data-confirm attribute
document.querySelectorAll('form[data-confirm]').forEach((form) => {
  form.addEventListener('submit', (e) => {
    if (!confirm(form.dataset.confirm)) e.preventDefault();
  });
});

// File input label feedback
document.querySelectorAll('input[type="file"]').forEach((input) => {
  input.addEventListener('change', () => {
    const label = input.previousElementSibling;
    if (label && input.files.length) {
      label.textContent = `Selected: ${input.files[0].name}`;
    }
  });
});
