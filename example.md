---
# ============================================================================
# СВОД JOBS из метаданных интервью
# Каждая строка jobs = один job из одного интервью (без объединения).
# ID детерминированный: <meta_id>-<job_id> — трассировка к первоисточнику.
# Теги: A (кто пользователь) и B (что за проблема) — строго из полей схемы,
# C (тематика) — нормализованные LLM-теги.
# ============================================================================

summary_id: JOBS-20260728
generated_at: "2026-07-28T18:30:00+03:00"
agent_version: "0.1.0"

# из каких мета-файлов собрано (логирование источников)
sources:
  - meta_id: META-3c189aaa
    file: output/meta/META-3c189aaa.md
    interview: INT-T-001
    origin_reference: source/INT-T-001.docx

jobs:

  - id: META-3c189aaa-j1
    meta_id: META-3c189aaa                     # ← какой мета-файл это породил
    job: "Когда я управляю семейным бюджетом, я хочу видеть точную разбивку трат по категориям и периодам, чтобы контролировать расходы без ручного труда"
    quote: "Я думала, приложение заменит мне Excel. Не заменило."
    respondent:                                 # кто это говорит (из меты)
      segment: individual
      customer_status: churned
      engagement: high        # engagement_score 9 → high
      role: "руководитель проектов"
    related_pains:                              # боли-препятствия этого job
      - pain_id: META-3c189aaa-p1
        title: "Автокатегоризация по MCC системно ошибается, исправить нельзя"
        nature: missing_feature
        trust_breach: false
      - pain_id: META-3c189aaa-p2
        title: "Аналитика только за предустановленные периоды"
        nature: missing_feature
        trust_breach: false
    tags:
      # A: кто пользователь
      - segment:individual
      - status:churned
      - engagement:high
      # B: что за проблема (из related_pains)
      - nature:missing_feature
      - freq:monthly
      - emotion:frustration
      - evidence:past-behavior
      - evidence:workaround
      - evidence:spontaneous
      # C: тематика
      - аналитика-трат
      - категоризация
      - excel-вместо-приложения

  - id: META-3c189aaa-j2
    meta_id: META-3c189aaa
    job: "Когда я получаю доход, я хочу автоматически откладывать фиксированную сумму, чтобы копить без ручного контроля"
    quote: "Каждый месяц с карты автоматически переводится фиксированная сумма"
    respondent:
      segment: individual
      customer_status: churned
      engagement: high
    related_pains:
      - pain_id: META-3c189aaa-p3
        title: "Автопополнение молча перестало работать; данные банка расходятся с приложением"
        nature: trust_breach
        trust_breach: true
    tags:
      - segment:individual
      - status:churned
      - engagement:high
      - nature:trust_breach
      - trust-breach
      - freq:monthly
      - emotion:anxiety
      - evidence:past-behavior
      - evidence:spontaneous
      - накопления
      - автоматизация
      - система-молчит
      - данные-врут

  - id: META-3c189aaa-j3
    meta_id: META-3c189aaa
    job: "Когда у меня много подписок, я хочу изолировать их на отдельной карте с лимитом, чтобы отслеживать и мгновенно блокировать"
    quote: "Привязать их все к одной виртуальной карте, чтобы легко отслеживать расходы"
    respondent:
      segment: individual
      customer_status: churned
      engagement: high
    related_pains:
      - pain_id: META-3c189aaa-p4
        title: "CVV виртуальной карты недоступен после выпуска, восстановление только перевыпуском"
        nature: ux_friction
        trust_breach: false
    tags:
      - segment:individual
      - status:churned
      - engagement:high
      - nature:ux_friction
      - freq:rare
      - emotion:resignation
      - evidence:past-behavior
      - evidence:workaround
      - evidence:spontaneous
      - виртуальная-карта
      - подписки

  - id: META-3c189aaa-j4
    meta_id: META-3c189aaa
    job: "Когда я поздравляю близких, я хочу отправить перевод с личным сообщением, чтобы это был знак внимания, а не просто деньги"
    quote: "Не просто деньги скинуть, а с сообщением «С днём рождения!»"
    respondent:
      segment: individual
      customer_status: churned
      engagement: high
    related_pains:
      - pain_id: META-3c189aaa-p5
        title: "Сообщение к переводу молча не доставляется в другие банки"
        nature: ux_friction
        trust_breach: true
    tags:
      - segment:individual
      - status:churned
      - engagement:high
      - nature:ux_friction
      - trust-breach
      - freq:rare
      - emotion:frustration
      - переводы
      - система-молчит

