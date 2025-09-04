"""
Advanced Data Pipeline with Agent-Based Processing
Handles massive files efficiently with parallel processing, chunking, and intelligent routing
"""

import asyncio
import aiofiles
import duckdb
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from pathlib import Path
from typing import AsyncIterator, Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import hashlib
import logging
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import multiprocessing as mp
from queue import Queue
import threading
import time
import psutil
import numpy as np

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PipelineStage(Enum):
    """Pipeline stages for data flow"""
    INGESTION = "ingestion"
    VALIDATION = "validation"
    TRANSFORMATION = "transformation"
    ENRICHMENT = "enrichment"
    LOADING = "loading"
    VERIFICATION = "verification"


@dataclass
class DataChunk:
    """Represents a chunk of data flowing through pipeline"""
    id: str
    stage: PipelineStage
    data: Any
    metadata: Dict
    size_bytes: int
    row_count: int
    checksum: str
    timestamp: float


class PipelineMetrics:
    """Track pipeline performance metrics"""
    
    def __init__(self):
        self.chunks_processed = 0
        self.bytes_processed = 0
        self.errors = 0
        self.start_time = time.time()
        self.stage_timings = {}
        
    def record_chunk(self, chunk: DataChunk, duration: float):
        self.chunks_processed += 1
        self.bytes_processed += chunk.size_bytes
        
        if chunk.stage not in self.stage_timings:
            self.stage_timings[chunk.stage] = []
        self.stage_timings[chunk.stage].append(duration)
        
    def get_throughput(self) -> float:
        elapsed = time.time() - self.start_time
        return self.bytes_processed / elapsed if elapsed > 0 else 0
        
    def get_stats(self) -> Dict:
        return {
            'chunks_processed': self.chunks_processed,
            'bytes_processed': self.bytes_processed,
            'throughput_mbps': self.get_throughput() / (1024 * 1024),
            'errors': self.errors,
            'avg_stage_times': {
                stage.value: np.mean(times) if times else 0
                for stage, times in self.stage_timings.items()
            }
        }


class StreamProcessor:
    """Base class for stream processors"""
    
    async def process(self, chunk: DataChunk) -> DataChunk:
        raise NotImplementedError


class ValidationProcessor(StreamProcessor):
    """Validates data quality and structure"""
    
    async def process(self, chunk: DataChunk) -> DataChunk:
        start = time.time()
        
        if isinstance(chunk.data, pd.DataFrame):
            # Check for required columns
            required_cols = ['folio', 'owner_name', 'just_value']
            missing = set(required_cols) - set(chunk.data.columns)
            if missing:
                logger.warning(f"Missing columns: {missing}")
                
            # Remove invalid rows
            original_count = len(chunk.data)
            chunk.data = chunk.data.dropna(subset=['folio'])
            removed = original_count - len(chunk.data)
            
            if removed > 0:
                logger.info(f"Removed {removed} invalid rows")
                
            chunk.metadata['validation_time'] = time.time() - start
            chunk.metadata['rows_validated'] = len(chunk.data)
            
        chunk.stage = PipelineStage.TRANSFORMATION
        return chunk


class TransformationProcessor(StreamProcessor):
    """Transform and clean data"""
    
    async def process(self, chunk: DataChunk) -> DataChunk:
        if isinstance(chunk.data, pd.DataFrame):
            df = chunk.data
            
            # Clean text fields
            text_cols = df.select_dtypes(include=['object']).columns
            for col in text_cols:
                df[col] = df[col].str.strip().str.upper()
                
            # Parse numeric values
            if 'just_value' in df.columns:
                df['just_value'] = pd.to_numeric(
                    df['just_value'].astype(str).str.replace(',', '').str.replace('$', ''),
                    errors='coerce'
                )
                
            # Add processing metadata
            df['processed_at'] = pd.Timestamp.now()
            
            chunk.data = df
            chunk.metadata['transformed'] = True
            
        chunk.stage = PipelineStage.ENRICHMENT
        return chunk


class EnrichmentProcessor(StreamProcessor):
    """Enrich data with additional information"""
    
    def __init__(self, enrichment_source: Optional[Dict] = None):
        self.enrichment_source = enrichment_source or {}
        
    async def process(self, chunk: DataChunk) -> DataChunk:
        if isinstance(chunk.data, pd.DataFrame):
            df = chunk.data
            
            # Add geocoding placeholder
            if 'situs_address_1' in df.columns:
                df['latitude'] = None
                df['longitude'] = None
                # In production, would call geocoding service here
                
            # Add market analysis
            if 'just_value' in df.columns and 'situs_city' in df.columns:
                city_medians = df.groupby('situs_city')['just_value'].median()
                df['market_median'] = df['situs_city'].map(city_medians)
                df['value_vs_median'] = df['just_value'] / df['market_median']
                
            chunk.data = df
            chunk.metadata['enriched'] = True
            
        chunk.stage = PipelineStage.LOADING
        return chunk


