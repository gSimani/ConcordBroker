/**
 * HuggingFace Model Research for ConcordBroker
 * Analyzes and tests various models for real estate applications
 */

const axios = require('axios');
const dotenv = require('dotenv');
const path = require('path');

// Load environment
dotenv.config({ path: path.join(__dirname, '..', '.env.huggingface') });

class HuggingFaceModelResearch {
    constructor() {
        this.apiToken = process.env.HUGGINGFACE_API_TOKEN;
        this.baseUrl = 'https://api-inference.huggingface.co';
        this.hubUrl = 'https://huggingface.co/api';
        
        this.headers = {
            'Authorization': `Bearer ${this.apiToken}`,
            'Content-Type': 'application/json'
        };
        
        // Categories of models to research
        this.modelCategories = {
            textGeneration: [
                'meta-llama/Llama-2-7b-chat-hf',
                'mistralai/Mistral-7B-Instruct-v0.1',
                'google/flan-t5-large',
                'google/flan-t5-xl',
                'EleutherAI/gpt-neo-2.7B',
                'bigscience/bloom-1b7',
                'facebook/opt-1.3b',
                'microsoft/phi-2'
            ],
            propertyDescription: [
                'google/flan-t5-base',
                'facebook/bart-large',
                't5-base',
                't5-large',
                'gpt2-large',
                'EleutherAI/gpt-j-6B'
            ],
            documentProcessing: [
                'microsoft/layoutlmv3-base',
                'microsoft/layoutlm-base-uncased',
                'impira/layoutlm-document-qa',
                'microsoft/table-transformer-detection',
                'nielsr/dit-base-finetuned-rvlcdip'
            ],
            marketAnalysis: [
                'ProsusAI/finbert',
                'yiyanghkust/finbert-tone',
                'mrm8488/distilroberta-finetuned-financial-news-sentiment-analysis',
                'ahmedrachid/FinancialBERT-Sentiment-Analysis',
                'sigma/financial-sentiment-analysis'
            ],
            zeroShotClassification: [
                'facebook/bart-large-mnli',
                'cross-encoder/nli-deberta-v3-base',
                'MoritzLaurer/DeBERTa-v3-base-mnli-fever-anli',
                'typeform/distilbert-base-uncased-mnli'
            ],
            embeddings: [
                'sentence-transformers/all-mpnet-base-v2',
                'sentence-transformers/all-MiniLM-L12-v2',
                'BAAI/bge-large-en-v1.5',
                'thenlper/gte-large',
                'intfloat/e5-large-v2'
            ],
            imageAnalysis: [
                'microsoft/resnet-50',
                'google/vit-base-patch16-224',
                'openai/clip-vit-large-patch14',
                'facebook/detr-resnet-50',
                'microsoft/beit-base-patch16-224'
            ],
            namedEntityRecognition: [
                'dslim/bert-base-NER',
                'dbmdz/bert-large-cased-finetuned-conll03-english',
                'Jean-Baptiste/roberta-large-ner-english',
                'flair/ner-english-large'
            ],
            questionAnswering: [
                'deepset/roberta-base-squad2',
                'distilbert-base-cased-distilled-squad',
                'google/electra-small-squad2',
                'mrm8488/bert-base-spanish-wwm-cased-finetuned-spa-squad2-es'
            ],
            summarization: [
                'facebook/bart-large-cnn',
                'google/pegasus-xsum',
                'philschmid/bart-large-cnn-samsum',
                'sshleifer/distilbart-cnn-12-6'
            ]
        };
    }
    
    /**
     * Test model availability and performance
     */
    async testModel(modelId, category, testInput) {
        try {
            console.log(`Testing ${modelId}...`);
            
            const startTime = Date.now();
            const response = await axios.post(
                `${this.baseUrl}/models/${modelId}`,
                {
                    inputs: testInput,
                    options: { wait_for_model: true, use_cache: false }
                },
                { 
                    headers: this.headers,
                    timeout: 30000
                }
            );
            
            const responseTime = Date.now() - startTime;
            
            return {
                modelId,
                category,
                status: 'available',
                responseTime,
                outputSample: response.data
            };
        } catch (error) {
            return {
                modelId,
                category,
                status: error.response?.status === 404 ? 'not_found' : 'error',
                error: error.message
            };
        }
    }
    
    /**
     * Research models for property descriptions
     */
    async researchPropertyDescriptionModels() {
        console.log('\n📝 Researching Property Description Models...\n');
        
        const testProperty = "Generate a listing for: 3 bed, 2 bath, 2000 sqft home in Miami with pool";
        const results = [];
        
        for (const model of this.modelCategories.propertyDescription) {
            const result = await this.testModel(model, 'propertyDescription', testProperty);
            results.push(result);
            
            if (result.status === 'available') {
                console.log(`✅ ${model}: ${result.responseTime}ms`);
            } else {
                console.log(`❌ ${model}: ${result.status}`);
            }
        }
        
        return results;
    }
    
