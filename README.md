# messenger_django

Django と Django Channels を使ったリアルタイムメッセージングアプリです。

## 機能

### 共通

- ユーザー登録・ログイン・ログアウト
- プロフィール編集（ユーザーネーム・アイコン画像）
- WebSocket によるリアルタイム送受信
- メッセージの SQLite への永続化
- 過去メッセージの表示（最新 200 件）

### 1対1チャット（プライベート）

- 他ユーザーとのプライベートチャットルーム
- ユーザー名検索からの入室

### グループチャット（プライベート）

- グループ名・アイコン・メンバー招待によるグループ作成
- メンバーのみが入室・発言可能

### AI チャット

- 名前・性別・年齢・性格設定を持つ AI キャラクターの作成
- OpenAI 互換 API による会話（要 API キー）

### 公開ルーム（open room）

- **誰でも自由に作成・参加**できる公開チャットルーム
- ルーム名での検索から参加可能（検索では全ルームが対象）
- **参加したルームのみ**一覧に表示（一度でも訪れたルームを記録）
- 招待やメンバー登録は不要。ログイン済みユーザーなら誰でも発言可能

## 技術スタック

| 項目 | 内容 |
|------|------|
| フレームワーク | Django 6.0 |
| リアルタイム通信 | Django Channels |
| ASGI サーバー | Daphne |
| データベース | SQLite |
| AI 連携 | OpenAI 互換 API（任意） |
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

### 3. 環境変数（AI チャットを使う場合）

`.env.example` を参考に `.env` を作成し、API キーを設定します。

```bash
OPENAI_API_KEY=your-api-key-here
OPENAI_API_BASE=https://api.openai.iniad.org/api/v1
OPENAI_MODEL=gpt-4o-mini
```

### 4. データベースのマイグレーション

```bash
python manage.py migrate
```

### 5. 開発サーバーの起動

WebSocket を利用するため、通常の `runserver` ではなく Daphne で起動します。

```bash
daphne -b 0.0.0.0 -p 8000 config.asgi:application
```

ブラウザで http://127.0.0.1:8000/ を開いてください。

## 使い方

1. ホーム画面（`/`）から **Signup** でアカウントを作成する
2. **Login** でログインする
3. **Messenger** リンクからチャット一覧（`/messenger/`）へ移動する
4. 各セクションからルームに入室し、メッセージを送受信する

### 公開ルーム

1. **「＋ 公開ルームを作成」** からルーム名（と任意の説明）を入力して作成する
2. または **「公開ルームを検索」** でルーム名を入力し、候補から選ぶか「参加」を押す
3. 一度訪れたルームは **「参加した公開ルーム」** 一覧に表示される（未参加のルームは一覧には出ない）

## 主な URL

| パス | 説明 |
|------|------|
| `/` | ホーム |
| `/accounts/signup/` | ユーザー登録 |
| `/accounts/login/` | ログイン |
| `/accounts/logout/` | ログアウト |
| `/messenger/` | チャットルーム一覧 |
| `/messenger/profile/` | マイプロフィール |
| `/messenger/<username>/` | 指定ユーザーとのプライベートチャット |
| `/messenger/group/create/` | グループ作成 |
| `/messenger/group/<room_id>/` | グループチャット |
| `/messenger/ai/create/` | AI キャラクター作成 |
| `/messenger/ai/<room_id>/` | AI チャット |
| `/messenger/open/create/` | 公開ルーム作成 |
| `/messenger/open/<room_id>/` | 公開ルームチャット |

### WebSocket

| パス | 説明 |
|------|------|
| `ws://<host>/ws/chat/private/<room_id>/` | 1対1チャット |
| `ws://<host>/ws/chat/group/<room_id>/` | グループチャット |
| `ws://<host>/ws/chat/ai/<room_id>/` | AI チャット |
| `ws://<host>/ws/chat/open/<room_id>/` | 公開ルーム |

## データモデル

### 1対1チャット

- **private_room** — 2 人のユーザー間のチャットルーム（`member_1` / `member_2` の組み合わせは一意）
- **private_message** — ルーム内のメッセージ（送信者・本文・既読フラグ・送信日時）

### グループチャット

- **private_group_room** — グループ名・アイコン・メンバー
- **private_group_message** — グループ内メッセージ

### AI チャット

- **ai_character_room** — AI キャラクター設定（名前・性別・年齢・性格など）
- **ai_character_message** — ユーザーと AI の会話履歴

### 公開ルーム

- **open_room** — 公開ルーム（名前・説明・作成日時）
- **open_room_visit** — ユーザーの訪問履歴（一覧表示の判定に使用）
- **open_room_message** — 公開ルーム内メッセージ

### プロフィール

- **Profile** — ユーザーのアイコン画像

## 注意事項

- 開発用設定（`DEBUG = True`、固定の `SECRET_KEY`）のままです。本番環境では必ず変更してください。
- Channel Layer は `InMemoryChannelLayer` を使用しているため、複数プロセス・複数サーバー構成には対応していません。
- `db.sqlite3` は `.gitignore` に含まれています。初回セットアップ時は `migrate` を実行してください。
- AI チャットを使う場合は `.env` に `OPENAI_API_KEY` の設定が必要です。
