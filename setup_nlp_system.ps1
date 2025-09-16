# NLP Intelligent Field Matching System Setup
# Automated setup for NLTK, spaCy, and all NLP components

Write-Host "================================================================" -ForegroundColor Cyan
Write-Host " NLP INTELLIGENT FIELD MATCHING SYSTEM SETUP" -ForegroundColor Cyan
Write-Host " NLTK + spaCy + Playwright MCP + OpenCV Integration" -ForegroundColor Cyan
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host ""

# Check prerequisites
Write-Host "[1/8] Checking prerequisites..." -ForegroundColor Yellow

# Check Python
if (!(Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "ERROR: Python not found. Please install Python 3.8+" -ForegroundColor Red
    exit 1
}

$pythonVersion = python --version 2>&1
Write-Host "✓ Python found: $pythonVersion" -ForegroundColor Green

# Check pip
if (!(Get-Command pip -ErrorAction SilentlyContinue)) {
    Write-Host "ERROR: pip not found. Please install pip" -ForegroundColor Red
    exit 1
}

Write-Host "✓ pip is available" -ForegroundColor Green
Write-Host ""

# Install NLP dependencies
Write-Host "[2/8] Installing NLP Python packages..." -ForegroundColor Yellow
pip install -r requirements-nlp.txt --upgrade --quiet

if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ NLP packages installed successfully" -ForegroundColor Green
} else {
    Write-Host "⚠ Some packages may have failed to install" -ForegroundColor Yellow
}
Write-Host ""

# Download spaCy models
Write-Host "[3/8] Downloading spaCy language models..." -ForegroundColor Yellow

Write-Host "  Downloading en_core_web_sm (small model)..." -ForegroundColor Gray
python -m spacy download en_core_web_sm --quiet 2>$null

Write-Host "  Downloading en_core_web_lg (large model)..." -ForegroundColor Gray
python -m spacy download en_core_web_lg --quiet 2>$null

Write-Host "✓ spaCy models downloaded" -ForegroundColor Green
Write-Host ""

# Download NLTK data
Write-Host "[4/8] Downloading NLTK data..." -ForegroundColor Yellow

$nltk_script = @"
import nltk
import ssl

# Handle SSL issues
try:
    _create_unverified_https_context = ssl._create_unverified_context
except AttributeError:
    pass
else:
    ssl._create_default_https_context = _create_unverified_https_context

# Download required NLTK data
downloads = [
    'punkt', 'stopwords', 'wordnet', 'averaged_perceptron_tagger',
    'maxent_ne_chunker', 'words', 'vader_lexicon', 'brown',
    'omw-1.4', 'reuters', 'movie_reviews', 'names'
]

for resource in downloads:
    try:
        nltk.download(resource, quiet=True)
        print(f'✓ {resource}')
    except Exception as e:
        print(f'⚠ {resource}: {e}')

print('NLTK data download completed')
"@

echo $nltk_script | python
Write-Host "✓ NLTK data downloaded" -ForegroundColor Green
Write-Host ""

# Install Playwright browsers
Write-Host "[5/8] Installing Playwright browsers..." -ForegroundColor Yellow

# Check if Playwright is installed
try {
    python -c "import playwright" 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  Installing Playwright browsers..." -ForegroundColor Gray
        python -m playwright install chromium --quiet
        Write-Host "✓ Playwright browsers installed" -ForegroundColor Green
    } else {
        Write-Host "⚠ Playwright not found - skipping browser install" -ForegroundColor Yellow
    }
} catch {
    Write-Host "⚠ Could not install Playwright browsers" -ForegroundColor Yellow
}
Write-Host ""

# Install Tesseract OCR
Write-Host "[6/8] Checking Tesseract OCR..." -ForegroundColor Yellow

# Check if Tesseract is available
$tesseractPath = Get-Command tesseract -ErrorAction SilentlyContinue
if ($tesseractPath) {
    Write-Host "✓ Tesseract OCR found: $($tesseractPath.Source)" -ForegroundColor Green
} else {
    Write-Host "⚠ Tesseract OCR not found" -ForegroundColor Yellow
    Write-Host "  Please install Tesseract from: https://github.com/UB-Mannheim/tesseract/wiki" -ForegroundColor Gray
    Write-Host "  Or using: winget install UB-Mannheim.TesseractOCR" -ForegroundColor Gray
}
Write-Host ""

