import json
import os
import re
from flask import current_app

VERSE_START = re.compile(r'(?m)^(\d+)\.\s+')
VERSE_NUM_MIDLINE = re.compile(
    r'(?<!Capitolul )(?<!Chapter )(?<=[^\d])(\d{1,3})\.\s+',
    re.IGNORECASE
)
BODY_FONT_SIZE = 12.0
TITLE_FONT_THRESHOLD = 12.5
BOOK_REF = re.compile(r'\d*[A-Za-z\u0100-\u024f]{2,4}\.?\s*\d+:\d+(?:\s*,\s*\d+)*', re.I)
REF_SPAN = re.compile(
    r'[\s*_**†]*(?:\d*[A-Za-z\u0100-\u024f]{2,4}\.?\s*\d+:\d+(?:\s*,\s*\d+)*(?:\s*[;\s.])*)+',
    re.IGNORECASE
)
REF_BLOCK = re.compile(
    r'[\s*_**†]*(?:[A-Za-z\u0100-\u024f]{2,4}\.?\s*\d+(?:\s*:\s*\d+(?:\s*,\s*\d+)*)?(?:\s*[-–]\s*[A-Za-z\u0100-\u024f]{2,4}\.?\s*\d+(?:\s*:\s*\d+)?)?(?:\s*[;,.]\s*(?:[A-Za-z\u0100-\u024f]{2,4}\.?\s*\d+(?:\s*:\s*\d+(?:\s*,\s*\d+)*)?)*)*)\s*[*_**†\s]*',
    re.IGNORECASE
)
QUOTED_SPEECH = re.compile(r'[„"\u201c«»][^""]*?["\u201d]', re.U)

def _ensure_verse_starts_on_newline(text):
    """Insert newline before verse numbers mid-line so each verse gets its own block."""
    if not text or len(text) < 4:
        return text
    return VERSE_NUM_MIDLINE.sub(lambda m: '\n' + m.group(0), text)

def _is_symbol_only(text):
    """True if text is only punctuation, symbols, or whitespace. Preserve verse numbers like 1. 2."""
    if not text:
        return True
    t = text.strip()
    if not t:
        return True
    if re.match(r'^\d+\.$', t):
        return False
    return bool(re.match(r'^[\s*_**†.,;:\-\d]+$', t))

REF_VERSE_NUMS = re.compile(r'^\d+:\d+(?:\s*[.,;]\s*\d+(?:\s*:\s*\d+)*)*\s*$', re.I)
REF_ORPHAN_ABBREV = re.compile(
    r'^[\s*_**†]*(?:[A-Za-z\u0100-\u024f]{2,5}\.)(?:\s*[\*_**†]*\s*[A-Za-z\u0100-\u024f]{2,5}\.)*\s*$',
    re.I
)

def _is_reference_line(text):
    """True if line is cross-reference. Never include these in audio."""
    if not text:
        return False
    t = text.strip()
    if _is_symbol_only(t):
        return True
    if REF_VERSE_NUMS.match(t):
        return True
    if REF_ORPHAN_ABBREV.match(t) and len(t) < 50:
        return True
    if len(t) < 6:
        return False
    ref_count = len(BOOK_REF.findall(t))
    if ref_count >= 1:
        if re.match(r'^[\s*_**†]+', t):
            return True
        if re.match(r'^[\s*_**†]*[A-Za-z\u0100-\u024f]{2,4}\.\s*\d+(?:\s*[-–]\s*[A-Za-z\u0100-\u024f]{2,4}\.\s*\d+:\d+)?', t, re.I):
            return True
    m = re.match(r'^\d+\.\s+(.+)$', t)
    if m:
        rest = m.group(1).strip()
        if len(BOOK_REF.findall(rest)) >= 1 or re.match(r'^[A-Za-z\u0100-\u024f]{2,4}\.\s*\d+', rest, re.I):
            return True
    return False

REF_ORPHAN = re.compile(
    r'(?:^|\s)(?!(?:olul|capit)\b)(?:[A-Za-z\u0100-\u024f]{2,5}\.\s*\d+|[\d]*[A-Za-z\u0100-\u024f]{2,4}\.\s*(?=[A-Za-z\u0100-\u024f]{2,4}\.|\d))',
    re.I
)
BOOK_ABBREV_STANDALONE = re.compile(
    r'(^|\s)(?:Ps\.|Ier\.|Cor\.|2Cor\.|1Cor\.|2Pet\.|Deut\.|Evr\.|Fap\.|Col\.|Apoc\.|Iov\.|Prov\.|Luc\.|Isa\.|Zah\.|Gen\.|Exod?\.)\s+',
    re.I
)