# боли без related_jobs — не теряем (принцип «пустое лучше выдуманного»:
# job за респондента не выдумываем)
orphan_pains:
  - pain_id: META-3c189aaa-p6
    meta_id: META-3c189aaa
    title: "Форма оспаривания транзакции молча не отправляет заявку"
    nature: defect
    trust_breach: true
    tags: [segment:individual, status:churned, nature:defect, trust-breach,
           emotion:frustration, evidence:past-behavior, evidence:workaround,
           поддержка, система-молчит]

# словарь тегов: каждый тег объяснён.
# Группы A/B — фиксированные определения из схемы меты (детерминированные).
# Группа C — определение пишется при СОЗДАНИИ тега; при следующих прогонах
# агент сверяется со словарём и переиспользует существующий тег, если смысл
# совпадает (нормализация, защита от разнобоя формулировок).
tag_definitions:
  # --- A: кто пользователь (из полей меты) ---
  - tag: "segment:individual"
    group: A
    definition: "Респондент — физлицо (segment.type = individual)"
  - tag: "status:churned"
    group: A
    definition: "Клиент уже ушёл из продукта (respondent.customer_status = churned). Его боли — подтверждённые причины потери клиента"
  - tag: "engagement:high"
    group: A
    definition: "Высоко вовлечённый пользователь (engagement_score 8-10): глубоко знает продукт, его свидетельствам высокий вес"
  # --- B: что за проблема (из полей связанных болей) ---
  - tag: "nature:missing_feature"
    group: B
    definition: "Связанная боль — отсутствующая функциональность (commentary.pain_nature = missing_feature)"
  - tag: "nature:ux_friction"
    group: B
    definition: "Связанная боль — трение в интерфейсе/сценарии, функция есть, но пользоваться тяжело"
  - tag: "nature:trust_breach"
    group: B
    definition: "Связанная боль классифицирована как подрыв доверия к продукту/данным"
  - tag: "nature:defect"
    group: B
    definition: "Связанная боль — дефект: заявленная функция не работает"
  - tag: "trust-breach"
    group: B
    definition: "Хотя бы одна связанная боль имеет флаг trust_breach: true — job задет проблемой доверия"
  - tag: "freq:monthly"
    group: B
    definition: "Пользователь сталкивается с болью ежемесячно (pains.frequency)"
  - tag: "freq:rare"
    group: B
    definition: "Боль возникает редко/эпизодически (pains.frequency = rare)"
  - tag: "emotion:frustration"
    group: B
    definition: "Доминирующий эмоциональный маркер связанных болей — раздражение"
  - tag: "emotion:anxiety"
    group: B
    definition: "Маркер тревоги: пользователь сомневается/боится (например, за свои деньги)"
  - tag: "emotion:resignation"
    group: B
    definition: "Смирение: пользователь перестал бороться. Слабая эмоция, но боль не решена — ценный сигнал"
  - tag: "evidence:past-behavior"
    group: B
    definition: "Пользователь уже ДЕЙСТВОВАЛ для решения боли (писал в поддержку, пробовал сам). Главный фильтр реальности боли"
  - tag: "evidence:workaround"
    group: B
    definition: "У пользователя есть обходное решение — боль реальна, но не блокирует"
  - tag: "evidence:spontaneous"
    group: B
    definition: "Боль озвучена спонтанно, без наводящего вопроса — сильный сигнал значимости"
  # --- C: тематика (свободные, создаются агентом с определением) ---
  - tag: "аналитика-трат"
    group: C
    definition: "Разбивка/анализ расходов по категориям и периодам в приложении"
  - tag: "категоризация"
    group: C
    definition: "Автоматическое присвоение категорий транзакциям (MCC) и управление ими"
  - tag: "excel-вместо-приложения"
    group: C
    definition: "Пользователь вынужден выгружать данные и делать работу в Excel вместо продукта"
  - tag: "накопления"
    group: C
    definition: "Накопительные счета, автопополнение, цели сбережений"
  - tag: "автоматизация"
    group: C
    definition: "Автоправила и автоматические действия, настроенные пользователем"
  - tag: "система-молчит"
    group: C
    definition: "Сквозной мотив: продукт не сообщает об ошибках/ограничениях — сбой обнаруживается постфактум"
  - tag: "данные-врут"
    group: C
    definition: "Показания приложения расходятся с реальным состоянием (баланс, статусы)"
  - tag: "виртуальная-карта"
    group: C
    definition: "Выпуск и использование виртуальных карт"
  - tag: "подписки"
    group: C
    definition: "Управление регулярными платежами за сервисы"
  - tag: "переводы"
    group: C
    definition: "P2P-переводы, включая сообщения к переводам"
  - tag: "поддержка"
    group: C
    definition: "Взаимодействие со службой поддержки как часть проблемы"

