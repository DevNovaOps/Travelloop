/* ===================================================
   TRAVELLOOP — Dashboard Logic (Backend-Connected)
   =================================================== */

document.addEventListener('DOMContentLoaded', () => {
  initDashUser();
  initDashStats();
  initDashTrips();
  initSidebarNav();
});

/* ---- User greeting (from API) ---- */
async function initDashUser() {
  let name = 'Traveler';
  let email = 'user@travelloop.com';

  try {
    const res = await fetch('/api/profile/');
    if (res.ok) {
      const data = await res.json();
      name = `${data.firstName || ''} ${data.lastName || ''}`.trim() || 'Traveler';
      email = data.email || email;
    }
  } catch (e) {
    console.warn('Could not fetch profile for dashboard:', e);
  }

  const initial = name.charAt(0).toUpperCase();
  const hour = new Date().getHours();
  let greeting = 'Good evening';
  if (hour < 12) greeting = 'Good morning';
  else if (hour < 17) greeting = 'Good afternoon';

  const el = document.getElementById('dashGreeting');
  if (el) el.textContent = `${greeting}, ${name.split(' ')[0]}! 👋`;

  // Sidebar
  const sn = document.getElementById('sidebarName');
  if (sn) sn.textContent = name;
  const se = document.getElementById('sidebarEmail');
  if (se) se.textContent = email;
  const sa = document.getElementById('sidebarAvatar');
  if (sa) sa.textContent = initial;

  // Top-right profile dropdown
  const topName = document.getElementById('topName');
  if (topName) topName.textContent = name;
  const topEmail = document.getElementById('topEmail');
  if (topEmail) topEmail.textContent = email;
  const topAvatar = document.getElementById('topAvatar');
  if (topAvatar) topAvatar.textContent = initial;

  // Close dropdown on click outside
  document.addEventListener('click', (e) => {
    const profile = document.getElementById('topbarProfile');
    if (profile && !profile.contains(e.target)) {
      profile.classList.remove('open');
    }
  });
}

/* ---- Stats cards (from API) ---- */
async function initDashStats() {
  try {
    const [statsRes, tripsRes] = await Promise.all([
      fetch('/api/dashboard/stats/'),
      fetch('/api/trips/'),
    ]);

    if (!statsRes.ok || !tripsRes.ok) {
      console.warn('Could not fetch dashboard stats');
      initDashCharts([], 0, 0);
      return;
    }

    const stats = await statsRes.json();
    const tripsData = await tripsRes.json();
    const trips = tripsData.trips || [];

    // — Active Trips stat card
    const activeCount = stats.ongoing + stats.upcoming;
    const activeEl = document.querySelector('.stat-card:nth-child(1) .stat-card__value');
    const activeChange = document.querySelector('.stat-card:nth-child(1) .stat-card__change');
    if (activeEl) activeEl.textContent = activeCount;
    if (activeChange) activeChange.textContent = `${stats.ongoing} ongoing, ${stats.upcoming} upcoming`;

    // — Cities Visited stat card (count unique cities from sections)
    let citiesCount = 0;
    const uniqueCities = new Set();
    trips.forEach(t => {
      if (t.cities) t.cities.forEach(c => uniqueCities.add(c));
      if (t.destination) uniqueCities.add(t.destination);
    });
    citiesCount = uniqueCities.size;
    const citiesEl = document.querySelector('.stat-card:nth-child(2) .stat-card__value');
    const citiesChange = document.querySelector('.stat-card:nth-child(2) .stat-card__change');
    if (citiesEl) citiesEl.textContent = citiesCount;
    if (citiesChange) citiesChange.textContent = `${stats.totalTrips} total trips`;

    // — Total Budget stat card
    const budgetEl = document.querySelector('.stat-card:nth-child(3) .stat-card__value');
    const budgetChange = document.querySelector('.stat-card:nth-child(3) .stat-card__change');
    if (budgetEl) budgetEl.textContent = `$${Number(stats.totalBudget).toLocaleString()}`;
    if (budgetChange) {
      const spent = stats.totalSpent || 0;
      const saved = stats.totalBudget - spent;
      budgetChange.textContent = spent > 0 ? `$${Number(spent).toLocaleString()} spent` : 'No expenses yet';
    }

    // — Days Until Next Trip stat card
    const upcoming = trips
      .filter(t => t.status === 'upcoming' && t.startDate)
      .sort((a, b) => new Date(a.startDate) - new Date(b.startDate));

    const daysEl = document.querySelector('.stat-card:nth-child(4) .stat-card__value');
    const daysChange = document.querySelector('.stat-card:nth-child(4) .stat-card__change');
    if (upcoming.length > 0) {
      const nextTrip = upcoming[0];
      const daysUntil = Math.max(0, Math.ceil((new Date(nextTrip.startDate) - new Date()) / 86400000));
      if (daysEl) daysEl.textContent = daysUntil;
      if (daysChange) daysChange.textContent = nextTrip.name;
    } else {
      if (daysEl) daysEl.textContent = '—';
      if (daysChange) {
        daysChange.textContent = 'No upcoming trips';
        daysChange.style.color = 'var(--text-muted)';
      }
    }

    // Initialize charts with real data
    initDashCharts(trips, stats.totalBudget, stats.totalSpent);

    // Initialize timeline with next upcoming trip
    if (upcoming.length > 0) {
      initDashTimeline(upcoming[0]);
    } else {
      initDashTimeline(null);
    }

  } catch (e) {
    console.error('Error loading dashboard stats:', e);
    initDashCharts([], 0, 0);
    initDashTimeline(null);
  }
}

