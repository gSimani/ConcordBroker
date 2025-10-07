"""
Firecrawl integration for website scraping
"""
from typing import List, Dict, Optional
from bs4 import BeautifulSoup
import re
import asyncio
from .config import config


class FirecrawlScraper:
    """Scrapes website using Firecrawl and extracts label-field pairs"""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or config.FIRECRAWL_API_KEY
        # Note: Install firecrawl-py: pip install firecrawl-py
        try:
            from firecrawl import FirecrawlApp
            self.firecrawl = FirecrawlApp(api_key=self.api_key)
        except ImportError:
            print("Warning: firecrawl-py not installed. Install with: pip install firecrawl-py")
            self.firecrawl = None

    async def crawl_website(
        self,
        url: str,
        max_pages: int = None,
        depth: int = None
    ) -> List[Dict]:
        """Crawl entire website and return all pages"""
        max_pages = max_pages or config.CRAWL_MAX_PAGES
        depth = depth or config.CRAWL_DEPTH

        if not self.firecrawl:
            print("Firecrawl not available, using fallback scraping")
            return await self._fallback_scrape(url)

        try:
            # Start crawl
            crawl_result = self.firecrawl.crawl_url(
                url,
                params={
                    'crawlerOptions': {
                        'excludes': [],
                        'includes': [],
                        'limit': max_pages,
                        'maxDepth': depth
                    },
                    'pageOptions': {
                        'onlyMainContent': False,
                        'includeHtml': True
                    }
                }
            )

            pages = []
            if crawl_result and 'data' in crawl_result:
                for page in crawl_result['data']:
                    pages.append({
                        'url': page.get('metadata', {}).get('sourceURL', ''),
                        'title': page.get('metadata', {}).get('title', ''),
                        'html': page.get('html', ''),
                        'markdown': page.get('markdown', ''),
                        'metadata': page.get('metadata', {})
                    })

            return pages

        except Exception as e:
            print(f"Error crawling with Firecrawl: {e}")
            return await self._fallback_scrape(url)

    async def _fallback_scrape(self, url: str) -> List[Dict]:
        """Fallback scraping using Playwright if Firecrawl unavailable"""
        # Use Playwright MCP for dynamic content
        from playwright.async_api import async_playwright

        pages = []

        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page()

            await page.goto(url)
            html = await page.content()

            pages.append({
                'url': url,
                'title': await page.title(),
                'html': html,
                'markdown': '',  # Could use html2text if needed
                'metadata': {}
            })

            await browser.close()

        return pages

    def extract_label_field_pairs(self, html: str, page_url: str) -> List[Dict]:
        """Extract all label-field pairs from HTML"""
        soup = BeautifulSoup(html, 'lxml')
        pairs = []

        # Pattern 1: <label> + input/select/textarea
        pairs.extend(self._extract_label_input_pairs(soup, page_url))

        # Pattern 2: Class-based (field-label + field-value)
        pairs.extend(self._extract_class_based_pairs(soup, page_url))

        # Pattern 3: Inline text (Label: Value)
        pairs.extend(self._extract_inline_pairs(soup, page_url))

        # Pattern 4: Data attributes
        pairs.extend(self._extract_data_attribute_pairs(soup, page_url))

        # Pattern 5: Table rows
        pairs.extend(self._extract_table_pairs(soup, page_url))

        return pairs

    def _extract_label_input_pairs(self, soup: BeautifulSoup, page_url: str) -> List[Dict]:
        """Extract <label>Text</label><input> patterns"""
        pairs = []

        for label in soup.find_all('label'):
            label_text = label.get_text(strip=True)
            if not label_text:
                continue

            # Check for associated input via 'for' attribute
            input_id = label.get('for')
            if input_id:
                field = soup.find(id=input_id)
                if field:
                    pairs.append(self._create_pair(
                        label_text,
                        field.get('value', ''),
                        f"#{input_id}",
                        page_url,
                        "label_input"
                    ))
                    continue

            # Check for adjacent input
            next_element = label.find_next_sibling(['input', 'select', 'textarea'])
            if next_element:
                value = next_element.get('value', '') or next_element.get_text(strip=True)
                selector = self._get_selector(next_element)
                pairs.append(self._create_pair(
                    label_text,
                    value,
                    selector,
                    page_url,
                    "label_adjacent"
                ))

        return pairs

    def _extract_class_based_pairs(self, soup: BeautifulSoup, page_url: str) -> List[Dict]:
        """Extract pairs based on CSS classes (label/value classes)"""
        pairs = []

        label_classes = config.EXTRACTION_PATTERNS[1]['label_classes']
        value_classes = config.EXTRACTION_PATTERNS[1]['value_classes']

        for label_class in label_classes:
            labels = soup.find_all(class_=re.compile(label_class))

            for label in labels:
                label_text = label.get_text(strip=True)
                if not label_text:
                    continue

                # Look for value in next sibling
                for value_class in value_classes:
                    value_elem = label.find_next_sibling(class_=re.compile(value_class))
                    if value_elem:
                        value = value_elem.get_text(strip=True)
                        selector = self._get_selector(value_elem)
                        pairs.append(self._create_pair(
                            label_text,
                            value,
                            selector,
                            page_url,
                            "class_based"
                        ))
                        break

        return pairs

    def _extract_inline_pairs(self, soup: BeautifulSoup, page_url: str) -> List[Dict]:
        """Extract inline patterns like 'Label: Value'"""
        pairs = []

        # Find all text nodes
        text_elements = soup.find_all(['div', 'p', 'span', 'li'])

        for elem in text_elements:
            text = elem.get_text(strip=True)
            # Match pattern "Label: Value"
            matches = re.findall(r'([^:]{2,30}):\s*([^:]{1,100})(?:\s|$)', text)

            for label_text, value in matches:
                label_text = label_text.strip()
                value = value.strip()

                if label_text and value and len(label_text) < 50:
                    selector = self._get_selector(elem)
                    pairs.append(self._create_pair(
                        label_text,
                        value,
                        selector,
                        page_url,
                        "inline_text"
                    ))

        return pairs

    def _extract_data_attribute_pairs(self, soup: BeautifulSoup, page_url: str) -> List[Dict]:
        """Extract pairs from data attributes"""
        pairs = []

        # Find elements with data-label attributes
        labeled_elements = soup.find_all(attrs={"data-label": True})

        for elem in labeled_elements:
            label_text = elem.get('data-label', '')
            value = elem.get('data-value', '') or elem.get_text(strip=True)

            if label_text and value:
                selector = self._get_selector(elem)
                pairs.append(self._create_pair(
                    label_text,
                    value,
                    selector,
                    page_url,
                    "data_attribute"
                ))

        return pairs

    def _extract_table_pairs(self, soup: BeautifulSoup, page_url: str) -> List[Dict]:
        """Extract label-value pairs from tables"""
        pairs = []

        tables = soup.find_all('table')

        for table in tables:
            rows = table.find_all('tr')

            for row in rows:
                cells = row.find_all(['td', 'th'])

                if len(cells) == 2:
                    label_text = cells[0].get_text(strip=True)
                    value = cells[1].get_text(strip=True)

                    if label_text and value:
                        selector = self._get_selector(cells[1])
                        pairs.append(self._create_pair(
                            label_text,
                            value,
                            selector,
                            page_url,
                            "table_row"
                        ))

        return pairs

    def _create_pair(
        self,
        label: str,
        value: str,
        selector: str,
        page_url: str,
        pattern_type: str
    ) -> Dict:
        """Create a standardized label-field pair dictionary"""
        return {
            'page_url': page_url,
            'label': label,
            'value': value,
            'selector': selector,
            'pattern_type': pattern_type,
            'data_type': self._infer_data_type(value)
        }

    def _get_selector(self, element) -> str:
        """Generate CSS selector for an element"""
        if element.get('id'):
            return f"#{element.get('id')}"
        elif element.get('class'):
            classes = '.'.join(element.get('class'))
            return f"{element.name}.{classes}"
        else:
            return element.name

    def _infer_data_type(self, value: str) -> str:
        """Infer data type from value"""
        if not value:
            return "empty"

        # Try to identify data type
        if re.match(r'^\$?[\d,]+\.?\d*$', value):
            return "currency"
        elif re.match(r'^\d+$', value):
            return "integer"
        elif re.match(r'^\d+\.\d+$', value):
            return "decimal"
        elif re.match(r'^\d{1,2}/\d{1,2}/\d{2,4}$', value):
            return "date"
        elif re.match(r'^\d{4}-\d{2}-\d{2}$', value):
            return "date_iso"
        elif value.lower() in ['yes', 'no', 'true', 'false']:
            return "boolean"
        else:
            return "text"

    def extract_property_id(self, url: str) -> Optional[str]:
        """Extract property ID from URL"""
        for pattern in config.PROPERTY_URL_PATTERNS:
            match = re.search(pattern, url)
            if match:
                return match.group(1)

        return None
