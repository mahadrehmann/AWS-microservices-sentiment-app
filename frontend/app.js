/**
 * app.js — SentimentAI Frontend Logic
 *
 * API routing strategy (Kubernetes-ready):
 * ──────────────────────────────────────
 * All requests go to the *relative* path `/api/analyze`.
 * Nginx (nginx.conf) proxies `/api/` → `http://backend:8000/`.
 *
 * In Docker Compose:  "backend" resolves to the compose service.
 * In Kubernetes:      Replace the Nginx upstream with your K8s Service
 *                     DNS name (e.g. http://sentiment-backend-svc:8000/).
 *                     Zero changes to this file required.
 *
 * If you ever need to point directly at the backend for local debugging
 * without Nginx, set window.API_BASE to the full URL before loading this
 * script, e.g. <script>window.API_BASE = "http://localhost:8000"</script>
 */

const API_BASE = window.API_BASE || "";          // "" = same origin (via Nginx proxy)
const ANALYZE_URL = `${API_BASE}/api/analyze`;  // mapped by nginx.conf → /analyze

// ── DOM References ──────────────────────────────────────────────────────────
const textInput     = document.getElementById("text-input");
const charCount     = document.getElementById("char-count");
const analyzeBtn    = document.getElementById("analyze-btn");
const loadingEl     = document.getElementById("loading");
const errorBox      = document.getElementById("error-box");
const resultCard    = document.getElementById("result-card");
const sentimentBadge= document.getElementById("sentiment-badge");
const confidenceVal = document.getElementById("confidence-value");
const confidenceBar = document.getElementById("confidence-bar");
const analyzedText  = document.getElementById("analyzed-text");

// ── Character Counter ───────────────────────────────────────────────────────
textInput.addEventListener("input", () => {
  const len = textInput.value.length;
  charCount.textContent = `${len} / 2000`;
  charCount.style.color = len > 1800 ? "#f87171" : "";
});

// ── Keyboard shortcut: Ctrl/Cmd + Enter to analyze ─────────────────────────
textInput.addEventListener("keydown", (e) => {
  if ((e.ctrlKey || e.metaKey) && e.key === "Enter") analyzeBtn.click();
});

// ── UI State Helpers ────────────────────────────────────────────────────────
function showLoading() {
  loadingEl.hidden  = false;
  errorBox.hidden   = true;
  resultCard.hidden = true;
  analyzeBtn.disabled = true;
}

function hideLoading() {
  loadingEl.hidden    = false; // keep false briefly; hidden in finally
  analyzeBtn.disabled = false;
  loadingEl.hidden    = true;
}

function showError(message) {
  errorBox.textContent = `⚠ ${message}`;
  errorBox.hidden = false;
  resultCard.hidden = true;
}

function showResult(data) {
  const isPositive = data.label.toUpperCase() === "POSITIVE";
  const pct = Math.round(data.score * 100);
  const cls = isPositive ? "positive" : "negative";

  // Label badge
  sentimentBadge.textContent = isPositive ? "😊 Positive" : "😞 Negative";
  sentimentBadge.className = `sentiment-badge ${cls}`;

  // Confidence value
  confidenceVal.textContent = `${pct}%`;

  // Confidence bar — animate after paint
  confidenceBar.className = `confidence-bar ${cls}`;
  confidenceBar.style.width = "0%";
  requestAnimationFrame(() => {
    requestAnimationFrame(() => {
      confidenceBar.style.width = `${pct}%`;
    });
  });

  // Echo text
  analyzedText.textContent = data.text.length > 300
    ? data.text.slice(0, 300) + "…"
    : data.text;

  resultCard.hidden = false;
}

// ── Main Analyze Handler ────────────────────────────────────────────────────
analyzeBtn.addEventListener("click", async () => {
  const text = textInput.value.trim();

  if (!text) {
    showError("Please enter some text before analyzing.");
    return;
  }

  showLoading();

  try {
    const response = await fetch(ANALYZE_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text }),
    });

    if (!response.ok) {
      let detail = `Server error ${response.status}`;
      try {
        const err = await response.json();
        detail = err.detail || detail;
      } catch (_) { /* ignore JSON parse error */ }
      throw new Error(detail);
    }

    const data = await response.json();
    showResult(data);
  } catch (err) {
    if (err.name === "TypeError") {
      // Network-level failure (CORS, unreachable host, etc.)
      showError("Cannot reach the AI backend. Is the backend service running?");
    } else {
      showError(err.message);
    }
  } finally {
    hideLoading();
  }
});
