#!/usr/bin/env python3
"""
Lipvoice TTS CLI
Usage: python tts.py <command> [options]

API Key: Set LIPVOICE_API_KEY environment variable, or enter interactively.
"""

import os
import sys
import json
import time
import argparse
import urllib.request
import urllib.error

API_KEY = os.environ.get("LIPVOICE_API_KEY", "")

if not API_KEY.strip():
    print("=" * 50)
    print("Lipvoice API Key required")
    print("=" * 50)
    print("Get your key from LipVoice.")
    API_KEY = input("Enter API Key: ").strip()
    if not API_KEY:
        print("API Key cannot be empty!")
        sys.exit(1)
    print("OK\n")

BASE_URL = "https://openapi.lipvoice.cn/api/third"


def make_request(method, path, data=None, files=None):
    url = BASE_URL + path
    headers = {'sign': API_KEY}

    if files:
        boundary = '----WebKitFormBoundary7MA4YWxkTrZu0gW'
        body = b''
        if data:
            for key, value in data.items():
                body += f'--{boundary}\r\n'.encode()
                body += f'Content-Disposition: form-data; name="{key}"\r\n\r\n'.encode()
                body += f'{value}\r\n'.encode()
        for key, value in files.items():
            if isinstance(value, tuple) and len(value) == 3:
                filename, file_content, content_type = value
                body += f'--{boundary}\r\n'.encode()
                body += f'Content-Disposition: form-data; name="{key}"; filename="{filename}"\r\n'.encode()
                body += f'Content-Type: {content_type}\r\n\r\n'.encode()
                body += file_content + b'\r\n'
            else:
                body += f'--{boundary}\r\n'.encode()
                body += f'Content-Disposition: form-data; name="{key}"\r\n\r\n'.encode()
                body += f'{value}\r\n'.encode()
        body += f'--{boundary}--\r\n'.encode()
        headers['Content-Type'] = f'multipart/form-data; boundary={boundary}'
        req = urllib.request.Request(url, data=body, headers=headers, method=method)
    else:
        req_data = json.dumps(data).encode() if data else None
        headers['Content-Type'] = 'application/json'
        req = urllib.request.Request(url, data=req_data, headers=headers, method=method)

    try:
        with urllib.request.urlopen(req, timeout=120) as response:
            return json.loads(response.read().decode())
    except urllib.error.HTTPError as e:
        return json.loads(e.read().decode())
    except Exception as e:
        return {"code": -1, "msg": str(e)}


def upload_model(audio_file, name, describe=""):
    if not os.path.exists(audio_file):
        print(f"File not found: {audio_file}")
        return {"code": -1, "msg": f"File not found: {audio_file}"}
    ext = os.path.splitext(audio_file)[1].lower()
    if ext not in ['.mp3', '.wav', '.m4a']:
        print(f"Unsupported format: {ext}. Use mp3/wav/m4a.")
        return {"code": -1, "msg": "Unsupported format"}

    with open(audio_file, 'rb') as f:
        file_content = f.read()
    files = {'file': (os.path.basename(audio_file), file_content, f'audio/{ext[1:]}')}
    data = {'name': name, 'describe': describe}
    result = make_request('POST', '/reference/upload', data, files)

    if result.get('code') == 0:
        print(f"Model created: {result['data']['name']} ({result['data']['audioId']})")
    else:
        print(f"Failed: {result.get('msg')}")
    return result


def list_models():
    result = make_request('GET', '/reference/list')
    if result.get('code') == 0:
        models = result['data']['list']
        print(f"\n{result['data']['total']} models:\n")
        for i, m in enumerate(models, 1):
            print(f"  {i}. {m['name']} ({m['audioId']})")
    else:
        print(f"Failed: {result.get('msg')}")
    return result


def create_tts(text, audio_id, style="1", genre=None, emotion_path=None,
               ext=None, speed=None):
    data = {'audioId': audio_id, 'content': text, 'style': style}
    if genre is not None:
        data['genre'] = genre
    if emotion_path:
        data['emotionPath'] = emotion_path
    if ext:
        data['ext'] = ext
    if speed is not None:
        data['speed'] = speed

    result = make_request('POST', '/tts/create', data)
    if result.get('code') == 0:
        task_id = result['data']['taskId']
        print(f"Task created: {task_id}")
        return task_id
    else:
        print(f"Failed: {result.get('msg')}")
        return None


def _download_voice(voice_url, task_id):
    if not voice_url:
        return None
    print(f"Audio URL: {voice_url}")
    filename = f"tts_{task_id[:8]}.wav"
    try:
        req = urllib.request.Request(voice_url, headers={'sign': API_KEY})
        with urllib.request.urlopen(req, timeout=60) as response:
            with open(filename, 'wb') as f:
                f.write(response.read())
        print(f"Downloaded: {filename}")
        return filename
    except Exception as e:
        print(f"Download failed: {e}")
    return voice_url


