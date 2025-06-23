#!/usr/bin/env python3
"""
Utility module for chunked data generation to handle large datasets efficiently.

This module provides:
- Memory-efficient batch generation
- Progress tracking with ETA
- Resume capability for interrupted generations
- Configurable chunk sizes
"""

import os
import json
import time
from datetime import datetime, timedelta
from typing import Generator, List, Dict, Any, Callable

class ChunkedGenerator:
    """Manages chunked generation of large datasets with progress tracking"""
    
    def __init__(self, 
                 generator_name: str,
                 total_records: int,
                 chunk_size: int = 10000,
                 progress_file: str = None):
        """
        Initialize chunked generator
        
        Args:
            generator_name: Name of the generator (for progress tracking)
            total_records: Total number of records to generate
            chunk_size: Number of records per chunk
            progress_file: Path to progress file (optional)
        """
        self.generator_name = generator_name
        self.total_records = total_records
        self.chunk_size = chunk_size
        self.progress_file = progress_file or f".{generator_name}_progress.json"
        
        self.start_time = None
        self.records_generated = 0
        self.chunks_completed = 0
        self.total_chunks = (total_records + chunk_size - 1) // chunk_size
        
    def load_progress(self) -> int:
        """Load progress from file if it exists"""
        if os.path.exists(self.progress_file):
            try:
                with open(self.progress_file, 'r') as f:
                    data = json.load(f)
                    self.records_generated = data.get('records_generated', 0)
                    self.chunks_completed = data.get('chunks_completed', 0)
                    print(f"📥 Resuming from chunk {self.chunks_completed + 1}/{self.total_chunks}")
                    print(f"   {self.records_generated:,} records already generated")
                    return self.records_generated
            except:
                pass
        return 0
    
    def save_progress(self):
        """Save current progress to file"""
        progress_data = {
            'generator_name': self.generator_name,
            'timestamp': datetime.now().isoformat(),
            'records_generated': self.records_generated,
            'chunks_completed': self.chunks_completed,
            'total_records': self.total_records,
            'total_chunks': self.total_chunks
        }
        
        with open(self.progress_file, 'w') as f:
            json.dump(progress_data, f, indent=2)
    
    def print_progress(self):
        """Print current progress with ETA"""
        if not self.start_time:
            return
            
        elapsed = time.time() - self.start_time
        if elapsed == 0:
            return
            
        records_per_second = self.records_generated / elapsed
        remaining_records = self.total_records - self.records_generated
        eta_seconds = remaining_records / records_per_second if records_per_second > 0 else 0
        
        progress_pct = (self.records_generated / self.total_records) * 100
        
        # Format ETA
        if eta_seconds < 60:
            eta_str = f"{int(eta_seconds)}s"
        elif eta_seconds < 3600:
            eta_str = f"{int(eta_seconds / 60)}m {int(eta_seconds % 60)}s"
        else:
            hours = int(eta_seconds / 3600)
            minutes = int((eta_seconds % 3600) / 60)
            eta_str = f"{hours}h {minutes}m"
        
        print(f"\r📊 Progress: {self.records_generated:,}/{self.total_records:,} "
              f"({progress_pct:.1f}%) | "
              f"Chunk: {self.chunks_completed}/{self.total_chunks} | "
              f"Speed: {records_per_second:.0f} rec/s | "
              f"ETA: {eta_str}", end='', flush=True)
    
    def generate_chunks(self, 
                       record_generator: Callable,
                       insert_function: Callable,
                       resume: bool = True) -> int:
        """
        Generate data in chunks
        
        Args:
            record_generator: Function that generates records
            insert_function: Function to insert records into database
            resume: Whether to resume from previous progress
            
        Returns:
            Total number of records generated
        """
        self.start_time = time.time()
        
        # Load previous progress if resuming
        if resume:
            starting_record = self.load_progress()
        else:
            starting_record = 0
            
        print(f"\n🚀 Starting chunked generation: {self.generator_name}")
        print(f"   Total records: {self.total_records:,}")
        print(f"   Chunk size: {self.chunk_size:,}")
        print(f"   Total chunks: {self.total_chunks:,}")
        
        try:
            # Generate remaining records
            while self.records_generated < self.total_records:
                # Calculate chunk size (may be smaller for last chunk)
                remaining = self.total_records - self.records_generated
                current_chunk_size = min(self.chunk_size, remaining)
                
                # Generate chunk
                chunk_start_time = time.time()
                chunk_records = []
                
                for _ in range(current_chunk_size):
                    record = record_generator(self.records_generated)
                    if record:
                        chunk_records.append(record)
                    self.records_generated += 1
                
                # Insert chunk
                if chunk_records:
                    inserted = insert_function(chunk_records)
                    
                chunk_time = time.time() - chunk_start_time
                self.chunks_completed += 1
                
                # Save progress after each chunk
                self.save_progress()
                
                # Print progress
                self.print_progress()
                
                # Print chunk completion for large chunks
                if self.chunk_size >= 100000 or self.chunks_completed % 10 == 0:
                    print(f"\n✓ Chunk {self.chunks_completed}/{self.total_chunks} completed "
                          f"({len(chunk_records):,} records in {chunk_time:.1f}s)")
            
            # Final summary
            total_time = time.time() - self.start_time
            print(f"\n\n✅ Generation complete!")
            print(f"   Total records: {self.records_generated:,}")
            print(f"   Total time: {total_time/60:.1f} minutes")
            print(f"   Average speed: {self.records_generated/total_time:.0f} records/second")
            
            # Clean up progress file
            if os.path.exists(self.progress_file):
                os.remove(self.progress_file)
                
        except KeyboardInterrupt:
            print(f"\n\n⚠️  Generation interrupted at {self.records_generated:,} records")
            print(f"   Progress saved to {self.progress_file}")
            print(f"   Run again with resume=True to continue")
            raise
        except Exception as e:
            print(f"\n\n❌ Error during generation: {e}")
            print(f"   Progress saved to {self.progress_file}")
            raise
            
        return self.records_generated


