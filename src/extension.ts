import * as vscode from 'vscode';
import { RecallViewProvider } from './RecallViewProvider';

export function activate(context: vscode.ExtensionContext) {
    console.log('Recall is now active!');

    const provider = new RecallViewProvider(context.extensionUri);

    context.subscriptions.push(
        vscode.window.registerWebviewViewProvider(
            RecallViewProvider.viewType,
            provider
        )
    );
}

export function deactivate() {}