NUM_PER_BATCH=10000 vectordbbench vdsshnsw \
  --grpc-host 172.17.0.2 \
  --grpc-port 50051 \
  --case-type Performance768D1M \
  --m 32 \
  --ef-construction 300 \
  --ef-search 300