class DataPipelineAgent:
    """Agent that manages a specific pipeline stage"""
    
    def __init__(self, name: str, processor: StreamProcessor, max_workers: int = 4):
        self.name = name
        self.processor = processor
        self.input_queue: asyncio.Queue = asyncio.Queue(maxsize=100)
        self.output_queue: Optional[asyncio.Queue] = None
        self.max_workers = max_workers
        self.metrics = PipelineMetrics()
        self.running = False
        
    def connect(self, next_agent: 'DataPipelineAgent'):
        """Connect this agent's output to next agent's input"""
        self.output_queue = next_agent.input_queue
        
    async def start(self):
        """Start processing chunks"""
        self.running = True
        tasks = [
            asyncio.create_task(self._worker(i))
            for i in range(self.max_workers)
        ]
        await asyncio.gather(*tasks)
        
    async def _worker(self, worker_id: int):
        """Worker that processes chunks"""
        while self.running:
            try:
                chunk = await asyncio.wait_for(
                    self.input_queue.get(),
                    timeout=1.0
                )
                
                start = time.time()
                processed_chunk = await self.processor.process(chunk)
                duration = time.time() - start
                
                self.metrics.record_chunk(processed_chunk, duration)
                
                if self.output_queue:
                    await self.output_queue.put(processed_chunk)
                    
                logger.debug(f"{self.name} worker {worker_id} processed chunk {chunk.id}")
                
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Error in {self.name} worker {worker_id}: {e}")
                self.metrics.errors += 1
                
    async def stop(self):
        """Stop processing"""
        self.running = False


class AdvancedDataPipeline:
    """
    Advanced data pipeline with multiple processing stages and agents
    Optimized for large file processing with parallel execution
    """
    
    def __init__(self, num_workers: int = None):
        self.num_workers = num_workers or mp.cpu_count()
        self.agents: List[DataPipelineAgent] = []
        self.metrics = PipelineMetrics()
        self.conn = duckdb.connect(':memory:')
        
        # Configure DuckDB for performance
        self.conn.execute(f"SET threads={self.num_workers}")
        self.conn.execute("SET memory_limit='4GB'")
        
    def build_pipeline(self) -> List[DataPipelineAgent]:
        """Build the processing pipeline with agents"""
        
        # Create processing agents
        validation_agent = DataPipelineAgent(
            "Validator",
            ValidationProcessor(),
            max_workers=2
        )
        
        transform_agent = DataPipelineAgent(
            "Transformer",
            TransformationProcessor(),
            max_workers=4
        )
        
        enrichment_agent = DataPipelineAgent(
            "Enricher",
            EnrichmentProcessor(),
            max_workers=2
        )
        
        # Connect agents in sequence
        validation_agent.connect(transform_agent)
        transform_agent.connect(enrichment_agent)
        
        self.agents = [validation_agent, transform_agent, enrichment_agent]
        return self.agents
        
    async def process_file_stream(
        self,
        file_path: Path,
        chunk_size: int = 50000
    ) -> AsyncIterator[DataChunk]:
        """
        Stream process a large file in chunks
        Optimized for memory efficiency
        """
        
        file_ext = file_path.suffix.lower()
        chunk_id = 0
        
        if file_ext in ['.csv', '.txt']:
            # Use DuckDB for efficient CSV streaming
            query = f"""
                SELECT * FROM read_csv_auto('{file_path}', 
                    sample_size=100000,
                    parallel=true)
            """
            
            # Stream results in chunks
            result = self.conn.execute(query)
            while True:
                df = result.fetch_df_chunk(chunk_size)
                if df is None or df.empty:
                    break
                    
                chunk = DataChunk(
                    id=f"{file_path.name}_{chunk_id}",
                    stage=PipelineStage.VALIDATION,
                    data=df,
                    metadata={'source': str(file_path)},
                    size_bytes=df.memory_usage(deep=True).sum(),
                    row_count=len(df),
                    checksum=hashlib.md5(pd.util.hash_pandas_object(df).values).hexdigest(),
                    timestamp=time.time()
                )
                
                chunk_id += 1
                yield chunk
                
        elif file_ext in ['.xlsx', '.xls']:
            # For Excel, use pandas with chunking
            for df_chunk in pd.read_excel(file_path, chunksize=chunk_size):
                chunk = DataChunk(
                    id=f"{file_path.name}_{chunk_id}",
                    stage=PipelineStage.VALIDATION,
                    data=df_chunk,
                    metadata={'source': str(file_path)},
                    size_bytes=df_chunk.memory_usage(deep=True).sum(),
                    row_count=len(df_chunk),
                    checksum=hashlib.md5(pd.util.hash_pandas_object(df_chunk).values).hexdigest(),
                    timestamp=time.time()
                )
                
                chunk_id += 1
                yield chunk
                
        elif file_ext == '.parquet':
            # Use PyArrow for efficient Parquet reading
            parquet_file = pq.ParquetFile(file_path)
            
            for batch in parquet_file.iter_batches(batch_size=chunk_size):
                df = batch.to_pandas()
                
                chunk = DataChunk(
                    id=f"{file_path.name}_{chunk_id}",
                    stage=PipelineStage.VALIDATION,
                    data=df,
                    metadata={'source': str(file_path)},
                    size_bytes=df.memory_usage(deep=True).sum(),
                    row_count=len(df),
                    checksum=hashlib.md5(pd.util.hash_pandas_object(df).values).hexdigest(),
                    timestamp=time.time()
                )
                
                chunk_id += 1
                yield chunk
                
    async def parallel_process_files(
        self,
        file_paths: List[Path],
        output_format: str = 'parquet'
    ) -> Dict:
        """
        Process multiple files in parallel
        """
        
        # Build and start pipeline
        agents = self.build_pipeline()
        
        # Start all agents
        agent_tasks = [
            asyncio.create_task(agent.start())
            for agent in agents
        ]
        
        # Process files concurrently
        processing_tasks = [
            asyncio.create_task(self._process_single_file(file_path, agents[0]))
            for file_path in file_paths
        ]
        
        # Wait for processing to complete
        await asyncio.gather(*processing_tasks)
        
        # Stop agents
        for agent in agents:
            await agent.stop()
            
        # Collect metrics
        total_metrics = {
            'total_chunks': sum(a.metrics.chunks_processed for a in agents),
            'total_bytes': sum(a.metrics.bytes_processed for a in agents),
            'total_errors': sum(a.metrics.errors for a in agents),
            'agent_stats': {
                a.name: a.metrics.get_stats()
                for a in agents
            }
        }
        
        return total_metrics
        
    async def _process_single_file(
        self,
        file_path: Path,
        first_agent: DataPipelineAgent
    ):
        """Process a single file through the pipeline"""
        
        async for chunk in self.process_file_stream(file_path):
            await first_agent.input_queue.put(chunk)
            
            # Backpressure control
            while first_agent.input_queue.qsize() > 50:
                await asyncio.sleep(0.1)


