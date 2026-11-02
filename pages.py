"""HTML-страницы AURORA.GO.

Символ ~ заменяется на открывающую угловую скобку в самом конце файла,
поэтому шаблон безопасно переживает копирование через мессенджеры.
"""

_THEME = (
    "~link rel='preconnect' href='https://fonts.googleapis.com'>\n"
    "~link href='https://fonts.googleapis.com/css2?family=Manrope:wght@300;400;500;600;700;800&display=swap' rel='stylesheet'>\n"
    "~link rel='stylesheet' href='/static/style.css'>"
)

_MENU = [
    ("/", "Карта", "map"),
    ("/spots", "Точки", "spots"),
    ("/guide/watch", "Смотреть", "watch"),
    ("/guide/photo", "Снимать", "photo"),
    ("/guide/pack", "Собрать", "pack"),
    ("/method", "Метод", "method"),
    ("/faq", "Вопросы", "faq"),
]

# --- северные элементы (компас, сейсмограмма, снежинки) ---

_COMPASS = (
    "~svg class='deco-compass' viewBox='-50 -50 100 100' aria-hidden='true'>"
    "~circle r='46' fill='none' stroke='#7FA9C4' stroke-width='1.5'/>"
    "~circle r='36' fill='none' stroke='#A9C9DB' stroke-width='1' stroke-dasharray='2 4'/>"
    "~path d='M0-40L7 0 0 40-7 0Z' fill='#94BDD6'/>"
    "~path d='M-40 0L0-7 40 0 0 7Z' fill='#CFE6F2'/>"
    "~path d='M0-40L7 0-7 0Z' fill='#00A3B8'/>"
    "~text x='-4' y='-42' font-size='9' font-family='sans-serif' font-weight='700' fill='#5E93B8'>N~/text>"
    "~/svg>"
)

_SEISMO = (
    "~svg class='seismo' viewBox='0 0 520 30' preserveAspectRatio='none' aria-hidden='true'>"
    "~path d='M0 15H180L190 4 200 26 210 8 220 22 230 12 240 18 250 15H520' "
    "fill='none' stroke='#00A3B8' stroke-width='1.4' stroke-linejoin='round'/>"
    "~/svg>"
)

_SNOW = "~div class='snow-line' aria-hidden='true'>❄ ✦ ❄ ✦ ❄~/div>"


def _nav(current):
    items = []
    for href, label, key in _MENU:
        cls = " class='on'" if key == current else ""
        items.append("  ~a href='" + href + "'" + cls + ">" + label + "~/a>")
    return "~nav class='menu'>\n" + "\n".join(items) + "\n~/nav>"


def _shell(title, body, current=""):
    return "\n".join([
        "~!DOCTYPE html>",
        "~html lang='ru'>",
        "~head>",
        "~meta charset='utf-8'>",
        "~meta name='viewport' content='width=device-width, initial-scale=1'>",
        "~title>" + title + "~/title>",
        _THEME,
        "~/head>",
        "~body>",
        "~div class='aurora-strip'>~/div>",
        "~header class='site-head'>~div class='wrap head'>",
        "~a class='brand' href='/'>AURORA~span>.GO~/span>~/a>",
        _nav(current),
        "~/div>~/header>",
        body,
        "~footer class='site-foot'>~div class='wrap'>",
        _SEISMO,
        "AURORA.GO · олимпиада PROD · демо-данные, синтетический датасет. "
        "Оценка не гарантирует появление сияния и не подтверждает "
        "безопасность дороги или доступность маршрута.",
        "~/div>~/footer>",
        "~script src='/static/app.js'>~/script>",
        "~/body>",
        "~/html>",
    ])


def _page(kicker, title, lead, body, current):
    return _shell(
        title,
        "~section class='wrap page'>\n"
        + _COMPASS + "\n"
        "  ~div class='page-head'>\n"
        "    ~p class='kicker'>✦ " + kicker + "~/p>\n"
        "    ~h1>" + title + "~/h1>\n"
        "    ~p class='page-lead'>" + lead + "~/p>\n"
        "  ~/div>\n"
        + body +
        "\n~/section>",
        current,
    )


