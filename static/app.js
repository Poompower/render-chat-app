// OmniTech AI Frontend Application

let conversationHistory = [];

document.addEventListener("DOMContentLoaded", () => {
  loadHealth();
  loadSampleQueries();
  loadEvaluation();
  loadDataInspector();
});

// Tab Switching
function switchTab(tabName) {
  document.querySelectorAll(".tab-btn").forEach(btn => btn.classList.remove("active"));
  document.querySelectorAll(".tab-pane").forEach(pane => pane.classList.remove("active"));

  if (tabName === "chat") {
    document.getElementById("tab-chat-btn").classList.add("active");
    document.getElementById("pane-chat").classList.add("active");
  } else if (tabName === "eval") {
    document.getElementById("tab-eval-btn").classList.add("active");
    document.getElementById("pane-eval").classList.add("active");
    loadEvaluation();
  } else if (tabName === "data") {
    document.getElementById("tab-data-btn").classList.add("active");
    document.getElementById("pane-data").classList.add("active");
    loadDataInspector();
  }
}

// Check Health & Status
async function loadHealth() {
  try {
    const res = await fetch("/api/health");
    if (res.ok) {
      const data = await res.json();
      document.getElementById("system-status").textContent = 
        `${data.model} • ${data.knowledge_chunks_loaded} Chunks • ${data.products_in_db} Products`;
    }
  } catch (err) {
    document.getElementById("system-status").textContent = "Service Offline";
  }
}

// Load Sample Query Chips
async function loadSampleQueries() {
  const container = document.getElementById("sample-chips");
  try {
    const res = await fetch("/api/sample-queries");
    if (res.ok) {
      const queries = await res.json();
      container.innerHTML = "";
      queries.forEach(item => {
        const btn = document.createElement("button");
        btn.className = "chip-btn";
        btn.textContent = item.query;
        btn.title = `${item.category}: ${item.desc}`;
        btn.onclick = () => {
          document.getElementById("user-input").value = item.query;
          document.getElementById("user-input").focus();
        };
        container.appendChild(btn);
      });
    }
  } catch (err) {
    console.error("Failed to load sample queries:", err);
  }
}

// Chat Handling
async function handleSendMessage(event) {
  event.preventDefault();
  const input = document.getElementById("user-input");
  const sendBtn = document.getElementById("send-button");
  const query = input.value.trim();
  if (!query) return;

  // 1. Render User Message
  appendMessage("user", query);
  input.value = "";
  sendBtn.disabled = true;

  // 2. Render Temporary Thinking Bubble
  const thinkingId = "thinking-" + Date.now();
  appendThinkingMessage(thinkingId);

  try {
    const res = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        message: query,
        temperature: 0.0,
        history: conversationHistory
      })
    });

    const data = await res.json();
    removeThinkingMessage(thinkingId);

    if (res.ok) {
      appendAssistantMessage(data);
      conversationHistory.push({ role: "user", content: query });
      conversationHistory.push({ role: "assistant", content: data.reply });
      if (conversationHistory.length > 8) {
        conversationHistory = conversationHistory.slice(-8);
      }
    } else {
      appendErrorMessage(data.detail || "Error communicating with OmniTech Assistant.");
    }
  } catch (err) {
    removeThinkingMessage(thinkingId);
    appendErrorMessage(`Network Error: ${err.message}`);
  } finally {
    sendBtn.disabled = false;
    input.focus();
  }
}

function appendMessage(role, text) {
  const container = document.getElementById("messages-list");
  const msgEl = document.createElement("div");
  msgEl.className = `message ${role}-msg`;

  const avatar = document.createElement("div");
  avatar.className = "msg-avatar";
  avatar.textContent = role === "user" ? "You" : "AI";

  const bubble = document.createElement("div");
  bubble.className = "msg-bubble";
  bubble.textContent = text;

  msgEl.appendChild(avatar);
  msgEl.appendChild(bubble);
  container.appendChild(msgEl);
  container.scrollTop = container.scrollHeight;
}

function appendThinkingMessage(id) {
  const container = document.getElementById("messages-list");
  const msgEl = document.createElement("div");
  msgEl.className = "message assistant-msg thinking-bubble";
  msgEl.id = id;

  msgEl.innerHTML = `
    <div class="msg-avatar">AI</div>
    <div class="msg-bubble">
      <span class="status-indicator" style="display:inline-block; margin-right:8px;"></span>
      Thinking, retrieving knowledge & running database queries...
    </div>
  `;
  container.appendChild(msgEl);
  container.scrollTop = container.scrollHeight;
}

function removeThinkingMessage(id) {
  const el = document.getElementById(id);
  if (el) el.remove();
}

