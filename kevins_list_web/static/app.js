// -------------------------
// SCANLINES
// -------------------------

function drawScanlines() {
  const canvas = document.getElementById("scanlines");
  const ctx = canvas.getContext("2d");
  canvas.width = window.innerWidth;
  canvas.height = window.innerHeight;

  ctx.clearRect(0, 0, canvas.width, canvas.height);
  ctx.strokeStyle = "#001900";

  for (let y = 0; y < canvas.height; y += 4) {
    ctx.beginPath();
    ctx.moveTo(0, y);
    ctx.lineTo(canvas.width, y);
    ctx.stroke();
  }
}

window.addEventListener("resize", drawScanlines);
drawScanlines();

// -------------------------
// MATRIX RAIN (played once when all tasks are done)
// -------------------------

function matrixRain(durationMs = 5000) {
  const canvas = document.getElementById("matrix");
  const ctx = canvas.getContext("2d");
  canvas.width = window.innerWidth;
  canvas.height = window.innerHeight;
  canvas.classList.remove("hidden");

  const chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789@#$%&*";
  const columns = Math.max(1, Math.floor(canvas.width / 18));
  const drops = Array.from({ length: columns }, () => Math.floor(Math.random() * -20));

  let running = true;

  function frame() {
    if (!running) return;

    ctx.fillStyle = "rgba(0,0,0,0.25)";
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    ctx.fillStyle = "#00FF41";
    ctx.font = "bold 16px Consolas, monospace";

    for (let i = 0; i < columns; i++) {
      const char = chars[Math.floor(Math.random() * chars.length)];
      const x = i * 18;
      const y = drops[i] * 18;
      ctx.fillText(char, x, y);

      drops[i]++;
      if (y > canvas.height && Math.random() > 0.975) {
        drops[i] = Math.floor(Math.random() * -20);
      }
    }

    requestAnimationFrame(frame);
  }

  frame();

  setTimeout(() => {
    running = false;
    canvas.classList.add("hidden");
  }, durationMs);
}

// -------------------------
// BOOT SEQUENCE
// -------------------------

function typeText(el, text, speed = 22) {
  return new Promise((resolve) => {
    let i = 0;
    el.textContent = "";
    const timer = setInterval(() => {
      i++;
      el.textContent = text.slice(0, i);
      if (i >= text.length) {
        clearInterval(timer);
        resolve();
      }
    }, speed);
  });
}

async function bootSequence() {
  const consoleEl = document.getElementById("boot-console");
  const messages =
    "RETRO TERMINAL TODO v1.0\n\n" +
    "Initializing system...\n" +
    "Connecting to cloud....OK\n" +
    "Loading tasks..........OK\n" +
    "CRT display.............ONLINE\n" +
    "\nREADY";

  await typeText(consoleEl, messages);
  await new Promise((r) => setTimeout(r, 500));

  consoleEl.classList.add("hidden");
  document.getElementById("app").classList.remove("hidden");

  await loadTasks();
}

// -------------------------
// API
// -------------------------

const API = "/api/tasks";

async function apiList() {
  const res = await fetch(API);
  return res.json();
}

async function apiAdd(text) {
  const res = await fetch(API, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text }),
  });
  return res.json();
}

