/* AURORA.GO — клиент */
(function () {
  'use strict';

  var $ = function (s, r) { return (r || document).querySelector(s); };
  var $$ = function (s, r) {
    return Array.prototype.slice.call((r || document).querySelectorAll(s));
  };

  var KIND_RU = { walk: 'Пешком', taxi: 'Такси', transfer: 'Трансфер' };
  var KIND_SHORT = { walk: 'пешком', taxi: 'такси', transfer: 'трансфер' };

  var S = {
    points: [], intervals: [], overview: null,
    pointId: null, intervalId: null,
    zoom: 1, panX: 0, panY: 0,
    stage: null, layers: null, pins: {}, tip: null,
    drag: null, moved: false
  };

  function api(url, opts) {
    return fetch(url, opts).then(function (r) {
      if (!r.ok) throw new Error('HTTP ' + r.status);
      return r.json();
    });
  }

  function el(tag, cls, html) {
    var n = document.createElement(tag);
    if (cls) n.className = cls;
    if (html != null) n.innerHTML = html;
    return n;
  }

  function clamp(v, a, b) { return v < a ? a : (v > b ? b : v); }

  function esc(s) {
    return String(s == null ? '' : s)
      .replace(/&/g, '&amp;').replace(/</g, '&lt;')
      .replace(/>/g, '&gt;').replace(/"/g, '&quot;');
  }

  function scoreClass(v) {
    if (v == null) return 's0';
    if (v < 20) return 's0';
    if (v < 40) return 's1';
    if (v < 60) return 's2';
    if (v < 80) return 's3';
    return 's4';
  }

  /* =================================================================
     ОБЛОЖКА
     ================================================================= */

  var HERO_CAPS = [
    { t: 'Мурманск', p: 'Город за полярным кругом. Света нет 40 дней в году.' },
    { t: 'Кольский залив', p: 'Север открыт — но фонари портят половину кадров.' },
    { t: 'Сопки', p: 'Двадцать минут от центра, и небо становится чёрным.' }
  ];

  function initHero() {
    var slides = $$('.hero-slide');
    var dots = $$('.hero-dot');
    var cap = $('#hero-caption');
    if (!slides.length) return;
    var idx = 0, timer = null;

    function show(i) {
      idx = (i + slides.length) % slides.length;
      slides.forEach(function (s, k) { s.classList.toggle('on', k === idx); });
      dots.forEach(function (d, k) { d.classList.toggle('on', k === idx); });
      if (cap && HERO_CAPS[idx]) {
        cap.style.opacity = '0';
        setTimeout(function () {
          $('b', cap).textContent = HERO_CAPS[idx].t;
          $('p', cap).textContent = HERO_CAPS[idx].p;
          cap.style.opacity = '1';
        }, 220);
      }
    }

    function start() {
      stop();
      timer = setInterval(function () { show(idx + 1); }, 6000);
    }
    function stop() { if (timer) { clearInterval(timer); timer = null; } }

    dots.forEach(function (d, k) {
      d.addEventListener('click', function () { show(k); start(); });
    });
    var prev = $('#hero-prev'), next = $('#hero-next');
    if (prev) prev.addEventListener('click', function () { show(idx - 1); start(); });
    if (next) next.addEventListener('click', function () { show(idx + 1); start(); });

    var cover = $('.hero-cover');
    if (cover) {
      cover.addEventListener('mouseenter', stop);
      cover.addEventListener('mouseleave', start);
    }
    document.addEventListener('visibilitychange', function () {
      if (document.hidden) stop(); else start();
    });
    show(0);
    start();
  }

  /* =================================================================
     ПОЯВЛЕНИЕ ПРИ СКРОЛЛЕ
     ================================================================= */

  function initReveal() {
    var nodes = $$('.reveal');
    if (!nodes.length) return;
    if (!('IntersectionObserver' in window)) {
      nodes.forEach(function (n) { n.classList.add('in'); });
      return;
    }
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (e.isIntersecting) {
          e.target.classList.add('in');
          io.unobserve(e.target);
        }
      });
    }, { threshold: 0.12, rootMargin: '0px 0px -60px 0px' });
    nodes.forEach(function (n) { io.observe(n); });
  }

  /* =================================================================
     КАРТА
     ================================================================= */

  var COORDS = {
    'murmansk-centre': [60.0, 48.4],
    'murmansk-memorial': [58.5, 43.5],
    'semcon': [63.0, 46.8],
    'abram-mys': [47.0, 50.0],
    'zelenets': [66.0, 53.2],
    'murmansk-bridge': [52.4, 41.9],
    'kirovsk': [62.0, 75.8],
    'kirovsk-pass': [64.5, 79.8],
    'lovozero': [74.0, 69.4],
    'teriberka': [85.0, 48.4],
    'kandalaksha': [38.0, 75.8]
  };

  var MAP_SVG = [
    '<svg viewBox="0 0 1000 620" preserveAspectRatio="none" aria-hidden="true"',
    ' style="position:absolute;inset:0;width:100%;height:100%;display:block">',
    '<defs>',
    '<linearGradient id="mgSea" x1="0" y1="0" x2="0" y2="1">',
    '<stop offset="0" stop-color="#D8ECF7"/><stop offset="1" stop-color="#BFE0F2"/>',
    '</linearGradient>',
    '<linearGradient id="mgLand" x1="0" y1="0" x2="0.4" y2="1">',
    '<stop offset="0" stop-color="#FAFDFE"/><stop offset="1" stop-color="#E4F1F8"/>',
    '</linearGradient>',
    '<linearGradient id="mgAur" x1="0" y1="0" x2="1" y2="0">',
    '<stop offset="0" stop-color="#0FB5A0" stop-opacity="0"/>',
    '<stop offset="0.35" stop-color="#0FB5A0" stop-opacity="0.42"/>',
    '<stop offset="0.7" stop-color="#00A3B8" stop-opacity="0.3"/>',
    '<stop offset="1" stop-color="#7B6FD6" stop-opacity="0"/>',
    '</linearGradient>',
    '<linearGradient id="mgAur2" x1="0" y1="0" x2="1" y2="0">',
    '<stop offset="0" stop-color="#7B6FD6" stop-opacity="0"/>',
    '<stop offset="0.5" stop-color="#7B6FD6" stop-opacity="0.2"/>',
    '<stop offset="1" stop-color="#0FB5A0" stop-opacity="0"/>',
    '</linearGradient>',
    '<filter id="mgBlur"><feGaussianBlur stdDeviation="20"/></filter>',
    '</defs>',

    '<rect width="1000" height="620" fill="url(#mgSea)"/>',

    '<g filter="url(#mgBlur)" opacity="0.85">',
    '<path d="M -80 104 C 160 48 380 124 580 68 C 760 20 900 84 1080 48"',
    ' fill="none" stroke="url(#mgAur)" stroke-width="54" stroke-linecap="round"/>',
    '<path d="M -80 160 C 180 104 400 172 610 116 C 790 68 940 132 1080 96"',
    ' fill="none" stroke="url(#mgAur2)" stroke-width="30" stroke-linecap="round"/>',
    '</g>',

    '<g stroke="#A9C9DB" stroke-width="1" stroke-dasharray="2 10" opacity="0.5" fill="none">',
    '<path d="M 0 290 C 250 272 750 308 1000 290"/>',
    '<path d="M 0 430 C 250 412 750 448 1000 430"/>',
    '<path d="M 240 0 C 228 210 252 410 240 620"/>',
    '<path d="M 610 0 C 598 210 622 410 610 620"/>',
    '</g>',

    '<path d="M 0 222 C 55 208 100 228 158 212 C 216 196 258 218 308 206',
    ' C 350 196 384 212 422 202 C 458 194 480 208 500 198',
    ' L 514 248 C 522 268 538 270 544 250 L 548 198',
    ' C 588 188 628 206 678 192 C 728 178 778 198 828 180',
    ' C 874 164 930 180 1000 162 L 1000 620 L 0 620 Z"',
    ' fill="url(#mgLand)" stroke="#7FA9C4" stroke-width="2.4"/>',

    '<path d="M 0 222 C 55 208 100 228 158 212 C 216 196 258 218 308 206',
    ' C 350 196 384 212 422 202 C 458 194 480 208 500 198"',
    ' fill="none" stroke="#5E93B8" stroke-width="2.6" opacity="0.5"/>',

    '<g fill="#C4E2F2" stroke="#8FB8D2" stroke-width="1.5">',
    '<path d="M 392 328 C 422 310 462 320 478 338 C 492 356 462 374 434 368',
    ' C 408 362 382 346 392 328 Z"/>',
    '<path d="M 654 326 C 682 314 712 324 722 342 C 730 358 704 370 680 364',
    ' C 658 358 642 340 654 326 Z"/>',
    '<path d="M 582 380 C 602 372 622 380 626 392 C 628 404 606 410 590 404',
    ' C 576 398 572 388 582 380 Z"/>',
    '</g>',

    '<g fill="none" stroke="#9CC2D8" stroke-width="1.8" stroke-linecap="round">',
    '<path d="M 478 340 C 498 362 512 388 526 418"/>',
    '<path d="M 632 358 C 650 376 664 392 680 410"/>',
    '</g>',

    '<g stroke="#6FA3C4" stroke-width="2.2" fill="none" stroke-linejoin="round" opacity="0.8">',
    '<path d="M 538 470 L 566 410 L 594 458 L 622 400 L 650 454"/>',
    '<path d="M 648 450 L 676 394 L 704 446"/>',
    '<path d="M 592 480 L 620 438 L 648 474"/>',
    '</g>',
    '<g fill="#A9C9DB">',
    '<path d="M 560 430 L 566 410 L 573 430 Z"/>',
    '<path d="M 617 418 L 622 400 L 628 418 Z"/>',
    '<path d="M 670 412 L 676 394 L 682 412 Z"/>',
    '</g>',

    '<path d="M 294 188 C 340 200 390 240 448 278 C 490 304 530 340 580 370"',
    ' fill="none" stroke="#94BDD6" stroke-width="1.8" stroke-dasharray="8 6" opacity="0.65"/>',

    '<g font-family="Manrope,Inter,sans-serif" font-weight="700" letter-spacing="0.14em">',
    '<text x="92" y="86" font-size="12" fill="#6A8CA3" opacity=".85">БАРЕНЦЕВО МОРЕ</text>',
    '<text x="512" y="316" font-size="10" fill="#7FA9C4" opacity=".85"',
    ' transform="rotate(-70 512 316)">КОЛЬСКИЙ ЗАЛ.</text>',
    '<text x="604" y="510" font-size="10" fill="#6A8CA3" opacity=".85">ХИБИНЫ</text>',
    '<text x="352" y="392" font-size="10" fill="#6A8CA3" opacity=".85">ИМАНДРА</text>',
    '</g>',

    '<g transform="translate(734 48)">',
    '<line x1="0" y1="0" x2="120" y2="0" stroke="#7FA9C4" stroke-width="1.8"/>',
    '<line x1="0" y1="-5" x2="0" y2="5" stroke="#7FA9C4" stroke-width="1.8"/>',
    '<line x1="60" y1="-3" x2="60" y2="3" stroke="#7FA9C4" stroke-width="1.4"/>',
    '<line x1="120" y1="-5" x2="120" y2="5" stroke="#7FA9C4" stroke-width="1.8"/>',
    '<text x="60" y="20" text-anchor="middle" font-family="Manrope,Inter,sans-serif"',
    ' font-size="10" font-weight="700" letter-spacing=".08em" fill="#5E93B8">50 км</text>',
    '</g>',

    '<g transform="translate(910 556)">',
    '<circle r="32" fill="#FFFFFF" fill-opacity=".72" stroke="#A9C9DB" stroke-width="1.5"/>',
    '<circle r="22" fill="none" stroke="#CFE6F2" stroke-width="1"/>',
    '<path d="M 0 -20 L 5.5 4 L 0 0 L -5.5 4 Z" fill="#00A3B8"/>',
    '<path d="M 0 20 L 5.5 -4 L 0 0 L -5.5 -4 Z" fill="#94BDD6"/>',
    '</g>',
    '</svg>'
  ].join('');

  /* =================================================================
     ЗУМ И ПЕРЕТАСКИВАНИЕ
     ================================================================= */

  function applyTransform() {
    if (!S.layers) return;
    S.layers.style.transform =
      'translate(' + S.panX + 'px,' + S.panY + 'px) scale(' + S.zoom + ')';
    var k = 1 / S.zoom;
    Object.keys(S.pins).forEach(function (id) {
      S.pins[id].style.transform = 'translate(-50%,-50%) scale(' + k + ')';
    });
  }

  function clampPan() {
    if (!S.stage) return;
    var w = S.stage.clientWidth, h = S.stage.clientHeight;
    S.panX = clamp(S.panX, w * (1 - S.zoom), 0);
    S.panY = clamp(S.panY, h * (1 - S.zoom), 0);
  }

  function zoomAt(factor, cx, cy) {
    if (!S.stage) return;
    var w = S.stage.clientWidth, h = S.stage.clientHeight;
    var nz = clamp(S.zoom * factor, 1, 2.6);
    if (Math.abs(nz - S.zoom) < 0.001) return;
    var px = (cx == null ? w / 2 : cx);
    var py = (cy == null ? h / 2 : cy);
    var contentX = (px - S.panX) / S.zoom;
    var contentY = (py - S.panY) / S.zoom;
    S.zoom = nz;
    S.panX = px - contentX * nz;
    S.panY = py - contentY * nz;
    clampPan();
    applyTransform();
    hideTip();
  }

  function resetZoom() {
    S.zoom = 1; S.panX = 0; S.panY = 0;
    applyTransform();
    hideTip();
  }

  function initZoom() {
    var stage = $('#map-stage');
    if (!stage) return;
    S.stage = stage;

    stage.addEventListener('wheel', function (e) {
      e.preventDefault();
      var r = stage.getBoundingClientRect();
      var f = e.deltaY < 0 ? 1.18 : 1 / 1.18;
      zoomAt(f, e.clientX - r.left, e.clientY - r.top);
    }, { passive: false });

    $$('[data-zoom]').forEach(function (b) {
      b.addEventListener('click', function () {
        var m = b.getAttribute('data-zoom');
        if (m === 'in') zoomAt(1.4);
        else if (m === 'out') zoomAt(1 / 1.4);
        else resetZoom();
      });
    });

    stage.addEventListener('pointerdown', function (e) {
      if (e.target.closest('.pin')) return;
      if (e.target.closest('.map-toolbar')) return;
      S.drag = { x: e.clientX, y: e.clientY, px: S.panX, py: S.panY };
      S.moved = false;
      stage.classList.add('grabbing');
      S.layers.classList.add('dragging');
      stage.setPointerCapture(e.pointerId);
    });

    stage.addEventListener('pointermove', function (e) {
      if (!S.drag) return;
      var dx = e.clientX - S.drag.x, dy = e.clientY - S.drag.y;
      if (Math.abs(dx) + Math.abs(dy) > 4) S.moved = true;
      if (S.zoom <= 1.001) return;
      S.panX = S.drag.px + dx;
      S.panY = S.drag.py + dy;
      clampPan();
      applyTransform();
      hideTip();
    });

    function endDrag(e) {
      if (!S.drag) return;
      S.drag = null;
      stage.classList.remove('grabbing');
      S.layers.classList.remove('dragging');
      if (stage.hasPointerCapture && e && e.pointerId != null) {
        try { stage.releasePointerCapture(e.pointerId); } catch (err) {}
      }
    }
    stage.addEventListener('pointerup', endDrag);
    stage.addEventListener('pointercancel', endDrag);
    stage.addEventListener('pointerleave', endDrag);

    window.addEventListener('resize', function () {
      clampPan(); applyTransform(); hideTip();
    });
  }

  /* =================================================================
     МАРКЕРЫ И ПОДСКАЗКА
     ================================================================= */

  function hideTip() {
    if (S.tip) S.tip.classList.remove('show');
  }

  function showTip(id) {
    if (!S.tip || !S.pointId) return;
    var d = (S.tipData || {})[id];
    var pin = S.pins[id];
    if (!d || !pin) return;
    var score = d.score == null ? '—' : d.score.toFixed(1);
    var kp = '—', cloud = '—';
    if (d.kp != null) kp = d.kp;
    if (d.cloud != null) cloud = d.cloud + '%';

    S.tip.innerHTML =
      '<div class="tip-name">' + esc(d.name) + '</div>' +
      '<div class="tip-city">' + esc(d.city) + ' · ' + esc(d.walk) + '</div>' +
      '<div class="tip-row"><span>Kp-индекс</span><b>' + kp + '</b></div>' +
      '<div class="tip-row"><span>Облачность</span><b>' + cloud + '</b></div>' +
      '<div class="tip-row"><span>Засветка</span><b>' + d.lp + '%</b></div>' +
      '<div class="tip-score"><span>Оценка</span><b>' + score + '</b></div>';

    var stage = S.stage.getBoundingClientRect();
    var box = pin.getBoundingClientRect();
    var tw = 250, th = 190;
    var x = box.left - stage.left + box.width / 2 + 14;
    var y = box.top - stage.top - 10;
    x = clamp(x, 10, Math.max(10, stage.width - tw - 10));
    y = clamp(y, th + 10, Math.max(th + 10, stage.height - 10));
    S.tip.style.left = x + 'px';
    S.tip.style.top = (y - 12) + 'px';
    S.tip.style.transform = 'translateY(-100%)';
    S.tip.classList.add('show');
  }

  function buildPins() {
    var host = $('#map');
    if (!host) return;
    host.innerHTML = '';

    S.points.forEach(function (p) {
      var c = COORDS[p.id];
      if (!c) return;
      var b = el('button', 'pin ' + p.kind);
      b.type = 'button';
      b.style.left = c[1] + '%';
      b.style.top = c[0] + '%';
      b.setAttribute('data-point', p.id);
      b.setAttribute('aria-label', p.name);
      b.innerHTML = '<span>' + esc(p.name) + '</span>';
      b.style.transform = 'translate(-50%,-50%)';

      b.addEventListener('click', function (e) {
        e.stopPropagation();
        if (S.moved) return;
        selectPoint(p.id);
      });
      b.addEventListener('mouseenter', function () { showTip(p.id); });
      b.addEventListener('mouseleave', hideTip);
      b.addEventListener('focus', function () { showTip(p.id); });
      b.addEventListener('blur', hideTip);

      host.appendChild(b);
      S.pins[p.id] = b;
    });
    applyTransform();
  }

  function markPins() {
    Object.keys(S.pins).forEach(function (id) {
      S.pins[id].classList.toggle('active', id === S.pointId);
    });
  }

  function initMapIllustration() {
    var box = $('#map-illustration');
    if (box) box.innerHTML = MAP_SVG;
    S.layers = $('#map-layers');
    S.tip = $('#tip');
  }

  /* =================================================================
     ПАНЕЛЬ РЕЗУЛЬТАТА
     ================================================================= */

  function renderPanel(data) {
    var out = $('#out');
    if (!out) return;

    if (!data || data.error) {
      out.innerHTML = '<p class="err">Не удалось получить прогноз.</p>';
      return;
    }

    var sc = data.score;
    var badgeCls = scoreClass(sc);
    var num = sc == null ? '—' : sc.toFixed(1);

    var html = '';
    html += '<div class="score-hero">';
    html += '<div class="score-big">' + num + '<small>/100</small></div>';
    html += '<span class="score-badge ' + badgeCls + '">' + esc(data.verdict) + '</span>';
    html += '<div class="score-note">' + esc(data.verdict_note) + '</div>';
    html += '</div>';

    if (data.data_status === 'stale') {
      html += '<div class="status-row stale">Наблюдение ' + data.age_minutes +
        ' мин назад. Данные устарели — относитесь к баллу осторожно.</div>';
    } else if (data.data_status === 'missing') {
      html += '<div class="status-row missing">Не хватает наблюдений. ' +
        'Оценка не рассчитана, чтобы не давать ложной уверенности.</div>';
    }

    (data.factors || []).forEach(function (f) {
      var miss = f.part == null;
      var w = miss ? 100 : Math.round(clamp(f.part, 0, 1) * 100);
      html += '<div class="factor">';
      html += '<div class="f-top"><span class="k">' + esc(f.label) + '</span>';
      html += '<span class="v">' + esc(f.value) + (f.unit || '') + '</span></div>';
      html += '<div class="bar"><i class="' + (miss ? 'miss' : '') +
        '" style="width:' + w + '%"></i></div>';
      html += '<div class="f-note">' + esc(f.note) + '</div>';
      html += '</div>';
    });

    html += '<div class="expl">' + data.explanation + '</div>';
    html += '<div class="meta">' + esc(data.interval_label) +
      ' · источник: ' + esc(data.source) + '</div>';

    out.innerHTML = html;
  }

  function loadForecast() {
    if (!S.pointId || !S.intervalId) return;
    var out = $('#out');
    if (out) out.innerHTML = '<p class="muted"><span class="spin"></span> Считаем…</p>';

    api('/api/forecast?point_id=' + encodeURIComponent(S.pointId) +
        '&interval_id=' + encodeURIComponent(S.intervalId))
      .then(renderPanel)
      .catch(function () {
        if (out) out.innerHTML = '<p class="err">Сервер не ответил. Проверьте, ' +
          'что uvicorn запущен.</p>';
      });
  }

  function selectPoint(id) {
    S.pointId = id;
    var p = S.points.filter(function (x) { return x.id === id; })[0];
    var t = $('#pp-title'), sub = $('#pp-sub');
    if (p && t) t.textContent = p.name;
    if (p && sub) sub.textContent = p.city + ' · ' + p.walk + ' · ' + KIND_SHORT[p.kind];
    markPins();
    loadForecast();
  }

  function stepPoint(delta) {
    if (!S.points.length) return;
    var i = S.points.findIndex(function (p) { return p.id === S.pointId; });
    if (i < 0) i = 0;
    var n = (i + delta + S.points.length) % S.points.length;
    selectPoint(S.points[n].id);
  }

  function buildStrip() {
    var host = $('#interval-strip');
    if (!host) return;
    host.innerHTML = '';
    S.intervals.forEach(function (iv, k) {
      var b = el('button', 'chip' + (k === 0 ? ' active' : ''), esc(iv.label));
      b.type = 'button';
      b.setAttribute('data-interval', iv.id);
      b.addEventListener('click', function () {
        S.intervalId = iv.id;
        $$('.chip').forEach(function (c) { c.classList.remove('active'); });
        b.classList.add('active');
        var cap = $('#interval-caption');
        if (cap) cap.textContent = iv.title;
        loadForecast();
      });
      host.appendChild(b);
    });
    if (S.intervals.length) {
      S.intervalId = S.intervals[0].id;
      var cap = $('#interval-caption');
      if (cap) cap.textContent = S.intervals[0].title;
    }
  }

  /* =================================================================
     ФОРМАТЫ: НАВЕДЕНИЕ ПОДСВЕЧИВАЕТ ТОЧКИ
     ================================================================= */

  function initFormats() {
    var cards = $$('.format-card');
    if (!cards.length) return;

    function fill(list, kind) {
      var items = S.points.filter(function (p) { return p.kind === kind; });
      list.innerHTML = '';
      items.slice(0, 4).forEach(function (p) {
        var d = (S.tipData || {})[p.id] || {};
        var sc = d.score;
        var txt = sc == null ? 'нет' : sc.toFixed(0);
        var li = el('li', '',
          '<span class="hf">' + esc(p.name) + '</span>' +
          '<span class="hd">' + esc(p.walk) + '</span>' +
          '<span class="hb' + (sc == null ? ' na' : '') + '">' + txt + '</span>');
        li.addEventListener('click', function () {
          selectPoint(p.id);
          var app = $('#app');
          if (app) app.scrollIntoView({ behavior: 'smooth', block: 'start' });
        });
        list.appendChild(li);
      });
    }

    cards.forEach(function (card) {
      var kind = card.getAttribute('data-format');
      var list = $('.hint-list', card);
      if (list) fill(list, kind);

      function dim(on) {
        Object.keys(S.pins).forEach(function (id) {
          var p = S.points.filter(function (x) { return x.id === id; })[0];
          if (!p) return;
          S.pins[id].classList.toggle('dim', on && p.kind !== kind);
        });
      }
      card.addEventListener('mouseenter', function () { dim(true); });
      card.addEventListener('mouseleave', function () { dim(false); });
    });
  }

  /* =================================================================
     КАТАЛОГ ТОЧЕК
     ================================================================= */

  function initSpots() {
    var grid = $('#spots-grid');
    if (!grid) return;

    var all = [];

    function render(kind) {
      api('/api/intervals').then(function (ivs) {
        return api('/api/overview?interval_id=' + encodeURIComponent(ivs[0].id));
      }).then(function (data) {
        all = data.results || [];
        paint(kind);
      }).catch(function () {
        grid.innerHTML = '<p class="err">Не удалось загрузить точки.</p>';
      });
    }

    function paint(kind) {
      var items = all.filter(function (r) {
        return kind === 'all' || r.kind === kind;
      });
      grid.innerHTML = '';
      items.forEach(function (r) {
        var sc = r.score == null ? '—' : r.score.toFixed(1);
        var card = el('article', 'spot',
          '<div class="spot-top">' +
            '<span class="spot-kind ' + r.kind + '">' + KIND_RU[r.kind] + '</span>' +
            '<span class="spot-city">' + esc(r.city) + '</span>' +
          '</div>' +
          '<h3>' + esc(r.point_name) + '</h3>' +
          '<p>' + esc(r.about) + '</p>' +
          '<div class="spot-foot">' +
            '<span>' + esc(r.walk) + '</span>' +
            '<b>' + sc + '</b>' +
          '</div>');
        card.addEventListener('click', function () {
          window.location.href = '/#app';
        });
        grid.appendChild(card);
      });
      if (!items.length) grid.innerHTML = '<p class="muted">Ничего не найдено.</p>';
    }

    $$('#spots-filters .filter').forEach(function (b) {
      b.addEventListener('click', function () {
        $$('#spots-filters .filter').forEach(function (x) { x.classList.remove('on'); });
        b.classList.add('on');
        paint(b.getAttribute('data-f'));
      });
    });

    render('all');
  }

  /* =================================================================
     СРАВНЕНИЕ
     ================================================================= */

  var CMP = { mode: 'points', picked: {} };

  function initCompare() {
    var box = $('#choices');
    if (!box) return;

    function renderChoices() {
      box.innerHTML = '';
      CMP.picked = {};
      var list = CMP.mode === 'points' ? S.points : S.intervals;
      list.forEach(function (item) {
        var id = item.id;
        var label = CMP.mode === 'points'
          ? item.name
          : (item.title || item.label);
        var lab = el('label', 'chk',
          '<input type="checkbox" value="' + esc(id) + '">' + esc(label));
        var input = $('input', lab);
        input.addEventListener('change', function () {
          lab.classList.toggle('on', input.checked);
          if (input.checked) CMP.picked[id] = true;
          else delete CMP.picked[id];
        });
        box.appendChild(lab);
      });
    }

    function fillSelects() {
      var si = $('#cmbi'), sp = $('#cmbp');
      if (si) {
        si.innerHTML = '';
        S.intervals.forEach(function (iv) {
          var o = el('option', '', esc(iv.title));
          o.value = iv.id;
          si.appendChild(o);
        });
      }
      if (sp) {
        sp.innerHTML = '';
        S.points.forEach(function (p) {
          var o = el('option', '', esc(p.name));
          o.value = p.id;
          sp.appendChild(o);
        });
      }
    }

    $$('.inner-tabs .app-tab').forEach(function (t) {
      t.addEventListener('click', function () {
        $$('.inner-tabs .app-tab').forEach(function (x) { x.classList.remove('active'); });
        t.classList.add('active');
        CMP.mode = t.getAttribute('data-mode');
        $('#w-int').style.display = CMP.mode === 'points' ? '' : 'none';
        $('#w-pt').style.display = CMP.mode === 'points' ? 'none' : '';
        renderChoices();
        $('#cmpout').innerHTML = '';
      });
    });

    var run = $('#run');
    if (run) {
      run.addEventListener('click', function () {
        var ids = Object.keys(CMP.picked);
        if (ids.length < 2) {
          $('#cmpout').innerHTML =
            '<div class="rec">Выберите хотя бы две позиции, чтобы было что сравнивать.</div>';
          return;
        }
        var body = { mode: CMP.mode, point_ids: [], interval_ids: [] };
        if (CMP.mode === 'points') {
          body.point_ids = ids;
          body.interval_ids = [$('#cmbi').value];
        } else {
          body.interval_ids = ids;
          body.point_ids = [$('#cmbp').value];
        }

        $('#cmpout').innerHTML = '<p class="muted"><span class="spin"></span> Сравниваем…</p>';
        api('/api/compare', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(body)
        }).then(function (data) {
          if (data.error) {
            $('#cmpout').innerHTML = '<p class="err">' + esc(data.error) + '</p>';
            return;
          }
          var rows = data.results || [];
          var head = CMP.mode === 'points' ? 'Точка' : 'Интервал';
          var html = '<table class="cmp-table"><thead><tr>' +
            '<th>' + head + '</th><th>Оценка</th><th>Вердикт</th></tr></thead><tbody>';
          rows.forEach(function (r) {
            var best = data.best_id && (CMP.mode === 'points'
              ? r.point_id === data.best_id
              : r.interval_id === data.best_id);
            var name = CMP.mode === 'points' ? r.point_name : r.interval_label;
            var num = r.score == null
              ? '<span class="na">нет данных</span>'
              : r.score.toFixed(1);
            html += '<tr' + (best ? ' class="best"' : '') + '>' +
              '<td>' + esc(name) + '</td>' +
              '<td class="big">' + num + '</td>' +
              '<td>' + esc(r.verdict) + '</td></tr>';
          });
          html += '</tbody></table>';
          html += '<div class="rec">' + (data.explanation || '') + '</div>';
          html += '<p class="meta">' + esc(data.disclaimer || '') + '</p>';
          $('#cmpout').innerHTML = html;
        }).catch(function () {
          $('#cmpout').innerHTML = '<p class="err">Сервер не ответил.</p>';
        });
      });
    }

    fillSelects();
    renderChoices();
  }

  /* =================================================================
     ПЕРЕКЛЮЧАТЕЛЬ КАРТА / СРАВНЕНИЕ
     ================================================================= */

  function initViews() {
    $$('.app-tabs > .app-tab[data-view]').forEach(function (t) {
      t.addEventListener('click', function () {
        $$('.app-tabs > .app-tab[data-view]').forEach(function (x) {
          x.classList.remove('active');
        });
        t.classList.add('active');
        var v = t.getAttribute('data-view');
        $('#view-forecast').style.display = v === 'forecast' ? '' : 'none';
        $('#view-compare').style.display = v === 'compare' ? '' : 'none';
        if (v === 'forecast') { clampPan(); applyTransform(); }
      });
    });
  }

  /* =================================================================
     ЗАПУСК
     ================================================================= */

  function boot() {
    initHero();
    initReveal();

    initSpots();
    var hasApp = $('#map-stage');
    if (!hasApp) return;

    initMapIllustration();
    initZoom();
    initViews();

    var prev = $('#pp-prev'), next = $('#pp-next');
    if (prev) prev.addEventListener('click', function () { stepPoint(-1); });
    if (next) next.addEventListener('click', function () { stepPoint(1); });

    Promise.all([api('/api/points'), api('/api/intervals')]).then(function (res) {
      S.points = res[0] || [];
      S.intervals = res[1] || [];
      S.tipData = {};
      S.points.forEach(function (p) { S.tipData[p.id] = { name: p.name, city: p.city, walk: p.walk, lp: p.light_pollution }; });

      buildPins();
      buildStrip();
      initFormats();
      initCompare();

      if (S.points.length) selectPoint(S.points[0].id);

      if (S.intervals.length && S.points.length) {
        api('/api/overview?interval_id=' + encodeURIComponent(S.intervals[0].id))
          .then(function (data) {
            (data.results || []).forEach(function (r) {
              var d = S.tipData[r.point_id];
              if (!d) return;
              d.score = r.score;
              d.verdict = r.verdict;
            });
            initFormats();
          });
      }
    }).catch(function () {
      var out = $('#out');
      if (out) out.innerHTML = '<p class="err">Сервер не ответил. Запущен ли uvicorn?</p>';
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', boot);
  } else {
    boot();
  }
})();
