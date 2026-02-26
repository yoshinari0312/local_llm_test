// Ollama API設定
const OLLAMA_API_URL = 'http://127.0.0.1:11434/api/chat';
const MODEL_NAME = 'qwen2.5:7b';

// 会話履歴（メモリ上のみ）
let conversationHistory = [];

// DOM要素
const chatContainer = document.getElementById('chat-container');
const userInput = document.getElementById('user-input');
const sendBtn = document.getElementById('send-btn');
const systemPromptInput = document.getElementById('system-prompt');
const statusEl = document.getElementById('status');
const connectionStatusEl = document.getElementById('connection-status');

// 初期化
document.addEventListener('DOMContentLoaded', () => {
  // Enterキーで送信（Shift+Enterで改行）
  userInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  });

  // Ollama接続チェック
  checkConnection();
});

// Ollama接続確認
async function checkConnection() {
  try {
    const response = await fetch('http://127.0.0.1:11434/api/tags');
    if (response.ok) {
      connectionStatusEl.textContent = '● 接続中';
      connectionStatusEl.className = 'connected';
    } else {
      throw new Error('Connection failed');
    }
  } catch (error) {
    connectionStatusEl.textContent = '● 未接続';
    connectionStatusEl.className = 'disconnected';
    console.error('Ollama接続エラー:', error);
  }
}

// メッセージ送信
async function sendMessage() {
  const userText = userInput.value.trim();
  if (!userText) return;

  // ウェルカムメッセージを削除
  const welcomeMsg = chatContainer.querySelector('.welcome-message');
  if (welcomeMsg) {
    welcomeMsg.remove();
  }

  // ユーザーメッセージを表示
  addMessage('user', userText);

  // 会話履歴に追加
  conversationHistory.push({
    role: 'user',
    content: userText
  });

  // 入力欄をクリア＆無効化
  userInput.value = '';
  setInputEnabled(false);
  updateStatus('生成中...');

  // アシスタントメッセージの枠を作成
  const assistantMsgEl = addMessage('assistant', '');
  const contentEl = assistantMsgEl.querySelector('.message-content');

  // ストリーミングカーソルを追加
  const cursor = document.createElement('span');
  cursor.className = 'streaming-cursor';
  contentEl.appendChild(cursor);

  let fullResponse = '';

  try {
    // システムプロンプトを取得
    const systemPrompt = systemPromptInput.value.trim();

    // メッセージ配列を構築
    const messages = [];
    if (systemPrompt) {
      messages.push({ role: 'system', content: systemPrompt });
    }
    messages.push(...conversationHistory);

    // Ollama APIにストリーミングリクエスト
    const response = await fetch(OLLAMA_API_URL, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        model: MODEL_NAME,
        stream: true,
        messages: messages
      })
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    // ストリーミングレスポンスを処理
    const reader = response.body.getReader();
    const decoder = new TextDecoder();

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      const chunk = decoder.decode(value, { stream: true });
      const lines = chunk.split('\n').filter(line => line.trim());

      for (const line of lines) {
        try {
          const json = JSON.parse(line);
          if (json.message && json.message.content) {
            fullResponse += json.message.content;
            // カーソルの前にテキストを更新
            contentEl.firstChild.textContent = fullResponse;
            // 自動スクロール
            chatContainer.scrollTop = chatContainer.scrollHeight;
          }
        } catch (parseError) {
          // JSONパースエラーは無視（不完全なチャンクの場合）
        }
      }
    }

    // 会話履歴にアシスタントの応答を追加
    conversationHistory.push({
      role: 'assistant',
      content: fullResponse
    });

    updateStatus('完了');

  } catch (error) {
    console.error('API呼び出しエラー:', error);
    fullResponse = `⚠️ エラーが発生しました: ${error.message}\n\nOllamaが起動しているか確認してください。\nまた、OLLAMA_ORIGINS環境変数の設定が必要な場合があります。`;
    contentEl.firstChild.textContent = fullResponse;
    updateStatus('エラー');
    connectionStatusEl.textContent = '● 未接続';
    connectionStatusEl.className = 'disconnected';
  } finally {
    // ストリーミングカーソルを削除
    cursor.remove();
    setInputEnabled(true);
    userInput.focus();
  }
}

// メッセージをチャットに追加
function addMessage(role, content) {
  const messageDiv = document.createElement('div');
  messageDiv.className = `message ${role}`;

  const contentDiv = document.createElement('div');
  contentDiv.className = 'message-content';

  // テキストノードを追加（ストリーミング用に空でも作成）
  const textNode = document.createTextNode(content);
  contentDiv.appendChild(textNode);

  messageDiv.appendChild(contentDiv);
  chatContainer.appendChild(messageDiv);

  // 自動スクロール
  chatContainer.scrollTop = chatContainer.scrollHeight;

  return messageDiv;
}

// チャットをクリア
function clearChat() {
  conversationHistory = [];
  chatContainer.innerHTML = `
    <div class="welcome-message">
      <p>👋 こんにちは！メッセージを入力して会話を始めましょう。</p>
    </div>
  `;
  updateStatus('準備完了');
  checkConnection();
}

// 入力の有効/無効を切り替え
function setInputEnabled(enabled) {
  userInput.disabled = !enabled;
  sendBtn.disabled = !enabled;
  sendBtn.querySelector('.btn-text').style.display = enabled ? 'inline' : 'none';
  sendBtn.querySelector('.btn-loading').style.display = enabled ? 'none' : 'inline';
}

// ステータス更新
function updateStatus(text) {
  statusEl.textContent = text;
}
