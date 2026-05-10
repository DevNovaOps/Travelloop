/* ===================================================
   TRAVELOOP — Main Application JavaScript
   =================================================== */

// ---- Init Lucide Icons ----
document.addEventListener('DOMContentLoaded', () => {
  if (typeof lucide !== 'undefined') lucide.createIcons();
  initTheme();
  initNavbar();
  initStars();
  initAIChat();
  initFeatureCards();
  initDestinationCards();
  initTimeline();
  initScrollAnimations();
});

/* ==========================================
   Theme Toggle
   ========================================== */
function initTheme() {
  const saved = localStorage.getItem('traveloop_theme') || 'dark';
  document.documentElement.setAttribute('data-theme', saved);
  const btn = document.getElementById('themeToggle');
  if (!btn) return;
  btn.addEventListener('click', () => {
    const current = document.documentElement.getAttribute('data-theme');
    const next = current === 'dark' ? 'light' : 'dark';
    document.documentElement.setAttribute('data-theme', next);
    localStorage.setItem('traveloop_theme', next);
    if (typeof lucide !== 'undefined') lucide.createIcons();
  });
}

/* ==========================================
   Navbar scroll & mobile toggle
   ========================================== */
function initNavbar() {
  const nav = document.getElementById('navbar');
  if (nav) {
    window.addEventListener('scroll', () => {
      nav.classList.toggle('scrolled', window.scrollY > 40);
    });
  }
  const toggle = document.getElementById('navToggle');
  const links = document.getElementById('navLinks');
  if (toggle && links) {
    toggle.addEventListener('click', () => links.classList.toggle('open'));
    links.querySelectorAll('a').forEach(a => a.addEventListener('click', () => links.classList.remove('open')));
  }
}

/* ==========================================
   Star Particles Canvas
   ========================================== */
function initStars() {
  const canvas = document.getElementById('starsCanvas');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  let stars = [];
  const COUNT = 120;

  function resize() {
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
  }
  resize();
  window.addEventListener('resize', resize);

  for (let i = 0; i < COUNT; i++) {
    stars.push({
      x: Math.random() * canvas.width,
      y: Math.random() * canvas.height,
      r: Math.random() * 1.5 + 0.3,
      speed: Math.random() * 0.3 + 0.05,
      opacity: Math.random() * 0.6 + 0.2,
      flicker: Math.random() * 0.02
    });
  }

  function draw() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    stars.forEach(s => {
      s.opacity += s.flicker;
      if (s.opacity > 0.8 || s.opacity < 0.1) s.flicker *= -1;
      ctx.beginPath();
      ctx.arc(s.x, s.y, s.r, 0, Math.PI * 2);
      ctx.fillStyle = `rgba(148, 163, 184, ${s.opacity})`;
      ctx.fill();
      s.y += s.speed;
      if (s.y > canvas.height) { s.y = 0; s.x = Math.random() * canvas.width; }
    });
    requestAnimationFrame(draw);
  }
  draw();
}

/* ==========================================
   AI Chat Widget
   ========================================== */
function initAIChat() {
  const toggle = document.getElementById('aiChatToggle');
  const panel = document.getElementById('aiChatPanel');
  const input = document.getElementById('aiChatInput');
  const sendBtn = document.getElementById('aiChatSend');
  const messages = document.getElementById('aiChatMessages');
  if (!toggle || !panel) return;

  toggle.addEventListener('click', () => panel.classList.toggle('open'));

  const responses = [
    "I'd recommend visiting Kyoto in spring — the cherry blossoms are magical! 🌸",
    "For budget travel, consider hostels or capsule hotels. I can find some great options!",
    "The best time to visit Bali is April-October. Want me to plan a 7-day itinerary?",
    "Pro tip: Book flights on Tuesdays for the best deals ✈️",
    "I found 3 hidden gems near your destination! Want to explore them?",
    "Your current budget looks great! You could save 15% by shifting dates by 2 days.",
    "Consider this route: Tokyo → Osaka → Kyoto — saves 20% on transport! 🚅",
  ];

  function sendMessage() {
    const text = input.value.trim();
    if (!text) return;
    appendMsg(text, 'user');
    input.value = '';
    // Typing indicator
    const typing = document.createElement('div');
    typing.className = 'ai-msg ai-msg--bot typing-dots';
    typing.innerHTML = '<span></span><span></span><span></span>';
    messages.appendChild(typing);
    messages.scrollTop = messages.scrollHeight;

    setTimeout(() => {
      typing.remove();
      const resp = responses[Math.floor(Math.random() * responses.length)];
      appendMsg(resp, 'bot');
    }, 1200 + Math.random() * 800);
  }

  function appendMsg(text, type) {
    const div = document.createElement('div');
    div.className = `ai-msg ai-msg--${type}`;
    div.textContent = text;
    messages.appendChild(div);
    messages.scrollTop = messages.scrollHeight;
  }

  if (sendBtn) sendBtn.addEventListener('click', sendMessage);
  if (input) input.addEventListener('keydown', e => { if (e.key === 'Enter') sendMessage(); });
}

/* ==========================================
   Feature Cards (Landing Page)
   ========================================== */