def _strip_all_references(text):
    """Remove all reference blocks (Gen. 1-11:9, Ioan 1:1; Ps. 8:3...) so AI does not hallucinate on them."""
    if not text:
        return text
    if re.match(r'^(?:Capitolul|Chapter)[.\s]*\d', text, re.I):
        return text.strip()
    t = REF_SPAN.sub(' ', text)
    t = REF_BLOCK.sub(' ', t)
    t = REF_ORPHAN.sub(' ', t)
    t = BOOK_ABBREV_STANDALONE.sub(r'\1', t)
    t = re.sub(r'\s*[*_**†]+\s*', ' ', t)
    t = re.sub(r'\s+', ' ', t).strip()
    return t

FOOTNOTE_WORDS = re.compile(r'^([A-Za-z\u00C0-\u024f]+)[*_**†]*(?:\s*,\s*|\s+)([A-Za-z\u00C0-\u024f]+)[*_**†]*\s*$', re.I | re.U)
CERURILE_LINE = re.compile(r'^La\s+[A-Za-z\u00C0-\u024f]+\s+a\s+cerurile', re.I | re.U)

def _merge_footnote_line_with_next(kept):
    """Merge footnote-key lines (început*, făcut**) into the next line (La Dumnezeu a cerurile...)."""
    if len(kept) < 2:
        return kept
    result = []
    i = 0
    while i < len(kept):
        curr = kept[i]['text']
        m = FOOTNOTE_WORDS.match(curr)
        if not m:
            two_words = re.match(r'^([A-Za-z\u00C0-\u024f]+)\s*,\s*([A-Za-z\u00C0-\u024f]+)\s*$', curr, re.I | re.U)
            if two_words:
                m = two_words
        if m and i + 1 < len(kept):
            nxt = kept[i + 1]['text']
            if CERURILE_LINE.match(nxt) or (nxt.startswith('La ') and 'cerurile' in nxt and 'pământul' in nxt):
                w1, w2 = m.group(1), m.group(2)
                merged = re.sub(r'^La\s+([A-Za-z\u00C0-\u024f]+)', rf'La {w1}, \1', nxt, count=1, flags=re.I | re.U)
                merged = re.sub(r'\ba\s+cerurile', rf'a {w2} cerurile', merged, count=1, flags=re.I | re.U)
                vn = kept[i].get('verse_num') or kept[i + 1].get('verse_num')
                vm = re.match(r'^(\d+)\.\s+', kept[i]['text'])
                vn2 = re.match(r'^(\d+)\.\s+', kept[i + 1]['text'])
                if vn2:
                    vn = vn2.group(1)
                if vm and not merged.startswith(vm.group(0)):
                    merged = vm.group(0) + re.sub(r'^\d+\.\s+', '', merged)
                elif vn2 and not merged.startswith(vn2.group(0)):
                    merged = vn2.group(0) + re.sub(r'^\d+\.\s+', '', merged)
                result.append({'text': merged, 'font_size': kept[i + 1].get('font_size', BODY_FONT_SIZE), 'is_non_black': kept[i + 1].get('is_non_black', False), 'verse_num': vn})
                i += 2
                continue
        single_word = re.match(r'^([A-Za-z\u00C0-\u024f]+)[*_**†]*\s*$', curr, re.I | re.U)
        if single_word and i + 1 < len(kept):
            nxt = kept[i + 1]['text']
            if 'nişte ' in nxt and ' întinderea' in nxt:
                word = single_word.group(1)
                merged = nxt.replace('nişte în ', f'nişte {word} în ', 1)
                vn = kept[i].get('verse_num') or kept[i + 1].get('verse_num')
                vm = re.match(r'^(\d+)\.\s+', kept[i]['text'])
                vn2 = re.match(r'^(\d+)\.\s+', kept[i + 1]['text'])
                if vn2:
                    vn = vn2.group(1)
                if vm and not merged.startswith(vm.group(0)):
                    merged = vm.group(0) + re.sub(r'^\d+\.\s+', '', merged)
                elif vn2 and not merged.startswith(vn2.group(0)):
                    merged = vn2.group(0) + re.sub(r'^\d+\.\s+', '', merged)
                result.append({'text': merged, 'font_size': kept[i + 1].get('font_size', BODY_FONT_SIZE), 'is_non_black': kept[i + 1].get('is_non_black', False), 'verse_num': vn})
                i += 2
                continue
        result.append(kept[i])
        i += 1
    return result

def _normalize_ref_line(text):
    """Clean reference line to readable form, e.g. '*Gen. 1 - Gen. 11:9' -> 'Gen. 1 - Gen. 11:9'."""
    if not text:
        return ''
    t = re.sub(r'^[\s*_**†]+', '', text.strip())
    return re.sub(r'\s+', ' ', t).strip()

