#!/bin/bash

# VDSS Benchmark Script
# 
# Storage Types:
#   --storage-type zendb  (default, persistent storage)
#   --storage-type mem    (in-memory only, faster but no persistence)

# Example 1: Using ZenDB (persistent storage)
# NUM_PER_BATCH=10000 vectordbbench vdsshnsw \
#   --grpc-host 172.17.0.2 \
#   --grpc-port 50051 \
#   --case-type Performance768D1M \
#   --m 32 \
#   --ef-construction 300 \
#   --ef-search 300 \
#   --storage-type zendb

# Example 2: Using MEM (in-memory storage, faster)
NUM_PER_BATCH=10000 vectordbbench vdsshnsw \
  --grpc-host 172.17.0.2 \
  --grpc-port 50051 \
  --case-type Performance768D1M \
  --m 32 \
  --ef-construction 300 \
  --ef-search 300 \
  --storage-type mem