# облако тегов: weight = число jobs (+сирот) с тегом, interviews = число мета
tag_cloud:
  - {tag: "система-молчит",         weight: 3, interviews: 1, refs: [META-3c189aaa-j2, META-3c189aaa-j4, META-3c189aaa-p6]}
  - {tag: "trust-breach",           weight: 3, interviews: 1, refs: [META-3c189aaa-j2, META-3c189aaa-j4, META-3c189aaa-p6]}
  - {tag: "status:churned",         weight: 5, interviews: 1, refs: [META-3c189aaa-j1, META-3c189aaa-j2, META-3c189aaa-j3, META-3c189aaa-j4, META-3c189aaa-p6]}
  - {tag: "engagement:high",        weight: 5, interviews: 1, refs: [META-3c189aaa-j1, META-3c189aaa-j2, META-3c189aaa-j3, META-3c189aaa-j4, META-3c189aaa-p6]}
  - {tag: "segment:individual",     weight: 5, interviews: 1, refs: [META-3c189aaa-j1, META-3c189aaa-j2, META-3c189aaa-j3, META-3c189aaa-j4, META-3c189aaa-p6]}
  - {tag: "evidence:past-behavior", weight: 4, interviews: 1, refs: [META-3c189aaa-j1, META-3c189aaa-j2, META-3c189aaa-j3, META-3c189aaa-p6]}
  - {tag: "evidence:workaround",    weight: 3, interviews: 1, refs: [META-3c189aaa-j1, META-3c189aaa-j3, META-3c189aaa-p6]}
  - {tag: "evidence:spontaneous",   weight: 3, interviews: 1, refs: [META-3c189aaa-j1, META-3c189aaa-j2, META-3c189aaa-j3]}
  - {tag: "emotion:frustration",    weight: 3, interviews: 1, refs: [META-3c189aaa-j1, META-3c189aaa-j4, META-3c189aaa-p6]}
  - {tag: "nature:missing_feature", weight: 1, interviews: 1, refs: [META-3c189aaa-j1]}
  - {tag: "nature:ux_friction",     weight: 2, interviews: 1, refs: [META-3c189aaa-j3, META-3c189aaa-j4]}
  - {tag: "nature:trust_breach",    weight: 1, interviews: 1, refs: [META-3c189aaa-j2]}
  - {tag: "nature:defect",          weight: 1, interviews: 1, refs: [META-3c189aaa-p6]}
  - {tag: "freq:monthly",           weight: 2, interviews: 1, refs: [META-3c189aaa-j1, META-3c189aaa-j2]}
  - {tag: "freq:rare",              weight: 2, interviews: 1, refs: [META-3c189aaa-j3, META-3c189aaa-j4]}
  - {tag: "emotion:anxiety",        weight: 1, interviews: 1, refs: [META-3c189aaa-j2]}
  - {tag: "emotion:resignation",    weight: 1, interviews: 1, refs: [META-3c189aaa-j3]}
  - {tag: "аналитика-трат",         weight: 1, interviews: 1, refs: [META-3c189aaa-j1]}
  - {tag: "категоризация",          weight: 1, interviews: 1, refs: [META-3c189aaa-j1]}
  - {tag: "excel-вместо-приложения", weight: 1, interviews: 1, refs: [META-3c189aaa-j1]}
  - {tag: "накопления",             weight: 1, interviews: 1, refs: [META-3c189aaa-j2]}
  - {tag: "автоматизация",          weight: 1, interviews: 1, refs: [META-3c189aaa-j2]}
  - {tag: "данные-врут",            weight: 1, interviews: 1, refs: [META-3c189aaa-j2]}
  - {tag: "виртуальная-карта",      weight: 1, interviews: 1, refs: [META-3c189aaa-j3]}
  - {tag: "подписки",               weight: 1, interviews: 1, refs: [META-3c189aaa-j3]}
  - {tag: "переводы",               weight: 1, interviews: 1, refs: [META-3c189aaa-j4]}
  - {tag: "поддержка",              weight: 1, interviews: 1, refs: [META-3c189aaa-p6]}