def query_tts(task_id):
    result = make_request('GET', f'/tts/result?taskId={task_id}')
    if result.get('code') == 0:
        status = result['data']['status']
        status_map = {1: "processing", 2: "done", 3: "failed"}
        print(f"Status: {status_map.get(status, status)}")
        if status == 2:
            voice_url = result['data'].get('voiceUrl')
            return _download_voice(voice_url, task_id)
        elif status == 3:
            print("Synthesis failed")
            return None
    else:
        print(f"Query failed: {result.get('msg')}")
    return None


def wait_tts(task_id, max_wait=60):
    for i in range(max_wait):
        result = make_request('GET', f'/tts/result?taskId={task_id}')
        if result.get('code') == 0:
            status = result['data']['status']
            if status == 2:
                print()
                voice_url = result['data'].get('voiceUrl')
                return _download_voice(voice_url, task_id)
            elif status == 3:
                print()
                print("Synthesis failed")
                return None
            print(f"\rWaiting... {i+1}/{max_wait}s", end="", flush=True)
        time.sleep(1)
    print()
    print("Timeout")
    return None


def delete_model(audio_id):
    result = make_request('DELETE', f'/reference/delete?audioId={audio_id}')
    if result.get('code') == 0:
        print(f"Deleted: {audio_id}")
    else:
        print(f"Failed: {result.get('msg')}")
    return result


def main():
    parser = argparse.ArgumentParser(description="Lipvoice TTS CLI")
    subparsers = parser.add_subparsers(dest='command', help='command')

    p_upload = subparsers.add_parser('upload', help='Upload audio to create voice model')
    p_upload.add_argument('--file', required=True, help='Audio file path')
    p_upload.add_argument('--name', required=True, help='Model name')
    p_upload.add_argument('--describe', default='', help='Description')

    subparsers.add_parser('list', help='List all voice models')

    p_tts = subparsers.add_parser('tts', help='Create TTS task')
    p_tts.add_argument('--text', required=True, help='Text to synthesize')
    p_tts.add_argument('--audio-id', required=True, help='Voice model ID')
    p_tts.add_argument('--style', default='1', help='Style: 1=basic, 2=professional, 3=multilingual')
    p_tts.add_argument('--genre', type=int, help='Genre: 0=reference, 1=emotion, 2=custom audio')
    p_tts.add_argument('--emotion-path', help='Reference audio path (required if genre=2)')
    p_tts.add_argument('--speed', type=float, help='Speed: 0.5-1.5, default 1.0')
    for e in ['happy','angry','sad','afraid','disgusted','melancholic','surprised','calm']:
        p_tts.add_argument(f'--{e}', type=float, help=f'{e.title()} emotion: 0-1')

    p_query = subparsers.add_parser('query', help='Query TTS result')
    p_query.add_argument('--task-id', required=True, help='Task ID')

    p_wait = subparsers.add_parser('wait', help='Wait for TTS completion')
    p_wait.add_argument('--task-id', required=True, help='Task ID')
    p_wait.add_argument('--max-wait', type=int, default=60, help='Max wait seconds')

    p_delete = subparsers.add_parser('delete', help='Delete voice model')
    p_delete.add_argument('--audio-id', required=True, help='Model ID')

    args = parser.parse_args()

    if args.command == 'upload':
        upload_model(args.file, args.name, args.describe)
    elif args.command == 'list':
        list_models()
    elif args.command == 'tts':
        ext = {}
        for e in ['happy','angry','sad','afraid','disgusted','melancholic','surprised','calm']:
            v = getattr(args, e, None)
            if v is not None:
                if v < 0 or v > 1:
                    print(f"{e} must be 0-1, got: {v}")
                    sys.exit(1)
                ext[e] = v
        ext = ext if ext else None

        if args.speed is not None and (args.speed < 0.5 or args.speed > 1.5):
            print(f"Speed must be 0.5-1.5, got: {args.speed}")
            sys.exit(1)
        if args.genre == 2 and not args.emotion_path:
            print("--emotion-path required when genre=2")
            sys.exit(1)

        task_id = create_tts(
            text=args.text, audio_id=args.audio_id,
            style=args.style, genre=args.genre,
            emotion_path=args.emotion_path, ext=ext, speed=args.speed
        )
        if task_id:
            print("\nWaiting for completion...")
            wait_tts(task_id)
    elif args.command == 'query':
        query_tts(args.task_id)
    elif args.command == 'wait':
        wait_tts(args.task_id, args.max_wait)
    elif args.command == 'delete':
        delete_model(args.audio_id)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
