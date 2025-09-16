/**
 * Test Redis Cloud connection and Supabase integration
 * This script tests the Redis caching layer with Supabase database
 */

const path = require('path');
require('dotenv').config({ path: path.join(__dirname, '.env.mcp') });
const { getCacheService } = require('./mcp-server/services/redis-cache');
const { createClient } = require('@supabase/supabase-js');

// Initialize Supabase client
const supabase = createClient(
  process.env.SUPABASE_URL,
  process.env.SUPABASE_ANON_KEY
);

async function testRedisConnection() {
  console.log('🔄 Testing Redis Cloud connection...\n');

  console.log('Redis Configuration:');
  console.log('  Host:', process.env.REDIS_CLOUD_HOST);
  console.log('  Port:', process.env.REDIS_CLOUD_PORT);
  console.log('  Password:', process.env.REDIS_CLOUD_PASSWORD ? '✓ Set' : '✗ Not set');
  console.log();

  try {
    // Get cache service
    const cache = await getCacheService();

    // Test basic operations
    console.log('📝 Testing basic cache operations...');

    // Set a test value
    await cache.set('test:key', { message: 'Hello from Redis!' }, 60);
    console.log('✅ Set test value in cache');

    // Get the test value
    const value = await cache.get('test:key');
    console.log('✅ Retrieved value:', value);

    // Get cache stats
    const stats = cache.getStats();
    console.log('\n📊 Cache Statistics:');
    console.log('  Type:', stats.cacheType);
    console.log('  Connected:', stats.redisConnected);
    console.log('  Hit Rate:', stats.hitRate);
    console.log('  Memory Size:', stats.memorySize);

    return cache;
  } catch (error) {
    console.error('❌ Redis connection failed:', error.message);
    return null;
  }
}

async function testSupabaseWithCache(cache) {
  console.log('\n🔄 Testing Supabase integration with Redis cache...\n');

  try {
    // Test fetching property data with caching
    console.log('📝 Fetching property data from Supabase...');

    // Generate cache key
    const cacheKey = cache.generateKey('property', {
      table: 'florida_parcels',
      limit: 5
    });

    // Check if data exists in cache
    let properties = await cache.get(cacheKey);

    if (properties) {
      console.log('✅ Data retrieved from cache (fast!)');
    } else {
      console.log('⏳ Cache miss, fetching from database...');

      // Fetch from Supabase
      const { data, error } = await supabase
        .from('florida_parcels')
        .select('parcel_id, phy_addr1, phy_city, county, just_value')
        .limit(5);

      if (error) {
        console.error('❌ Supabase error:', error.message);
        return;
      }

      properties = data;
      console.log('✅ Data fetched from Supabase');

      // Store in cache for 5 minutes
      await cache.set(cacheKey, properties, 300);
      console.log('✅ Data cached for future requests');
    }

    console.log(`\n📊 Found ${properties.length} properties:`);
    properties.forEach(p => {
      console.log(`  - ${p.parcel_id}: ${p.phy_addr1}, ${p.phy_city}`);
    });

  } catch (error) {
    console.error('❌ Integration test failed:', error.message);
  }
}

async function testCachingStrategy(cache) {
  console.log('\n🔄 Testing intelligent caching strategy...\n');

  const testCases = [
    {
      key: 'tax_deed:upcoming',
      data: { count: 15, next_auction: '2025-01-20' },
      ttl: 300  // 5 minutes
    },
    {
      key: 'property:search:broward',
      data: { results: 250, cached_at: new Date().toISOString() },
      ttl: 900  // 15 minutes
    },
    {
      key: 'market:analysis:2025',
      data: { avg_price: 450000, growth: 5.2 },
      ttl: 3600  // 1 hour
    }
  ];

  console.log('📝 Setting multiple cache entries with different TTLs...');

  for (const test of testCases) {
    await cache.set(test.key, test.data, test.ttl);
    console.log(`  ✅ ${test.key} (TTL: ${test.ttl}s)`);
  }

  console.log('\n📊 Testing retrieval:');

  for (const test of testCases) {
    const value = await cache.get(test.key);
    console.log(`  ✅ ${test.key}:`, value);
  }

  // Test cache key generation
  console.log('\n🔑 Testing cache key generation:');
  const key1 = cache.generateKey('property', { county: 'BROWARD', type: 'residential' });
  const key2 = cache.generateKey('property', { type: 'residential', county: 'BROWARD' });
  console.log('  Key 1:', key1);
  console.log('  Key 2:', key2);
  console.log('  Keys match:', key1 === key2 ? '✅ Yes (correct!)' : '❌ No');
}

async function main() {
  console.log('═══════════════════════════════════════════════');
  console.log('  Redis Cloud & Supabase Integration Test');
  console.log('═══════════════════════════════════════════════\n');

  // Test Redis connection
  const cache = await testRedisConnection();

  if (cache) {
    // Test Supabase integration
    await testSupabaseWithCache(cache);

    // Test caching strategy
    await testCachingStrategy(cache);

    // Final stats
    console.log('\n═══════════════════════════════════════════════');
    console.log('  Final Cache Statistics');
    console.log('═══════════════════════════════════════════════');
    const finalStats = cache.getStats();
    console.log('  Type:', finalStats.cacheType);
    console.log('  Hit Rate:', finalStats.hitRate);
    console.log('  Total Hits:', finalStats.hits);
    console.log('  Total Misses:', finalStats.misses);
    console.log('  Errors:', finalStats.errors);

    if (finalStats.redisConnected) {
      console.log('\n✅ Redis Cloud is connected and working with Supabase!');
    } else {
      console.log('\n⚠️ Using in-memory cache (Redis not available)');
    }
  } else {
    console.log('\n❌ Could not establish cache service');
  }

  console.log('\n═══════════════════════════════════════════════\n');

  // Keep process alive for a moment to see any async errors
  setTimeout(() => {
    process.exit(0);
  }, 1000);
}

// Run the test
main().catch(console.error);