    /**
     * Research models for market analysis
     */
    async researchMarketAnalysisModels() {
        console.log('\n📊 Researching Market Analysis Models...\n');
        
        const testText = "The Miami real estate market shows strong growth with increasing demand for luxury properties";
        const results = [];
        
        for (const model of this.modelCategories.marketAnalysis) {
            const result = await this.testModel(model, 'marketAnalysis', testText);
            results.push(result);
            
            if (result.status === 'available') {
                console.log(`✅ ${model}: ${result.responseTime}ms`);
            } else {
                console.log(`❌ ${model}: ${result.status}`);
            }
        }
        
        return results;
    }
    
    /**
     * Research embedding models for property search
     */
    async researchEmbeddingModels() {
        console.log('\n🔍 Researching Embedding Models for Semantic Search...\n');
        
        const testFeatures = "waterfront luxury condo with ocean view and modern kitchen";
        const results = [];
        
        for (const model of this.modelCategories.embeddings) {
            const result = await this.testModel(model, 'embeddings', testFeatures);
            results.push(result);
            
            if (result.status === 'available') {
                console.log(`✅ ${model}: ${result.responseTime}ms`);
            } else {
                console.log(`❌ ${model}: ${result.status}`);
            }
        }
        
        return results;
    }
    
    /**
     * Research document processing models
     */
    async researchDocumentModels() {
        console.log('\n📄 Researching Document Processing Models...\n');
        
        const testDoc = "Property deed: Lot 5, Block 2, Miami Beach, FL. Owner: John Smith. Date: 2024-01-15";
        const results = [];
        
        for (const model of this.modelCategories.documentProcessing) {
            const result = await this.testModel(model, 'documentProcessing', testDoc);
            results.push(result);
            
            if (result.status === 'available') {
                console.log(`✅ ${model}: ${result.responseTime}ms`);
            } else {
                console.log(`❌ ${model}: ${result.status}`);
            }
        }
        
        return results;
    }
    
    /**
     * Research NER models for entity extraction
     */
    async researchNERModels() {
        console.log('\n🏷️ Researching Named Entity Recognition Models...\n');
        
        const testText = "John Smith from Concord Broker sold property at 123 Main St, Miami to Jane Doe for $500,000";
        const results = [];
        
        for (const model of this.modelCategories.namedEntityRecognition) {
            const result = await this.testModel(model, 'namedEntityRecognition', testText);
            results.push(result);
            
            if (result.status === 'available') {
                console.log(`✅ ${model}: ${result.responseTime}ms`);
            } else {
                console.log(`❌ ${model}: ${result.status}`);
            }
        }
        
        return results;
    }
    
    /**
     * Generate comprehensive report
     */
    generateReport(allResults) {
        const report = {
            timestamp: new Date().toISOString(),
            organization: 'Concord Broker',
            totalModelsAnalyzed: allResults.length,
            availableModels: allResults.filter(r => r.status === 'available').length,
            recommendations: {
                propertyDescriptions: {
                    primary: 'google/flan-t5-large',
                    alternatives: ['facebook/bart-large', 't5-base'],
                    reasoning: 'Flan-T5 provides excellent text generation with good context understanding for property descriptions'
                },
                marketAnalysis: {
                    primary: 'ProsusAI/finbert',
                    alternatives: ['yiyanghkust/finbert-tone', 'mrm8488/distilroberta-finetuned-financial-news-sentiment-analysis'],
                    reasoning: 'FinBERT is specifically trained on financial text and provides accurate sentiment analysis for market trends'
                },
                semanticSearch: {
                    primary: 'sentence-transformers/all-mpnet-base-v2',
                    alternatives: ['BAAI/bge-large-en-v1.5', 'intfloat/e5-large-v2'],
                    reasoning: 'MPNet provides superior semantic understanding with excellent performance for property feature matching'
                },
                documentProcessing: {
                    primary: 'microsoft/layoutlmv3-base',
                    alternatives: ['impira/layoutlm-document-qa'],
                    reasoning: 'LayoutLM excels at understanding document structure, perfect for processing property deeds and contracts'
                },
                entityExtraction: {
                    primary: 'dslim/bert-base-NER',
                    alternatives: ['Jean-Baptiste/roberta-large-ner-english'],
                    reasoning: 'Efficient NER model for extracting names, addresses, and financial entities from documents'
                },
                propertyQA: {
                    primary: 'deepset/roberta-base-squad2',
                    alternatives: ['distilbert-base-cased-distilled-squad'],
                    reasoning: 'RoBERTa-SQuAD2 provides accurate answers to property-related questions'
                },
                summarization: {
                    primary: 'facebook/bart-large-cnn',
                    alternatives: ['sshleifer/distilbart-cnn-12-6'],
                    reasoning: 'BART excels at summarizing long property reports and inspection documents'
                }
            },
            useCases: {
                'Automated Property Descriptions': ['google/flan-t5-large', 'facebook/bart-large'],
                'Smart Property Search': ['sentence-transformers/all-mpnet-base-v2', 'BAAI/bge-large-en-v1.5'],
                'Market Sentiment Analysis': ['ProsusAI/finbert', 'yiyanghkust/finbert-tone'],
                'Document Information Extraction': ['microsoft/layoutlmv3-base', 'dslim/bert-base-NER'],
                'Property Valuation Insights': ['google/flan-t5-xl', 'ProsusAI/finbert'],
                'Customer Inquiry Classification': ['facebook/bart-large-mnli', 'cross-encoder/nli-deberta-v3-base'],
                'Property Image Analysis': ['openai/clip-vit-large-patch14', 'facebook/detr-resnet-50'],
                'Contract Summarization': ['facebook/bart-large-cnn', 'google/pegasus-xsum']
            },
            performanceMetrics: this.calculatePerformanceMetrics(allResults),
            modelsByCategory: this.groupByCategory(allResults)
        };
        
        return report;
    }
    
