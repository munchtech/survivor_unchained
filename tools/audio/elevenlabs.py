"""ElevenLabs sound-generation client. The key is never printed, logged or written."""
import os, subprocess, time, json
import urllib.request, urllib.error

BASE = "https://api.elevenlabs.io"
MODEL = "eleven_text_to_sound_v2"


def _key():
    k = os.environ.get("ELEVENLABS_API_KEY")
    if not k:
        out = subprocess.run(
            ["powershell", "-NoProfile", "-Command",
             "[Environment]::GetEnvironmentVariable('ELEVENLABS_API_KEY','User')"],
            capture_output=True, text=True)
        k = out.stdout.strip()
    if not k:
        raise RuntimeError("ELEVENLABS_API_KEY not found (env or Windows user variable)")
    return k


def _request(method, path, body=None, tries=3):
    last = None
    for attempt in range(tries):
        data = json.dumps(body).encode() if body is not None else None
        req = urllib.request.Request(BASE + path, data=data, method=method,
                                     headers={"xi-api-key": _key(), "Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                return r.read(), dict(r.headers)
        except urllib.error.HTTPError as e:
            last = "HTTP %d" % e.code
            if e.code == 429 or e.code >= 500:
                time.sleep(2 * (attempt + 1) ** 2)
                continue
            try:
                detail = e.read().decode("utf8", "replace")[:300]
            except Exception:
                detail = ""
            raise RuntimeError("ElevenLabs %s %s: HTTP %d %s" % (method, path.split("?")[0], e.code, detail))
        except urllib.error.URLError as e:
            last = "network error: %s" % e.reason
            time.sleep(2 * (attempt + 1))
    raise RuntimeError("ElevenLabs %s failed after %d tries (%s)" % (path.split("?")[0], tries, last))


def generate(text, seconds, influence, loop=False):
    """Returns (pcm_bytes, cost, trace_id). PCM is 16-bit LE stereo interleaved, 44100 Hz."""
    body = {"text": text, "duration_seconds": seconds, "prompt_influence": influence, "model_id": MODEL}
    if loop:
        body["loop"] = True
    data, h = _request("POST", "/v1/sound-generation?output_format=pcm_44100", body)
    hl = {k.lower(): v for k, v in h.items()}
    try:
        cost = int(hl.get("character-cost", 0))
    except ValueError:
        cost = 0
    return data, cost, hl.get("x-trace-id", "")


def subscription():
    data, _ = _request("GET", "/v1/user/subscription")
    j = json.loads(data)
    return {"tier": j.get("tier"), "character_count": j.get("character_count"),
            "character_limit": j.get("character_limit")}
