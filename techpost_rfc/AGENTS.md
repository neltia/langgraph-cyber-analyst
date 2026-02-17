이 문서는 LangGraph 기반 "블로거 워크플로 자동화 툴"의 그래프 상태(State)와 각 노드(Agent)의 역할 및 입출력 명세를 정의합니다.

코드 작성 시에는 다음의 규칙을 따라야 합니다.
- 언어: Python 3.12
- 패키지 관리자: uv, docker
- 라이브러리 버전: 2026년 2월 기준 최신 버전 사용, langchain==1.0.1
- 코드 작성 스타일 : PEP8 가이드라인 준수

#### 1. Graph State Definition (`State`)

그래프를 관통하며 유지되는 상태 객체입니다. `TypedDict` 또는 Pydantic 모델로 구현합니다.

* `document_content` (str): 로드된 원본 문서 전체 또는 청크된 텍스트.
* `document_metadata` (dict): 문서 메타데이터 (제목, 출처 등).
* `series_toc` (List[dict]): 추출된 연재 포스트 목차 (각 항목은 `topic`, `summary`, `relevant_sections` 포함).
* `current_index` (int): 현재 작업 중인 목차의 인덱스 (Loop 제어용).
* `generated_posts` (List[dict]): 생성 완료된 포스트 객체 배열 (각 항목은 `title`, `draft`, `demo_ideas` 포함).

#### 2. Agents (Nodes)

**Agent A: Document Ingestor (문서 처리기)**

* **Role:** PDF, Markdown 등 다양한 포맷의 표준 문서(NIST, OWASP 등)를 파싱하고 LLM이 처리하기 좋은 형태로 텍스트를 정제합니다.
* **Input:** 파일 경로 또는 URL
* **Output:** `document_content`, `document_metadata` 업데이트

**Agent B: Structure Analyzer (목차 추출기)**

* **Role:** 전체 문서의 구조를 파악하고, 블로그 연재에 적합한 논리적 흐름(챕터/토픽 단위)으로 분해하여 목차(TOC)를 기획합니다.
* **Prompt Strategy:** "당신은 테크니컬 라이터입니다. 주어진 기술/표준 문서를 분석하여, 독자가 이해하기 쉬운 블로그 연재 시리즈 목차를 JSON 형태로 추출하세요."
* **Output:** `series_toc` 업데이트 (Pydantic Structured Output 활용 권장)

**Agent C: Draft Writer (초안 작성기)**

* **Role:** `series_toc`의 개별 토픽과 관련된 원본 문서의 내용을 바탕으로 기술 블로그 포스트 초안(Markdown)을 작성합니다.
* **Input:** `document_content` (또는 관련 청크), 현재 토픽 정보
* **Output:** 임시 변수 `current_draft` 반환

**Agent D: Demo Ideator (데모 기획기)**

* **Role:** 작성된 초안 또는 토픽을 기반으로, 독자의 이해를 도울 수 있는 실습 코드, CLI 명령어, 아키텍처 다이어그램(Mermaid), 또는 Docker Compose 구성 아이디어를 제안합니다.
* **Input:** 현재 토픽 정보, `current_draft`
* **Output:** 임시 변수 `current_demo_ideas` 반환

**Agent E: State Updater & Router (상태 병합 및 라우터)**

* **Role:** Draft Writer와 Demo Ideator의 결과를 병합하여 `generated_posts`에 추가하고, `current_index`를 1 증가시킵니다. 다음 목차가 남아있으면 Agent C로 루프를 돌고, 끝나면 End Node로 라우팅합니다.