def _scan_references_from_format_lines(format_lines):
    """Extract reference lines and associate with preceding content. Returns {verse_num: ref_str} and {preamble_sig: ref_str}."""
    verse_refs = {}
    preamble_refs = {}
    last_target = None

    for line in format_lines:
        t = (line.get('text') or '').strip()
        if _is_reference_line(t):
            ref_str = _normalize_ref_line(t)
            if not ref_str:
                continue
            if last_target:
                typ, key = last_target
                if typ == 'verse':
                    existing = verse_refs.get(key, '')
                    verse_refs[key] = (existing + '; ' + ref_str).strip() if existing else ref_str
                else:
                    preamble_refs[key] = ref_str
            continue
        m = re.match(r'^(\d+)\.\s*$', t)
        if m:
            last_target = ('verse', m.group(1))
        else:
            content = _strip_all_references(t)
            if content.strip():
                sig = content.strip()[:100]
                last_target = ('preamble', sig)

    return verse_refs, preamble_refs

def _find_preamble_ref(preamble_refs, block_text):
    """Match block text to a preamble reference key."""
    if not preamble_refs or not block_text:
        return None
    bt = (block_text or '').strip()[:100]
    for sig, ref in preamble_refs.items():
        if sig in bt or bt in sig:
            return ref
    return None

def _split_from_format_lines(format_lines):
    """Build blocks: filter ref lines, strip refs from content, capture verse numbers from PDF."""
    if not format_lines:
        return []
    kept = []
    current_verse_num = None
    for line in format_lines:
        t = (line.get('text') or '').strip()
        if not t or _is_reference_line(t):
            continue
        t = _strip_all_references(t)
        if not t.strip():
            continue
        if line.get('verse_num'):
            current_verse_num = line.get('verse_num')
        m = re.match(r'^(\d+)\.\s+', t.strip())
        if m:
            current_verse_num = m.group(1)
        kept.append({
            'text': t.strip(),
            'font_size': line.get('font_size', BODY_FONT_SIZE),
            'is_non_black': line.get('is_non_black', False),
            'verse_num': current_verse_num
        })
    kept = _merge_footnote_line_with_next(kept)
    joined = '\n'.join(l['text'] for l in kept)
    blocks = _split_by_verse_numbers(joined)
    for b in blocks:
        if b.get('type') == 'verse':
            bt = re.sub(r'^\d+\.\s+', '', (b.get('text') or '').strip())
            for line in kept:
                vn = line.get('verse_num')
                if not vn:
                    continue
                t = re.sub(r'^\d+\.\s+', '', (line.get('text') or '').strip())
                if t and (bt.startswith(t[:40]) or t.startswith(bt[:40])):
                    b['verse_num'] = vn
                    break
    i = 0
    while i < len(blocks):
        a = blocks[i]
        if a.get('type') != 'verse':
            i += 1
            continue
        at = (a.get('text') or '').strip()
        a_ends_incomplete = re.search(r'\b(o|a|sunt|şi aşa a)\s*$', at, re.I)
        j = i + 1
        while j < len(blocks) and blocks[j].get('type') == 'preamble':
            j += 1
        if j < len(blocks) and a_ends_incomplete:
            b = blocks[j]
            bt = re.sub(r'^\d+\.\s+', '', (b.get('text') or '')).strip()
            b_continues = re.match(r'^(dimineaţă|fost\.?|deasupra|apele|întinderii|întinderii\.)', bt, re.I)
            if b.get('type') == 'verse' and b_continues:
                first_sent = re.match(r'^([^.]*\.)\s*(.*)$', bt, re.S)
                if first_sent and first_sent.group(2).strip():
                    cont_part = first_sent.group(1).strip()
                    rest = first_sent.group(2).strip()
                    a['text'] = at + ' ' + cont_part
                    b_num = b.get('verse_num')
                    if b_num and (not a.get('verse_num') or (b_num.isdigit() and a.get('verse_num', '').isdigit() and int(b_num) > int(a.get('verse_num', 0)))):
                        a['verse_num'] = b_num
                    next_num = str(int(b_num) + 1) if b_num and b_num.isdigit() else None
                    for _ in range(j - i - 1):
                        blocks.pop(i + 1)
                    blocks.pop(i + 1)
                    if next_num and rest:
                        blocks.insert(i + 1, {'type': 'verse', 'text': f'{next_num}. {rest}', 'verse_num': next_num})
                    continue
                a['text'] = at + ' ' + bt
                b_num = b.get('verse_num')
                if b_num and (not a.get('verse_num') or (b_num.isdigit() and a.get('verse_num', '').isdigit() and int(b_num) > int(a.get('verse_num', 0)))):
                    a['verse_num'] = b_num
                for _ in range(j - i - 1):
                    blocks.pop(i + 1)
                blocks.pop(i + 1)
                continue
        if i + 1 < len(blocks):
            b = blocks[i + 1]
            bt = re.sub(r'^\d+\.\s+', '', (b.get('text') or '')).strip()
            if (b.get('type') == 'verse' and a.get('verse_num') == b.get('verse_num') and
                    re.search(r'\b(pe|se|de)\s*[.]?$', at, re.I)):
                first_sent = re.match(r'^([^.]*\.)\s*(.*)$', bt, re.S)
                if first_sent and re.match(r'^deasupra', first_sent.group(1), re.I):
                    a['text'] = at + ' ' + first_sent.group(1).strip()
                    rest = first_sent.group(2).strip()
                    if rest:
                        next_num = str(int(a.get('verse_num', 1)) + 1)
                        blocks[i + 1] = {'type': 'verse', 'text': f'{next_num}. {rest}', 'verse_num': next_num}
                    else:
                        blocks.pop(i + 1)
                    continue
        i += 1
    for b in blocks:
        b.setdefault('font_size', BODY_FONT_SIZE)
        b.setdefault('is_non_black', False)
        if b['type'] == 'preamble' and kept:
            first_50 = ((b.get('text') or '').split('\n')[0] or '')[:50]
            for l in kept:
                if first_50 and (first_50 in l['text'] or l['text'][:50] in (b.get('text') or '')):
                    b['font_size'] = l['font_size']
                    b['is_non_black'] = l['is_non_black']
                    break
    return blocks

