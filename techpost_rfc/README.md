# techpost_rfc

**techpost_rfc**는 논문, 백서, 기술 표준 문서(NIST, RFC, OWASP 등)와 같이 방대하고 무거운 텍스트를 분석하여, 읽기 쉬운 **시리즈형 블로그 포스트 초안과 실습/데모 아이디어로 자동 변환**해 주는 LangGraph 기반 워크플로 자동화 툴

## Motivation
자료 읽기 → 목차 구성 → 초안 작성 → 실습 코드 작성

## Key Features
- **Document Ingestion:** PDF, Markdown 등 다양한 형태의 문서를 파싱하고 청크(Chunk) 단위로 처리
- **Smart TOC Extraction:** 전체 문서의 논리적 흐름을 파악하여, 블로그 연재에 적합한 챕터 단위의 목차(TOC)를 자동 기획
- **Draft Generation:** 각 목차에 맞춰 원본 문서의 내용을 바탕으로 기술 블로그 포스트 초안을 Markdown 포맷으로 작성
- **Demo & Code Ideation:** 작성된 초안의 이해를 돕기 위한 실습 코드 Snippet, 아키텍처 다이어그램(Mermaid), Docker Compose 구성 등의 아이디어를 함께 제안

## Architecture (LangGraph Workflow)

본 프로젝트는 LangGraph의 상태(State) 머신을 활용하여 다중 에이전트(Multi-Agent) 형태로 동작합니다. 자세한 노드 및 상태 정의는 [`AGENTS.md`](./AGENTS.md)를 참고하세요.

1. **Document Ingestor:** 문서 로드 및 텍스트 정제
2. **Structure Analyzer:** 연재용 시리즈 목차(TOC) 추출
3. **Draft Writer (Loop):** 목차별 블로그 초안 작성
4. **Demo Ideator (Loop):** 해당 포스트에 어울리는 코드/데모 기획
5. **State Updater & Router:** 결과물 병합 및 다음 목차로 순회(Loop)