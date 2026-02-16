import yaml
import re
import json
import logging
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import JsonOutputParser, StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from .state import AgentState, AnalysisResult

logger = logging.getLogger("TTPAnalyzer")


def load_prompt(name: str):
    with open(f"prompts/{name}.yaml", "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
    return ChatPromptTemplate.from_template(config['ttp_analysis']['template'])


class TTPAnalyzer:
    def __init__(self, vector_db):
        self.db = vector_db
        self.llm = ChatOpenAI(
            model="Qwen/Qwen2.5-14B-Instruct-AWQ",
            base_url="http://localhost:8000/v1",
            api_key="dummy",
            temperature=0,
            # 서버 응답 대기 시간 설정
            timeout=120
        )
        self.parser = JsonOutputParser(pydantic_object=AnalysisResult)
        self.workflow = self._create_graph()

    async def retrieve(self, state: AgentState):
        try:
            search_gen_prompt = (
                f"다음 HTTP 페이로드를 분석하여 관련된 MITRE ATT&CK 기술을 찾기 위한 "
                f"보안 키워드와 공격 설명을 한 문장으로 요약하세요.\n"
                f"대상: {state['payload'][:200]}"
            )

            # [수정] StrOutputParser()를 붙여 무조건 문자열로 받음
            optimized_query = await (self.llm | StrOutputParser()).ainvoke(search_gen_prompt)

            docs = self.db.max_marginal_relevance_search(
                optimized_query,
                k=10,
                fetch_k=20,
                lambda_mult=0.5
            )

            refined_candidates = [d.page_content for d in docs]
            return {"candidates": refined_candidates, "iteration": state.get('iteration', 0) + 1}

        except Exception as e:
            logger.error(f"Retrieval Error: {str(e)}")
            return {"candidates": [], "iteration": state.get('iteration', 0) + 1}

    async def analyze(self, state: AgentState):
        format_instructions = self.parser.get_format_instructions()
        prompt = load_prompt("ttp_analyzer")

        chain = prompt | self.llm | StrOutputParser()

        try:
            raw_res_text = await chain.ainvoke({
                "payload": state['payload'],
                "candidates": "\n".join(state['candidates']),
                "feedback": state.get('feedback', 'None'),
                "format_instructions": format_instructions
            })

            json_match = re.search(r"\{.*\}", raw_res_text, re.DOTALL)
            if json_match:
                res_dict = json.loads(json_match.group())
                return {"analysis": AnalysisResult(**res_dict)}
            else:
                raise ValueError("No JSON found in response")

        except Exception as e:
            logger.error(f"Analyze Node Error: {str(e)[:50]}...")
            return {"analysis": AnalysisResult(
                is_malicious=False, tid="N/A", technique_name="Error",
                tactic="Error", sub_tactic="N/A", confidence=0.0, reasoning=str(e)
            )}

    async def verify(self, state: AgentState):
        res = state.get('analysis')
        candidates = state.get('candidates', [])

        # 존재 여부 검증 (Hallucination Check)
        # - 모델이 후보군에 없는 ID를 뱉었는지 확인
        is_id_in_candidates = any(res.tid in c for c in candidates)

        # 구체성 검증
        # - 서브 기법(.xxx)이 존재함에도 상위 기법을 선택했는지 체크
        has_sub_technique_in_candidates = any("." in c.split("ID: ")[1].split("\n")[0] for c in candidates if res.tid.split(".")[0] in c)
        is_specific_enough = not (has_sub_technique_in_candidates and "." not in res.tid)

        # 신뢰도 및 논리 근거 검증
        is_reliable = res.confidence >= 0.85 and len(res.reasoning) > 50

        if not is_reliable or not is_id_in_candidates or not is_specific_enough:
            if state.get('iteration', 0) < 3:
                feedback = "분석 결과가 부적절합니다."
                if not is_id_in_candidates:
                    feedback = f"ID {res.tid}는 제공된 후보군에 없습니다. KB 내에서만 선택하세요."
                elif not is_specific_enough:
                    feedback = "더 구체적인 서브 기법(.xxx)이 후보군에 있습니다. 다시 확인하세요."

                return {"feedback": feedback, "is_final": False}

        return {"feedback": "pass", "is_final": True}

    def _create_graph(self):
        graph = StateGraph(AgentState)
        graph.add_node("retrieve", self.retrieve)
        graph.add_node("analyze", self.analyze)
        graph.add_node("verify", self.verify)
        graph.set_entry_point("retrieve")
        graph.add_edge("retrieve", "analyze")
        graph.add_edge("analyze", "verify")

        graph.add_conditional_edges(
            "verify",
            lambda x: "end" if x.get("is_final") else "retry",
            {"retry": "analyze", "end": END}
        )
        return graph.compile()
