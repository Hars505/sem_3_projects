// ===================================
// STATE MANAGEMENT
// ===================================

const appState = {
  isLoggedIn: false,
  user: null,
  currentTheme: "light",
  currentFeature: null,
};

// ===================================
// DOM ELEMENTS
// ===================================

const elements = {
  // Navbar
  navBtns: document.querySelectorAll(".nav-btn"),
  profileBtn: document.getElementById("profileBtn"),

  // Sidebar
  sidebar: document.getElementById("profileSidebar"),
  sidebarOverlay: document.getElementById("sidebarOverlay"),
  sidebarClose: document.getElementById("sidebarClose"),

  // Login/Profile
  loginContainer: document.getElementById("loginContainer"),
  profileContainer: document.getElementById("profileContainer"),
  loginForm: document.getElementById("loginForm"),
  logoutBtn: document.getElementById("logoutBtn"),
  userName: document.getElementById("userName"),
  userEmail: document.getElementById("userEmail"),
  userInitials: document.getElementById("userInitials"),

  // Theme
  themeBtns: document.querySelectorAll(".theme-btn"),

  // Features
  featureCards: document.querySelectorAll(".feature-card"),
  featureDetail: document.getElementById("featureDetail"),
  backBtn: document.getElementById("backBtn"),
  detailIcon: document.getElementById("detailIcon"),
  detailTitle: document.getElementById("detailTitle"),
  detailOverview: document.getElementById("detailOverview"),

  // Main content
  mainContent: document.getElementById("mainContent"),
};

// ===================================
// UTILITY FUNCTIONS
// ===================================

function getInitials(name) {
  return name
    .split(" ")
    .map((word) => word[0])
    .join("")
    .toUpperCase()
    .slice(0, 2);
}

function saveState() {
  localStorage.setItem("appState", JSON.stringify(appState));
}

function loadState() {
  const saved = localStorage.getItem("appState");
  if (saved) {
    const parsed = JSON.parse(saved);
    appState.isLoggedIn = parsed.isLoggedIn || false;
    appState.user = parsed.user || null;
    appState.currentTheme = parsed.currentTheme || "light";

    // Apply saved theme
    document.body.className = `theme-${appState.currentTheme}`;

    // Update theme buttons
    elements.themeBtns.forEach((btn) => {
      btn.classList.toggle(
        "active",
        btn.dataset.theme === appState.currentTheme,
      );
    });

    // Update profile view if logged in
    if (appState.isLoggedIn && appState.user) {
      updateProfileView();
    }
  }
}

// ===================================
// NAVBAR FUNCTIONALITY
// ===================================

elements.navBtns.forEach((btn) => {
  btn.addEventListener("click", () => {
    // Don't handle profile button here
    if (btn.id === "profileBtn") return;

    // Update active state
    elements.navBtns.forEach((b) => b.classList.remove("active"));
    btn.classList.add("active");

    // Add click animation
    btn.style.transform = "scale(0.95)";
    setTimeout(() => {
      btn.style.transform = "";
    }, 150);
  });
});

// ===================================
// SIDEBAR FUNCTIONALITY
// ===================================

function openSidebar() {
  elements.sidebar.classList.add("active");
  elements.sidebarOverlay.classList.add("active");
  document.body.style.overflow = "hidden";
}

function closeSidebar() {
  elements.sidebar.classList.remove("active");
  elements.sidebarOverlay.classList.remove("active");
  document.body.style.overflow = "";
}

elements.profileBtn.addEventListener("click", openSidebar);
elements.sidebarClose.addEventListener("click", closeSidebar);
elements.sidebarOverlay.addEventListener("click", closeSidebar);

// Close sidebar on ESC key
document.addEventListener("keydown", (e) => {
  if (e.key === "Escape" && elements.sidebar.classList.contains("active")) {
    closeSidebar();
  }
});

// ===================================
// LOGIN/LOGOUT FUNCTIONALITY
// ===================================

// elements.loginForm.addEventListener("submit", (e) => {
//   e.preventDefault();

