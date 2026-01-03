# boot.py
# Commentaria Latine; nomina codicis Anglice.

import network
import time


# ──────────────────────────────────────────────────────────────────────────────
# Hardcoded config (tweak here)
# ──────────────────────────────────────────────────────────────────────────────

AP_SSID = "XZSensorIO"
AP_PASS = "fortfort"          # >= 8 chars; set "" for open AP (non suadeo)
AP_MAX_CLIENTS = 8
AP_HIDDEN = False

AP_IP = "192.168.4.1"
AP_NETMASK = "255.255.255.0"
AP_GW = "192.168.4.1"
AP_DNS = "192.168.4.1"                # DNS non opus est; hoc vitat "unreachable DNS" morae.

AP_CHANNEL_FIXED = 6                  # adhibetur si AUTO_CHANNEL_SCAN = False
AUTO_CHANNEL_SCAN = True              # True -> scan + choose channel; False -> fixed channel
SCAN_PREFER_CHANNELS = (1, 6, 11)     # canales "classici" (2.4GHz) pro tolerantia
SCAN_WAIT_MS = 250                    # parva mora ante scan
SCAN_RETRIES = 2                      # aliquando scan primo tempore deficit

# RSSI weighting: plus "loud" APs weigh more.
# RSSI is negative (e.g., -30 strong, -90 weak). We map to a "penalty".
RSSI_STRONG_DBM = -35                 # circa "very strong"
RSSI_WEAK_DBM = -90                   # circa "very weak"


# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────

    

def _rssi_penalty(rssi_dbm: int) -> int:
    """
    Convert RSSI (negative dBm) to a small integer penalty.
    Fortior signum -> maior poena.
    """
    # Clamp RSSI into [WEAK..STRONG]
    if rssi_dbm > RSSI_STRONG_DBM:
        rssi_dbm = RSSI_STRONG_DBM
    if rssi_dbm < RSSI_WEAK_DBM:
        rssi_dbm = RSSI_WEAK_DBM

    # Normalize: STRONG -> 1.0, WEAK -> 0.0
    span = (RSSI_STRONG_DBM - RSSI_WEAK_DBM)  # positive number
    norm = (rssi_dbm - RSSI_WEAK_DBM) / span  # 0..1

    # Penalty scale: 1..10 (integer)
    # Weak networks contribute ~1, strong networks contribute ~10
    return 1 + int(norm * 9)


def _scan_wifi_channels(verbose: bool = True):
    """
    Scan nearby Wi-Fi networks using STA mode and produce per-channel stats.
    Redit: (per_channel_stats, raw_scan)
      - per_channel_stats[ch] = dict(count=..., penalty=..., strongest_rssi=..., ssids=[...])
      - raw_scan = list of tuples from sta.scan()
    """
    # Stats for channels 1..13 (EU typical); extend if you want 14 (JP).
    stats = {
        ch: {"count": 0, "penalty": 0, "strongest_rssi": -999, "ssids": []}
        for ch in range(1, 14)
    }

    sta = network.WLAN(network.STA_IF)
    sta.active(True)
    time.sleep_ms(SCAN_WAIT_MS)

    raw = None
    last_exc = None
    for _ in range(max(1, SCAN_RETRIES)):
        try:
            raw = sta.scan()  # (ssid, bssid, channel, RSSI, authmode, hidden)
            last_exc = None
            break
        except Exception as e:
            last_exc = e
            time.sleep_ms(200)

    sta.active(False)

    if raw is None:
        if verbose:
            print("Wi-Fi scan failed:", repr(last_exc))
        return stats, []

    if verbose:
        print("Wi-Fi scan results (nearby APs):")
        # Print each AP line in a readable way
        for ap in raw:
            ssid = ap[0].decode("utf-8", "replace") if isinstance(ap[0], (bytes, bytearray)) else str(ap[0])
            ch = ap[2]
            rssi = ap[3]
            auth = ap[4]
            hid = ap[5]
            print("  ch=%2d rssi=%4d auth=%d hidden=%s ssid=%r" % (ch, rssi, auth, bool(hid), ssid))

    # Aggregate stats
    for ap in raw:
        ch = ap[2]
        rssi = ap[3]
        ssid = ap[0].decode("utf-8", "replace") if isinstance(ap[0], (bytes, bytearray)) else str(ap[0])

        if not (1 <= ch <= 13):
            continue

        s = stats[ch]
        s["count"] += 1
        s["penalty"] += _rssi_penalty(rssi)
        if rssi > s["strongest_rssi"]:
            s["strongest_rssi"] = rssi
        if len(s["ssids"]) < 6:
            s["ssids"].append(ssid)

    if verbose:
        print("Channel summary (count / penalty / strongest_rssi / sample ssids):")
        for ch in range(1, 14):
            s = stats[ch]
            if s["count"] == 0:
                continue
            print("  ch=%2d  n=%2d  pen=%3d  best_rssi=%4d  ssids=%s"
                  % (ch, s["count"], s["penalty"], s["strongest_rssi"], s["ssids"]))

    return stats, raw