function initFeatureCards() {
  const grid = document.getElementById('featureGrid');
  if (!grid) return;

  const features = [
    { icon: 'map', title: 'Multi-City Itineraries', desc: 'Plan complex routes across multiple cities with drag-and-drop simplicity.', color: 'cyan' },
    { icon: 'calendar-days', title: 'Smart Scheduling', desc: 'AI-powered date optimization that finds the best travel windows for you.', color: 'teal' },
    { icon: 'wallet', title: 'Budget Tracking', desc: 'Real-time expense tracking with visual breakdowns and saving suggestions.', color: 'purple' },
    { icon: 'compass', title: 'Activity Discovery', desc: 'Discover local experiences, restaurants, and hidden gems at every stop.', color: 'cyan' },
    { icon: 'share-2', title: 'Share & Collaborate', desc: 'Share trip plans with friends and plan together in real-time.', color: 'teal' },
    { icon: 'bot', title: 'Nova AI Assistant', desc: 'Your personal travel AI that gives recommendations and optimizes plans.', color: 'purple' },
  ];

  features.forEach((f, i) => {
    const card = document.createElement('div');
    card.className = `glass-card glass-card--glow feature-card animate-fadeInUp delay-${i % 6 + 1}`;
    card.innerHTML = `
      <div class="feature-card__icon" style="border-color:var(--${f.color});">
        <i data-lucide="${f.icon}" style="width:28px;height:28px;color:var(--${f.color});"></i>
      </div>
      <h3 class="feature-card__title">${f.title}</h3>
      <p class="feature-card__desc">${f.desc}</p>
    `;
    grid.appendChild(card);
  });
  if (typeof lucide !== 'undefined') lucide.createIcons();
}

/* ==========================================
   Destination Cards (Landing Page)
   ========================================== */
function initDestinationCards() {
  const grid = document.getElementById('destGrid');
  if (!grid) return;

  const destinations = [
    { name: 'Santorini, Greece', img: '/static/assets/images/santorini.png', days: '5 days', mood: 'Luxury', moodClass: 'luxury', price: '$2,400' },
    { name: 'Tokyo, Japan', img: '/static/assets/images/tokyo.png', days: '7 days', mood: 'Adventure', moodClass: 'adventure', price: '$1,800' },
    { name: 'Bali, Indonesia', img: '/static/assets/images/bali.png', days: '6 days', mood: 'Nature', moodClass: 'nature', price: '$1,200' },
  ];

  destinations.forEach((d, i) => {
    const card = document.createElement('div');
    card.className = `glass-card dest-card animate-fadeInUp delay-${i + 1}`;
    card.innerHTML = `
      <div class="dest-card__img-wrap">
        <img class="dest-card__img" src="${d.img}" alt="${d.name}" loading="lazy" />
      </div>
      <div class="dest-card__body">
        <div class="flex justify-between items-center">
          <h3 class="dest-card__name">${d.name}</h3>
          <span class="badge badge--${d.moodClass}">${d.mood}</span>
        </div>
        <div class="dest-card__meta">
          <span>📅 ${d.days}</span>
          <span>⭐ 4.${8 + i}</span>
        </div>
        <div class="dest-card__price">From ${d.price}</div>
      </div>
    `;
    grid.appendChild(card);
  });
}

/* ==========================================
   Timeline (Landing Page)
   ========================================== */
function initTimeline() {
  const container = document.getElementById('timelineDemo');
  if (!container) return;

  const items = [
    { day: 'Day 1', title: 'Arrive in Tokyo', desc: 'Check into hotel in Shinjuku. Evening walk through Kabukicho.' },
    { day: 'Day 2', title: 'Shibuya & Harajuku', desc: 'Explore Meiji Shrine, Takeshita Street, and Shibuya Crossing.' },
    { day: 'Day 3', title: 'Akihabara & Ueno', desc: 'Visit the electronics district and Ueno Park / National Museum.' },
    { day: 'Day 4', title: 'Day Trip to Kamakura', desc: 'See the Great Buddha and surf at Yuigahama Beach.' },
    { day: 'Day 5', title: 'Asakusa & Skytree', desc: 'Senso-ji Temple, Nakamise Street, and Tokyo Skytree sunset views.' },
  ];

  items.forEach((item, i) => {
    const el = document.createElement('div');
    el.className = `timeline__item animate-fadeInUp delay-${i + 1}`;
    el.innerHTML = `
      <div class="timeline__dot"></div>
      <div class="timeline__day">${item.day}</div>
      <div class="timeline__card glass-card glass-card--glow">
        <h4>${item.title}</h4>
        <p>${item.desc}</p>
      </div>
    `;
    container.appendChild(el);
  });
}

/* ==========================================
   Scroll Animations (Intersection Observer)
   ========================================== */
function initScrollAnimations() {
  const elements = document.querySelectorAll('.animate-fadeInUp, .animate-slideInLeft, .animate-slideInRight, .animate-scaleIn');
  if (!elements.length) return;

  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.style.opacity = '';
        observer.unobserve(entry.target);
      }
    });
  }, { threshold: 0.1, rootMargin: '0px 0px -40px 0px' });

  elements.forEach(el => observer.observe(el));
}

/* ==========================================
   Toast Notifications
   ========================================== */
function showToast(message, type = 'info') {
  const container = document.getElementById('toastContainer');
  if (!container) return;
  const toast = document.createElement('div');
  toast.className = `toast toast--${type}`;
  const icons = { success: '✅', error: '❌', info: 'ℹ️' };
  toast.innerHTML = `<span>${icons[type] || 'ℹ️'}</span><span>${message}</span>`;
  container.appendChild(toast);
  setTimeout(() => { toast.style.opacity = '0'; setTimeout(() => toast.remove(), 300); }, 3500);
}
