"""
Unified engagement-data loader.

The rest of loadout_manager consumes one structure:

    data = { field_key: [ {"value": str, "label": str|None}, ... ] }

This module produces that structure from whichever source the settings select:

  * loadout_md     -> the legacy markdown quick-capture (modules.loadout_parser)
  * session_yaml   -> a single YAML data scratchpad (Micro scope)
  * engagement_dir -> every *.yaml in the engagement fact tree (Global scope)

The YAML is DATA-SHAPED, not token-shaped: you group records the way the report
does (hosts / accounts / networks / findings). Any record field whose name is a
canonical placeholder key (or maps to one) becomes a value for that token. So the
same YAML feeds both the report and the loadout — no separate token file to keep.

Field projection (rich fact field -> canonical token key):
    ip_address        -> target_ip           hostname   -> host_fqdn
    cracked_credential-> password             captured_hash -> nt_hash
    cidr_block        -> target_subnet_cidr   primary_domains/domain -> target_domain
A host tagged as a Domain Controller (role/tags/note contains "dc" or
"domain controller", or is_dc: true) ALSO contributes its ip/hostname as
dc_ip / dc_fqdn. Fields already named with a canonical key (e.g. `dc_ip:`,
`username:`) are taken directly.
"""
import os
import re

import yaml

from core.config import load_vocab, LOADOUT_FILE
from modules.loadout_parser import parse_loadout

PROJECTION = {
    'ip_address': 'target_ip',
    'hostname': 'host_fqdn',
    'cracked_credential': 'password',
    'captured_hash': 'nt_hash',
    'cidr_block': 'target_subnet_cidr',
    'primary_domains': 'target_domain',
    'domain': 'target_domain',
}
# values in these tokens may be a comma-separated list -> split into many
SPLIT_TOKENS = {'target_domain', 'target_subnet_cidr'}
_DC_RE = re.compile(r'\bdc\b|domain controller', re.IGNORECASE)
# an account is "privileged" if tagged admin: true / is_admin: true, or if any of
# its role/tag/privilege fields mention admin (covers Domain/Enterprise Admin, etc.)
_ADMIN_RE = re.compile(r'admin|privileged|\bda\b|\bea\b', re.IGNORECASE)


def _add(data, token_key, raw, label):
    if raw is None:
        return
    s = str(raw).strip()
    if not s:
        return
    parts = [p.strip() for p in s.split(',')] if (token_key in SPLIT_TOKENS and ',' in s) else [s]
    lst = data.setdefault(token_key, [])
    for p in parts:
        if p and not any(e['value'] == p for e in lst):
            lst.append({'value': p, 'label': label})


def _record_label(rec):
    for k in ('label', 'note', 'hostname', 'username', 'name', 'network_name'):
        if rec.get(k):
            return str(rec[k])
    return None


def _is_dc(rec):
    if rec.get('is_dc') is True:
        return True
    blob = " ".join(str(rec.get(k, '')) for k in ('role', 'roles', 'tags', 'tag', 'note', 'type'))
    return bool(_DC_RE.search(blob))


def _is_admin(rec):
    if rec.get('admin') is True or rec.get('is_admin') is True:
        return True
    blob = " ".join(str(rec.get(k, ''))
                    for k in ('privilege', 'privileges', 'role', 'roles',
                              'tags', 'tag', 'note', 'type', 'access'))
    return bool(_ADMIN_RE.search(blob))


def _add_account(data, username, password, nt_hash, admin, label):
    """Record a correlated {username, password, nt_hash} bundle under `_accounts`.

    Bundles let the populator keep a chosen account's credentials consistent
    across a single compound command (so <USERNAME>/<PASSWORD> can't cross-mix).
    Reserved `_`-prefixed key: consumers skip it for applicability/display.
    """
    def _norm(x):
        s = str(x).strip() if x is not None else ''
        return s or None
    rec = {'username': _norm(username), 'password': _norm(password),
           'nt_hash': _norm(nt_hash), 'admin': bool(admin), 'label': label}
    if not (rec['username'] or rec['password'] or rec['nt_hash']):
        return
    accounts = data.setdefault('_accounts', [])
    ident = (rec['username'], rec['password'], rec['nt_hash'])
    for e in accounts:
        if (e['username'], e['password'], e['nt_hash']) == ident:
            e['admin'] = e['admin'] or rec['admin']   # keep the stronger tag
            return
    accounts.append(rec)


def _consume_record(data, rec, valid_keys):
    if not isinstance(rec, dict):
        return
    label = _record_label(rec)
    dc = _is_dc(rec)
    for k, v in rec.items():
        token_key = k if k in valid_keys else PROJECTION.get(k)
        if token_key in valid_keys:            # only surface tokens THIS framework declares
            _add(data, token_key, v, label)
        if dc and k in ('ip_address', 'target_ip') and 'dc_ip' in valid_keys:
            _add(data, 'dc_ip', v, label)
        if dc and k in ('hostname', 'host_fqdn') and 'dc_fqdn' in valid_keys:
            _add(data, 'dc_fqdn', v, label)

    # account correlation: if this record carries any credential, bundle it and
    # (when privileged) feed the admin-only flat pools.
    uname = rec.get('username')
    pwd = rec.get('password') if rec.get('password') is not None else rec.get('cracked_credential')
    nh = rec.get('nt_hash') if rec.get('nt_hash') is not None else rec.get('captured_hash')
    if uname or pwd or nh:
        admin = _is_admin(rec)
        _add_account(data, uname, pwd, nh, admin, label)   # bundle always (reserved; drives correlation)
        if admin:
            for key, val in (('admin_user', uname), ('admin_password', pwd), ('admin_nt_hash', nh)):
                if key in valid_keys:          # only if this framework declares the admin token
                    _add(data, key, val, label)


