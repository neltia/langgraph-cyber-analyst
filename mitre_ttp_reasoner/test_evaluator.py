import json
import logging
import datetime
from tqdm.asyncio import tqdm

logger = logging.getLogger("TTPAnalyzer.Evaluator")


async def evaluate_accuracy(analyzer_app, test_set):
    stats = {"total": len(test_set), "correct_id": 0, "correct_tactic": 0}
    # 파일 저장용
    full_results = []

    logger.info(f"Engine Started: Processing {len(test_set)} samples")
    pbar = tqdm(test_set, desc="Analyzing TTP")

    async for case in pbar:
        # 모델에 전달할 통합 페이로드 구성 (Context + Payload)
        combined_payload = f"[Context]\n{case.get('context', 'N/A')}\n\n[Payload]\n{case['payload']}"
        final_state = await analyzer_app.ainvoke({"payload": combined_payload})
        res = final_state['analysis']

        # 결과 데이터 수집 (JSON 저장용)
        full_results.append({
            "payload": case['payload'],
            "predicted": res.model_dump(),
            "label": case['label']
        })

        # 터미널에는 핵심 로그만 간결하게 출력
        status = "MATCH" if res.tid == case['label']['tid'] else "MISMATCH"
        pbar.write(f"[{status}] ID: {res.tid} | Conf: {res.confidence:.2f}")

        if res.tid == case['label']['tid']:
            stats["correct_id"] += 1

        if res.tactic == case['label']['tactic']:
            stats["correct_tactic"] += 1

    # 별도 JSON 파일로 결과 저장
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    report_filename = f"report_{timestamp}.json"
    with open(report_filename, "w", encoding="utf-8") as f:
        json.dump(full_results, f, indent=2, ensure_ascii=False)

    accuracy = stats['correct_id'] / stats['total'] if stats['total'] > 0 else 0
    tactic_accuracy = stats['correct_tactic'] / stats['total'] if stats['total'] > 0 else 0

    logger.info(f"Report saved to {report_filename}")
    logger.info(f"Final Accuracy - TID: {accuracy:.2%}, Tactic: {tactic_accuracy:.2%}")