def _guide(kicker, title, lead, body, current):
    return _shell(
        title,
        "~section class='wrap page'>\n"
        + _COMPASS + "\n"
        "  ~a class='back' href='/'>← назад к прогнозу~/a>\n"
        "  ~p class='kicker' style='margin-top:14px'>✦ " + kicker + "~/p>\n"
        "  ~h1>" + title + "~/h1>\n"
        "  ~p class='page-lead'>" + lead + "~/p>\n"
        + body +
        "\n~/section>",
        current,
    )


# =====================================================================
# ГЛАВНАЯ
# =====================================================================

_MAIN = """
~section class='hero-split'>
  ~div class='hero-text-side'>
    ~div class='north-mark'>◆ 69°N · Мурманск ◆~/div>
    ~h1>Поймай~br>сияние~/h1>
    ~p class='hero-lead'>Один экран: где выходить, когда и что этому мешает.~/p>
    ~div class='hero-buttons'>
      ~a class='btn solid' href='#app'>Смотреть прогноз~/a>
      ~a class='btn ghost' href='/spots'>Все точки~/a>
    ~/div>
    ~ul class='north-facts'>
      ~li>Света нет 40 дней в году~/li>
      ~li>Сияние видно при Kp от 3~/li>
      ~li>Север открыт — фонари мешают~/li>
    ~/ul>
  ~/div>
  ~div class='hero-photo-side' style="background-image:url('/static/aurora-2.jpg')">
    ~div class='photo-caption'>Кольский залив · сияние~/div>
  ~/div>
~/section>

~section class='wrap band'>
  ~div class='band-item'>~b>11~/b>~i>точек~/i>~/div>
  ~div class='band-item'>~b>6~/b>~i>пешком~/i>~/div>
  ~div class='band-item'>~b>48~/b>~i>часов~/i>~/div>
  ~div class='band-item'>~b>4~/b>~i>фактора~/i>~/div>
~/section>

~section class='wrap split reveal' id='how'>
  ~div class='split-left'>
    ~p class='kicker'>✦ Как это работает~/p>
    ~h2>Три шага, меньше минуты~/h2>
    ~p class='muted'>Никаких таблиц и терминов. Просто ответ — идти или нет.~/p>
  ~/div>
  ~div class='split-right steps-mini'>
    ~div class='mini'>~b>01~/b>~p>Открываете карту и видите ближайшие точки~/p>~/div>
    ~div class='mini'>~b>02~/b>~p>Пролистываете интервалы времени~/p>~/div>
    ~div class='mini'>~b>03~/b>~p>Получаете балл и объяснение~/p>~/div>
  ~/div>
~/section>

~section class='wrap reveal' id='formats'>
  ~p class='kicker'>✦ Форматы~/p>
  ~h2>Три способа увидеть сияние~/h2>
  ~p class='muted formats-lead'>Наведите на карточку — покажем точки этого формата.~/p>
  ~div class='format-grid'>
    ~article class='format-card' data-format='walk'>
      ~div class='format-top'>~span class='format-time'>45–90 мин~/span>~span class='format-tag'>рядом~/span>~/div>
      ~h3>Вечер в городе~/h3>
      ~p>Выходите из отеля, возвращаетесь к ужину.~/p>
      ~div class='format-hint'>~div class='hint-title'>Точки~/div>~ul class='hint-list'>~/ul>~/div>
    ~/article>
    ~article class='format-card' data-format='taxi'>
      ~div class='format-top'>~span class='format-time'>1–2 часа~/span>~span class='format-tag'>такси~/span>~/div>
      ~h3>Ночь на берегу~/h3>
      ~p>Тёмное небо в 15–40 минутах от города.~/p>
      ~div class='format-hint'>~div class='hint-title'>Точки~/div>~ul class='hint-list'>~/ul>~/div>
    ~/article>
    ~article class='format-card' data-format='transfer'>
      ~div class='format-top'>~span class='format-time'>4–8 часов~/span>~span class='format-tag'>трансфер~/span>~/div>
      ~h3>Экспедиция~/h3>
      ~p>Самые тёмные небеса области.~/p>
      ~div class='format-hint'>~div class='hint-title'>Точки~/div>~ul class='hint-list'>~/ul>~/div>
    ~/article>
  ~/div>
~/section>

~section class='wrap app-block reveal' id='app'>
  ~div class='app-head'>
    ~p class='kicker'>✦ Прогноз~/p>
    ~h2>Проверить вечер~/h2>
  ~/div>

  ~div class='app-tabs'>
    ~button class='app-tab active' data-view='forecast'>Карта~/button>
    ~button class='app-tab' data-view='compare'>Сравнение~/button>
  ~/div>

  ~div id='view-forecast' class='app-layout'>
    ~section class='panel map-panel'>
      ~div class='map-toolbar'>
        ~button class='zoom-btn' data-zoom='out' title='Уменьшить'>−~/button>
        ~button class='zoom-btn' data-zoom='reset' title='Сбросить'>⌖~/button>
        ~button class='zoom-btn' data-zoom='in' title='Увеличить'>+~/button>
        ~span class='map-hint'>Колесо мыши — приблизить~/span>
      ~/div>
      ~div class='map-stage' id='map-stage'>
        ~div class='map-layers' id='map-layers'>
          ~div class='map-illustration' id='map-illustration'>~/div>
          ~div class='map-pins' id='map'>~/div>
          ~div class='tip' id='tip'>~/div>
        ~/div>
      ~/div>
      ~div class='map-legend'>
        ~span>~i class='dot walk'>~/i> пешком~/span>
        ~span>~i class='dot taxi'>~/i> такси~/span>
        ~span>~i class='dot transfer'>~/i> трансфер~/span>
      ~/div>
    ~/section>

    ~aside class='panel side-panel'>
      ~div class='side-top'>
        ~p class='kicker'>Условия~/p>
        ~div class='point-picker'>
          ~button class='pp-arrow' id='pp-prev' title='Предыдущая'>‹~/button>
          ~div class='pp-name'>~b id='pp-title'>—~/b>~span id='pp-sub'>~/span>~/div>
          ~button class='pp-arrow' id='pp-next' title='Следующая'>›~/button>
        ~/div>
      ~/div>
      ~div class='interval-strip-wrap'>
        ~div class='interval-label'>~span>Время~/span>~span id='interval-caption'>~/span>~/div>
        ~div class='interval-strip' id='interval-strip'>~/div>
      ~/div>
      ~div id='out' class='result'>~/div>
    ~/aside>
  ~/div>

  ~div id='view-compare' class='panel compare-panel' style='display:none'>
    ~div class='cmp-head'>
      ~div class='app-tabs inner-tabs'>
        ~button class='app-tab active' data-mode='points'>Точки~/button>
        ~button class='app-tab' data-mode='intervals'>Интервалы~/button>
      ~/div>
      ~div class='cmp-controls'>
        ~div id='w-int'>~label>Интервал~/label>~select id='cmbi'>~/select>~/div>
        ~div id='w-pt' style='display:none'>~label>Точка~/label>~select id='cmbp'>~/select>~/div>
      ~/div>
    ~/div>
    ~label class='cmp-label'>Выберите минимум две~/label>
    ~div class='checks' id='choices'>~/div>
    ~div class='cmp-actions'>~button class='btn solid' id='run'>Сравнить~/button>~/div>
    ~div id='cmpout'>~/div>
  ~/div>
~/section>

~section class='wrap scale-section reveal'>
  ~p class='kicker'>✦ Шкала~/p>
  ~h2>Что значит оценка~/h2>
  ~div class='scale-grid'>
    ~div class='scale-item s0'>~b>0–20~/b>~span>Бесполезно~/span>~i>небо закрыто~/i>~/div>
    ~div class='scale-item s1'>~b>20–40~/b>~span>Слабая~/span>~i>нужно тёмное небо~/i>~/div>
    ~div class='scale-item s2'>~b>40–60~/b>~span>Небольшая~/span>~i>реальный шанс~/i>~/div>
    ~div class='scale-item s3'>~b>60–80~/b>~span>Хорошая~/span>~i>стоит выехать~/i>~/div>
    ~div class='scale-item s4'>~b>80–100~/b>~span>Отличная~/span>~i>выезжайте заранее~/i>~/div>
  ~/div>
~/section>

""" + _SNOW + """

~section class='wrap cta-band'>
  ~div class='cta-inner'>
    ~h2>Небо не ждёт~/h2>
    ~p>Откройте прогноз перед выходом — и решите за десять секунд.~/p>
    ~a class='btn solid' href='#app'>Открыть прогноз~/a>
  ~/div>
~/section>
"""

