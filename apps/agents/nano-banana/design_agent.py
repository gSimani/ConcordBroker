#!/usr/bin/env python3
"""
Nano Banana Design Agent
=========================

AI-powered design generation using Google AI Studio (Gemini API).
Generates design assets, mockups, style variations, and UI/UX recommendations
for the ConcordBroker application.

API Configuration:
    Project: gen-lang-client-0357643652
    Project Number: 712858526586

Usage:
    from design_agent import NanoBananaDesignAgent

    agent = NanoBananaDesignAgent()

    # Generate a design concept
    concept = agent.generate_design_concept("property card with modern styling")

    # Generate CSS styles
    styles = agent.generate_css("button component with tiffany brand color")

    # Generate component code
    code = agent.generate_component("metric display card with sparkline")
"""

import os
import json
import base64
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Google AI Studio Configuration
GOOGLE_AI_CONFIG = {
    "project_name": "gen-lang-client-0357643652",
    "project_number": "712858526586",
    "api_key": os.getenv("GOOGLE_AI_API_KEY", "AIzaSyCeDczyc6zOYiX2y6MBmh-ojW9I_NCWWvg"),
    "api_endpoint": "https://generativelanguage.googleapis.com/v1beta",
    "model": "gemini-2.5-flash",  # Fast and capable model for design generation
    "model_pro": "gemini-2.5-pro",  # Pro model for complex design tasks
    "model_nano_banana": "gemini-2.5-flash-image",  # Nano Banana (image generation)
    "model_nano_banana_pro": "nano-banana-pro-preview",  # Nano Banana Pro (advanced)
}

# ConcordBroker Design Context
DESIGN_CONTEXT = """
You are a senior UI/UX designer for ConcordBroker, a Florida property analytics platform.

BRAND GUIDELINES:
- Primary Color (Tiffany): #0ABAB5 (trust, clarity, professional)
- Accent Color (Gold): #D4AF37 (premium, value, success)
- Background: Clean whites (#FFFFFF) and subtle grays (#F5F5F5, #FAFAFA)
- Typography: Inter font family
- Border Radius: 8px for cards, 4px for buttons
- Shadows: Subtle layered shadows for depth

DESIGN PRINCIPLES:
1. Progressive Disclosure - Show summary first, details on demand
2. Context Over Data - Numbers with meaning (trends, comparisons)
3. Action-Oriented - Every screen has a clear primary action
4. Mobile-First - Design for mobile, scale up to desktop
5. Accessibility - WCAG 2.2 AA compliant

TARGET USERS:
- Real estate investors
- Property analysts
- Tax deed buyers
- Title researchers

KEY DATA DISPLAYED:
- Property addresses and values
- Owner information
- Sales history with trends
- Tax deed opportunities
- Market analytics
"""


@dataclass
class DesignRequest:
    """Design generation request"""
    request_type: str  # concept, css, component, mockup
    description: str
    context: Optional[str] = None
    constraints: Optional[List[str]] = None
    style_preferences: Optional[Dict[str, str]] = None


@dataclass
class DesignResult:
    """Design generation result"""
    request_type: str
    content: str
    metadata: Dict[str, Any]
    timestamp: str


