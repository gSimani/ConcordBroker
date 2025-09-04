/**
 * Advanced Stream Pipeline for Large File Processing
 * Optimized for Florida DOR data with agent-based architecture
 */

const fs = require('fs');
const { pipeline, Transform, PassThrough, Writable } = require('stream');
const { promisify } = require('util');
const zlib = require('zlib');
const crypto = require('crypto');
const EventEmitter = require('events');
const cluster = require('cluster');
const os = require('os');

// For Excel processing
const XLSX = require('xlsx');
const csv = require('csv-parser');
const { Pool } = require('pg');

/**
 * Pipeline Agent - Manages a stage of data processing
 */
class PipelineAgent extends EventEmitter {
    constructor(name, processor, options = {}) {
        super();
        this.name = name;
        this.processor = processor;
        this.concurrency = options.concurrency || 4;
        this.bufferSize = options.bufferSize || 100;
        this.metrics = {
            processed: 0,
            errors: 0,
            bytesProcessed: 0,
            startTime: Date.now()
        };
        this.queue = [];
        this.processing = 0;
    }

    async process(chunk) {
        if (this.processing >= this.concurrency) {
            await new Promise(resolve => {
                this.queue.push({ chunk, resolve });
            });
        }

        this.processing++;
        try {
            const start = Date.now();
            const result = await this.processor(chunk);
            
            this.metrics.processed++;
            this.metrics.bytesProcessed += chunk.length;
            
            this.emit('processed', {
                agent: this.name,
                duration: Date.now() - start,
                size: chunk.length
            });

            return result;
        } catch (error) {
            this.metrics.errors++;
            this.emit('error', error);
            throw error;
        } finally {
            this.processing--;
            if (this.queue.length > 0) {
                const { resolve } = this.queue.shift();
                resolve();
            }
        }
    }

    getMetrics() {
        const elapsed = (Date.now() - this.metrics.startTime) / 1000;
        return {
            ...this.metrics,
            throughput: this.metrics.bytesProcessed / elapsed,
            avgProcessingTime: elapsed / this.metrics.processed
        };
    }
}

/**
 * Transform stream with backpressure handling
 */
class SmartTransform extends Transform {
    constructor(agent, options = {}) {
        super({
            ...options,
            objectMode: true,
            highWaterMark: options.highWaterMark || 16
        });
        this.agent = agent;
        this.pendingCallbacks = [];
    }

    async _transform(chunk, encoding, callback) {
        try {
            // Apply backpressure if too many pending
            if (this.pendingCallbacks.length > this.agent.concurrency * 2) {
                await new Promise(resolve => setTimeout(resolve, 10));
            }

            const processed = await this.agent.process(chunk);
            callback(null, processed);
        } catch (error) {
            callback(error);
        }
    }

    _flush(callback) {
        // Wait for all pending operations
        Promise.all(this.pendingCallbacks).then(() => callback());
    }
}

/**
 * Advanced Pipeline Manager
 */
class AdvancedPipeline {
    constructor(options = {}) {
        this.agents = [];
        this.streams = [];
        this.options = {
            chunkSize: options.chunkSize || 64 * 1024, // 64KB chunks
            parallelism: options.parallelism || os.cpus().length,
            compression: options.compression || false,
            ...options
        };
        this.metrics = new Map();
    }

    /**
     * Add processing agent to pipeline
     */
    addAgent(name, processor, options) {
        const agent = new PipelineAgent(name, processor, options);
        this.agents.push(agent);
        
        agent.on('processed', (data) => {
            if (!this.metrics.has(name)) {
                this.metrics.set(name, []);
            }
            this.metrics.get(name).push(data);
        });

        return this;
    }

    /**
     * Build the stream pipeline
     */
    build() {
        const streams = [];

        // Add agents as transform streams
        for (const agent of this.agents) {
            streams.push(new SmartTransform(agent, {
                highWaterMark: this.options.chunkSize
            }));
        }

        // Add compression if enabled
        if (this.options.compression) {
            streams.push(zlib.createGzip());
        }

        this.streams = streams;
        return streams;
    }

