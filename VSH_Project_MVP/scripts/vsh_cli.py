from __future__ import annotations

import sys
import argparse
import json
import logging
import time
from pathlib import Path

# ✅ Python path 조정 (scripts/ → parent directory)
sys.path.insert(0, str(Path(__file__).parent.parent))

from vsh_runtime.engine import VshRuntimeEngine
from vsh_runtime.watcher import ProjectWatcher
from vsh_runtime.l3_integration import initialize_l3, get_l3_runner  # ✅ L3 추가
from repository.shared_db_adapter import get_shared_db  # ✅ SharedDB 추가

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)


def _print(payload: dict, fmt: str):
    if fmt == "json":
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    elif fmt == "markdown":
        print(payload.get("previews", {}).get("markdown", ""))
    else:
        print(payload.get("previews", {}).get("inline", ""))


def main() -> None:
    parser = argparse.ArgumentParser(prog="vsh")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sf = sub.add_parser("scan-file")
    sf.add_argument("file")
    sf.add_argument("--format", choices=["json", "markdown", "summary"], default="summary")
    sf.add_argument("--wait-l3", action="store_true", help="Wait for L3 completion (default: false)")

    sp = sub.add_parser("scan-project")
    sp.add_argument("dir")
    sp.add_argument("--format", choices=["json", "markdown", "summary"], default="summary")
    sp.add_argument("--wait-l3", action="store_true", help="Wait for L3 completion (default: false)")

    dg = sub.add_parser("diagnostics")
    dg.add_argument("target")

    wt = sub.add_parser("watch")
    wt.add_argument("dir")
    wt.add_argument("--debounce", type=float, default=1.0)

    args = parser.parse_args()
    
    # ✅ L3 초기화
    shared_db = get_shared_db()
    l3_runner = get_l3_runner(shared_db)
    l3_enabled = initialize_l3(shared_db)
    
    engine = VshRuntimeEngine()

    if args.cmd == "scan-file":
        result = engine.analyze_file(args.file)
        _print(result, args.format)
        
        # ✅ L3 백그라운드 실행
        if l3_enabled:
            logger.info("🔄 Starting L3 validation in background...")
            l3_runner.run_async(args.file)
            
            if args.wait_l3:
                logger.info("⏳ Waiting for L3 completion (max 5min)...")
                if l3_runner.wait_completion(timeout_sec=300):
                    logger.info("✅ L3 completed")
                else:
                    logger.warning("⚠️  L3 timeout")
            else:
                logger.info("💡 Use --wait-l3 to wait for L3 completion")
        
    elif args.cmd == "scan-project":
        result = engine.analyze_project(args.dir)
        _print(result, args.format)
        
        # ✅ L3 백그라운드 실행
        if l3_enabled:
            logger.info("🔄 Starting L3 validation in background...")
            l3_runner.run_async(args.dir)
            
            if args.wait_l3:
                logger.info("⏳ Waiting for L3 completion (max 5min)...")
                if l3_runner.wait_completion(timeout_sec=300):
                    logger.info("✅ L3 completed")
                else:
                    logger.warning("⚠️  L3 timeout")
            else:
                logger.info("💡 Use --wait-l3 to wait for L3 completion")
        
    elif args.cmd == "diagnostics":
        print(json.dumps(engine.get_diagnostics(args.target), ensure_ascii=False, indent=2))
    elif args.cmd == "watch":
        ProjectWatcher(args.dir, debounce_sec=args.debounce).watch_forever()


if __name__ == "__main__":
    main()
