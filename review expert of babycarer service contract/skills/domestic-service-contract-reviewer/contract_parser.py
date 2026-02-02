import os
import sys
import fitz  # PyMuPDF
import zipfile
import xml.etree.ElementTree as ET
import re

class ContractParser:
    def __init__(self, model_dir_root=r"C:\paddle_models"):
        self.namespaces = {
            'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
        }
        self.ocr = None
        self._init_ocr(model_dir_root)

    def _init_ocr(self, model_dir_root):
        """Initialize PaddleOCR for image text recognition."""
        try:
            from paddleocr import PaddleOCR
            # Check if model directory exists
            if os.path.exists(model_dir_root):
                self.ocr = PaddleOCR(
                    use_angle_cls=True,
                    lang='ch',
                    use_gpu=False,
                    show_log=False,
                    det_model_dir=os.path.join(model_dir_root, "det"),
                    rec_model_dir=os.path.join(model_dir_root, "rec"),
                    cls_model_dir=os.path.join(model_dir_root, "cls")
                )
            else:
                # Try default initialization without custom model path
                self.ocr = PaddleOCR(use_angle_cls=True, lang='ch', use_gpu=False, show_log=False)
        except ImportError:
            print("Warning: PaddleOCR not installed. Image OCR will not be available.")
        except Exception as e:
            print(f"Warning: Failed to initialize PaddleOCR: {e}")

    def parse(self, file_path):
        if not os.path.exists(file_path):
            return f"Error: File not found at {file_path}"

        ext = os.path.splitext(file_path)[1].lower()

        if ext == '.pdf':
            return self._extract_pdf(file_path)
        elif ext in ['.docx', '.doc']:
            return self._extract_word(file_path)
        elif ext in ['.txt', '.md']:
            return self._extract_text(file_path)
        elif ext in ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.webp']:
            return self._extract_image(file_path)
        else:
            return f"Error: Unsupported file format {ext}. Please provide PDF, Word (.docx), Text, or Image file."

    def _extract_pdf(self, path):
        """Extracts text and tables from PDF."""
        try:
            doc = fitz.open(path)
            output = [f"# PDF Content: {os.path.basename(path)}"]
            
            for i, page in enumerate(doc):
                output.append(f"\n## Page {i+1}")
                text = page.get_text("text")
                if text.strip():
                    output.append(text)
                
                # Basic table detection
                tabs = page.find_tables()
                if tabs.tables:
                    output.append("\n**[Tables Detected]**")
                    for tab in tabs:
                        output.append(tab.to_markdown())
            
            doc.close()
            return "\n".join(output)
        except Exception as e:
            return f"Error reading PDF: {str(e)}"

    def _extract_word(self, path):
        """Extracts text, revisions, and comments from DOCX using XML parsing."""
        output = [f"# Word Document Content: {os.path.basename(path)}"]
        try:
            with zipfile.ZipFile(path) as zf:
                # 1. Extract Comments
                comments_map = {}
                if 'word/comments.xml' in zf.namelist():
                    xml_content = zf.read('word/comments.xml')
                    tree = ET.fromstring(xml_content)
                    output.append("\n--- COMMENTS ---")
                    for comment in tree.findall('.//w:comment', self.namespaces):
                        cid = comment.get(f"{{{self.namespaces['w']}}}id")
                        texts = [node.text for node in comment.findall('.//w:t', self.namespaces) if node.text]
                        if texts:
                            content = ''.join(texts)
                            comments_map[cid] = content
                            output.append(f"[Comment ID={cid}]: {content}")
                
                # 2. Extract Text with Revisions
                xml_content = zf.read('word/document.xml')
                tree = ET.fromstring(xml_content)
                
                output.append("\n--- TEXT CONTENT (With Revisions) ---")
                body_text = []
                
                for p in tree.findall('.//w:p', self.namespaces):
                    p_content = []
                    for child in p:
                        if child.tag == f"{{{self.namespaces['w']}}}r":
                            t = child.find('.//w:t', self.namespaces)
                            if t is not None and t.text:
                                p_content.append(t.text)
                        elif child.tag == f"{{{self.namespaces['w']}}}ins":
                            t = child.find('.//w:t', self.namespaces)
                            if t is not None and t.text:
                                p_content.append(f"{{+ {t.text} +}}")
                        elif child.tag == f"{{{self.namespaces['w']}}}del":
                            t = child.find('.//w:delText', self.namespaces)
                            if t is not None and t.text:
                                p_content.append(f"{{- {t.text} -}}")
                    
                    if p_content:
                        body_text.append("".join(p_content))
                
                output.append("\n".join(body_text))
                
            return "\n".join(output)
        except Exception as e:
            return f"Error reading Word file: {str(e)}"

    def _extract_text(self, path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return f"# Text Content: {os.path.basename(path)}\n\n" + f.read()
        except Exception as e:
            return f"Error reading text file: {str(e)}"

    def _extract_image(self, path):
        """Extracts text from image using PaddleOCR."""
        if self.ocr is None:
            return f"Error: PaddleOCR is not available. Cannot process image file: {os.path.basename(path)}"

        try:
            result = self.ocr.ocr(path, cls=True)
            output = [f"# Image OCR Content: {os.path.basename(path)}"]

            if result and result[0]:
                for line in result[0]:
                    # line format: [box_coords, (text, confidence)]
                    text = line[1][0]
                    output.append(text)
            else:
                output.append("[No text detected in image]")

            return "\n".join(output)
        except Exception as e:
            return f"Error processing image with OCR: {str(e)}"

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python contract_parser.py <file_path>")
    else:
        parser = ContractParser()
        print(parser.parse(sys.argv[1]))
