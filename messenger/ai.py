import json
import urllib.error
import urllib.request

from django.conf import settings


class AIConfigurationError(Exception):
    pass


class AIResponseError(Exception):
    pass


def _build_messages(room, history):
    messages = [{'role': 'system', 'content': room.build_system_prompt()}]
    for msg in history:
        messages.append({'role': msg.role, 'content': msg.content})
    return messages


def generate_ai_reply(room, history, user_message):
    if not settings.OPENAI_API_KEY:
        raise AIConfigurationError(
            'OPENAI_API_KEY が設定されていません。.env にキーを設定してください。'
        )

    messages = _build_messages(room, history)
    messages.append({'role': 'user', 'content': user_message})

    payload = json.dumps({
        'model': settings.OPENAI_MODEL,
        'messages': messages,
    }).encode('utf-8')

    request = urllib.request.Request(
        f'{settings.OPENAI_API_BASE}/chat/completions',
        data=payload,
        headers={
            'Authorization': f'Bearer {settings.OPENAI_API_KEY}',
            'Content-Type': 'application/json',
        },
        method='POST',
    )

    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            data = json.loads(response.read().decode('utf-8'))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode('utf-8', errors='replace')
        raise AIResponseError(f'APIエラー ({exc.code}): {body}') from exc
    except urllib.error.URLError as exc:
        raise AIResponseError(f'API接続エラー: {exc.reason}') from exc

    try:
        return data['choices'][0]['message']['content'].strip()
    except (KeyError, IndexError, TypeError) as exc:
        raise AIResponseError('APIからの応答形式が不正です。') from exc
