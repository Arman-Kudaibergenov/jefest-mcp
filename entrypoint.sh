#!/bin/sh
set -e

mkdir -p /data/rlm /data/logs /data/temp

echo "Starting Jefest MCP Server + RLM"
exec supervisord -c /app/supervisord.conf -n
