import os
import orjson
import logging
import asyncio
from core.mitre_loader import MitreLoader
from core.vector_engine import VectorEngine
from core.analyzer import TTPAnalyzer
from test_evaluator import evaluate_accuracy


# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger("TTPAnalyzer")


def load_test_cases(filepath="tests/test_cases.json"):
    """외부 JSON 파일에서 테스트 데이터셋을 로드합니다."""
    if not os.path.exists(filepath):
        print(f"[!] Test case file not found: {filepath}")
        return []
    with open(filepath, "r", encoding="utf-8") as f:
        return orjson.loads(f.read())


async def main():
    #  데이터 준비
    MitreLoader.download()

    # 벡터 DB 구축
    # - 최초 1회 실행 후 get_db로 전환
    engine = VectorEngine()
    db_dir = "./db"

    if os.path.exists(db_dir) and os.listdir(db_dir):
        print("[*] 기존 벡터 저장소를 재사용합니다.")
        vector_db = engine.get_db()
    else:
        print("[*] 신규 벡터 저장소를 구축합니다. (최초 1회 소요)")
        refined_data = MitreLoader.load_and_refine()
        vector_db = engine.build_db(refined_data)

    # 분석기 초기화
    analyzer = TTPAnalyzer(vector_db)
    app = analyzer.workflow

    # 테스트 데이터셋 정의
    test_cases = [
        {
            "payload": "GET /index.php?id=1' UNION SELECT NULL, user(), database()-- HTTP/1.1",
            "label": {"tid": "T1190", "tactic": "initial-access"}
        },
        {
            "payload": "POST /upload.php HTTP/1.1\n\n<?php system($_GET['c']); ?>",
            "label": {"tid": "T1505.003", "tactic": "persistence"}
        }
    ]

    # 실행 및 평가
    await evaluate_accuracy(app, test_cases)


if __name__ == "__main__":
    asyncio.run(main())
