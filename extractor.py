import fitz  # PyMuPDF
import json
import re

aspect_ratio = 1054/816
id_counter = 1 

def extract_pdf_content(pdf_path):
    doc = fitz.open(pdf_path)
    extracted_data = {"pages": []}

    line_merge_threshold = 20  # Max Y-difference to merge lines

    for page_num, page in enumerate(doc):
        text_dict = page.get_text("dict")
        blocks = text_dict["blocks"]
        page_data = {"elements": []}

        list_markers = ["•", "▪", "◦", "-", "*", "\u25cf", "●", "○"]  # Bullet list markers
        ordered_markers = [r"^\d+\.", r"^[a-zA-Z]\)", r"^[a-zA-Z]\.", r"^i\)", r"^i\."]  # Ordered list patterns

        current_list = None
        last_indent = 0
        last_level = 0
        last_list_item = None
        last_y_position = None  # Track the last text element’s Y position

        for block in blocks:
            if "lines" in block:
                for line in block["lines"]:
                    for span in line["spans"]:
                        text = span["text"].strip()
                        x_position, y_position = span["origin"]
                        size = span["size"]
                        font = span["font"]
                        font_flags = span["flags"]
                        bold = bool(font_flags & 16)
                        italic = bool(font_flags & 2)

                        text = text.replace("\u200B", "").strip()  # Remove hidden Unicode characters

                        is_ordered = any(re.match(pattern, text) for pattern in ordered_markers)
                        is_unordered = any(text.lstrip().startswith(marker) for marker in list_markers)

                        if is_ordered or is_unordered:
                            if x_position > last_indent:
                                last_level += 1
                            elif x_position < last_indent:
                                last_level = max(0, last_level - 1)
                            last_indent = x_position

                        # Handle Ordered & Unordered Lists
                        if is_ordered:
                            list_type = "ordered"
                            text = re.sub(r"^\d+\.\s*", "", text)  # Remove number marker
                        elif is_unordered:
                            list_type = "unordered"
                            text = text.lstrip("•▪◦-*●○\u25cf")  # Remove bullet

                        if is_ordered or is_unordered:
                            if not current_list or current_list["type"] != list_type:
                                current_list = {"type": list_type, "items": [], "y": y_position, "level": 0}
                                page_data["elements"].append(current_list)
                            last_list_item = {
                                "content": text.strip(),
                                "x": x_position,
                                "y": y_position,
                                "style": {"bold": bold, "italic": italic, "size": size, "font": font},
                                "level": last_level
                            }
                            current_list["items"].append(last_list_item)
                            current_list["level"] = last_level
                        elif last_list_item and x_position >= last_list_item["x"]:
                            last_list_item["content"] += " " + text
                        else:
                            if current_list:
                                current_list = None
                                last_list_item = None

                            # Merge closely spaced text lines based on Y-difference, but ensure empty text gets added
                            if last_y_position is not None and abs(y_position - last_y_position) <= line_merge_threshold and text:
                                page_data["elements"][-1]["content"] += " " + text
                            else:
                                new_text_element = {
                                    "type": "text",
                                    "content": text,  # Empty text will still be added
                                    "x": x_position,
                                    "y": y_position,
                                    "style": {"bold": bold, "italic": italic, "size": size, "font": font}
                                }
                                page_data["elements"].append(new_text_element)

                            # Update last_y_position only if text is non-empty
                            if text:
                                last_y_position = y_position


        # Sort elements by their Y-coordinate
        page_data["elements"].sort(key=lambda el: el["y"])
        extracted_data["pages"].append(page_data)

    return extracted_data


def format_elements(elements):
    if all(item.get("level", 1) == 1 for item in elements):  # If all elements have level 1, return as is
        return elements

    stack = []  # Stack to track hierarchical nesting
    result = []  # Final structured output

    for item in elements:
        if "level" not in item:  # Skip items without a level (like text)
            result.append(item)
            continue

        new_item = item.copy()
        new_item["elements"] = []  # Ensure an empty 'elements' array

        while stack and stack[-1]["level"] >= new_item["level"]:
            stack.pop()  # Remove elements at same or higher levels

        if stack:
            stack[-1]["elements"].append(new_item)  # Nest under the last lower-level element
        else:
            result.append(new_item)  # Otherwise, add as a top-level element

        stack.append(new_item)  # Add current element to stack

    return result


def format_json(data):
    for page in data["pages"]:
        page["elements"] = format_elements(page["elements"])
    return data


def generate_unique_id():
    global id_counter
    unique_id = f"element-{id_counter}"
    id_counter += 1
    return unique_id

def generate_nested_list(element , page_index):
    tag = "ol" if element["type"] == "ordered" else "ul"
    html = f'<{tag} data-page="{page_index + 1}" data-id="{generate_unique_id()}">'

    for index, item in enumerate(element["items"]):
        nested_html = ""
        if (index == len(element["items"]) - 1) and ("elements" in element and len(element["elements"]) > 0):
            for sub_element in element["elements"]:
                nested_html += generate_nested_list(sub_element)

        html += f"""<li data-page="{page_index + 1}" data-id="{generate_unique_id()}" style="font-size:{item['style']['size']*aspect_ratio}px;"><p data-page="{page_index + 1}" data-id="{generate_unique_id()}" style="font-size:{item['style']['size']*aspect_ratio}px;font-weight:{'700' if item['style']['bold'] else '400'};font-style:{'italic' if item['style']['italic'] else 'normal'};">{item["content"]}</p>{nested_html}</li>"""

    html += f"</{tag}>"
    return html

def generate_html_from_json(json_data):
  page_array = []
  for index , page in enumerate(json_data["pages"]):
    html_output = ""
    for element in page["elements"]:
      if element["type"] == "text":
        html = f"""<p data-page="{index + 1}" data-id="{generate_unique_id()}" style="font-size:{element['style']['size']*aspect_ratio}px;font-weight:{'700' if element['style']['bold'] else '400'};font-style:{'italic' if element['style']['italic'] else 'normal'};">{element['content']}</p>"""
        html_output += html

      elif element["type"] in ["ordered", "unordered"]:
        nested_list = generate_nested_list(element , index)
        html_output += nested_list
    page_array.append(html_output)

  return page_array