//   const email = document.getElementById("email").value;
//   const password = document.getElementById("password").value;

//   // Dummy validation - accept any email/password
//   if (email && password) {
//     // Extract name from email (simple approach)
//     const name = email
//       .split("@")[0]
//       .split(".")
//       .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
//       .join(" ");

//     // Update state
//     appState.isLoggedIn = true;
//     appState.user = {
//       name: name || "User",
//       email: email,
//     };

//     saveState();
//     updateProfileView();

//     // Show success animation
//     const btn = elements.loginForm.querySelector(".btn-primary");
//     btn.innerHTML = "<span>Success! ✓</span>";
//     btn.style.background = "linear-gradient(135deg, #00c853, #00e676)";

//     setTimeout(() => {
//       btn.innerHTML = `
//                 <span>Sign In</span>
//                 <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
//                     <line x1="5" y1="12" x2="19" y2="12"></line>
//                     <polyline points="12 5 19 12 12 19"></polyline>
//                 </svg>
//             `;
//       btn.style.background = "";
//     }, 1500);
//   }
// });

// elements.logoutBtn.addEventListener("click", () => {
//   appState.isLoggedIn = false;
//   appState.user = null;
//   saveState();
//   updateProfileView();

//   // Reset form
//   elements.loginForm.reset();
// });

// function updateProfileView() {
//   if (appState.isLoggedIn && appState.user) {
//     // Show profile, hide login
//     elements.loginContainer.classList.add("hidden");
//     elements.profileContainer.classList.remove("hidden");

//     // Update user info
//     elements.userName.textContent = appState.user.name;
//     elements.userEmail.textContent = appState.user.email;
//     elements.userInitials.textContent = getInitials(appState.user.name);
//   } else {
//     // Show login, hide profile
//     elements.loginContainer.classList.remove("hidden");
//     elements.profileContainer.classList.add("hidden");
//   }
// }

// ===================================
// THEME SWITCHING
// ===================================

elements.themeBtns.forEach((btn) => {
  btn.addEventListener("click", () => {
    const theme = btn.dataset.theme;

    // Update state
    appState.currentTheme = theme;
    saveState();

    // Update active button
    elements.themeBtns.forEach((b) => b.classList.remove("active"));
    btn.classList.add("active");

    // Apply theme with animation
    document.body.style.transition = "none";
    document.body.classList.add("transitioning");

    requestAnimationFrame(() => {
      document.body.className = `theme-${theme} transitioning`;

      setTimeout(() => {
        document.body.classList.remove("transitioning");
        document.body.style.transition = "";
      }, 50);
    });

    // Add ripple effect
    createRipple(btn, event);
  });
});

function createRipple(element, event) {
  const ripple = document.createElement("span");
  const rect = element.getBoundingClientRect();
  const size = Math.max(rect.width, rect.height);
  const x = event.clientX - rect.left - size / 2;
  const y = event.clientY - rect.top - size / 2;

  ripple.style.width = ripple.style.height = size + "px";
  ripple.style.left = x + "px";
  ripple.style.top = y + "px";
  ripple.style.position = "absolute";
  ripple.style.borderRadius = "50%";
  ripple.style.background = "rgba(255, 255, 255, 0.5)";
  ripple.style.transform = "scale(0)";
  ripple.style.animation = "ripple 0.6s ease-out";
  ripple.style.pointerEvents = "none";

  element.style.position = "relative";
  element.style.overflow = "hidden";
  element.appendChild(ripple);

  setTimeout(() => ripple.remove(), 600);
}

// Add ripple animation to CSS dynamically
const style = document.createElement("style");
style.textContent = `
    @keyframes ripple {
        to {
            transform: scale(2);
            opacity: 0;
        }
    }
`;
document.head.appendChild(style);

// ===================================
// FEATURE CARDS FUNCTIONALITY
// ===================================