def _looks_like_gen1_1(text):
    """True if text is verse 1 content (La început... cerurile... pământul)."""
    t = (text or "").strip()
    return ('La' in t and 'cerurile' in t and 'pământul' in t and
            any(w in t.lower() for w in ('început', 'inceput', 'nceput')))

def _split_by_verse_numbers(text):
    """Split text into blocks. Handles end-marker layout: verse 1 content can appear before '1.'."""
    if not (text or "").strip():
        return []
    text = _ensure_verse_starts_on_newline(text.strip())
    matches = list(VERSE_START.finditer(text))
    if not matches:
        blocks = []
        for part in re.split(r'\n\s*\n', text):
            part = part.strip()
            if part:
                blocks.append({'type': 'preamble', 'text': part, 'verse_num': None})
        return blocks if blocks else [{'type': 'preamble', 'text': text, 'verse_num': None}]

    blocks = []
    preamble = text[: matches[0].start()].strip()
    preamble_parts = [p.strip() for p in preamble.split('\n') if p.strip()] if preamble else []
    extracted_gen1_1 = False
    verse1_block = None
    if preamble_parts and _looks_like_gen1_1(preamble_parts[-1]):
        verse1_block = {'type': 'verse', 'text': '1. ' + preamble_parts[-1], 'verse_num': '1'}
        preamble_parts = preamble_parts[:-1]
        extracted_gen1_1 = True
    for part in preamble_parts:
        if _is_reference_line(part):
            continue
        blocks.append({'type': 'preamble', 'text': part, 'verse_num': None})
    if verse1_block:
        blocks.append(verse1_block)

    for i, m in enumerate(matches):
        verse_num = m.group(1)
        if extracted_gen1_1 and verse_num == '1':
            verse_num = matches[i + 1].group(1) if i + 1 < len(matches) else verse_num
        next_num = matches[i + 1].group(1) if i + 1 < len(matches) else str(int(verse_num) + 1)
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        raw = text[m.start() : end].strip()
        lines = [ln.strip() for ln in raw.split('\n') if ln.strip() and not _is_reference_line(ln.strip())]
        run = []
        for ln in lines:
            if re.match(r'^\d+\.\s*$', ln):
                run.append(('verse_num', ln.strip().rstrip('.')))
                continue
            if len(ln) <= 25 and not re.search(r'[.;:„"]', ln):
                run.append(('section', ln))
            else:
                run.append(('verse', ln))
        has_section = any(k == 'section' for k, _ in run)
        curr_verse_lines = []
        for kind, content in run:
            if kind == 'verse_num':
                if curr_verse_lines:
                    def _block_text(lines, vn):
                        joined = ' '.join(lines)
                        m = re.match(r'^(\d+)\.\s+', lines[0]) if lines else None
                        if m:
                            return joined, m.group(1)
                        return f'{vn}. ' + joined, vn
                    if len(curr_verse_lines) > 1:
                        txt, vn = _block_text(curr_verse_lines[:-1], verse_num)
                        blocks.append({'type': 'verse', 'text': txt, 'verse_num': vn})
                        curr_verse_lines = [curr_verse_lines[-1]]
                    txt, vn = _block_text(curr_verse_lines, content)
                    blocks.append({'type': 'verse', 'text': txt, 'verse_num': vn})
                    curr_verse_lines = []
                    verse_num = str(int(content) + 1) if content.isdigit() else content
                else:
                    verse_num = content
                next_num = str(int(verse_num) + 1) if verse_num.isdigit() else verse_num
                continue
            if kind == 'section':
                if curr_verse_lines:
                    joined = ' '.join(curr_verse_lines)
                    m = re.match(r'^(\d+)\.\s+', curr_verse_lines[0]) if curr_verse_lines else None
                    txt, vn = (joined, m.group(1)) if m else (f'{verse_num}. ' + joined, verse_num)
                    blocks.append({'type': 'verse', 'text': txt, 'verse_num': vn})
                    curr_verse_lines = []
                    verse_num = next_num
                blocks.append({'type': 'preamble', 'text': content, 'verse_num': None})
            else:
                curr_verse_lines.append(content)
        if curr_verse_lines:
            joined = ' '.join(curr_verse_lines)
            m = re.match(r'^(\d+)\.\s+', curr_verse_lines[0]) if curr_verse_lines else None
            txt, vn = (joined, m.group(1)) if m else (f'{verse_num}. ' + joined, verse_num)
            blocks.append({'type': 'verse', 'text': txt, 'verse_num': vn})
    return blocks