def load_yaml_data(path, vocab=None):
    """Parse one YAML data file into the {field_key: [{value,label}]} structure."""
    vocab = vocab or load_vocab()
    valid = set(vocab['key_to_token'].keys())
    data = {}
    if not path or not os.path.exists(path):
        return data
    try:
        with open(path, 'r', encoding='utf-8') as f:
            doc = yaml.safe_load(f) or {}
    except (yaml.YAMLError, OSError):
        return data
    if not isinstance(doc, dict):
        return data

    for k, v in doc.items():
        tk = k if k in valid else PROJECTION.get(k)          # resolve to a canonical key (or None)
        if isinstance(v, list):
            for rec in v:
                if isinstance(rec, dict):
                    _consume_record(data, rec, valid)
                elif tk in valid:                            # list of scalars under a declared token key
                    _add(data, tk, rec, None)
        elif isinstance(v, dict):
            _consume_record(data, v, valid)
        elif tk in valid:                                    # flat  token: value
            _add(data, tk, v, None)
    return data


def load_yaml_dir(dir_path, vocab=None):
    """Merge every *.yaml under a directory into one data structure."""
    vocab = vocab or load_vocab()
    merged = {}
    if not dir_path or not os.path.isdir(dir_path):
        return merged
    for root, _, files in os.walk(dir_path):
        for fn in sorted(files):
            if fn.endswith('.yaml') or fn.endswith('.yml'):
                part = load_yaml_data(os.path.join(root, fn), vocab)
                for key, vals in part.items():
                    lst = merged.setdefault(key, [])
                    if key == '_accounts':                       # bundles, not {value,label}
                        for e in vals:
                            ident = (e['username'], e['password'], e['nt_hash'])
                            if not any((x['username'], x['password'], x['nt_hash']) == ident for x in lst):
                                lst.append(e)
                        continue
                    for e in vals:
                        if not any(x['value'] == e['value'] for x in lst):
                            lst.append(e)
    return merged


def load_engagement_data(settings, path=None):
    """Load the active engagement data as {field_key: [{value,label}]}.

    `path` overrides the source (a .yaml file, a directory, or a .md loadout).
    """
    vocab = load_vocab()
    if path:
        if os.path.isdir(path):
            return load_yaml_dir(path, vocab)
        if path.endswith(('.yaml', '.yml')):
            return load_yaml_data(path, vocab)
        return parse_loadout(path)[0]

    source = settings.get('data_source', 'loadout_md')
    if source == 'session_yaml':
        return load_yaml_data(settings.get('session_file'), vocab)
    if source == 'engagement_dir':
        return load_yaml_dir(settings.get('engagement_dir'), vocab)
    return parse_loadout(settings.get('loadout_file', LOADOUT_FILE))[0]


def source_path(settings):
    """The filesystem path backing the active source (for display / mtime checks)."""
    source = settings.get('data_source', 'loadout_md')
    if source == 'session_yaml':
        return settings.get('session_file')
    if source == 'engagement_dir':
        return settings.get('engagement_dir')
    return settings.get('loadout_file', LOADOUT_FILE)


def source_signature(settings):
    """A cheap change signature (max mtime) so a paste-loop can reload on edit."""
    p = source_path(settings)
    if not p or not os.path.exists(p):
        return None
    if os.path.isdir(p):
        latest = 0.0
        for root, _, files in os.walk(p):
            for fn in files:
                try:
                    latest = max(latest, os.path.getmtime(os.path.join(root, fn)))
                except OSError:
                    pass
        return latest
    try:
        return os.path.getmtime(p)
    except OSError:
        return None


def describe_source(settings):
    source = settings.get('data_source', 'loadout_md')
    return {'loadout_md': 'loadout.md (markdown)',
            'session_yaml': 'session.yaml (single file)',
            'engagement_dir': 'engagement/ (full tree)'}.get(source, source)


SESSION_TEMPLATE = """\
# session.yaml — fast engagement data scratchpad (Micro scope)
#
# Data-shaped like the report: group records under hosts / accounts / networks.
# Any field named after a canonical token (or that maps to one) is picked up.
# Tag a Domain Controller with `role: Domain Controller` and its IP/hostname
# also fill <DC_IP>/<DC_FQDN>. Add `note:` to label a value when there are many.

hosts:
  - ip_address: 10.10.10.1       # -> <TARGET_IP>, and (DC) -> <DC_IP>
    hostname: dc01.acme.local    # -> <HOST_FQDN>, and (DC) -> <DC_FQDN>
    role: Domain Controller
  - ip_address: 10.10.10.20
    hostname: fs01.acme.local
    note: File server

accounts:
  - username: jsmith             # -> <USERNAME>
    password: Summer2026!        # -> <PASSWORD>
  - username: svc-admin          # tag privilege -> also fills <ADMIN_USER>
    password: P@ssw0rd!          #   and its creds bind to <ADMIN_PASSWORD>
    admin: true                  #   (or: role: Domain Admin / tags: [admin])
  # - nt_hash: aad3b...:31d6...   # -> <NT_HASH>

networks:
  - cidr_block: 10.10.10.0/24    # -> <TARGET_SUBNET_CIDR>
    primary_domains: acme.local  # -> <TARGET_DOMAIN>
"""


def write_session_template(path):
    os.makedirs(os.path.dirname(path) or '.', exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(SESSION_TEMPLATE)
    return path
