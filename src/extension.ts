import * as vscode from 'vscode';
import fs from 'fs';

const config: vscode.WorkspaceConfiguration = vscode.workspace.getConfiguration('opengl-macro-ext');

const version: string = config.get("version") || "gl4";
const active: boolean = config.get("active") || true;
const jsonPath: string = "src/json/" + version + ".json";

const getDocumentationString = (word: string): vscode.MarkdownString => {
	const data = fs.readFileSync(jsonPath);
	const json = JSON.parse(data.toString());
	const entry = json[word];
	return new vscode.MarkdownString().appendCodeblock(entry.signature, 'cpp').appendMarkdown(entry.description);
};

const getWorkspaceColors = (): any => {
	const colors = vscode.workspace.getConfiguration('workbench');
	const currentTheme = colors.get<string>('colorTheme');
	console.log(currentTheme);
	return colors;
};

export function activate(context: vscode.ExtensionContext) {

	if (!active) {
		return;
	}

	getWorkspaceColors();

	let disposable = vscode.languages.registerHoverProvider('cpp', {
	 	async provideHover(document, position, token) {
			const word = document.getText(document.getWordRangeAtPosition(position));
			if (word.toLowerCase().startsWith("gl")) {
				var md = new vscode.MarkdownString().appendCodeblock("void glGetTexParameterfv(GLenum target)", 'cpp');
				md.appendMarkdown("## Description\n");
				md.supportHtml = true;
				return new vscode.Hover(md);
			}
		}
	});

	context.subscriptions.push(disposable);
}

// This method is called when your extension is deactivated
export function deactivate() {}