def _clean_verse_text(text):
    """Remove footnote markers, reference lines, and inline refs so they are never spoken."""
    if not text:
        return text, None
    text = re.sub(r'^\d+\.\s+', '', text.strip(), count=1)
    lines = text.split('\n')
    kept = []
    refs = []
    for ln in lines:
        ln = ln.strip()
        if not ln:
            continue
        if _is_reference_line(ln):
            for r in BOOK_REF.findall(ln):
                if r.strip():
                    refs.append(r.strip())
            continue
        ln = _strip_all_references(ln)
        if ln.strip():
            kept.append(ln)
    t = '\n'.join(kept)
    for m in REF_SPAN.finditer(t):
        for r in BOOK_REF.findall(m.group()):
            if r.strip():
                refs.append(r.strip())
    t = _strip_all_references(t)
    t = BOOK_ABBREV_STANDALONE.sub(r'\1', t)
    t = re.sub(r'[*_**†]+\s*,\s*\d+\s*', ' ', t)
    t = re.sub(r'\*\*', ' ', t)
    t = re.sub(r'\*', ' ', t)
    t = re.sub(r'†', ' ', t)
    t = re.sub(r'_(?=\s|$)', ' ', t)
    t = re.sub(r'\s+', ' ', t).strip()
    return t, refs if refs else None

def _looks_like_title_format(block):
    """True if block has title-like formatting (larger font or non-black)."""
    if not block:
        return False
    return (float(block.get('font_size', BODY_FONT_SIZE)) > TITLE_FONT_THRESHOLD or
            block.get('is_non_black', False))

def _split_verse_by_character_speech(verse_text):
    """Split verse into narrator/character segments. Returns [(role, text, char_name, refs?), ...]."""
    clean, refs = _clean_verse_text(verse_text)
    if not clean:
        return []
    parts = []
    last_end = 0
    for m in QUOTED_SPEECH.finditer(clean):
        before = clean[last_end:m.start()].strip()
        if before:
            parts.append({'role': 'narrator', 'text': before, 'character_name': None, 'references': refs if not parts else None})
        quoted = (m.group(0) or '').strip()
        if quoted:
            parts.append({'role': 'character', 'text': quoted, 'character_name': 'Dumnezeu', 'references': None})
        last_end = m.end()
    after = clean[last_end:].strip()
    if after:
        parts.append({'role': 'narrator', 'text': after, 'character_name': None, 'references': refs if not parts else None})
    if not parts:
        return [{'role': 'narrator', 'text': clean, 'character_name': None, 'references': refs}]
    if refs and not any(p.get('references') for p in parts):
        parts[0]['references'] = refs
    return parts

def _infer_preamble_type(text):
    t = (text or "").strip()
    if re.match(r'^(?:Capitolul|Chapter)\s+\d+', t, re.I):
        return 'chapter_number'
    if len(t.split()) == 1 and t.isupper():
        return 'book_title'
    if len(t) > 50:
        return 'chapter_name'
    return 'section_title'

def _looks_like_chapter_name(text):
    """Verse content that is actually a chapter subtitle (e.g. '1. Cei şaptezeci ani – Pedepsirea...')."""
    if not text or len(text) < 40:
        return False
    t = text.strip()
    if re.search(r'(?:Dumnezeu|„|"|să fie|să (?:dea|despartă|slujească|stăpânească))', t, re.I):
        return False
    m = re.match(r'^\d+\.\s+(.+)$', t)
    content = m.group(1).strip() if m else t
    if len(content) < 35:
        return False
    if ' – ' in content or ' — ' in content or (' - ' in content and len(content) > 50):
        return True
    if re.search(r'(?:ani de|pedepsirea|facerea lumii|vremurile străvechi|până la)', content, re.I):
        return len(content) > 50
    return False

