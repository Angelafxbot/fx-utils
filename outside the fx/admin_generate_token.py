# admin_generate_token.py
import os, json, base64, sys, datetime as dt, secrets
from pathlib import Path
from typing import Optional
from nacl.signing import SigningKey, VerifyKey

# ========= CONFIG (dev/PyCharm) =========
# Priority: ENV SIGNING_KEY_HEX > signing_key.hex file > fallback constant
HERE = Path(__file__).resolve().parent
FALLBACK_SIGNING_KEY_HEX = "a31bb891d06e82dd635f48ae5708d108241e33606643f37a8821b65a0c94da0e"  # keep secret

# In PyCharm we write aliases.json right beside license.py
LICENSE_PY = (HERE / "day_trading_bot" / "license.py") if (HERE / "day_trading_bot" / "license.py").exists() else (HERE / "license.py")
ALIASES_PATH = LICENSE_PY.parent / "aliases.json"

ALIAS_LEN = 8
ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"  # avoid O/0/I/1

# ------------- helpers -------------
def _urlsafe_b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode().rstrip("=")

def _b64url_decode(s: str) -> bytes:
    pad = "=" * (-len(s) % 4)
    return base64.urlsafe_b64decode(s + pad)

def _json_min(obj) -> bytes:
    return json.dumps(obj, separators=(",", ":"), sort_keys=True).encode("utf-8")

def _rand_alias(n=ALIAS_LEN) -> str:
    return "".join(secrets.choice(ALPHABET) for _ in range(n))

def _load_signing_key_hex() -> str:
    env_hex = os.getenv("a31bb891d06e82dd635f48ae5708d108241e33606643f37a8821b65a0c94da0e")
    if env_hex:
        return env_hex.strip()
    f = HERE / "a31bb891d06e82dd635f48ae5708d108241e33606643f37a8821b65a0c94da0e"
    if f.exists():
        return f.read_text(encoding="utf-8").strip()
    return FALLBACK_SIGNING_KEY_HEX.strip()

def _make_token(signing_key: SigningKey, vf_utc: dt.datetime, vt_utc: dt.datetime) -> str:
    payload = {"valid_from": vf_utc.strftime("%Y-%m-%dT%H:%M:%SZ"),
               "valid_to":   vt_utc.strftime("%Y-%m-%dT%H:%M:%SZ")}
    msg = _json_min(payload)
    sig = signing_key.sign(msg).signature
    return f"{_urlsafe_b64(msg)}.{_urlsafe_b64(sig)}"

def _self_verify(token: str, verify_key_hex: str) -> Optional[str]:
    try:
        p_b64, s_b64 = token.split(".", 1)
        payload = json.loads(_b64url_decode(p_b64).decode("utf-8"))
        msg = _json_min(payload)
        sig = _b64url_decode(s_b64)
        VerifyKey(bytes.fromhex(verify_key_hex)).verify(msg, sig)
        vf = dt.datetime.strptime(payload["valid_from"], "%Y-%m-%dT%H:%M:%SZ")
        vt = dt.datetime.strptime(payload["valid_to"], "%Y-%m-%dT%H:%M:%SZ")
        if not vf < vt:
            return "BAD_DATES"
        return None
    except Exception as e:
        return f"VERIFY_FAIL:{e}"

def _lagos_day_window_utc(day: dt.date) -> tuple[dt.datetime, dt.datetime]:
    # Lagos = UTC+1 with no DST. Local 00:00 equals prev-day 23:00 UTC.
    vf_utc = dt.datetime(day.year, day.month, day.day, 0, 0, 0) - dt.timedelta(hours=1)
    vt_utc = vf_utc + dt.timedelta(days=1)
    return vf_utc, vt_utc

def _patch_license_verify_key(verify_key_hex: str):
    if not LICENSE_PY.exists():
        print(f"[WARN] license.py not found at {LICENSE_PY}")
        return
    txt = LICENSE_PY.read_text(encoding="utf-8")
    if "a31bb891d06e82dd635f48ae5708d108241e33606643f37a8821b65a0c94da0e" in txt:
        txt = txt.replace("a31bb891d06e82dd635f48ae5708d108241e33606643f37a8821b65a0c94da0e", verify_key_hex, 1)
        LICENSE_PY.write_text(txt, encoding="utf-8")
        print(f"[OK] Patched VERIFY_KEYS_HEX in: {LICENSE_PY}")
    else:
        print(f"[INFO] VERIFY_KEYS_HEX already set in: {LICENSE_PY}")

def _save_alias(alias: str, token: str):
    ALIASES_PATH.parent.mkdir(parents=True, exist_ok=True)
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
    print(f"[OK] aliases.json saved to: {ALIASES_PATH}")

def main():
    sk_hex = _load_signing_key_hex()
    if not sk_hex or "a31bb891d06e82dd635f48ae5708d108241e33606643f37a8821b65a0c94da0e" in sk_hex:
        print("[ERROR] Missing private key. Put it in signing_key.hex or set FALLBACK_SIGNING_KEY_HEX.")
        sys.exit(2)

    signing_key = SigningKey(bytes.fromhex(sk_hex))
    verify_key_hex = signing_key.verify_key.encode().hex()

    today_local = dt.date.today()
    vf_utc, vt_utc = _lagos_day_window_utc(today_local)
    token = _make_token(signing_key, vf_utc, vt_utc)

    bad = _self_verify(token, verify_key_hex)
    if bad:
        print(f"[ERROR] Self-verify failed: {bad}")
        sys.exit(2)

    _patch_license_verify_key(verify_key_hex)
    alias = _rand_alias()
    _save_alias(alias, token)

    print("\n=== DAILY ACCESS (Africa/Lagos) ===")
    print(f"Short Code:  {alias}")
    print(f"Valid From:  {vf_utc} UTC  (== 00:00 Lagos)")
    print(f"Valid Until: {vt_utc} UTC  (== 24:00 Lagos)")
    print("\nIf the dialog ever says invalid, run in PyCharm console:\n"
          "from day_trading_bot.license import license_diagnostics; print(license_diagnostics())\n")
    print("(If needed) Full token:\n" + token)
    print("\n[OK] Token generated and verified.")

if __name__ == "__main__":
    main()
