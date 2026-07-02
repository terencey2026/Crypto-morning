/* ============================================
   CRYPTO MORNING BRIEFING — APP ENGINE
   Data fetching · Rendering · Navigation
   ============================================ */

(function () {
  'use strict';

  // ── State ──────────────────────────────────
  const state = {
    currentDate: null,
    data: null,
    index: null,
    isLoading: false,
  };

  // ── DOM Cache ──────────────────────────────
  const $ = (id) => document.getElementById(id);
  const dom = {};

  function cacheDom() {
    dom.loadingScreen = $('loading-screen');
    dom.errorScreen = $('error-screen');
    dom.errorTitle = $('error-title');
    dom.errorMessage = $('error-message');
    dom.app = $('app');
    dom.dateText = $('date-text');
    dom.weekdayBadge = $('weekday-badge');
    dom.datePicker = $('date-picker');
    dom.updateTime = $('update-time');
    dom.btnPrev = $('btn-prev');
    dom.btnNext = $('btn-next');
    dom.btnRefresh = $('btn-refresh');
    dom.cryptoGrid = $('crypto-grid');
    dom.stocksContainer = $('stocks-container');
    dom.sectionAlerts = $('section-alerts');
    dom.alertsContainer = $('alerts-container');
    dom.etfCard = $('etf-card');
    dom.newsContainer = $('news-container');
    dom.viewpointsContainer = $('viewpoints-container');
    dom.riskCard = $('risk-card');
    dom.sectionSupplementary = $('section-supplementary');
    dom.supplementaryContainer = $('supplementary-container');
    dom.footerHistory = $('footer-history');
    dom.mainContent = $('main-content');
  }

  // ── Utility: Number Formatting ─────────────
  function formatLargeNumber(num) {
    if (num == null || isNaN(num)) return '—';
    const abs = Math.abs(num);
    if (abs >= 1e12) return (num / 1e12).toFixed(2) + 'T';
    if (abs >= 1e9) return (num / 1e9).toFixed(2) + 'B';
    if (abs >= 1e6) return (num / 1e6).toFixed(1) + 'M';
    if (abs >= 1e3) return (num / 1e3).toFixed(1) + 'K';
    return num.toFixed(0);
  }

  function formatPrice(price) {
    if (price == null || isNaN(price)) return '—';
    if (Math.abs(price) < 1) return '$' + price.toFixed(4);
    return '$' + price.toLocaleString('en-US', {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    });
  }

  function formatPercent(pct) {
    if (pct == null || isNaN(pct)) return '—';
    const sign = pct > 0 ? '+' : '';
    return sign + pct.toFixed(2) + '%';
  }

  function changeClass(pct) {
    if (pct == null || isNaN(pct) || pct === 0) return 'flat';
    return pct > 0 ? 'positive' : 'negative';
  }

  function isLargeMove(pct) {
    return pct != null && Math.abs(pct) > 5;
  }

  function formatTime(isoStr) {
    if (!isoStr) return '';
    try {
      const d = new Date(isoStr);
      const hh = String(d.getHours()).padStart(2, '0');
      const mm = String(d.getMinutes()).padStart(2, '0');
      return `${hh}:${mm}`;
    } catch {
      return '';
    }
  }

  function formatPublishTime(isoStr) {
    if (!isoStr) return '';
    try {
      const d = new Date(isoStr);
      const month = String(d.getMonth() + 1).padStart(2, '0');
      const day = String(d.getDate()).padStart(2, '0');
      const hh = String(d.getHours()).padStart(2, '0');
      const mm = String(d.getMinutes()).padStart(2, '0');
      return `${month}-${day} ${hh}:${mm}`;
    } catch {
      return '';
    }
  }

  function escapeHtml(str) {
    if (!str) return '';
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
  }

  // ── Data Fetching ──────────────────────────
  async function fetchJSON(url) {
    const resp = await fetch(url, { cache: 'no-cache' });
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
    return resp.json();
  }

  async function loadIndex() {
    try {
      state.index = await fetchJSON('data/index.json');
    } catch {
      state.index = { dates: [], latest: null };
    }
  }

  async function loadDate(date) {
    if (state.isLoading) return;
    state.isLoading = true;

    showLoading();

    try {
      await loadIndex();

      const url = date === 'latest'
        ? 'data/latest.json'
        : `data/${date}.json`;

      const data = await fetchJSON(url);
      state.data = data;
      state.currentDate = data.date || date;

      hideLoading();
      hideError();
      showApp();
      render();
      animateSections();
    } catch (err) {
      console.error('Failed to load data:', err);
      hideLoading();

      if (date === 'latest') {
        showError('欢迎使用加密晨报', '暂无可用数据，请稍后再试或添加数据文件');
      } else {
        showError('该日期暂无晨报数据', `日期 ${date} 的数据文件未找到`);
      }
    } finally {
      state.isLoading = false;
    }
  }

  // ── UI State Helpers ───────────────────────
  function showLoading() {
    dom.loadingScreen.classList.remove('hidden');
    dom.errorScreen.classList.add('hidden');
    dom.app.classList.add('hidden');
  }

  function hideLoading() {
    dom.loadingScreen.classList.add('hidden');
  }

  function showError(title, message) {
    dom.errorTitle.textContent = title;
    dom.errorMessage.textContent = message;
    dom.errorScreen.classList.remove('hidden');
    dom.app.classList.add('hidden');
  }

  function hideError() {
    dom.errorScreen.classList.add('hidden');
  }

  function showApp() {
    dom.app.classList.remove('hidden');
  }

  // ── Section Animation ─────────────────────
  function animateSections() {
    const sections = dom.mainContent.querySelectorAll('.section-animate');
    sections.forEach((el) => el.classList.remove('visible'));

    sections.forEach((section, i) => {
      setTimeout(() => {
        section.classList.add('visible');
      }, 80 + i * 60);
    });
  }

  // ── Render ─────────────────────────────────
  function render() {
    const d = state.data;
    if (!d) return;

    renderHeader(d);
    renderCrypto(d.market_data?.crypto);
    renderStocks(d.market_data?.stocks);
    renderETF(d.analysis?.etf_summary);
    renderNews(d.news);
    renderViewpoints(d.analysis?.viewpoints);
    renderRisk(d.analysis?.risk_alerts);
    renderSupplementary(d.analysis?.supplementary_news);
    renderFooter();
    updateNavButtons();
  }

  // ── Header ─────────────────────────────────
  function renderHeader(d) {
    dom.dateText.textContent = d.date || '—';
    dom.weekdayBadge.textContent = d.weekday || '—';

    if (d.is_weekend_recap) {
      // Add weekend badge if not already present
      let badge = dom.weekdayBadge.parentNode.querySelector('.weekend-badge');
      if (!badge) {
        badge = document.createElement('span');
        badge.className = 'weekend-badge';
        badge.textContent = '周末回顾';
        dom.weekdayBadge.parentNode.appendChild(badge);
      }
    } else {
      const badge = dom.weekdayBadge.parentNode.querySelector('.weekend-badge');
      if (badge) badge.remove();
    }

    if (d.generated_at) {
      dom.updateTime.textContent = `更新于 ${formatTime(d.generated_at)}`;
    } else {
      dom.updateTime.textContent = '';
    }

    if (d.date) {
      dom.datePicker.value = d.date;
    }
  }

  // ── Crypto Grid ────────────────────────────
  function renderCrypto(cryptoList) {
    if (!cryptoList || !cryptoList.length) {
      dom.cryptoGrid.innerHTML = '<p style="color:var(--text-tertiary);grid-column:1/-1;text-align:center;font-style:italic;">暂无加密货币数据</p>';
      return;
    }

    dom.cryptoGrid.innerHTML = cryptoList.map((c) => {
      const cls = changeClass(c.change_24h_pct);
      const pulse = isLargeMove(c.change_24h_pct) ? ' pulse' : '';
      const arrow = c.change_24h_pct > 0 ? '▲' : c.change_24h_pct < 0 ? '▼' : '';

      return `
        <div class="crypto-card">
          <div class="crypto-symbol">${escapeHtml(c.symbol)}</div>
          <div class="crypto-name">${escapeHtml(c.name || '')}</div>
          <div class="crypto-price mono">${formatPrice(c.price)}</div>
          <div class="crypto-change ${cls}${pulse}">
            ${arrow} ${formatPercent(c.change_24h_pct)}
          </div>
          <div class="crypto-volume">24h量 <span class="mono">${formatLargeNumber(c.volume_24h)}</span></div>
        </div>`;
    }).join('');
  }

  // ── Stocks ─────────────────────────────────
  function renderStocks(stocks) {
    const container = dom.stocksContainer;
    if (!stocks || !stocks.primary || !stocks.primary.length) {
      container.innerHTML = '<p style="color:var(--text-tertiary);text-align:center;font-style:italic;">暂无概念股数据</p>';
      return;
    }

    // Group by category
    const groups = {};
    stocks.primary.forEach((s) => {
      const group = s.group || '其他';
      if (!groups[group]) groups[group] = [];
      groups[group].push(s);
    });

    let html = '';
    for (const [groupName, items] of Object.entries(groups)) {
      html += `<div class="stock-group">
        <div class="stock-group-label">${escapeHtml(groupName)}</div>`;

      items.forEach((s) => {
        const cls = changeClass(s.change_pct);
        const pulse = isLargeMove(s.change_pct) ? ' pulse' : '';
        const arrow = s.change_pct > 0 ? '▲' : s.change_pct < 0 ? '▼' : '';

        html += `
          <div class="stock-row">
            <span class="stock-ticker">${escapeHtml(s.ticker)}</span>
            <span class="stock-name">${escapeHtml(s.name || '')}</span>
            <span class="stock-price mono">${formatPrice(s.price)}</span>
            <span class="stock-change ${cls}${pulse} mono">
              ${arrow} ${formatPercent(s.change_pct)}
            </span>
          </div>`;
      });

      html += '</div>';
    }

    container.innerHTML = html;
  }

  // ── Secondary Alerts ───────────────────────
  function renderAlerts(alerts) {
    if (!alerts || !alerts.length) {
      dom.sectionAlerts.classList.add('hidden');
      return;
    }

    dom.sectionAlerts.classList.remove('hidden');

    dom.alertsContainer.innerHTML = alerts.map((a) => {
      const cls = changeClass(a.change_pct);
      const arrow = a.change_pct > 0 ? '▲' : a.change_pct < 0 ? '▼' : '';

      return `
        <div class="alert-card">
          <div class="alert-indicator"></div>
          <div class="alert-info">
            <div class="alert-ticker">${escapeHtml(a.ticker)}</div>
            <div class="alert-name">${escapeHtml(a.name || '')} · ${escapeHtml(a.group || '')}</div>
          </div>
          <div class="alert-meta">
            <div class="alert-price mono">${formatPrice(a.price)}</div>
            <div class="alert-change ${cls} mono">${arrow} ${formatPercent(a.change_pct)}</div>
          </div>
        </div>`;
    }).join('');
  }

  // ── Handle both stocks render + alerts in one call ──
  function renderStocksAll(stocks) {
    renderStocks(stocks);
    renderAlerts(stocks?.secondary_alerts);
  }

  // ── ETF Summary ────────────────────────────
  function renderETF(summary) {
    if (!summary) {
      dom.etfCard.innerHTML = '<p class="etf-empty">暂无 ETF 概况数据</p>';
      return;
    }
    dom.etfCard.innerHTML = `<p class="etf-text">${escapeHtml(summary)}</p>`;
  }

  // ── News ───────────────────────────────────
  function renderNews(newsList) {
    const container = dom.newsContainer;
    if (!newsList || !newsList.length) {
      container.innerHTML = '<p style="color:var(--text-tertiary);text-align:center;font-style:italic;">暂无新闻</p>';
      return;
    }

    container.innerHTML = newsList.map((n) => {
      const sentimentCls = n.sentiment === 'positive' ? 'positive'
        : n.sentiment === 'negative' ? 'negative'
        : 'neutral';

      const linkIcon = `<svg class="news-link-icon" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/><polyline points="15 3 21 3 21 9"/><line x1="10" y1="14" x2="21" y2="3"/></svg>`;

      const tag = n.url ? 'a' : 'div';
      const href = n.url ? ` href="${escapeHtml(n.url)}" target="_blank" rel="noopener noreferrer"` : '';

      return `
        <${tag} class="news-item"${href}>
          <span class="sentiment-dot ${sentimentCls}" title="${sentimentCls === 'positive' ? '利多' : sentimentCls === 'negative' ? '利空' : '中性'}"></span>
          <div class="news-content">
            <div class="news-title">${escapeHtml(n.title)}</div>
            <div class="news-meta">
              <span class="news-source">${escapeHtml(n.source || '')}</span>
              <span>${formatPublishTime(n.published_at)}</span>
            </div>
          </div>
          ${n.url ? linkIcon : ''}
        </${tag}>`;
    }).join('');
  }

  // ── Viewpoints (MOST IMPORTANT) ────────────
  function renderViewpoints(viewpoints) {
    const container = dom.viewpointsContainer;
    if (!viewpoints || !viewpoints.length) {
      container.innerHTML = '<p style="color:var(--text-tertiary);text-align:center;font-style:italic;">暂无核心观点</p>';
      return;
    }

    container.innerHTML = viewpoints.map((v) => {
      const dir = v.direction === 'bullish' ? 'bullish'
        : v.direction === 'bearish' ? 'bearish'
        : 'neutral-dir';

      const dirArrow = v.direction === 'bullish' ? '↗'
        : v.direction === 'bearish' ? '↘'
        : '→';

      // Parse targets
      let targetsHtml = '';
      if (v.targets) {
        const tags = v.targets.split(/[\/,、]/).map((t) => t.trim()).filter(Boolean);
        targetsHtml = `
          <div class="viewpoint-section">
            <div class="viewpoint-label">【标的】</div>
            <div class="viewpoint-targets">
              ${tags.map((t) => `<span class="target-tag">${escapeHtml(t)}</span>`).join('')}
            </div>
          </div>`;
      }

      return `
        <div class="viewpoint-card ${dir}">
          <div class="viewpoint-header">
            <div class="direction-icon ${dir}">${dirArrow}</div>
            <div class="viewpoint-title">${escapeHtml(v.title)}</div>
          </div>
          ${v.view ? `
          <div class="viewpoint-section">
            <div class="viewpoint-label">【观点】</div>
            <div class="viewpoint-text">${escapeHtml(v.view)}</div>
          </div>` : ''}
          ${v.logic ? `
          <div class="viewpoint-section">
            <div class="viewpoint-label">【逻辑】</div>
            <div class="viewpoint-text">${escapeHtml(v.logic)}</div>
          </div>` : ''}
          ${targetsHtml}
        </div>`;
    }).join('');
  }

  // ── Risk Alerts ────────────────────────────
  function renderRisk(risks) {
    if (!risks || !risks.length) {
      dom.riskCard.innerHTML = '<p class="risk-empty">暂无风险提示</p>';
      return;
    }

    dom.riskCard.innerHTML = `
      <ul class="risk-list">
        ${risks.map((r) => `
          <li class="risk-item">
            <span class="risk-bullet">●</span>
            <span>${escapeHtml(r)}</span>
          </li>`).join('')}
      </ul>`;
  }

  // ── Supplementary News ─────────────────────
  function renderSupplementary(items) {
    if (!items || !items.length) {
      dom.sectionSupplementary.classList.add('hidden');
      return;
    }

    dom.sectionSupplementary.classList.remove('hidden');

    dom.supplementaryContainer.innerHTML = items.map((item) => {
      const linkHtml = item.url
        ? `<a class="supp-link" href="${escapeHtml(item.url)}" target="_blank" rel="noopener noreferrer">查看原文 →</a>`
        : '';

      return `
        <div class="supp-card">
          <div class="supp-title">${escapeHtml(item.title)}</div>
          ${item.summary ? `<div class="supp-summary">${escapeHtml(item.summary)}</div>` : ''}
          <div class="supp-meta">
            <span class="supp-source">${escapeHtml(item.source || '')}</span>
            ${linkHtml}
          </div>
        </div>`;
    }).join('');
  }

  // ── Footer ─────────────────────────────────
  function renderFooter() {
    const count = state.index?.dates?.length || 0;
    dom.footerHistory.textContent = count > 0
      ? `共收录 ${count} 期晨报`
      : '';
  }

  // ── Navigation ─────────────────────────────
  function updateNavButtons() {
    const dates = state.index?.dates || [];
    const curIdx = dates.indexOf(state.currentDate);

    // dates[0] is the latest, higher index = older
    // Prev = older (curIdx + 1), Next = newer (curIdx - 1)
    dom.btnPrev.disabled = curIdx < 0 || curIdx >= dates.length - 1;
    dom.btnNext.disabled = curIdx <= 0;
  }

  function navigatePrev() {
    const dates = state.index?.dates || [];
    const curIdx = dates.indexOf(state.currentDate);
    if (curIdx >= 0 && curIdx < dates.length - 1) {
      loadDate(dates[curIdx + 1]);
    }
  }

  function navigateNext() {
    const dates = state.index?.dates || [];
    const curIdx = dates.indexOf(state.currentDate);
    if (curIdx > 0) {
      loadDate(dates[curIdx - 1]);
    }
  }

  function navigateToDate(dateStr) {
    if (dateStr) {
      loadDate(dateStr);
    }
  }

  // ── Override the render of stocks to include alerts ──
  function renderAll() {
    const d = state.data;
    if (!d) return;
    renderHeader(d);
    renderCrypto(d.market_data?.crypto);
    renderStocksAll(d.market_data?.stocks);
    renderETF(d.analysis?.etf_summary);
    renderNews(d.news);
    renderViewpoints(d.analysis?.viewpoints);
    renderRisk(d.analysis?.risk_alerts);
    renderSupplementary(d.analysis?.supplementary_news);
    renderFooter();
    updateNavButtons();
  }

  // Patch: use renderAll in main render
  function render() {
    renderAll();
  }

  // ── Event Binding ──────────────────────────
  function bindEvents() {
    dom.btnPrev.addEventListener('click', navigatePrev);
    dom.btnNext.addEventListener('click', navigateNext);

    dom.datePicker.addEventListener('change', (e) => {
      navigateToDate(e.target.value);
    });

    dom.btnRefresh.addEventListener('click', () => {
      dom.btnRefresh.classList.add('spinning');
      const target = state.currentDate || 'latest';
      loadDate(target).finally(() => {
        setTimeout(() => dom.btnRefresh.classList.remove('spinning'), 600);
      });
    });

    // Keyboard nav
    document.addEventListener('keydown', (e) => {
      if (e.key === 'ArrowLeft') navigatePrev();
      if (e.key === 'ArrowRight') navigateNext();
    });
  }

  // ── Public API (for error screen button) ───
  window.CryptoBriefing = {
    loadLatest: () => loadDate('latest'),
  };

  // ── Init ───────────────────────────────────
  async function init() {
    cacheDom();
    bindEvents();
    await loadDate('latest');
  }

  // Boot
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