def _use_vertex_ai():
    api_key = current_app.config.get('GOOGLE_API_KEY')
    use_vertex = current_app.config.get('GOOGLE_GENAI_USE_VERTEXAI', False)
    return bool(api_key and use_vertex)

def _has_new_genai():
    try:
        from google import genai  # noqa: F401
        return True
    except ImportError:
        return False

def _ensure_vertex_env():
    if not _use_vertex_ai():
        return
    api_key = current_app.config.get('GOOGLE_API_KEY')
    if api_key and 'GOOGLE_API_KEY' not in os.environ:
        os.environ['GOOGLE_API_KEY'] = api_key
    if current_app.config.get('GOOGLE_GENAI_USE_VERTEXAI'):
        os.environ['GOOGLE_GENAI_USE_VERTEXAI'] = 'True'

def _gemini_client():
    from google import genai
    from google.genai.types import HttpOptions

    if _use_vertex_ai():
        _ensure_vertex_env()
        return genai.Client(http_options=HttpOptions(api_version="v1"))
    api_key = (
        current_app.config.get('GOOGLE_GEMINI_API_KEY') or current_app.config.get('GEMINI_API_KEY')
    )
    if not api_key:
        raise ValueError(
            "Set GOOGLE_GEMINI_API_KEY or GEMINI_API_KEY (AI Studio API key from aistudio.google.com)"
        )
    saved = {
        k: os.environ.pop(k, None)
        for k in (
            "GOOGLE_APPLICATION_CREDENTIALS",
            "GOOGLE_GENAI_USE_VERTEXAI",
            "GOOGLE_CLOUD_PROJECT",
            "GOOGLE_CLOUD_LOCATION",
        )
    }
    try:
        return genai.Client(api_key=api_key)
    finally:
        for k, v in saved.items():
            if v is not None:
                os.environ[k] = v

def _default_model():
    return current_app.config.get('GEMINI_MODEL_ID') or 'gemini-3-flash-preview'

def _generate_config():
    from google.genai import types
    level = current_app.config.get('GEMINI_THINKING_LEVEL')
    if not level:
        return None
    try:
        if hasattr(types, 'ThinkingConfig'):
            return types.GenerateContentConfig(thinking_config=types.ThinkingConfig(thinking_level=level))
        return types.GenerateContentConfig(thinking_config={'thinking_level': level})
    except Exception:
        return None

def _build_classification_prompt(blocks):
    lines = []
    for i, b in enumerate(blocks):
        lines.append(f"[{i+1}] {b['text'][:500]}{'...' if len(b.get('text','')) > 500 else ''}")
    return f"""The text below is PRE-SPLIT into blocks. Each verse starts with "N. " (e.g. "1.", "22."). Your job is ONLY to assign role, character_name, chunk_type, and references.

For each block, return one JSON object. Order must match exactly.

RULES:
- role: "narrator" or "character" (verses with direct speech → "character", name in character_name)
- chunk_type: "book_title"|"chapter_number"|"chapter_name"|"section_title"|"verse"
- references: for verses, extract refs like Ioan 1:1, Ps. 8:3 into array; else null
- Do NOT change, split, or merge any block text

Blocks:
{chr(10).join(lines)}

Return JSON array only: [{{"role":"narrator","character_name":null,"chunk_type":"verse","references":null}}, ...]"""

def _call_gemini_for_classification(blocks):
    from google import genai
    client = _gemini_client()
    model_id = _default_model()
    prompt = _build_classification_prompt(blocks)
    config = _generate_config()
    kwargs = dict(model=model_id, contents=prompt)
    if config is not None:
        kwargs['config'] = config
    response = client.models.generate_content(**kwargs)
    response_text = (getattr(response, 'text', None) or "").strip()
    if not response_text:
        raise ValueError("Gemini returned no text.")
    if response_text.startswith('```'):
        response_text = response_text.split('```')[1]
        if response_text.startswith('json'):
            response_text = response_text[4:]
        response_text = response_text.strip()
    classifications = json.loads(response_text)
    if not isinstance(classifications, list):
        classifications = [classifications]
    return classifications

def _call_gemini_new(text):
    from google import genai

    client = _gemini_client()
    model_id = _default_model()
    prompt = _build_prompt(text)
    config = _generate_config()
    kwargs = dict(model=model_id, contents=prompt)
    if config is not None:
        kwargs['config'] = config
    response = client.models.generate_content(**kwargs)
    response_text = (getattr(response, 'text', None) or "").strip()
    if not response_text:
        raise ValueError(
            "Gemini returned no text. Check your API key and that the model is available in your project."
        )
    return _parse_response(response_text)

