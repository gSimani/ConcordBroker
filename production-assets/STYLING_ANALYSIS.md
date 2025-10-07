# ConcordBroker.com Production Styling Analysis

## Files Downloaded Successfully
- **Main CSS**: `index-C-q-SXQP.css` (104KB)
- **Main JS**: `index-ClMffTrI.js` (60KB)
- **Vendor bundles**:
  - `vendor-react-C3NQ-yZE.js` (162KB)
  - `vendor-ui-BaixMg1S.js` (194KB)
  - `vendor-data-BjoAjfOE.js` (184KB)
  - `vendor-utils-rSftHtKs.js` (91KB)

## Key Color Scheme (CSS Custom Properties)

### Navy & Gold Colors
```css
--navy: 210 33% 31%;
--navy-dark: 210 38% 26%;
--gold: 42 74% 58%;
--gold-light: 44 84% 85%;
--gray-elegant: 210 12% 55%;
```

### Brand Colors
```css
--brand-50: 240 100% 98%;
--brand-100: 240 100% 95%;
--brand-200: 240 94% 90%;
--brand-300: 240 79% 80%;
--brand-400: 240 68% 68%;
--brand-500: 240 56% 56%;
--brand-600: 240 56% 45%;
--brand-700: 240 56% 35%;
--brand-800: 240 56% 25%;
--brand-900: 240 56% 15%;
--brand-950: 240 56% 8%;
```

### Core UI Colors
```css
--background: 0 0% 100%;
--foreground: 222.2 84% 4.9%;
--card: 0 0% 100%;
--card-foreground: 222.2 84% 4.9%;
--primary: 222.2 47.4% 11.2%;
--primary-foreground: 210 40% 98%;
--secondary: 210 40% 96.1%;
--border: 214.3 31.8% 91.4%;
--radius: .5rem;
```

### Gray Scale
```css
--gray-25: 210 20% 98%;
--gray-50: 210 20% 95%;
--gray-100: 210 20% 90%;
--gray-200: 210 16% 82%;
--gray-300: 210 14% 72%;
--gray-400: 210 12% 55%;
--gray-500: 210 10% 40%;
--gray-600: 210 12% 30%;
--gray-700: 210 14% 22%;
--gray-800: 210 16% 16%;
--gray-900: 210 20% 10%;
--gray-950: 210 24% 6%;
```

## Typography

### Primary Font
```css
font-family: "Josefin Sans", sans-serif;
font-weight: 300; /* Light weight as default */
```

### Imported from Google Fonts
```css
@import "https://fonts.googleapis.com/css2?family=Josefin+Sans:wght@100;200;300;400;500;600;700&display=swap";
```

### Monospace Font
```css
font-family: "JetBrains Mono", monospace; /* For code elements */
```

## Glass Morphism Effects

### Standard Glass
```css
.glass {
  background: #ffffff0d;
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255,255,255,.1);
}
```

### Glass Card
```css
.glass-card {
  background: #ffffff1f;
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255,255,255,.15);
  box-shadow: 0 8px 32px #1f268726, 0 1px 1px #ffffff40 inset, 0 -1px 1px #0000000d inset;
}
```

### Dark Mode Glass
```css
.dark .glass {
  background: #ffffff05;
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255,255,255,.05);
}

.dark .glass-card {
  background: #ffffff0d;
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255,255,255,.1);
  box-shadow: 0 8px 32px #0006, 0 1px 1px #ffffff1a inset, 0 -1px 1px #0003 inset;
}
```

## Interactive Elements

### Interactive Class
```css
.interactive {
  transition: all .2s ease;
  cursor: pointer;
}

.interactive:hover {
  transform: translateY(-2px);
}

.interactive:active {
  transform: translateY(0);
}
```

### Primary Gradient Background
```css
.bg-gradient-primary {
  background: linear-gradient(135deg, hsl(var(--brand-500)), hsl(var(--brand-700)));
}
```

## Layout & Container

### Container
```css
.container {
  width: 100%;
  margin-right: auto;
  margin-left: auto;
  padding-right: 2rem;
  padding-left: 2rem;
}

@media (min-width: 1400px) {
  .container {
    max-width: 1400px;
  }
}
```

## Custom Scrollbar

```css
.custom-scrollbar::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}

.custom-scrollbar::-webkit-scrollbar-track {
  background: transparent;
}

.custom-scrollbar::-webkit-scrollbar-thumb {
  background: hsl(var(--gray-300));
  border-radius: 3px;
  transition: background-color .2s ease;
}

.custom-scrollbar::-webkit-scrollbar-thumb:hover {
  background: hsl(var(--gray-400));
}
```

## Animation Keyframes

### Animations
```css
@keyframes fadeInUp {
  0% { opacity: 0; transform: translateY(30px); }
  100% { opacity: 1; transform: translateY(0); }
}

@keyframes scaleIn {
  0% { opacity: 0; transform: scale(.9); }
  100% { opacity: 1; transform: scale(1); }
}

@keyframes float {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-10px); }
}

@keyframes pulse-glow {
  0%, 100% { box-shadow: 0 0 20px #3b82f666; }
  50% { box-shadow: 0 0 40px #3b82f6cc; }
}
```

## Status Indicators

### Status Dot
```css
.status-dot {
  position: relative;
  display: inline-flex;
  height: .5rem;
  width: .5rem;
  border-radius: 9999px;
}

.status-dot:before {
  animation: ping 1s cubic-bezier(0,0,.2,1) infinite;
  border-radius: 9999px;
  opacity: .75;
  content: "";
  background-color: inherit;
}
```

## Key CSS Framework

The site uses **Tailwind CSS** with extensive customization through CSS custom properties. The design follows a modern glass morphism aesthetic with:

1. **Navy and gold accent colors** for branding
2. **Josefin Sans** as the primary typeface
3. **Glass morphism effects** for cards and overlays
4. **Smooth animations** and interactions
5. **Responsive container** system
6. **Custom scrollbars** and UI elements
7. **Dark mode support** through CSS variables

## Property Cards Implementation

Based on the extracted styles, property cards would likely use:

- `glass-card` class for the glass morphism effect
- `interactive` class for hover animations
- Navy (`hsl(var(--navy))`) and gold (`hsl(var(--gold))`) for accents
- Border radius of `.5rem` (8px)
- Shadow patterns from the glass-card definition
- Josefin Sans typography at weight 300-500

## Recommended Implementation Strategy

1. **Use the exact CSS custom properties** for color consistency
2. **Import Josefin Sans** from Google Fonts
3. **Implement glass morphism cards** using the extracted patterns
4. **Apply interactive hover effects** for better UX
5. **Use the container system** for consistent layout
6. **Implement dark mode support** using the provided CSS variables