const featureData = {
  speed: {
    title: "Speed",
    icon: `<svg width="60" height="60" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"></polygon>
        </svg>`,
    overview:
      "Monitor and optimize your system performance in real-time. Track metrics, identify bottlenecks, and boost efficiency with advanced analytics and automated optimization recommendations.",
    gradient: "var(--gradient-1)",
  },
  health: {
    title: "Health",
    icon: `<svg width="60" height="60" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"></path>
        </svg>`,
    overview:
      "Comprehensive health monitoring and wellness tracking. Get insights into system vitality, receive proactive alerts, and maintain optimal operational health with intelligent diagnostics.",
    gradient: "var(--gradient-2)",
  },
  dashboard: {
    title: "Dashboard",
    icon: `<svg width="60" height="60" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <rect x="3" y="3" width="7" height="7"></rect>
            <rect x="14" y="3" width="7" height="7"></rect>
            <rect x="14" y="14" width="7" height="7"></rect>
            <rect x="3" y="14" width="7" height="7"></rect>
        </svg>`,
    overview:
      "Powerful analytics dashboard with customizable widgets and real-time data visualization. Create custom reports, track KPIs, and make data-driven decisions with interactive charts and insights.",
    gradient: "var(--gradient-3)",
  },
  password: {
    title: "Password Manager",
    icon: `<svg width="60" height="60" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect>
            <path d="M7 11V7a5 5 0 0 1 10 0v4"></path>
        </svg>`,
    overview:
      "Secure password management with military-grade encryption. Store, generate, and auto-fill passwords across all your devices. Protect your digital identity with advanced security features.",
    gradient: "var(--gradient-4)",
  },
};

elements.featureCards.forEach((card) => {
  card.addEventListener("click", () => {
    const feature = card.dataset.feature;
    openFeatureDetail(feature, card);
  });

  // Add hover effect
  card.addEventListener("mouseenter", function () {
    this.style.transition = "all 0.4s cubic-bezier(0.4, 0, 0.2, 1)";
  });

  card.addEventListener("mouseleave", function () {
    this.style.transition = "all 0.4s cubic-bezier(0.4, 0, 0.2, 1)";
  });
});

function openFeatureDetail(feature, cardElement) {
  const data = featureData[feature];
  if (!data) return;

  appState.currentFeature = feature;

  // Get card position for animation origin
  const rect = cardElement.getBoundingClientRect();
  const centerX = rect.left + rect.width / 2;
  const centerY = rect.top + rect.height / 2;

  // Update detail content
  elements.detailIcon.innerHTML = data.icon;
  elements.detailIcon.style.background = data.gradient;
  elements.detailTitle.textContent = data.title;
  elements.detailOverview.textContent = data.overview;

  // Show detail view with animation
  elements.featureDetail.classList.remove("hidden", "collapsing");
  elements.featureDetail.classList.add("active", "expanding");

  // Set transform origin for scale animation
  elements.featureDetail.style.transformOrigin = `${centerX}px ${centerY}px`;

  // Hide main content
  setTimeout(() => {
    elements.mainContent.style.opacity = "0";
    elements.mainContent.style.transform = "scale(0.95)";
  }, 100);

  // Prevent body scroll
  document.body.style.overflow = "hidden";

  // Remove expanding class after animation
  setTimeout(() => {
    elements.featureDetail.classList.remove("expanding");
  }, 600);
}

function closeFeatureDetail() {
  elements.featureDetail.classList.remove("expanding");
  elements.featureDetail.classList.add("collapsing");

  // Show main content
  elements.mainContent.style.opacity = "1";
  elements.mainContent.style.transform = "scale(1)";

  // After animation
  setTimeout(() => {
    elements.featureDetail.classList.remove("active", "collapsing");
    elements.featureDetail.classList.add("hidden");
    document.body.style.overflow = "";
    appState.currentFeature = null;
  }, 600);
}

elements.backBtn.addEventListener("click", closeFeatureDetail);

// Close feature detail on ESC key
document.addEventListener("keydown", (e) => {
  if (
    e.key === "Escape" &&
    elements.featureDetail.classList.contains("active")
  ) {
    closeFeatureDetail();
  }
});

