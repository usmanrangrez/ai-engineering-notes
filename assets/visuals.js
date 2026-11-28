(() => {
  const esc = s => String(s).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));

  /* 1. Three-frame 2D Embedding Walkthrough */
  function mountEmbeddingPlot(root) {
    const frames = [
      {
        tab: '1. Raw texts',
        badges: ['string', 'string', 'string'],
        metas: ['stored chunk · page 3 (example)', 'user input · waiting to embed', 'stored chunk · unrelated topic'],
        ret: 'Waiting for embeddings — plain strings cannot be compared by vector similarity yet.',
        foot: '<strong>Frame 1 — Raw texts:</strong> Passage A (“rain gauge”, “rainfall”) and the Question (“device”, “precipitation”) share almost no keywords, so exact word matching misses the link.'
      },
      {
        tab: '2. Embed & plot',
        badges: ['[0.84, 0.72]', '[0.78, 0.84]', '[0.18, 0.24]'],
        metas: ['embedded alone → upper-right', 'embedded alone → upper-right', 'embedded alone → lower-left'],
        ret: 'Illustrative 2D vectors plotted. Real Gemini vectors use 3,072 dimensions working together.',
        foot: '<strong>Frame 2 — Google’s already-trained model embeds each string separately:</strong> Learned patterns place related question–passage pairs close together without processing them together.'
      },
      {
        tab: '3. Match & return',
        badges: ['MATCH', 'query', 'farther'],
        metas: ['highest similarity → returned', 'compared against stored vectors', 'low similarity → skipped'],
        ret: 'Returned original text: “A rain gauge measures rainfall.” (metadata: page 3)',
        foot: '<strong>Frame 3 — Our retrieval code compares vectors:</strong> Similarity scores (dependent on the chosen metric) select Passage A and hand back its original text and page metadata—not raw floats.'
      }
    ];
    let cur = 0;
    function render() {
      const f = frames[cur];
      const pt = (x, y, vis) => `transform="translate(${vis ? x : 56}, ${y})" style="opacity:${vis ? 1 : 0}"`;
      root.innerHTML = `
        <div class="v-bar">
          <div class="v-tabs">${frames.map((fr, i) => `<button type="button" class="v-btn ${i === cur ? 'active' : ''}" data-i="${i}">${esc(fr.tab)}</button>`).join('')}</div>
          <div class="v-tabs">
            <span class="v-meta">Teaching examples · illustrative 2D</span>
            <button type="button" class="v-btn" data-d="-1" ${cur === 0 ? 'disabled' : ''}>Prev</button>
            <button type="button" class="v-btn" data-d="1" ${cur === 2 ? 'disabled' : ''}>Next</button>
          </div>
        </div>
        <div class="v-grid-wide">
          <div class="v-stack">
            <div class="v-card" style="border-color:${cur === 2 ? 'var(--v-ok)' : 'var(--line)'}">
              <div class="v-card-head"><span style="color:var(--v-ok)">● Passage A (example)</span><span class="v-mono" style="color:${cur === 2 ? 'var(--v-ok)' : 'var(--muted)'}">${esc(f.badges[0])}</span></div>
              <div>“A rain gauge measures rainfall.”</div>
              <div class="v-muted v-mono">${esc(f.metas[0])}</div>
            </div>
            <div class="v-card">
              <div class="v-card-head"><span style="color:var(--accent)">◆ Question (example)</span><span class="v-mono v-muted">${esc(f.badges[1])}</span></div>
              <div>“What device measures precipitation?”</div>
              <div class="v-muted v-mono">${esc(f.metas[1])}</div>
            </div>
            <div class="v-card" style="opacity:${cur === 2 ? .55 : 1}">
              <div class="v-card-head"><span style="color:var(--v-alt)">● Passage B (unrelated)</span><span class="v-mono v-muted">${esc(f.badges[2])}</span></div>
              <div>“How do I bake pizza?”</div>
              <div class="v-muted v-mono">${esc(f.metas[2])}</div>
            </div>
          </div>
          <div class="v-card v-stack">
            <svg class="v-svg" viewBox="0 0 380 226" role="img" aria-label="Illustrative 2D embedding plot">
              <g stroke="var(--line)" stroke-width="1" opacity="0.6">
                <line x1="46" y1="62" x2="360" y2="62" stroke-dasharray="3 3"/>
                <line x1="46" y1="106" x2="360" y2="106" stroke-dasharray="3 3"/>
                <line x1="46" y1="150" x2="360" y2="150" stroke-dasharray="3 3"/>
                <line x1="124" y1="18" x2="124" y2="190" stroke-dasharray="3 3"/>
                <line x1="203" y1="18" x2="203" y2="190" stroke-dasharray="3 3"/>
                <line x1="281" y1="18" x2="281" y2="190" stroke-dasharray="3 3"/>
              </g>
              <line x1="46" y1="190" x2="362" y2="190" stroke="var(--muted)" stroke-width="1.2"/>
              <line x1="46" y1="190" x2="46" y2="16" stroke="var(--muted)" stroke-width="1.2"/>
              <text x="203" y="216" fill="var(--muted)" font-size="11" text-anchor="middle">Dimension 1 (illustrative)</text>
              <text x="15" y="104" fill="var(--muted)" font-size="11" text-anchor="middle" transform="rotate(-90 15 104)">Dimension 2 (illustrative)</text>
              ${cur === 0 ? `<rect x="86" y="76" width="234" height="52" rx="4" fill="var(--surface)" stroke="var(--line)" stroke-dasharray="4 3"/><text x="203" y="99" fill="var(--text)" font-size="12" font-weight="600" text-anchor="middle">No vectors yet</text><text x="203" y="116" fill="var(--muted)" font-size="11" text-anchor="middle">Click Next to embed each text</text>` : ''}
              ${cur === 2 ? `<line x1="291" y1="46" x2="103" y2="150" stroke="var(--muted)" stroke-width="1.5" stroke-dasharray="5 4" opacity="0.7"/><rect x="136" y="94" width="106" height="20" rx="3" fill="var(--bg)" stroke="var(--line)"/><text x="189" y="108" fill="var(--muted)" font-size="11" text-anchor="middle">Low similarity</text><line x1="291" y1="46" x2="310" y2="67" stroke="var(--v-ok)" stroke-width="2.5"/><rect x="172" y="54" width="114" height="20" rx="3" fill="var(--bg)" stroke="var(--v-ok)"/><text x="229" y="68" fill="var(--text)" font-size="11" font-weight="600" text-anchor="middle">Closest match</text>` : ''}
              <g class="v-dot" ${pt(291, 46, cur > 0)}>
                <rect x="-6" y="-6" width="12" height="12" transform="rotate(45)" fill="var(--accent)" stroke="var(--bg)" stroke-width="1.5"/>
                <text x="-12" y="-10" fill="var(--text)" font-size="11" font-weight="600" text-anchor="end">Question</text>
                <text x="-12" y="3" fill="var(--muted)" font-size="10" font-family="monospace" text-anchor="end">[0.78, 0.84]</text>
              </g>
              <g class="v-dot" ${pt(310, 67, cur > 0)}>
                <circle cx="0" cy="0" r="6.5" fill="var(--v-ok)" stroke="var(--bg)" stroke-width="1.5"/>
                <text x="0" y="22" fill="var(--text)" font-size="11" font-weight="600" text-anchor="middle">Passage A</text>
                <text x="0" y="35" fill="var(--muted)" font-size="10" font-family="monospace" text-anchor="middle">[0.84, 0.72]</text>
              </g>
              <g class="v-dot" ${pt(103, 150, cur > 0)}>
                <circle cx="0" cy="0" r="6.5" fill="var(--v-alt)" stroke="var(--bg)" stroke-width="1.5"/>
                <text x="12" y="4" fill="var(--text)" font-size="11" font-weight="600">Passage B</text>
                <text x="12" y="17" fill="var(--muted)" font-size="10" font-family="monospace">[0.18, 0.24]</text>
              </g>
            </svg>
            <div class="v-row" style="border-color:${cur === 2 ? 'var(--v-ok)' : 'var(--line)'}"><span>${esc(f.ret)}</span></div>
          </div>
        </div>
        <div class="v-foot">${f.foot}</div>`;
      root.querySelectorAll('[data-i]').forEach(b => b.addEventListener('click', () => { cur = Number(b.dataset.i); render(); }));
      root.querySelectorAll('[data-d]').forEach(b => b.addEventListener('click', () => { cur = Math.max(0, Math.min(2, cur + Number(b.dataset.d))); render(); }));
    }
    render();
  }

  /* 2. Two-Table Retriever (Vector Index + Docstore) */
  function mountTwoTableRetriever(root) {
    const steps = [
      { tab: '1. Score vectors', scores: ['0.99', '0.21', '0.95'], foot: '<strong>Step 1 — Score Table 1 (Vector Index):</strong> Compare the Question vector <code>[0.78, 0.84]</code> against every stored vector mathematically. English text is not read in this step.' },
      { tab: '2. Pick top-k IDs', scores: ['#1 (0.99) ✓', '#3 (0.21)', '#2 (0.95) ✓'], foot: '<strong>Step 2 — Sort and pick top-k IDs:</strong> With <code>k=2</code>, row IDs <code>id=0</code> and <code>id=2</code> win.' },
      { tab: '3. Look up text', scores: ['#1 (0.99) ✓', '#3 (0.21)', '#2 (0.95) ✓'], foot: '<strong>Step 3 — Look up Table 2 (Docstore):</strong> Use winning IDs as keys to hand back the original <code>Document</code> text and page metadata.' }
    ];
    const rows = [
      { id: 0, vec: '[0.84, 0.72]', page: 3, text: '“A rain gauge measures rainfall.”', win: true },
      { id: 1, vec: '[0.18, 0.24]', page: 9, text: '“How do I bake pizza?”', win: false },
      { id: 2, vec: '[0.74, 0.66]', page: 4, text: '“Tipping-bucket gauges record rain depth.”', win: true }
    ];
    let cur = 0;
    function render() {
      const s = steps[cur];
      root.innerHTML = `
        <div class="v-bar">
          <div class="v-tabs">${steps.map((st, i) => `<button type="button" class="v-btn ${i === cur ? 'active' : ''}" data-i="${i}">${esc(st.tab)}</button>`).join('')}</div>
          <div class="v-tabs"><span class="v-meta">Illustrative · k = 2</span><button type="button" class="v-btn" data-d="-1" ${cur === 0 ? 'disabled' : ''}>Prev</button><button type="button" class="v-btn" data-d="1" ${cur === 2 ? 'disabled' : ''}>Next</button></div>
        </div>
        <div class="v-grid">
          <div class="v-stack">
            <div class="v-meta"><strong>Table 1: Vector Index</strong> (numbers only)</div>
            ${rows.map((r, i) => `<div class="v-row" style="border-color:${cur >= 1 && r.win ? 'var(--v-ok)' : (cur === 0 ? 'var(--accent)' : 'var(--line)')};opacity:${cur >= 1 && !r.win ? .45 : 1}"><span class="v-mono"><strong>id=${r.id}</strong> · ${r.vec}</span><span class="v-mono" style="color:${cur >= 1 && r.win ? 'var(--v-ok)' : 'var(--muted)'}">${esc(s.scores[i])}</span></div>`).join('')}
          </div>
          <div class="v-stack">
            <div class="v-meta"><strong>Table 2: Docstore</strong> (original text + metadata)</div>
            ${rows.map(r => `<div class="v-row" style="border-color:${cur === 2 && r.win ? 'var(--v-ok)' : 'var(--line)'};opacity:${cur < 2 ? .55 : (r.win ? 1 : .45)}"><span><strong>id=${r.id}</strong> · ${esc(r.text)}</span><span class="v-mono v-muted">p.${r.page}</span></div>`).join('')}
          </div>
        </div>
        <div class="v-foot">${s.foot}</div>`;
      root.querySelectorAll('[data-i]').forEach(b => b.addEventListener('click', () => { cur = Number(b.dataset.i); render(); }));
      root.querySelectorAll('[data-d]').forEach(b => b.addEventListener('click', () => { cur = Math.max(0, Math.min(2, cur + Number(b.dataset.d))); render(); }));
    }
    render();
  }

  /* 3. Cosine Similarity + Narrow Cone Interactive Widget */
  function mountCosineCone(root) {
    let deg = 41;
    function render() {
      const rad = (deg * Math.PI) / 180;
      const cos = Math.cos(rad);
      const cx = 130, cy = 128, r = 86, base = 10;
      const pRad = ((base + deg) * Math.PI) / 180;
      const px = (cx + r * Math.cos(pRad)).toFixed(1);
      const py = (cy - r * Math.sin(pRad)).toFixed(1);
      const qx = (cx + r * Math.cos(base * Math.PI / 180)).toFixed(1);
      const qy = (cy - r * Math.sin(base * Math.PI / 180)).toFixed(1);
      const pct = (((cos + 1) / 2) * 100).toFixed(1);
      const color = cos >= 0.7 ? 'var(--v-ok)' : (cos >= 0.35 ? 'var(--v-warn)' : 'var(--muted)');
      const label = cos >= 0.7 ? 'Strong match (inside cone, ~0.75 in our lab)' : (cos >= 0.35 ? 'Unrelated English floor (~0.48 pizza in our lab)' : 'Near 90° / opposite (rare for normal English)');
      root.innerHTML = `
        <div class="v-bar">
          <div class="v-tabs">
            <button type="button" class="v-btn ${Math.abs(deg - 41) <= 2 ? 'active' : ''}" data-a="41">Lab match (41° → 0.75)</button>
            <button type="button" class="v-btn ${Math.abs(deg - 61) <= 2 ? 'active' : ''}" data-a="61">Lab pizza (61° → 0.48)</button>
            <button type="button" class="v-btn ${Math.abs(deg - 90) <= 2 ? 'active' : ''}" data-a="90">Perpendicular (90° → 0.00)</button>
          </div>
          <label class="v-slider-wrap">Angle <input type="range" min="0" max="180" value="${deg}"><span class="v-mono">${deg}°</span></label>
        </div>
        <div class="v-grid">
          <div class="v-card">
            <svg class="v-svg" viewBox="0 0 260 156" role="img" aria-label="Angle between two vectors">
              <circle cx="${cx}" cy="${cy}" r="${r}" fill="none" stroke="var(--line)" stroke-dasharray="3 3"/>
              <path d="M ${cx} ${cy} L ${qx} ${qy} A ${r} ${r} 0 0 0 ${(cx + r * Math.cos(80 * Math.PI / 180)).toFixed(1)} ${(cy - r * Math.sin(80 * Math.PI / 180)).toFixed(1)} Z" fill="var(--accent)" opacity="0.1"/>
              <line x1="${cx}" y1="${cy}" x2="${qx}" y2="${qy}" stroke="var(--accent)" stroke-width="2.5"/>
              <line x1="${cx}" y1="${cy}" x2="${px}" y2="${py}" stroke="${color}" stroke-width="2.5"/>
              <circle cx="${cx}" cy="${cy}" r="3" fill="var(--muted)"/>
              <text x="218" y="107" fill="var(--accent)" font-size="11" font-weight="600">Query</text>
              <text x="${Math.max(10, Math.min(205, Number(px)))}" y="${Math.max(14, Number(py) - 6)}" fill="${color}" font-size="11" font-weight="600">Passage</text>
              <text x="195" y="24" fill="var(--muted)" font-size="10">English cone</text>
            </svg>
          </div>
          <div class="v-card v-stack" style="justify-content:space-between">
            <div>
              <div class="v-muted">cos(${deg}°) = cosine similarity</div>
              <div class="v-mono" style="font-size:26px;font-weight:600;color:${color}">${cos >= 0 ? '+' : ''}${cos.toFixed(2)}</div>
              <div style="font-size:12px;color:${color};font-weight:600">${esc(label)}</div>
            </div>
            <div>
              <div class="v-meter"><div class="v-meter-fill" style="width:${pct}%;background:${color}"></div></div>
              <div style="display:flex;justify-content:space-between" class="v-mono v-muted"><span>-1.0</span><span>0.0</span><span>+1.0</span></div>
            </div>
            <div class="v-muted">Normal English texts cluster inside one narrow cone, so unrelated topics still score ~+0.48 instead of negative.</div>
          </div>
        </div>`;
      root.querySelectorAll('[data-a]').forEach(b => b.addEventListener('click', () => { deg = Number(b.dataset.a); render(); }));
      root.querySelector('input[type=range]').addEventListener('input', e => { deg = Number(e.target.value); render(); });
    }
    render();
  }

  /* 4. 6-Step LangGraph + rag_tool Code Flow Debugger */
  function mountCodeFlow(root) {
    const code = [
      '1  @tool def rag_tool(query: str) -> str:',
      '2    results = vector_store.similarity_search_with_score(query, k=3)',
      '3    return "Source: my_paper.pdf, Page 5 ...\\n..."',
      '4  def ask_model(state: MessagesState) -> dict:',
      '5    response = model_with_tools.invoke([System] + state["messages"])',
      '6    return {"messages": [response]}',
      '7  builder.add_edge(START, "ask_model")',
      '8  builder.add_conditional_edges("ask_model", tools_condition)',
      '9  builder.add_edge("tools", "ask_model")',
      '10 result = graph.invoke({"messages": [HumanMessage(prompt)]})',
      '11 print("FINAL ANSWER:", result["messages"][-1].content)'
    ];
    const msgs = [
      { t: 'HumanMessage', c: 'var(--accent)', s: '"What regression methods are used for rainfall measurement?"' },
      { t: 'AIMessage (Call #1)', c: 'var(--v-warn)', s: 'tool_calls=[rag_tool(query="regression methods rainfall measurement")]' },
      { t: 'ToolMessage', c: 'var(--v-alt)', s: '"Source: my_paper.pdf, Page 5 ... Linear Regression, MLR, GRNN, CLR ..."' },
      { t: 'AIMessage (Call #2)', c: 'var(--v-ok)', s: '"The paper highlights Linear Regression, MLR, GRNN, CLR [my_paper.pdf, p 5]..."' }
    ];
    const steps = [
      { who: 'Python → LangGraph', c: 'var(--accent)', lines: [9, 6], n: 1, add: 0, io: '<code>graph.invoke(...)</code> merges your <code>HumanMessage</code> into <code>state["messages"]</code> via <code>add_messages</code>, then follows <code>START → ask_model</code>.' },
      { who: 'Groq Chat Model (#1)', c: 'var(--v-warn)', lines: [3, 4, 5], n: 2, add: 1, io: '<code>ask_model</code> calls Groq. Groq rewrites the search query and returns an <code>AIMessage</code> with <code>tool_calls=[rag_tool]</code>—it does not run the tool itself.' },
      { who: 'LangGraph (tools_condition)', c: 'var(--accent)', lines: [7], n: 2, add: -1, io: '<code>tools_condition</code> sees non-empty <code>tool_calls</code> and routes execution to the <code>"tools"</code> node. State stays at 2 messages.' },
      { who: 'ToolNode → Google + VectorStore', c: 'var(--v-alt)', lines: [0, 1, 2], n: 3, add: 2, io: '<code>ToolNode</code> runs <code>rag_tool</code>. Google embeds the query, the vector store returns top-3 chunks (pages 4 &amp; 5), and <code>ToolNode</code> appends a <code>ToolMessage</code>.' },
      { who: 'Groq Chat Model (#2)', c: 'var(--v-ok)', lines: [8, 3, 4, 5], n: 4, add: 3, io: 'Edge <code>"tools" → "ask_model"</code> loops back. Groq now reads the <code>ToolMessage</code> and writes the final grounded answer with page citations (<code>tool_calls=[]</code>).' },
      { who: 'LangGraph → END → Python', c: 'var(--v-ok)', lines: [7, 10], n: 4, add: -1, io: '<code>tools_condition</code> sees empty <code>tool_calls</code>, routes to <code>END</code>, and Python prints <code>result["messages"][-1].content</code>.' }
    ];
    let cur = 0;
    function render() {
      const s = steps[cur];
      root.innerHTML = `
        <div class="v-bar">
          <div class="v-tabs">${steps.map((_, i) => `<button type="button" class="v-btn ${i === cur ? 'active' : ''}" data-i="${i}">Step ${i + 1}</button>`).join('')}</div>
          <div class="v-tabs">
            <span class="v-badge" style="border-color:${s.c};color:${s.c}">${esc(s.who)}</span>
            <button type="button" class="v-btn" data-d="-1" ${cur === 0 ? 'disabled' : ''}>Prev</button>
            <button type="button" class="v-btn" data-d="1" ${cur === 5 ? 'disabled' : ''}>Next</button>
          </div>
        </div>
        <div class="v-grid">
          <div class="v-code">${code.map((ln, i) => {
            const on = s.lines.includes(i);
            return `<div class="v-cline" style="border-left-color:${on ? s.c : 'transparent'};background:${on ? 'var(--bg)' : 'transparent'};opacity:${on ? 1 : .45};font-weight:${on ? 600 : 400}">${esc(ln)}</div>`;
          }).join('')}</div>
          <div class="v-stack">
            <div class="v-meta"><strong>Live state["messages"]</strong> (len = ${s.n})</div>
            ${msgs.slice(0, s.n).map((m, i) => `<div class="v-card" style="border-color:${i === s.add ? m.c : 'var(--line)'}"><div class="v-card-head"><span class="v-mono" style="color:${m.c}">[${i}] ${esc(m.t)}</span>${i === s.add ? `<span class="v-mono" style="color:${m.c}">+ added</span>` : ''}</div><div class="v-muted">${esc(m.s)}</div></div>`).join('')}
          </div>
        </div>
        <div class="v-foot">${s.io}</div>`;
      root.querySelectorAll('[data-i]').forEach(b => b.addEventListener('click', () => { cur = Number(b.dataset.i); render(); }));
      root.querySelectorAll('[data-d]').forEach(b => b.addEventListener('click', () => { cur = Math.max(0, Math.min(5, cur + Number(b.dataset.d))); render(); }));
    }
    render();
  }

  /* 5. Persistence Checkpoints, Super-Steps & Threads */
  function mountPersistenceCheckpoints(root) {
    const threads = {
      a: {
        id: 'ticket-A',
        snaps: [
          { id: 'CP 0', kind: 'INITIAL', c: 'var(--accent)', st: '{"ticket": "Order ORD-42 is late"}', nxt: "('classify',)", nc: 'var(--v-warn)', why: 'Input merged at <strong>START</strong>. Neither node has run yet—<code>snapshot.next</code> schedules <code>classify</code>.' },
          { id: 'CP 1', kind: 'INTERMEDIATE', c: 'var(--v-warn)', st: '{"ticket": "Order ORD-42 is late", "category": "delivery"}', nxt: "('draft_reply',)", nc: 'var(--v-warn)', why: '<strong>Fault tolerance:</strong> <code>classify</code> finished and saved this checkpoint. If <code>draft_reply</code> crashes, <code>invoke(None, config)</code> resumes here without re-running <code>classify</code>.' },
          { id: 'CP 2', kind: 'FINAL', c: 'var(--v-ok)', st: '{"ticket": "Order ORD-42 is late", "category": "delivery", "reply": "Handling delivery..."}', nxt: '()  (finished)', nc: 'var(--v-ok)', why: 'Graph reached <strong>END</strong>, yet all checkpoints stay saved under <code>ticket-A</code> for follow-up turns or time travel.' }
        ]
      },
      b: {
        id: 'ticket-B',
        snaps: [
          { id: 'CP 0', kind: 'INITIAL', c: 'var(--accent)', st: '{"ticket": "Please cancel ORD-99"}', nxt: "('classify',)", nc: 'var(--v-warn)', why: 'Completely isolated from <code>ticket-A</code>—same graph, separate timeline.' },
          { id: 'CP 1', kind: 'INTERMEDIATE', c: 'var(--v-warn)', st: '{"ticket": "Please cancel ORD-99", "category": "cancellation"}', nxt: "('draft_reply',)", nc: 'var(--v-warn)', why: '<code>ticket-A</code> delivery state never leaks into <code>ticket-B</code>.' },
          { id: 'CP 2', kind: 'FINAL', c: 'var(--v-ok)', st: '{"ticket": "Please cancel ORD-99", "category": "cancellation", "reply": "Handling cancellation..."}', nxt: '()  (finished)', nc: 'var(--v-ok)', why: 'Calling <code>get_state(config)</code> loads whichever <code>thread_id</code> you request.' }
        ]
      }
    };
    let th = 'a', cp = 0;
    function render() {
      const t = threads[th], s = t.snaps[cp];
      const nodes = ['START', 'classify', 'draft_reply', 'END'];
      const done = cp === 0 ? 0 : (cp === 1 ? 1 : 3);
      root.innerHTML = `
        <div class="v-bar">
          <div class="v-tabs">
            <button type="button" class="v-btn ${th === 'a' ? 'active' : ''}" data-t="a">ticket-A</button>
            <button type="button" class="v-btn ${th === 'b' ? 'active' : ''}" data-t="b">ticket-B</button>
          </div>
          <div class="v-tabs">
            ${[0, 1, 2].map(i => `<button type="button" class="v-btn ${cp === i ? 'active' : ''}" data-c="${i}">CP ${i}</button>`).join('')}
            <button type="button" class="v-btn" data-n="1">Next →</button>
          </div>
        </div>
        <div class="v-card" style="margin-bottom:10px;display:flex;flex-wrap:wrap;align-items:center;justify-content:space-between;gap:6px">
          ${nodes.map((n, i) => `<span class="v-badge" style="border-color:${i <= done ? 'var(--v-ok)' : (i === done + 1 ? 'var(--v-warn)' : 'var(--line)')};color:${i <= done ? 'var(--text)' : (i === done + 1 ? 'var(--v-warn)' : 'var(--muted)')}">${esc(n)}</span>`).join('<span class="v-muted">→</span>')}
        </div>
        <div class="v-grid">
          <div class="v-card v-stack">
            <div class="v-card-head"><span>Checkpointer Snapshot (${esc(s.id)})</span><span class="v-badge" style="border-color:${s.c};color:${s.c}">${esc(s.kind)}</span></div>
            <div class="v-mono"><span class="v-muted">thread_id:</span> <strong style="color:var(--accent)">"${esc(t.id)}"</strong></div>
            <div class="v-mono"><span class="v-muted">values:</span> ${esc(s.st)}</div>
            <div class="v-mono"><span class="v-muted">next:</span> <strong style="color:${s.nc}">${esc(s.nxt)}</strong></div>
          </div>
          <div class="v-card v-stack" style="justify-content:space-between">
            <div>${s.why}</div>
            <div class="v-muted"><strong>RAM vs. Disk:</strong> <code>InMemorySaver</code> clears on process exit; <code>SqliteSaver</code> survives restarts.</div>
          </div>
        </div>`;
      root.querySelectorAll('[data-t]').forEach(b => b.addEventListener('click', () => { th = b.dataset.t; render(); }));
      root.querySelectorAll('[data-c]').forEach(b => b.addEventListener('click', () => { cp = Number(b.dataset.c); render(); }));
      root.querySelector('[data-n]').addEventListener('click', () => { cp = (cp + 1) % 3; render(); });
    }
    render();
  }

  /* 6. Time Travel & Forking Diagram */
  function mountTimeTravel(root) {
    root.innerHTML = `
      <div class="v-bar">
        <span class="v-meta"><strong>Time Travel &amp; Forking</strong> · thread_id="ticket-1" (4 original → 7 total checkpoints)</span>
        <span class="v-meta">history is never erased</span>
      </div>
      <div class="v-card">
        <svg class="v-svg" viewBox="0 0 540 162" role="img" aria-label="Forking a LangGraph checkpoint timeline">
          <defs>
            <marker id="tt-orig" markerWidth="6" markerHeight="6" refX="5" refY="3" orient="auto"><polygon points="0 0,6 3,0 6" fill="var(--muted)"/></marker>
            <marker id="tt-fork" markerWidth="6" markerHeight="6" refX="5" refY="3" orient="auto"><polygon points="0 0,6 3,0 6" fill="var(--v-ok)"/></marker>
          </defs>
          <line x1="126" y1="34" x2="178" y2="34" stroke="var(--muted)" stroke-width="1.8" marker-end="url(#tt-orig)"/>
          <line x1="316" y1="34" x2="368" y2="34" stroke="var(--muted)" stroke-width="1.8" marker-end="url(#tt-orig)"/>
          <rect x="8" y="10" width="118" height="48" rx="4" fill="var(--surface)" stroke="var(--accent)" stroke-width="2"/>
          <text x="67" y="27" fill="var(--accent)" font-size="11" font-weight="600" font-family="monospace" text-anchor="middle">CP 0 (past)</text>
          <text x="67" y="41" fill="var(--text)" font-size="10" font-family="monospace" text-anchor="middle">ORD-42 is late</text>
          <text x="67" y="52" fill="var(--muted)" font-size="9.5" font-family="monospace" text-anchor="middle">next=('classify',)</text>
          <rect x="182" y="10" width="134" height="48" rx="4" fill="var(--surface)" stroke="var(--line)" opacity="0.75"/>
          <text x="249" y="27" fill="var(--muted)" font-size="10.5" font-family="monospace" text-anchor="middle">CP 1 (original)</text>
          <text x="249" y="41" fill="var(--muted)" font-size="10" font-family="monospace" text-anchor="middle">category: delivery</text>
          <text x="249" y="52" fill="var(--muted)" font-size="9.5" font-family="monospace" text-anchor="middle">kept in history</text>
          <rect x="372" y="10" width="156" height="48" rx="4" fill="var(--surface)" stroke="var(--line)" opacity="0.75"/>
          <text x="450" y="27" fill="var(--muted)" font-size="10.5" font-family="monospace" text-anchor="middle">CP 2 (original)</text>
          <text x="450" y="41" fill="var(--muted)" font-size="10" font-family="monospace" text-anchor="middle">reply: delivery...</text>
          <text x="450" y="52" fill="var(--muted)" font-size="9.5" font-family="monospace" text-anchor="middle">next=() · preserved</text>
          <path d="M 67 58 L 67 118 L 178 118" fill="none" stroke="var(--v-ok)" stroke-width="2" marker-end="url(#tt-fork)"/>
          <text x="74" y="92" fill="var(--v-ok)" font-size="10" font-family="monospace" font-weight="600">update_state(past_config,</text>
          <text x="74" y="104" fill="var(--v-ok)" font-size="10" font-family="monospace">{"ticket": "Please cancel ORD-99"})</text>
          <rect x="182" y="94" width="144" height="48" rx="4" fill="var(--surface)" stroke="var(--v-ok)" stroke-width="2"/>
          <text x="254" y="111" fill="var(--v-ok)" font-size="11" font-weight="600" font-family="monospace" text-anchor="middle">CP 0-fork (new)</text>
          <text x="254" y="125" fill="var(--text)" font-size="10" font-family="monospace" text-anchor="middle">cancel ORD-99</text>
          <text x="254" y="136" fill="var(--muted)" font-size="9.5" font-family="monospace" text-anchor="middle">next=('classify',)</text>
          <line x1="326" y1="118" x2="368" y2="118" stroke="var(--v-ok)" stroke-width="2" marker-end="url(#tt-fork)"/>
          <text x="347" y="109" fill="var(--v-ok)" font-size="9.5" font-family="monospace" text-anchor="middle">invoke(None)</text>
          <rect x="372" y="94" width="156" height="48" rx="4" fill="var(--surface)" stroke="var(--v-ok)" stroke-width="2"/>
          <text x="450" y="111" fill="var(--v-ok)" font-size="11" font-weight="600" font-family="monospace" text-anchor="middle">Forked Final</text>
          <text x="450" y="125" fill="var(--text)" font-size="10" font-family="monospace" text-anchor="middle">category: cancellation</text>
          <text x="450" y="136" fill="var(--muted)" font-size="9.5" font-family="monospace" text-anchor="middle">reply: cancellation...</text>
        </svg>
      </div>
      <div class="v-foot">Like <code>git branch</code>, <code>update_state</code> branches from a past <code>checkpoint_id</code> without deleting original checkpoints—4 checkpoints grew to 7 in our live lab.</div>`;
  }

  /* 7. Streaming Modes Interactive Replay */
  function mountStreamingModes(root) {
    const modes = {
      invoke: { tab: 'invoke()', title: 'Blocks until END', shape: '1 final dict after full wait', use: 'User stares at a blank screen until every token finishes.', delay: 1100, replace: true, chunks: ['Waiting for entire response...', 'We’re sorry—your order ORD-42 is delayed and should arrive shortly.'] },
      messages: { tab: 'messages', title: 'Token-by-token LLM output', shape: 'for chunk, meta in stream(...):\n  meta["langgraph_node"]', use: 'Best for ChatGPT-style typing. Filter by langgraph_node to hide internal classifier tokens.', delay: 140, replace: false, chunks: ['We', '’re', ' sorry', ' your', ' order', ' ORD', '-42', ' is', ' delayed', '.', ' It', ' should', ' arrive', ' shortly', '.'] },
      updates: { tab: 'updates', title: 'Node delta after each node', shape: '{node_name: partial_dict}', use: 'Best for backend logs and step tracking.', delay: 480, replace: false, chunks: ["{'classify_node': {}}\n", "{'reply_node': {'messages': [AIMessage(...)]}}\n"] },
      values: { tab: 'values', title: 'Full state per super-step', shape: 'full_state_dict', use: 'Best when UI needs the complete state snapshot after each step.', delay: 480, replace: false, chunks: ["step 0: {'messages': [HumanMessage]}\n", "step 1: {'messages': [HumanMessage, AIMessage]}\n"] },
      custom: { tab: 'custom', title: 'Explicit progress (get_stream_writer)', shape: 'writer("-> [status] ...")', use: 'Best for live status badges like "Classifying ticket..." or "Searching PDF...".', delay: 460, replace: false, chunks: ['-> [status] Classifying ticket internally...\n', '-> [status] Internal label decided: DELIVERY\n', '-> [status] Streaming reply to customer...\n'] }
    };
    let cur = 'messages', timers = [];
    function clear() { timers.forEach(clearTimeout); timers = []; }
    function play() {
      clear();
      const m = modes[cur];
      root.innerHTML = `
        <div class="v-bar">
          <div class="v-tabs">${Object.keys(modes).map(k => `<button type="button" class="v-btn ${k === cur ? 'active' : ''}" data-m="${k}">${esc(modes[k].tab)}</button>`).join('')}</div>
          <button type="button" class="v-btn active" data-r="1">▶ Replay</button>
        </div>
        <div class="v-grid-wide">
          <div class="v-card v-stack">
            <div class="v-card-head"><span>${esc(m.title)}</span><span class="v-mono v-muted" data-st>streaming...</span></div>
            <div class="v-code" style="min-height:92px;white-space:pre-wrap" data-out></div>
          </div>
          <div class="v-card v-stack" style="justify-content:space-between">
            <div><div class="v-meta">Yielded shape:</div><div class="v-mono" style="margin-top:4px;white-space:pre-wrap">${esc(m.shape)}</div></div>
            <div class="v-muted">${esc(m.use)}</div>
          </div>
        </div>`;
      root.querySelectorAll('[data-m]').forEach(b => b.addEventListener('click', () => { cur = b.dataset.m; play(); }));
      root.querySelector('[data-r]').addEventListener('click', play);
      const out = root.querySelector('[data-out]'), st = root.querySelector('[data-st]');
      if (m.replace) {
        out.textContent = m.chunks[0];
        st.textContent = 'blocked...';
        timers.push(setTimeout(() => { out.textContent = m.chunks[1]; st.textContent = 'done (1 dump)'; }, m.delay));
      } else {
        m.chunks.forEach((ch, idx) => {
          timers.push(setTimeout(() => {
            out.textContent += ch;
            if (idx === m.chunks.length - 1) st.textContent = `done (${m.chunks.length} events)`;
          }, (idx + 1) * m.delay));
        });
      }
    }
    play();
  }

  /* 8. HITL: Python input() vs LangGraph interrupt() */
  function mountHitlVsInput(root) {
    root.innerHTML = `
      <div class="v-grid">
        <div class="v-card v-stack">
          <div class="v-card-head"><span>Plain Python <code>input()</code></span><span class="v-badge" style="color:var(--v-warn);border-color:var(--v-warn)">Blocks process</span></div>
          <div class="v-row"><span>1. Agent drafts $120 refund</span></div>
          <div class="v-row" style="border-color:var(--v-warn)"><span>2. <strong>FREEZES</strong> waiting on keyboard...</span></div>
          <div class="v-row" style="opacity:.6"><span>3. Server restart / 2 hr wait → state LOST</span></div>
          <div class="v-muted">Cannot hold an HTTP request open while waiting for a human reviewer.</div>
        </div>
        <div class="v-card v-stack">
          <div class="v-card-head"><span>LangGraph <code>interrupt()</code></span><span class="v-badge" style="color:var(--v-ok);border-color:var(--v-ok)">Save &amp; exit</span></div>
          <div class="v-row"><span>1. Agent drafts $120 refund</span></div>
          <div class="v-row" style="border-color:var(--accent)"><span>2. <code>interrupt()</code> saves checkpoint &amp; exits</span></div>
          <div class="v-row" style="border-color:var(--v-ok)"><span>3. Later: <code>Command(resume=...)</code> wakes it up</span></div>
          <div class="v-muted">Server stays free while waiting; checkpointer restores the exact paused run.</div>
        </div>
      </div>`;
  }

  /* 9. HITL 4-Frame Pause & Resume (Approve / Edit / Reject) */
  function mountHitlPauseResume(root) {
    const choices = {
      approve: { cmd: 'Command(resume={"action": "approve"})', out: 'REFUND_ISSUED: $120 refunded for ORD-42.' },
      edit: { cmd: 'Command(resume={"action": "edit", "amount": 50})', out: 'REFUND_ISSUED_EDITED: $50 refunded for ORD-42 (revised from $120).' },
      reject: { cmd: 'Command(resume={"action": "reject"})', out: 'REFUND_REJECTED: human reviewer declined $120 refund for ORD-42.' }
    };
    const tabs = ['1. Tool called', '2. Pause (interrupt)', '3. Human resumes', '4. Tool & reply finish'];
    let f = 0, ch = 'approve';
    function render() {
      const c = choices[ch];
      const badge = f === 0 ? ['RUNNING', 'var(--accent)'] : (f === 1 ? ['PAUSED', 'var(--v-warn)'] : (f === 2 ? ['RESUMING', 'var(--v-ok)'] : ['DONE', 'var(--v-ok)']));
      const payload = f === 0
        ? 'graph.invoke(\n  {"messages": [HumanMessage("Refund $120 for ORD-42")]},\n  config={"configurable": {"thread_id": "ticket-1"}}\n)'
        : f === 1
        ? 'result["messages"] -> 2 msgs (NO ToolMessage yet)\nresult["__interrupt__"] -> [\n  Interrupt(value={"order_id": "ORD-42", "amount": 120})\n]'
        : f === 2
        ? `graph.invoke(\n  ${c.cmd},\n  config={"configurable": {"thread_id": "ticket-1"}}\n)`
        : `ToolMessage:\n  "${c.out}"\n\nask_model (#2) reads ToolMessage → writes final reply (4 msgs total).`;
      const foot = [
        '<strong>Frame 1:</strong> Groq requests <code>issue_refund("ORD-42", 120)</code>. Safe tools like <code>get_order_status</code> skip interrupts completely.',
        '<strong>Frame 2:</strong> Inside <code>issue_refund</code>, <code>interrupt()</code> freezes BEFORE <code>return</code>—so NO <code>ToolMessage</code> exists yet and no money moves.',
        '<strong>Frame 3:</strong> Human chooses Approve, Edit ($50), or Reject. Your app sends <code>Command(resume=...)</code> using the <strong>same <code>thread_id</code></strong>.',
        '<strong>Frame 4:</strong> LangGraph restarts <code>issue_refund</code> from line 1, hands the resume value out of <code>interrupt()</code>, creates <code>ToolMessage</code>, and Groq writes the final answer.'
      ][f];
      root.innerHTML = `
        <div class="v-bar">
          <div class="v-tabs">${tabs.map((t, i) => `<button type="button" class="v-btn ${i === f ? 'active' : ''}" data-f="${i}">${esc(t)}</button>`).join('')}</div>
          <div class="v-tabs"><span class="v-badge" style="color:${badge[1]};border-color:${badge[1]}">${badge[0]}</span><button type="button" class="v-btn" data-d="-1" ${f === 0 ? 'disabled' : ''}>Prev</button><button type="button" class="v-btn" data-d="1" ${f === 3 ? 'disabled' : ''}>Next</button></div>
        </div>
        <div class="v-grid">
          <div class="v-card v-stack">
            <div class="v-meta"><strong>Try human decision (Frames 3–4):</strong></div>
            <div class="v-tabs">
              <button type="button" class="v-btn ${ch === 'approve' ? 'active' : ''}" data-k="approve">Approve ($120)</button>
              <button type="button" class="v-btn ${ch === 'edit' ? 'active' : ''}" data-k="edit">Edit ($50)</button>
              <button type="button" class="v-btn ${ch === 'reject' ? 'active' : ''}" data-k="reject">Reject</button>
            </div>
            <div class="v-muted" style="margin-top:6px"><strong>Critical rule:</strong> On resume, LangGraph re-runs the paused tool/node from its top line—always put side effects <em>after</em> <code>interrupt()</code>.</div>
          </div>
          <div class="v-code" style="white-space:pre-wrap">${esc(payload)}</div>
        </div>
        <div class="v-foot">${foot}</div>`;
      root.querySelectorAll('[data-f]').forEach(b => b.addEventListener('click', () => { f = Number(b.dataset.f); render(); }));
      root.querySelectorAll('[data-d]').forEach(b => b.addEventListener('click', () => { f = Math.max(0, Math.min(3, f + Number(b.dataset.d))); render(); }));
      root.querySelectorAll('[data-k]').forEach(b => b.addEventListener('click', () => { ch = b.dataset.k; if (f < 2) f = 2; render(); }));
    }
    render();
  }

  const registry = {
    'rag-embedding-plot': mountEmbeddingPlot,
    'rag-two-table-retriever': mountTwoTableRetriever,
    'rag-cosine-cone': mountCosineCone,
    'rag-code-flow': mountCodeFlow,
    'persistence-checkpoints': mountPersistenceCheckpoints,
    'persistence-time-travel': mountTimeTravel,
    'streaming-modes': mountStreamingModes,
    'hitl-vs-input': mountHitlVsInput,
    'hitl-pause-resume': mountHitlPauseResume
  };

  document.querySelectorAll('.visual-box[data-visual]').forEach(el => {
    const fn = registry[el.dataset.visual];
    if (fn) fn(el);
  });
})();
