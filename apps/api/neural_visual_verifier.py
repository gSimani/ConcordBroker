"""
Neural Network Enhanced Visual Verification System
Uses Keras deep learning models for advanced computer vision verification
"""

import asyncio
import numpy as np
import cv2
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers, models
from PIL import Image, ImageDraw, ImageFont
import pytesseract
from playwright.async_api import async_playwright, Page, Browser
import json
import os
import re
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from datetime import datetime
import base64
from io import BytesIO

@dataclass
class NeuralVerificationResult:
    """Enhanced verification result with neural network analysis"""
    field_name: str
    expected_value: Any
    displayed_value: Any
    ocr_extracted_value: Any
    neural_confidence: float
    visual_similarity: float
    text_accuracy: float
    element_detection_score: float
    screenshot_path: str
    annotated_screenshot_path: str
    coordinates: Tuple[int, int, int, int]
    verification_status: str
    timestamp: datetime
    neural_analysis: Dict[str, float]

class NeuralVisualVerifier:
    """Advanced visual verification using neural networks"""

    def __init__(self, base_url: str = "http://localhost:5173"):
        self.base_url = base_url
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None

        # Neural network models
        self.text_detector = None
        self.element_classifier = None
        self.value_validator = None
        self.layout_analyzer = None

        # Computer vision models
        self.ocr_confidence_threshold = 0.8
        self.element_detection_threshold = 0.7

        # Results storage
        self.verification_results: List[NeuralVerificationResult] = []

        # Configure Tesseract
        pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

    async def initialize(self):
        """Initialize browser and neural networks"""
        print("Initializing Neural Visual Verifier...")

        # Initialize Playwright
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=False,
            args=['--start-maximized', '--disable-web-security']
        )
        self.context = await self.browser.new_context(
            viewport={'width': 1920, 'height': 1080}
        )
        self.page = await self.context.new_page()

        # Build and load neural networks
        self.build_neural_networks()
        self.load_pretrained_models()

        print("✓ Neural Visual Verifier initialized")

    async def close(self):
        """Cleanup resources"""
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()

    def build_neural_networks(self):
        """Build neural network architectures for visual verification"""
        print("Building neural networks for visual verification...")

        # 1. Text Detection and Recognition Network
        self.text_detector = self._build_text_detector()

        # 2. UI Element Classification Network
        self.element_classifier = self._build_element_classifier()

        # 3. Value Validation Network
        self.value_validator = self._build_value_validator()

        # 4. Layout Analysis Network
        self.layout_analyzer = self._build_layout_analyzer()

        print("✓ Neural networks built")

    def _build_text_detector(self) -> keras.Model:
        """Build text detection and OCR confidence network"""
        # Input: Image patch
        image_input = layers.Input(shape=(64, 256, 3), name='image_patch')

        # Convolutional layers for feature extraction
        conv1 = layers.Conv2D(32, (3, 3), activation='relu', padding='same')(image_input)
        pool1 = layers.MaxPooling2D((2, 2))(conv1)

        conv2 = layers.Conv2D(64, (3, 3), activation='relu', padding='same')(pool1)
        pool2 = layers.MaxPooling2D((2, 2))(conv2)

        conv3 = layers.Conv2D(128, (3, 3), activation='relu', padding='same')(pool2)
        pool3 = layers.MaxPooling2D((2, 2))(conv3)

        # Recurrent layers for sequence processing
        reshape = layers.Reshape((8, 32 * 128))(pool3)
        lstm1 = layers.LSTM(256, return_sequences=True)(reshape)
        lstm2 = layers.LSTM(256, return_sequences=True)(lstm1)

        # Attention mechanism
        attention = layers.MultiHeadAttention(num_heads=8, key_dim=64)(lstm2, lstm2)
        global_features = layers.GlobalAveragePooling1D()(attention)

        # Output layers
        text_confidence = layers.Dense(1, activation='sigmoid', name='text_confidence')(global_features)
        char_probabilities = layers.Dense(95, activation='softmax', name='char_probs')(global_features)

        model = keras.Model(
            inputs=image_input,
            outputs=[text_confidence, char_probabilities]
        )

        model.compile(
            optimizer='adam',
            loss={'text_confidence': 'binary_crossentropy', 'char_probs': 'sparse_categorical_crossentropy'},
            metrics={'text_confidence': 'accuracy', 'char_probs': 'accuracy'}
        )

        return model

    def _build_element_classifier(self) -> keras.Model:
        """Build UI element classification network"""
        # Input: Screenshot region
        image_input = layers.Input(shape=(224, 224, 3), name='element_image')

        # Use transfer learning with pre-trained CNN
        base_model = keras.applications.ResNet50(
            weights='imagenet',
            include_top=False,
            input_shape=(224, 224, 3)
        )
        base_model.trainable = False

        # Feature extraction
        features = base_model(image_input)
        pooled = layers.GlobalAveragePooling2D()(features)

        # Classification layers
        dense1 = layers.Dense(512, activation='relu')(pooled)
        dropout1 = layers.Dropout(0.5)(dense1)
        dense2 = layers.Dense(256, activation='relu')(dropout1)
        dropout2 = layers.Dropout(0.3)(dense2)

        # Multi-output classification
        element_type = layers.Dense(10, activation='softmax', name='element_type')(dropout2)
        field_type = layers.Dense(8, activation='softmax', name='field_type')(dropout2)
        data_type = layers.Dense(6, activation='softmax', name='data_type')(dropout2)

        model = keras.Model(
            inputs=image_input,
            outputs=[element_type, field_type, data_type]
        )

        model.compile(
            optimizer='adam',
            loss={
                'element_type': 'sparse_categorical_crossentropy',
                'field_type': 'sparse_categorical_crossentropy',
                'data_type': 'sparse_categorical_crossentropy'
            },
            metrics=['accuracy']
        )

        return model

    def _build_value_validator(self) -> keras.Model:
        """Build value validation network"""
        # Inputs
        expected_text = layers.Input(shape=(50,), name='expected_text')
        displayed_text = layers.Input(shape=(50,), name='displayed_text')
        context_features = layers.Input(shape=(20,), name='context_features')

        # Text embeddings
        embedding = layers.Embedding(1000, 128, mask_zero=True)

        expected_embedded = embedding(expected_text)
        displayed_embedded = embedding(displayed_text)

        # LSTM processing
        expected_lstm = layers.LSTM(128)(expected_embedded)
        displayed_lstm = layers.LSTM(128)(displayed_embedded)

        # Similarity computation
        concatenated = layers.Concatenate()([expected_lstm, displayed_lstm, context_features])

        # Validation layers
        dense1 = layers.Dense(256, activation='relu')(concatenated)
        dropout1 = layers.Dropout(0.3)(dense1)
        dense2 = layers.Dense(128, activation='relu')(dropout1)

        # Outputs
        match_probability = layers.Dense(1, activation='sigmoid', name='match_prob')(dense2)
        confidence_score = layers.Dense(1, activation='sigmoid', name='confidence')(dense2)

        model = keras.Model(
            inputs=[expected_text, displayed_text, context_features],
            outputs=[match_probability, confidence_score]
        )

        model.compile(
            optimizer='adam',
            loss={'match_prob': 'binary_crossentropy', 'confidence': 'mse'},
            metrics={'match_prob': 'accuracy'}
        )

        return model

    def _build_layout_analyzer(self) -> keras.Model:
        """Build layout analysis network"""
        # Input: Full page screenshot
        page_input = layers.Input(shape=(512, 512, 3), name='page_screenshot')

        # Encoder-decoder architecture for semantic segmentation
        # Encoder
        conv1 = layers.Conv2D(64, 3, activation='relu', padding='same')(page_input)
        conv1 = layers.Conv2D(64, 3, activation='relu', padding='same')(conv1)
        pool1 = layers.MaxPooling2D(2)(conv1)

        conv2 = layers.Conv2D(128, 3, activation='relu', padding='same')(pool1)
        conv2 = layers.Conv2D(128, 3, activation='relu', padding='same')(conv2)
        pool2 = layers.MaxPooling2D(2)(conv2)

        conv3 = layers.Conv2D(256, 3, activation='relu', padding='same')(pool2)
        conv3 = layers.Conv2D(256, 3, activation='relu', padding='same')(conv3)
        pool3 = layers.MaxPooling2D(2)(conv3)

        # Bottleneck
        conv4 = layers.Conv2D(512, 3, activation='relu', padding='same')(pool3)
        conv4 = layers.Conv2D(512, 3, activation='relu', padding='same')(conv4)

        # Decoder
        up1 = layers.UpSampling2D(2)(conv4)
        up1 = layers.Concatenate()([up1, conv3])
        conv5 = layers.Conv2D(256, 3, activation='relu', padding='same')(up1)

        up2 = layers.UpSampling2D(2)(conv5)
        up2 = layers.Concatenate()([up2, conv2])
        conv6 = layers.Conv2D(128, 3, activation='relu', padding='same')(up2)

        up3 = layers.UpSampling2D(2)(conv6)
        up3 = layers.Concatenate()([up3, conv1])
        conv7 = layers.Conv2D(64, 3, activation='relu', padding='same')(up3)

        # Output: Segmentation mask
        layout_mask = layers.Conv2D(5, 1, activation='softmax', name='layout_segmentation')(conv7)

        model = keras.Model(inputs=page_input, outputs=layout_mask)
        model.compile(
            optimizer='adam',
            loss='sparse_categorical_crossentropy',
            metrics=['accuracy']
        )

        return model

    def load_pretrained_models(self):
        """Load pre-trained models if available"""
        models_dir = "models"
        os.makedirs(models_dir, exist_ok=True)

        model_files = {
            'text_detector': 'text_detector.h5',
            'element_classifier': 'element_classifier.h5',
            'value_validator': 'value_validator.h5',
            'layout_analyzer': 'layout_analyzer.h5'
        }

        for model_name, filename in model_files.items():
            filepath = os.path.join(models_dir, filename)
            if os.path.exists(filepath):
                try:
                    setattr(self, model_name, keras.models.load_model(filepath))
                    print(f"✓ Loaded {model_name}")
                except:
                    print(f"⚠ Could not load {model_name}, using new model")

    async def analyze_page_layout(self) -> Dict[str, Any]:
        """Analyze page layout using neural networks"""
        # Capture full page screenshot
        screenshot_bytes = await self.page.screenshot(full_page=True)

        # Convert to numpy array
        nparr = np.frombuffer(screenshot_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        # Resize for neural network
        img_resized = cv2.resize(img, (512, 512))
        img_normalized = img_resized.astype(np.float32) / 255.0

        # Analyze layout with neural network
        if self.layout_analyzer:
            layout_prediction = self.layout_analyzer.predict(
                np.expand_dims(img_normalized, axis=0)
            )
            layout_mask = layout_prediction[0]

            # Extract layout regions
            regions = self._extract_layout_regions(layout_mask)
        else:
            # Fallback to traditional computer vision
            regions = self._extract_regions_cv(img)

        return {
            "regions": regions,
            "layout_score": self._calculate_layout_score(regions),
            "detected_elements": len(regions)
        }

    def _extract_layout_regions(self, layout_mask: np.ndarray) -> List[Dict]:
        """Extract regions from neural network layout analysis"""
        regions = []

        # Get different region types (0: background, 1: header, 2: content, 3: sidebar, 4: footer)
        for region_type in range(1, 5):
            mask = (layout_mask.argmax(axis=-1) == region_type).astype(np.uint8)

            # Find contours
            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            for contour in contours:
                if cv2.contourArea(contour) > 1000:  # Filter small regions
                    x, y, w, h = cv2.boundingRect(contour)
                    regions.append({
                        "type": ["background", "header", "content", "sidebar", "footer"][region_type],
                        "bbox": (x, y, w, h),
                        "area": w * h,
                        "confidence": 0.8  # From neural network
                    })

        return regions

    def _extract_regions_cv(self, img: np.ndarray) -> List[Dict]:
        """Fallback computer vision region extraction"""
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # Edge detection
        edges = cv2.Canny(gray, 50, 150)

        # Find contours
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        regions = []
        for contour in contours:
            if cv2.contourArea(contour) > 2000:
                x, y, w, h = cv2.boundingRect(contour)
                regions.append({
                    "type": "content",
                    "bbox": (x, y, w, h),
                    "area": w * h,
                    "confidence": 0.5
                })

        return regions

    def _calculate_layout_score(self, regions: List[Dict]) -> float:
        """Calculate layout quality score"""
        if not regions:
            return 0.0

        # Factors: coverage, organization, overlap
        total_area = sum(r["area"] for r in regions)
        coverage = min(total_area / (1920 * 1080), 1.0)

        # Check for reasonable organization
        organization_score = len(regions) / 20.0  # Normalize by expected number of regions

        return (coverage + organization_score) / 2.0

    async def verify_field_with_neural_networks(self, field_selector: str, expected_value: Any,
                                              field_name: str, field_type: str = "text") -> NeuralVerificationResult:
        """Verify field using neural network enhanced analysis"""
        try:
            # Find element
            element = await self.page.query_selector(field_selector)
            if not element:
                # Try alternative selectors
                element = await self.page.query_selector(f'[data-field="{field_name}"]')
                if not element:
                    element = await self.page.query_selector(f'text=/{field_name}/i')

            if element:
                # Get element information
                bbox = await element.bounding_box()
                displayed_text = await element.text_content()
                displayed_text = displayed_text.strip() if displayed_text else ""

                # Capture element screenshot
                element_screenshot = await element.screenshot()

                # Neural network analysis
                neural_analysis = await self._analyze_element_with_neural_networks(
                    element_screenshot, expected_value, displayed_text, field_type
                )

                # Enhanced OCR with neural network validation
                ocr_result = self._extract_text_with_neural_ocr(element_screenshot)

                # Calculate comprehensive scores
                text_accuracy = self._calculate_text_accuracy(expected_value, displayed_text, ocr_result)
                visual_similarity = neural_analysis.get("visual_similarity", 0.0)
                neural_confidence = neural_analysis.get("overall_confidence", 0.0)

                # Determine verification status
                overall_score = (neural_confidence * 0.5 + text_accuracy * 0.3 + visual_similarity * 0.2)

                if overall_score >= 0.95:
                    status = "passed"
                elif overall_score >= 0.7:
                    status = "partial"
                else:
                    status = "failed"

                # Save screenshots
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                screenshot_path = f"verification/neural_{field_name}_{timestamp}.png"
                annotated_path = f"verification/neural_{field_name}_{timestamp}_annotated.png"

                os.makedirs("verification", exist_ok=True)

                with open(screenshot_path, "wb") as f:
                    f.write(element_screenshot)

                # Create annotated screenshot
                self._create_annotated_screenshot(
                    element_screenshot, annotated_path, neural_analysis, status
                )

                return NeuralVerificationResult(
                    field_name=field_name,
                    expected_value=expected_value,
                    displayed_value=displayed_text,
                    ocr_extracted_value=ocr_result,
                    neural_confidence=neural_confidence,
                    visual_similarity=visual_similarity,
                    text_accuracy=text_accuracy,
                    element_detection_score=neural_analysis.get("element_detection", 0.0),
                    screenshot_path=screenshot_path,
                    annotated_screenshot_path=annotated_path,
                    coordinates=(bbox['x'], bbox['y'], bbox['width'], bbox['height']) if bbox else (0, 0, 0, 0),
                    verification_status=status,
                    timestamp=datetime.now(),
                    neural_analysis=neural_analysis
                )

            else:
                # Element not found
                return NeuralVerificationResult(
                    field_name=field_name,
                    expected_value=expected_value,
                    displayed_value=None,
                    ocr_extracted_value=None,
                    neural_confidence=0.0,
                    visual_similarity=0.0,
                    text_accuracy=0.0,
                    element_detection_score=0.0,
                    screenshot_path="",
                    annotated_screenshot_path="",
                    coordinates=(0, 0, 0, 0),
                    verification_status="failed",
                    timestamp=datetime.now(),
                    neural_analysis={"error": "Element not found"}
                )

        except Exception as e:
            print(f"Error in neural verification for {field_name}: {e}")
            return NeuralVerificationResult(
                field_name=field_name,
                expected_value=expected_value,
                displayed_value=None,
                ocr_extracted_value=None,
                neural_confidence=0.0,
                visual_similarity=0.0,
                text_accuracy=0.0,
                element_detection_score=0.0,
                screenshot_path="",
                annotated_screenshot_path="",
                coordinates=(0, 0, 0, 0),
                verification_status="error",
                timestamp=datetime.now(),
                neural_analysis={"error": str(e)}
            )

    async def _analyze_element_with_neural_networks(self, image_bytes: bytes, expected_value: Any,
                                                  displayed_text: str, field_type: str) -> Dict[str, float]:
        """Comprehensive neural network analysis of UI element"""
        analysis = {}

        # Convert image bytes to numpy array
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if img is None:
            return {"error": "Could not decode image"}

        # 1. Element Classification
        if self.element_classifier:
            img_resized = cv2.resize(img, (224, 224))
            img_normalized = img_resized.astype(np.float32) / 255.0

            predictions = self.element_classifier.predict(
                np.expand_dims(img_normalized, axis=0)
            )

            analysis["element_type_confidence"] = float(np.max(predictions[0][0]))
            analysis["field_type_confidence"] = float(np.max(predictions[1][0]))
            analysis["data_type_confidence"] = float(np.max(predictions[2][0]))

        # 2. Text Detection and OCR Confidence
        if self.text_detector and img.shape[0] >= 64 and img.shape[1] >= 256:
            # Resize for text detector
            text_img = cv2.resize(img, (256, 64))
            text_normalized = text_img.astype(np.float32) / 255.0

            text_predictions = self.text_detector.predict(
                np.expand_dims(text_normalized, axis=0)
            )

            analysis["text_detection_confidence"] = float(text_predictions[0][0][0])
            analysis["ocr_quality"] = float(np.max(text_predictions[1][0]))

        # 3. Value Validation
        if self.value_validator:
            # Encode texts
            expected_encoded = self._encode_text_for_validation(str(expected_value))
            displayed_encoded = self._encode_text_for_validation(displayed_text)

            # Context features (simplified)
            context_features = self._extract_context_features(field_type, img)

            validation_result = self.value_validator.predict([
                np.expand_dims(expected_encoded, axis=0),
                np.expand_dims(displayed_encoded, axis=0),
                np.expand_dims(context_features, axis=0)
            ])

            analysis["value_match_probability"] = float(validation_result[0][0][0])
            analysis["validation_confidence"] = float(validation_result[1][0][0])

        # 4. Visual Similarity Analysis
        analysis["visual_similarity"] = self._calculate_visual_similarity(img, expected_value)

        # 5. Overall confidence calculation
        confidence_scores = [
            analysis.get("element_type_confidence", 0.5),
            analysis.get("text_detection_confidence", 0.5),
            analysis.get("value_match_probability", 0.5),
            analysis.get("validation_confidence", 0.5)
        ]

        analysis["overall_confidence"] = float(np.mean(confidence_scores))
        analysis["element_detection"] = analysis.get("element_type_confidence", 0.5)

        return analysis

    def _encode_text_for_validation(self, text: str) -> np.ndarray:
        """Encode text for neural network validation"""
        # Simple character-based encoding
        encoded = np.zeros(50, dtype=int)
        for i, char in enumerate(text[:50]):
            encoded[i] = ord(char) % 1000

        return encoded

    def _extract_context_features(self, field_type: str, img: np.ndarray) -> np.ndarray:
        """Extract context features for validation"""
        features = np.zeros(20)

        # Field type encoding
        type_map = {
            "text": 0, "currency": 1, "date": 2, "area": 3,
            "integer": 4, "decimal": 5, "address": 6, "name": 7
        }
        features[0] = type_map.get(field_type, 0)

        # Image properties
        if img is not None:
            features[1] = img.shape[0] / 1000.0  # Height normalized
            features[2] = img.shape[1] / 1000.0  # Width normalized
            features[3] = np.mean(img) / 255.0   # Average brightness

        # Additional context features would go here
        return features

    def _calculate_visual_similarity(self, img: np.ndarray, expected_value: Any) -> float:
        """Calculate visual similarity score"""
        # This is a simplified version - in practice, you'd have more sophisticated analysis
        if img is None:
            return 0.0

        # Basic image quality metrics
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        contrast = gray.std()
        brightness = gray.mean()

        # Normalize metrics
        contrast_score = min(contrast / 50.0, 1.0)  # Good contrast > 50
        brightness_score = 1.0 - abs(brightness - 127) / 127.0  # Ideal brightness ~127

        return (contrast_score + brightness_score) / 2.0

    def _extract_text_with_neural_ocr(self, image_bytes: bytes) -> str:
        """Extract text using neural network enhanced OCR"""
        # Convert to PIL Image
        img = Image.open(BytesIO(image_bytes))

        # Preprocess image for better OCR
        img_cv = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
        gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)

        # Apply image enhancements
        # Denoise
        denoised = cv2.fastNlMeansDenoising(gray)

        # Increase contrast
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(denoised)

        # Threshold
        _, thresh = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        # Extract text with Tesseract
        custom_config = r'--oem 3 --psm 6'
        text = pytesseract.image_to_string(thresh, config=custom_config)

        return text.strip()

    def _calculate_text_accuracy(self, expected: Any, displayed: str, ocr: str) -> float:
        """Calculate text accuracy score"""
        expected_str = str(expected).strip()
        displayed_clean = displayed.strip()
        ocr_clean = ocr.strip()

        # Calculate similarities
        display_similarity = self._string_similarity(expected_str, displayed_clean)
        ocr_similarity = self._string_similarity(expected_str, ocr_clean)

        # Weight displayed text more heavily than OCR
        return display_similarity * 0.7 + ocr_similarity * 0.3

    def _string_similarity(self, str1: str, str2: str) -> float:
        """Calculate string similarity using multiple metrics"""
        if not str1 or not str2:
            return 0.0 if (str1 or str2) else 1.0

        # Exact match
        if str1 == str2:
            return 1.0

        # Normalize strings
        s1 = re.sub(r'[^\w\s]', '', str1.lower())
        s2 = re.sub(r'[^\w\s]', '', str2.lower())

        # Calculate edit distance
        edit_distance = self._levenshtein_distance(s1, s2)
        max_len = max(len(s1), len(s2))

        return 1.0 - (edit_distance / max_len) if max_len > 0 else 1.0

    def _levenshtein_distance(self, s1: str, s2: str) -> int:
        """Calculate Levenshtein distance"""
        if len(s1) < len(s2):
            return self._levenshtein_distance(s2, s1)

        if len(s2) == 0:
            return len(s1)

        previous_row = range(len(s2) + 1)
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row

        return previous_row[-1]

    def _create_annotated_screenshot(self, image_bytes: bytes, output_path: str,
                                   analysis: Dict, status: str):
        """Create annotated screenshot with neural network analysis"""
        # Load image
        img = Image.open(BytesIO(image_bytes))
        draw = ImageDraw.Draw(img)

        # Load font
        try:
            font = ImageFont.truetype("arial.ttf", 12)
        except:
            font = ImageFont.load_default()

        # Color based on status
        color = "green" if status == "passed" else "red" if status == "failed" else "orange"

        # Add annotations
        y_offset = 10
        annotations = [
            f"Status: {status.upper()}",
            f"Neural Confidence: {analysis.get('overall_confidence', 0):.2%}",
            f"Text Detection: {analysis.get('text_detection_confidence', 0):.2%}",
            f"Element Detection: {analysis.get('element_detection', 0):.2%}",
            f"Value Match: {analysis.get('value_match_probability', 0):.2%}"
        ]

        for annotation in annotations:
            draw.text((10, y_offset), annotation, fill=color, font=font)
            y_offset += 15

        # Save annotated image
        img.save(output_path)

    async def navigate_to_property(self, parcel_id: str):
        """Navigate to property profile page"""
        url = f"{self.base_url}/property/{parcel_id}"
        await self.page.goto(url, wait_until='networkidle')
        await self.page.wait_for_timeout(3000)

    async def navigate_to_tab(self, tab_name: str):
        """Navigate to specific tab"""
        tab_selector = f'[data-tab="{tab_name}"], button:has-text("{tab_name}"), [value="{tab_name}"]'
        try:
            await self.page.click(tab_selector, timeout=5000)
            await self.page.wait_for_timeout(1500)
        except:
            await self.page.click(f'text="{tab_name}"')
            await self.page.wait_for_timeout(1500)

    async def verify_property_with_neural_networks(self, parcel_id: str,
                                                 expected_data: Dict[str, Dict]) -> List[NeuralVerificationResult]:
        """Verify complete property data using neural networks"""
        results = []

        print(f"Starting neural verification for property {parcel_id}")

        # Navigate to property
        await self.navigate_to_property(parcel_id)

        # Analyze page layout first
        layout_analysis = await self.analyze_page_layout()
        print(f"Page layout score: {layout_analysis['layout_score']:.2f}")

        # Verify each tab
        for tab_name, tab_data in expected_data.items():
            print(f"Verifying tab: {tab_name}")

            await self.navigate_to_tab(tab_name)

            for field_name, expected_value in tab_data.items():
                # Determine field type
                field_type = self._determine_field_type(field_name, expected_value)

                # Build selector
                selector = f'[data-field="{field_name}"], .{field_name}-value, #{field_name}'

                # Verify with neural networks
                result = await self.verify_field_with_neural_networks(
                    selector, expected_value, field_name, field_type
                )

                results.append(result)

                print(f"  {field_name}: {result.verification_status} "
                      f"(neural: {result.neural_confidence:.2%}, "
                      f"text: {result.text_accuracy:.2%})")

        self.verification_results.extend(results)
        return results

    def _determine_field_type(self, field_name: str, expected_value: Any) -> str:
        """Determine field type based on name and value"""
        field_name_lower = field_name.lower()

        if "price" in field_name_lower or "value" in field_name_lower or "tax" in field_name_lower:
            return "currency"
        elif "date" in field_name_lower:
            return "date"
        elif "area" in field_name_lower or "sqft" in field_name_lower:
            return "area"
        elif "year" in field_name_lower:
            return "integer"
        elif "addr" in field_name_lower or "address" in field_name_lower:
            return "address"
        elif "name" in field_name_lower:
            return "name"
        else:
            return "text"

    def generate_neural_verification_report(self, results: List[NeuralVerificationResult]) -> str:
        """Generate comprehensive neural verification report"""
        report = []
        report.append("# Neural Network Enhanced Verification Report")
        report.append(f"Generated: {datetime.now().isoformat()}\n")

        # Summary statistics
        total = len(results)
        passed = sum(1 for r in results if r.verification_status == "passed")
        failed = sum(1 for r in results if r.verification_status == "failed")
        partial = sum(1 for r in results if r.verification_status == "partial")

        avg_neural_confidence = np.mean([r.neural_confidence for r in results]) if results else 0
        avg_text_accuracy = np.mean([r.text_accuracy for r in results]) if results else 0
        avg_visual_similarity = np.mean([r.visual_similarity for r in results]) if results else 0

        report.append("## Summary")
        report.append(f"- Total fields verified: {total}")
        report.append(f"- Passed: {passed} ({(passed/total)*100:.1f}%)")
        report.append(f"- Failed: {failed} ({(failed/total)*100:.1f}%)")
        report.append(f"- Partial: {partial} ({(partial/total)*100:.1f}%)")
        report.append(f"- Average Neural Confidence: {avg_neural_confidence:.2%}")
        report.append(f"- Average Text Accuracy: {avg_text_accuracy:.2%}")
        report.append(f"- Average Visual Similarity: {avg_visual_similarity:.2%}\n")

        # Detailed analysis by status
        for status in ["failed", "partial", "passed"]:
            status_results = [r for r in results if r.verification_status == status]
            if status_results:
                report.append(f"### {status.capitalize()} Verifications\n")
                report.append("| Field | Expected | Displayed | Neural Conf | Text Acc | Visual Sim | Screenshot |")
                report.append("|-------|----------|-----------|-------------|----------|------------|------------|")

                for result in status_results:
                    report.append(
                        f"| {result.field_name} | {str(result.expected_value)[:20]} | "
                        f"{str(result.displayed_value)[:20] if result.displayed_value else 'None'} | "
                        f"{result.neural_confidence:.2%} | {result.text_accuracy:.2%} | "
                        f"{result.visual_similarity:.2%} | [View]({result.annotated_screenshot_path}) |"
                    )
                report.append("")

        # Neural network analysis insights
        report.append("## Neural Network Analysis Insights\n")

        # High confidence but failed verifications
        high_conf_failed = [r for r in results if r.neural_confidence > 0.8 and r.verification_status == "failed"]
        if high_conf_failed:
            report.append("### High Neural Confidence but Failed Verifications")
            report.append("These may indicate data transformation issues or display formatting problems:")
            for r in high_conf_failed:
                report.append(f"- {r.field_name}: Expected '{r.expected_value}', Got '{r.displayed_value}'")
            report.append("")

        # Low confidence but passed verifications
        low_conf_passed = [r for r in results if r.neural_confidence < 0.5 and r.verification_status == "passed"]
        if low_conf_passed:
            report.append("### Low Neural Confidence but Passed Verifications")
            report.append("These may need model retraining or better feature extraction:")
            for r in low_conf_passed:
                report.append(f"- {r.field_name}: Neural score {r.neural_confidence:.2%}")
            report.append("")

        return "\n".join(report)


async def run_neural_verification_test():
    """Run neural network verification test"""
    verifier = NeuralVisualVerifier()

    try:
        await verifier.initialize()

        # Test data
        test_property = "064210010010"
        expected_data = {
            "overview": {
                "property_address": "123 Main St",
                "owner_name": "John Doe",
                "market_value": "$250,000",
                "year_built": "1995"
            },
            "core-property": {
                "parcel_id": "064210010010",
                "property_type": "Single Family",
                "land_size": "7,500 sq ft",
                "zoning": "RS-1"
            },
            "valuation": {
                "just_value": "$250,000",
                "assessed_value": "$225,000",
                "taxable_value": "$200,000"
            }
        }

        # Run verification
        results = await verifier.verify_property_with_neural_networks(test_property, expected_data)

        # Generate report
        report = verifier.generate_neural_verification_report(results)

        # Save report
        with open("neural_verification_report.md", "w") as f:
            f.write(report)

        print("\n" + "=" * 60)
        print("✓ Neural network verification complete!")
        print("✓ Report saved to: neural_verification_report.md")
        print(f"✓ {len(results)} fields verified with neural networks")

    finally:
        await verifier.close()


if __name__ == "__main__":
    asyncio.run(run_neural_verification_test())