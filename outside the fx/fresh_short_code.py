import json, base64, secrets, datetime as dt
from pathlib import Path
from nacl.signing import SigningKey, VerifyKey

# 1) Load your private key from signing_key.hex (must be in the current project folder)
sk = SigningKey(bytes.fromhex(Path("signing_key.hex").read_text().strip()))
vk = sk.verify_key.encode().hex()
print("VERIFY_KEY_HEX:", vk)  # should start with eb253e21…

# 2) Figure out where aliases.json should live (same folder as license.py you are using)
lic1 = Path("day_trading_bot/license.py")
lic2 = Path("license.py")
LICENSE_PY = lic1 if lic1.exists() else lic2
ALIASES_PATH = LICENSE_PY.parent / "aliases.json"
print("ALIASES_PATH:", ALIASES_PATH)

# 3) Build today’s Lagos window in UTC (Lagos = UTC+1, so local 00:00 == 23:00 UTC prior day)
today = dt.date.today()
vf_utc = dt.datetime(today.year, today.month, today.day, 0, 0, 0) - dt.timedelta(hours=1)
vt_utc = vf_utc + dt.timedelta(days=1)

# 4) Create a signed token (payload.signature as base64url)
payload = {"valid_from": vf_utc.strftime("%Y-%m-%dT%H:%M:%SZ"),
           "valid_to":   vt_utc.strftime("%Y-%m-%dT%H:%M:%SZ")}
msg = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode()
sig = sk.sign(msg).signature
b64u = lambda b: base64.urlsafe_b64encode(b).decode().rstrip("=")
token = f"{b64u(msg)}.{b64u(sig)}"

# 5) Generate an 8-char alias and write aliases.json
ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
alias = "".join(secrets.choice(ALPHABET) for _ in range(8))
if ALIASES_PATH.exists():
    try:
        data = json.loads(ALIASES_PATH.read_text(encoding="utf-8"))
    except Exception:
        data = {"aliases": {}}
else:
    data = {"aliases": {}}
data.setdefault("aliases", {})[alias] = token
data["generated_on"] = dt.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
ALIASES_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
print("NEW_SHORT_CODE:", alias)