function appendAssistantMessage(data) {
  const container = document.getElementById("messages-list");
  const msgEl = document.createElement("div");
  msgEl.className = "message assistant-msg";

  let toolsHtml = "";
  if (data.tools_called && data.tools_called.length > 0) {
    const traceItems = data.tools_called.map((tc, idx) => `
      <div class="trace-item">
        <div>
          <span class="trace-badge">Step ${tc.step}: ${tc.tool}</span>
        </div>
        <pre class="trace-code">${escapeHtml(tc.args)}</pre>
        <div style="font-size:0.75rem; color:#94a3b8;">${escapeHtml(tc.summary)}</div>
      </div>
    `).join("");

    toolsHtml = `
      <div class="tool-trace-box">
        <div class="trace-summary-header" onclick="this.nextElementSibling.style.display = this.nextElementSibling.style.display === 'none' ? 'flex' : 'none'">
          <span>⚡ Agent Tools Executed (${data.tools_called.length})</span>
          <span style="font-size:0.75rem;">▼ Toggle Trace</span>
        </div>
        <div class="trace-details-body" style="display:none;">
          ${traceItems}
        </div>
      </div>
    `;
  }

  let sqlHtml = "";
  if (data.sql_queries && data.sql_queries.length > 0) {
    const sqlItems = data.sql_queries.map(q => `<code class="trace-code" style="display:block; margin-top:4px;">${escapeHtml(q)}</code>`).join("");
    sqlHtml = `
      <div style="margin-top:8px;">
        <span style="font-size:0.75rem; color:#67e8f9; font-family:var(--font-mono);">🗄️ Guarded SQL Executed:</span>
        ${sqlItems}
      </div>
    `;
  }

  let citationsHtml = "";
  if (data.citations && data.citations.length > 0) {
    const pills = data.citations.map(c => `<span class="citation-pill">📌 ${escapeHtml(c)}</span>`).join("");
    citationsHtml = `
      <div class="citations-box">
        <span style="font-size:0.75rem; color:#6ee7b7; font-weight:600;">Sources Cited:</span>
        ${pills}
      </div>
    `;
  }

  msgEl.innerHTML = `
    <div class="msg-avatar">AI</div>
    <div class="msg-bubble">
      <div class="msg-header">
        <span class="msg-author">OmniTech Support AI</span>
        <span class="msg-badge">${data.latency_ms}ms • ${data.steps} turn${data.steps > 1 ? 's' : ''}</span>
      </div>
      <div class="msg-text">${formatMarkdown(data.reply)}</div>
      ${citationsHtml}
      ${sqlHtml}
      ${toolsHtml}
    </div>
  `;

  container.appendChild(msgEl);
  container.scrollTop = container.scrollHeight;
}

function appendErrorMessage(errorText) {
  const container = document.getElementById("messages-list");
  const msgEl = document.createElement("div");
  msgEl.className = "message assistant-msg";
  msgEl.innerHTML = `
    <div class="msg-avatar" style="background:#f43f5e;">!</div>
    <div class="msg-bubble" style="border-color:#f43f5e; color:#fecdd3;">
      <strong>Error:</strong> ${escapeHtml(errorText)}
    </div>
  `;
  container.appendChild(msgEl);
  container.scrollTop = container.scrollHeight;
}

// Evaluation Benchmark Loader
async function loadEvaluation() {
  try {
    const res = await fetch("/api/evaluation");
    if (!res.ok) return;
    const data = await res.json();

    // 1. Update Metrics Cards
    const b = data.retrieval_comparison.baseline;
    const i = data.retrieval_comparison.improved;
    const imp = data.retrieval_comparison.improvement;

    document.getElementById("val-hybrid-r1").textContent = `${(i["recall@1"] * 100).toFixed(1)}%`;
    document.getElementById("badge-r1-gain").textContent = `+${imp.recall1_lift_pct}% vs Baseline`;
    document.getElementById("sub-baseline-r1").textContent = `Baseline (BM25 Only): ${(b["recall@1"] * 100).toFixed(1)}%`;

    document.getElementById("val-hybrid-r5").textContent = `${(i["recall@5"] * 100).toFixed(1)}%`;
    document.getElementById("val-hybrid-mrr").textContent = i["mrr"].toFixed(4);
    document.getElementById("badge-mrr-gain").textContent = `+${imp.mrr_lift_pct}% vs Baseline`;
    document.getElementById("sub-baseline-mrr").textContent = `Baseline (BM25 Only): ${b["mrr"].toFixed(4)}`;

    document.getElementById("val-sql-acc").textContent = `${(data.sql_execution_accuracy * 100).toFixed(1)}%`;

    // 2. Populate 30-case Benchmark Table
    const tbody = document.getElementById("benchmark-tbody");
    tbody.innerHTML = "";

    // Load full benchmark data
    const benchRes = await fetch("/benchmark_data.json").catch(() => null);
    
    // First add RAG detailed rows
    if (data.rag_detailed) {
      data.rag_detailed.forEach(item => {
        const tr = document.createElement("tr");
        tr.innerHTML = `
          <td><strong>${item.id}</strong></td>
          <td><span class="cat-badge cat-rag">RAG</span></td>
          <td>${escapeHtml(item.question)}</td>
          <td><code>${item.bm25_top_chunk}</code> (R@1: ${item["bm25_recall@1"]})</td>
          <td><code>${item.hybrid_top_chunk}</code> (R@1: ${item["hybrid_recall@1"]})</td>
          <td><span class="citation-pill" style="font-size:0.7rem;">${escapeHtml(item.top_citation)}</span></td>
        `;
        tbody.appendChild(tr);
      });
    }

    // Add SQL detailed rows
    if (data.sql_detailed) {
      data.sql_detailed.forEach(item => {
        const tr = document.createElement("tr");
        tr.innerHTML = `
          <td><strong>${item.id}</strong></td>
          <td><span class="cat-badge cat-sql">SQL</span></td>
          <td>${escapeHtml(item.question)}</td>
          <td>N/A (Database Query)</td>
          <td><span class="metric-badge positive" style="font-size:0.7rem;">Executed OK</span></td>
          <td><code>${escapeHtml(item.gold_sql)}</code></td>
        `;
        tbody.appendChild(tr);
      });
    }

    // 3. Populate Failure Cases
    const failContainer = document.getElementById("failure-cases-list");
    failContainer.innerHTML = "";
    if (data.failure_analysis) {
      data.failure_analysis.forEach(f => {
        const card = document.createElement("div");
        card.className = "failure-card";
        card.innerHTML = `
          <div class="failure-title">[${f.case_id}] ${escapeHtml(f.type)}</div>
          <div class="failure-obs"><strong>Observation:</strong> ${escapeHtml(f.observation)}</div>
          <div class="failure-fix"><strong>Defense / Fix:</strong> ${escapeHtml(f.how_improved_fixes_it)}</div>
        `;
        failContainer.appendChild(card);
      });
    }

  } catch (err) {
    console.error("Evaluation load error:", err);
  }
}