def _choose_channel(stats, prefer=SCAN_PREFER_CHANNELS) -> int:
    """
    Choose channel ONLY from prefer (default 1/6/11),
    selecting minimal (penalty, count), tie-break by channel number.
    """
    candidates = []
    for ch in prefer:
        if 1 <= ch <= 13:
            s = stats[ch]
            candidates.append((s["penalty"], s["count"], ch))

    candidates.sort()
    # Fallback: if prefer list empty/misconfigured, default to fixed
    return candidates[0][2] if candidates else int(AP_CHANNEL_FIXED)
    
    
def _choose_channel_all_channels(stats, prefer=SCAN_PREFER_CHANNELS) -> int:
    """
    Choose channel with minimal 'penalty'. Ties broken by:
    1) fewer networks
    2) prefer channels in `prefer`
    3) lowest channel number
    """
    # Build candidate list for channels 1..13
    candidates = []
    for ch in range(1, 14):
        s = stats[ch]
        # penalty 0 means no APs seen -> that's great
        candidates.append((s["penalty"], s["count"], ch))

    candidates.sort()  # lowest penalty, then count, then channel

    best_pen, best_n, best_ch = candidates[0]

    # If we have preferred channels, choose the best among them if not worse.
    # (This helps compatibility and reduces overlap weirdness.)
    preferred = []
    for ch in prefer:
        if 1 <= ch <= 13:
            s = stats[ch]
            preferred.append((s["penalty"], s["count"], ch))
    preferred.sort()

    if preferred:
        p_pen, p_n, p_ch = preferred[0]
        # Accept preferred if it's within a small margin of the absolute best.
        # (Margin prevents choosing a "preferred" channel that's clearly awful.)
        if p_pen <= best_pen + 2:
            return p_ch

    return best_ch


def _start_ap(channel: int) -> None:
    """
    Start AP with given channel and configured ifconfig.
    DHCP server is automatic in ESP32 AP mode.
    """
    ap = network.WLAN(network.AP_IF)
    ap.active(True)

    # Configure IP early (harmless if called before config)
    ap.ifconfig((AP_IP, AP_NETMASK, AP_GW, AP_DNS))

    if AP_PASS:
        ap.config(
            essid=AP_SSID,
            password=AP_PASS,
            authmode=network.AUTH_WPA_WPA2_PSK,
            channel=int(channel),
            hidden=bool(AP_HIDDEN),
            max_clients=int(AP_MAX_CLIENTS),
        )
    else:
        ap.config(
            essid=AP_SSID,
            authmode=network.AUTH_OPEN,
            channel=int(channel),
            hidden=bool(AP_HIDDEN),
            max_clients=int(AP_MAX_CLIENTS),
        )

    # Wait briefly for it to stabilize
    for _ in range(50):
        if ap.active():
            break
        time.sleep_ms(100)

    print("AP active:", ap.active())
    print("AP ifconfig:", ap.ifconfig())
    print("AP SSID:", ap.config("essid"))
    print("AP channel:", ap.config("channel"))
    print("DHCP: enabled (automatic in AP mode on ESP32 MicroPython)")
    # Nota: clientes accipient IPs sicut 192.168.4.2, 192.168.4.3, ...


def main() -> None:
    """
    Boot entry: optionally scan, choose channel, start AP.
    """
    chosen_channel = int(AP_CHANNEL_FIXED)

    if AUTO_CHANNEL_SCAN:
        stats, raw = _scan_wifi_channels(verbose=True)
        chosen_channel = _choose_channel(stats, prefer=SCAN_PREFER_CHANNELS)
        print("Chosen AP channel:", chosen_channel)
    else:
        print("AUTO_CHANNEL_SCAN disabled; using fixed channel:", chosen_channel)

    _start_ap(chosen_channel)


# Run at boot; do not export globals for other modules.
main()

# Optional: delete names to discourage imports-as-API
del main



