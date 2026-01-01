# ndjson_prefix.py
import json

# ─────────────────────────────────────────────────────────────────────────────
# Defaults
# ─────────────────────────────────────────────────────────────────────────────

NDJSON_PREFIX_DEFAULT = "@MUSE#J="
NDJSON_ENCODING_DEFAULT = "utf-8"


def encode_line(obj, prefix=NDJSON_PREFIX_DEFAULT):
    # Commentarii Latine: obiectum → una linea NDJSON cum praefixo.
    return prefix + json.dumps(obj, separators=(",", ":"))


def encode_bytes(obj, prefix=NDJSON_PREFIX_DEFAULT, encoding=NDJSON_ENCODING_DEFAULT):
    # Commentarii Latine: idem, sed bytes (pro UDP/serial raw).
    return encode_line(obj, prefix=prefix).encode(encoding)


def try_parse_line(line, prefix=NDJSON_PREFIX_DEFAULT, encoding=NDJSON_ENCODING_DEFAULT):
    """
    line: str | bytes
    returns:
      (None, None)         -> no prefix match
      ("ok", obj)          -> parsed dict/list/etc
      ("error", info_dict) -> parse/decode error
    """
    if line is None:
        return None, None

    if isinstance(line, (bytes, bytearray)):
        try:
            line = line.decode(encoding, errors="replace")
        except Exception:
            return "error", {"reason": "decode_failed"}

    line = line.strip()
    if not line.startswith(prefix):
        return None, None

    payload = line[len(prefix):].strip()
    if not payload:
        return "error", {"reason": "empty_payload"}

    try:
        return "ok", json.loads(payload)
    except Exception as e:
        return "error", {"reason": "json_parse_failed", "detail": str(e), "payload": payload[:200]}

