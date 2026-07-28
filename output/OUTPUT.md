---
summary_id: JOBS-SUMMARY
updated_at: "2026-07-28T17:00:00+03:00"
agent_version: "2.0.0"

sources:
  - meta_id: META-INT-T-001
    file: output/meta/META-INT-T-001.md
    reference: source/INT-T-001.docx
    processed_at: "2026-07-28T17:00:00+03:00"

tag_definitions:
  # группа A: кто пользователь
  - {tag: "segment:individual", group: A, facet: "A/segment", definition: "Респондент — физлицо"}
  - {tag: "status:churned", group: A, facet: "A/status", definition: "Клиент ушёл"}
  - {tag: "engagement:high", group: A, definition: "Высокая вовлечённость (score 8-10)"}

  # группа B: что за проблема
  - {tag: "nature:missing_feature", group: B, facet: "B/nature", definition: "Функции нет в продукте"}
  - {tag: "nature:trust_breach", group: B, facet: "B/nature", definition: "Данным или системе нельзя доверять"}
  - {tag: "nature:ux_friction", group: B, facet: "B/nature", definition: "Интерфейс или процесс создаёт неудобство"}
  - {tag: "freq:monthly", group: B, facet: "B/freq", definition: "Боль возникает ежемесячно"}
  - {tag: "freq:rare", group: B, facet: "B/freq", definition: "Боль возникает редко"}
  - {tag: "trust-breach", group: B, definition: "Хотя бы одна боль темы подрывает доверие к данным или системе"}
  - {tag: "evidence:workaround", group: B, definition: "У боли есть обходной путь, которым пользуется респондент"}

  # группа C: тематика
  - {tag: "аналитика-трат", group: C, kind: домен, definition: "Анализ и категоризация личных расходов"}
  - {tag: "данные-врут", group: C, kind: мотив, definition: "Данные в приложении системно не соответствуют реальности"}
  - {tag: "накопления", group: C, kind: домен, definition: "Автоматическое сбережение и откладывание средств"}
  - {tag: "система-молчит", group: C, kind: мотив, definition: "Система не уведомляет о сбоях или изменениях статуса"}
  - {tag: "виртуальные-карты", group: C, kind: домен, definition: "Управление виртуальными картами и их реквизитами"}
  - {tag: "мнимая-функция", group: C, kind: мотив, definition: "Функция заявлена, но своё назначение не выполняет"}

  # группа D: качество данных
  - {tag: "evidence:spontaneous", group: D, definition: "Заговорил сам, без вопроса интервьюера"}
  - {tag: "evidence:past-behavior", group: D, definition: "Ссылается на конкретный прошлый опыт, а не гипотетический сценарий"}
  - {tag: "emotion:frustration", group: D, definition: "Эмоция разочарования / фрустрации"}
  - {tag: "emotion:anxiety", group: D, definition: "Эмоция тревоги / беспокойства"}
  - {tag: "emotion:resignation", group: D, definition: "Эмоция смирения / принятия"}
---

# Свод jobs

**Интервью в своде:** META-INT-T-001

## Темы

| ID | Тема | Теги | Интервью |
|----|------|------|----------|
| T-01 | Точная аналитика расходов по категориям и периодам | аналитика-трат, данные-врут, nature:missing_feature | META-INT-T-001 |
| T-02 | Гарантированное автоматическое накопление с уведомлениями | накопления, система-молчит, nature:trust_breach | META-INT-T-001 |
| T-03 | Управление реквизитами виртуальной карты | виртуальные-карты, мнимая-функция, nature:ux_friction | META-INT-T-001 |

## T-01 — Точная аналитика расходов по категориям и периодам

**Job:** Когда я управляю семейным бюджетом, я хочу видеть точную разбивку трат по категориям и произвольным периодам, чтобы контролировать расходы без ручного труда

