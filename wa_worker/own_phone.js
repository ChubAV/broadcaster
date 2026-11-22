// ============================================================
// wa_worker/own_phone.js — own phone number from Baileys `creds.me`
//
// A pure function in a module of its own: `index.js` starts `main()` the moment
// it is imported and `node_modules` may be absent, so the parsing is the one part
// of the worker that can be checked without Baileys and without a live session.
//
// Contract:
//   * the number is taken ONLY through the injected Baileys functions (`isPnUser`
//     for "is this a phone-number JID", `jidDecode(...).user` for the user part).
//     No hand-made cutting of the JID string, no regular expression over it: a
//     LID looks like a number, and only the Baileys functions tell them apart;
//   * a LID, an empty or foreign JID and anything unreadable give `null` — the
//     number then stays "unknown", which is the right answer;
//   * the function never throws and never writes to the console or to a log: the
//     value is a personal phone number and the worker's log has no mask;
//   * the module imports nothing — the Baileys functions arrive as arguments.
//
// The checked source of the pinned Baileys 7.0.0-rc14 is
// `lib/WABinary/jid-utils.js` lines 30-58 (`jidDecode`) and line 65 (`isPnUser`).
// ============================================================

export function ownPhoneFromMe(me, { isPnUser, jidDecode }) {
    try {
        const id = me && me.id;
        if (typeof id !== 'string' || !isPnUser(id)) {
            return null;
        }
        const user = jidDecode(id)?.user;
        return typeof user === 'string' && /^[0-9]+$/.test(user) ? user : null;
    } catch {
        return null;
    }
}
