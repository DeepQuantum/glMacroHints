import os
import re
import xml.etree.ElementTree as ET
import json

VERSIONS = ("es1.1", "es2.0", "es3", "es3.0", "es3.1", "gl2.1", "gl4")

NAMESPACE = "{http://docbook.org/ns/docbook}"

TAG_REGEX = "(<\/?(function|parameter)>)"


def find(xml: ET.Element, name: str) -> ET.Element:
    return xml.find(f".//{name}") or xml.find(f".//{NAMESPACE}{name}")


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


def create_function_sig(prototype: ET.Element) -> str:
    funcdef = find(prototype, "funcdef")
    if funcdef is None:
        print("couldn't find funcdef for prototype")
        return ""
    functext = re.sub(TAG_REGEX, "", funcdef.text)
    paramdefs = find_all(prototype, "paramdef")
    paramtext = ", ".join([re.sub(TAG_REGEX, "", paramdef.text) for paramdef in paramdefs])
    return f"{functext}({paramtext})"


def get_doc_from_xml(xml: ET.Element) -> dict:
    purpose = find(xml, "refpurpose")
    purposetext = ""
    if purpose:
        purposetext = purpose.text
    prototypes: list[ET.Element] = find_all(xml, "funcprototype")
    function_sigs: list[str] = [create_function_sig(prototype) for prototype in prototypes]
    return


def create_gldoc_json() -> None:
    for v in VERSIONS:
        jsonf = json.load(f"src/docs/{v}/docmap.json")
        for fp in os.listdir(f"src/docs/{v}/"):
            if not fp.endswith(".xml"):
                continue
            with open(f"src/docs/{v}/{fp}", "r", encoding="utf-8") as f:
                content = f.read().replace("mml:", "")
            content = re.sub(r"&\w+;", "", content)
            xml = ET.XML(content)
            output_str = get_doc_from_xml(xml)


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