async function refreshEvaluation() {
  const btn = document.getElementById("btn-run-eval");
  btn.disabled = true;
  btn.textContent = "Running 30 Cases...";
  try {
    const res = await fetch("/api/evaluate", { method: "POST" });
    if (res.ok) {
      await loadEvaluation();
    }
  } finally {
    btn.disabled = false;
    btn.innerHTML = `
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <polyline points="23 4 23 10 17 10"/>
        <path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"/>
      </svg>
      Run Benchmark Now
    `;
  }
}

// Corpus and Database Inspector
async function loadDataInspector() {
  // Populate knowledge documents
  const docsList = document.getElementById("docs-list");
  docsList.innerHTML = `
    <div class="doc-card">
      <div class="doc-name">warranty_and_returns.md</div>
      <div class="doc-meta">30-day money-back guarantee, restocking fee, 1-year hardware warranty, 6-mo battery rule</div>
    </div>
    <div class="doc-card">
      <div class="doc-name">shipping_and_delivery.md</div>
      <div class="doc-meta">Domestic 2-4 days, 1,500 THB free shipping, 14:00 cutoff for same-day express delivery</div>
    </div>
    <div class="doc-card">
      <div class="doc-name">troubleshooting_audio.md</div>
      <div class="doc-meta">AeroPulse ANC-X 40mm drivers, Bluetooth 5.3 multipoint, 8-sec factory reset</div>
    </div>
    <div class="doc-card">
      <div class="doc-name">troubleshooting_smartwatch.md</div>
      <div class="doc-meta">ChronoFit Pro AMOLED, 5ATM water rating restrictions, PPG sensor calibration</div>
    </div>
    <div class="doc-card">
      <div class="doc-name">troubleshooting_hardware.md</div>
      <div class="doc-meta">TitanBook 14 Intel Ultra 7, Fn+Q thermal profiles, MechWave RGB hot-swap switches</div>
    </div>
  `;

  // Schema display
  const schemaCode = document.getElementById("schema-code");
  schemaCode.textContent = `-- SQLite Relational Database (store.db)

CREATE TABLE products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sku TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    category TEXT NOT NULL,
    price REAL NOT NULL,
    stock INTEGER NOT NULL,
    rating REAL NOT NULL,
    warranty_months INTEGER NOT NULL
);

CREATE TABLE orders (
    order_id TEXT PRIMARY KEY,
    customer_name TEXT NOT NULL,
    customer_email TEXT NOT NULL,
    product_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL,
    total_price REAL NOT NULL,
    status TEXT NOT NULL,  -- 'processing', 'shipped', 'delivered', 'cancelled', 'returned'
    order_date TEXT NOT NULL,
    tracking_number TEXT,
    FOREIGN KEY (product_id) REFERENCES products(id)
);

CREATE TABLE returns (
    return_id TEXT PRIMARY KEY,
    order_id TEXT NOT NULL,
    reason TEXT NOT NULL,
    status TEXT NOT NULL,  -- 'pending_inspection', 'approved', 'refunded', 'rejected'
    refund_amount REAL NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (order_id) REFERENCES orders(order_id)
);`;
}

// Helpers
function escapeHtml(str) {
  if (typeof str !== "string") str = JSON.stringify(str);
  return str.replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
}

function formatMarkdown(text) {
  if (!text) return "";
  let html = escapeHtml(text);
  // Bold
  html = html.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
  // Inline code
  html = html.replace(/`([^`]+)`/g, '<code class="trace-code" style="padding:2px 5px;">$1</code>');
  // Line breaks
  html = html.replace(/\n\n/g, '<br><br>').replace(/\n/g, '<br>');
  return html;
}
