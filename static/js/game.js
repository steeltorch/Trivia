// ── State ─────────────────────────────────────────────────────────────────────
let questions = [];
let theme = "";
let category = "";
let timerInterval = null;
let countdownInterval = null;
let startTime = null;
let elapsed = 0;
let submitted = false;

const STORAGE_KEY = "trivia_today";

// ── Date / time helpers ───────────────────────────────────────────────────────

function getESTDateString() {
  // 'sv' locale reliably produces YYYY-MM-DD
  return new Intl.DateTimeFormat("sv", { timeZone: "America/New_York" }).format(new Date());
}

function getNextMidnightEST() {
  // Standard trick: interpret 'now' as EST wall-clock time, find next midnight,
  // then shift back by the same offset to get a real UTC timestamp.
  const now = new Date();
  const estNow = new Date(now.toLocaleString("en-US", { timeZone: "America/New_York" }));
  const diff = now - estNow; // ms offset between UTC and local clock
  const estMidnight = new Date(estNow);
  estMidnight.setHours(24, 0, 0, 0);
  return new Date(estMidnight.getTime() + diff);
}

function formatDate(d) {
  return d.toLocaleDateString("en-US", {
    weekday: "long",
    year: "numeric",
    month: "long",
    day: "numeric",
  });
}

function formatTime(ms) {
  const totalSeconds = Math.floor(ms / 1000);
  const minutes = Math.floor(totalSeconds / 60);
  const seconds = totalSeconds % 60;
  return `${minutes}:${seconds.toString().padStart(2, "0")}`;
}

function formatCountdown(ms) {
  if (ms <= 0) return "0:00:00";
  const s = Math.floor(ms / 1000);
  const h = Math.floor(s / 3600);
  const m = Math.floor((s % 3600) / 60);
  const sec = s % 60;
  return `${h}:${String(m).padStart(2, "0")}:${String(sec).padStart(2, "0")}`;
}

// ── localStorage ──────────────────────────────────────────────────────────────

function getTodayResult() {
  try {
    const data = JSON.parse(localStorage.getItem(STORAGE_KEY));
    if (data && data.date === getESTDateString()) return data;
  } catch (e) {}
  return null;
}

function saveTodayResult(score, total, elapsedMs, results) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify({
    date: getESTDateString(),
    score,
    total,
    elapsed: elapsedMs,
    theme,
    category,
    emoji: results.map(r => r.correct ? "\uD83D\uDFE9" : "\uD83D\uDFE5").join(""),
    dots: results.map(r => r.correct),
  }));
}

// ── Countdown ─────────────────────────────────────────────────────────────────

function startCountdown(...elementIds) {
  function tick() {
    const remaining = getNextMidnightEST() - Date.now();
    const text = formatCountdown(remaining);
    elementIds.forEach(id => {
      const el = document.getElementById(id);
      if (el) el.textContent = text;
    });
    if (remaining <= 0) {
      window.location.reload();
    }
  }
  tick();
  countdownInterval = setInterval(tick, 1000);
}

// ── UI helpers ────────────────────────────────────────────────────────────────

function showScreen(id) {
  document.querySelectorAll(".screen").forEach(s => s.classList.remove("active"));
  document.getElementById(id).classList.add("active");
}

function setCategoryBadge(wrapId, pillId, value) {
  const wrap = document.getElementById(wrapId);
  const pill = document.getElementById(pillId);
  if (value) {
    pill.textContent = value;
    wrap.classList.remove("hidden");
  } else {
    wrap.classList.add("hidden");
  }
}

function renderDots(containerId, dots) {
  const el = document.getElementById(containerId);
  el.innerHTML = "";
  dots.forEach(correct => {
    const dot = document.createElement("div");
    dot.className = `score-dot ${correct ? "correct" : "incorrect"}`;
    el.appendChild(dot);
  });
}

// ── Locked screen ─────────────────────────────────────────────────────────────

function showLockedScreen(result) {
  setCategoryBadge("locked-category-wrap", "locked-category", result.category);
  document.getElementById("locked-theme").textContent = result.theme;
  renderDots("locked-dots", result.dots);
  document.getElementById("locked-score").textContent = `${result.score} / ${result.total}`;
  document.getElementById("locked-points").textContent =
    result.score === 1 ? "1 point earned" : `${result.score} points earned`;
  document.getElementById("locked-time").textContent =
    `Completed in ${formatTime(result.elapsed)}`;
  document.getElementById("locked-share").textContent =
    `Daily Trivia  ${result.emoji}  ${formatTime(result.elapsed)}`;

  showScreen("locked-screen");
  startCountdown("locked-countdown");
}

// ── Game logic ────────────────────────────────────────────────────────────────

