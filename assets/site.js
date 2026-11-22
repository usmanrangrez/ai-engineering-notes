(() => {
  const root = document.documentElement;
  const theme = document.querySelector('#theme-toggle');
  function syncTheme() {
    const dark = root.dataset.theme === 'dark';
    theme.textContent = dark ? 'Light mode' : 'Dark mode';
    theme.setAttribute('aria-label', `Switch to ${dark ? 'light' : 'dark'} mode`);
  }
  syncTheme();
  theme.addEventListener('click', () => {
    root.dataset.theme = root.dataset.theme === 'dark' ? 'light' : 'dark';
    try { localStorage.setItem('ai-notes-theme', root.dataset.theme); } catch (_) {}
    syncTheme();
  });
  const menu = document.querySelector('#menu-toggle');
  const sidebar = document.querySelector('#chapter-nav');
  function closeMenu() {
    sidebar.classList.remove('open');
    menu.setAttribute('aria-expanded', 'false');
    document.body.style.overflow = '';
  }
  menu.addEventListener('click', () => {
    const open = menu.getAttribute('aria-expanded') !== 'true';
    sidebar.classList.toggle('open', open);
    menu.setAttribute('aria-expanded', String(open));
    document.body.style.overflow = open ? 'hidden' : '';
  });
  document.addEventListener('keydown', event => {
    if (event.key === 'Escape' && sidebar.classList.contains('open')) {
      closeMenu(); menu.focus();
    }
  });
  matchMedia('(min-width: 761px)').addEventListener('change', event => {
    if (event.matches) closeMenu();
  });
  document.querySelectorAll('.copy-button').forEach(button => {
    button.addEventListener('click', async () => {
      const text = button.closest('.code-block').querySelector('code').textContent;
      try {
        await navigator.clipboard.writeText(text);
        button.textContent = 'Copied';
        document.querySelector('#copy-status').textContent = 'Code copied to clipboard.';
        setTimeout(() => { button.textContent = 'Copy'; }, 1800);
      } catch (_) {
        button.textContent = 'Select code';
        const range = document.createRange();
        range.selectNodeContents(button.closest('.code-block').querySelector('code'));
        const selection = getSelection(); selection.removeAllRanges(); selection.addRange(range);
        document.querySelector('#copy-status').textContent = 'Automatic copy unavailable. Code selected; use your copy shortcut.';
      }
    });
  });
  const search = document.querySelector('#chapter-search');
  if (!search) return;
  let selected = 'All';
  const buttons = [...document.querySelectorAll('[data-filter]')];
  const rows = [...document.querySelectorAll('.chapter-row')];
  function filter() {
    const query = search.value.toLowerCase().trim();
    let count = 0;
    rows.forEach(row => {
      const match = (selected === 'All' || row.dataset.status === selected) && row.dataset.search.includes(query);
      row.hidden = !match;
      if (match) count++;
    });
    document.querySelector('#results-count').textContent = `${count} chapter${count === 1 ? '' : 's'}`;
    document.querySelector('#empty-results').hidden = count > 0;
  }
  search.addEventListener('input', filter);
  buttons.forEach(button => button.addEventListener('click', () => {
    selected = button.dataset.filter;
    buttons.forEach(b => b.setAttribute('aria-pressed', String(b === button)));
    filter();
  }));
})();
