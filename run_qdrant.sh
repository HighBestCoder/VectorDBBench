vectordbbench qdrantlocal \
  --url "http://172.17.0.4:6333" \
  --grpc-port 6334 \
  --prefer-grpc \
  --case-type Performance1536D50K \
  --m 16 \
  --ef-construct 200 \
  --hnsw-ef 100 \
  --db-label "qdrant_grpc_test"
