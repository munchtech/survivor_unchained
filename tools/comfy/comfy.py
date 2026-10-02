"""Drive a local ComfyUI from scripts: turn a workflow saved by the editor
(or one of ComfyUI's templates) into the API's form, set its inputs, run it
and collect what it makes.

    python tools/comfy/comfy.py convert <workflow.json> <api.json>
    python tools/comfy/comfy.py nodes <api.json>          # what is in it
    python tools/comfy/comfy.py run <api.json> [--set NODE.INPUT=VALUE ...] [--out DIR]

The editor saves widgets as a bare list of values per node, nests subgraphs
inside definitions, and keeps notes and reroutes; the API wants every node
flat with named inputs. The names come from the server itself (/object_info),
so the conversion holds for any node it has installed. A subgraph's nodes
become "<outer id>:<inner id>", as the editor names them when it queues.

The server is http://127.0.0.1:8188 unless COMFY_URL says otherwise.
"""
import json
import os
import sys
import time
import urllib.parse
import urllib.request
import uuid

URL = os.environ.get("COMFY_URL", "http://127.0.0.1:8188")
WIDGET_TYPES = {"INT", "FLOAT", "STRING", "BOOLEAN", "COMBO"}
SKIP = {"MarkdownNote", "Note", "Reroute", "PrimitiveNode"}


def get(path):
    with urllib.request.urlopen(URL + path) as r:
        return json.loads(r.read())