// ===================================
// SMOOTH SCROLL FOR MAIN CONTENT
// ===================================

elements.mainContent.style.transition =
  "opacity 0.3s ease, transform 0.3s ease";

// ===================================
// INTERSECTION OBSERVER FOR ANIMATIONS
// ===================================

const observerOptions = {
  threshold: 0.1,
  rootMargin: "0px 0px -50px 0px",
};

const observer = new IntersectionObserver((entries) => {
  entries.forEach((entry) => {
    if (entry.isIntersecting) {
      entry.target.style.opacity = "1";
      entry.target.style.transform = "translateY(0)";
    }
  });
}, observerOptions);

// Observe all feature cards
elements.featureCards.forEach((card) => {
  card.style.opacity = "0";
  card.style.transform = "translateY(20px)";
  observer.observe(card);
});

// ===================================
// PARALLAX EFFECT FOR HERO
// ===================================

window.addEventListener("scroll", () => {
  const scrolled = window.pageYOffset;
  const hero = document.querySelector(".hero-background");

  if (hero) {
    hero.style.transform = `translateY(${scrolled * 0.5}px)`;
  }
});

// ===================================
// CURSOR TRAIL EFFECT (OPTIONAL ENHANCEMENT)
// ===================================

let cursorTrail = [];
const maxTrailLength = 20;

document.addEventListener("mousemove", (e) => {
  // Only show in neon theme
  if (appState.currentTheme !== "neon") return;

  const trail = document.createElement("div");
  trail.className = "cursor-trail";
  trail.style.cssText = `
        position: fixed;
        width: 8px;
        height: 8px;
        background: var(--accent-primary);
        border-radius: 50%;
        pointer-events: none;
        z-index: 9999;
        left: ${e.clientX - 4}px;
        top: ${e.clientY - 4}px;
        opacity: 0.6;
        animation: cursorFade 0.5s ease-out forwards;
    `;

  document.body.appendChild(trail);
  cursorTrail.push(trail);

  if (cursorTrail.length > maxTrailLength) {
    const oldest = cursorTrail.shift();
    oldest.remove();
  }
});

// Add cursor fade animation
const cursorStyle = document.createElement("style");
cursorStyle.textContent = `
    @keyframes cursorFade {
        to {
            opacity: 0;
            transform: scale(0);
        }
    }
`;
document.head.appendChild(cursorStyle);

// ===================================
// CARD TILT EFFECT (3D)
// ===================================

// elements.featureCards.forEach(card => {
//     card.addEventListener('mousemove', handleCardTilt);
//     card.addEventListener('mouseleave', resetCardTilt);
// });

// function handleCardTilt(e) {
//     const card = e.currentTarget;
//     const rect = card.getBoundingClientRect();
//     const x = e.clientX - rect.left;
//     const y = e.clientY - rect.top;

//     const centerX = rect.width / 2;
//     const centerY = rect.height / 2;

//     const rotateX = (y - centerY) / 20;
//     const rotateY = (centerX - x) / 20;

//     card.style.transform = `
//         translateY(-8px)
//         perspective(1000px)
//         rotateX(${rotateX}deg)
//         rotateY(${rotateY}deg)
//         scale3d(1.02, 1.02, 1.02)
//     `;
// }

// function resetCardTilt(e) {
//     const card = e.currentTarget;
//     card.style.transform = '';
// }

// ===================================
// LOADING ANIMATIONS
// ===================================

window.addEventListener("load", () => {
  // Add loaded class to body for any load-triggered animations
  document.body.classList.add("loaded");

  // Trigger any entrance animations
  const animatedElements = document.querySelectorAll("[data-animate]");
  animatedElements.forEach((el, index) => {
    setTimeout(() => {
      el.classList.add("animated");
    }, index * 100);
  });
});

// ===================================
// FORM INPUT ANIMATIONS
// ===================================

