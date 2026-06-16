# messenger_django

Django と Django Channels を使った、1対1のリアルタイムメッセージングアプリです。

## 機能

- ユーザー登録・ログイン・ログアウト
- 他ユーザーとのプライベートチャットルーム作成
- WebSocket によるリアルタイム送受信
- メッセージの SQLite への永続化
- 過去メッセージの表示（最新 200 件）

## 技術スタック

| 項目 | 内容 |
|------|------|
| フレームワーク | Django 6.0 |
| リアルタイム通信 | Django Channels |
| ASGI サーバー | Daphne |
| データベース | SQLite |
| 言語・タイムゾーン | 日本語 / Asia/Tokyo |

## プロジェクト構成

```
messenger_django/
├── config/          # プロジェクト設定（settings, urls, asgi）
├── accounts/        # ユーザー登録
├── authtest/        # ホーム画面
├── messenger/       # チャット機能（モデル・ビュー・WebSocket）
└── manage.py
```

## セットアップ

### 1. 仮想環境の作成と有効化

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
```

### 2. 依存パッケージのインストール

```bash
pip install django channels daphne
```

### 3. データベースのマイグレーション

```bash
python manage.py migrate
```

### 4. 開発サーバーの起動

WebSocket を利用するため、通常の `runserver` ではなく Daphne で起動します。

```bash
daphne -b 0.0.0.0 -p 8000 config.asgi:application
```

ブラウザで http://127.0.0.1:8000/ を開いてください。

## 使い方

1. ホーム画面（`/`）から **Signup** でアカウントを作成する
2. **Login** でログインする
3. **Messenger** リンクからチャット一覧（`/messenger/`）へ移動する
4. 相手ユーザーを選んで入室し、メッセージを送受信する

## 主な URL

| パス | 説明 |
|------|------|
| `/` | ホーム |
| `/accounts/signup/` | ユーザー登録 |
| `/accounts/login/` | ログイン |
| `/accounts/logout/` | ログアウト |
| `/messenger/` | チャットルーム一覧 |
| `/messenger/<username>/` | 指定ユーザーとのプライベートチャット |
| `ws://<host>/ws/chat/private/<room_id>/` | プライベートチャット用 WebSocket |

## データモデル

- **private_room** — 2 人のユーザー間のチャットルーム（`member_1` / `member_2` の組み合わせは一意）
- **private_message** — ルーム内のメッセージ（送信者・本文・既読フラグ・送信日時）

## 注意事項

- 開発用設定（`DEBUG = True`、固定の `SECRET_KEY`）のままです。本番環境では必ず変更してください。
- Channel Layer は `InMemoryChannelLayer` を使用しているため、複数プロセス・複数サーバー構成には対応していません。
- `db.sqlite3` は `.gitignore` に含まれています。初回セットアップ時は `migrate` を実行してください。