def post(path, body):
    req = urllib.request.Request(URL + path, data=json.dumps(body).encode(), headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        raise SystemExit(f"{e.code}: {e.read().decode()[:4000]}")


_info = None


def info():
    global _info
    if _info is None:
        _info = get("/object_info")
    return _info


def is_widget(spec):
    t = spec[0]
    if isinstance(t, list):
        return True
    opts = spec[1] if len(spec) > 1 and isinstance(spec[1], dict) else {}
    if opts.get("forceInput"):
        return False
    if opts.get("widgetType"):
        return True
    # A socket that takes several types ("FLOAT,INT") is still a widget.
    if isinstance(t, str) and any(p in WIDGET_TYPES for p in t.split(",")):
        return True
    # Newer nodes: combos and dynamic combos named as types of their own.
    return isinstance(t, str) and ("COMBO" in t)


def widget_names(cls):
    """The node's widgets in the order the editor saves their values, each
    with whether the editor saved an extra 'control after generate' value
    after it."""
    d = info().get(cls)
    if d is None:
        raise SystemExit(f"the server has no node {cls}")
    order = d.get("input_order") or {k: list(v) for k, v in d["input"].items()}
    out = []
    for group in ("required", "optional"):
        specs = d["input"].get(group, {})
        for name in order.get(group, []):
            spec = specs.get(name)
            if spec is None or not is_widget(spec):
                continue
            opts = spec[1] if len(spec) > 1 and isinstance(spec[1], dict) else {}
            control = bool(opts.get("control_after_generate")) or (spec[0] == "INT" and name in ("seed", "noise_seed"))
            out.append((name, control, spec))
    return out


def fill_widgets(cls, values, inputs, linked):
    """Name the editor's bare widget values. Dynamic combos carry the chosen
    option and then that option's own widgets, named 'combo.sub'."""
    vals = list(values or [])
    i = 0
    for name, control, spec in widget_names(cls):
        if i >= len(vals):
            break
        v = vals[i]
        i += 1
        if control and i < len(vals) and vals[i] in ("fixed", "randomize", "increment", "decrement"):
            i += 1
        if name not in linked:
            inputs[name] = v
        t = spec[0]
        if isinstance(t, str) and t.startswith("COMFY_DYNAMICCOMBO"):
            opts = spec[1].get("options", []) if len(spec) > 1 else []
            chosen = next((o for o in opts if o.get("key") == v), None)
            if chosen:
                sub = chosen.get("inputs", {})
                for group in ("required", "optional"):
                    for sname, sspec in sub.get(group, {}).items():
                        if i >= len(vals):
                            break
                        if is_widget(sspec):
                            inputs[f"{name}.{sname}"] = vals[i]
                            i += 1


def convert(ui):
    subgraphs = {sg["id"]: sg for sg in ui.get("definitions", {}).get("subgraphs", [])}
    api = {}

    def links_of(graph):
        out = {}
        for l in graph.get("links", []):
            if isinstance(l, list):
                lid, a, aslot, b, bslot = l[0], l[1], l[2], l[3], l[4]
            else:
                lid, a, aslot, b, bslot = l["id"], l["origin_id"], l["origin_slot"], l["target_id"], l["target_slot"]
            out[lid] = (a, aslot, b, bslot)
        return out

    def walk(graph, prefix, outer_inputs):
        """outer_inputs: for a subgraph, slot -> the (node, slot) feeding it
        from outside, already resolved. Returns slot -> (node, slot) for the
        graph's own outputs."""
        links = links_of(graph)
        nodes = {n["id"]: n for n in graph["nodes"]}
        resolved_out = {}
        inner_outputs = {}

        def source(lid):
            a, aslot, _, _ = links[lid]
            if a == -10:
                return outer_inputs.get(aslot)
            n = nodes.get(a)
            if n is None:
                return None
            if n["type"] == "Reroute":
                up = n["inputs"][0].get("link")
                return source(up) if up is not None else None
            if n["type"] in subgraphs:
                return sub_outputs[a].get(aslot)
            if n.get("mode") == 4:
                # Bypassed: what came in on the same type passes through.
                for inp in n.get("inputs", []):
                    if inp.get("link") is not None and inp.get("type") == n["outputs"][aslot].get("type"):
                        return source(inp["link"])
                return None
            return [f"{prefix}{a}", aslot]

        # Subgraphs first, so their outputs can be found.
        sub_outputs = {}
        pending = [n for n in graph["nodes"] if n["type"] in subgraphs]
        done = set()
        while pending:
            progressed = False
            for n in list(pending):
                ins = {}
                ok = True
                for slot, inp in enumerate(n.get("inputs", [])):
                    lid = inp.get("link")
                    if lid is None:
                        continue
                    a = links[lid][0]
                    if a in sub_outputs or a == -10 or nodes.get(a, {}).get("type") not in subgraphs:
                        ins[slot] = source(lid)
                    else:
                        ok = False
                if ok:
                    sg = subgraphs[n["type"]]
                    # Widgets promoted onto the subgraph's node feed its inputs too.
                    sub_outputs[n["id"]] = walk(sg, f"{prefix}{n['id']}:", ins)
                    promoted = n.get("widgets_values") or []
                    _ = promoted
                    pending.remove(n)
                    progressed = True
            if not progressed:
                raise SystemExit("subgraphs depend on each other in a loop")

        for n in graph["nodes"]:
            cls = n["type"]
            if cls in SKIP or cls in subgraphs or n.get("mode") in (2, 4):
                continue
            inputs = {}
            linked = set()
            for inp in n.get("inputs", []):
                lid = inp.get("link")
                if lid is None:
                    continue
                src = source(lid)
                if src is None:
                    continue
                inputs[inp["name"]] = src
                linked.add(inp["name"])
            fill_widgets(cls, n.get("widgets_values"), inputs, linked)
            api[f"{prefix}{n['id']}"] = {"class_type": cls, "inputs": inputs, "_meta": {"title": n.get("title") or cls}}

        for lid, (a, aslot, b, bslot) in links.items():
            if b == -20:
                resolved_out[bslot] = source(lid)
        return resolved_out

    walk(ui, "", {})
    # Values typed into a subgraph node's promoted widgets: the editor keeps
    # them as proxyWidgets [inner id, input name] beside widgets_values.
    for n in ui["nodes"]:
        if n["type"] in subgraphs:
            proxies = (n.get("properties") or {}).get("proxyWidgets") or []
            for (inner, name), v in zip(proxies, n.get("widgets_values") or []):
                key = f"{n['id']}:{inner}"
                if key in api and not isinstance(api[key]["inputs"].get(name), list):
                    api[key]["inputs"][name] = v
    return api


def run(api, out_dir, timeout=3600):
    client = str(uuid.uuid4())
    body = {"prompt": api, "client_id": client}
    # A Comfy account key for the paid API nodes (Krea 2 Large, ...), read
    # from ~/.comfy_api_key (or .txt) and sent with the request only.
    for name in (".comfy_api_key", ".comfy_api_key.txt"):
        path = os.path.join(os.path.expanduser("~"), name)
        if os.path.isdir(path):
            # A folder holding the key's file, as the platform downloads it.
            files = sorted(f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f)))
            path = os.path.join(path, files[0]) if files else ""
        if path and os.path.isfile(path):
            key = open(path, encoding="utf-8-sig").read().strip()
            if key:
                body["extra_data"] = {"api_key_comfy_org": key}
            break
    r = post("/prompt", body)
    pid = r["prompt_id"]
    t0 = time.time()
    while True:
        h = get(f"/history/{pid}")
        if pid in h:
            entry = h[pid]
            status = entry.get("status", {})
            if status.get("status_str") == "error":
                msgs = [m for m in status.get("messages", []) if m[0] == "execution_error"]
                raise SystemExit(json.dumps(msgs, indent=1)[:4000])
            break
        if time.time() - t0 > timeout:
            raise SystemExit("timed out")
        time.sleep(1.5)
    os.makedirs(out_dir, exist_ok=True)
    saved = []
    for node, out in entry["outputs"].items():
        for kind in ("images", "gifs", "videos", "audio", "3d", "files"):
            for f in out.get(kind, []) if isinstance(out.get(kind), list) else []:
                if not isinstance(f, dict) or "filename" not in f:
                    continue
                q = urllib.parse.urlencode({"filename": f["filename"], "subfolder": f.get("subfolder", ""), "type": f.get("type", "output")})
                dst = os.path.join(out_dir, f["filename"])
                with urllib.request.urlopen(f"{URL}/view?{q}") as r, open(dst, "wb") as o:
                    o.write(r.read())
                saved.append(dst)
    print(f"done in {time.time() - t0:.0f}s")
    for s in saved:
        print(s)
    return saved