class NanoBananaDesignAgent:
    """
    AI-powered design generation agent using Google Gemini.

    Capabilities:
    - Generate design concepts and recommendations
    - Create CSS styles and Tailwind classes
    - Generate React component code
    - Create mockup descriptions
    - Suggest UI/UX improvements
    """

    def __init__(self, api_key: str = None):
        self.api_key = api_key or GOOGLE_AI_CONFIG["api_key"]
        self.api_endpoint = GOOGLE_AI_CONFIG["api_endpoint"]
        self.model = GOOGLE_AI_CONFIG["model"]
        self._client = None
        self._initialized = False

        logger.info(f"NanoBananaDesignAgent initialized with model: {self.model}")

    def initialize(self) -> bool:
        """Initialize the Google AI client"""
        try:
            import google.generativeai as genai

            genai.configure(api_key=self.api_key)
            self._client = genai.GenerativeModel(self.model)
            self._initialized = True

            logger.info("Google AI client initialized successfully")
            return True

        except ImportError:
            logger.error("google-generativeai not installed. Install with: pip install google-generativeai")
            return False
        except Exception as e:
            logger.error(f"Failed to initialize Google AI client: {e}")
            return False

    def _ensure_initialized(self):
        """Ensure the client is initialized"""
        if not self._initialized:
            if not self.initialize():
                raise RuntimeError("Failed to initialize Google AI client")

    def generate_design_concept(
        self,
        description: str,
        component_type: str = "general",
        constraints: List[str] = None
    ) -> DesignResult:
        """
        Generate a design concept based on description.

        Args:
            description: What to design
            component_type: Type of component (card, page, section, etc.)
            constraints: Design constraints to follow

        Returns:
            DesignResult with concept details
        """
        self._ensure_initialized()

        prompt = f"""{DESIGN_CONTEXT}

TASK: Generate a detailed design concept for the following:

Component Type: {component_type}
Description: {description}
Constraints: {constraints or 'None specified'}

Provide:
1. Visual Description - Detailed description of how it should look
2. Layout Structure - How elements are arranged
3. Color Usage - Specific colors from the brand palette
4. Typography - Font sizes and weights
5. Spacing - Margins and padding
6. Interactive States - Hover, focus, active states
7. Accessibility Notes - ARIA labels, keyboard navigation
8. Responsive Behavior - How it adapts to different screen sizes

Format your response as structured JSON.
"""

        try:
            response = self._client.generate_content(prompt)
            content = response.text

            return DesignResult(
                request_type="concept",
                content=content,
                metadata={
                    "component_type": component_type,
                    "description": description,
                    "model": self.model
                },
                timestamp=datetime.now().isoformat()
            )

        except Exception as e:
            logger.error(f"Failed to generate design concept: {e}")
            raise

    def generate_css(
        self,
        description: str,
        use_tailwind: bool = True,
        include_dark_mode: bool = True
    ) -> DesignResult:
        """
        Generate CSS styles or Tailwind classes.

        Args:
            description: What to style
            use_tailwind: Generate Tailwind classes instead of raw CSS
            include_dark_mode: Include dark mode variants

        Returns:
            DesignResult with CSS/Tailwind classes
        """
        self._ensure_initialized()

        format_type = "Tailwind CSS classes" if use_tailwind else "raw CSS"

        prompt = f"""{DESIGN_CONTEXT}

TASK: Generate {format_type} for the following:

Description: {description}
Include Dark Mode: {include_dark_mode}

Requirements:
- Use the brand color palette
- Ensure WCAG 2.2 AA color contrast
- Include hover, focus, and active states
- {"Use Tailwind utility classes" if use_tailwind else "Write clean, maintainable CSS"}
- Add transitions for smooth interactions

{"Return Tailwind classes as a className string." if use_tailwind else "Return CSS with proper selectors."}
"""

        try:
            response = self._client.generate_content(prompt)
            content = response.text

            return DesignResult(
                request_type="css",
                content=content,
                metadata={
                    "use_tailwind": use_tailwind,
                    "include_dark_mode": include_dark_mode,
                    "model": self.model
                },
                timestamp=datetime.now().isoformat()
            )

        except Exception as e:
            logger.error(f"Failed to generate CSS: {e}")
            raise

    def generate_component(
        self,
        description: str,
        framework: str = "react",
        typescript: bool = True
    ) -> DesignResult:
        """
        Generate a UI component code.

        Args:
            description: Component description
            framework: react, vue, or svelte
            typescript: Use TypeScript

        Returns:
            DesignResult with component code
        """
        self._ensure_initialized()

        lang = "TypeScript" if typescript else "JavaScript"

        prompt = f"""{DESIGN_CONTEXT}

TASK: Generate a {framework.title()} component in {lang}:

Description: {description}

Requirements:
- Use Tailwind CSS for styling
- Follow the ConcordBroker design system
- Include proper TypeScript types (if applicable)
- Add JSDoc comments
- Include accessibility attributes (aria-*, role)
- Make it fully responsive
- Export as a named export

Additional Guidelines:
- Use Lucide React for icons
- Use the cn() utility for class merging
- Include loading and error states if applicable
- Add proper prop validation

Return ONLY the code, no explanation.
"""

        try:
            response = self._client.generate_content(prompt)
            content = response.text

            # Clean up code blocks if present
            if "```" in content:
                # Extract code from markdown code blocks
                import re
                code_match = re.search(r'```(?:tsx?|jsx?|typescript|javascript)?\n?(.*?)```', content, re.DOTALL)
                if code_match:
                    content = code_match.group(1).strip()

            return DesignResult(
                request_type="component",
                content=content,
                metadata={
                    "framework": framework,
                    "typescript": typescript,
                    "model": self.model
                },
                timestamp=datetime.now().isoformat()
            )

        except Exception as e:
            logger.error(f"Failed to generate component: {e}")
            raise

    def suggest_improvements(
        self,
        current_design: str,
        context: str = None
    ) -> DesignResult:
        """
        Suggest UX/UI improvements for existing design.

        Args:
            current_design: Description or code of current design
            context: Additional context about the design

        Returns:
            DesignResult with improvement suggestions
        """
        self._ensure_initialized()

        prompt = f"""{DESIGN_CONTEXT}

TASK: Review the following design and suggest improvements:

Current Design:
{current_design}

Additional Context: {context or 'None provided'}

Provide improvements in these categories:
1. Visual Hierarchy - How to better organize information
2. Usability - How to make it easier to use
3. Accessibility - How to make it more accessible
4. Performance - How to make it faster
5. Mobile Experience - How to improve on small screens
6. Micro-interactions - Animations and feedback
7. Data Presentation - How to better show the data

For each suggestion:
- Explain the problem
- Provide the solution
- Show example code or design specs

Format as structured JSON with priority levels (high, medium, low).
"""

        try:
            response = self._client.generate_content(prompt)
            content = response.text

            return DesignResult(
                request_type="improvements",
                content=content,
                metadata={
                    "context": context,
                    "model": self.model
                },
                timestamp=datetime.now().isoformat()
            )

        except Exception as e:
            logger.error(f"Failed to generate improvements: {e}")
            raise

    def generate_color_palette(
        self,
        base_color: str = "#0ABAB5",
        style: str = "professional"
    ) -> DesignResult:
        """
        Generate a complete color palette from a base color.

        Args:
            base_color: Primary brand color
            style: professional, playful, minimal, bold

        Returns:
            DesignResult with color palette
        """
        self._ensure_initialized()

        prompt = f"""{DESIGN_CONTEXT}

TASK: Generate a complete color palette for a real estate analytics platform.

Base Color: {base_color}
Style: {style}

Generate:
1. Primary scale (50-900)
2. Secondary/Accent scale
3. Neutral scale (50-900)
4. Semantic colors (success, warning, error, info)
5. Chart colors (8 distinct, color-blind safe)
6. Background colors (light and dark mode)
7. Text colors (primary, secondary, tertiary, disabled)
8. Border colors

For each color provide:
- Hex value
- RGB value
- CSS variable name
- Usage description

Format as JSON with proper structure.
"""

        try:
            response = self._client.generate_content(prompt)
            content = response.text

            return DesignResult(
                request_type="palette",
                content=content,
                metadata={
                    "base_color": base_color,
                    "style": style,
                    "model": self.model
                },
                timestamp=datetime.now().isoformat()
            )

        except Exception as e:
            logger.error(f"Failed to generate color palette: {e}")
            raise

    def generate_mockup_spec(
        self,
        page_name: str,
        page_purpose: str,
        data_to_display: List[str]
    ) -> DesignResult:
        """
        Generate a detailed mockup specification for a page.

        Args:
            page_name: Name of the page
            page_purpose: What the page is for
            data_to_display: List of data elements to show

        Returns:
            DesignResult with mockup specification
        """
        self._ensure_initialized()

        prompt = f"""{DESIGN_CONTEXT}

TASK: Create a detailed mockup specification for a page.

Page Name: {page_name}
Purpose: {page_purpose}
Data to Display: {json.dumps(data_to_display)}

Provide:
1. Page Layout (ASCII art wireframe)
2. Component List (all components needed)
3. Data Mapping (which data goes where)
4. User Flows (how users interact)
5. Responsive Breakpoints (mobile, tablet, desktop)
6. State Variations (loading, empty, error, success)
7. Animation Specs (what animates and how)
8. Accessibility Checklist

Include specific:
- Component dimensions
- Spacing values (in pixels)
- Typography specs (size, weight, color)
- Color assignments
- Icon names (from Lucide)

Format as structured markdown with code blocks for wireframes.
"""

        try:
            response = self._client.generate_content(prompt)
            content = response.text

            return DesignResult(
                request_type="mockup",
                content=content,
                metadata={
                    "page_name": page_name,
                    "page_purpose": page_purpose,
                    "data_elements": data_to_display,
                    "model": self.model
                },
                timestamp=datetime.now().isoformat()
            )

        except Exception as e:
            logger.error(f"Failed to generate mockup spec: {e}")
            raise


