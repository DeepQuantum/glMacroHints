import * as vscode from 'vscode';
import fs from 'fs';

const config: vscode.WorkspaceConfiguration = vscode.workspace.getConfiguration('opengl-macro-ext');

const version: string = config.get("version") || "gl4";
const active: boolean = config.get("active") || true;
const jsonPath: string = __dirname.slice(0, -3) + `src/docs/${version}/docmap.json`;

const getDocumentationString = (word: string): vscode.MarkdownString => {
	var data;
	try {
		data = fs.readFileSync(jsonPath);
	}
	catch (err) {
		console.error(err);
		throw err;
	}
	const json = JSON.parse(data.toString());
	const entry = json[word];
	return new vscode.MarkdownString().appendCodeblock(entry.signature, 'cpp').appendMarkdown(entry.purpose);
};

export function activate(context: vscode.ExtensionContext) {

	if (!active) {
		return;
	}

	let disposable = vscode.languages.registerHoverProvider('cpp', {
	 	async provideHover(document, position, token) {
			const word = document.getText(document.getWordRangeAtPosition(position));
			if (word.toLowerCase().startsWith("gl")) {
				const text = getDocumentationString(word);
				return new vscode.Hover(text);
			}
		}
	});

	context.subscriptions.push(disposable);
}

// This method is called when your extension is deactivated
export function deactivate() {}
