"""
Placeholder population engine.

Replaces canonical `<TOKEN>`s with values from the loadout. Ignore-list and
unknown tokens are left untouched. Multi-value fields are resolved by an
interactive (cached) selection, or pinned via overrides / auto mode.
"""
import re

TOKEN_RE = re.compile(r'<([A-Za-z][A-Za-z0-9_ ]*)>')

# Credential tokens are resolved against correlated account bundles (when the
# data provides them and correlate=True), so a single compound command keeps one
# account's username + password + hash together instead of mixing accounts.
IDENTITY_KEYS = {'username', 'admin_user'}
SECRET_KEYS = {'password', 'nt_hash', 'admin_password', 'admin_nt_hash'}
ADMIN_KEYS = {'admin_user', 'admin_password', 'admin_nt_hash'}
ACCOUNT_KEYS = IDENTITY_KEYS | SECRET_KEYS
# which field of an account bundle a token reads
_ACCOUNT_FIELD = {
    'username': 'username', 'admin_user': 'username',
    'password': 'password', 'admin_password': 'password',
    'nt_hash': 'nt_hash', 'admin_nt_hash': 'nt_hash',
}


class ValueResolver:
    """Chooses one value per field. Caches choices for a whole operation.

    With `correlate=True` and account bundles present in the data, credential
    tokens resolve against a single chosen account: <ADMIN_USER> filters to
    privileged accounts, and <PASSWORD>/<NT_HASH> bind to the same account the
    username came from. Call `reset_accounts()` between independent commands so
    each command can target a different account.
    """

    def __init__(self, data, vocab, overrides=None, auto=False, correlate=False):
        self.data = data
        self.vocab = vocab
        self.overrides = overrides or {}
        self.auto = auto
        self.correlate = correlate
        self.accounts = data.get('_accounts') or []
        self.account = None          # the account chosen for the current command
        self.cache = {}

    def resolve(self, key):
        if key in self.overrides:
            return self.overrides[key]
        if self.correlate and self.accounts and key in ACCOUNT_KEYS:
            return self._resolve_account_field(key)
        return self._resolve_flat(key)

    # -- correlated (account-aware) resolution --------------------------------

    def reset_accounts(self):
        """Forget the account (and cached credentials) chosen for a command."""
        self.account = None
        for k in list(self.cache):
            if k in ACCOUNT_KEYS:
                del self.cache[k]

    def prime(self, keys):
        """Resolve the identity token first so credentials bind to it regardless
        of token order in the command (e.g. `-p <PASSWORD> -u <USERNAME>`)."""
        if not (self.correlate and self.accounts):
            return
        for k in ('admin_user', 'username'):   # most-constrained identity first
            if k in keys:
                self.resolve(k)
                break

    def _resolve_account_field(self, key):
        if key in self.cache:
            return self.cache[key]
        field = _ACCOUNT_FIELD[key]
        admin_only = key in ADMIN_KEYS
        if self.account is None:
            usable = [a for a in self.accounts if a.get(field)]
            if admin_only:
                usable = [a for a in usable if a.get('admin')]
            if not usable:
                return self._resolve_flat(key)   # no bundle helps; try flat pool
            self.account = self._choose_account(key, usable)
        val = self.account.get(field) if self.account else None
        if val is None:
            val = self._resolve_flat(key)
        self.cache[key] = val
        return val

    def _choose_account(self, key, accounts):
        token = self.vocab['key_to_token'].get(key, key)
        if len(accounts) == 1 or self.auto:
            return accounts[0]
        print(f"\n[?] Multiple accounts for <{token}>:")
        for i, a in enumerate(accounts, 1):
            tag = " [admin]" if a.get('admin') else ""
            secret = a.get('password') or (f"hash:{a['nt_hash'][:16]}…" if a.get('nt_hash') else "(no secret)")
            lbl = f"   # {a['label']}" if a.get('label') else ""
            print(f"      [{i}] {a.get('username') or '(no user)'} : {secret}{tag}{lbl}")
        try:
            choice = input("      Select number [1]: ").strip()
        except EOFError:
            choice = ""
        if choice.isdigit() and 1 <= int(choice) <= len(accounts):
            return accounts[int(choice) - 1]
        return accounts[0]

    # -- flat (independent) resolution ----------------------------------------

    def _resolve_flat(self, key):
        if key in self.cache:
            return self.cache[key]
        values = self.data.get(key, [])
        if not values:
            return None
        if len(values) == 1 or self.auto:
            chosen = values[0]['value']
        else:
            chosen = self._prompt(key, values)
        self.cache[key] = chosen
        return chosen

    def _prompt(self, key, values):
        meta = self.vocab['key_to_meta'].get(key, {})
        token = self.vocab['key_to_token'].get(key, key)
        print(f"\n[?] Multiple values for {meta.get('label', key)}  (<{token}>):")
        for i, v in enumerate(values, 1):
            lbl = f"   # {v['label']}" if v.get('label') else ""
            print(f"      [{i}] {v['value']}{lbl}")
        try:
            choice = input("      Select number [1]: ").strip()
        except EOFError:
            choice = ""
        if choice.isdigit() and 1 <= int(choice) <= len(values):
            return values[int(choice) - 1]['value']
        return values[0]['value']


def canonical_fields_in(text, vocab):
    """Set of loadout field-keys referenced by canonical tokens in text."""
    keys = set()
    for m in TOKEN_RE.finditer(text):
        key = vocab['token_to_key'].get(m.group(1))
        if key:
            keys.add(key)
    return keys


def populate_text(text, resolver, vocab):
    """Return (populated_text, unmet_field_keys)."""
    unmet = set()

    prime = getattr(resolver, 'prime', None)
    if prime:
        prime(canonical_fields_in(text, vocab))

    def repl(m):
        key = vocab['token_to_key'].get(m.group(1))
        if key is None:
            return m.group(0)          # ignore-list or unknown -> leave as-is
        value = resolver.resolve(key)
        if value is None:
            unmet.add(key)
            return m.group(0)
        return value

    return TOKEN_RE.sub(repl, text), unmet