async function apiUpdate(id, patch) {
  const res = await fetch(`${API}/${id}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(patch),
  });
  return res.json();
}

async function apiDelete(id) {
  await fetch(`${API}/${id}`, { method: "DELETE" });
}

async function apiReset() {
  await fetch(`${API}/reset`, { method: "POST" });
}

// -------------------------
// STATE + RENDER
// -------------------------

let tasks = [];

async function loadTasks() {
  try {
    tasks = await apiList();
    render();
    setStatus("SYNCED TO CLOUD_");
  } catch (err) {
    setStatus("OFFLINE - RETRYING_");
    setTimeout(loadTasks, 3000);
  }
}

function setStatus(text) {
  document.getElementById("status-line").textContent = text;
}

function updateProgress() {
  const label = document.getElementById("progress-label");
  const total = tasks.length;

  if (total === 0) {
    label.textContent = "NO TASKS LOADED";
    return;
  }

  const done = tasks.filter((t) => t.checked).length;
  const pct = Math.floor((done / total) * 100);
  const barWidth = 30;
  const filled = Math.floor((barWidth * done) / total);
  const bar = "#".repeat(filled) + "-".repeat(barWidth - filled);

  label.textContent = `[${bar}] ${pct}%  (${done}/${total})`;
}

function render() {
  const list = document.getElementById("task-list");
  list.innerHTML = "";

  for (const task of tasks) {
    const li = document.createElement("li");
    li.className = "task-row" + (task.checked ? " done" : "");

    const box = document.createElement("div");
    box.className = "checkbox" + (task.checked ? " checked" : "");
    box.addEventListener("click", () => toggleTask(task));

    const text = document.createElement("div");
    text.className = "task-text";
    text.textContent = "> " + task.text;
    text.addEventListener("dblclick", () => openEditModal(task));

    const del = document.createElement("button");
    del.className = "del-btn";
    del.textContent = "[X]";
    del.addEventListener("click", () => deleteTask(task));

    li.appendChild(box);
    li.appendChild(text);
    li.appendChild(del);
    list.appendChild(li);
  }

  updateProgress();
}

// -------------------------
// ACTIONS
// -------------------------

async function toggleTask(task) {
  task.checked = !task.checked;
  render();

  try {
    await apiUpdate(task.id, { checked: task.checked });
    setStatus("SYNCED TO CLOUD_");
  } catch {
    setStatus("SYNC FAILED_");
  }

  if (tasks.length > 0 && tasks.every((t) => t.checked)) {
    matrixRain(6000);
  }
}

async function deleteTask(task) {
  tasks = tasks.filter((t) => t.id !== task.id);
  render();

  try {
    await apiDelete(task.id);
    setStatus("SYNCED TO CLOUD_");
  } catch {
    setStatus("SYNC FAILED_");
  }
}

async function resetChecks() {
  tasks.forEach((t) => (t.checked = false));
  render();

  try {
    await apiReset();
    setStatus("SYNCED TO CLOUD_");
  } catch {
    setStatus("SYNC FAILED_");
  }
}

// -------------------------
// MODALS
// -------------------------

function openAddModal() {
  const modal = document.getElementById("add-modal");
  const input = document.getElementById("add-input");
  input.value = "";
  modal.classList.remove("hidden");
  input.focus();
}

function closeAddModal() {
  document.getElementById("add-modal").classList.add("hidden");
}

async function confirmAdd() {
  const input = document.getElementById("add-input");
  const text = input.value.trim();
  closeAddModal();

  if (!text) return;

  try {
    const created = await apiAdd(text);
    tasks.push(created);
    render();
    setStatus("SYNCED TO CLOUD_");
  } catch {
    setStatus("SYNC FAILED_");
  }
}

let editingTask = null;

function openEditModal(task) {
  editingTask = task;
  const modal = document.getElementById("edit-modal");
  const input = document.getElementById("edit-input");
  input.value = task.text;
  modal.classList.remove("hidden");
  input.focus();
  input.select();
}

function closeEditModal() {
  document.getElementById("edit-modal").classList.add("hidden");
  editingTask = null;
}

async function confirmEdit() {
  const input = document.getElementById("edit-input");
  const text = input.value.trim();
  const task = editingTask;
  closeEditModal();

  if (!text || !task) return;

  task.text = text;
  render();

  try {
    await apiUpdate(task.id, { text });
    setStatus("SYNCED TO CLOUD_");
  } catch {
    setStatus("SYNC FAILED_");
  }
}

// -------------------------
// WIRE UP EVENTS
// -------------------------

document.getElementById("add-btn").addEventListener("click", openAddModal);
document.getElementById("add-confirm").addEventListener("click", confirmAdd);
document.getElementById("add-cancel").addEventListener("click", closeAddModal);
document.getElementById("add-input").addEventListener("keydown", (e) => {
  if (e.key === "Enter") confirmAdd();
  if (e.key === "Escape") closeAddModal();
});

document.getElementById("reset-btn").addEventListener("click", resetChecks);

document.getElementById("edit-confirm").addEventListener("click", confirmEdit);
document.getElementById("edit-cancel").addEventListener("click", closeEditModal);
document.getElementById("edit-input").addEventListener("keydown", (e) => {
  if (e.key === "Enter") confirmEdit();
  if (e.key === "Escape") closeEditModal();
});

// -------------------------
// PWA SERVICE WORKER
// -------------------------

if ("serviceWorker" in navigator) {
  window.addEventListener("load", () => {
    navigator.serviceWorker.register("/static/sw.js").catch(() => {});
  });
}

// -------------------------
// START
// -------------------------

bootSequence();
