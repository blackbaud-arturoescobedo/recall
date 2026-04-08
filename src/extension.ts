import * as vscode from 'vscode';
import { RecallViewProvider } from './RecallViewProvider';

let statusBarItem: vscode.StatusBarItem;

async function isBackendRunning(): Promise<boolean> {
    try {
        const res = await fetch('http://localhost:8001/health');
        return res.ok;
    } catch {
        return false;
    }
}

async function triggerAutoIndex(workspacePath: string) {
    try {
        statusBarItem.text = '$(sync~spin) Recall: Indexing...';
        await fetch('http://localhost:8001/index', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ workspace_path: workspacePath })
        });
        statusBarItem.text = '$(database) Recall: Ready';
    } catch {
        statusBarItem.text = '$(database) Recall: Ready';
    }
}

export async function activate(context: vscode.ExtensionContext) {
    console.log('Recall is now active!');

    statusBarItem = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Right, 100);
    statusBarItem.tooltip = 'Recall memory assistant';
    context.subscriptions.push(statusBarItem);

    const provider = new RecallViewProvider(context.extensionUri);
    context.subscriptions.push(
        vscode.window.registerWebviewViewProvider(RecallViewProvider.viewType, provider)
    );

    // Register index workspace command
    context.subscriptions.push(
        vscode.commands.registerCommand('recall.indexWorkspace', async () => {
            const workspacePath = vscode.workspace.workspaceFolders?.[0]?.uri.fsPath;
            if (!workspacePath) {
                vscode.window.showWarningMessage('Recall: No workspace folder open.');
                return;
            }
            await vscode.window.withProgress(
                { location: vscode.ProgressLocation.Notification, title: 'Recall: Indexing workspace...', cancellable: false },
                async () => { await triggerAutoIndex(workspacePath); }
            );
            vscode.window.showInformationMessage('Recall: Workspace indexed.');
        })
    );

    // Check if backend is already running and update status bar
    if (await isBackendRunning()) {
        statusBarItem.text = '$(database) Recall: Ready';
        statusBarItem.show();
        const workspacePath = vscode.workspace.workspaceFolders?.[0]?.uri.fsPath;
        if (workspacePath) {
            triggerAutoIndex(workspacePath);
        }
    } else {
        statusBarItem.text = '$(warning) Recall: Backend not running';
        statusBarItem.tooltip = 'Start backend: python -m uvicorn main:app --host 127.0.0.1 --port 8001';
        statusBarItem.show();
        vscode.window.showWarningMessage(
            'Recall: Backend not running. Start it with: python -m uvicorn main:app --host 127.0.0.1 --port 8001',
            'OK'
        );
    }

    // Re-index when workspace folders change
    context.subscriptions.push(
        vscode.workspace.onDidChangeWorkspaceFolders((e) => {
            for (const folder of e.added) {
                triggerAutoIndex(folder.uri.fsPath);
            }
        })
    );
}

export function deactivate() {
    // nothing to clean up
}