# Convenience functions
_agent = None

def get_agent() -> NanoBananaDesignAgent:
    """Get or create the global design agent instance"""
    global _agent
    if _agent is None:
        _agent = NanoBananaDesignAgent()
    return _agent


def generate_design(description: str, design_type: str = "concept") -> str:
    """
    Quick function to generate a design.

    Args:
        description: What to design
        design_type: concept, css, component, improvements, palette, mockup

    Returns:
        Generated design content
    """
    agent = get_agent()

    if design_type == "concept":
        result = agent.generate_design_concept(description)
    elif design_type == "css":
        result = agent.generate_css(description)
    elif design_type == "component":
        result = agent.generate_component(description)
    elif design_type == "improvements":
        result = agent.suggest_improvements(description)
    elif design_type == "palette":
        result = agent.generate_color_palette()
    elif design_type == "mockup":
        result = agent.generate_mockup_spec(description, "General purpose", [])
    else:
        raise ValueError(f"Unknown design type: {design_type}")

    return result.content


# CLI Interface
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Nano Banana Design Agent")
    parser.add_argument("--type", choices=["concept", "css", "component", "improvements", "palette", "mockup"],
                       default="concept", help="Type of design to generate")
    parser.add_argument("--description", "-d", required=True, help="Design description")
    parser.add_argument("--output", "-o", help="Output file (optional)")

    args = parser.parse_args()

    print(f"\n{'='*60}")
    print("Nano Banana Design Agent")
    print(f"{'='*60}")
    print(f"Type: {args.type}")
    print(f"Description: {args.description}")
    print(f"{'='*60}\n")

    try:
        result = generate_design(args.description, args.type)

        if args.output:
            with open(args.output, 'w') as f:
                f.write(result)
            print(f"Output saved to: {args.output}")
        else:
            print(result)

    except Exception as e:
        print(f"Error: {e}")
        exit(1)
