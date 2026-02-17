이 문서는 Antigravity가 순차적으로 실행해야 할 MVP 구현 태스크 목록입니다. 각 단계는 이전 단계의 완료를 전제로 합니다.

#### Phase 1: Environment & State Setup

* [ ] `pyproject.toml` 또는 `requirements.txt`에 의존성 추가: `langchain`, `langgraph`, `langchain-openai` (또는 `langchain-groq` / 로컬 모델용 `langchain-community`), `pydantic`, `unstructured` (문서 파싱용).
* [ ] `state.py` 생성: `AGENTS.md`에 명시된 `GraphState` TypedDict(또는 Pydantic BaseModels) 정의.
* [ ] LLM 인스턴스 초기화 팩토리 함수 작성 (Groq, OpenAI 또는 로컬 Ollama 모델 연결 지원).

#### Phase 2: Core Nodes Implementation (`nodes.py`)

* [ ] **Node `load_document` 구현:** 파일 확장자에 따른 Document Loader (PyPDFLoader, TextLoader 등) 구성 및 텍스트 반환.
* [ ] **Node `extract_toc` 구현:** `with_structured_output`을 사용하여 문서를 분석하고 `List[Topic]` 형태의 목차 객체를 반환하는 LLM 체인 작성.
* [ ] **Node `generate_draft` 구현:** 특정 토픽에 대한 블로그 포스트(Markdown)를 생성하는 프롬프트 템플릿 및 LLM 호출 로직 작성.
* [ ] **Node `generate_demo_ideas` 구현:** 초안 컨텍스트를 받아 실습용 코드 스니펫이나 Mermaid 다이어그램 아이디어를 반환하는 프롬프트 체인 작성.
* [ ] **Node `aggregate_post` 구현:** 초안과 데모 아이디어를 묶어 `generated_posts` 리스트에 append 하고 `current_index`를 업데이트하는 로직 작성.

#### Phase 3: LangGraph Construction (`graph.py`)

* [ ] `StateGraph(GraphState)` 인스턴스화.
* [ ] Phase 2에서 만든 모든 노드를 그래프에 `add_node`로 등록.
* [ ] 엣지(Edge) 연결 로직 구현:
* `START` -> `load_document` -> `extract_toc`
* `extract_toc` -> `generate_draft`
* `generate_draft` -> `generate_demo_ideas` -> `aggregate_post`


* [ ] **Conditional Edge 추가:** `aggregate_post` 이후, `current_index`가 `series_toc`의 길이보다 작으면 `generate_draft`로 루프(Loop)를 돌고, 같거나 크면 `END`로 라우팅하는 조건부 엣지 작성.
* [ ] 그래프 컴파일 (`graph.compile()`).

#### Phase 4: Main Execution & CLI (`main.py`)

* [ ] 사용자 입력을 받는 간단한 CLI 진입점(Entry point) 작성 (문서 경로 입력).
* [ ] 컴파일된 그래프에 초기 상태(State)를 주입하고 `graph.invoke()` 실행.
* [ ] 최종 결과물(`generated_posts`)을 읽기 좋게 콘솔에 출력하거나, `/output` 디렉토리에 `[01_목차명.md]`, `[02_목차명.md]` 형태로 마크다운 파일로 자동 저장하는 I/O 로직 작성.

#### Phase 5: MVP Testing

* [ ] OWASP Top 10 요약본이나 짧은 RFC 문서를 더미 데이터로 활용하여 파이프라인 전체(문서 입력 -> 다중 포스트 마크다운 파일 생성)가 정상 동작하는지 테스트 및 디버깅.