const formInputs = document.querySelectorAll("input");
formInputs.forEach((input) => {
  input.addEventListener("focus", function () {
    this.parentElement.classList.add("focused");
  });

  input.addEventListener("blur", function () {
    if (!this.value) {
      this.parentElement.classList.remove("focused");
    }
  });

  // Add typing animation
  input.addEventListener("input", function () {
    this.style.transform = "scale(1.01)";
    setTimeout(() => {
      this.style.transform = "";
    }, 100);
  });
});

// ===================================
// PERFORMANCE OPTIMIZATIONS
// ===================================

// Debounce function for scroll/resize events
function debounce(func, wait) {
  let timeout;
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout);
      func(...args);
    };
    clearTimeout(timeout);
    timeout = setTimeout(later, wait);
  };
}

// Optimized scroll handler
const handleScroll = debounce(() => {
  // Handle any scroll-based animations here
}, 100);

window.addEventListener("scroll", handleScroll);

// ===================================
// INITIALIZE APP
// ===================================

function initApp() {
  // Load saved state
  loadState();

  // Set initial animations
  setTimeout(() => {
    document.body.classList.add("initialized");
  }, 100);

  console.log("🚀 NexusHub initialized successfully!");
  console.log("Current theme:", appState.currentTheme);
  console.log("Logged in:", appState.isLoggedIn);
}

// Run initialization
initApp();

// ===================================
// EASTER EGG: KONAMI CODE
// ===================================

let konamiCode = [];
const konamiSequence = [
  "ArrowUp",
  "ArrowUp",
  "ArrowDown",
  "ArrowDown",
  "ArrowLeft",
  "ArrowRight",
  "ArrowLeft",
  "ArrowRight",
  "b",
  "a",
];

document.addEventListener("keydown", (e) => {
  konamiCode.push(e.key);
  konamiCode = konamiCode.slice(-10);

  if (JSON.stringify(konamiCode) === JSON.stringify(konamiSequence)) {
    activateEasterEgg();
    konamiCode = [];
  }
});

function activateEasterEgg() {
  // Create confetti effect
  for (let i = 0; i < 100; i++) {
    createConfetti();
  }

  // Show message
  const message = document.createElement("div");
  message.textContent = "🎉 You found the secret! 🎉";
  message.style.cssText = `
        position: fixed;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        background: var(--gradient-1);
        color: white;
        padding: 2rem 4rem;
        border-radius: 20px;
        font-family: 'Syne', sans-serif;
        font-size: 2rem;
        font-weight: 800;
        z-index: 10000;
        animation: bounce 0.5s ease;
        box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
    `;

  document.body.appendChild(message);

  setTimeout(() => {
    message.style.animation = "fadeOut 0.5s ease forwards";
    setTimeout(() => message.remove(), 500);
  }, 3000);
}

function createConfetti() {
  const confetti = document.createElement("div");
  const colors = ["#ff0066", "#00ffff", "#ffff00", "#00ff00", "#ff00ff"];
  const color = colors[Math.floor(Math.random() * colors.length)];

  confetti.style.cssText = `
        position: fixed;
        width: 10px;
        height: 10px;
        background: ${color};
        left: ${Math.random() * 100}%;
        top: -10px;
        z-index: 9999;
        animation: confettiFall ${2 + Math.random() * 2}s linear forwards;
        border-radius: 50%;
    `;

  document.body.appendChild(confetti);

  setTimeout(() => confetti.remove(), 4000);
}

// Add confetti animation
const confettiStyle = document.createElement("style");
confettiStyle.textContent = `
    @keyframes confettiFall {
        to {
            transform: translateY(100vh) rotate(${Math.random() * 360}deg);
            opacity: 0;
        }
    }
    
    @keyframes bounce {
        0%, 100% { transform: translate(-50%, -50%) scale(1); }
        50% { transform: translate(-50%, -50%) scale(1.1); }
    }
    
    @keyframes fadeOut {
        to {
            opacity: 0;
            transform: translate(-50%, -50%) scale(0.8);
        }
    }
`;
document.head.appendChild(confettiStyle);

// ===================================
// ACCESSIBILITY ENHANCEMENTS
// ===================================