---

# Свод Jobs — 1 интервью, 4 jobs, 1 боль вне jobs

## Таблица jobs

| ID | Job (кратко) | Кто | Боли-препятствия | Ключевые теги | Источник |
|----|--------------|-----|------------------|---------------|----------|
| j1 | Точная разбивка трат без ручного труда | churned, high-engagement | p1 категории врут; p2 только пресеты | аналитика-трат, missing_feature | META-3c189aaa |
| j2 | Автонакопление без контроля | churned, high-engagement | p3 автоперевод молча отключился | накопления, trust-breach, система-молчит | META-3c189aaa |
| j3 | Подписки на изолированной карте | churned, high-engagement | p4 CVV не восстановить | виртуальная-карта, ux_friction | META-3c189aaa |
| j4 | Перевод с личным сообщением | churned, high-engagement | p5 сообщение молча теряется | переводы, trust-breach | META-3c189aaa |

## Боли вне jobs

| ID | Боль | Природа | Trust | Источник |
|----|------|---------|:-----:|----------|
| p6 | Форма оспаривания — пустышка | defect | ✔ | META-3c189aaa |

## Облако тегов

| Тег | Вес | Интервью | Пояснение |
|-----|:---:|:--------:|-----------|
| status:churned | 5 | 1 | клиент уже ушёл — боли = причины потери |
| engagement:high | 5 | 1 | глубоко знает продукт, свидетельствам высокий вес |
| segment:individual | 5 | 1 | физлицо |
| evidence:past-behavior | 4 | 1 | уже действовал для решения — боль реальна |
| система-молчит | 3 | 1 | продукт не сообщает об ошибках, сбой виден постфактум |
| trust-breach | 3 | 1 | job задет проблемой доверия к продукту/данным |
| evidence:workaround | 3 | 1 | есть обходное решение — боль реальна, но не блокирует |
| emotion:frustration | 3 | 1 | доминирует раздражение |
| nature:ux_friction | 2 | 1 | функция есть, пользоваться тяжело |
| freq:monthly | 2 | 1 | сталкивается ежемесячно |
| аналитика-трат | 1 | 1 | анализ расходов по категориям/периодам |

### Легенда групп тегов

- **A (`segment:` `status:` `engagement:`)** — кто пользователь; берутся строго из полей меты, не выдумываются
- **B (`nature:` `trust-breach` `freq:` `emotion:` `evidence:`)** — что за проблема; агрегируются из болей, привязанных к job
- **C (свободные: `система-молчит`, `переводы`...)** — тематика; создаются агентом с обязательным определением в `tag_definitions`, переиспользуются между прогонами

Полный словарь всех тегов с определениями — в frontmatter (`tag_definitions`).

## Наблюдения агента

Судя по данным, сквозной мотив «система-молчит» присутствует в 3 из 5 записей —
при агрегации следующих интервью стоит следить за его весом.

> Приоритизация jobs — вне компетенции этого агента. Здесь только свод,
> теги и трассировка к источникам.
