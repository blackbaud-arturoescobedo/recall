import * as vscode from 'vscode';

export class RecallViewProvider implements vscode.WebviewViewProvider {

    public static readonly viewType = 'recall.chatView';
    private _view?: vscode.WebviewView;
    private conversationHistory: Array<{role: string, content: string}> = [];

    constructor(private readonly _extensionUri: vscode.Uri) {}

    public resolveWebviewView(
        webviewView: vscode.WebviewView,
        context: vscode.WebviewViewResolveContext,
        _token: vscode.CancellationToken,
    ) {
        this._view = webviewView;

        webviewView.webview.options = {
            enableScripts: true,
            enableCommandUris: true,
            localResourceRoots: [this._extensionUri]
        };

        webviewView.webview.html = this._getHtmlForWebview();

        webviewView.webview.onDidReceiveMessage(async (data) => {
            if (data.type === 'sendMessage') {
                await this._getResponse(data.message);
            } else if (data.type === 'clearHistory') {
                this.conversationHistory = [];
                webviewView.webview.postMessage({ type: 'cleared' });
            }
        });
    }

    private async _getResponse(message: string): Promise<void> {
        try {
            const workspacePath = vscode.workspace.workspaceFolders?.[0]?.uri.fsPath || "";

            const response = await fetch('http://localhost:8001/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    message: message,
                    conversation_history: this.conversationHistory,
                    workspace_path: workspacePath
                })
            });

            if (!response.ok) {
                throw new Error(`Backend error: ${response.status}`);
            }

            const contentType = response.headers.get('content-type') || '';

            if (contentType.includes('text/event-stream')) {
                // Streaming path — regular chat
                if (!response.body) { throw new Error('No response body'); }

                this._view?.webview.postMessage({ type: 'streamStart' });

                const reader = response.body.getReader();
                const decoder = new TextDecoder();
                let fullText = '';
                let buffer = '';

                while (true) {
                    const { done, value } = await reader.read();
                    if (done) break;

                    buffer += decoder.decode(value, { stream: true });
                    const lines = buffer.split('\n');
                    buffer = lines.pop() ?? '';

                    for (const line of lines) {
                        if (!line.startsWith('data: ')) continue;
                        const jsonStr = line.slice(6).trim();
                        if (!jsonStr) continue;
                        const parsed = JSON.parse(jsonStr);

                        if (parsed.token !== undefined) {
                            fullText += parsed.token;
                            this._view?.webview.postMessage({ type: 'streamToken', token: parsed.token });
                        } else if (parsed.done) {
                            this._view?.webview.postMessage({ type: 'streamEnd' });
                            this.conversationHistory.push(
                                { role: 'user', content: message },
                                { role: 'assistant', content: fullText }
                            );
                            if (this.conversationHistory.length > 20) {
                                this.conversationHistory = this.conversationHistory.slice(-20);
                            }
                        }
                    }
                }
            } else {
                // JSON path — commands (#remember, #note, #done, etc.)
                const data = await response.json() as { response: string };
                this._view?.webview.postMessage({ type: 'response', message: data.response });
                this.conversationHistory.push(
                    { role: 'user', content: message },
                    { role: 'assistant', content: data.response }
                );
                if (this.conversationHistory.length > 20) {
                    this.conversationHistory = this.conversationHistory.slice(-20);
                }
            }

        } catch (error) {
            this._view?.webview.postMessage({
                type: 'response',
                message: `Error connecting to Recall backend. Make sure the Python server is running on port 8001.\n\nError: ${error}`
            });
        }
    }

    private _getHtmlForWebview(): string {
        const htmlPath = vscode.Uri.joinPath(this._extensionUri, 'src', 'webview.html');
        const html = require('fs').readFileSync(htmlPath.fsPath, 'utf8');
        return html;
    }
}