    /**
     * Process file through pipeline
     */
    async processFile(inputPath, outputPath) {
        return new Promise((resolve, reject) => {
            const startTime = Date.now();
            let totalBytes = 0;

            // Create read stream with optimized settings
            const readStream = fs.createReadStream(inputPath, {
                highWaterMark: this.options.chunkSize,
                encoding: null
            });

            // Create write stream
            const writeStream = fs.createWriteStream(outputPath, {
                highWaterMark: this.options.chunkSize
            });

            // Track progress
            readStream.on('data', (chunk) => {
                totalBytes += chunk.length;
            });

            // Build pipeline
            const streams = [readStream, ...this.build(), writeStream];

            // Execute pipeline
            pipeline(...streams, (error) => {
                if (error) {
                    reject(error);
                } else {
                    const duration = (Date.now() - startTime) / 1000;
                    resolve({
                        duration,
                        bytesProcessed: totalBytes,
                        throughput: totalBytes / duration,
                        agentMetrics: this.agents.map(a => ({
                            name: a.name,
                            ...a.getMetrics()
                        }))
                    });
                }
            });
        });
    }

    /**
     * Process Excel file with streaming
     */
    async processExcel(inputPath, processor) {
        return new Promise((resolve, reject) => {
            const workbook = XLSX.readFile(inputPath, { 
                type: 'buffer',
                cellDates: true,
                cellNF: false,
                cellText: false
            });

            const results = [];
            
            for (const sheetName of workbook.SheetNames) {
                const worksheet = workbook.Sheets[sheetName];
                
                // Convert to stream-friendly format
                const stream = XLSX.stream.to_json(worksheet, {
                    raw: false,
                    defval: null
                });

                // Process each row
                for (const row of stream) {
                    const processed = processor(row);
                    results.push(processed);
                    
                    // Yield control periodically
                    if (results.length % 1000 === 0) {
                        await new Promise(resolve => setImmediate(resolve));
                    }
                }
            }

            resolve(results);
        });
    }

    /**
     * Parallel file processing using worker threads
     */
    async processParallel(files) {
        if (cluster.isMaster) {
            const numWorkers = Math.min(files.length, this.options.parallelism);
            const results = [];
            const fileQueue = [...files];

            // Create workers
            for (let i = 0; i < numWorkers; i++) {
                const worker = cluster.fork();
                
                worker.on('message', (msg) => {
                    if (msg.type === 'result') {
                        results.push(msg.data);
                        
                        // Assign next file
                        if (fileQueue.length > 0) {
                            const nextFile = fileQueue.shift();
                            worker.send({ type: 'process', file: nextFile });
                        } else {
                            worker.kill();
                        }
                    }
                });

                // Start processing
                if (fileQueue.length > 0) {
                    const file = fileQueue.shift();
                    worker.send({ type: 'process', file });
                }
            }

            // Wait for completion
            await new Promise(resolve => {
                cluster.on('exit', () => {
                    if (Object.keys(cluster.workers).length === 0) {
                        resolve();
                    }
                });
            });

            return results;

        } else {
            // Worker process
            process.on('message', async (msg) => {
                if (msg.type === 'process') {
                    const result = await this.processFile(msg.file, msg.file + '.processed');
                    process.send({ type: 'result', data: result });
                }
            });
        }
    }
}

/**
 * DOR Data Processor Pipeline
 */
class DORDataPipeline extends AdvancedPipeline {
    constructor(dbConfig) {
        super({
            chunkSize: 128 * 1024, // 128KB chunks for DOR data
            compression: true
        });
        
        this.dbPool = new Pool(dbConfig);
        this.setupAgents();
    }