class BatchInserter:
    """Handles efficient batch insertion with automatic flushing"""
    
    def __init__(self, 
                 table_name: str,
                 insert_function: Callable,
                 batch_size: int = 1000,
                 verbose: bool = True):
        """
        Initialize batch inserter
        
        Args:
            table_name: Name of the target table
            insert_function: Function to insert records
            batch_size: Number of records per insert batch
            verbose: Whether to print insert progress
        """
        self.table_name = table_name
        self.insert_function = insert_function
        self.batch_size = batch_size
        self.verbose = verbose
        
        self.buffer = []
        self.total_inserted = 0
        
    def add(self, record: Dict[str, Any]):
        """Add a record to the buffer"""
        self.buffer.append(record)
        
        # Auto-flush when buffer is full
        if len(self.buffer) >= self.batch_size:
            self.flush()
    
    def flush(self):
        """Insert all buffered records"""
        if not self.buffer:
            return
            
        inserted = self.insert_function(self.buffer)
        self.total_inserted += inserted
        
        if self.verbose and self.total_inserted % (self.batch_size * 10) == 0:
            print(f"   Inserted {self.total_inserted:,} records into {self.table_name}")
        
        self.buffer = []
        
    def __enter__(self):
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Ensure buffer is flushed on exit"""
        self.flush()


def estimate_memory_usage(record_size_bytes: int, chunk_size: int) -> str:
    """
    Estimate memory usage for a given chunk size
    
    Args:
        record_size_bytes: Average size of one record in bytes
        chunk_size: Number of records per chunk
        
    Returns:
        Human-readable memory estimate
    """
    total_bytes = record_size_bytes * chunk_size
    
    if total_bytes < 1024:
        return f"{total_bytes} B"
    elif total_bytes < 1024 * 1024:
        return f"{total_bytes / 1024:.1f} KB"
    elif total_bytes < 1024 * 1024 * 1024:
        return f"{total_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{total_bytes / (1024 * 1024 * 1024):.1f} GB"


def calculate_optimal_chunk_size(total_records: int,
                               record_size_bytes: int,
                               max_memory_mb: int = 100) -> int:
    """
    Calculate optimal chunk size based on memory constraints
    
    Args:
        total_records: Total number of records to generate
        record_size_bytes: Average size of one record
        max_memory_mb: Maximum memory to use in MB
        
    Returns:
        Recommended chunk size
    """
    max_memory_bytes = max_memory_mb * 1024 * 1024
    max_chunk_size = max_memory_bytes // record_size_bytes
    
    # Common chunk sizes for good performance
    standard_sizes = [1000, 5000, 10000, 25000, 50000, 100000, 250000, 500000]
    
    # Find the largest standard size that fits in memory
    for size in reversed(standard_sizes):
        if size <= max_chunk_size:
            return size
    
    # If even smallest standard size is too big, use calculated size
    return min(max_chunk_size, total_records)


if __name__ == "__main__":
    # Example usage
    print("Chunked Generation Utility Module")
    print("=" * 60)
    
    # Example memory calculations
    print("\nMemory usage examples:")
    print(f"  10K records @ 1KB each: {estimate_memory_usage(1024, 10000)}")
    print(f"  100K records @ 500B each: {estimate_memory_usage(500, 100000)}")
    print(f"  1M records @ 200B each: {estimate_memory_usage(200, 1000000)}")
    
    # Example optimal chunk sizes
    print("\nOptimal chunk size examples:")
    print(f"  1M records @ 1KB each: {calculate_optimal_chunk_size(1000000, 1024):,}")
    print(f"  100M records @ 200B each: {calculate_optimal_chunk_size(100000000, 200):,}")
    print(f"  1B records @ 100B each: {calculate_optimal_chunk_size(1000000000, 100):,}")