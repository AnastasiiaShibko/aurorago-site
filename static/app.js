/* AURORA.GO — клиент */
(function () {
  'use strict';

  var $ = function (s, r) { return (r || document).querySelector(s); };
  var $$ = function (s, r) {
    return Array.prototype.slice.call((r || document).querySelectorAll(s));
  };

  var KIND_RU = { walk: '', taxi: '', transfer: '' };
  var KIND_SHORT = { walk: '', taxi: '', transfer: '' };

  /* -----------------------------------------------------------------
     Географическая рамка карты.
     Всё, что рисуется, задаётся реальными широтой и долготой.
     ----------------------------------------------------------------- */

  var FRAME = {
    lonMin: 30.0, lonMax: 37.5,
    latMin: 66.4, latMax: 69.7,
    vw: 1000, vh: 620
  };

  function project(lat, lon) {
    return [
      (lon - FRAME.lonMin) / (FRAME.lonMax - FRAME.lonMin) * FRAME.vw,
      (FRAME.latMax - lat) / (FRAME.latMax - FRAME.latMin) * FRAME.vh
    ];
  }

  /* Возвращает [top%, left%] — в том порядке, в каком нужно для CSS */
  function percent(lat, lon) {
    return [
      (FRAME.latMax - lat) / (FRAME.latMax - FRAME.latMin) * 100,
      (lon - FRAME.lonMin) / (FRAME.lonMax - FRAME.lonMin) * 100
    ];
  }

  /* Северный берег: от норвежской границы до горла Белого моря */
  var COAST = [
    [69.68, 30.00], [69.42, 30.55], [69.45, 31.60], [69.36, 32.60],
    [69.30, 33.40], [69.20, 34.40], [69.15, 35.20], [68.92, 36.10],
    [68.70, 36.90], [68.45, 37.50]
  ];

  var LAND = COAST.concat([
    [66.40, 37.50], [66.40, 30.00]
  ]);

  /* Кольский залив — узкая полоса моря, врезанная в сушу */
  var BAY = [
    [69.30, 33.30], [69.10, 33.20], [68.95, 33.10], [68.85, 33.03],
    [68.85, 33.13], [68.95, 33.22], [69.12, 33.34], [69.31, 33.42]
  ];

  /* Озеро Имандра */
  var IMANDRA = [
    [67.62, 32.72], [67.54, 32.95], [67.48, 33.10], [67.42, 32.95],
    [67.48, 32.70], [67.56, 32.58]
  ];

  var RIVERS = [
    [[68.95, 33.15], [68.82, 33.00], [68.72, 32.82], [68.64, 32.60]],
    [[67.52, 33.05], [67.40, 32.85], [67.28, 32.62]]
  ];

  var CITY_MARKS = [
    { n: 'МУРМАНСК',   lat: 68.97, lon: 33.08, dx: 8,  dy: -8 },
    { n: 'КИРОВСК',    lat: 67.61, lon: 33.73, dx: 8,  dy: 16 },
    { n: 'ТЕРИБЕРКА',  lat: 69.16, lon: 35.14, dx: -8, dy: -12 },
    { n: 'КАНДАЛАКША', lat: 67.16, lon: 32.41, dx: 8,  dy: 16 }
  ];

  var S = {
    points: [], intervals: [],
    pointId: null, intervalId: null,
    zoom: 1, panX: 0, panY: 0,
    stage: null, layers: null, pins: {}, tip: null,
    tipData: {}, drag: null, moved: false
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
          var b = $('b', cap), p = $('p', cap);
          if (b) b.textContent = HERO_CAPS[idx].t;
          if (p) p.textContent = HERO_CAPS[idx].p;
          cap.style.opacity = '1';
        }, 220);
      }
    }

    function start() { stop(); timer = setInterval(function () { show(idx + 1); }, 6000); }
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
     ПОДЛОЖКА КАРТЫ
     ================================================================= */

  function polyPath(points, close) {
    if (!points.length) return '';
    var p = project(points[0][0], points[0][1]);
    var d = 'M ' + p[0].toFixed(1) + ' ' + p[1].toFixed(1);
    for (var i = 1; i < points.length; i++) {
      p = project(points[i][0], points[i][1]);
      d += ' L ' + p[0].toFixed(1) + ' ' + p[1].toFixed(1);
    }
    return close === false ? d : d + ' Z';
  }

  function buildMapSVG() {
    var p = [];

    p.push('<svg viewBox="0 0 ' + FRAME.vw + ' ' + FRAME.vh + '"',
      ' preserveAspectRatio="none" aria-hidden="true"',
      ' style="position:absolute;inset:0;width:100%;height:100%;display:block">');

    p.push('<defs>',
      '<linearGradient id="mgSea" x1="0" y1="0" x2="0" y2="1">',
      '<stop offset="0" stop-color="#CFE6F2"/><stop offset="1" stop-color="#DCEFF8"/>',
      '</linearGradient>',
      '<linearGradient id="mgLand" x1="0" y1="0" x2="0.4" y2="1">',
      '<stop offset="0" stop-color="#FBFDFE"/><stop offset="1" stop-color="#E9F4FA"/>',
      '</linearGradient>',
      '<linearGradient id="mgAur" x1="0" y1="0" x2="1" y2="0">',
      '<stop offset="0" stop-color="#0FB5A0" stop-opacity="0"/>',
      '<stop offset="0.4" stop-color="#0FB5A0" stop-opacity="0.35"/>',
      '<stop offset="1" stop-color="#7B6FD6" stop-opacity="0"/>',
      '</linearGradient>',
      '<filter id="mgBlur"><feGaussianBlur stdDeviation="18"/></filter>',
      '</defs>');

    p.push('<rect width="', FRAME.vw, '" height="', FRAME.vh, '" fill="url(#mgSea)"/>');

    p.push('<g filter="url(#mgBlur)" opacity="0.75">',
      '<path d="M -60 50 C 250 10 620 80 1060 30" fill="none"',
      ' stroke="url(#mgAur)" stroke-width="40" stroke-linecap="round"/>',
      '</g>');

    p.push('<g stroke="#A9C9DB" stroke-width="0.8" stroke-dasharray="2 9"',
      ' opacity="0.4" fill="none">');
    [67, 68, 69].forEach(function (lat) {
      var q = project(lat, FRAME.lonMin);
      p.push('<line x1="0" y1="', q[1].toFixed(1), '" x2="', FRAME.vw,
        '" y2="', q[1].toFixed(1), '"/>');
    });
    [31, 33, 35, 37].forEach(function (lon) {
      var q = project(FRAME.latMin, lon);
      p.push('<line x1="', q[0].toFixed(1), '" y1="0" x2="', q[0].toFixed(1),
        '" y2="', FRAME.vh, '"/>');
    });
    p.push('</g>');

    /* суша */
    p.push('<path d="', polyPath(LAND), '" fill="url(#mgLand)"',
      ' stroke="#7FA9C4" stroke-width="2.2" stroke-linejoin="round"/>');

    /* вода внутри суши */
    p.push('<path d="', polyPath(BAY), '" fill="#CFE6F2" stroke="#8FB8D2"',
      ' stroke-width="1.2"/>');
    p.push('<path d="', polyPath(IMANDRA), '" fill="#CFE6F2" stroke="#8FB8D2"',
      ' stroke-width="1.2"/>');

    /* реки */
    p.push('<g fill="none" stroke="#9CC2D8" stroke-width="1.6"',
      ' stroke-linecap="round" opacity="0.8">');
    RIVERS.forEach(function (r) { p.push('<path d="', polyPath(r, false), '"/>'); });
    p.push('</g>');

    /* подписи */
    p.push('<g font-family="Manrope,Inter,sans-serif" font-weight="700"',
      ' letter-spacing="0.14em">');

    var sea = project(69.50, 31.3);
    p.push('<text x="', sea[0].toFixed(1), '" y="', sea[1].toFixed(1),
      '" font-size="12" fill="#6A8CA3" opacity=".85">БАРЕНЦЕВО МОРЕ</text>');

    var white = project(66.75, 35.6);
    p.push('<text x="', white[0].toFixed(1), '" y="', white[1].toFixed(1),
      '" font-size="10" fill="#6A8CA3" opacity=".7">БЕЛОЕ МОРЕ</text>');

    var gulf = project(69.02, 33.55);
    p.push('<text x="', gulf[0].toFixed(1), '" y="', gulf[1].toFixed(1),
      '" font-size="8" fill="#7FA9C4" opacity=".9">КОЛЬСКИЙ ЗАЛ.</text>');

    var khib = project(67.78, 34.35);
    p.push('<text x="', khib[0].toFixed(1), '" y="', khib[1].toFixed(1),
      '" font-size="10" fill="#6A8CA3" opacity=".85">ХИБИНЫ</text>');

    var im = project(67.36, 32.85);
    p.push('<text x="', im[0].toFixed(1), '" y="', im[1].toFixed(1),
      '" font-size="8" fill="#6A8CA3" opacity=".8">ИМАНДРА</text>');

    CITY_MARKS.forEach(function (c) {
      var q = project(c.lat, c.lon);
      p.push('<text x="', (q[0] + c.dx).toFixed(1), '" y="', (q[1] + c.dy).toFixed(1),
        '" font-size="8" fill="#5E93B8" opacity=".65">', c.n, '</text>');
    });

    p.push('</g>');

    /* масштабная линейка 50 км */
    var kmLon = 50 / (111.32 * Math.cos(68 * Math.PI / 180));
    var s0 = project(69.62, 30.4);
    var s1 = project(69.62, 30.4 + kmLon);
    var barW = Math.abs(s1[0] - s0[0]);
    p.push('<g transform="translate(', (FRAME.vw - barW - 60).toFixed(1), ' 34)">',
      '<line x1="0" y1="0" x2="', barW.toFixed(1), '" y2="0" stroke="#7FA9C4" stroke-width="1.8"/>',
      '<line x1="0" y1="-5" x2="0" y2="5" stroke="#7FA9C4" stroke-width="1.8"/>',
      '<line x1="', (barW / 2).toFixed(1), '" y1="-3" x2="', (barW / 2).toFixed(1),
      '" y2="3" stroke="#7FA9C4" stroke-width="1.4"/>',
      '<line x1="', barW.toFixed(1), '" y1="-5" x2="', barW.toFixed(1),
      '" y2="5" stroke="#7FA9C4" stroke-width="1.8"/>',
      '<text x="', (barW / 2).toFixed(1), '" y="20" text-anchor="middle"',
      ' font-family="Manrope,Inter,sans-serif" font-size="10" font-weight="700"',
      ' letter-spacing=".08em" fill="#5E93B8">50 км</text>',
      '</g>');

    /* роза ветров */
    p.push('<g transform="translate(', FRAME.vw - 84, ' ', FRAME.vh - 62, ')">',
            '<circle r="28" fill="#FFFFFF" fill-opacity=".7" stroke="#A9C9DB" stroke-width="1.5"/>',
      '<circle r="19" fill="none" stroke="#CFE6F2" stroke-width="1"/>',
      '<path d="M 0 -17 L 5 4 L 0 0 L -5 4 Z" fill="#00A3B8"/>',
      '<path d="M 0 17 L 5 -4 L 0 0 L -5 -4 Z" fill="#94BDD6"/>',
      '<text x="0" y="-21" text-anchor="middle" font-size="7" font-weight="800"',
      ' font-family="Manrope,Inter,sans-serif" fill="#5E93B8">N</text>',
      '</g>');

    p.push('</svg>');
    return p.join('');
  }

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
    var nz = clamp(S.zoom * factor, 1, 3);
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
      zoomAt(e.deltaY < 0 ? 1.18 : 1 / 1.18, e.clientX - r.left, e.clientY - r.top);
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
      if (S.layers) S.layers.classList.add('dragging');
      try { stage.setPointerCapture(e.pointerId); } catch (err) {}
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
      if (S.layers) S.layers.classList.remove('dragging');
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
    if (!S.tip) return;
    var d = (S.tipData || {})[id];
    var pin = S.pins[id];
    if (!d || !pin) return;

    var score = d.score == null ? '—' : d.score.toFixed(1);
    var kp = d.kp != null ? d.kp : '—';
    var cloud = d.cloud != null ? d.cloud + '%' : '—';
    var lp = d.lp != null ? d.lp + '%' : '—';

    S.tip.innerHTML =
      '<div class="tip-name">' + esc(d.name) + '</div>' +
      '<div class="tip-city">' + esc(d.city) + ' · ' + esc(d.walk) + '</div>' +
      '<div class="tip-row"><span>Kp-индекс</span><b>' + esc(kp) + '</b></div>' +
      '<div class="tip-row"><span>Облачность</span><b>' + esc(cloud) + '</b></div>' +
      '<div class="tip-row"><span>Засветка</span><b>' + esc(lp) + '</b></div>' +
      '<div class="tip-score"><span>Оценка</span><b>' + esc(score) + '</b></div>';

    var stage = S.stage.getBoundingClientRect();
    var box = pin.getBoundingClientRect();
    var tw = 240, th = 180;
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
    S.pins = {};

    S.points.forEach(function (pt) {
      if (pt.lat == null || pt.lon == null) return;
      var pos = percent(pt.lat, pt.lon);

      var b = el('button', 'pin ' + pt.kind);
      b.type = 'button';
      b.style.left = pos[1].toFixed(3) + '%';
      b.style.top = pos[0].toFixed(3) + '%';
      b.style.transform = 'translate(-50%,-50%)';
      b.setAttribute('data-point', pt.id);
      b.setAttribute('aria-label', pt.name);
      b.innerHTML = '<span>' + esc(pt.name) + '</span>';

      b.addEventListener('click', function (e) {
        e.stopPropagation();
        if (S.moved) return;
        selectPoint(pt.id);
      });
      b.addEventListener('mouseenter', function () { showTip(pt.id); });
      b.addEventListener('mouseleave', hideTip);
      b.addEventListener('focus', function () { showTip(pt.id); });
      b.addEventListener('blur', hideTip);

      host.appendChild(b);
      S.pins[pt.id] = b;
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
    if (box) box.innerHTML = buildMapSVG();
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
    var num = sc == null ? '—' : sc.toFixed(1);

    var html = '';
    html += '<div class="score-hero">';
    html += '<div class="score-big">' + num + '<small>/100</small></div>';
    html += '<span class="score-badge ' + scoreClass(sc) + '">' + esc(data.verdict) + '</span>';
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
      html += '<span class="v">' + esc(f.value) + esc(f.unit || '') + '</span></div>';
      html += '<div class="bar"><i class="' + (miss ? 'miss' : '') +
        '" style="width:' + w + '%"></i></div>';
      html += '<div class="f-note">' + esc(f.note) + '</div>';
      html += '</div>';
    });

    html += '<div class="expl">' + (data.explanation || '') + '</div>';
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
      .then(function (data) {
        renderPanel(data);
        var d = S.tipData[S.pointId];
        if (d) {
          d.score = data.score;
          d.verdict = data.verdict;
          (data.factors || []).forEach(function (f) {
            if (f.key === 'kp') d.kp = f.value;
            if (f.key === 'cloud') d.cloud = f.value;
          });
        }
      })
      .catch(function () {
        if (out) out.innerHTML = '<p class="err">Сервер не ответил. ' +
          'Проверьте, что uvicorn запущен.</p>';
      });
  }

  function selectPoint(id) {
    S.pointId = id;
    var p = null;
    for (var i = 0; i < S.points.length; i++) {
      if (S.points[i].id === id) { p = S.points[i]; break; }
    }
    var t = $('#pp-title'), sub = $('#pp-sub');
    if (p && t) t.textContent = p.name;
    if (p && sub) {
      sub.textContent = p.city + ' · ' + p.walk + ' · ' + (KIND_SHORT[p.kind] || p.kind);
    }
    markPins();
    loadForecast();
  }

  function stepPoint(delta) {
    if (!S.points.length) return;
    var i = -1;
    for (var k = 0; k < S.points.length; k++) {
      if (S.points[k].id === S.pointId) { i = k; break; }
    }
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
     ФОРМАТЫ
     ================================================================= */

  function fillHints() {
    $$('.format-card').forEach(function (card) {
      var kind = card.getAttribute('data-format');
      var list = $('.hint-list', card);
      if (!list) return;

      var items = S.points.filter(function (p) { return p.kind === kind; });
      list.innerHTML = '';

      items.slice(0, 4).forEach(function (p) {
        var d = S.tipData[p.id] || {};
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
    });
  }

  function initFormats() {
    var cards = $$('.format-card');
    if (!cards.length) return;

    cards.forEach(function (card) {
      var kind = card.getAttribute('data-format');

      function dim(on) {
        Object.keys(S.pins).forEach(function (id) {
          var p = null;
          for (var i = 0; i < S.points.length; i++) {
            if (S.points[i].id === id) { p = S.points[i]; break; }
          }
          if (!p) return;
          S.pins[id].classList.toggle('dim', on && p.kind !== kind);
        });
      }
      card.addEventListener('mouseenter', function () { dim(true); });
      card.addEventListener('mouseleave', function () { dim(false); });
    });

    fillHints();
  }

  /* =================================================================
     КАТАЛОГ ТОЧЕК
     ================================================================= */

  function initSpots() {
    var grid = $('#spots-grid');
    if (!grid) return;

    var all = [];
    var current = 'all';

    function paint(kind) {
      var items = all.filter(function (r) {
        return kind === 'all' || r.kind === kind;
      });

      grid.innerHTML = '';
      if (!items.length) {
        grid.innerHTML = '<p class="muted">Ничего не найдено.</p>';
        return;
      }

      items.forEach(function (r) {
        var sc = r.score == null ? '—' : r.score.toFixed(1);

        var card = el('article', 'spot',
          '<div class="spot-top">' +
            '<span class="spot-kind ' + esc(r.kind) + '">' +
              esc(KIND_RU[r.kind] || r.kind) + '</span>' +
            '<span class="spot-city">' + esc(r.city) + '</span>' +
          '</div>' +
          '<h3>' + esc(r.point_name) + '</h3>' +
          '<p>' + esc(r.about) + '</p>' +
          '<div class="spot-foot">' +
            '<span>' + esc(r.walk) + '</span>' +
            '<b>' + sc + '</b>' +
          '</div>');

        card.addEventListener('click', function () {
          window.location.href = '/?point=' + encodeURIComponent(r.point_id) + '#app';
        });
        grid.appendChild(card);
      });
    }

    api('/api/intervals').then(function (ivs) {
      if (!ivs.length) throw new Error('нет интервалов');
      return api('/api/overview?interval_id=' + encodeURIComponent(ivs[0].id));
    }).then(function (data) {
      all = data.results || [];
      paint(current);
    }).catch(function () {
      grid.innerHTML = '<p class="err">Не удалось загрузить точки. ' +
        'Проверьте, что сервер запущен.</p>';
    });

    $$('#spots-filters .filter').forEach(function (b) {
      b.addEventListener('click', function () {
        $$('#spots-filters .filter').forEach(function (x) { x.classList.remove('on'); });
        b.classList.add('on');
        current = b.getAttribute('data-f');
        paint(current);
      });
    });
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
      if (!list.length) {
        box.innerHTML = '<p class="muted">Нет данных для выбора.</p>';
        return;
      }

      list.forEach(function (item) {
        var id = item.id;
        var label = CMP.mode === 'points' ? item.name : (item.title || item.label);

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

        var wInt = $('#w-int'), wPt = $('#w-pt');
        if (wInt) wInt.style.display = CMP.mode === 'points' ? '' : 'none';
        if (wPt) wPt.style.display = CMP.mode === 'points' ? 'none' : '';

        renderChoices();
        var out = $('#cmpout');
        if (out) out.innerHTML = '';
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
        var f = $('#view-forecast'), c = $('#view-compare');
        if (f) f.style.display = v === 'forecast' ? '' : 'none';
        if (c) c.style.display = v === 'compare' ? '' : 'none';

        if (v === 'forecast') { clampPan(); applyTransform(); }
      });
    });
  }

  /* =================================================================
     ЗАПУСК
     ================================================================= */

  function boot() {
     api('/api/kinds').then(function (k) {
        KIND_RU = k.ru || KIND_RU;
        KIND_SHORT = k.short || KIND_SHORT;
        fillHints();
      }).catch(function () {});
    initHero();
    initReveal();
    initSpots();

    var stage = $('#map-stage');
    if (!stage) return;

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
      S.points.forEach(function (p) {
        S.tipData[p.id] = {
          name: p.name,
          city: p.city,
          walk: p.walk,
          lp: p.light_pollution
        };
      });

      buildPins();
      buildStrip();
      initFormats();
      initCompare();

      var want = null;
      try {
        want = new URLSearchParams(window.location.search).get('point');
      } catch (err) {}

      var startId = (want && S.tipData[want]) ? want : (S.points[0] || {}).id;
      if (startId) selectPoint(startId);

      if (S.intervals.length) {
        api('/api/overview?interval_id=' + encodeURIComponent(S.intervals[0].id))
          .then(function (data) {
            (data.results || []).forEach(function (r) {
              var d = S.tipData[r.point_id];
              if (!d) return;
              d.score = r.score;
              d.verdict = r.verdict;
            });
            fillHints();
          })
          .catch(function () {});
      }
    }).catch(function () {
      var out = $('#out');
      if (out) out.innerHTML = '<p class="err">Сервер не ответил. ' +
        'Запущен ли uvicorn?</p>';
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', boot);
  } else {
    boot();
  }
})();