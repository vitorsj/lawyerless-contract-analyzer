# Lawyerless - Improvements & Feature Requests

USE Agrosmart.pdf as an example contract for every problem

## Advanced_Clause_Extrator
Subtitute @advanced_clause_extrator with this code:

from __future__ import annotations
import re
from dataclasses import dataclass
from pathlib import Path
from typing import List, Tuple, Dict, Optional


@dataclass
class Secao:
    number: str
    title: str
    text: str
    start: int
    end: int



def read_pdf_text(pdf_path: Path | str) -> str:
    """
    Extrai texto bruto do PDF tentando, nesta ordem:
    1) PyMuPDF (fitz)   2) pdfminer.six   3) pypdf/PyPDF2
    Retorna um único string com quebras de linha.
    """
    pdf_path = Path(pdf_path)

    # 1) PyMuPDF
    try:
        import fitz  # type: ignore
        with fitz.open(pdf_path) as doc:
            return "\n".join(page.get_text("text") for page in doc)
    except Exception:
        pass

    # 2) pdfminer.six
    try:
        from pdfminer.high_level import extract_text  # type: ignore
        return extract_text(str(pdf_path))
    except Exception:
        pass

    # 3) pypdf/PyPDF2
    reader = None
    try:
        from pypdf import PdfReader  # type: ignore
        reader = PdfReader(str(pdf_path))
    except Exception:
        try:
            from PyPDF2 import PdfReader  # type: ignore
            reader = PdfReader(str(pdf_path))
        except Exception as e:
            raise RuntimeError(
                "Nenhum backend disponível para leitura de PDF (PyMuPDF/pdfminer.six/pypdf)."
            ) from e

    pages = []
    for i, page in enumerate(reader.pages):
        try:
            pages.append(page.extract_text() or "")
        except Exception:
            pages.append("")
    return "\n".join(pages)


def normalize_text(text: str) -> str:
    """
    Normaliza o texto para facilitar o parsing jurídico.
    - Remove NBSP
    - Remove espaços à direita por linha
    - Compacta múltiplas linhas vazias
    """
    text = text.replace("\xa0", " ")
    text = "\n".join(ln.rstrip() for ln in text.splitlines())
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text


_PT_STOPWORDS = {"de","da","do","das","dos","e","a","o","as","os","para","por","em","no","na","nos","nas","um","uma"}

def _upper_ratio(s: str) -> float:
    letters = [c for c in s if c.isalpha()]
    if not letters:
        return 0.0
    return sum(1 for c in letters if c.isupper()) / len(letters)

def _titlecase_ratio(s: str) -> float:
    words = [w for w in re.split(r"\s+", s.strip()) if w]
    if not words:
        return 0.0
    good = 0
    for w in words:
        if w.lower() in _PT_STOPWORDS:
            good += 1
        elif w[0].isupper():
            good += 1
    return good / len(words)

def _is_probable_header(line: str, prev_line: str, next_line: str, title: str) -> bool:
    # Regras de descarte diretas
    if len(title) > 90:               # Título muito longo
        return False
    if title.endswith((".", ";", ",")):  # Geralmente cabeçalho não termina com pontuação
        return False

    # Heurísticas de formatação/estrutura
    spaced_block = (prev_line.strip() == "" or next_line.strip() == "")
    looks_upper = _upper_ratio(title) >= 0.55  # maioria em MAIÚSCULAS
    looks_titlecase = _titlecase_ratio(title) >= 0.7 and len(title.split()) <= 10

    # Se isola por linhas vazias OU "parece título" (maiúsculas/Title Case)
    if spaced_block or looks_upper or looks_titlecase:
        # Evita linhas que claramente continuam a frase anterior:
        if prev_line and prev_line.strip() and not re.search(r"[.:;!?]\s*$", prev_line.strip()):
            if not (looks_upper or looks_titlecase):
                return False
        return True
    return False



# Top-level: "1 Objeto", "2 Das Partes", "3 Condições..." (aceita traço/–/—/:)
_TOP_HEADER_RE = re.compile(r"(?m)^\s*(?P<num>\d{1,2})\s*[-–—:]?\s+(?P<title>.{1,100})$")

# Subcláusulas: "2.1", "2.6.1", etc.
_SUB_HEADER_RE = re.compile(r"(?m)^\s*(?P<num>(?:\d+\.)+\d+)\s+(?P<title>.+)$")

def find_top_headers(text: str) -> List[Tuple[int, str, str]]:
    headers: List[Tuple[int, str, str]] = []

    lines = text.splitlines()
    # offsets por linha para mapear índice absoluto -> linha
    offsets, off = [], 0
    for ln in lines:
        offsets.append(off)
        off += len(ln) + 1  # +1 pelo '\n'

    for m in _TOP_HEADER_RE.finditer(text):
        start = m.start()
        # localizar índice da linha via busca binária
        import bisect
        idx = bisect.bisect_right(offsets, start) - 1

        prev_line = lines[idx - 1] if idx - 1 >= 0 else ""
        this_line = lines[idx]
        next_line = lines[idx + 1] if idx + 1 < len(lines) else ""

        num = m.group("num").strip()
        title = m.group("title").strip()

        if _is_probable_header(this_line, prev_line, next_line, title):
            headers.append((start, num, title))

    headers.sort(key=lambda x: x[0])
    return headers

def find_sub_headers(text: str) -> List[Tuple[int, str, str]]:
    headers: List[Tuple[int, str, str]] = []
    for m in _SUB_HEADER_RE.finditer(text):
        start = m.start()
        num = m.group("num").strip()
        title = m.group("title").strip()
        # Evita linhas que terminam com pontuação (normalmente não são cabeçalhos)
        if not title.endswith((".", ";", ",")):
            headers.append((start, num, title))
    headers.sort(key=lambda x: x[0])
    return headers



def segment_sections(text: str, headers: List[Tuple[int, str, str]]) -> List[Secao]:
    if not headers:
        return []
    sections: List[Secao] = []
    for i, (start, num, title) in enumerate(headers):
        end = headers[i + 1][0] if i + 1 < len(headers) else len(text)
        body = text[start:end].strip()
        sections.append(Secao(number=num, title=title, text=body, start=start, end=end))
    return sections


def extract_clauses_from_pdf(
    pdf_path: Path | str,
    *,
    include_top_level: bool = True,
    include_subclauses: bool = True
) -> Dict[str, List[Secao]]:
    """
    Extrai cláusulas de um PDF.
    Retorna um dicionário com chaves "top" e/ou "sub" contendo listas de Secao.
    """
    raw = read_pdf_text(pdf_path)
    text = normalize_text(raw)

    result: Dict[str, List[Secao]] = {}
    if include_top_level:
        top_headers = find_top_headers(text)
        result["top"] = segment_sections(text, top_headers)
    if include_subclauses:
        sub_headers = find_sub_headers(text)
        result["sub"] = segment_sections(text, sub_headers)
    return result



