// ============================================================
// Cell Counter 2.0 — Login Page Script
// ============================================================
// Handles: animated background cells, form validation,
// password toggle, and authentication redirect.
// ============================================================

// ── Floating Cell Background ──────────────────────────────────
(function initFloatingCells() {
  const container = document.getElementById("bgCells");
  const cellColors = ["violet", "teal", "blue"];
  const CELL_COUNT = 25;

  for (let i = 0; i < CELL_COUNT; i++) {
    const cell = document.createElement("div");
    cell.className = `floating-cell ${cellColors[i % cellColors.length]}`;

    const size = Math.random() * 30 + 10; // 10–40px
    cell.style.width = `${size}px`;
    cell.style.height = `${size}px`;
    cell.style.left = `${Math.random() * 100}%`;
    cell.style.animationDuration = `${Math.random() * 15 + 10}s`; // 10–25s
    cell.style.animationDelay = `${Math.random() * 10}s`;

    container.appendChild(cell);
  }
})();

// ── DOM Elements ──────────────────────────────────────────────
const loginForm = document.getElementById("loginForm");
const usernameInput = document.getElementById("username");
const passwordInput = document.getElementById("password");
const togglePassword = document.getElementById("togglePassword");
const loginBtn = document.getElementById("loginBtn");
const loginError = document.getElementById("loginError");
const errorText = document.getElementById("errorText");
const loginSpinner = document.getElementById("loginSpinner");
const rememberMe = document.getElementById("rememberMe");

// ── Accepted Credentials ──────────────────────────────────────
// Simple client-side auth for lab use. 
// In production, replace with server-side authentication.
const VALID_CREDENTIALS = [
  { username: "admin",        password: "blueberry2026" },
  { username: "maria.santos", password: "labtech1" },
  { username: "james.park",   password: "labtech2" },
  { username: "priya",        password: "labtech3" },
  { username: "dr.chen",      password: "pi2026" },
  { username: "lab",          password: "lab" },
];

// ── Password Toggle ───────────────────────────────────────────
togglePassword.addEventListener("click", () => {
  const isPassword = passwordInput.type === "password";
  passwordInput.type = isPassword ? "text" : "password";
  togglePassword.textContent = isPassword ? "🙈" : "👁️";
});

// ── Remember Me (load saved username) ─────────────────────────
(function loadRememberedUser() {
  const saved = localStorage.getItem("cellcounter_username");
  if (saved) {
    usernameInput.value = saved;
    rememberMe.checked = true;
    passwordInput.focus();
  }
})();

// ── Form Submission ───────────────────────────────────────────
loginForm.addEventListener("submit", async (e) => {
  e.preventDefault();

  const username = usernameInput.value.trim().toLowerCase();
  const password = passwordInput.value;

  // Hide previous error
  loginError.classList.remove("visible");

  // Validate
  if (!username || !password) {
    showError("Please enter both username and password.");
    return;
  }

  // Show loading state
  loginBtn.classList.add("loading");
  loginBtn.disabled = true;

  // Simulate a tiny network delay for UX polish
  await new Promise((resolve) => setTimeout(resolve, 800));

  // Check credentials
  const match = VALID_CREDENTIALS.find(
    (c) => c.username === username && c.password === password
  );

  if (match) {
    // Remember username if checked
    if (rememberMe.checked) {
      localStorage.setItem("cellcounter_username", username);
    } else {
      localStorage.removeItem("cellcounter_username");
    }

    // Store session
    sessionStorage.setItem("cellcounter_authenticated", "true");
    sessionStorage.setItem("cellcounter_user", match.username);

    // Success animation
    loginBtn.style.background = "linear-gradient(135deg, #10B981, #34D399)";
    loginBtn.querySelector(".btn-text").textContent = "✓ Welcome!";
    loginBtn.querySelector(".btn-text").style.opacity = "1";
    loginBtn.classList.remove("loading");

    // Redirect after brief success display
    setTimeout(() => {
      window.location.href = "/";
    }, 600);
  } else {
    // Failed
    loginBtn.classList.remove("loading");
    loginBtn.disabled = false;
    showError("Invalid username or password. Please try again.");
    passwordInput.value = "";
    passwordInput.focus();
  }
});

function showError(message) {
  errorText.textContent = message;
  loginError.classList.add("visible");
}

// ── Input Focus Effects ───────────────────────────────────────
[usernameInput, passwordInput].forEach((input) => {
  input.addEventListener("focus", () => {
    loginError.classList.remove("visible");
  });
});

// ── Keyboard shortcut: Enter to submit ────────────────────────
passwordInput.addEventListener("keydown", (e) => {
  if (e.key === "Enter") {
    loginForm.dispatchEvent(new Event("submit"));
  }
});
