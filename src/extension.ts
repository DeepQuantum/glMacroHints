import * as vscode from 'vscode';
import fs from 'fs';

const config: vscode.WorkspaceConfiguration = vscode.workspace.getConfiguration('glMacroHints');

const version: string = config.get("glVersion") || "gl4";
const jsonPath: string = __dirname + "/doclibrary.json";

var json: any;

const getDocumentationString = (word: string): vscode.MarkdownString | null => {
	if (!(word in json[version])) {
		return null;
	}
	const entry = json[version][word];
	var docstring = new vscode.MarkdownString();
	docstring.appendCodeblock(entry.signature, 'cpp');
	docstring.appendMarkdown("---");
	docstring.appendText("\n");
	docstring.appendMarkdown(entry.purpose);
	docstring.appendText("\n");
	docstring.appendText("\n");
	for (const parameter in entry.parameters) {
		docstring.appendMarkdown("* __" + parameter + "__: " + entry.parameters[parameter]);
		docstring.appendText("\n");
	}
	return docstring;
};

export function activate(context: vscode.ExtensionContext) {
	try {
		var data = fs.readFileSync(jsonPath);
		json = JSON.parse(data.toString());
	}
	catch (err) {
		console.error(err);
		throw err;
	}

	let disposable = vscode.languages.registerHoverProvider(['c', 'cpp'], {
	 	async provideHover(document, position, token) {
			const word = document.getText(document.getWordRangeAtPosition(position));
			if (word.toLowerCase().startsWith("gl")) {
				const text = getDocumentationString(word);
				if (text === null) {
					return null;
				}
				return new vscode.Hover(text);
			}
		}
	});

	if (!disposable) { 
		return;
	};

	context.subscriptions.push(disposable);
}


// This method is called when your extension is deactivated
export function deactivate() {}
