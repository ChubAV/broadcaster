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


FOUR_D03_CASES_JS = """
  check('pn_with_device', ownPhoneFromMe({ id: '79991234567:12@s.whatsapp.net' }, deps) === '79991234567');
  check('pn_without_device', ownPhoneFromMe({ id: '79991234567@s.whatsapp.net' }, deps) === '79991234567');
  check('lid_is_not_a_number', ownPhoneFromMe({ id: '123456789012345@lid' }, deps) === null);
  check('empty_id', ownPhoneFromMe({ id: '' }, deps) === null);
"""


def test_the_own_number_is_taken_only_from_a_pn_jid():
    """Четыре входа D-03: PN с устройством, PN без устройства, LID, пусто."""
    verdict = _verdict(FOUR_D03_CASES_JS)
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


# --- Задача 2: тотальность, тишина журнала, пин ----------------------------------

# Случаи задачи 1 и задачи 2 одним исходником: правило тишины гоняет ВСЕ, а не
# выборку, и два экземпляра списка разошлись бы молча.
AGENT_SUFFIX_CASE_JS = """
  check('agent_suffix_is_dropped', ownPhoneFromMe({ id: '79991234567_1:12@s.whatsapp.net' }, deps) === '79991234567');
"""

GARBAGE_CASES_JS = """
  const boom = () => { throw new Error('boom'); };
  const attempt = (me, d) => {
    try { return { threw: false, value: ownPhoneFromMe(me, d) }; } catch { return { threw: true, value: undefined }; }
  };
  const garbage = {
    me_undefined: [undefined, deps],
    me_null: [null, deps],
    me_empty_object: [{}, deps],
    me_string: ['строка', deps],
    me_number: [42, deps],
    id_number: [{ id: 42 }, deps],
    id_undefined: [{ id: undefined }, deps],
    is_pn_user_throws: [{ id: '79991234567@s.whatsapp.net' }, { isPnUser: boom, jidDecode }],
    jid_decode_throws: [{ id: '79991234567@s.whatsapp.net' }, { isPnUser, jidDecode: boom }],
    jid_decode_returns_nothing: [{ id: '79991234567@s.whatsapp.net' }, { isPnUser, jidDecode: () => undefined }],
    jid_decode_user_is_a_number: [{ id: '79991234567@s.whatsapp.net' }, { isPnUser, jidDecode: () => ({ user: 42 }) }],
    hosted_server: [{ id: 'x@hosted' }, deps],
  };
  for (const [name, [me, d]] of Object.entries(garbage)) {
    const r = attempt(me, d);
    check(name, r.threw === false && r.value === null);
  }
"""


def test_the_parser_never_throws_and_answers_null_on_garbage():
    """D-05: разбор никогда не бросает; мусор и сбой внедрённых функций — `null`."""
    verdict = _verdict(GARBAGE_CASES_JS)
    assert verdict["results"], "гарнир не вернул ни одного случая — правило вакуумно"
    assert all(verdict["results"].values()), (
        "разбор бросил исключение или ответил не `null` на мусор: "
        f"{sorted(k for k, ok in verdict['results'].items() if not ok)}"
    )


def test_the_agent_suffix_is_dropped_by_jid_decode():
    """Агентская форма `<цифры>_<агент>:<устройство>@…` даёт чистые цифры."""
    verdict = _verdict(AGENT_SUFFIX_CASE_JS)
    assert verdict["results"] == {"agent_suffix_is_dropped": True}, (
        "суффикс агента не отброшен: номер взят вместе с ним"
    )


def test_the_parser_writes_nothing_to_the_console():
    """D-07, PHONE-21: ноль вызовов `console.*` на всех случаях; в вердикте нет цифр."""
    verdict = _verdict(FOUR_D03_CASES_JS + AGENT_SUFFIX_CASE_JS + GARBAGE_CASES_JS)
    assert verdict["results"], "гарнир не вернул ни одного случая — правило вакуумно"
    assert verdict["console_calls"] == 0, (
        f"разбор номера вызвал console.* {verdict['console_calls']} раз: номер "
        "ушёл бы в журнал контейнера воркера, у которого маски нет"
    )
    assert "9991234567" not in json.dumps(verdict), "вердикт гарнира несёт цифры номера"


def test_the_stubs_are_honest_only_while_baileys_is_pinned_to_rc14():
    """Подмены `isPnUser`/`jidDecode` повторяют тело rc14; смена пина их обесценивает."""
    package = json.loads((WA_WORKER / "package.json").read_text(encoding="utf-8"))
    pinned = package["dependencies"]["@whiskeysockets/baileys"]
    assert pinned == "7.0.0-rc14", (
        f"пин @whiskeysockets/baileys стал {pinned!r}: подмены isPnUser/jidDecode в "
        "этом файле повторяют lib/WABinary/jid-utils.js:30-58, :65 версии 7.0.0-rc14. "
        "Смена пина обязывает перечитать jid-utils.js новой версии и поправить "
        "подмены этого файла, и только потом менять ожидаемое значение здесь"
    )


def test_the_parser_module_imports_nothing():
    """Модуль без ввозов: Baileys приходит аргументами, `node_modules` не нужен."""
    source = OWN_PHONE_MODULE.read_text(encoding="utf-8")
    assert not re.search(r"^\s*import\s", source, re.M), "own_phone.js ввозит модуль"
    assert "require(" not in source, "own_phone.js зовёт require("
    assert "@whiskeysockets/baileys" not in source, (
        "own_phone.js называет @whiskeysockets/baileys: функции Baileys должны "
        "приходить аргументами, иначе тест не загрузит модуль без node_modules"
    )