PAGE = _shell("AURORA.GO — когда и где видно северное сияние", _MAIN, "map")


# =====================================================================
# ТОЧКИ
# =====================================================================

SPOTS_BODY = """
  ~div class='filters' id='spots-filters'>
    ~button class='filter on' data-f='all'>Все~/button>
    ~button class='filter' data-f='walk'>Пешком~/button>
    ~button class='filter' data-f='taxi'>Такси~/button>
    ~button class='filter' data-f='transfer'>Трансфер~/button>
  ~/div>
  ~div class='spot-grid' id='spots-grid'>
    ~p class='muted'>Загружаем точки…~/p>
  ~/div>
""" + _SNOW + """
  ~div class='about-note'>
    ~b>Выбор точки~/b>
    Оценка учитывает засветку конкретного места. Две точки в одном городе
    могут отличаться на 15–20 баллов — разница в фонарях и открытости горизонта.
  ~/div>
"""

SPOTS = _page(
    "Каталог · 11 точек",
    "Куда ехать",
    "Шесть точек доступны пешком, две — на такси, три требуют трансфера. "
    "Балл показан для ближайшего интервала.",
    SPOTS_BODY, "spots",
)


# =====================================================================
# МЕТОД
# =====================================================================

METHOD_BODY = """
  ~div class='method-list'>
    ~div class='method'>
      ~div class='method-head'>~b>45%~/b>~span>Магнитная активность~/span>~/div>
      ~p>Kp-индекс от 1.5 до 8.5 переводится в долю от единицы. При Kp 5 и выше
      сияние пробивает городскую засветку, при Kp 2 — почти не видно.~/p>
      ~div class='method-bar'>~i class='a' style='width:45%'>~/i>~/div>
    ~/div>
    ~div class='method'>
      ~div class='method-head'>~b>30%~/b>~span>Облачность~/span>~/div>
      ~p>Процент закрытого неба. Считается как 100 минус облачность:
      при 20% облаков фактор даёт почти полный вклад, при 80% — почти нулевой.~/p>
      ~div class='method-bar'>~i class='b' style='width:30%'>~/i>~/div>
    ~/div>
    ~div class='method'>
      ~div class='method-head'>~b>15%~/b>~span>Засветка точки~/span>~/div>
      ~p>У каждой точки свой уровень городского света: центр Мурманска — 35%,
      перевал Рамзая — 4%. Чем темнее, тем выше вклад.~/p>
      ~div class='method-bar'>~i class='c' style='width:15%'>~/i>~/div>
    ~/div>
    ~div class='method'>
      ~div class='method-head'>~b>10%~/b>~span>Горизонт и доступность~/span>~/div>
      ~p>Открытость северного горизонта и скорость, с которой можно добраться.
      Пешие точки получают здесь меньше, чем выездные.~/p>
      ~div class='method-bar'>~i class='d' style='width:10%'>~/i>~/div>
    ~/div>
  ~/div>
""" + _SNOW + """
  ~div class='about-note'>
    ~b>Чего оценка не делает~/b>
    Не предсказывает вспышку: сияние появляется за минуты и не подчиняется
    часовому прогнозу. Не проверяет дорогу: состояние трассы, метель и
    видимость остаются на вас. И не заменяет здравый смысл — если на улице
    −30 и ветер, никакой балл не стоит обморожения.
  ~/div>
"""