// Keyboard navigation for cards
elements.featureCards.forEach((card, index) => {
  card.setAttribute("tabindex", "0");
  card.setAttribute("role", "button");
  card.setAttribute("aria-label", `Open ${card.dataset.feature} feature`);

  card.addEventListener("keypress", (e) => {
    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      card.click();
    }
  });
});

// Focus trap in sidebar
function trapFocus(element) {
  const focusableElements = element.querySelectorAll(
    'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])',
  );
  const firstElement = focusableElements[0];
  const lastElement = focusableElements[focusableElements.length - 1];

  element.addEventListener("keydown", (e) => {
    if (e.key !== "Tab") return;

    if (e.shiftKey) {
      if (document.activeElement === firstElement) {
        lastElement.focus();
        e.preventDefault();
      }
    } else {
      if (document.activeElement === lastElement) {
        firstElement.focus();
        e.preventDefault();
      }
    }
  });
}

function speed() {
  window.location.href = "https://www.google.com";
}
function history() {
  window.location.href = "https://www.google.com";
}
function all_servers() {
  window.location.href = "https://www.google.com";
}
function best_server() {
  window.location.href = "https://www.google.com";
}
// Apply focus trap to sidebar when opened
elements.profileBtn.addEventListener("click", () => {
  setTimeout(() => {
    elements.sidebarClose.focus();
  }, 300);
});

// Store user data in memory
const users = {};

function showForm(formType) {
  const signinForm = document.getElementById("signin-form");
  const signupForm = document.getElementById("signup-form");
  const tabs = document.querySelectorAll(".tab-btn");

  // Hide success message when switching tabs
  document.getElementById("successMsg").style.display = "none";

  if (formType === "signin") {
    signinForm.classList.add("active");
    signupForm.classList.remove("active");
    tabs[0].classList.add("active");
    tabs[1].classList.remove("active");
  } else {
    signupForm.classList.add("active");
    signinForm.classList.remove("active");
    tabs[1].classList.add("active");
    tabs[0].classList.remove("active");
  }
}

function showError(fieldId, message) {
  const errorEl = document.getElementById(fieldId + "-error");
  errorEl.textContent = message;
  errorEl.style.display = "block";
}

function clearErrors() {
  const errors = document.querySelectorAll(".error");
  errors.forEach((error) => (error.style.display = "none"));
}

function showSuccess(message) {
  const successEl = document.getElementById("successMsg");
  successEl.textContent = message;
  successEl.style.display = "block";
  setTimeout(() => {
    successEl.style.display = "none";
  }, 3000);
}

function handleSignUp(e) {
  e.preventDefault();
  clearErrors();

  const fullname = document.getElementById("signup-fullname").value;
  const email = document.getElementById("signup-email").value;
  const password = document.getElementById("signup-password").value;
  const confirmPassword = document.getElementById(
    "signup-confirm-password",
  ).value;

  // Validation
  if (fullname.trim().length < 2) {
    showError("signup-fullname", "Full name must be at least 2 characters");
    return;
  }

  if (password.length < 6) {
    showError("signup-password", "Password must be at least 6 characters");
    return;
  }

  if (password !== confirmPassword) {
    showError("signup-confirm", "Passwords do not match");
    return;
  }

  if (users[email]) {
    showError("signup-email", "Email already registered");
    return;
  }

  // Store user
  users[email] = { fullname, password };

  showSuccess("Account created successfully! You can now sign in.");

  // Reset form
  e.target.reset();

  // Switch to sign in after 1.5 seconds
  setTimeout(() => showForm("signin"), 1500);
}

function handleSignIn(e) {
  e.preventDefault();
  clearErrors();

  const email = document.getElementById("signin-email").value;
  const password = document.getElementById("signin-password").value;

  if (!users[email]) {
    showError("signin-email", "Email not found. Please sign up first.");
    return;
  }

  if (users[email].password !== password) {
    showError("signin-password", "Incorrect password");
    return;
  }

  showSuccess("Welcome back, " + users[email].fullname + "!");
  e.target.reset();
}
console.log("✨ All systems operational!");
