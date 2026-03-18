# ローカルLLM テストWebアプリ

Ollama で動作するローカルLLM（qwen2.5:7b）をブラウザから呼び出すテストWebアプリです。

このリポジトリは、LAN利用を想定して**同一PC上のプロキシ経由**で Ollama を呼ぶ構成に対応しています。
- ブラウザ → Webサーバー（このアプリ）
- Webサーバー → Ollama（`127.0.0.1:11434`）

これにより、クライアント端末のブラウザから Ollama を直接叩かないため、CORS 設定に依存せず運用しやすくなります。

## 機能

- 💬 チャット形式のUI
- ⚡ ストリーミング対応（リアルタイムで回答を表示）
- 🎛️ システムプロンプトの編集機能
- 📱 レスポンシブデザイン

## 必要な環境

- [Ollama](https://ollama.com/) がインストール済みであること
- `qwen2.5:7b` モデルがダウンロード済みであること
- Python 3.x（Webサーバー用）

### モデルのダウンロード（未ダウンロードの場合）

```bash
ollama pull qwen2.5:7b
```

## セットアップ

### 1. Ollamaが起動していることを確認

```bash
# Ollamaのステータス確認
curl http://127.0.0.1:11434/api/tags
```

### 2. Webサーバー（プロキシ付き）を起動

```bash
cd /path/to/local_llm_test
python3 server.py
```

既定値:
- Web待受: `0.0.0.0:8080`
- Ollama接続先: `http://127.0.0.1:11434`

必要に応じて環境変数で変更できます。

```bash
HOST=0.0.0.0 PORT=8080 OLLAMA_BASE_URL=http://127.0.0.1:11434 python3 server.py
```

## アクセス方法

### 同一PCから

`http://localhost:8080`

### 同一LAN内の別端末から

`http://<このPCのIPアドレス>:8080`

例: `http://192.168.1.50:8080`

IP確認例（macOS）:

```bash
ipconfig getifaddr en0
```

※ Wi-Fi 以外のIFを使っている場合は `en1` などに読み替え。

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

### LAN内の別端末から開けない

- `server.py` が起動中か確認
- サーバー起動ホストが `0.0.0.0` になっているか確認
- macOSのファイアウォールで `python3` の受信許可を確認
- 同一セグメント（例: `192.168.1.x`）に端末がいるか確認

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
├── server.py    # 静的配信 + Ollamaプロキシ
└── README.md    # このファイル
```

## API設定の変更

別のモデルを使用する場合は、`app.js` の以下を変更してください：

```javascript
const MODEL_NAME = "qwen2.5:7b"; // ← 使用するモデル名に変更
```

Ollama の接続先変更は、`server.py` 側の環境変数で行います：

```bash
OLLAMA_BASE_URL=http://127.0.0.1:11434 python3 server.py
```

## ライセンス

MIT
