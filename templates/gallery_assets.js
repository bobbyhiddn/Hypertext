(function () {
  function qs(sel, root) { return (root || document).querySelector(sel); }
  function qsa(sel, root) { return Array.from((root || document).querySelectorAll(sel)); }

  function rarityRank(r) {
    switch ((r || '').toUpperCase()) {
      case 'GLORIOUS': return 4;
      case 'RARE': return 3;
      case 'UNCOMMON': return 2;
      case 'COMMON': return 1;
      default: return 0;
    }
  }

  function initSeriesPage() {
    var gallery = qs('#gallery');
    if (!gallery) return;

    var cards = qsa('[data-card]', gallery);
    var search = qs('#search');
    var sort = qs('#sort');
    var rarity = qs('#rarity');
    var type = qs('#type');
    var reset = qs('#reset');

    function updateStats(visibleCards) {
      var totals = { total: 0, common: 0, uncommon: 0, rare: 0, glorious: 0 };
      visibleCards.forEach(function (el) {
        totals.total += 1;
        var r = (el.dataset.rarity || '').toLowerCase();
        if (r === 'common') totals.common += 1;
        if (r === 'uncommon') totals.uncommon += 1;
        if (r === 'rare') totals.rare += 1;
        if (r === 'glorious') totals.glorious += 1;
      });

      qsa('[data-stat]').forEach(function (el) {
        var key = el.getAttribute('data-stat');
        el.textContent = String(totals[key] || 0);
      });
    }

    function apply() {
      var query = (search && search.value || '').trim().toLowerCase();
      var rarityVal = (rarity && rarity.value || 'ALL').toUpperCase();
      var typeVal = (type && type.value || 'ALL').toUpperCase();

      var visible = [];
      cards.forEach(function (el) {
        var ok = true;
        if (rarityVal !== 'ALL' && (el.dataset.rarity || '') !== rarityVal) ok = false;
        if (typeVal !== 'ALL' && (el.dataset.type || '') !== typeVal) ok = false;

        if (ok && query) {
          var hay = ((el.dataset.word || '') + ' ' + (el.dataset.gloss || '')).toLowerCase();
          if (hay.indexOf(query) === -1) ok = false;
        }

        el.style.display = ok ? '' : 'none';
        if (ok) visible.push(el);
      });

      updateStats(visible);
      sortVisible(visible);
    }

    function sortVisible(visible) {
      var val = (sort && sort.value) || 'number-asc';
      var parts = val.split('-');
      var key = parts[0];
      var dir = parts[1] === 'desc' ? -1 : 1;

      visible.sort(function (a, b) {
        if (key === 'number') {
          return dir * ((parseInt(a.dataset.number || '0', 10) || 0) - (parseInt(b.dataset.number || '0', 10) || 0));
        }
        if (key === 'word') {
          return dir * String(a.dataset.word || '').localeCompare(String(b.dataset.word || ''));
        }
        if (key === 'rarity') {
          return dir * (rarityRank(a.dataset.rarity) - rarityRank(b.dataset.rarity));
        }
        if (key === 'type') {
          return dir * String(a.dataset.type || '').localeCompare(String(b.dataset.type || ''));
        }
        return 0;
      });

      visible.forEach(function (el) { gallery.appendChild(el); });
    }

    if (search) search.addEventListener('input', apply);
    if (sort) sort.addEventListener('change', apply);
    if (rarity) rarity.addEventListener('change', apply);
    if (type) type.addEventListener('change', apply);
    if (reset) reset.addEventListener('click', function () {
      if (search) search.value = '';
      if (rarity) rarity.value = 'ALL';
      if (type) type.value = 'ALL';
      if (sort) sort.value = 'number-asc';
      apply();
    });

    // Lightbox
    var lightbox = qs('#lightbox');
    var lbImg = qs('#lbImg');
    var lbTitle = qs('#lbTitle');
    var lbSubtitle = qs('#lbSubtitle');
    var lbDownload = qs('#lbDownload');

    function close() {
      if (!lightbox) return;
      lightbox.setAttribute('aria-hidden', 'true');
      document.body.style.overflow = '';
    }

    function open(el) {
      if (!lightbox) return;
      var img = qs('img', el);
      if (!img) return;

      lbImg.src = img.src;
      lbImg.alt = img.alt || '';

      var title = '#' + (el.dataset.number || '???') + ' ' + (el.dataset.word || '');
      var sub = (el.dataset.type || '') + ' • ' + (el.dataset.rarity || '');

      if (lbTitle) lbTitle.textContent = title;
      if (lbSubtitle) lbSubtitle.textContent = sub;
      if (lbDownload) lbDownload.href = img.src;

      lightbox.setAttribute('aria-hidden', 'false');
      document.body.style.overflow = 'hidden';
    }

    cards.forEach(function (el) {
      var img = qs('img', el);
      if (img) img.addEventListener('click', function () { open(el); });
    });

    if (lightbox) {
      qsa('[data-close]', lightbox).forEach(function (el) {
        el.addEventListener('click', close);
      });
      window.addEventListener('keydown', function (e) {
        if (e.key === 'Escape') close();
      });
    }

    apply();
  }

  initSeriesPage();
})();
