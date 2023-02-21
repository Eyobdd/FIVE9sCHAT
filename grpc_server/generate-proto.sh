#!/bin/bash
echo "Generating proto grpc files..."
python3 -m grpc_tools.protoc -I=proto/ --python_out=proto/ --grpc_python_out=proto/ proto/chat.proto
echo "DONE"