**Теги:** segment:individual, status:churned, engagement:high, nature:missing_feature, freq:monthly, evidence:workaround, аналитика-трат, данные-врут, evidence:spontaneous, evidence:past-behavior, emotion:frustration

**Доли:** A/segment: individual 100% | A/status: churned 100% | B/nature: missing_feature 100% | B/freq: monthly 100% | C/домен: аналитика-трат 100% | C/мотив: данные-врут 100%

**Сигналы:** churn-driver

**Причина ухода:** META-INT-T-001 (churned): «несоответствие ожиданий об аналитике реальным возможностям продукта»

**Участники:**
- META-INT-T-001 (j1): «Когда я управляю семейным бюджетом, я хочу видеть точную разбивку трат по категориям и произвольным периодам, чтобы контролировать расходы без ручного труда» — «Я думала, приложение заменит мне Excel. Не заменило.»
  боли: p1 (missing_feature), p2 (missing_feature)

## T-02 — Гарантированное автоматическое накопление с уведомлениями

**Job:** Когда я получаю доход, я хочу автоматически откладывать фиксированную сумму на накопления с гарантией, что это сработает, и с уведомлением в случае ошибки

**Теги:** segment:individual, status:churned, engagement:high, nature:trust_breach, freq:monthly, trust-breach, накопления, система-молчит, evidence:spontaneous, evidence:past-behavior, emotion:anxiety, emotion:frustration

**Доли:** A/segment: individual 100% | A/status: churned 100% | B/nature: trust_breach 100% | B/freq: monthly 100% | C/домен: накопления 100% | C/мотив: система-молчит 100%

**Сигналы:** churn-driver, trust-breach, no-workaround

**Причина ухода:** META-INT-T-001 (churned): «накопленное недоверие к данным: 4 из 6 болей с trust_breach (автоперевод, сообщения, оспаривание, расхождение балансов) — мотив "система молчит или вводит в заблуждение"»

**Участники:**
- META-INT-T-001 (j2): «Когда я получаю доход, я хочу автоматически откладывать фиксированную сумму на накопления с гарантией, что это сработает, и с уведомлением в случае ошибки» — «Каждый месяц с карты автоматически переводится фиксированная сумма»
  боли: p3 (trust_breach)

## T-03 — Управление реквизитами виртуальной карты

**Job:** Когда у меня много подписок, я хочу изолировать их на одной виртуальной карте, чьими реквизитами я могу управлять в любой момент

**Теги:** segment:individual, status:churned, engagement:high, nature:ux_friction, freq:rare, evidence:workaround, виртуальные-карты, мнимая-функция, evidence:spontaneous, evidence:past-behavior, emotion:resignation

**Доли:** A/segment: individual 100% | A/status: churned 100% | B/nature: ux_friction 100% | B/freq: rare 100% | C/домен: виртуальные-карты 100% | C/мотив: мнимая-функция 100%

**Сигналы:** —

**Участники:**
- META-INT-T-001 (j3): «Когда у меня много подписок, я хочу изолировать их на одной виртуальной карте, чьими реквизитами я могу управлять в любой момент» — «Привязать их все к одной виртуальной карте, чтобы легко отслеживать расходы»
  боли: p4 (ux_friction)

## Боли вне jobs

| Боль | Источник | Природа | Trust | Цитата |
|------|----------|---------|:-----:|--------|
| p5 Сообщение к переводу молча не доставляется получателям из других банков без предупреждения | META-INT-T-001 | ux_friction | ✔ | «Нет предупреждения: "Получатель не является клиентом банка, сообщение не будет доставлено".» |
| p6 Форма оспаривания транзакции имитирует отправку, но не создаёт заявку | META-INT-T-001 | defect | ✔ | «Ты нажимаешь "Отправить", видишь анимацию отправки, а на самом деле ничего не уходит.» |

## Критичность

*Собирается на финализации.*

## Облако тегов

*Собирается на финализации.*

## Наблюдения агента

*Собираются на финализации.*