    setupAgents() {
        // Validation agent
        this.addAgent('validation', async (chunk) => {
            const data = JSON.parse(chunk.toString());
            
            // Validate required fields
            if (!data.folio || !data.owner_name) {
                throw new Error('Missing required fields');
            }
            
            // Clean data
            data.folio = data.folio.trim().toUpperCase();
            data.owner_name = data.owner_name.trim().toUpperCase();
            
            return Buffer.from(JSON.stringify(data));
        }, { concurrency: 2 });

        // Transformation agent
        this.addAgent('transformation', async (chunk) => {
            const data = JSON.parse(chunk.toString());
            
            // Parse numeric values
            if (data.just_value) {
                data.just_value = parseFloat(
                    data.just_value.toString()
                        .replace(/,/g, '')
                        .replace(/\$/g, '')
                );
            }
            
            // Add metadata
            data.processed_at = new Date().toISOString();
            data.processor_version = '2.0';
            
            return Buffer.from(JSON.stringify(data));
        }, { concurrency: 4 });

        // Database loading agent
        this.addAgent('database', async (chunk) => {
            const data = JSON.parse(chunk.toString());
            
            // Insert to database
            const query = `
                INSERT INTO dor_properties 
                (folio, owner_name, just_value, processed_at)
                VALUES ($1, $2, $3, $4)
                ON CONFLICT (folio) DO UPDATE
                SET owner_name = EXCLUDED.owner_name,
                    just_value = EXCLUDED.just_value,
                    processed_at = EXCLUDED.processed_at
            `;
            
            await this.dbPool.query(query, [
                data.folio,
                data.owner_name,
                data.just_value,
                data.processed_at
            ]);
            
            return chunk;
        }, { concurrency: 8 });
    }

    async processDORFile(inputPath) {
        const ext = inputPath.split('.').pop().toLowerCase();
        
        if (ext === 'xlsx' || ext === 'xls') {
            // Process Excel file
            return await this.processExcel(inputPath, (row) => {
                // Map Excel columns to our schema
                return {
                    folio: row['FOLIO'] || row['ParcelID'],
                    owner_name: row['OWNER NAME'] || row['Owner'],
                    just_value: row['JUST VALUE'] || row['Market Value'],
                    // ... map other fields
                };
            });
        } else {
            // Process CSV or other formats
            return await this.processFile(inputPath, inputPath + '.processed');
        }
    }

    async close() {
        await this.dbPool.end();
    }
}

/**
 * Usage Example
 */
async function main() {
    // Database configuration
    const dbConfig = {
        host: process.env.DB_HOST,
        port: process.env.DB_PORT,
        database: process.env.DB_NAME,
        user: process.env.DB_USER,
        password: process.env.DB_PASSWORD,
        ssl: { rejectUnauthorized: false }
    };

    // Create pipeline
    const pipeline = new DORDataPipeline(dbConfig);

    try {
        // Process single file
        console.log('Processing DOR data file...');
        const result = await pipeline.processDORFile('./data/broward_2025.xlsx');
        
        console.log('Processing complete:');
        console.log(`- Duration: ${result.duration}s`);
        console.log(`- Throughput: ${(result.throughput / 1024 / 1024).toFixed(2)} MB/s`);
        console.log(`- Agent metrics:`, result.agentMetrics);

        // Process multiple files in parallel
        const files = [
            './data/broward_2025.xlsx',
            './data/miami_dade_2025.xlsx',
            './data/palm_beach_2025.xlsx'
        ];
        
        console.log('\nProcessing multiple files in parallel...');
        const parallelResults = await pipeline.processParallel(files);
        console.log('Parallel processing complete:', parallelResults);

    } catch (error) {
        console.error('Pipeline error:', error);
    } finally {
        await pipeline.close();
    }
}

// Export for use in other modules
module.exports = {
    AdvancedPipeline,
    DORDataPipeline,
    PipelineAgent,
    SmartTransform
};

// Run if executed directly
if (require.main === module) {
    main().catch(console.error);
}