def _call_gemini(text):
    if not _has_new_genai():
        raise ImportError(
            "Gemini requires google-genai. Run: py -m pip install google-genai"
        )
    return _call_gemini_new(text)

def _build_prompt(text):
    return f"""Analyze this Bible text and identify narrator and character speech. Create SEPARATE chunks for each distinct element.

CHUNK TYPES (create separate chunks for each):
1. Book title: Standalone book names in ALL CAPS or title case (e.g., "GENEZA", "Geneza") → chunk_type: "book_title"
2. Chapter number: Lines like "Capitolul 1", "Chapter 1", "Capitolul 2" → chunk_type: "chapter_number"
3. Chapter name/subtitle: Descriptive text after chapter number (e.g., "Vremurile străvechi de la facerea lumii până la Avraam") → chunk_type: "chapter_name"
4. Section titles: Short descriptive titles (e.g., "Facerea lumii", "Lumina", "Cerul", "Pământul") → chunk_type: "section_title"
5. Verses: Numbered verses with text (e.g., "1. La început, Dumnezeu a făcut cerurile şi pământul.") → chunk_type: "verse"
6. Character speech: Direct quotes from characters (e.g., Dumnezeu says "Să fie lumină!") → chunk_type: "verse", role: "character"

RULES:
- Extract verse references separately. Reference lines look like "Ioan 1:1, 2; Evr. 1:10. **Ps. 8:3; Ps. 33:6; ..." or " *Ps. 33:6; Isa. 40:13"
- For each verse chunk, extract its references into a "references" array. Parse references like: "Ioan 1:1, 2" → ["Ioan 1:1", "Ioan 1:2"], "Ps. 8:3" → ["Ps. 8:3"]
- Remove footnote markers (\\*, \\**, †, _) from the main text, but extract references before removing markers.
- The "text" field should be clean for speech (no reference lines, no footnote symbols).
- Each verse (with its number) should be ONE separate chunk.
- Book titles, chapter numbers, and chapter names must be separate chunks, not combined.
- Section titles are typically short phrases (1-5 words) that describe a section.

Return JSON with this exact structure:
{{
  "chunks": [
    {{
      "text": "clean text to be read aloud (no reference lines, no footnote symbols)",
      "role": "narrator" or "character",
      "character_name": null or "character name",
      "chunk_type": "book_title" or "chapter_number" or "chapter_name" or "section_title" or "verse",
      "references": ["Ioan 1:1", "Evr. 1:10", "Ps. 8:3"] or null (only for verse chunks with references),
      "position": 1
    }}
  ]
}}

Text to analyze:
{text}

Return only valid JSON, no additional text."""

def _parse_response(response_text):
    if response_text.startswith('```json'):
        response_text = response_text.replace('```json', '').replace('```', '').strip()
    elif response_text.startswith('```'):
        response_text = response_text.replace('```', '').strip()

    result = json.loads(response_text)
    if 'chunks' not in result:
        raise ValueError("Invalid response format: missing 'chunks' key")

    for i, chunk in enumerate(result['chunks'], start=1):
        if 'position' not in chunk:
            chunk['position'] = i
        if 'chunk_type' not in chunk:
            chunk['chunk_type'] = 'verse'
        if 'references' not in chunk:
            chunk['references'] = None
    return result['chunks']