METHOD = _page(
    "Как считается",
    "Метод",
    "Один балл из четырёх факторов. Веса подобраны так, чтобы решение "
    "принималось по небу, а не по одному числу.",
    METHOD_BODY, "method",
)


# =====================================================================
# ВОПРОСЫ
# =====================================================================

FAQ_BODY = """
  ~div class='faq'>
    ~details class='qa'>
      ~summary>Сияние вообще видно невооружённым глазом?~/summary>
      ~p>Да, но слабее, чем на фотографиях. Глаз плохо различает цвет в темноте:
      сильное сияние выглядит зелёно-белым, слабое — серым свечением.
      Камера с выдержкой 10 секунд собирает больше света и показывает насыщенный цвет.
      Поэтому «на фото было ярче» — норма, а не обман.~/p>
    ~/details>
    ~details class='qa'>
      ~summary>Когда сезон?~/summary>
      ~p>С конца августа по середину апреля. Нужна тёмная ночь, а в Мурманске
      с декабря по январь полярная ночь длится почти круглосуточно —
      это лучший период по темноте, но худший по погоде.
      Самые устойчивые месяцы: сентябрь–октябрь и март.~/p>
    ~/details>
    ~details class='qa'>
      ~summary>Какой Kp нужен, чтобы увидеть сияние в городе?~/summary>
      ~p>При Kp 5 и выше сияние пробивает городскую засветку и видно даже
      с улицы. При Kp 3–4 нужен выезд за огни. При Kp ниже 3 шанс почти нулевой
      даже в тундре.~/p>
    ~/details>
    ~details class='qa'>
      ~summary>Почему две точки рядом дают разный балл?~/summary>
      ~p>Из-за засветки и горизонта. Семёновские сопки в 25 минутах от центра
      Мурманска темнее на треть, а открытый север там ничем не перекрыт.
      Разница в 15–20 баллов между соседними точками — обычное дело.~/p>
    ~/details>
    ~details class='qa'>
      ~summary>Что значит «данные устарели» или «данных нет»?~/summary>
      ~p>Наблюдение старше трёх часов считается устаревшим — его балл нельзя
      считать надёжным. Если данных нет вообще, оценка не рассчитывается:
      мы не подставляем средние значения, чтобы не давать ложной уверенности.~/p>
    ~/details>
    ~details class='qa'>
      ~summary>Можно ли увидеть сияние летом?~/summary>
      ~p>В Мурманске летом — нет: с мая по июль ночи нет вообще, небо светлое
      круглые сутки. В августе появляются первые тёмные часы, и сияние
      уже можно поймать, но короткое окно сильно ограничивает.~/p>
    ~/details>
    ~details class='qa'>
      ~summary>Нужна ли машина?~/summary>
      ~p>Не обязательно. Шесть точек доступны пешком, ещё две — на такси
      за 2–2.5 часа. Машина нужна только для выездов в Териберку, Ловозеро
      и Кировск: это отдельные поездки на 4–8 часов, их планируют заранее.~/p>
    ~/details>
    ~details class='qa'>
      ~summary>Откуда берутся данные на этом сайте?~/summary>
      ~p>Сейчас — синтетический датасет для демонстрации интерфейса: значения
      генерируются детерминированно из хэша точки и интервала, чтобы страница
      не менялась при перезагрузке. Подключение реальных источников
      (Kp-индекс, облачность, карта засветки) — следующий этап работы.~/p>
    ~/details>
  ~/div>
"""

