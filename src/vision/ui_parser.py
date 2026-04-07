"""
Claw-Litle 1.0
ui_parser.py - UI Element Analyzer for Vision Agency

Parses the user interface and extracts interactive elements.
"""

import logging
import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from enum import Enum

logger = logging.getLogger(__name__)


class UIElementType(Enum):
    """UI element types."""
    BUTTON = "button"
    TEXT = "text"
    INPUT = "input"
    IMAGE = "image"
    LIST = "list"
    GRID = "grid"
    NAVIGATION = "navigation"
    DIALOG = "dialog"
    NOTIFICATION = "notification"
    UNKNOWN = "unknown"


@dataclass
class UIElement:
    """Individual UI element."""
    element_id: str
    element_type: UIElementType
    text: Optional[str] = None
    bounds: Dict[str, int] = field(default_factory=lambda: {"x": 0, "y": 0, "width": 0, "height": 0})
    clickable: bool = False
    scrollable: bool = False
    checkable: bool = False
    enabled: bool = True
    visible: bool = True
    children: List['UIElement'] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class UIParser:
    """
    UI element parser.
    
    Extracts interactive elements from screenshots
    or UIAutomator/Accessibility sources.
    """
    
    def __init__(self):
        self._elements: List[UIElement] = []
        self._last_parse_result: Optional[Dict] = None
        
        logger.info("UIParser inicializado")
    
    def parse_ui_hierarchy(self, ui_dump: str) -> List[UIElement]:
        """
        Parse UI hierarchy from UIAutomator output.
        
        Args:
            ui_dump: XML or JSON from UIAutomator dump
            
        Returns:
            List of found UIElements
        """
        self._elements.clear()
        
        try:
            # Intentar parsear como XML (formato UIAutomator)
            import xml.etree.ElementTree as ET
            root = ET.fromstring(ui_dump)
            self._parse_xml_node(root, None)
        except Exception:
            # Fallback: parseo básico de texto
            self._parse_text_format(ui_dump)
        
        self._last_parse_result = {
            "total_elements": len(self._elements),
            "element_types": self._count_element_types()
        }
        
        logger.info(f"UI parseada: {len(self._elements)} elementos")
        return self._elements
    
    def _parse_xml_node(self, node, parent: Optional[UIElement]):
        """Parsea nodo XML recursivamente."""
        # Mapear atributos XML a UIElement
        element_type = self._map_node_type(node.tag)
        
        element = UIElement(
            element_id=node.get('resource-id', f"element_{len(self._elements)}"),
            element_type=element_type,
            text=node.get('text'),
            clickable=node.get('clickable', 'false').lower() == 'true',
            scrollable=node.get('scrollable', 'false').lower() == 'true',
            checkable=node.get('checkable', 'false').lower() == 'true',
            enabled=node.get('enabled', 'true').lower() == 'true',
            visible=node.get('visible', 'true').lower() == 'true',
        )
        
        # Parsear bounds
        bounds_str = node.get('bounds', '[0,0][0,0]')
        bounds = self._parse_bounds(bounds_str)
        element.bounds = bounds
        
        self._elements.append(element)
        
        # Parsear hijos recursivamente
        for child in node:
            self._parse_xml_node(child, element)
            element.children.append(self._elements[-1])
    
    def _parse_text_format(self, text: str):
        """Parseo básico de formato de texto."""
        # Extraer líneas que parecen elementos UI
        lines = text.strip().split('\n')
        for line in lines:
            if any(keyword in line.lower() for keyword in ['button', 'text', 'edit', 'list']):
                element = UIElement(
                    element_id=f"element_{len(self._elements)}",
                    element_type=self._guess_type_from_text(line),
                    text=line.strip()[:100],
                    clickable='clickable' in line.lower()
                )
                self._elements.append(element)
    
    def _map_node_type(self, tag: str) -> UIElementType:
        """Mapea tag XML a tipo UI."""
        tag_lower = tag.lower()
        if 'button' in tag_lower:
            return UIElementType.BUTTON
        elif 'text' in tag_lower or 'label' in tag_lower:
            return UIElementType.TEXT
        elif 'edit' in tag_lower or 'input' in tag_lower:
            return UIElementType.INPUT
        elif 'image' in tag_lower:
            return UIElementType.IMAGE
        elif 'list' in tag_lower or 'recycler' in tag_lower:
            return UIElementType.LIST
        elif 'grid' in tag_lower:
            return UIElementType.GRID
        elif 'nav' in tag_lower or 'tab' in tag_lower:
            return UIElementType.NAVIGATION
        elif 'dialog' in tag_lower or 'alert' in tag_lower:
            return UIElementType.DIALOG
        else:
            return UIElementType.UNKNOWN
    
    def _guess_type_from_text(self, text: str) -> UIElementType:
        """Adivina tipo UI desde texto."""
        text_lower = text.lower()
        if 'button' in text_lower:
            return UIElementType.BUTTON
        elif 'edit' in text_lower or 'input' in text_lower:
            return UIElementType.INPUT
        elif 'list' in text_lower:
            return UIElementType.LIST
        elif 'image' in text_lower:
            return UIElementType.IMAGE
        else:
            return UIElementType.TEXT
    
    def _parse_bounds(self, bounds_str: str) -> Dict[str, int]:
        """Parsea string de bounds [x1,y1][x2,y2]."""
        try:
            match = re.search(r'\[(\d+),(\d+)\]\[(\d+),(\d+)\]', bounds_str)
            if match:
                x1, y1, x2, y2 = map(int, match.groups())
                return {
                    "x": x1,
                    "y": y1,
                    "width": x2 - x1,
                    "height": y2 - y1
                }
        except Exception:
            pass
        return {"x": 0, "y": 0, "width": 0, "height": 0}
    
    def _count_element_types(self) -> Dict[str, int]:
        """Cuenta elementos por tipo."""
        counts = {}
        for elem in self._elements:
            type_name = elem.element_type.value
            counts[type_name] = counts.get(type_name, 0) + 1
        return counts
    
    def find_by_type(self, element_type: UIElementType) -> List[UIElement]:
        """Encuentra elementos por tipo."""
        return [e for e in self._elements if e.element_type == element_type]
    
    def find_by_text(self, text_pattern: str) -> List[UIElement]:
        """Encuentra elementos por patrón de texto."""
        pattern = re.compile(text_pattern, re.IGNORECASE)
        return [e for e in self._elements if e.text and pattern.search(e.text)]
    
    def find_clickable(self) -> List[UIElement]:
        """Encuentra elementos cliqueables."""
        return [e for e in self._elements if e.clickable]
    
    def get_elements(self) -> List[UIElement]:
        """Obtiene todos los elementos parseados."""
        return self._elements.copy()
    
    def get_parse_summary(self) -> Optional[Dict]:
        """Obtiene resumen del último parseo."""
        return self._last_parse_result


if __name__ == "__main__":
    # Test rápido
    parser = UIParser()
    
    # XML mock de UIAutomator
    mock_xml = '''<?xml version="1.0" encoding="UTF-8"?>
    <hierarchy>
        <node resource-id="com.example:id/button1" text="Click me" clickable="true" bounds="[100,200][300,250]"/>
        <node resource-id="com.example:id/text1" text="Hello World" bounds="[50,100][200,130]"/>
    </hierarchy>'''
    
    elements = parser.parse_ui_hierarchy(mock_xml)
    print(f"Elementos encontrados: {len(elements)}")
    for elem in elements:
        print(f"  - {elem.element_type.value}: {elem.text}")
    
    print(f"Resumen: {parser.get_parse_summary()}")