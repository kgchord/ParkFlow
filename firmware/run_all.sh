#!/usr/bin/env bash
# Build + test everything; logs go to firmware/test_logs/. Host only, no network.
set -u
cd "$(dirname "$0")"
LOG=test_logs
mkdir -p "$LOG"
rc=0
{ echo "# $(date -u +%Y-%m-%dT%H:%M:%SZ)"; g++ --version | head -1; } > "$LOG/lane_controller_build.log"
( cd lane_controller && make clean >/dev/null && make 2>&1 ) >> "$LOG/lane_controller_build.log" || rc=1
{ echo "# plain build"; ./lane_controller/build/test_all; echo "exit=$?"; echo; echo "# ASan+UBSan build"; ./lane_controller/build/test_all_san; echo "exit=$?"; } > "$LOG/lane_controller_tests.log" 2>&1
grep -q "exit=0" "$LOG/lane_controller_tests.log" && ! grep -q "exit=[1-9]" "$LOG/lane_controller_tests.log" || rc=1
{ python3 --version; pytest --version; } > "$LOG/edge_node_pytest.log" 2>&1
( cd edge_node && pytest -v tests 2>&1 ) >> "$LOG/edge_node_pytest.log" || rc=1
( cd edge_node && python3 -m parkflow_edge.simulator --out ../$LOG/simulator_run.json ) > "$LOG/simulator.log" 2>&1 || rc=1
( cd edge_node && python3 bench_fusion.py ../$LOG/fusion_latency_host.json ) > "$LOG/fusion_latency_host.log" 2>&1 || rc=1
echo "overall exit=$rc"
exit $rc
