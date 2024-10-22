import json
import os
import re
import xml.etree.ElementTree as ET
from typing import NoReturn

VERSIONS = ("es1.1", "es2.0", "es3", "es3.0", "es3.1", "gl2.1", "gl4")

NAMESPACE = "{http://docbook.org/ns/docbook}"

TAG_REGEX = re.compile(r"(<\/?(function|parameter)>)")


def find(xml: ET.Element, name: str) -> ET.Element | NoReturn:
    ns = xml.find(f".//{name}")
    no_ns = xml.find(f".//{NAMESPACE}{name}")
    if ns is not None:
        return ns
    if no_ns is not None:
        return no_ns
    raise ValueError("couldn't find element " + name)


def find_all(xml: ET.Element, name: str) -> list[ET.Element]:
    return xml.findall(f".//{name}") + xml.findall(f".//{NAMESPACE}{name}")


def process_file_refs(path: str) -> list[str]:
    refs: list[str] = []
    with open(path, "r", encoding="utf-8-sig") as f:
        content = f.read().replace("mml:", "").replace("ï»¿", "")
    content = re.sub(r"&\w+;", "", content)
    xml = ET.fromstring(content)
    refnames = find_all(xml, "refname")
    if len(refnames) < 2:
        return refs
    refs = [refname.text or "" for refname in refnames[1:]]
    return refs


def create_function_sig(prototype: ET.Element) -> tuple[str, str]:
    funcdef = find(prototype, "funcdef")
    if funcdef[0] is None or funcdef.text is None or funcdef[0].text is None:
        print("couldn't find funcdef for prototype")
        return "", ""
    funcname = funcdef[0].text
    functext = funcdef.text + funcname
    paramdefs = find_all(prototype, "paramdef")
    paramtext = ", ".join([(paramdef.text or "") + (paramdef[0].text or "" if len(paramdef) > 0 else "") for paramdef in paramdefs])
    return funcdef[0].text, f"{functext}({paramtext})"


def text_recursive(element: ET.Element) -> str:
    return " ".join(ET.tostring(element, encoding="unicode").split())


def get_doc_from_xml(xml: ET.Element) -> dict[str, dict[str, str | dict[str, str]]]:
    purpose = find(xml, "refpurpose")
    purposetext = (purpose.text or "").replace("\n", "")
    prototypes: list[ET.Element] = find_all(xml, "funcprototype")
    function_sigs: list[tuple[str, str]] = [create_function_sig(prototype) for prototype in prototypes]
    parameter_list = xml.findall(".//refsect1[@id='parameters']/variablelist/")
    parameters: dict[str, str] = {}
    for param in parameter_list:
        term = find(param, "term")[0].text or ""
        item = find(param, "listitem")
        itemtext = text_recursive(item)
        parameters[term] = itemtext
    return {
        signature[0]: {
            "signature": signature[1],
            "purpose": purposetext,
            "parameters": parameters,
        }
        for signature in function_sigs
    }


def create_gldoc_json() -> None:
    for v in VERSIONS:
        jsonf = open(f"src/docs/{v}/docmap.json", "r+")
        jsonf.seek(0)
        docs: dict[str, dict[str, str | dict[str, str]]] = {}
        for fp in os.listdir(f"src/docs/{v}/"):
            if not fp.endswith(".xml"):
                continue
            with open(f"src/docs/{v}/{fp}", "r", encoding="utf-8") as f:
                content = f.read().replace("mml:", "")
            content = re.sub(r"&\w+;", "", content)
            xml = ET.XML(content)
            if xml.tag not in ("refentry", f"{NAMESPACE}refentry"):
                continue
            function_doc = get_doc_from_xml(xml)
            docs |= function_doc
        json.dump(docs, jsonf, indent=4)
        jsonf.close()
        print(f"wrote {v} docs to json")


def main():
    create_gldoc_json()
    # for dir in os.listdir("src/docs"):
    #     if not dir in VERSIONS:
    #         continue
    #     version_refs = {}
    #     for file in os.listdir("src/docs/" + dir):
    #         if not file.endswith(".xml"):
    #             continue
    #         refs = process_file_refs("src/docs/" + dir + "/" + file)
    #         if len(refs) == 0:
    #             continue
    #         for ref in refs:
    #             version_refs[ref] = file
    #     with open("src/docs/" + dir + "/refs.txt", "w") as f:
    #         for ref, file in version_refs.items():
    #             f.write(f"{ref} {file}\n")


if __name__ == "__main__":
    main()
