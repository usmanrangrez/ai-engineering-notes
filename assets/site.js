(() => {
  const root = document.documentElement;

  /* 1. Theme switcher */
  const theme = document.querySelector('#theme-toggle');
  function syncTheme() {
    const dark = root.dataset.theme === 'dark';
    theme.textContent = dark ? 'Light' : 'Dark';
    theme.setAttribute('aria-label', `Switch to ${dark ? 'light' : 'dark'} mode`);
  }
  syncTheme();
  theme.addEventListener('click', () => {
    root.dataset.theme = root.dataset.theme === 'dark' ? 'light' : 'dark';
    try { localStorage.setItem('ai-notes-theme', root.dataset.theme); } catch (_) {}
    syncTheme();
  });

  /* 2. Mobile drawer */
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
  document.addEventListener('keydown', e => {
    if (e.key === 'Escape' && sidebar.classList.contains('open')) { closeMenu(); menu.focus(); }
  });
  matchMedia('(min-width: 761px)').addEventListener('change', e => { if (e.matches) closeMenu(); });

  /* 3. Lightweight Python / Bash syntax highlighting (preserves raw copy text) */
  const PY_KW = /\b(def|class|return|if|elif|else|for|in|while|with|as|import|from|try|except|raise|break|continue|pass|True|False|None|and|or|not|is|async|await|yield|lambda)\b/g;
  function highlightPython(codeEl) {
    const raw = codeEl.textContent;
    const esc = s => s.replace(/[&<>]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;' }[c]));
    const tokens = [];
    const hold = html => { tokens.push(html); return `\x00${tokens.length - 1}\x00`; };
    let out = esc(raw);
    out = out.replace(/("""[\s\S]*?"""|'''[\s\S]*?'''|"(?:\\.|[^"\\])*"|'(?:\\.|[^'\\])*')/g, m => hold(`<span class="tok-str">${m}</span>`));
    out = out.replace(/(#[^\n]*)/g, m => hold(`<span class="tok-com">${m}</span>`));
    out = out.replace(/(^|\n)(\s*@[A-Za-z_][\w.]*)/g, (_, pre, dec) => pre + hold(`<span class="tok-dec">${dec}</span>`));
    out = out.replace(PY_KW, m => hold(`<span class="tok-kw">${m}</span>`));
    out = out.replace(/\b(\d+(?:\.\d+)?)\b/g, m => hold(`<span class="tok-num">${m}</span>`));
    out = out.replace(/\x00(\d+)\x00/g, (_, idx) => tokens[Number(idx)]);
    codeEl.dataset.raw = raw;
    codeEl.innerHTML = out;
  }
  document.querySelectorAll('.code-block[data-lang="python"] pre code').forEach(highlightPython);

  /* 4. Copy-to-clipboard buttons */
  document.querySelectorAll('.copy-button').forEach(button => {
    button.addEventListener('click', async () => {
      const codeEl = button.closest('.code-block').querySelector('code');
      const text = codeEl.dataset.raw || codeEl.textContent;
      try {
        await navigator.clipboard.writeText(text);
        button.textContent = 'Copied';
        document.querySelector('#copy-status').textContent = 'Code copied to clipboard.';
        setTimeout(() => { button.textContent = 'Copy'; }, 1600);
      } catch (_) {
        button.textContent = 'Select';
        const range = document.createRange();
        range.selectNodeContents(codeEl);
        const sel = getSelection(); sel.removeAllRanges(); sel.addRange(range);
      }
    });
  });

  /* 5. Personal Study Tracker (localStorage) */
  const STUDY_KEY = 'ai-notes-studied-v1';
  function loadStudied() {
    try { return new Set(JSON.parse(localStorage.getItem(STUDY_KEY) || '[]')); } catch (_) { return new Set(); }
  }
  function saveStudied(set) {
    try { localStorage.setItem(STUDY_KEY, JSON.stringify([...set])); } catch (_) {}
  }
  function syncStudyUI() {
    const studied = loadStudied();
    const readyLinks = [...document.querySelectorAll('.chapter-link .dot-read')];
    const totalReady = Math.max(1, readyLinks.length);
    document.querySelectorAll('.chapter-link[data-slug]').forEach(a => {
      a.classList.toggle('is-studied', studied.has(a.dataset.slug));
    });
    const sbCount = document.querySelector('#sidebar-studied');
    const sbFill = document.querySelector('#sidebar-studied-fill');
    if (sbCount) sbCount.textContent = `${studied.size} / ${totalReady}`;
    if (sbFill) sbFill.style.width = `${Math.min(100, (studied.size / totalReady) * 100)}%`;

    const homeCount = document.querySelector('#home-studied-count');
    if (homeCount) homeCount.textContent = `${studied.size} / ${totalReady}`;

    document.querySelectorAll('.chapter-row[data-slug]').forEach(row => {
      const pill = row.querySelector('.studied-pill');
      if (pill) pill.hidden = !studied.has(row.dataset.slug);
    });
    document.querySelectorAll('.study-toggle[data-study-slug]').forEach(btn => {
      const done = studied.has(btn.dataset.studySlug);
      btn.classList.toggle('studied', done);
      btn.textContent = done ? '✓ Marked studied' : 'Mark as studied';
    });
  }
  document.querySelectorAll('.study-toggle[data-study-slug]').forEach(btn => {
    btn.addEventListener('click', () => {
      const s = loadStudied();
      const slug = btn.dataset.studySlug;
      if (s.has(slug)) s.delete(slug); else s.add(slug);
      saveStudied(s);
      syncStudyUI();
    });
  });
  syncStudyUI();

  /* 6. Reading progress bar & Scroll-spy TOC */
  const progressFill = document.querySelector('#read-progress-fill');
  const tocLinks = [...document.querySelectorAll('.page-toc a[data-toc]')];
  const headings = tocLinks.map(a => document.getElementById(a.dataset.toc)).filter(Boolean);
  if (progressFill || headings.length) {
    function onScroll() {
      if (progressFill) {
        const docH = document.documentElement.scrollHeight - window.innerHeight;
        const pct = docH > 0 ? Math.min(100, Math.max(0, (window.scrollY / docH) * 100)) : 0;
        progressFill.style.width = `${pct}%`;
      }
      if (headings.length) {
        let activeId = headings[0].id;
        for (const h of headings) {
          if (h.getBoundingClientRect().top <= 130) activeId = h.id;
        }
        tocLinks.forEach(a => a.classList.toggle('toc-active', a.dataset.toc === activeId));
      }
    }
    window.addEventListener('scroll', onScroll, { passive: true });
    onScroll();
  }

  /* 7. Homepage search & filter */
  const search = document.querySelector('#chapter-search');
  if (!search) return;
  let selected = 'All';
  const buttons = [...document.querySelectorAll('[data-filter]')];
  const rows = [...document.querySelectorAll('.chapter-row')];
  function filter() {
    const query = search.value.toLowerCase().trim();
    let count = 0;
    rows.forEach(row => {
      const matchMode =
        selected === 'All' ||
        (selected === 'Visual' && row.dataset.visual === 'yes') ||
        row.dataset.status === selected;
      const match = matchMode && row.dataset.search.includes(query);
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
