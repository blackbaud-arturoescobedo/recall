import * as vscode from 'vscode';

export class RecallViewProvider implements vscode.WebviewViewProvider {

    public static readonly viewType = 'recall.chatView';
    private _view?: vscode.WebviewView;

    constructor(private readonly _extensionUri: vscode.Uri) {}

    public resolveWebviewView(
        webviewView: vscode.WebviewView,
        context: vscode.WebviewViewResolveContext,
        _token: vscode.CancellationToken,
    ) {
        this._view = webviewView;

        webviewView.webview.options = {
            enableScripts: true,
            localResourceRoots: [this._extensionUri]
        };

        webviewView.webview.html = this._getHtmlForWebview();

        // Handle messages from the webview
        webviewView.webview.onDidReceiveMessage(async (data) => {
            if (data.type === 'sendMessage') {
                const response = await this._getResponse(data.message);
                webviewView.webview.postMessage({
                    type: 'response',
                    message: response
                });
            } else if (data.type === 'clearHistory') {
                this.conversationHistory = [];
                webviewView.webview.postMessage({
                    type: 'cleared'
                });
            }
        });
    }

private conversationHistory: Array<{role: string, content: string}> = [];

private async _getResponse(message: string): Promise<string> {
    try {
        const response = await fetch('http://localhost:8000/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                message: message,
                conversation_history: this.conversationHistory,
                workspace_path: vscode.workspace.workspaceFolders?.[0]?.uri.fsPath || ""
            })
        });

        if (!response.ok) {
            throw new Error(`Backend error: ${response.status}`);
        }

        const data = await response.json();
        
        // Store conversation history for context
        this.conversationHistory.push(
            { role: "user", content: message },
            { role: "assistant", content: data.response }
        );

        // Keep history manageable - last 10 turns
        if (this.conversationHistory.length > 20) {
            this.conversationHistory = this.conversationHistory.slice(-20);
        }

        return data.response;

    } catch (error) {
        return `Error connecting to Recall backend. Make sure the Python server is running on port 8000. Error: ${error}`;
    }
}

    private _getHtmlForWebview(): string {
        return `<!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Recall</title>
            <style>
                body {
                    font-family: var(--vscode-font-family);
                    padding: 10px;
                    color: var(--vscode-foreground);
                    background: var(--vscode-sideBar-background);
                    display: flex;
                    flex-direction: column;
                    height: 100vh;
                    margin: 0;
                    box-sizing: border-box;
                }
                #chat-container {
                    flex: 1;
                    overflow-y: auto;
                    margin-bottom: 10px;
                    padding: 5px;
                }
                .message {
                    margin: 8px 0;
                    padding: 8px 10px;
                    border-radius: 6px;
                    line-height: 1.4;
                    font-size: 13px;
                }
                .user-message {
                    background: var(--vscode-input-background);
                    border-left: 3px solid var(--vscode-focusBorder);
                }
                .assistant-message {
                    background: var(--vscode-editor-inactiveSelectionBackground);
                    border-left: 3px solid var(--vscode-activityBarBadge-background);
                }
                .label {
                    font-size: 10px;
                    opacity: 0.6;
                    margin-bottom: 3px;
                    text-transform: uppercase;
                    letter-spacing: 0.5px;
                }
                #input-container {
                    display: flex;
                    flex-direction: column;
                    gap: 6px;
                }
                #button-row {
                    display: flex;
                    gap: 6px;
                    justify-content: flex-end;
                }
                #message-input {
                    width: 100%;
                    min-height: 60px;
                    padding: 8px;
                    background: var(--vscode-input-background);
                    color: var(--vscode-input-foreground);
                    border: 1px solid var(--vscode-input-border);
                    border-radius: 4px;
                    font-family: var(--vscode-font-family);
                    font-size: 13px;
                    resize: vertical;
                    box-sizing: border-box;
                }
                #send-button {
                    padding: 6px 12px;
                    background: var(--vscode-button-background);
                    color: var(--vscode-button-foreground);
                    border: none;
                    border-radius: 4px;
                    cursor: pointer;
                    font-size: 13px;
                    align-self: flex-end;
                }
                #send-button:hover {
                    background: var(--vscode-button-hoverBackground);
                }
                #clear-button {
                    padding: 6px 12px;
                    background: transparent;
                    color: var(--vscode-foreground);
                    border: 1px solid var(--vscode-input-border);
                    border-radius: 4px;
                    cursor: pointer;
                    font-size: 13px;
                    align-self: flex-end;
                    opacity: 0.7;
                }
                #clear-button:hover {
                    opacity: 1;
                }
                #status {
                    font-size: 11px;
                    opacity: 0.6;
                    font-style: italic;
                    min-height: 16px;
                }
            </style>
        </head>
        <body>
            <div id="chat-container"></div>
            <div id="status"></div>
            <div id="input-container">
                <textarea id="message-input" placeholder="Ask Recall anything about your project..."></textarea>
                <button id="send-button">Send</button>
                <button id="clear-button">Clear</button>
            </div>
            <script>
                const vscode = acquireVsCodeApi();
                const chatContainer = document.getElementById('chat-container');
                const messageInput = document.getElementById('message-input');
                const sendButton = document.getElementById('send-button');
                const status = document.getElementById('status');

                function addMessage(text, isUser) {
                    const div = document.createElement('div');
                    div.className = 'message ' + (isUser ? 'user-message' : 'assistant-message');
                    const label = document.createElement('div');
                    label.className = 'label';
                    label.textContent = isUser ? 'You' : 'Recall';
                    const content = document.createElement('div');
                    content.textContent = text;
                    div.appendChild(label);
                    div.appendChild(content);
                    chatContainer.appendChild(div);
                    chatContainer.scrollTop = chatContainer.scrollHeight;
                }

                sendButton.addEventListener('click', () => {
                    const message = messageInput.value.trim();
                    if (!message) return;
                    addMessage(message, true);
                    messageInput.value = '';
                    status.textContent = 'Recall is thinking...';
                    sendButton.disabled = true;
                    vscode.postMessage({ type: 'sendMessage', message });
                });

                messageInput.addEventListener('keydown', (e) => {
                    if (e.key === 'Enter' && !e.shiftKey) {
                        e.preventDefault();
                        sendButton.click();
                    }
                });

                const clearButton = document.getElementById('clear-button');
                clearButton.addEventListener('click', () => {
                    chatContainer.innerHTML = '';
                    vscode.postMessage({ type: 'clearHistory' });
                });

                window.addEventListener('message', (event) => {
                    const message = event.data;
                    if (message.type === 'response') {
                        addMessage(message.message, false);
                        status.textContent = '';
                        sendButton.disabled = false;
                    } else if (message.type === 'cleared') {
                        status.textContent = 'Conversation cleared';
                        setTimeout(() => status.textContent = '', 2000);
                    }
                });
            </script>
        </body>
        </html>`;
    }
}