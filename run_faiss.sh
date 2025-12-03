#!/bin/bash

NUM_PER_BATCH=10000 vectordbbench faiss \
  --case-type Performance768D1M \
  --metric-type COSINE \
  --m 32 \
  --ef-construction 300 \
  --ef-search 300 \
  --batch-size 20000 \
  --num-threads 0 \
  --faiss-root /data/third-party/faiss/linux-x64 \
  --client-library /opt/code/faissclient/lib/libfaissclient.so