class SmartBufferManager:
    """
    Intelligent buffer management for optimal memory usage
    Adapts buffer size based on available memory and throughput
    """
    
    def __init__(self, target_memory_percent: float = 0.5):
        self.target_memory_percent = target_memory_percent
        self.min_buffer_size = 1000
        self.max_buffer_size = 100000
        self.current_buffer_size = 10000
        self.throughput_history = []
        
    def get_optimal_buffer_size(self) -> int:
        """Calculate optimal buffer size based on system resources"""
        
        # Get available memory
        memory = psutil.virtual_memory()
        available_mb = memory.available / (1024 * 1024)
        
        # Calculate target buffer size
        target_memory_mb = available_mb * self.target_memory_percent
        
        # Estimate row size (assume 1KB per row average)
        row_size_kb = 1
        optimal_size = int(target_memory_mb * 1024 / row_size_kb)
        
        # Apply bounds
        optimal_size = max(self.min_buffer_size, min(optimal_size, self.max_buffer_size))
        
        # Adjust based on throughput history
        if len(self.throughput_history) > 5:
            avg_throughput = np.mean(self.throughput_history[-5:])
            if avg_throughput < 1000:  # Low throughput, reduce buffer
                optimal_size = int(optimal_size * 0.8)
            elif avg_throughput > 10000:  # High throughput, increase buffer
                optimal_size = int(optimal_size * 1.2)
                
        self.current_buffer_size = optimal_size
        return optimal_size
        
    def record_throughput(self, rows_per_second: float):
        """Record throughput for adaptive optimization"""
        self.throughput_history.append(rows_per_second)
        if len(self.throughput_history) > 100:
            self.throughput_history = self.throughput_history[-100:]


async def main():
    """Example usage of the advanced pipeline"""
    
    # Create pipeline
    pipeline = AdvancedDataPipeline(num_workers=4)
    
    # Example files to process
    data_dir = Path("C:/Users/gsima/Documents/MyProject/ConcordBroker/data/dor")
    files = list(data_dir.glob("*.csv")) + list(data_dir.glob("*.xlsx"))
    
    if files:
        logger.info(f"Processing {len(files)} files with advanced pipeline")
        
        # Process files
        metrics = await pipeline.parallel_process_files(files)
        
        # Display results
        logger.info("\n" + "="*60)
        logger.info("PIPELINE PROCESSING COMPLETE")
        logger.info("="*60)
        logger.info(f"Total chunks processed: {metrics['total_chunks']}")
        logger.info(f"Total data processed: {metrics['total_bytes'] / (1024**3):.2f} GB")
        logger.info(f"Total errors: {metrics['total_errors']}")
        
        for agent_name, stats in metrics['agent_stats'].items():
            logger.info(f"\n{agent_name} Agent:")
            logger.info(f"  Throughput: {stats['throughput_mbps']:.2f} MB/s")
            logger.info(f"  Chunks: {stats['chunks_processed']}")
            
    else:
        logger.info("No files found to process")
        logger.info("Place CSV, Excel, or Parquet files in: " + str(data_dir))


if __name__ == "__main__":
    asyncio.run(main())