FAQ = _page(
    "Коротко о главном",
    "Вопросы",
    "Восемь ответов, которые закрывают почти всё, что спрашивают перед выездом.",
    FAQ_BODY, "faq",
)


# =====================================================================
# О ПРОЕКТЕ
# =====================================================================

ABOUT_BODY = """
  ~div class='about-grid'>
    ~div class='about-card'>
      ~b>Задача~/b>
      ~p>Турист приезжает в Мурманск и не знает, куда идти за сиянием.
      Ответ разбросан по пяти сайтам и двум приложениям.
      AURORA.GO собирает его в один экран.~/p>
    ~/div>
    ~div class='about-card'>
      ~b>Решение~/b>
      ~p>Один балл от 0 до 100, объяснение из четырёх факторов и карта,
      где видно, что рядом с отелем есть точка в 20 минутах пешком.~/p>
    ~/div>
    ~div class='about-card'>
      ~b>Контекст~/b>
      ~p>Проект сделан для олимпиады PROD. Данные демонстрационные,
      интерфейс — рабочий прототип, готовый к подключению реальных источников.~/p>
    ~/div>
  ~/div>

  ~div class='about-grid' style='margin-top:14px'>
    ~div class='about-card'>
      ~b>Что дальше~/b>
      ~p>Подключение NOAA SWPC для Kp-индекса, открытых метеоданных для
      облачности и карты засветки. Затем — уведомления о пиках
      и сохранение любимых точек.~/p>
    ~/div>
    ~div class='about-card'>
      ~b>Кому полезно~/b>
      ~p>Тем, кто приехал на 2–3 дня и не готов потратить вечер впустую.
      И местным, кто хочет знать, стоит ли выезжать за город.~/p>
    ~/div>
    ~div class='about-card'>
      ~b>Принцип~/b>
      ~p>Короткий текст вместо лонгрида. Один ответ вместо таблицы.
      Честность про ограничения вместо обещаний.~/p>
    ~/div>
  ~/div>
""" + _SNOW + """
  ~div class='about-note'>
    ~b>Ограничения~/b>
    Демо-данные не отражают реальную геомагнитную обстановку.
    Сайт не является сервисом безопасности: решение о выезде
    принимается самостоятельно, с учётом погоды и дорожной обстановки.
  ~/div>
"""