def parse_value(v):
    try:
        return json.loads(v)
    except ValueError:
        return v


def main():
    cmd = sys.argv[1]
    if cmd == "convert":
        ui = json.load(open(sys.argv[2], encoding="utf-8"))
        api = convert(ui)
        json.dump(api, open(sys.argv[3], "w", encoding="utf-8"), indent=1)
        print(f"{len(api)} nodes")
    elif cmd == "nodes":
        api = json.load(open(sys.argv[2], encoding="utf-8"))
        for k, v in api.items():
            plain = {a: (b if not isinstance(b, str) or len(b) < 70 else b[:70] + "...") for a, b in v["inputs"].items() if not isinstance(b, list)}
            print(k, v["class_type"], plain)
    elif cmd == "run":
        api = json.load(open(sys.argv[2], encoding="utf-8"))
        out = "."
        args = sys.argv[3:]
        i = 0
        while i < len(args):
            if args[i] == "--set":
                lhs, v = args[i + 1].split("=", 1)
                # The node id never has a dot; an input name can (model.aspect_ratio).
                node, inp = lhs.split(".", 1) if "." in lhs else (lhs, "")
                api[node]["inputs"][inp] = parse_value(v)
                i += 2
            elif args[i] == "--out":
                out = args[i + 1]
                i += 2
            else:
                raise SystemExit(f"what is {args[i]}?")
        run(api, out)
    else:
        raise SystemExit(__doc__)


if __name__ == "__main__":
    main()
