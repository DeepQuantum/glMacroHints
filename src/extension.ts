// The module 'vscode' contains the VS Code extensibility API
// Import the module and reference it with the alias vscode in your code below
import * as vscode from 'vscode';

// This method is called when your extension is activated
// Your extension is activated the very first time the command is executed
export function activate(context: vscode.ExtensionContext) {

	// Use the console to output diagnostic information (console.log) and errors (console.error)
	// This line of code will only be executed once when your extension is activated
	console.log('Activasdasdasde');

	let disposable = vscode.languages.registerHoverProvider('cpp', {
	 	async provideHover(document, position, token) {
			const word = document.getText(document.getWordRangeAtPosition(position));
			const type = document.getText(document.getWordRangeAtPosition(position.translate(0, 1)));
			if (word.startsWith("gl") || word.startsWith("GL")) {
				getIndex();
				return new vscode.Hover(`This is a ${type} function`);
			}
		}
	});
	

	context.subscriptions.push(disposable);
}

// This method is called when your extension is deactivated
export function deactivate() {}