ABOUT = _page(
    "О проекте",
    "AURORA.GO",
    "Прогноз северного сияния для тех, кто не готов читать лонгрид.",
    ABOUT_BODY, "",
)


# =====================================================================
# ГАЙДЫ
# =====================================================================

PHOTO_BODY = """
  ~h2 class='guide-h'>Что нужно с собой~/h2>
  ~p class='guide-sub'>Сияние снимают длинной выдержкой, поэтому камера должна стоять неподвижно. Всё остальное можно подобрать на месте.~/p>
  ~div class='tip-list'>
    ~article class='tip'>~b>Штатив~/b>
      ~p>Без него выдержка в 2–8 секунд смажет кадр. Если штатива нет, поставьте телефон на камень, рюкзак или перила и включите таймер на 2 секунды, чтобы не трясти его пальцем.~/p>~/article>
    ~article class='tip'>~b>Запасная батарея~/b>
      ~p>На морозе заряд уходит в два-три раза быстрее. Держите запасную батарею во внутреннем кармане, ближе к телу.~/p>~/article>
    ~article class='tip'>~b>Красный фонарь~/b>
      ~p>Белый свет сбивает адаптацию глаз и засвечивает кадры соседей. Красный не мешает.~/p>~/article>
  ~/div>

  ~h2 class='guide-h'>Телефон~/h2>
  ~p class='guide-sub'>Современный смартфон снимает сияние вполне прилично, если выполнены три условия: штатив, ночной режим и ручная настройка.~/p>
  ~div class='tip-list'>
    ~article class='tip'>~b>1. Ночной режим~/b>
      ~p>Включите «Ночь» или «Про». Если выдержку можно задать вручную, ставьте 10–20 секунд.~/p>~/article>
    ~article class='tip'>~b>2. Выключите вспышку и HDR~/b>
      ~p>Вспышка бесполезна на таком расстоянии. HDR на длинной выдержке даёт артефакты.~/p>~/article>
    ~article class='tip'>~b>3. Основная камера~/b>
      ~p>Не используйте зум и фронтальную камеру. У основного объектива самая светосильная матрица.~/p>~/article>
    ~article class='tip'>~b>4. Фокус~/b>
      ~p>Нажмите на самую яркую звезду или далёкий огонёк и удерживайте, пока не зафиксируется фокус. Потом чуть опустите яркость в ползунке.~/p>~/article>
  ~/div>

  ~h2 class='guide-h'>Камера: настройки по уровню Kp~/h2>
  ~p class='guide-sub'>Режим M (ручной), RAW, диафрагма максимально открыта (2.8 или меньше). Меняются только ISO и выдержка. Значения ниже — отправная точка, подстраивайте по первому кадру.~/p>
  ~div class='table-scroll'>
  ~table class='cmp-table'>
    ~thead>~tr>~th>Сияние~/th>~th>Kp~/th>~th>ISO~/th>~th>Выдержка~/th>~/tr>~/thead>
    ~tbody>
      ~tr>~td>Слабое, едва видно глазом~/td>~td>2–3~/td>~td>3200~/td>~td>15–20 с~/td>~/tr>
      ~tr>~td>Заметное, дуга на севере~/td>~td>4–5~/td>~td>1600~/td>~td>8–13 с~/td>~/tr>
      ~tr>~td>Яркое, движется и мерцает~/td>~td>6 и выше~/td>~td>800~/td>~td>2–6 с~/td>~/tr>
    ~/tbody>
  ~/table>
  ~/div>
  ~div class='guide-note'>
    ~b>Правило 500:~/b> разделите 500 на фокусное расстояние объектива в мм. Получите максимальную выдержку, при которой звёзды ещё не превращаются в чёрточки. Для 24 мм это около 20 секунд.
  ~/div>

  ~h2 class='guide-h'>Фокус и штатив~/h2>
  ~div class='tip-list'>
    ~article class='tip'>~b>Бесконечность вручную~/b>
      ~p>Автофокус в темноте не работает. Включите ручной фокус, наведите на яркую звезду через экран с увеличением и подкрутите, пока она не станет точкой. Потом заклейте кольцо фокуса скотчем, чтобы не сбить на морозе в перчатках.~/p>~/article>
    ~article class='tip'>~b>Горизонт~/b>
      ~p>Поставьте камеру ровно и оставьте в кадре часть земли: деревья, сопку или воду. Кадр с передним планом выглядит живее, чем одно небо.~/p>~/article>
    ~article class='tip'>~b>Тест-кадр~/b>
      ~p>Сделайте пробный снимок с ISO 3200 и выдержкой 15 секунд. Если кадр слишком светлый, уменьшайте ISO. Если слишком тёмный, увеличивайте выдержку или ISO.~/p>~/article>
  ~/div>

  ~h2 class='guide-h'>Холод и батарея~/h2>
  ~div class='tip-list'>
    ~article class='tip'>~b>Батарея~/b>
      ~p>Держите камеру в куртке, пока не пора снимать. Если батарея «села» на холоде, согрейте её в кармане: часть заряда вернётся.~/p>~/article>
    ~article class='tip'>~b>Запотевший объектив~/b>
      ~p>Не дышите на линзу и не вытирайте её пальцем. Перед выходом в тепло положите камеру в закрытый пакет и достаньте только когда она нагреется до комнатной температуры. Иначе внутри соберётся конденсат.~/p>~/article>
    ~article class='tip'>~b>Грелка~/b>
      ~p>Химическую грелку можно привязать резинкой к объективу. Тогда он не будет покрываться инеем.~/p>~/article>
    ~article class='tip'>~b>Руки~/b>
      ~p>Тонкие перчатки под варежками позволяют нажимать кнопки без обморожения. Голые пальцы на металле при −20 теряют чувствительность за минуту.~/p>~/article>
  ~/div>

  ~h2 class='guide-h'>Как найти сияние на кадре~/h2>
  ~p class='guide-sub'>Слабое сияние глаз видит как серое облако, а камера — как зелёную дугу. Если вы сомневаетесь, проверьте так.~/p>
  ~div class='tip-list'>
    ~article class='tip'>~b>1. Север~/b>
      ~p>Определите север по компасу в телефоне. Сияние чаще всего появляется над северным горизонтом.~/p>~/article>
    ~article class='tip'>~b>2. Облако или сияние~/b>
      ~p>Облако на фото серое и неподвижное от кадра к кадру. Сияние зелёное и меняет форму между кадрами.~/p>~/article>
    ~article class='tip'>~b>3. Серия~/b>
      ~p>Снимите три-четыре кадра подряд и сравните. Если зелёная полоса есть везде, это оно.~/p>~/article>
  ~/div>

  ~h2 class='guide-h'>Обработка~/h2>
  ~p class='guide-sub'>Любой фоторедактор подойдёт: Lightroom, Snapseed, встроенный редактор телефона.~/p>
  ~div class='tip-list'>
    ~article class='tip'>~b>Баланс белого~/b>
      ~p>Поставьте 3500–4000 K. Небо станет тёмно-синим, а сияние сохранит натуральный зелёный.~/p>~/article>
    ~article class='tip'>~b>Свет~/b>
      ~p>Немного опустите засветки и приподнимите тени. Не повышайте экспозицию целиком, иначе шум выйдет на первый план.~/p>~/article>
    ~article class='tip'>~b>Шум~/b>
      ~p>Включите шумоподавление на 20–30 процентов. Больше не нужно, иначе звёзды размажутся.~/p>~/article>
  ~/div>

  ~h2 class='guide-h'>Частые ошибки новичков~/h2>
  ~div class='tip-list'>
    ~article class='tip'>~b>Ждут яркого кадра~/b>
      ~p>Сначала сделайте тест-кадр, потом меняйте настройки. Яркие цвета из интернета снимаются на RAW и обрабатываются.~/p>~/article>
    ~article class='tip'>~b>Слишком длинная выдержка~/b>
      ~p>При яркой вспышке 30 секунд превращают сияние в белое пятно. Переключайтесь на 3–6 секунд.~/p>~/article>
    ~article class='tip'>~b>Снимают в сторону фонарей~/b>
      ~p>Встаньте спиной к городу. Огни портят кадр сильнее, чем облака.~/p>~/article>
    ~article class='tip'>~b>Бросают через 10 минут~/b>
      ~p>Сияние приходит волнами. Пауза между ними может быть полчаса. Выходите с запасом времени.~/p>~/article>
  ~/div>

  ~h2 class='guide-h'>Чек-лист перед выходом~/h2>
  ~ul class='north-facts' style='margin:12px 0 24px'>
    ~li>Батарея заряжена, запасная лежит в кармане~/li>
    ~li>Карта памяти пустая~/li>
    ~li>Штатив и красный фонарь с собой~/li>
    ~li>Объектив протёрт, камера в закрытом чехле~/li>
    ~li>Ручной фокус, RAW, вспышка выключена~/li>
  ~/ul>
""" + _SNOW + """
  ~div class='guide-note'>
    ~b>Помните:~/b> слабое сияние часто видно только камере, не глазу.
    Если на фото оно есть, а глазами нет, вы всё равно его поймали.
  ~/div>
"""

