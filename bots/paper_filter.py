"""Evidence-based preference ranking of keyword-matched arXiv candidates."""
import hashlib
import io
import json
import logging
import re
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from urllib.request import Request, urlopen

from pypdf import PdfReader

from . import CONFIGS_DIR

CONFIG_PATH = CONFIGS_DIR / 'paper_preferences.json'
GROUPS = ('companies', 'institutions', 'venues')
MAX_PDF_BYTES = 50_000_000
LOGGER = logging.getLogger(__name__)


def paper_id(result) -> str:
    """Canonical identity excludes versions, protocols and abs/pdf URL differences."""
    value = getattr(result, 'entry_id', '') or getattr(result, 'pdf_url', '') or ''
    value = re.sub(r'^https?://[^/]+/(?:abs|pdf)/', '', value)
    return re.sub(r'v\d+$', '', value.removesuffix('.pdf'))


def normalize(text: str) -> str:
    return re.sub(r'\s+', ' ', text).strip().casefold()


def alias_pattern(alias: str) -> str:
    return r'(?<!\w)' + re.escape(normalize(alias)) + r'(?!\w)'


def match_names(text: str, names: dict) -> list[str]:
    text = normalize(text)
    return [name for name, aliases in names.items()
            if any(re.search(alias_pattern(alias), text) for alias in aliases)]


def author_header(text: str, result) -> str:
    """Only inspect the author block preceding Abstract, never the paper body."""
    title = getattr(result, 'title', '') or ''
    if title.strip():
        title_pattern = r'\s+'.join(re.escape(word) for word in title.split())
        text = re.sub(title_pattern, '', text, flags=re.IGNORECASE)
    for author in getattr(result, 'authors', []):
        name = getattr(author, 'name', '') or ''
        if name.strip():
            name_pattern = r'\s+'.join(re.escape(word) for word in name.split())
            text = re.sub(name_pattern, '', text, flags=re.IGNORECASE)
    abstract = re.search(r'^\s*(?:abstract\b|摘\s*要)', text, flags=re.IGNORECASE | re.MULTILINE)
    # Without a section boundary, the whole first page is unsafe affiliation evidence.
    return normalize(text[:abstract.start()]) if abstract else ''


def accepted_venues(result, names: dict) -> list[str]:
    """Use author-reported publication metadata; exclude submission/workshop claims."""
    matches = set()
    negative = r'\b(?:submitted|submission|under review|rejected|withdrawn|workshops?)\b|\bnot\s+accepted\b'
    status = r'(?:accepted\s+(?:at|to|by|for)|to\s+appear\s+(?:at|in)|published\s+(?:at|in)|appeared\s+(?:at|in))'
    for field in ('journal_ref', 'comment'):
        text = normalize(getattr(result, field, '') or '')
        for clause in re.split(r'[;\n]|(?<=[.!?])\s+', text):
            if re.search(negative, clause):
                continue
            for name, aliases in names.items():
                for alias in aliases:
                    venue = alias_pattern(alias)
                    if not re.search(venue, clause):
                        continue
                    if field == 'journal_ref' or re.search(
                        status + r'\s+(?:the\s+)?(?:proceedings\s+of\s+(?:the\s+)?)?(?:ieee(?:/cvf)?\s+)?' + venue, clause
                    ) or re.search(
                        venue + r'\s*(?:20\d{2})?\s*[(:,-]?\s*accepted\b', clause
                    ):
                        matches.add(name)
    return [name for name in names if name in matches]


@dataclass
class RankedPaper:
    result: object
    companies: list[str]
    institutions: list[str]
    venues: list[str]
    affiliation_source: str

    def reason(self) -> str:
        parts = []
        for group in GROUPS:
            names = getattr(self, group)
            if names:
                parts.append(f'{group}={", ".join(names)}')
        if self.companies or self.institutions:
            parts.append(f'affiliations={self.affiliation_source}')
        return '; '.join(parts) or 'no verified preference signal; recency fallback'


