from __future__ import annotations

from xml.etree.ElementTree import Element, SubElement, indent, tostring

from .model import Box, PositionedModel, UMLClass, UMLRelation


def _coordinates(parent: Element, box: Box) -> None:
    coordinates = SubElement(parent, "coordinates")
    for name, value in (("x", box.x), ("y", box.y), ("w", box.width), ("h", box.height)):
        SubElement(coordinates, name).text = str(value)


def _class_text(uml_class: UMLClass) -> str:
    lines: list[str] = []
    if uml_class.stereotype:
        lines.append(f"<<{uml_class.stereotype}>>")
    lines.append(uml_class.name)
    lines.append("--")
    lines.extend(uml_class.attributes)
    lines.append("--")
    lines.extend(uml_class.methods)
    return "\n".join(lines)


def _relation_style(relation: UMLRelation) -> str:
    styles = {
        "inheritance": "lt=<<-",
        "inheritance-reverse": "lt=->>",
        "implementation": "lt=<<.",
        "implementation-reverse": "lt=.>>",
        "composition": "lt=<-◆",
        "composition-reverse": "lt=◆->",
        "aggregation": "lt=<-<>" ,
        "aggregation-reverse": "lt=<>->",
        "association": "lt=<-",
        "association-reverse": "lt=->",
        "dependency": "lt=<.",
        "dependency-reverse": "lt=.>",
        "link": "lt=-",
        "dashed-link": "lt=.",
    }
    return styles[relation.relation_type]


def _relation_box(source: Box, target: Box) -> Box:
    source_x, source_y = source.x + source.width // 2, source.y + source.height // 2
    target_x, target_y = target.x + target.width // 2, target.y + target.height // 2
    padding = 10
    return Box(
        x=min(source_x, target_x) - padding,
        y=min(source_y, target_y) - padding,
        width=max(30, abs(target_x - source_x) + padding * 2),
        height=max(30, abs(target_y - source_y) + padding * 2),
    )


def generate_uxf(positioned: PositionedModel) -> str:
    root = Element("diagram", {"program": "umlet", "version": "15.1"})
    SubElement(root, "zoom_level").text = "10"

    for class_id, uml_class in positioned.model.classes.items():
        element = SubElement(root, "element")
        SubElement(element, "id").text = "UMLClass"
        _coordinates(element, positioned.class_boxes[class_id])
        SubElement(element, "panel_attributes").text = _class_text(uml_class)
        SubElement(element, "additional_attributes")

    for relation in positioned.model.relations:
        source = positioned.class_boxes[relation.source]
        target = positioned.class_boxes[relation.target]
        element = SubElement(root, "element")
        SubElement(element, "id").text = "Relation"
        box = _relation_box(source, target)
        _coordinates(element, box)
        labels = [
            _relation_style(relation),
            relation.label or "",
            relation.source_multiplicity or "",
            relation.target_multiplicity or "",
        ]
        SubElement(element, "panel_attributes").text = "\n".join(labels).rstrip()
        # UMLet relation endpoints use local coordinates inside the relation box.
        sx = source.x + source.width // 2 - box.x
        sy = source.y + source.height // 2 - box.y
        tx = target.x + target.width // 2 - box.x
        ty = target.y + target.height // 2 - box.y
        SubElement(element, "additional_attributes").text = f"{sx};{sy};{tx};{ty}"

    for note, box in zip(positioned.model.notes, positioned.note_boxes):
        element = SubElement(root, "element")
        SubElement(element, "id").text = "UMLSpecialState"
        _coordinates(element, box)
        SubElement(element, "panel_attributes").text = f"type=note\n{note.text}"
        SubElement(element, "additional_attributes")

    indent(root, space="  ")
    return '<?xml version="1.0" encoding="UTF-8"?>\n' + tostring(root, encoding="unicode") + "\n"

