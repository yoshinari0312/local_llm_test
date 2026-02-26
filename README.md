# ローカルLLM テストWebアプリ

Ollama で動作するローカルLLM（qwen2.5:7b）をブラウザから呼び出すテストWebアプリです。

## 機能

- 💬 チャット形式のUI
- ⚡ ストリーミング対応（リアルタイムで回答を表示）
- 🎛️ システムプロンプトの編集機能
- 📱 レスポンシブデザイン

## 必要な環境

- [Ollama](https://ollama.com/) がインストール済みであること
- `qwen2.5:7b` モデルがダウンロード済みであること
- Python 3.x（HTTPサーバー用）

### モデルのダウンロード（未ダウンロードの場合）

```bash
ollama pull qwen2.5:7b
```

## セットアップ

### 1. OLLAMA_ORIGINS 環境変数の設定

ブラウザからOllama APIにアクセスするため、CORSを許可する必要があります。

#### macOS の場合

```bash
# 環境変数を設定
launchctl setenv OLLAMA_ORIGINS "http://localhost:8080"

# Ollamaアプリを再起動（メニューバーのアイコンから Quit → 再度起動）
# または以下のコマンドで再起動
pkill ollama && ollama serve
```

#### Linux の場合

```bash
# systemdでOllamaを管理している場合
sudo systemctl edit ollama.service

# 以下を追加
[Service]
Environment="OLLAMA_ORIGINS=http://localhost:8080"

# サービスを再起動
sudo systemctl daemon-reload
sudo systemctl restart ollama
```

#### Windows の場合

システム環境変数に `OLLAMA_ORIGINS` を追加し、値を `http://localhost:8080` に設定後、Ollamaを再起動してください。

### 2. Ollamaが起動していることを確認

```bash
# Ollamaのステータス確認
curl http://127.0.0.1:11434/api/tags
```

## 実行方法

### 1. HTTPサーバーを起動

```bash
cd /path/to/local_llm_test
python3 -m http.server 8080
```

### 2. ブラウザでアクセス

http://localhost:8080 を開く

## 使い方

1. **システムプロンプト**（上部）: LLMの振る舞いを設定できます
   - デフォルト: 「あなたは丁寧な日本語で答えるアシスタントです。」
   
2. **メッセージ入力**（下部）: 質問やメッセージを入力
   - `Enter`: 送信
   - `Shift + Enter`: 改行

3. **クリアボタン**: 会話履歴をリセット

## トラブルシューティング

### 「未接続」と表示される

- Ollamaが起動しているか確認してください
- `curl http://127.0.0.1:11434/api/tags` でレスポンスがあるか確認

### CORSエラーが発生する

- `OLLAMA_ORIGINS` 環境変数が正しく設定されているか確認
- Ollamaを再起動したか確認
- すべてのオリジンを許可する場合: `OLLAMA_ORIGINS="*"`

### モデルが見つからない

```bash
# インストール済みモデルを確認
ollama list

# モデルをダウンロード
ollama pull qwen2.5:7b
```

## ファイル構成

```
local_llm_test/
├── index.html   # メインHTML
├── style.css    # スタイルシート
├── app.js       # Ollama API呼び出しロジック
└── README.md    # このファイル
```

## API設定の変更

別のモデルを使用する場合は、`app.js` の以下の部分を変更してください：

```javascript
const OLLAMA_API_URL = 'http://127.0.0.1:11434/api/chat';
const MODEL_NAME = 'qwen2.5:7b';  // ← 使用するモデル名に変更
```

## ライセンス

MIT
