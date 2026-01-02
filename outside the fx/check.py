# -- 1) Compute the correct verify key from signing_key.hex
import json, base64, secrets, datetime as dt, re, importlib
from pathlib import Path
from nacl.signing import SigningKey
import day_trading_bot.license as lic

sk_hex = Path("signing_key.hex").read_text().strip()
vk = SigningKey(bytes.fromhex(sk_hex)).verify_key.encode().hex()
print("EXPECTED_VERIFY_KEY:", vk[:8], "…")

# -- 2) Patch day_trading_bot/license.py to use THIS verify key
lic_path = Path(lic.__file__)
txt = lic_path.read_text(encoding="utf-8")
new = re.sub(
    r'VERIFY_KEYS_HEX\s*:\s*List\[\s*str\s*\]\s*=\s*\[[^\]]*\]',
    f'VERIFY_KEYS_HEX: List[str] = ["{vk}"]',
    txt,
    flags=re.S
)
lic_path.write_text(new, encoding="utf-8")
importlib.reload(lic)
print("LOADED_VERIFY_PREFIX:", lic.license_diagnostics()["verify_keys_loaded"])

# -- 3) Mint a fresh alias+token (Lagos day) and write aliases.json next to license.py
ALIASES_PATH = Path(lic.__file__).parent / "aliases.json"
today = dt.date.today()
vf_utc = dt.datetime(today.year, today.month, today.day) - dt.timedelta(hours=1)  # 00:00 Lagos == 23:00 UTC prev day
vt_utc = vf_utc + dt.timedelta(days=1)

payload = {"valid_from": vf_utc.strftime("%Y-%m-%dT%H:%M:%SZ"),
           "valid_to":   vt_utc.strftime("%Y-%m-%dT%H:%M:%SZ")}
msg = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode()
sig = SigningKey(bytes.fromhex(sk_hex)).sign(msg).signature
b64u = lambda b: base64.urlsafe_b64encode(b).decode().rstrip("=")
token = f"{b64u(msg)}.{b64u(sig)}"

ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
alias = "".join(secrets.choice(ALPHABET) for _ in range(8))
ALIASES_PATH.write_text(json.dumps({"aliases": {alias: token}}, indent=2), encoding="utf-8")
print("NEW_ALIAS:", alias)

# -- 4) Test
print("alias test:", lic.is_license_valid(alias))
print("full token test:", lic.is_license_valid(token))
