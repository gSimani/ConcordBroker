"""
OpenCV Property Image Analysis System
Advanced computer vision for real estate property analysis
"""

import cv2
import numpy as np
import asyncio
import aiohttp
from typing import Dict, Any, List, Tuple, Optional
import base64
from io import BytesIO
from PIL import Image
import logging
from dataclasses import dataclass
from enum import Enum

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FeatureType(Enum):
    """Types of features to detect in property images"""
    POOL = "pool"
    GARAGE = "garage"
    LAWN = "lawn"
    DRIVEWAY = "driveway"
    FENCE = "fence"
    ROOF_CONDITION = "roof_condition"
    LANDSCAPING = "landscaping"
    EXTERIOR_CONDITION = "exterior_condition"

@dataclass
class ImageAnalysisResult:
    """Results from image analysis"""
    features_detected: Dict[str, Any]
    quality_metrics: Dict[str, float]
    condition_assessment: Dict[str, Any]
    recommendations: List[str]
    confidence_scores: Dict[str, float]

class PropertyImageAnalyzer:
    """Advanced property image analysis using OpenCV"""

    def __init__(self):
        # Initialize feature detectors
        self.sift = cv2.SIFT_create()
        self.orb = cv2.ORB_create()

        # Color ranges for feature detection
        self.color_ranges = {
            'pool_blue': {
                'lower': np.array([100, 50, 50]),
                'upper': np.array([130, 255, 255])
            },
            'grass_green': {
                'lower': np.array([40, 40, 40]),
                'upper': np.array([80, 255, 255])
            },
            'roof_dark': {
                'lower': np.array([0, 0, 0]),
                'upper': np.array([180, 255, 50])
            }
        }

    async def analyze_property_image(self, image_url: str) -> ImageAnalysisResult:
        """Comprehensive analysis of property image"""
        try:
            # Download image
            image = await self._download_image(image_url)

            # Run analyses in parallel
            results = await asyncio.gather(
                self._detect_pool(image),
                self._analyze_lawn_condition(image),
                self._assess_roof_condition(image),
                self._detect_structural_features(image),
                self._analyze_lighting_quality(image),
                self._detect_damage_indicators(image)
            )

            # Combine results
            features = {
                'has_pool': results[0]['detected'],
                'pool_size': results[0].get('size_estimate'),
                'lawn_condition': results[1]['condition'],
                'lawn_coverage': results[1]['coverage_percentage'],
                'roof_condition': results[2]['condition'],
                'roof_issues': results[2]['issues'],
                'structural_features': results[3],
                'lighting_quality': results[4],
                'damage_indicators': results[5]
            }

            # Calculate quality metrics
            quality_metrics = self._calculate_quality_metrics(image)

            # Assess overall condition
            condition = self._assess_overall_condition(features, quality_metrics)

            # Generate recommendations
            recommendations = self._generate_recommendations(features, condition)

            # Calculate confidence scores
            confidence = self._calculate_confidence_scores(features)

            return ImageAnalysisResult(
                features_detected=features,
                quality_metrics=quality_metrics,
                condition_assessment=condition,
                recommendations=recommendations,
                confidence_scores=confidence
            )

        except Exception as e:
            logger.error(f"Error analyzing image: {e}")
            raise

    async def _download_image(self, url: str) -> np.ndarray:
        """Download and convert image to OpenCV format"""
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    image_data = await response.read()
                    nparr = np.frombuffer(image_data, np.uint8)
                    image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                    return image
                else:
                    raise Exception(f"Failed to download image: {response.status}")

    async def _detect_pool(self, image: np.ndarray) -> Dict[str, Any]:
        """Detect swimming pool in property image"""
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

        # Create mask for blue water
        mask = cv2.inRange(
            hsv,
            self.color_ranges['pool_blue']['lower'],
            self.color_ranges['pool_blue']['upper']
        )

        # Apply morphological operations
        kernel = np.ones((5, 5), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

        # Find contours
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # Look for pool-shaped contours
        pool_detected = False
        pool_size = 0

        for contour in contours:
            area = cv2.contourArea(contour)
            if area > 1000:  # Minimum area threshold
                perimeter = cv2.arcLength(contour, True)
                circularity = 4 * np.pi * area / (perimeter * perimeter)

                # Pools typically have regular shapes
                if circularity > 0.5:
                    pool_detected = True
                    pool_size = max(pool_size, area)

        return {
            'detected': pool_detected,
            'size_estimate': pool_size,
            'confidence': 0.8 if pool_detected else 0.0
        }

    async def _analyze_lawn_condition(self, image: np.ndarray) -> Dict[str, Any]:
        """Analyze lawn/landscaping condition"""
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

        # Create mask for green areas
        mask = cv2.inRange(
            hsv,
            self.color_ranges['grass_green']['lower'],
            self.color_ranges['grass_green']['upper']
        )

        # Calculate coverage
        total_pixels = image.shape[0] * image.shape[1]
        green_pixels = cv2.countNonZero(mask)
        coverage_percentage = (green_pixels / total_pixels) * 100

        # Analyze green color distribution for health
        green_areas = cv2.bitwise_and(image, image, mask=mask)
        if green_pixels > 0:
            mean_green = cv2.mean(green_areas, mask=mask)
            # Higher green channel indicates healthier lawn
            health_score = mean_green[1] / 255.0
        else:
            health_score = 0

        # Determine condition
        if coverage_percentage > 40 and health_score > 0.6:
            condition = "excellent"
        elif coverage_percentage > 25 and health_score > 0.4:
            condition = "good"
        elif coverage_percentage > 10:
            condition = "fair"
        else:
            condition = "poor"

        return {
            'condition': condition,
            'coverage_percentage': coverage_percentage,
            'health_score': health_score
        }

    async def _assess_roof_condition(self, image: np.ndarray) -> Dict[str, Any]:
        """Assess roof condition from aerial view"""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # Edge detection for structural analysis
        edges = cv2.Canny(gray, 50, 150)

        # Line detection for roof structure
        lines = cv2.HoughLinesP(edges, 1, np.pi/180, 100, minLineLength=100, maxLineGap=10)

        issues = []
        condition = "good"

        if lines is not None:
            # Analyze line patterns
            horizontal_lines = 0
            vertical_lines = 0

            for line in lines:
                x1, y1, x2, y2 = line[0]
                angle = np.abs(np.arctan2(y2 - y1, x2 - x1) * 180 / np.pi)

                if angle < 30 or angle > 150:
                    horizontal_lines += 1
                elif 60 < angle < 120:
                    vertical_lines += 1

            # Check for irregular patterns
            if horizontal_lines < 5 or vertical_lines < 5:
                issues.append("irregular_structure")
                condition = "fair"

        # Check for color consistency (damage/wear indicators)
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        roof_mask = cv2.inRange(
            hsv,
            self.color_ranges['roof_dark']['lower'],
            self.color_ranges['roof_dark']['upper']
        )

        # Calculate color variance
        if cv2.countNonZero(roof_mask) > 0:
            roof_area = cv2.bitwise_and(image, image, mask=roof_mask)
            variance = cv2.meanStdDev(roof_area, mask=roof_mask)[1]

            if np.mean(variance) > 50:
                issues.append("color_inconsistency")
                condition = "needs_inspection"

        return {
            'condition': condition,
            'issues': issues,
            'structural_lines_detected': len(lines) if lines is not None else 0
        }

    async def _detect_structural_features(self, image: np.ndarray) -> Dict[str, Any]:
        """Detect structural features like windows, doors, garage"""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # Use cascade classifiers if available
        features = {
            'windows_detected': 0,
            'doors_detected': 0,
            'garage_detected': False
        }

        # Simple rectangle detection for windows/doors
        edges = cv2.Canny(gray, 50, 150)
        contours, _ = cv2.findContours(edges, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

        rectangular_features = 0
        for contour in contours:
            approx = cv2.approxPolyDP(contour, 0.02 * cv2.arcLength(contour, True), True)
            if len(approx) == 4:  # Rectangle
                area = cv2.contourArea(contour)
                if 1000 < area < 50000:  # Size range for windows/doors
                    rectangular_features += 1

        features['rectangular_features'] = rectangular_features

        # Detect garage by looking for large rectangular area at ground level
        height, width = image.shape[:2]
        lower_third = image[2*height//3:, :]
        gray_lower = cv2.cvtColor(lower_third, cv2.COLOR_BGR2GRAY)

        edges_lower = cv2.Canny(gray_lower, 50, 150)
        contours_lower, _ = cv2.findContours(edges_lower, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        for contour in contours_lower:
            area = cv2.contourArea(contour)
            if area > 10000:  # Large area threshold
                features['garage_detected'] = True
                break

        return features

    async def _analyze_lighting_quality(self, image: np.ndarray) -> Dict[str, str]:
        """Analyze image lighting quality"""
        # Convert to LAB color space
        lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
        l_channel = lab[:, :, 0]

        # Calculate lighting metrics
        mean_brightness = np.mean(l_channel)
        std_brightness = np.std(l_channel)

        # Determine lighting quality
        if 60 < mean_brightness < 200 and std_brightness < 60:
            quality = "good"
        elif 40 < mean_brightness < 220:
            quality = "acceptable"
        else:
            quality = "poor"

        return {
            'quality': quality,
            'mean_brightness': float(mean_brightness),
            'uniformity': float(1 - (std_brightness / 255))
        }

    async def _detect_damage_indicators(self, image: np.ndarray) -> List[str]:
        """Detect potential damage indicators"""
        indicators = []

        # Check for dark spots (potential water damage/stains)
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        _, dark_areas = cv2.threshold(gray, 50, 255, cv2.THRESH_BINARY_INV)
        dark_ratio = cv2.countNonZero(dark_areas) / (gray.shape[0] * gray.shape[1])

        if dark_ratio > 0.1:
            indicators.append("dark_spots_detected")

        # Check for color anomalies
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        saturation = hsv[:, :, 1]

        if np.mean(saturation) < 30:
            indicators.append("faded_colors")

        # Edge detection for cracks
        edges = cv2.Canny(gray, 100, 200)
        edge_ratio = cv2.countNonZero(edges) / (edges.shape[0] * edges.shape[1])

        if edge_ratio > 0.15:
            indicators.append("excessive_edges_possible_damage")

        return indicators

    def _calculate_quality_metrics(self, image: np.ndarray) -> Dict[str, float]:
        """Calculate image quality metrics"""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # Sharpness (Laplacian variance)
        laplacian = cv2.Laplacian(gray, cv2.CV_64F)
        sharpness = laplacian.var()

        # Contrast
        contrast = gray.std()

        # Noise estimate
        noise = cv2.meanStdDev(gray)[1][0][0]

        # Color richness
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        saturation = hsv[:, :, 1]
        color_richness = np.mean(saturation)

        return {
            'sharpness': float(sharpness),
            'contrast': float(contrast),
            'noise_level': float(noise),
            'color_richness': float(color_richness),
            'overall_quality': float(min(100, (sharpness / 100 + contrast / 50 + color_richness / 255) * 33.33))
        }

    def _assess_overall_condition(self, features: Dict, metrics: Dict) -> Dict[str, Any]:
        """Assess overall property condition"""
        condition_score = 70  # Base score

        # Adjust based on features
        if features.get('lawn_condition') == 'excellent':
            condition_score += 10
        elif features.get('lawn_condition') == 'poor':
            condition_score -= 15

        if features.get('roof_condition') == 'good':
            condition_score += 10
        elif features.get('roof_condition') == 'needs_inspection':
            condition_score -= 20

        if features.get('has_pool'):
            condition_score += 5

        if len(features.get('damage_indicators', [])) > 0:
            condition_score -= 10 * len(features['damage_indicators'])

        # Adjust based on image quality
        if metrics['overall_quality'] > 70:
            confidence = "high"
        elif metrics['overall_quality'] > 40:
            confidence = "medium"
        else:
            confidence = "low"

        # Determine condition category
        if condition_score >= 80:
            category = "excellent"
        elif condition_score >= 60:
            category = "good"
        elif condition_score >= 40:
            category = "fair"
        else:
            category = "needs_attention"

        return {
            'score': condition_score,
            'category': category,
            'confidence': confidence
        }

    def _generate_recommendations(self, features: Dict, condition: Dict) -> List[str]:
        """Generate property recommendations"""
        recommendations = []

        if features.get('lawn_condition') in ['fair', 'poor']:
            recommendations.append("Consider landscaping improvements")

        if features.get('roof_condition') == 'needs_inspection':
            recommendations.append("Schedule professional roof inspection")

        if len(features.get('damage_indicators', [])) > 0:
            recommendations.append("Investigate potential damage areas")

        if not features.get('has_pool') and features.get('lawn_coverage', 0) > 50:
            recommendations.append("Property has space for pool installation")

        if condition['category'] == 'excellent':
            recommendations.append("Property shows excellent maintenance")
        elif condition['category'] == 'needs_attention':
            recommendations.append("Property requires immediate attention")

        return recommendations

    def _calculate_confidence_scores(self, features: Dict) -> Dict[str, float]:
        """Calculate confidence scores for each detection"""
        confidence = {}

        # Base confidence on feature detection
        if 'has_pool' in features:
            confidence['pool_detection'] = 0.85 if features['has_pool'] else 0.95

        if 'lawn_condition' in features:
            coverage = features.get('lawn_coverage', 0)
            confidence['lawn_analysis'] = min(1.0, coverage / 50)

        if 'roof_condition' in features:
            lines = features.get('structural_lines_detected', 0)
            confidence['roof_assessment'] = min(1.0, lines / 20)

        confidence['overall'] = np.mean(list(confidence.values()))

        return confidence

class PropertyImageBatchProcessor:
    """Process multiple property images efficiently"""

    def __init__(self, analyzer: PropertyImageAnalyzer):
        self.analyzer = analyzer

    async def process_batch(self, image_urls: List[str], max_concurrent: int = 5) -> List[ImageAnalysisResult]:
        """Process multiple images concurrently"""
        semaphore = asyncio.Semaphore(max_concurrent)

        async def process_with_limit(url):
            async with semaphore:
                try:
                    return await self.analyzer.analyze_property_image(url)
                except Exception as e:
                    logger.error(f"Failed to process {url}: {e}")
                    return None

        results = await asyncio.gather(*[process_with_limit(url) for url in image_urls])
        return [r for r in results if r is not None]

# Integration with MCP Server
class MCPImageAnalysisIntegration:
    """Integration with MCP Server for image analysis"""

    def __init__(self, mcp_url: str = "http://localhost:3001", api_key: str = "concordbroker-mcp-key"):
        self.mcp_url = mcp_url
        self.api_key = api_key
        self.analyzer = PropertyImageAnalyzer()

    async def analyze_and_report(self, property_id: str, image_urls: List[str]):
        """Analyze images and report to MCP Server"""
        # Analyze images
        processor = PropertyImageBatchProcessor(self.analyzer)
        results = await processor.process_batch(image_urls)

        # Prepare report
        report = {
            'property_id': property_id,
            'timestamp': np.datetime64('now').tolist(),
            'images_analyzed': len(results),
            'aggregate_condition': self._aggregate_conditions(results),
            'key_features': self._extract_key_features(results),
            'recommendations': self._consolidate_recommendations(results),
            'detailed_results': [self._serialize_result(r) for r in results]
        }

        # Send to MCP Server
        async with aiohttp.ClientSession() as session:
            headers = {
                'x-api-key': self.api_key,
                'Content-Type': 'application/json'
            }
            async with session.post(
                f"{self.mcp_url}/api/property-analysis/images",
                json=report,
                headers=headers
            ) as response:
                if response.status == 200:
                    logger.info(f"Successfully reported analysis for {property_id}")
                else:
                    logger.error(f"Failed to report analysis: {response.status}")

        return report

    def _aggregate_conditions(self, results: List[ImageAnalysisResult]) -> Dict:
        """Aggregate condition assessments"""
        if not results:
            return {}

        scores = [r.condition_assessment['score'] for r in results]
        categories = [r.condition_assessment['category'] for r in results]

        return {
            'average_score': np.mean(scores),
            'min_score': min(scores),
            'max_score': max(scores),
            'most_common_category': max(set(categories), key=categories.count)
        }

    def _extract_key_features(self, results: List[ImageAnalysisResult]) -> Dict:
        """Extract key features from all results"""
        features = {}
        for result in results:
            for key, value in result.features_detected.items():
                if key not in features:
                    features[key] = []
                features[key].append(value)

        # Aggregate features
        aggregated = {}
        for key, values in features.items():
            if isinstance(values[0], bool):
                aggregated[key] = any(values)
            elif isinstance(values[0], (int, float)):
                aggregated[key] = np.mean(values)
            else:
                aggregated[key] = max(set(values), key=values.count)

        return aggregated

    def _consolidate_recommendations(self, results: List[ImageAnalysisResult]) -> List[str]:
        """Consolidate recommendations from all results"""
        all_recommendations = []
        for result in results:
            all_recommendations.extend(result.recommendations)

        # Remove duplicates and prioritize
        unique_recommendations = list(set(all_recommendations))
        return unique_recommendations[:5]  # Top 5 recommendations

    def _serialize_result(self, result: ImageAnalysisResult) -> Dict:
        """Serialize analysis result for JSON"""
        return {
            'features': result.features_detected,
            'quality_metrics': result.quality_metrics,
            'condition': result.condition_assessment,
            'recommendations': result.recommendations,
            'confidence': result.confidence_scores
        }

# Example usage
async def main():
    """Example usage of OpenCV property analyzer"""
    analyzer = PropertyImageAnalyzer()

    # Example image URL
    image_url = "https://example.com/property_image.jpg"

    try:
        result = await analyzer.analyze_property_image(image_url)
        print(f"Analysis complete: {result.condition_assessment['category']}")
        print(f"Features detected: {result.features_detected}")
        print(f"Recommendations: {result.recommendations}")
    except Exception as e:
        print(f"Analysis failed: {e}")

if __name__ == "__main__":
    asyncio.run(main())