function startTimer() {
  startTime = Date.now();
  const timerEl = document.getElementById("timer");
  timerEl.classList.add("running");
  timerInterval = setInterval(() => {
    timerEl.textContent = formatTime(Date.now() - startTime);
  }, 100);
}

function stopTimer() {
  clearInterval(timerInterval);
  elapsed = Date.now() - startTime;
  document.getElementById("timer").classList.remove("running");
  document.getElementById("timer").textContent = formatTime(elapsed);
}

function buildQuestions(qs) {
  const container = document.getElementById("questions-container");
  container.innerHTML = "";
  qs.forEach((q, i) => {
    const card = document.createElement("div");
    card.className = "question-card";
    card.innerHTML = `
      <div class="question-number">Question ${i + 1} of ${qs.length}</div>
      <p class="question-text">${q}</p>
      <input type="text" class="answer-input" id="answer-${i}"
             placeholder="Type your answer..." autocomplete="off" spellcheck="false" />
      <div class="answer-feedback" id="feedback-${i}"></div>
    `;
    container.appendChild(card);
  });

  qs.forEach((_, i) => {
    document.getElementById(`answer-${i}`).addEventListener("keydown", e => {
      if (e.key === "Enter") {
        e.preventDefault();
        if (i < qs.length - 1) {
          document.getElementById(`answer-${i + 1}`).focus();
        } else {
          handleSubmit();
        }
      }
    });
  });
}

async function handleSubmit() {
  if (submitted) return;
  submitted = true;
  stopTimer();
  document.getElementById("submit-btn").disabled = true;

  const answers = questions.map((_, i) =>
    (document.getElementById(`answer-${i}`).value || "").trim()
  );

  const res = await fetch("/api/submit", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ answers, elapsed }),
  });
  const data = await res.json();

  // Per-question feedback
  data.results.forEach((result, i) => {
    const input = document.getElementById(`answer-${i}`);
    const feedback = document.getElementById(`feedback-${i}`);
    input.disabled = true;
    if (result.correct) {
      input.classList.add("correct");
      feedback.className = "answer-feedback correct";
      feedback.textContent = "Correct!";
    } else {
      input.classList.add("incorrect");
      feedback.className = "answer-feedback incorrect";
      feedback.textContent = `Answer: ${result.correct_answer}`;
    }
  });

  // Save to localStorage before showing result
  saveTodayResult(data.score, data.total, elapsed, data.results);

  // Result panel
  renderDots("score-dots", data.results.map(r => r.correct));
  document.getElementById("result-score").textContent = `${data.score} / ${data.total}`;
  document.getElementById("result-points").textContent =
    data.score === 1 ? "1 point earned" : `${data.score} points earned`;
  document.getElementById("result-time").textContent =
    `Completed in ${formatTime(elapsed)}`;
  setCategoryBadge("result-category-wrap", "result-category", category);

  const pct = data.score / data.total;
  document.getElementById("result-message").textContent =
    pct === 1   ? "Perfect score. A true trivia master." :
    pct >= 0.67 ? "Well done! Sharp mind." :
    pct >= 0.34 ? "Not bad — come back tomorrow!" :
                  "Better luck tomorrow!";

  const emoji = data.results.map(r => r.correct ? "\uD83D\uDFE9" : "\uD83D\uDFE5").join("");
  document.getElementById("result-share").textContent =
    `Daily Trivia  ${emoji}  ${formatTime(elapsed)}`;

  const panel = document.getElementById("result-panel");
  panel.classList.add("visible");
  panel.scrollIntoView({ behavior: "smooth" });

  // Start countdown in result panel
  startCountdown("result-countdown");
}

// ── Init ──────────────────────────────────────────────────────────────────────

async function loadDaily() {
  const res = await fetch("/api/daily");
  const data = await res.json();
  questions = data.questions;
  theme = data.theme;
  category = data.category || "";

  document.getElementById("header-date").textContent = formatDate(new Date());
  document.getElementById("start-theme").textContent = theme;
  document.getElementById("game-theme").textContent = theme;
  setCategoryBadge("start-category-wrap", "start-category", category);
  setCategoryBadge("game-category-wrap", "game-category", category);
}

document.addEventListener("DOMContentLoaded", async () => {
  await loadDaily();

  // Check if already played today
  const prior = getTodayResult();
  if (prior) {
    showLockedScreen(prior);
    return;
  }

  // Start button
  document.getElementById("start-btn").addEventListener("click", () => {
    showScreen("game-screen");
    buildQuestions(questions);
    startTimer();
    document.getElementById("answer-0").focus();
  });

  document.getElementById("submit-btn").addEventListener("click", handleSubmit);
});