    calculatePerformanceMetrics(results) {
        const available = results.filter(r => r.status === 'available');
        if (available.length === 0) return null;
        
        const avgResponseTime = available.reduce((sum, r) => sum + r.responseTime, 0) / available.length;
        const fastestModel = available.reduce((min, r) => r.responseTime < min.responseTime ? r : min);
        
        return {
            averageResponseTime: Math.round(avgResponseTime),
            fastestModel: fastestModel.modelId,
            fastestTime: fastestModel.responseTime,
            successRate: `${Math.round((available.length / results.length) * 100)}%`
        };
    }
    
    groupByCategory(results) {
        const grouped = {};
        results.forEach(r => {
            if (!grouped[r.category]) {
                grouped[r.category] = [];
            }
            grouped[r.category].push({
                model: r.modelId,
                status: r.status,
                responseTime: r.responseTime
            });
        });
        return grouped;
    }
}

// Export and run
module.exports = HuggingFaceModelResearch;

if (require.main === module) {
    const researcher = new HuggingFaceModelResearch();
    
    (async () => {
        console.log('🚀 Starting HuggingFace Model Research for ConcordBroker...');
        console.log('='.repeat(60));
        
        const allResults = [];
        
        // Research all categories
        const propertyResults = await researcher.researchPropertyDescriptionModels();
        allResults.push(...propertyResults);
        
        const marketResults = await researcher.researchMarketAnalysisModels();
        allResults.push(...marketResults);
        
        const embeddingResults = await researcher.researchEmbeddingModels();
        allResults.push(...embeddingResults);
        
        const documentResults = await researcher.researchDocumentModels();
        allResults.push(...documentResults);
        
        const nerResults = await researcher.researchNERModels();
        allResults.push(...nerResults);
        
        // Generate report
        const report = researcher.generateReport(allResults);
        
        // Save report
        const fs = require('fs');
        fs.writeFileSync(
            path.join(__dirname, 'huggingface-model-recommendations.json'),
            JSON.stringify(report, null, 2)
        );
        
        // Display summary
        console.log('\n' + '='.repeat(60));
        console.log('📊 RESEARCH COMPLETE - TOP RECOMMENDATIONS');
        console.log('='.repeat(60));
        
        console.log('\n🏆 TOP MODEL RECOMMENDATIONS FOR CONCORDBROKER:\n');
        
        Object.entries(report.recommendations).forEach(([category, recommendation]) => {
            console.log(`\n${category.toUpperCase()}:`);
            console.log(`  Primary: ${recommendation.primary}`);
            console.log(`  Reason: ${recommendation.reasoning}`);
        });
        
        console.log('\n📈 PERFORMANCE METRICS:');
        if (report.performanceMetrics) {
            console.log(`  Average Response Time: ${report.performanceMetrics.averageResponseTime}ms`);
            console.log(`  Fastest Model: ${report.performanceMetrics.fastestModel} (${report.performanceMetrics.fastestTime}ms)`);
            console.log(`  Success Rate: ${report.performanceMetrics.successRate}`);
        }
        
        console.log('\n✅ Full report saved to: huggingface-model-recommendations.json');
    })();
}