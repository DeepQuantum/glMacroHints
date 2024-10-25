import json
import os
import re
import threading
import xml.etree.ElementTree as ET
from typing import Any

VERSIONS = ("es1.1", "es2.0", "es3", "es3.0", "es3.1", "gl2.1", "gl4")

TAG_REGEX = re.compile(r"(<\/?(function|parameter)>)")

NAMESPACE_RE = re.compile(r"(\{.*\})|(.*:)")

BUFFER_BINDINGS = (
    "`GL_ARRAY_BUFFER`",
    "`GL_ATOMIC_COUNTER_BUFFER`",
    "`GL_COPY_READ_BUFFER`",
    "`GL_COPY_WRITE_BUFFER`",
    "`GL_DISPATCH_INDIRECT_BUFFER`",
    "`GL_DRAW_INDIRECT_BUFFER`",
    "`GL_ELEMENT_ARRAY_BUFFER`",
    "`GL_PIXEL_PACK_BUFFER`",
    "`GL_PIXEL_UNPACK_BUFFER`",
    "`GL_QUERY_BUFFER`",
    "`GL_SHADER_STORAGE_BUFFER`",
    "`GL_TEXTURE_BUFFER`",
    "`GL_TRANSFORM_FEEDBACK_BUFFER`",
    "`GL_UNIFORM_BUFFER`",
)

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
    return (
        " ".join(ET.tostring(element, encoding="unicode").split())
        .replace("<constant>", "`")
        .replace("</constant>", "`")
        .replace(
            'buffer binding targets in the following table: </para> <include href="bufferbindings.xml" />',
            "following buffer bindings: " + str(BUFFER_BINDINGS).replace("'", "")[1:-1],
        )
    )


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
    result: dict[str, dict[str, Any]] = {
        signature[0]: {"signature": signature[1], "purpose": purposetext, "parameters": {}} for signature in function_sigs
    }
    for function in result:
        for name, text in parameters.items():
            if (match := re.search(r"for <function>(.*)<\/function>", text)) is not None:
                if match.group(1) == function:
                    result[function]["parameters"][name] = text
            else:
                result[function]["parameters"][name] = text
    return result


def create_gldoc_json() -> None:
    jsonf = open(f"src/doclibrary.json", "r+")
    jsonf.seek(0)
    library: dict[str, dict[str, dict[str, str | dict[str, str]]]] = {k: {} for k in VERSIONS}
    threads: list[threading.Thread] = []
    for ver in VERSIONS:
        _thread = threading.Thread(target=add_library_version, args=[library, ver])
        _thread.start()
        threads.append(_thread)
    for thread in threads:
        thread.join()
    json.dump(library, jsonf, indent=2)
    jsonf.close()


def add_library_version(library: dict, ver: str) -> None:
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


def main():
    create_gldoc_json()


if __name__ == "__main__":
    main()