def analyze_text_chunks(text=None, format_lines=None):
    verse_refs, preamble_refs = {}, {}
    if format_lines:
        verse_refs, preamble_refs = _scan_references_from_format_lines(format_lines)
        blocks = _split_from_format_lines(format_lines)
        text = '\n'.join(l.get('text', '') for l in format_lines)
    else:
        if not (text or "").strip():
            raise ValueError("No text provided to analyze")
        blocks = _split_by_verse_numbers(text)
    if not blocks:
        return []
    try:
        chunks = []
        pos = 0
        for b in blocks:
            if b['type'] == 'verse':
                segments = _split_verse_by_character_speech(b['text'])
                verse_segments = [
                    {'text': s['text'], 'role': s['role'], 'character_name': s.get('character_name')}
                    for s in segments if (s.get('text') or '').strip()
                ]
                if not verse_segments:
                    continue
                clean_first = _strip_all_references((verse_segments[0].get('text') or '').strip())
                if len(clean_first) < 4 or REF_ORPHAN_ABBREV.match(clean_first):
                    continue
                block_text = (b.get('text') or '').strip()
                m = re.match(r'^(\d+)\.\s+', block_text)
                verse_num = m.group(1) if m else b.get('verse_num')
                ref_from_pdf = verse_refs.get(verse_num) if verse_num else None
                refs = ref_from_pdf or (segments[0].get('references') if segments else None)
                if refs and isinstance(refs, list):
                    refs = '; '.join(refs) if refs else None
                pos += 1
                chunks.append({
                    'chunk_type': 'verse',
                    'verse_num': verse_num,
                    'references': refs,
                    'position': pos,
                    'segments': verse_segments
                })
                continue
            raw = (b['text'] or '').strip()
            clean_text = _strip_all_references(raw)
            clean_text = re.sub(r'\s+', ' ', clean_text)
            chunk_type = _infer_preamble_type(b['text'])
            pre_ref = _find_preamble_ref(preamble_refs, raw) if preamble_refs else None
            pos += 1
            chunks.append({
                'chunk_type': chunk_type,
                'references': pre_ref,
                'position': pos,
                'segments': [{'text': clean_text or b['text'], 'role': 'narrator', 'character_name': None}]
            })

        if chunks and _has_new_genai() and not format_lines:
            try:
                classifications = _call_gemini_for_classification(blocks)
                for i, c in enumerate(classifications):
                    if i < len(chunks):
                        ch, segs = chunks[i], (chunks[i].get('segments') or [])
                        if len(segs) == 1 and c.get('role'):
                            segs[0]['role'] = c['role']
                        if len(segs) == 1 and 'character_name' in c:
                            segs[0]['character_name'] = c['character_name']
                        if c.get('chunk_type'):
                            ch['chunk_type'] = c['chunk_type']
                        if 'references' in c:
                            ch['references'] = c['references'] or ch.get('references')
            except (json.JSONDecodeError, ValueError, Exception):
                pass

        for c in chunks:
            segs = c.get('segments') or []
            first_text = segs[0].get('text', '') if segs else c.get('text', '')
            if c.get('chunk_type') == 'verse' and _looks_like_chapter_name(first_text):
                c['chunk_type'] = 'chapter_name'

        for i, c in enumerate(chunks, start=1):
            c['position'] = i

        last_verse_num = None
        for c in chunks:
            if c.get('chunk_type') != 'verse':
                continue
            vn = c.get('verse_num')
            if vn and str(vn).isdigit():
                v = int(vn)
                if last_verse_num is not None:
                    if v <= last_verse_num:
                        last_verse_num += 1
                        c['verse_num'] = str(last_verse_num)
                    elif v > last_verse_num + 1:
                        last_verse_num += 1
                        c['verse_num'] = str(last_verse_num)
                    else:
                        last_verse_num = v
                else:
                    last_verse_num = v
        return chunks
    except (ValueError, json.JSONDecodeError):
        raise
    except Exception as e:
        raise Exception(f"Gemini API error: {e}") from e

def _batch_format_lines(format_lines, max_chunk_size=30000):
    batches = []
    current = []
    current_len = 0
    i = 0
    while i < len(format_lines):
        line = format_lines[i]
        t = (line.get('text') or '').strip()
        if not t:
            i += 1
            continue
        line_len = len(t) + 1
        if current_len + line_len > max_chunk_size and current and VERSE_START.match(t):
            batches.append(current)
            current = []
            current_len = 0
        current.append(line)
        current_len += line_len
        i += 1
    if current:
        batches.append(current)
    return batches

def analyze_text_in_batches(text=None, format_lines=None, max_chunk_size=30000):
    if format_lines:
        joined = '\n'.join(l.get('text', '') for l in format_lines)
        if len(joined) <= max_chunk_size:
            all_chunks = analyze_text_chunks(format_lines=format_lines)
        else:
            batches = _batch_format_lines(format_lines, max_chunk_size)
            all_chunks = []
            for batch in batches:
                all_chunks.extend(analyze_text_chunks(format_lines=batch))
    else:
        if not (text or "").strip():
            return []
        if len(text) <= max_chunk_size:
            all_chunks = analyze_text_chunks(text)
        else:
            verse_starts = [0] + [m.start() for m in VERSE_START.finditer(text)] + [len(text)]
            batch_texts = []
            idx = 0
            while idx < len(verse_starts) - 1:
                start = verse_starts[idx]
                j = idx + 1
                while j < len(verse_starts) and verse_starts[j] - start <= max_chunk_size:
                    j += 1
                end = verse_starts[min(j, len(verse_starts) - 1)]
                batch_texts.append(text[start:end])
                idx = min(j, len(verse_starts) - 1)
            all_chunks = []
            for part in batch_texts:
                if part.strip():
                    all_chunks.extend(analyze_text_chunks(part))

    for i, c in enumerate(all_chunks, start=1):
        c['position'] = i
    return all_chunks