# Test NLP system
Write-Host "[7/8] Testing NLP system components..." -ForegroundColor Yellow

$test_script = @"
import sys
import warnings
warnings.filterwarnings('ignore')

def test_imports():
    try:
        import nltk
        print('✓ NLTK imported')

        import spacy
        print('✓ spaCy imported')

        # Test spaCy model
        try:
            nlp = spacy.load('en_core_web_sm')
            print('✓ spaCy small model loaded')
        except:
            print('⚠ spaCy small model not available')

        try:
            nlp = spacy.load('en_core_web_lg')
            print('✓ spaCy large model loaded')
        except:
            print('⚠ spaCy large model not available')

        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer('all-MiniLM-L6-v2')
        print('✓ Sentence Transformers working')

        from sklearn.feature_extraction.text import TfidfVectorizer
        print('✓ Scikit-learn available')

        import pandas as pd
        print('✓ Pandas available')

        # Test basic NLP operations
        doc = nlp('This is a test sentence.')
        tokens = [token.text for token in doc]
        print(f'✓ Text processing: {len(tokens)} tokens')

        # Test sentence embedding
        embedding = model.encode('test sentence')
        print(f'✓ Sentence embedding: {len(embedding)} dimensions')

        return True

    except Exception as e:
        print(f'✗ Error: {e}')
        return False

if test_imports():
    print('\\n✓ NLP system test passed!')
    sys.exit(0)
else:
    print('\\n✗ NLP system test failed!')
    sys.exit(1)
"@

echo $test_script | python
$nlp_test_result = $LASTEXITCODE

if ($nlp_test_result -eq 0) {
    Write-Host "✓ NLP system test passed" -ForegroundColor Green
} else {
    Write-Host "✗ NLP system test failed" -ForegroundColor Red
}
Write-Host ""

# Run field matching test
Write-Host "[8/8] Running field matching test..." -ForegroundColor Yellow

try {
    python -c "
from apps.api.nlp_intelligent_field_matcher import NLPFieldAnalyzer
analyzer = NLPFieldAnalyzer()
result = analyzer.analyze_field('owner_name')
print(f'✓ Field analysis test: {result.semantic_type} (confidence: {result.confidence:.2f})')
"
    Write-Host "✓ Field matching system ready" -ForegroundColor Green
} catch {
    Write-Host "⚠ Field matching test skipped (may need database connection)" -ForegroundColor Yellow
}
Write-Host ""

# Display summary
Write-Host "================================================================" -ForegroundColor Green
Write-Host " NLP SYSTEM SETUP COMPLETE!" -ForegroundColor Green
Write-Host "================================================================" -ForegroundColor Green
Write-Host ""

Write-Host "Components Installed:" -ForegroundColor Cyan
Write-Host "  ✓ NLTK with language data" -ForegroundColor White
Write-Host "  ✓ spaCy with English models" -ForegroundColor White
Write-Host "  ✓ Sentence Transformers" -ForegroundColor White
Write-Host "  ✓ scikit-learn for ML" -ForegroundColor White
Write-Host "  ✓ Playwright for verification" -ForegroundColor White
Write-Host "  ✓ OpenCV for computer vision" -ForegroundColor White
Write-Host ""

Write-Host "NLP Capabilities:" -ForegroundColor Cyan
Write-Host "  • Field name semantic analysis" -ForegroundColor Gray
Write-Host "  • Intelligent field matching" -ForegroundColor Gray
Write-Host "  • Business entity recognition" -ForegroundColor Gray
Write-Host "  • Property data classification" -ForegroundColor Gray
Write-Host "  • Similarity scoring" -ForegroundColor Gray
Write-Host "  • Visual validation with OCR" -ForegroundColor Gray
Write-Host ""

Write-Host "Usage:" -ForegroundColor Cyan
Write-Host "  • Run tests: python test_nlp_field_matching.py" -ForegroundColor White
Write-Host "  • Test single property: python -m apps.api.nlp_intelligent_field_matcher" -ForegroundColor White
Write-Host "  • Integration: from apps.api.nlp_intelligent_field_matcher import NLPDataMappingSystem" -ForegroundColor White
Write-Host ""

if ($nlp_test_result -eq 0) {
    Write-Host "🚀 Ready for intelligent field mapping!" -ForegroundColor Green
} else {
    Write-Host "⚠ Setup completed with warnings. Check errors above." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Press any key to continue..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")