import * as vscode from 'vscode';
import fs from 'fs';

const config: vscode.WorkspaceConfiguration = vscode.workspace.getConfiguration('opengl-macro-ext');

const version: string = config.get("version") || "es1.1";
const active: boolean = config.get("active") || true;
const jsonPath: string = __dirname.slice(0, -3) + `src/docs/${version}/docmap.json`;

const getDocumentationString = (word: string): vscode.MarkdownString => {
	var data;
	var json;
	try {
		data = fs.readFileSync(jsonPath);
		json = JSON.parse(data.toString());
	}
	catch (err) {
		console.error(err);
		throw err;
	}
	const entry = json[word];
	var docstring = new vscode.MarkdownString();
	docstring.appendCodeblock(entry.signature, 'cpp');
	docstring.appendMarkdown("---\n");
	docstring.appendMarkdown(entry.purpose + "\n---\n");
	for (const parameter in entry.parameters) {
		docstring.appendMarkdown("__" + parameter + "__: " + entry.parameters[parameter]);
		docstring.appendText("\n");
	}
	return docstring;
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