class PaperRanker:
    def __init__(self, cache_dir: Path, config_path: Path = CONFIG_PATH):
        self.config = json.loads(Path(config_path).read_text(encoding='utf-8'))
        self._validate_config()
        self.cache_dir = Path(cache_dir)
        self._last_request = time.monotonic()

    def _validate_config(self):
        cfg = self.config
        order = cfg.get('priority_order')
        if not isinstance(order, list) or len(order) != 3 or set(order) != set(GROUPS):
            raise ValueError('priority_order must contain companies, institutions and venues once each.')
        for key in ('candidate_multiplier', 'max_candidates_per_query'):
            if type(cfg.get(key)) is not int or cfg[key] < 1:
                raise ValueError(f'{key} must be a positive integer.')
        delay = cfg.get('request_delay_seconds')
        if type(delay) not in (int, float) or delay < 3:
            raise ValueError('request_delay_seconds must be at least 3.')
        if type(cfg.get('inspect_pdf_affiliations')) is not bool:
            raise ValueError('inspect_pdf_affiliations must be true or false.')
        for group in GROUPS:
            if not isinstance(cfg.get(group), dict):
                raise ValueError(f'{group} must map names to alias lists.')
            for name, aliases in cfg[group].items():
                if not name or not isinstance(aliases, list) or not aliases or not all(
                    isinstance(alias, str) and alias.strip() for alias in aliases
                ):
                    raise ValueError(f'{group}.{name} must have nonempty string aliases.')

    def candidate_count(self, limit: int) -> int:
        return max(limit, min(limit * self.config['candidate_multiplier'],
                              self.config['max_candidates_per_query']))

    def note_api_request(self):
        self._last_request = time.monotonic()

    def _pdf_header(self, result) -> str:
        url = getattr(result, 'pdf_url', None)
        if not url:
            return ''
        # Include the versioned URL in the cache key so updated affiliations are re-read.
        digest = hashlib.sha256(url.encode()).hexdigest()
        path = self.cache_dir / (digest + '.json')
        try:
            cached = json.loads(path.read_text(encoding='utf-8'))
            if isinstance(cached, dict) and isinstance(cached.get('header'), str):
                return cached['header']
        except (OSError, ValueError):
            pass
        delay = self.config['request_delay_seconds'] - (time.monotonic() - self._last_request)
        if delay > 0:
            time.sleep(delay)
        self._last_request = time.monotonic()
        request = Request(url, headers={'User-Agent': 'WorkflowBot/1.0'})
        with urlopen(request, timeout=90) as response:
            data = response.read(MAX_PDF_BYTES)
        if len(data) >= MAX_PDF_BYTES or b'%PDF-' not in data[:1024]:
            raise ValueError('Affiliation inspection requires a PDF smaller than 50 MB.')
        reader = PdfReader(io.BytesIO(data))
        text = reader.pages[0].extract_text() if reader.pages else ''
        header = author_header(text or '', result)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        try:
            path.write_text(json.dumps({'header': header}, ensure_ascii=False), encoding='utf-8')
        except OSError as error:
            LOGGER.warning('Cannot cache affiliations for %s: %s', paper_id(result), error)
        return header

    def inspect(self, result) -> RankedPaper:
        affiliations = []
        for author in getattr(result, 'authors', []):
            values = getattr(author, 'affiliation', []) or []
            affiliations.extend([values] if isinstance(values, str) else values)
        text = '\n'.join(affiliations)
        source = 'arXiv author metadata' if text else 'unknown'
        # PDF author block also finds coauthors omitted from sparse API affiliations.
        if self.config['inspect_pdf_affiliations']:
            try:
                header = self._pdf_header(result)
                if header:
                    text += '\n' + header
                    source = 'author metadata / PDF header' if affiliations else 'PDF header'
            except Exception as error:
                # Missing signals lower preference, but never discard a relevant paper.
                LOGGER.warning('Affiliations unavailable for %s: %s', paper_id(result), error)
        return RankedPaper(result, match_names(text, self.config['companies']),
                           match_names(text, self.config['institutions']),
                           accepted_venues(result, self.config['venues']), source)

    def rank(self, results: list) -> list[RankedPaper]:
        ranked = [self.inspect(result) for result in results]
        def key(paper):
            preference = tuple(bool(getattr(paper, group)) for group in self.config['priority_order'])
            date = getattr(paper.result, 'published', None)
            recency = date.timestamp() if isinstance(date, datetime) else 0
            return preference + (recency,)
        return sorted(ranked, key=key, reverse=True)
