#!/bin/bash
# ============================================================================
# Regenerate Python gRPC code from proto files
# ============================================================================
#
# Requirements:
#   - protobuf >= 6.31.0
#   - grpcio-tools
#
# Install with:
#   pip install 'protobuf>=6.31.0' grpcio-tools --upgrade
#
# ============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "============================================"
echo "Regenerating VDSS Python gRPC code"
echo "============================================"
echo ""
echo "Working directory: $(pwd)"
echo ""

# Check Python version
PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
echo "Python version: $PYTHON_VERSION"

# Check if grpc_tools is installed
if ! python3 -c "import grpc_tools" 2>/dev/null; then
    echo ""
    echo "Error: grpc_tools not found!"
    echo ""
    echo "Please install required packages:"
    echo "  pip install 'protobuf>=6.31.0' grpcio-tools --upgrade"
    echo ""
    exit 1
fi

# Check protobuf version
PROTOBUF_VERSION=$(python3 -c "import google.protobuf; print(google.protobuf.__version__)" 2>/dev/null || echo "unknown")
echo "Protobuf version: $PROTOBUF_VERSION"

# Verify protobuf version is >= 6.31.0
if [[ "$PROTOBUF_VERSION" != "unknown" ]]; then
    MAJOR_VERSION=$(echo $PROTOBUF_VERSION | cut -d. -f1)
    if [ "$MAJOR_VERSION" -lt 6 ]; then
        echo ""
        echo "Warning: Protobuf version $PROTOBUF_VERSION is too old!"
        echo "VDSS requires Protobuf >= 6.31.0"
        echo ""
        echo "Please upgrade with:"
        echo "  pip install 'protobuf>=6.31.0' --upgrade"
        echo ""
        read -p "Continue anyway? (y/N) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
fi

# Check proto files exist
if [ ! -f "vdss_types.proto" ] || [ ! -f "vdss_service.proto" ]; then
    echo ""
    echo "Error: Proto files not found!"
    echo "Expected files:"
    echo "  - vdss_types.proto"
    echo "  - vdss_service.proto"
    echo ""
    exit 1
fi

echo ""
echo "Proto files found:"
echo "  - vdss_types.proto"
echo "  - vdss_service.proto"
echo ""

# Generate Python code
echo "Generating Python code..."
echo ""
python3 -m grpc_tools.protoc \
    -I. \
    --python_out=. \
    --pyi_out=. \
    --grpc_python_out=. \
    vdss_types.proto \
    vdss_service.proto

if [ $? -eq 0 ]; then
    echo ""
    echo "============================================"
    echo "✓ Successfully generated:"
    echo "============================================"
    echo "  - vdss_types_pb2.py"
    echo "  - vdss_types_pb2.pyi"
    echo "  - vdss_types_pb2_grpc.py"
    echo "  - vdss_service_pb2.py"
    echo "  - vdss_service_pb2.pyi"
    echo "  - vdss_service_pb2_grpc.py"
    echo ""
    echo "✓ Done!"
    echo ""
else
    echo ""
    echo "✗ Failed to generate Python code"
    echo ""
    exit 1
fi