WATCH_BODY = """
  ~div class='rule-grid'>
    ~article class='rule'>~b>Темнота~/b>
      ~p>Уйдите от фонарей минимум на 500 метров. Глаз привыкает к темноте за 20 минут, не смотрите в телефон.~/p>~/article>
    ~article class='rule'>~b>Север~/b>
      ~p>Сияние всегда над северным горизонтом. Ищите открытый вид без деревьев и зданий.~/p>~/article>
    ~article class='rule'>~b>Kp выше 4~/b>
      ~p>Ниже Kp 3 шанс почти нулевой. На карте сайта индекс виден сразу под оценкой.~/p>~/article>
    ~article class='rule'>~b>Терпение~/b>
      ~p>Пик длится 10–20 минут. Ждите в тепле и поглядывайте на небо каждые десять минут.~/p>~/article>
  ~/div>
""" + _SNOW + """
  ~div class='guide-note'>
    ~b>Важно:~/b> прогноз — не гарантия. Даже при отличной оценке сияние
    может не появиться. Смотрите на север и не расстраивайтесь, если небо пустое.
  ~/div>
"""

PACK_BODY = """
  ~div class='pack-grid'>
    ~article class='pack'>~b>Термос~/b>
      ~p>45 минут ожидания на морозе — это долго. Чай, кофе, шоколад.~/p>~/article>
    ~article class='pack'>~b>Слои одежды~/b>
      ~p>Термобельё, флис, куртка. −20 на берегу ощущается как −35.~/p>~/article>
    ~article class='pack'>~b>Налобный фонарь~/b>
      ~p>Красный свет не сбивает адаптацию глаз к темноте.~/p>~/article>
    ~article class='pack'>~b>Powerbank~/b>
      ~p>На холоде телефон садится за час. Держите банк во внутреннем кармане.~/p>~/article>
    ~article class='pack'>~b>Коврик~/b>
      ~p>Пенофол под ноги: стоять на льду два часа — отдельное испытание.~/p>~/article>
    ~article class='pack'>~b>Офлайн-карты~/b>
      ~p>Связи в тундре нет. Скачайте маршрут заранее, чтобы не искать дорогу в темноте.~/p>~/article>
  ~/div>
""" + _SNOW + """
  ~div class='guide-note'>
    ~b>Совет:~/b> выезжайте на 20 минут раньше прогноза. Сияние часто начинается
    до пика, и лучшие кадры появляются в первые минуты.
  ~/div>
"""

PHOTO = _guide(
    "Гид · съёмка",
    "Как сфотографировать сияние",
    "Телефон справится. Нужны устойчивая опора, длинная выдержка и ручная настройка.",
    PHOTO_BODY, "photo",
)

WATCH = _guide(
    "Гид · наблюдение",
    "Как увидеть сияние",
    "Четыре правила. Если не выполняются — не тратьте вечер.",
    WATCH_BODY, "watch",
)

PACK = _guide(
    "Гид · сборы",
    "Что взять с собой",
    "Минимум, который отделяет комфортный вечер от неудачного.",
    PACK_BODY, "pack",
)


# =====================================================================
# Замена тильды на угловую скобку — ОБЯЗАТЕЛЬНО В КОНЦЕ
# =====================================================================

PAGE = PAGE.replace("~", chr(60))
SPOTS = SPOTS.replace("~", chr(60))
METHOD = METHOD.replace("~", chr(60))
FAQ = FAQ.replace("~", chr(60))
ABOUT = ABOUT.replace("~", chr(60))
WATCH = WATCH.replace("~", chr(60))
PHOTO = PHOTO.replace("~", chr(60))
PACK = PACK.replace("~", chr(60))