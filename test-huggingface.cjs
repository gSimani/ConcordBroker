/**
 * Test HuggingFace API Integration
 */

const axios = require('axios');

async function testHuggingFace() {
  console.log('🧪 Testing HuggingFace Integration...\n');

  try {
    // Test 1: Check health endpoint
    console.log('1️⃣ Checking MCP Server health...');
    const healthResponse = await axios.get('http://localhost:3001/health');
    const hfStatus = healthResponse.data.services.huggingface.status;
    console.log(`   ✅ HuggingFace status: ${hfStatus}\n`);

    if (hfStatus !== 'configured') {
      console.log('   ⚠️  HuggingFace is not configured properly');
      return;
    }

    // Test 2: Test sentiment analysis with a stable model
    console.log('2️⃣ Testing sentiment analysis...');
    const inferenceResponse = await axios.post(
      'http://localhost:3001/api/huggingface/inference',
      {
        model: 'distilbert-base-uncased-finetuned-sst-2-english',
        inputs: 'ConcordBroker is an excellent real estate platform for investors'
      },
      {
        headers: {
          'Content-Type': 'application/json',
          'x-api-key': 'concordbroker-mcp-key'
        }
      }
    );

    console.log('   ✅ Inference successful!');
    console.log('   📝 Response:', JSON.stringify(inferenceResponse.data, null, 2).substring(0, 200) + '...\n');

    console.log('✨ All HuggingFace tests passed!');
  } catch (error) {
    console.error('❌ Test failed:', error.message);
    if (error.response) {
      console.error('   Response:', error.response.data);
    }
  }
}

testHuggingFace();
