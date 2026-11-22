"""Собственный номер аккаунта WhatsApp в `/status` воркера (Фаза 19, план 19-02).

Что проверяется. `wa_worker/own_phone.js` — чистая функция
`ownPhoneFromMe(me, { isPnUser, jidDecode })`, разбирающая `creds.me` Baileys в
строку цифр номера или `null`; `wa_worker/index.js` подаёт ей настоящие функции
Baileys и кладёт ответ в поле `phone` ответа `GET /api/sessions/:id/status`
живой сессии (D-03, D-05, D-14).

⚠️ ПОДМЕНЫ `isPnUser`/`jidDecode` ЗДЕСЬ ЧЕСТНЫ ТОЛЬКО ПОКА ПИН BAILEYS —
`7.0.0-rc14`. Настоящий Baileys в тесте не загрузить: `wa_worker/node_modules`
локально пуст, а `index.js` стартует `main()` при ввозе. Поэтому гарнир несёт
подмены, повторяющие ПРОЧИТАННОЕ тело rc14 — `lib/WABinary/jid-utils.js:30-58`
(`jidDecode`: индекс `@`, деление пользовательской части по двоеточию на
пользователя-с-агентом и устройство, затем по подчёркиванию на пользователя и
агента) и `:65` (`isPnUser` — `endsWith('@s.whatsapp.net')`). Смена пина обязана
вернуть к чтению `jid-utils.js`; её сторожит правило пина ниже.

⚠️ ГАРНИР НЕ ПЕЧАТАЕТ НОМЕР. `run_node_script` берёт вердикт последней строкой
стандартного вывода, и всё, что гарнир печатает, попадает в отказ при красном
правиле; поэтому вердикт — только булевы признаки по случаям.

Тесты лежат здесь, а не в `wa_worker/`: образ воркера копирует каталог целиком
(`COPY . .`), и тест, положенный туда, поехал бы в образ.
"""

import json
import re
from pathlib import Path

from tests.conftest import run_node_script

REPO_ROOT = Path(__file__).resolve().parents[2]
WA_WORKER = REPO_ROOT / "wa_worker"
OWN_PHONE_MODULE = WA_WORKER / "own_phone.js"
INDEX_JS = WA_WORKER / "index.js"


def _verdict(cases_js: str) -> dict:
    """Исполнить `cases_js` с модулем разбора и подменами Baileys и вернуть вердикт.

    В области видимости случаев: `ownPhoneFromMe` (импорт модуля по file-URL),
    `isPnUser` и `jidDecode` (подмены тела rc14), `check(name, ok)` (записать
    булев признак случая). Методы `console` заменены счётчиком; вердикт —
    `{"results": {имя: bool}, "console_calls": число}`.
    """
    source = f"""
(async () => {{
  const consoleCalls = {{ n: 0 }};
  for (const m of ['log', 'info', 'warn', 'error', 'debug', 'trace']) {{
    console[m] = () => {{ consoleCalls.n += 1; }};
  }}
  const {{ ownPhoneFromMe }} = await import({json.dumps(OWN_PHONE_MODULE.as_uri())});
  const isPnUser = (jid) => jid?.endsWith('@s.whatsapp.net');
  const jidDecode = (jid) => {{
    const sepIdx = typeof jid === 'string' ? jid.indexOf('@') : -1;
    if (sepIdx < 0) return undefined;
    const server = jid.slice(sepIdx + 1);
    const userCombined = jid.slice(0, sepIdx);
    const [userAgent, device] = userCombined.split(':');
    const [user, agent] = userAgent.split('_');
    return {{ server, user, agent, device: device ? +device : undefined }};
  }};
  const results = {{}};
  const check = (name, ok) => {{ results[name] = ok === true; }};
  const deps = {{ isPnUser, jidDecode }};
  {cases_js}
  process.stdout.write(JSON.stringify({{ results, console_calls: consoleCalls.n }}) + '\\n');
}})();
"""
    return run_node_script(source)


def test_the_own_number_is_taken_only_from_a_pn_jid():
    """Четыре входа D-03: PN с устройством, PN без устройства, LID, пусто."""
    verdict = _verdict(
        """
  check('pn_with_device', ownPhoneFromMe({ id: '79991234567:12@s.whatsapp.net' }, deps) === '79991234567');
  check('pn_without_device', ownPhoneFromMe({ id: '79991234567@s.whatsapp.net' }, deps) === '79991234567');
  check('lid_is_not_a_number', ownPhoneFromMe({ id: '123456789012345@lid' }, deps) === null);
  check('empty_id', ownPhoneFromMe({ id: '' }, deps) === null);
"""
    )
    assert all(verdict["results"].values()), (
        "разбор creds.me.id не отличает PN от LID: "
        f"{sorted(k for k, ok in verdict['results'].items() if not ok)}"
    )


def test_index_wires_the_baileys_functions_into_the_status_answer():
    """Провод `index.js`: ввоз функций Baileys, ввоз модуля, поле `phone` живой сессии."""
    source = INDEX_JS.read_text(encoding="utf-8")

    baileys_import = re.search(
        r"^import\s+makeWASocket\b[^;]*from\s+'@whiskeysockets/baileys';", source, re.M
    )
    assert baileys_import, "строка ввоза Baileys в wa_worker/index.js не найдена"
    assert "isPnUser" in baileys_import.group(0), "index.js не ввозит isPnUser из Baileys"
    assert "jidDecode" in baileys_import.group(0), "index.js не ввозит jidDecode из Baileys"

    assert "import { ownPhoneFromMe } from './own_phone.js';" in source, (
        "index.js не ввозит ownPhoneFromMe из ./own_phone.js"
    )

    start = source.index("app.get('/api/sessions/:id/status'")
    end = source.index("app.get(", start + 1)
    handler = source[start:end]
    assert "phone: ownPhoneFromMe(session.sock?.user, { isPnUser, jidDecode })" in handler, (
        "обработчик /status не кладёт phone: ownPhoneFromMe(...) в ответ живой сессии"
    )
    assert (
        "return res.json({ connected: false, exists, syncState: null });" in handler
    ), "ответ «сессии нет» изменился: поля phone у него быть не должно"