/* ---- Charts (data-driven) ---- */
function initDashCharts(trips, totalBudget, totalSpent) {
  const isDark = document.documentElement.getAttribute('data-theme') !== 'light';
  const gridColor = isDark ? 'rgba(148,163,184,0.08)' : 'rgba(15,23,42,0.06)';
  const textColor = isDark ? '#94A3B8' : '#475569';

  // Budget doughnut — aggregate budgets by trip mood
  const budgetCtx = document.getElementById('budgetChart');
  if (budgetCtx) {
    const moodBudgets = {};
    trips.forEach(t => {
      const mood = t.mood || 'other';
      moodBudgets[mood] = (moodBudgets[mood] || 0) + (t.budget || 0);
    });

    const labels = Object.keys(moodBudgets).length > 0
      ? Object.keys(moodBudgets).map(m => m.charAt(0).toUpperCase() + m.slice(1))
      : ['No Data'];
    const data = Object.keys(moodBudgets).length > 0
      ? Object.values(moodBudgets)
      : [1];
    const colors = ['#06B6D4', '#8B5CF6', '#14B8A6', '#F59E0B', '#EC4899', '#22C55E'];

    new Chart(budgetCtx, {
      type: 'doughnut',
      data: {
        labels,
        datasets: [{
          data,
          backgroundColor: colors.slice(0, labels.length),
          borderColor: isDark ? '#0F172A' : '#FFFFFF',
          borderWidth: 3,
          hoverOffset: 12,
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        cutout: '68%',
        plugins: {
          legend: {
            position: 'bottom',
            labels: { color: textColor, padding: 16, usePointStyle: true, pointStyleWidth: 10, font: { family: 'Inter', size: 12 } }
          },
          tooltip: {
            backgroundColor: isDark ? '#1E293B' : '#FFFFFF',
            titleColor: isDark ? '#F8FAFC' : '#0F172A',
            bodyColor: textColor,
            borderColor: isDark ? 'rgba(255,255,255,0.08)' : 'rgba(0,0,0,0.08)',
            borderWidth: 1,
            cornerRadius: 12,
            padding: 12,
            callbacks: { label: ctx => ` ${ctx.label}: $${ctx.raw.toLocaleString()}` }
          }
        }
      }
    });
  }

  // Monthly spending bar — aggregate budgets by month
  const spendCtx = document.getElementById('spendingChart');
  if (spendCtx) {
    const monthNames = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
    const monthlyData = new Array(12).fill(0);
    trips.forEach(t => {
      if (t.startDate) {
        const month = new Date(t.startDate).getMonth();
        monthlyData[month] += (t.budget || 0);
      }
    });

    // Show only months with data, or current 6-month window
    const now = new Date();
    const startMonth = Math.max(0, now.getMonth() - 5);
    const displayLabels = monthNames.slice(startMonth, startMonth + 6);
    const displayData = monthlyData.slice(startMonth, startMonth + 6);

    new Chart(spendCtx, {
      type: 'bar',
      data: {
        labels: displayLabels,
        datasets: [{
          label: 'Budget ($)',
          data: displayData,
          backgroundColor: ctx => {
            const g = ctx.chart.ctx.createLinearGradient(0, 0, 0, 300);
            g.addColorStop(0, 'rgba(34,211,238,0.7)');
            g.addColorStop(1, 'rgba(139,92,246,0.3)');
            return g;
          },
          borderRadius: 8,
          borderSkipped: false,
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          tooltip: {
            backgroundColor: isDark ? '#1E293B' : '#FFFFFF',
            titleColor: isDark ? '#F8FAFC' : '#0F172A',
            bodyColor: textColor,
            borderColor: isDark ? 'rgba(255,255,255,0.08)' : 'rgba(0,0,0,0.08)',
            borderWidth: 1, cornerRadius: 12, padding: 12,
          }
        },
        scales: {
          x: { grid: { display: false }, ticks: { color: textColor, font: { family: 'Inter', size: 12 } } },
          y: { grid: { color: gridColor }, ticks: { color: textColor, font: { family: 'Inter', size: 12 }, callback: v => `$${v}` }, border: { display: false } }
        }
      }
    });
  }
}

/* ---- Trip cards (from API) ---- */
async function initDashTrips() {
  const grid = document.getElementById('tripsGrid');
  if (!grid) return;

  try {
    const res = await fetch('/api/trips/?status=upcoming');
    if (!res.ok) throw new Error('Failed to fetch trips');
    const data = await res.json();
    const trips = (data.trips || []).slice(0, 3);

    if (trips.length === 0) {
      grid.innerHTML = `
        <div class="glass-card glass-card--glow p-6" style="grid-column:1/-1;text-align:center;">
          <p style="color:var(--text-muted);margin-bottom:var(--sp-4);">No upcoming trips yet.</p>
          <a href="/create-trip/" class="btn btn--primary">Plan Your First Trip</a>
        </div>`;
      return;
    }

    const moodLabels = { adventure: 'Adventure', luxury: 'Luxury', nature: 'Nature', budget: 'Budget', nightlife: 'Nightlife' };

    trips.forEach((t, i) => {
      const startDate = new Date(t.startDate);
      const endDate = new Date(t.endDate);
      const dateStr = `${startDate.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })} – ${endDate.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}`;
      const mood = moodLabels[t.mood] || t.mood;
      const img = t.image || '/static/assets/images/placeholder.png';

      const card = document.createElement('div');
      card.className = `glass-card glass-card--glow dest-card animate-fadeInUp delay-${i + 1}`;
      card.style.cursor = 'pointer';
      card.onclick = () => window.location.href = '/itinerary-view/?trip=' + t.id;
      card.innerHTML = `
        <div class="dest-card__img-wrap"><img class="dest-card__img" src="${img}" alt="${t.name}" loading="lazy" onerror="this.style.display='none'" /></div>
        <div class="dest-card__body">
          <div class="flex justify-between items-center">
            <h3 class="dest-card__name">${t.name}</h3>
            <span class="badge badge--${t.mood}">${mood}</span>
          </div>
          <div class="dest-card__meta">
            <span>📅 ${dateStr}</span>
            <span>🏙️ ${t.citiesCount || 0} cities</span>
          </div>
          <div class="dest-card__price">$${Number(t.budget).toLocaleString()}</div>
        </div>
      `;
      grid.appendChild(card);
    });
  } catch (e) {
    console.error('Error loading trips:', e);
    grid.innerHTML = `
      <div class="glass-card glass-card--glow p-6" style="grid-column:1/-1;text-align:center;">
        <p style="color:var(--text-muted);">Could not load trips. Please try again.</p>
      </div>`;
  }
}

/* ---- Dashboard timeline (from next trip API) ---- */
async function initDashTimeline(nextTrip) {
  const container = document.getElementById('dashTimeline');
  const titleEl = container?.closest('.glass-card')?.querySelector('h3');
  if (!container) return;

  if (!nextTrip) {
    if (titleEl) titleEl.textContent = 'No Upcoming Itinerary';
    container.innerHTML = `<p style="color:var(--text-muted);text-align:center;padding:var(--sp-4);">Create a trip and build an itinerary to see it here.</p>`;
    // Hide badge
    const badge = container?.closest('.glass-card')?.querySelector('.badge');
    if (badge) badge.style.display = 'none';
    return;
  }

  if (titleEl) titleEl.textContent = `${nextTrip.name} Itinerary`;
  // Update badge
  const badge = container?.closest('.glass-card')?.querySelector('.badge');
  const moodLabels = { adventure: 'Adventure', luxury: 'Luxury', nature: 'Nature', budget: 'Budget', nightlife: 'Nightlife' };
  if (badge) {
    badge.textContent = `${moodLabels[nextTrip.mood] || nextTrip.mood} Trip`;
    badge.className = `badge badge--${nextTrip.mood}`;
  }

  try {
    const res = await fetch(`/api/trips/${nextTrip.id}/`);
    if (!res.ok) throw new Error('Failed to fetch trip detail');
    const tripDetail = await res.json();

    const sections = tripDetail.sections || [];
    if (sections.length === 0) {
      container.innerHTML = `<p style="color:var(--text-muted);text-align:center;padding:var(--sp-4);">No itinerary sections yet. <a href="/build-itinerary/?trip=${nextTrip.id}" class="text-cyan">Build one →</a></p>`;
      return;
    }

    // Show up to 3 sections as timeline
    sections.slice(0, 3).forEach((section, i) => {
      const dateStr = section.startDate
        ? new Date(section.startDate).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
        : '';
      const dayLabel = dateStr ? `Section ${i + 1} — ${dateStr}` : `Section ${i + 1}`;
      const activities = (section.activities || []).map(a => a.name).join(', ') || section.description || 'No activities yet';

      const el = document.createElement('div');
      el.className = `timeline__item animate-fadeInUp delay-${i + 1}`;
      el.innerHTML = `
        <div class="timeline__dot"></div>
        <div class="timeline__day">${dayLabel}</div>
        <div class="timeline__card glass-card glass-card--glow">
          <h4>${section.title}</h4>
          <p>${activities}</p>
        </div>
      `;
      container.appendChild(el);
    });
  } catch (e) {
    console.error('Error loading trip timeline:', e);
    container.innerHTML = `<p style="color:var(--text-muted);text-align:center;padding:var(--sp-4);">Could not load itinerary.</p>`;
  }
}

/* ---- Sidebar nav ---- */
function initSidebarNav() {
  const path = window.location.pathname;
  document.querySelectorAll('.sidebar__link').forEach(link => {
    link.classList.remove('active');
    if (link.getAttribute('href') === path) {
      link.classList.add('active');
    }
  });
}
