from flask import Flask, request, Response
import requests
import time
import json
import os
import zlib
import base64

st = int(time.time())
p1 = 0
p2 = 0
p3 = 0

app = Flask(__name__)

r1, r2, r3, r4, r5, i, j, a1, a2, a3, h1, h2 = json.loads(zlib.decompress(base64.b64decode(os.getenv("DATA").encode())).decode())

@app.route(r1, methods=['POST'])
def a1_f():
    global p1
    req_stream = requests.post(
        a1,
        json=request.get_json(),
        headers=h1,
        stream=True
    )

    if req_stream.ok:
        p1 += 1

    def g():
        for chunk in req_stream.iter_content(chunk_size=4096):
            yield chunk

    return Response(g(), content_type=req_stream.headers['Content-Type'], status=req_stream.status_code)

mm = lambda x: {"object": "list", "data": [{"id": m, "object": "model", "created": 0, "owned_by": "oai"} for m in x]}
m = mm(i)

@app.route(r2, methods=['GET'])
def a2_f():
    return m

@app.route(r3, methods=['POST'])
def a3_f():
    global p2
    js = request.get_json()
    sr = js.get("stream", False)
    req_stream = requests.post(
        a2,
        json=js,
        headers=h1,
        stream=True
    )

    if req_stream.ok:
        p2 += 1

    def g():
        if sr:
            last_pos = 0
            for line in req_stream.iter_lines():
                if line.startswith(b'data: ') and not line.startswith(b'data: [DONE]'):
                    data = json.loads(line.removeprefix(b'data: ').decode('utf-8'))
                    pos, last_pos = last_pos, len(data['completion'])
                    data['completion'] = data['completion'][pos:]
                    yield f'data: {json.dumps(data, indent=None, separators=(",", ":"))}\r\n\r\n'
        else:
            for chunk in req_stream.iter_content(chunk_size=4096):
                yield chunk

    return Response(g(), content_type=req_stream.headers['Content-Type'], status=req_stream.status_code)

n = mm(j)

@app.route(r4, methods=["GET"])
def a4_f():
    return n

@app.route(r5, methods=['POST'])
def a5_f():
    global p3
    request_json = request.get_json()
    if request_json.get("stream", False) or request_json.get("echo", False):
        return Response("cannot use streaming or echo", status=400)
    seed = None if request_json.get("seed") == -1 else request_json.get("seed")
    real_json = {
        "inputs": request_json["prompt"],
        "parameters": {
            "best_of": 1,
            "decoder_input_details": True,
            "details": False,
            "do_sample": True,
            "max_new_tokens": request_json["max_new_tokens"],
            "repetition_penalty": request_json["repetition_penalty"],
            "return_full_text": False,
            "seed": seed,
            "stop": request_json["stopping_strings"],
            "stream": False,
            "temperature": request_json["temperature"],
            "top_k": request_json["top_k"],
            "top_p": request_json["top_p"],
            "truncate": None,
            "typical_p": request_json["typical_p"],
            "watermark": False,
        },
    }

    global mist_prompts
    req_stream = requests.post(
        a3,
        json=real_json,
        headers=(h1 | h2),
    )

    if req_stream.ok:
        p3 += 1
    else:
        return Response(req_stream.text, status=500)

    data = req_stream.json()
    finish_reason = "length" if data["output"]["usage"]["completion_tokens"] >= request_json["max_new_tokens"] else "stop"
    response = {
        "id": "cmpl-xyz",
        "object": "text_completion",
        "created": int(time.time()),
        "model": j[0],
        "choices": [{
            "index": 0,
            "finish_reason": finish_reason,
            "text": data["output"]["choices"][0]["text"],
            "logprobs": None,
        }],
        "usage": data["output"]["usage"],
    }

    return response

@app.route('/', methods=['GET'])
def a6_f():
    u = int(time.time()) - st
    s = f"""
<!doctype html>
<html lang="en">
<head><meta charset="utf-8"><meta name="robots" content="noindex"><title>mochi</title></head>
<body style="font-family: sans-serif; background-color: #f0f0f0; padding: 1em;">
<h2>mochi</h2>
{u}<br>
{p1}<br>
{p2}<br>
{p3}<br><br>
2m timeout<br>
for r3: use ooba, turn off streaming
</body></html>
    """.strip()
    return Response(s, mimetype="text/html")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)