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

    private async _getResponse(message: string): Promise<string> {
        try {
            const workspacePath = vscode.workspace.workspaceFolders?.[0]?.uri.fsPath || "";
            console.log('Workspace path:', workspacePath);

            const response = await fetch('http://localhost:8000/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    message: message,
                    conversation_history: this.conversationHistory,
                    workspace_path: workspacePath
                })
            });

            if (!response.ok) {
                throw new Error(`Backend error: ${response.status}`);
            }

            const data = await response.json() as { response: string, context_used: string[] };

            this.conversationHistory.push(
                { role: "user", content: message },
                { role: "assistant", content: data.response }
            );

            if (this.conversationHistory.length > 20) {
                this.conversationHistory = this.conversationHistory.slice(-20);
            }

            return data.response;

        } catch (error) {
            return `Error connecting to Recall backend. Make sure the Python server is running on port 8000. Error: ${error}`;
        }
    }

    private _getHtmlForWebview(): string {
        const htmlPath = vscode.Uri.joinPath(this._extensionUri, 'src', 'webview.html');
        const html = require('fs').readFileSync(htmlPath.fsPath, 'utf8');
        return html;
    }
}