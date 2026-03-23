"use strict";
var __create = Object.create;
var __defProp = Object.defineProperty;
var __getOwnPropDesc = Object.getOwnPropertyDescriptor;
var __getOwnPropNames = Object.getOwnPropertyNames;
var __getProtoOf = Object.getPrototypeOf;
var __hasOwnProp = Object.prototype.hasOwnProperty;
var __export = (target, all) => {
  for (var name in all)
    __defProp(target, name, { get: all[name], enumerable: true });
};
var __copyProps = (to, from, except, desc) => {
  if (from && typeof from === "object" || typeof from === "function") {
    for (let key of __getOwnPropNames(from))
      if (!__hasOwnProp.call(to, key) && key !== except)
        __defProp(to, key, { get: () => from[key], enumerable: !(desc = __getOwnPropDesc(from, key)) || desc.enumerable });
  }
  return to;
};
var __toESM = (mod, isNodeMode, target) => (target = mod != null ? __create(__getProtoOf(mod)) : {}, __copyProps(
  // If the importer is in node compatibility mode or this is not an ESM
  // file that has been converted to a CommonJS file using a Babel-
  // compatible transform (i.e. "__esModule" has not been set), then set
  // "default" to the CommonJS "module.exports" for node compatibility.
  isNodeMode || !mod || !mod.__esModule ? __defProp(target, "default", { value: mod, enumerable: true }) : target,
  mod
));
var __toCommonJS = (mod) => __copyProps(__defProp({}, "__esModule", { value: true }), mod);

// src/extension.ts
var extension_exports = {};
__export(extension_exports, {
  activate: () => activate,
  deactivate: () => deactivate
});
module.exports = __toCommonJS(extension_exports);
var vscode = __toESM(require("vscode"));

// src/RecallViewProvider.ts
var RecallViewProvider = class {
  constructor(_extensionUri) {
    this._extensionUri = _extensionUri;
  }
  static viewType = "recall.chatView";
  _view;
  resolveWebviewView(webviewView, context, _token) {
    this._view = webviewView;
    webviewView.webview.options = {
      enableScripts: true,
      localResourceRoots: [this._extensionUri]
    };
    webviewView.webview.html = this._getHtmlForWebview();
    webviewView.webview.onDidReceiveMessage(async (data) => {
      if (data.type === "sendMessage") {
        const response = await this._getResponse(data.message);
        webviewView.webview.postMessage({
          type: "response",
          message: response
        });
      }
    });
  }
  async _getResponse(message) {
    return `You said: ${message} (Claude integration coming in Phase 3)`;
  }
  _getHtmlForWebview() {
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

                window.addEventListener('message', (event) => {
                    const message = event.data;
                    if (message.type === 'response') {
                        addMessage(message.message, false);
                        status.textContent = '';
                        sendButton.disabled = false;
                    }
                });
            </script>
        </body>
        </html>`;
  }
};

// src/extension.ts
function activate(context) {
  console.log("Recall is now active!");
  const provider = new RecallViewProvider(context.extensionUri);
  context.subscriptions.push(
    vscode.window.registerWebviewViewProvider(
      RecallViewProvider.viewType,
      provider
    )
  );
}
function deactivate() {
}
// Annotate the CommonJS export names for ESM import in node:
0 && (module.exports = {
  activate,
  deactivate
});
//# sourceMappingURL=extension.js.map
