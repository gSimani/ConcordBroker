"""
Advanced PIL/Pillow Image Processing for Visual Data Verification
Comprehensive computer vision system for validating data placement across all tabs
"""

from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageFilter, ImageOps
import numpy as np
import cv2
import pytesseract
import asyncio
import logging
from typing import Dict, List, Tuple, Any, Optional, NamedTuple
from dataclasses import dataclass, field
from datetime import datetime
import json
import re
from pathlib import Path
import base64
from io import BytesIO
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.cluster import DBSCAN
from scipy import ndimage
import hashlib

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class FieldLocation:
    """Represents a detected field location in the image"""
    field_name: str
    bounding_box: Tuple[int, int, int, int]  # (x1, y1, x2, y2)
    confidence: float
    text_content: str
    value_content: str
    data_type: str
    tab_section: str

@dataclass
class VisualVerificationResult:
    """Result of visual verification analysis"""
    image_path: str
    tab_name: str
    fields_detected: List[FieldLocation]
    accuracy_score: float
    missing_fields: List[str]
    misaligned_fields: List[str]
    color_analysis: Dict[str, Any]
    layout_analysis: Dict[str, Any]
    recommendations: List[str]
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

class PILVisualVerificationSystem:
    """Advanced PIL/Pillow system for visual data verification"""

    def __init__(self):
        # Initialize fonts for text rendering analysis
        self.fonts = self._load_fonts()

        # Field patterns for each tab
        self.field_patterns = self._initialize_field_patterns()

        # Color schemes for validation
        self.color_schemes = self._initialize_color_schemes()

        # OCR configuration
        self.ocr_config = '--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz$,.%-/: '

        # Results cache
        self.verification_cache = {}

    def _load_fonts(self) -> Dict[str, ImageFont.FreeTypeFont]:
        """Load fonts for text analysis"""
        fonts = {}
        try:
            # Try to load common system fonts
            font_paths = [
                "C:/Windows/Fonts/arial.ttf",
                "C:/Windows/Fonts/calibri.ttf",
                "/System/Library/Fonts/Arial.ttf",  # macOS
                "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",  # Linux
            ]

            for path in font_paths:
                if Path(path).exists():
                    fonts['regular'] = ImageFont.truetype(path, 12)
                    fonts['bold'] = ImageFont.truetype(path, 14)
                    break
            else:
                # Fallback to default font
                fonts['regular'] = ImageFont.load_default()
                fonts['bold'] = ImageFont.load_default()
        except Exception as e:
            logger.warning(f"Could not load fonts: {e}")
            fonts['regular'] = ImageFont.load_default()
            fonts['bold'] = ImageFont.load_default()

        return fonts

    def _initialize_field_patterns(self) -> Dict[str, Dict[str, Any]]:
        """Initialize field detection patterns for each tab"""
        return {
            'overview': {
                'address_patterns': [
                    r'\d+\s+[A-Za-z\s]+(?:St|Street|Ave|Avenue|Rd|Road|Dr|Drive|Blvd|Boulevard)',
                    r'[A-Za-z\s]+,\s*FL\s*\d{5}'
                ],
                'value_patterns': [
                    r'\$[\d,]+',
                    r'[\d,]+\s*sq\s*ft',
                    r'\d{4}-\d{2}-\d{2}'
                ],
                'expected_fields': [
                    'Site Address', 'Property Owner', 'Parcel ID', 'Just Value',
                    'Taxable Value', 'Land Value', 'Most Recent Sale'
                ]
            },
            'core-property': {
                'owner_patterns': [
                    r'[A-Z][a-z]+\s+[A-Z][a-z]+',
                    r'[A-Z][A-Z\s]+LLC',
                    r'[A-Z][A-Z\s]+CORP'
                ],
                'measurement_patterns': [
                    r'\d+\s*sq\s*ft',
                    r'\d+\s*[Xx]\s*\d+',
                    r'\d+\.\d+\s*acres'
                ],
                'expected_fields': [
                    'Site Address', 'Property Owner', 'Parcel ID', 'Property Use',
                    'Current Land Value', 'Building/Improvement', 'Just/Market Value',
                    'Assessed/SOH Value', 'Annual Tax', 'Adj. Bldg. S.F.'
                ]
            },
            'valuation': {
                'currency_patterns': [
                    r'\$[\d,]+\.?\d*',
                    r'[\d,]+\.?\d*'
                ],
                'expected_fields': [
                    'Just Value', 'Assessed Value', 'Taxable Value',
                    'Building Area', 'Year Built'
                ]
            },
            'taxes': {
                'tax_patterns': [
                    r'\$[\d,]+\.?\d*',
                    r'\d+\.?\d*%',
                    r'Active|Inactive'
                ],
                'expected_fields': [
                    'Tax Amount', 'Millage Rate', 'Exemptions', 'Homestead'
                ]
            },
            'sunbiz': {
                'entity_patterns': [
                    r'[A-Z][A-Z\s]+LLC',
                    r'[A-Z][A-Z\s]+CORP',
                    r'[A-Z][A-Z\s]+INC',
                    r'Active|Inactive'
                ],
                'expected_fields': [
                    'Business Entity Name', 'Document Number', 'Entity Status',
                    'Filing Date', 'Registered Agent'
                ]
            }
        }

    def _initialize_color_schemes(self) -> Dict[str, Dict[str, Tuple[int, int, int]]]:
        """Initialize expected color schemes for verification"""
        return {
            'primary_text': (31, 41, 55),  # Navy blue
            'secondary_text': (107, 114, 128),  # Gray
            'accent_color': (251, 191, 36),  # Gold
            'success_color': (16, 185, 129),  # Green
            'error_color': (239, 68, 68),  # Red
            'background': (255, 255, 255),  # White
            'card_background': (249, 250, 251)  # Light gray
        }

    async def analyze_screenshot(self, image_path: str, tab_name: str,
                                expected_data: Dict[str, Any]) -> VisualVerificationResult:
        """Comprehensive analysis of a screenshot"""

        # Load and preprocess image
        image = Image.open(image_path)
        processed_image = await self._preprocess_image(image)

        # Detect fields using multiple techniques
        detected_fields = await self._detect_fields_comprehensive(
            processed_image, tab_name, expected_data
        )

        # Analyze layout and structure
        layout_analysis = await self._analyze_layout(processed_image, tab_name)

        # Perform color analysis
        color_analysis = await self._analyze_colors(processed_image)

        # Calculate accuracy score
        accuracy_score = self._calculate_accuracy_score(
            detected_fields, expected_data, tab_name
        )

        # Identify missing and misaligned fields
        missing_fields, misaligned_fields = self._identify_issues(
            detected_fields, expected_data, tab_name
        )

        # Generate recommendations
        recommendations = self._generate_recommendations(
            detected_fields, layout_analysis, color_analysis, accuracy_score
        )

        return VisualVerificationResult(
            image_path=image_path,
            tab_name=tab_name,
            fields_detected=detected_fields,
            accuracy_score=accuracy_score,
            missing_fields=missing_fields,
            misaligned_fields=misaligned_fields,
            color_analysis=color_analysis,
            layout_analysis=layout_analysis,
            recommendations=recommendations
        )

    async def _preprocess_image(self, image: Image.Image) -> Image.Image:
        """Advanced image preprocessing for better analysis"""

        # Convert to RGB if necessary
        if image.mode != 'RGB':
            image = image.convert('RGB')

        # Enhance contrast and sharpness
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(1.2)

        enhancer = ImageEnhance.Sharpness(image)
        image = enhancer.enhance(1.1)

        # Slight noise reduction
        image = image.filter(ImageFilter.MedianFilter(size=3))

        return image

    async def _detect_fields_comprehensive(self, image: Image.Image, tab_name: str,
                                         expected_data: Dict[str, Any]) -> List[FieldLocation]:
        """Comprehensive field detection using multiple techniques"""

        detected_fields = []

        # Convert PIL to CV2 for advanced processing
        cv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)

        # Method 1: OCR-based detection
        ocr_fields = await self._detect_fields_ocr(image, tab_name)
        detected_fields.extend(ocr_fields)

        # Method 2: Template matching
        template_fields = await self._detect_fields_template(cv_image, tab_name)
        detected_fields.extend(template_fields)

        # Method 3: Color-based detection
        color_fields = await self._detect_fields_color(cv_image, tab_name)
        detected_fields.extend(color_fields)

        # Method 4: Layout structure analysis
        structure_fields = await self._detect_fields_structure(cv_image, tab_name)
        detected_fields.extend(structure_fields)

        # Merge and deduplicate fields
        merged_fields = self._merge_field_detections(detected_fields)

        return merged_fields

    async def _detect_fields_ocr(self, image: Image.Image, tab_name: str) -> List[FieldLocation]:
        """OCR-based field detection"""

        fields = []

        # Use pytesseract to get detailed OCR data
        ocr_data = pytesseract.image_to_data(
            image,
            config=self.ocr_config,
            output_type=pytesseract.Output.DICT
        )

        # Group text by lines and analyze
        lines = self._group_ocr_by_lines(ocr_data)

        patterns = self.field_patterns.get(tab_name, {})
        expected_fields = patterns.get('expected_fields', [])

        for line in lines:
            # Check if line contains field labels or values
            line_text = line['text'].strip()

            # Look for field labels
            for expected_field in expected_fields:
                if self._fuzzy_match(expected_field.lower(), line_text.lower()):

                    # Try to find associated value
                    value_text = self._find_associated_value(line, lines)

                    field = FieldLocation(
                        field_name=expected_field,
                        bounding_box=(line['left'], line['top'],
                                    line['left'] + line['width'],
                                    line['top'] + line['height']),
                        confidence=line['conf'] / 100.0,
                        text_content=line_text,
                        value_content=value_text,
                        data_type=self._infer_data_type(value_text),
                        tab_section=tab_name
                    )

                    fields.append(field)

        return fields

    async def _detect_fields_template(self, cv_image: np.ndarray, tab_name: str) -> List[FieldLocation]:
        """Template-based field detection for UI elements"""

        fields = []

        # Convert to grayscale for template matching
        gray = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)

        # Detect common UI elements
        # 1. Input fields
        input_fields = self._detect_input_fields(gray)

        # 2. Value containers
        value_containers = self._detect_value_containers(gray)

        # 3. Labels
        labels = self._detect_labels(gray)

        # Match elements to expected fields
        patterns = self.field_patterns.get(tab_name, {})
        expected_fields = patterns.get('expected_fields', [])

        # Create field locations from detected elements
        for element in input_fields + value_containers + labels:
            # Try to extract text from element
            x, y, w, h = element['bbox']
            element_roi = cv_image[y:y+h, x:x+w]

            # OCR on element
            element_text = pytesseract.image_to_string(
                element_roi, config=self.ocr_config
            ).strip()

            # Match to expected field
            best_match = self._find_best_field_match(element_text, expected_fields)

            if best_match:
                field = FieldLocation(
                    field_name=best_match,
                    bounding_box=(x, y, x + w, y + h),
                    confidence=element['confidence'],
                    text_content=element_text,
                    value_content=element_text,
                    data_type=self._infer_data_type(element_text),
                    tab_section=tab_name
                )

                fields.append(field)

        return fields

    async def _detect_fields_color(self, cv_image: np.ndarray, tab_name: str) -> List[FieldLocation]:
        """Color-based field detection"""

        fields = []

        # Convert to HSV for better color analysis
        hsv = cv2.cvtColor(cv_image, cv2.COLOR_BGR2HSV)

        # Define color ranges for different field types
        color_ranges = {
            'text_fields': {
                'lower': np.array([0, 0, 200]),
                'upper': np.array([180, 30, 255])
            },
            'value_fields': {
                'lower': np.array([0, 0, 240]),
                'upper': np.array([180, 20, 255])
            },
            'accent_elements': {
                'lower': np.array([20, 100, 200]),
                'upper': np.array([30, 255, 255])
            }
        }

        for field_type, color_range in color_ranges.items():
            # Create mask for color range
            mask = cv2.inRange(hsv, color_range['lower'], color_range['upper'])

            # Find contours
            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            for contour in contours:
                # Filter by area
                area = cv2.contourArea(contour)
                if 100 < area < 50000:  # Reasonable field size

                    # Get bounding box
                    x, y, w, h = cv2.boundingRect(contour)

                    # Extract text from region
                    roi = cv_image[y:y+h, x:x+w]
                    text = pytesseract.image_to_string(roi, config=self.ocr_config).strip()

                    if text and len(text) > 2:
                        field = FieldLocation(
                            field_name=f"color_detected_{field_type}",
                            bounding_box=(x, y, x + w, y + h),
                            confidence=0.7,
                            text_content=text,
                            value_content=text,
                            data_type=self._infer_data_type(text),
                            tab_section=tab_name
                        )

                        fields.append(field)

        return fields

    async def _detect_fields_structure(self, cv_image: np.ndarray, tab_name: str) -> List[FieldLocation]:
        """Structure-based field detection using layout analysis"""

        fields = []

        # Convert to grayscale
        gray = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)

        # Detect horizontal and vertical lines (table structure)
        horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (40, 1))
        vertical_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 40))

        # Detect horizontal lines
        horizontal_lines = cv2.morphologyEx(gray, cv2.MORPH_OPEN, horizontal_kernel)

        # Detect vertical lines
        vertical_lines = cv2.morphologyEx(gray, cv2.MORPH_OPEN, vertical_kernel)

        # Combine lines to find table structure
        table_mask = cv2.add(horizontal_lines, vertical_lines)

        # Find cells in table structure
        contours, _ = cv2.findContours(table_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # Analyze each potential cell
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)

            # Check if it's a reasonable cell size
            if 50 < w < 500 and 20 < h < 100:

                # Extract text from cell
                cell_roi = cv_image[y:y+h, x:x+w]
                cell_text = pytesseract.image_to_string(cell_roi, config=self.ocr_config).strip()

                if cell_text:
                    field = FieldLocation(
                        field_name="structure_detected",
                        bounding_box=(x, y, x + w, y + h),
                        confidence=0.6,
                        text_content=cell_text,
                        value_content=cell_text,
                        data_type=self._infer_data_type(cell_text),
                        tab_section=tab_name
                    )

                    fields.append(field)

        return fields

    def _group_ocr_by_lines(self, ocr_data: Dict) -> List[Dict]:
        """Group OCR data by text lines"""

        lines = []
        current_line = None

        for i in range(len(ocr_data['text'])):
            if int(ocr_data['conf'][i]) > 30:  # Confidence threshold

                text = ocr_data['text'][i].strip()
                if not text:
                    continue

                left = ocr_data['left'][i]
                top = ocr_data['top'][i]
                width = ocr_data['width'][i]
                height = ocr_data['height'][i]

                # Check if this word belongs to current line
                if current_line and abs(top - current_line['top']) < height * 0.5:
                    # Add to current line
                    current_line['text'] += ' ' + text
                    current_line['width'] = max(
                        current_line['left'] + current_line['width'],
                        left + width
                    ) - current_line['left']
                    current_line['conf'] = max(current_line['conf'], ocr_data['conf'][i])
                else:
                    # Start new line
                    if current_line:
                        lines.append(current_line)

                    current_line = {
                        'text': text,
                        'left': left,
                        'top': top,
                        'width': width,
                        'height': height,
                        'conf': ocr_data['conf'][i]
                    }

        if current_line:
            lines.append(current_line)

        return lines

    def _fuzzy_match(self, text1: str, text2: str, threshold: float = 0.8) -> bool:
        """Fuzzy string matching"""
        from difflib import SequenceMatcher

        similarity = SequenceMatcher(None, text1, text2).ratio()
        return similarity >= threshold

    def _find_associated_value(self, label_line: Dict, all_lines: List[Dict]) -> str:
        """Find value associated with a label"""

        label_y = label_line['top']
        label_right = label_line['left'] + label_line['width']

        # Look for value on same line (to the right)
        for line in all_lines:
            if (abs(line['top'] - label_y) < 10 and
                line['left'] > label_right and
                line['left'] - label_right < 200):
                return line['text']

        # Look for value on next line (below)
        for line in all_lines:
            if (line['top'] > label_y and
                line['top'] - label_y < 50 and
                abs(line['left'] - label_line['left']) < 100):
                return line['text']

        return ""

    def _infer_data_type(self, text: str) -> str:
        """Infer data type from text content"""

        if not text:
            return "unknown"

        # Currency
        if re.match(r'\$[\d,]+\.?\d*', text):
            return "currency"

        # Date
        if re.match(r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}', text):
            return "date"

        # Number
        if re.match(r'^\d+\.?\d*$', text):
            return "number"

        # Square footage
        if 'sq ft' in text.lower() or 'sqft' in text.lower():
            return "area"

        # Percentage
        if '%' in text:
            return "percentage"

        # Address
        if re.search(r'\d+\s+[A-Za-z\s]+(St|Street|Ave|Avenue|Rd|Road|Dr|Drive)', text):
            return "address"

        # Name (proper case)
        if re.match(r'^[A-Z][a-z]+(\s+[A-Z][a-z]+)*$', text):
            return "name"

        return "text"

    def _detect_input_fields(self, gray_image: np.ndarray) -> List[Dict]:
        """Detect input field elements"""

        fields = []

        # Use edge detection to find rectangular elements
        edges = cv2.Canny(gray_image, 50, 150)

        # Find contours
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        for contour in contours:
            # Get bounding rectangle
            x, y, w, h = cv2.boundingRect(contour)

            # Filter by aspect ratio and size (typical input field dimensions)
            aspect_ratio = w / h
            area = w * h

            if (2 < aspect_ratio < 15 and
                1000 < area < 50000 and
                h > 20 and h < 100):

                fields.append({
                    'bbox': (x, y, w, h),
                    'confidence': 0.7,
                    'type': 'input_field'
                })

        return fields

    def _detect_value_containers(self, gray_image: np.ndarray) -> List[Dict]:
        """Detect value container elements"""

        containers = []

        # Look for rectangular regions with light background
        blurred = cv2.GaussianBlur(gray_image, (5, 5), 0)

        # Threshold to find light regions
        _, thresh = cv2.threshold(blurred, 240, 255, cv2.THRESH_BINARY)

        # Find contours
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)

            # Filter by size
            if 50 < w < 300 and 15 < h < 60:
                containers.append({
                    'bbox': (x, y, w, h),
                    'confidence': 0.6,
                    'type': 'value_container'
                })

        return containers

    def _detect_labels(self, gray_image: np.ndarray) -> List[Dict]:
        """Detect label elements"""

        labels = []

        # Use MSER (Maximally Stable Extremal Regions) to find text regions
        mser = cv2.MSER_create()
        regions, _ = mser.detectRegions(gray_image)

        for region in regions:
            # Get bounding box
            x, y, w, h = cv2.boundingRect(region.reshape(-1, 1, 2))

            # Filter by typical label dimensions
            if 30 < w < 200 and 10 < h < 40:
                labels.append({
                    'bbox': (x, y, w, h),
                    'confidence': 0.5,
                    'type': 'label'
                })

        return labels

    def _find_best_field_match(self, text: str, expected_fields: List[str]) -> Optional[str]:
        """Find best matching expected field"""

        best_match = None
        best_score = 0

        for field in expected_fields:
            score = self._calculate_text_similarity(text.lower(), field.lower())
            if score > best_score and score > 0.6:
                best_score = score
                best_match = field

        return best_match

    def _calculate_text_similarity(self, text1: str, text2: str) -> float:
        """Calculate text similarity score"""
        from difflib import SequenceMatcher

        # Direct similarity
        direct_sim = SequenceMatcher(None, text1, text2).ratio()

        # Check if one contains the other
        if text1 in text2 or text2 in text1:
            direct_sim = max(direct_sim, 0.8)

        # Check for keyword matches
        words1 = set(text1.split())
        words2 = set(text2.split())

        if words1 & words2:  # Common words
            word_sim = len(words1 & words2) / max(len(words1), len(words2))
            direct_sim = max(direct_sim, word_sim * 0.9)

        return direct_sim

    def _merge_field_detections(self, fields: List[FieldLocation]) -> List[FieldLocation]:
        """Merge overlapping field detections"""

        if not fields:
            return []

        merged = []

        # Sort by confidence
        fields.sort(key=lambda f: f.confidence, reverse=True)

        for field in fields:
            # Check if this field overlaps with any merged field
            overlaps = False

            for merged_field in merged:
                if self._calculate_iou(field.bounding_box, merged_field.bounding_box) > 0.5:
                    overlaps = True
                    # Keep the higher confidence field
                    if field.confidence > merged_field.confidence:
                        merged.remove(merged_field)
                        merged.append(field)
                    break

            if not overlaps:
                merged.append(field)

        return merged

    def _calculate_iou(self, box1: Tuple[int, int, int, int],
                      box2: Tuple[int, int, int, int]) -> float:
        """Calculate Intersection over Union of two bounding boxes"""

        x1_1, y1_1, x2_1, y2_1 = box1
        x1_2, y1_2, x2_2, y2_2 = box2

        # Calculate intersection
        x1_i = max(x1_1, x1_2)
        y1_i = max(y1_1, y1_2)
        x2_i = min(x2_1, x2_2)
        y2_i = min(y2_1, y2_2)

        if x2_i <= x1_i or y2_i <= y1_i:
            return 0.0

        intersection = (x2_i - x1_i) * (y2_i - y1_i)

        # Calculate union
        area1 = (x2_1 - x1_1) * (y2_1 - y1_1)
        area2 = (x2_2 - x1_2) * (y2_2 - y1_2)
        union = area1 + area2 - intersection

        return intersection / union if union > 0 else 0.0

    async def _analyze_layout(self, image: Image.Image, tab_name: str) -> Dict[str, Any]:
        """Analyze layout structure and alignment"""

        # Convert to numpy array
        img_array = np.array(image)

        # Detect main content areas
        content_areas = self._detect_content_areas(img_array)

        # Analyze grid structure
        grid_analysis = self._analyze_grid_structure(img_array)

        # Check alignment
        alignment_analysis = self._analyze_alignment(img_array)

        # Measure spacing consistency
        spacing_analysis = self._analyze_spacing(img_array)

        return {
            'content_areas': content_areas,
            'grid_structure': grid_analysis,
            'alignment': alignment_analysis,
            'spacing': spacing_analysis,
            'layout_score': self._calculate_layout_score(
                content_areas, grid_analysis, alignment_analysis, spacing_analysis
            )
        }

    def _detect_content_areas(self, img_array: np.ndarray) -> Dict[str, Any]:
        """Detect main content areas in the layout"""

        # Convert to grayscale
        gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)

        # Find contours of content areas
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        edges = cv2.Canny(blurred, 30, 100)

        # Dilate to connect nearby elements
        kernel = np.ones((10, 10), np.uint8)
        dilated = cv2.dilate(edges, kernel, iterations=2)

        # Find contours
        contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # Filter and analyze content areas
        content_areas = []

        for contour in contours:
            area = cv2.contourArea(contour)
            if area > 5000:  # Significant content area
                x, y, w, h = cv2.boundingRect(contour)

                content_areas.append({
                    'bbox': (x, y, w, h),
                    'area': area,
                    'aspect_ratio': w / h
                })

        return {
            'count': len(content_areas),
            'areas': content_areas,
            'total_content_area': sum(area['area'] for area in content_areas)
        }

    def _analyze_grid_structure(self, img_array: np.ndarray) -> Dict[str, Any]:
        """Analyze grid structure and organization"""

        gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)

        # Detect horizontal lines
        horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (40, 1))
        horizontal_lines = cv2.morphologyEx(gray, cv2.MORPH_OPEN, horizontal_kernel)

        # Detect vertical lines
        vertical_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 40))
        vertical_lines = cv2.morphologyEx(gray, cv2.MORPH_OPEN, vertical_kernel)

        # Find line positions
        h_lines = np.where(np.sum(horizontal_lines, axis=1) > 1000)[0]
        v_lines = np.where(np.sum(vertical_lines, axis=0) > 1000)[0]

        # Analyze spacing between lines
        h_spacing = np.diff(h_lines) if len(h_lines) > 1 else []
        v_spacing = np.diff(v_lines) if len(v_lines) > 1 else []

        return {
            'horizontal_lines': len(h_lines),
            'vertical_lines': len(v_lines),
            'h_spacing_consistency': np.std(h_spacing) if len(h_spacing) > 0 else 0,
            'v_spacing_consistency': np.std(v_spacing) if len(v_spacing) > 0 else 0,
            'grid_regularity': self._calculate_grid_regularity(h_spacing, v_spacing)
        }

    def _analyze_alignment(self, img_array: np.ndarray) -> Dict[str, Any]:
        """Analyze text and element alignment"""

        # Use edge detection to find text blocks
        gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
        edges = cv2.Canny(gray, 50, 150)

        # Find contours of text blocks
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # Get bounding boxes
        text_blocks = []
        for contour in contours:
            area = cv2.contourArea(contour)
            if 100 < area < 5000:  # Text block size
                x, y, w, h = cv2.boundingRect(contour)
                text_blocks.append((x, y, w, h))

        if not text_blocks:
            return {'alignment_score': 0}

        # Analyze left alignment
        left_edges = [block[0] for block in text_blocks]
        left_alignment_score = 1.0 - (np.std(left_edges) / np.mean(left_edges)) if left_edges else 0

        # Analyze vertical alignment
        top_edges = [block[1] for block in text_blocks]
        vertical_alignment_score = 1.0 - (np.std(top_edges) / np.mean(top_edges)) if top_edges else 0

        return {
            'left_alignment_score': max(0, min(1, left_alignment_score)),
            'vertical_alignment_score': max(0, min(1, vertical_alignment_score)),
            'overall_alignment': (left_alignment_score + vertical_alignment_score) / 2
        }

    def _analyze_spacing(self, img_array: np.ndarray) -> Dict[str, Any]:
        """Analyze spacing consistency"""

        # Similar to alignment analysis but focus on spacing between elements
        gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)

        # Find text regions
        blurred = cv2.GaussianBlur(gray, (3, 3), 0)
        _, thresh = cv2.threshold(blurred, 200, 255, cv2.THRESH_BINARY_INV)

        # Find contours
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # Get centroids
        centroids = []
        for contour in contours:
            area = cv2.contourArea(contour)
            if area > 50:
                M = cv2.moments(contour)
                if M["m00"] != 0:
                    cx = int(M["m10"] / M["m00"])
                    cy = int(M["m01"] / M["m00"])
                    centroids.append((cx, cy))

        if len(centroids) < 2:
            return {'spacing_score': 1.0}

        # Calculate distances between nearby centroids
        distances = []
        centroids.sort(key=lambda p: p[1])  # Sort by y-coordinate

        for i in range(len(centroids) - 1):
            dist = np.sqrt((centroids[i][0] - centroids[i+1][0])**2 +
                          (centroids[i][1] - centroids[i+1][1])**2)
            distances.append(dist)

        # Calculate spacing consistency
        spacing_consistency = 1.0 - (np.std(distances) / np.mean(distances)) if distances else 1.0

        return {
            'spacing_consistency': max(0, min(1, spacing_consistency)),
            'average_spacing': np.mean(distances) if distances else 0,
            'spacing_variance': np.var(distances) if distances else 0
        }

    def _calculate_grid_regularity(self, h_spacing: np.ndarray, v_spacing: np.ndarray) -> float:
        """Calculate grid regularity score"""

        if len(h_spacing) == 0 and len(v_spacing) == 0:
            return 0.0

        h_regularity = 1.0 - (np.std(h_spacing) / np.mean(h_spacing)) if len(h_spacing) > 0 else 1.0
        v_regularity = 1.0 - (np.std(v_spacing) / np.mean(v_spacing)) if len(v_spacing) > 0 else 1.0

        return (h_regularity + v_regularity) / 2

    def _calculate_layout_score(self, content_areas: Dict, grid_analysis: Dict,
                               alignment_analysis: Dict, spacing_analysis: Dict) -> float:
        """Calculate overall layout quality score"""

        # Weight different aspects
        weights = {
            'content_organization': 0.3,
            'grid_regularity': 0.2,
            'alignment': 0.3,
            'spacing': 0.2
        }

        # Content organization score
        content_score = min(1.0, content_areas['count'] / 10)  # Optimal around 5-10 content areas

        # Grid score
        grid_score = grid_analysis['grid_regularity']

        # Alignment score
        alignment_score = alignment_analysis.get('overall_alignment', 0)

        # Spacing score
        spacing_score = spacing_analysis.get('spacing_consistency', 0)

        total_score = (
            content_score * weights['content_organization'] +
            grid_score * weights['grid_regularity'] +
            alignment_score * weights['alignment'] +
            spacing_score * weights['spacing']
        )

        return max(0, min(1, total_score))

    async def _analyze_colors(self, image: Image.Image) -> Dict[str, Any]:
        """Analyze color usage and consistency"""

        # Convert to numpy array
        img_array = np.array(image)

        # Flatten for color analysis
        pixels = img_array.reshape(-1, 3)

        # Remove white/near-white pixels (background)
        non_bg_pixels = pixels[np.sum(pixels, axis=1) < 750]  # Not pure white

        if len(non_bg_pixels) == 0:
            return {'color_score': 0}

        # Cluster colors
        from sklearn.cluster import KMeans

        n_colors = min(10, len(non_bg_pixels))
        if n_colors < 2:
            return {'color_score': 0.5}

        kmeans = KMeans(n_clusters=n_colors, random_state=42, n_init=10)
        color_labels = kmeans.fit_predict(non_bg_pixels)

        # Get dominant colors
        dominant_colors = kmeans.cluster_centers_.astype(int)
        color_counts = np.bincount(color_labels)

        # Analyze color scheme consistency
        scheme_score = self._analyze_color_scheme_consistency(dominant_colors)

        # Check against expected color scheme
        brand_consistency = self._check_brand_color_consistency(dominant_colors)

        return {
            'dominant_colors': dominant_colors.tolist(),
            'color_distribution': (color_counts / len(color_labels)).tolist(),
            'scheme_consistency': scheme_score,
            'brand_consistency': brand_consistency,
            'color_score': (scheme_score + brand_consistency) / 2
        }

    def _analyze_color_scheme_consistency(self, colors: np.ndarray) -> float:
        """Analyze if colors work well together"""

        if len(colors) < 2:
            return 1.0

        # Convert to HSV for better color analysis
        hsv_colors = []
        for color in colors:
            rgb_normalized = color / 255.0
            hsv = self._rgb_to_hsv(rgb_normalized)
            hsv_colors.append(hsv)

        hsv_colors = np.array(hsv_colors)

        # Check hue distribution
        hues = hsv_colors[:, 0]
        hue_variance = np.var(hues)

        # Check saturation consistency
        saturations = hsv_colors[:, 1]
        saturation_variance = np.var(saturations)

        # Check value (brightness) consistency
        values = hsv_colors[:, 2]
        value_variance = np.var(values)

        # Lower variance usually means better consistency
        consistency_score = 1.0 - min(1.0, (hue_variance + saturation_variance + value_variance) / 3)

        return max(0, consistency_score)

    def _check_brand_color_consistency(self, colors: np.ndarray) -> float:
        """Check consistency with expected brand colors"""

        expected_colors = self.color_schemes
        brand_score = 0

        for color in colors:
            # Check if color is close to any expected brand color
            for brand_color_name, brand_color_rgb in expected_colors.items():
                distance = np.sqrt(np.sum((color - np.array(brand_color_rgb))**2))
                if distance < 50:  # Close enough threshold
                    brand_score += 1
                    break

        return brand_score / len(colors) if len(colors) > 0 else 0

    def _rgb_to_hsv(self, rgb: np.ndarray) -> np.ndarray:
        """Convert RGB to HSV"""
        r, g, b = rgb

        max_val = max(r, g, b)
        min_val = min(r, g, b)
        diff = max_val - min_val

        # Hue calculation
        if diff == 0:
            h = 0
        elif max_val == r:
            h = (60 * ((g - b) / diff) + 360) % 360
        elif max_val == g:
            h = (60 * ((b - r) / diff) + 120) % 360
        else:
            h = (60 * ((r - g) / diff) + 240) % 360

        # Saturation calculation
        s = 0 if max_val == 0 else diff / max_val

        # Value calculation
        v = max_val

        return np.array([h, s, v])

    def _calculate_accuracy_score(self, detected_fields: List[FieldLocation],
                                 expected_data: Dict[str, Any], tab_name: str) -> float:
        """Calculate overall accuracy score"""

        if not expected_data:
            return 0.0

        expected_fields = set(expected_data.keys())
        detected_field_names = set(field.field_name for field in detected_fields)

        # Calculate field detection accuracy
        detected_expected = len(expected_fields & detected_field_names)
        detection_accuracy = detected_expected / len(expected_fields) if expected_fields else 0

        # Calculate content accuracy
        content_accuracy = 0
        content_checks = 0

        for field in detected_fields:
            if field.field_name in expected_data:
                expected_value = str(expected_data[field.field_name])
                similarity = self._calculate_text_similarity(
                    field.value_content.lower(),
                    expected_value.lower()
                )
                content_accuracy += similarity
                content_checks += 1

        content_accuracy = content_accuracy / content_checks if content_checks > 0 else 0

        # Combine scores
        overall_accuracy = (detection_accuracy * 0.6 + content_accuracy * 0.4)

        return max(0, min(1, overall_accuracy))

    def _identify_issues(self, detected_fields: List[FieldLocation],
                        expected_data: Dict[str, Any], tab_name: str) -> Tuple[List[str], List[str]]:
        """Identify missing and misaligned fields"""

        expected_fields = set(expected_data.keys())
        detected_field_names = set(field.field_name for field in detected_fields)

        # Missing fields
        missing_fields = list(expected_fields - detected_field_names)

        # Misaligned fields (detected but with low confidence or wrong position)
        misaligned_fields = []

        for field in detected_fields:
            if field.confidence < 0.5:
                misaligned_fields.append(field.field_name)

            # Check if field is in unusual position
            if self._is_field_misplaced(field, tab_name):
                misaligned_fields.append(field.field_name)

        return missing_fields, misaligned_fields

    def _is_field_misplaced(self, field: FieldLocation, tab_name: str) -> bool:
        """Check if field appears to be misplaced"""

        # Define expected regions for different field types
        expected_regions = {
            'overview': {
                'address': (0, 0, 0.6, 0.3),  # Upper left
                'values': (0.6, 0, 1.0, 0.5),  # Upper right
                'sale': (0, 0.5, 1.0, 1.0)  # Lower section
            },
            'core-property': {
                'owner': (0, 0, 0.5, 0.4),
                'property_details': (0.5, 0, 1.0, 0.4),
                'values': (0, 0.4, 1.0, 0.8)
            }
        }

        if tab_name not in expected_regions:
            return False

        # Check if field is in expected region based on field name
        for region_type, (x1, y1, x2, y2) in expected_regions[tab_name].items():
            if region_type.lower() in field.field_name.lower():
                # Normalize field position
                field_x = field.bounding_box[0] / 1920  # Assume 1920px width
                field_y = field.bounding_box[1] / 1080  # Assume 1080px height

                # Check if field is outside expected region
                if not (x1 <= field_x <= x2 and y1 <= field_y <= y2):
                    return True

        return False

    def _generate_recommendations(self, detected_fields: List[FieldLocation],
                                 layout_analysis: Dict, color_analysis: Dict,
                                 accuracy_score: float) -> List[str]:
        """Generate recommendations for improvement"""

        recommendations = []

        # Accuracy-based recommendations
        if accuracy_score < 0.7:
            recommendations.append("Overall field detection accuracy is low - review field placement and labeling")

        # Layout recommendations
        layout_score = layout_analysis.get('layout_score', 0)
        if layout_score < 0.6:
            recommendations.append("Layout structure could be improved - consider better alignment and spacing")

        # Color recommendations
        color_score = color_analysis.get('color_score', 0)
        if color_score < 0.7:
            recommendations.append("Color scheme consistency could be improved")

        # Field-specific recommendations
        low_confidence_fields = [f for f in detected_fields if f.confidence < 0.6]
        if low_confidence_fields:
            recommendations.append(f"Improve visibility of {len(low_confidence_fields)} fields with low detection confidence")

        # Alignment recommendations
        alignment_score = layout_analysis.get('alignment', {}).get('overall_alignment', 0)
        if alignment_score < 0.7:
            recommendations.append("Improve text and element alignment for better visual consistency")

        # Spacing recommendations
        spacing_score = layout_analysis.get('spacing', {}).get('spacing_consistency', 0)
        if spacing_score < 0.7:
            recommendations.append("Improve spacing consistency between elements")

        return recommendations

    async def create_annotated_screenshot(self, image_path: str,
                                        verification_result: VisualVerificationResult) -> str:
        """Create annotated screenshot with detected fields highlighted"""

        # Load image
        image = Image.open(image_path)
        draw = ImageDraw.Draw(image)

        # Draw bounding boxes for detected fields
        for field in verification_result.fields_detected:
            x1, y1, x2, y2 = field.bounding_box

            # Color based on confidence
            if field.confidence > 0.8:
                color = (0, 255, 0)  # Green
            elif field.confidence > 0.6:
                color = (255, 165, 0)  # Orange
            else:
                color = (255, 0, 0)  # Red

            # Draw rectangle
            draw.rectangle([x1, y1, x2, y2], outline=color, width=2)

            # Draw label
            label = f"{field.field_name} ({field.confidence:.2f})"
            text_bbox = draw.textbbox((x1, y1-20), label, font=self.fonts['regular'])
            draw.rectangle(text_bbox, fill=color)
            draw.text((x1, y1-20), label, fill=(255, 255, 255), font=self.fonts['regular'])

        # Save annotated image
        output_path = image_path.replace('.png', '_annotated.png')
        image.save(output_path)

        return output_path

    async def generate_verification_report(self, results: List[VisualVerificationResult]) -> str:
        """Generate comprehensive HTML report"""

        # Calculate overall statistics
        total_fields = sum(len(r.fields_detected) for r in results)
        avg_accuracy = sum(r.accuracy_score for r in results) / len(results) if results else 0

        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>PIL/Pillow Visual Verification Report</title>
            <style>
                body {{
                    font-family: 'Segoe UI', Arial, sans-serif;
                    margin: 0;
                    padding: 20px;
                    background: #f8fafc;
                }}
                .container {{ max-width: 1400px; margin: 0 auto; }}
                .header {{
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    padding: 30px;
                    border-radius: 15px;
                    margin-bottom: 30px;
                    box-shadow: 0 10px 30px rgba(0,0,0,0.1);
                }}
                .stats-grid {{
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                    gap: 20px;
                    margin-bottom: 30px;
                }}
                .stat-card {{
                    background: white;
                    padding: 20px;
                    border-radius: 10px;
                    box-shadow: 0 4px 15px rgba(0,0,0,0.1);
                    text-align: center;
                }}
                .stat-value {{
                    font-size: 2.5em;
                    font-weight: bold;
                    color: #4f46e5;
                    margin-bottom: 10px;
                }}
                .tab-result {{
                    background: white;
                    margin: 20px 0;
                    padding: 25px;
                    border-radius: 10px;
                    box-shadow: 0 4px 15px rgba(0,0,0,0.1);
                }}
                .tab-header {{
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    margin-bottom: 20px;
                    padding-bottom: 15px;
                    border-bottom: 2px solid #e5e7eb;
                }}
                .accuracy-bar {{
                    width: 100%;
                    height: 25px;
                    background: #e5e7eb;
                    border-radius: 12px;
                    overflow: hidden;
                    margin: 15px 0;
                }}
                .accuracy-fill {{
                    height: 100%;
                    background: linear-gradient(90deg, #ef4444, #f59e0b, #10b981);
                    transition: width 0.5s ease;
                }}
                .field-grid {{
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                    gap: 15px;
                    margin: 20px 0;
                }}
                .field-card {{
                    background: #f8fafc;
                    padding: 15px;
                    border-radius: 8px;
                    border-left: 4px solid #6366f1;
                }}
                .confidence-high {{ border-left-color: #10b981; }}
                .confidence-medium {{ border-left-color: #f59e0b; }}
                .confidence-low {{ border-left-color: #ef4444; }}
                .recommendations {{
                    background: #fef3c7;
                    border: 1px solid #f59e0b;
                    border-radius: 8px;
                    padding: 20px;
                    margin: 20px 0;
                }}
                .screenshot {{
                    max-width: 100%;
                    border-radius: 8px;
                    box-shadow: 0 4px 15px rgba(0,0,0,0.1);
                    margin: 15px 0;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🖼️ PIL/Pillow Visual Verification Report</h1>
                    <p style="font-size: 1.2em; opacity: 0.9;">
                        Comprehensive visual analysis using advanced image processing
                    </p>
                    <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                </div>

                <div class="stats-grid">
                    <div class="stat-card">
                        <div class="stat-value">{len(results)}</div>
                        <div>Tabs Analyzed</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value">{total_fields}</div>
                        <div>Fields Detected</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value">{avg_accuracy:.1%}</div>
                        <div>Average Accuracy</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value">{sum(1 for r in results if r.accuracy_score > 0.8)}</div>
                        <div>High Quality Tabs</div>
                    </div>
                </div>
        """

        # Add results for each tab
        for result in results:
            confidence_class = (
                'confidence-high' if result.accuracy_score > 0.8 else
                'confidence-medium' if result.accuracy_score > 0.6 else
                'confidence-low'
            )

            html += f"""
                <div class="tab-result">
                    <div class="tab-header">
                        <h2>{result.tab_name.replace('-', ' ').title()}</h2>
                        <span style="font-size: 1.5em; font-weight: bold; color: #4f46e5;">
                            {result.accuracy_score:.1%}
                        </span>
                    </div>

                    <div class="accuracy-bar">
                        <div class="accuracy-fill" style="width: {result.accuracy_score*100}%"></div>
                    </div>

                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 30px; margin: 20px 0;">
                        <div>
                            <h4>📊 Detection Summary</h4>
                            <p>Fields Detected: <strong>{len(result.fields_detected)}</strong></p>
                            <p>Missing Fields: <strong>{len(result.missing_fields)}</strong></p>
                            <p>Misaligned Fields: <strong>{len(result.misaligned_fields)}</strong></p>
                            <p>Layout Score: <strong>{result.layout_analysis.get('layout_score', 0):.1%}</strong></p>
                        </div>
                        <div>
                            <h4>🎨 Visual Quality</h4>
                            <p>Color Consistency: <strong>{result.color_analysis.get('color_score', 0):.1%}</strong></p>
                            <p>Alignment Score: <strong>{result.layout_analysis.get('alignment', {}).get('overall_alignment', 0):.1%}</strong></p>
                            <p>Spacing Score: <strong>{result.layout_analysis.get('spacing', {}).get('spacing_consistency', 0):.1%}</strong></p>
                        </div>
                    </div>
            """

            # Add detected fields
            if result.fields_detected:
                html += '<h4>🔍 Detected Fields</h4><div class="field-grid">'
                for field in result.fields_detected:
                    field_confidence_class = (
                        'confidence-high' if field.confidence > 0.8 else
                        'confidence-medium' if field.confidence > 0.6 else
                        'confidence-low'
                    )
                    html += f"""
                        <div class="field-card {field_confidence_class}">
                            <strong>{field.field_name}</strong><br>
                            <small>Confidence: {field.confidence:.1%}</small><br>
                            <small>Content: "{field.value_content[:50]}..."</small><br>
                            <small>Type: {field.data_type}</small>
                        </div>
                    """
                html += '</div>'

            # Add recommendations
            if result.recommendations:
                html += '<div class="recommendations"><h4>💡 Recommendations</h4><ul>'
                for rec in result.recommendations:
                    html += f'<li>{rec}</li>'
                html += '</ul></div>'

            html += '</div>'

        html += """
            </div>
        </body>
        </html>
        """

        # Save report
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = Path(f"pillow_verification_report_{timestamp}.html")

        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(html)

        logger.info(f"PIL/Pillow verification report saved to {report_path}")
        return str(report_path)

# Example usage
async def main():
    """Example usage of PIL visual verification system"""

    verifier = PILVisualVerificationSystem()

    # Example: Analyze a screenshot
    image_path = "screenshot_overview.png"
    tab_name = "overview"
    expected_data = {
        "Site Address": "123 Main St",
        "Property Owner": "John Doe",
        "Parcel ID": "064210010010",
        "Just Value": "$500,000",
        "Taxable Value": "$450,000"
    }

    try:
        result = await verifier.analyze_screenshot(image_path, tab_name, expected_data)

        print(f"Analysis complete for {tab_name} tab")
        print(f"Accuracy Score: {result.accuracy_score:.1%}")
        print(f"Fields Detected: {len(result.fields_detected)}")
        print(f"Missing Fields: {result.missing_fields}")

        # Create annotated screenshot
        annotated_path = await verifier.create_annotated_screenshot(image_path, result)
        print(f"Annotated screenshot saved: {annotated_path}")

        # Generate report
        report_path = await verifier.generate_verification_report([result])
        print(f"Report generated: {report_path}")

    except Exception as e:
        print(f"Error during analysis: {e}")

if __name__ == "__main__":
    asyncio.run(main())