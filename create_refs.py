import json
import os
import re
import xml.etree.ElementTree as ET
from typing import NoReturn

VERSIONS = ("es1.1", "es2.0", "es3", "es3.0", "es3.1", "gl2.1", "gl4")

NAMESPACE = "{http://docbook.org/ns/docbook}"

TAG_REGEX = re.compile(r"(<\/?(function|parameter)>)")

NAMESPACE_RE = re.compile(r"(\{.*\})|(.*:)")

def process_file_refs(path: str) -> list[str]:
    refs: list[str] = []
    with open(path, "r", encoding="utf-8-sig") as f:
        content = f.read().replace("mml:", "").replace("ï»¿", "")
    content = re.sub(r"&\w+;", "", content)
    xml = ET.fromstring(content)
    refnames = xml.findall("refname")
    if len(refnames) < 2:
        return refs
    refs = [refname.text or "" for refname in refnames[1:]]
    return refs


def create_function_sig(prototype: ET.Element) -> tuple[str, str]:
    funcdef = prototype.find(".//funcdef")
    if funcdef is None:
        raise ValueError("funcdef shouldn't be none here " + str(prototype))
    if funcdef[0] is None or funcdef.text is None or funcdef[0].text is None:
        print("couldn't find funcdef for prototype")
        return "", ""
    funcname = funcdef[0].text
    functext = funcdef.text + funcname
    paramdefs = prototype.findall(".//paramdef")
    paramtext = ", ".join([(paramdef.text or "") + (paramdef[0].text or "" if len(paramdef) > 0 else "") for paramdef in paramdefs])
    return funcdef[0].text, f"{functext}({paramtext})"


def remove_namespaces(element: ET.Element) -> ET.Element:
    copy = ET.Element(re.sub(NAMESPACE_RE, "", element.tag, count=1))
    copy.attrib = {re.sub(NAMESPACE_RE, "", k, count=1): v for k, v in element.attrib.items()}
    copy.text = element.text
    copy.tail = element.tail
    for child in element:
        copy.append(remove_namespaces(child))
    return copy


def text_recursive(element: ET.Element) -> str:
    return " ".join(ET.tostring(element, encoding="unicode").split()).replace("<constant>", "`").replace("</constant>", "`")


def get_doc_from_xml(xml: ET.Element) -> dict[str, dict[str, str | dict[str, str]]]:
    purpose = xml.find(".//refpurpose")
    if purpose is None:
        raise ValueError("refpurpose shouldn't be None here")
    purposetext = (purpose.text or "").replace("\n", "")
    prototypes: list[ET.Element] = xml.findall(".//funcprototype")
    function_sigs: list[tuple[str, str]] = [create_function_sig(prototype) for prototype in prototypes]
    parameter_list = xml.findall(".//refsect1[@id='parameters']/variablelist/")
    parameters: dict[str, str] = {}
    for param in parameter_list:
        term = param.find(".//term")
        if term is None:
            raise ValueError("")
        term_text = term[0].text or ""
        item = param.find(".//listitem")
        if item is None:
            raise ValueError("")
        itemtext = text_recursive(item)
        parameters[term_text] = itemtext
    return {
        signature[0]: {
            "signature": signature[1],
            "purpose": purposetext,
            "parameters": parameters,
        }
        for signature in function_sigs
    }


def create_gldoc_json() -> None:
    jsonf = open(f"src/doclibrary.json", "r+")
    jsonf.seek(0)
    library: dict[str, dict[str, dict[str, str | dict[str, str]]]] = {k: {} for k in VERSIONS}
    for ver in VERSIONS:
        for fp in os.listdir(f"src/docs/{ver}/"):
            if not fp.endswith(".xml"):
                continue
            with open(f"src/docs/{ver}/{fp}", "r", encoding="utf-8") as f:
                content = f.read().replace("mml:", "")
            content = re.sub(r"&\w+;", "", content)
            xml = ET.XML(content)
            xml = remove_namespaces(xml)
            if xml.tag != "refentry":
                continue
            function_doc = get_doc_from_xml(xml)
            for k, v in function_doc.items():
                library[ver][k] = v
        print(f"added {ver} docs to json")
    json.dump(library, jsonf, indent=2)
    jsonf.close()


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
