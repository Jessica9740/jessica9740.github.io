---
title: "MCP(Model Context Protocol)란? AI와 데이터를 연결하는 새로운 표준"
excerpt: Anthropic이 2024년 11월 공개한 MCP는 AI 모델과 외부 데이터 소스를 연결하는 개방형 표준 프로토콜입니다. 이 글에서는 MCP의 작동 원리, 핵심 구성 요소, 그리고 실무에서 활용할 수 있는 방법을 자세히 알아봅니다.
tags: [MCP, AI, Anthropic, Claude, LLM]
date: 2025-01-21
---

## MCP란 무엇인가?

**MCP(Model Context Protocol)**는 Anthropic이 2024년 11월 25일 공개한 **개방형 표준 프로토콜**로, AI 모델(특히 LLM)과 외부 데이터 소스 및 도구를 연결하는 통합 인터페이스를 제공합니다. Anthropic은 이를 "AI 애플리케이션을 위한 USB-C 포트"라고 비유합니다. 다양한 데이터 소스마다 별도의 커넥터를 만들 필요 없이, 하나의 표준 방식으로 모든 것을 연결할 수 있다는 의미입니다.

기존에는 Claude, ChatGPT 같은 LLM에 회사 내부 데이터나 GitHub, Slack, 데이터베이스 같은 외부 서비스를 연결하려면 개발자가 매번 맞춤형 통합 코드를 작성해야 했습니다. MCP는 이러한 **N×M 통합 문제**를 N+M 문제로 단순화합니다.

## 왜 MCP가 등장했는가?

LLM은 학습 시점까지의 지식만 가지고 있고, 실시간 정보나 사용자의 개인 데이터에 접근할 수 없다는 본질적 한계가 있습니다. 이를 보완하기 위해 다음과 같은 방식들이 사용되어 왔습니다:

- **RAG(Retrieval-Augmented Generation)**: 벡터 DB에서 관련 문서를 검색해 컨텍스트로 제공
- **Function Calling**: 모델이 사전 정의된 함수를 호출하도록 학습
- **Plugin/Custom Connector**: 각 서비스마다 개별 통합 구현

이 방법들은 모두 **벤더 종속적**이거나 **확장성이 떨어진다**는 단점이 있었습니다. 예를 들어 OpenAI의 플러그인 방식은 ChatGPT에서만 작동하고, 동일한 통합을 Claude에서 사용하려면 처음부터 다시 만들어야 했습니다. MCP는 이를 표준화하여 **한 번 만들면 어디서나 작동**하도록 설계되었습니다.

## MCP의 아키텍처

MCP는 **클라이언트-서버 아키텍처**를 따르며, JSON-RPC 2.0 메시지 형식을 사용합니다. 핵심 구성 요소는 세 가지입니다.

### 1. Host (호스트)
사용자가 직접 상호작용하는 AI 애플리케이션입니다. Claude Desktop, Cursor, Zed 같은 IDE 또는 커스텀 챗봇이 여기에 해당합니다.

### 2. Client (클라이언트)
호스트 내부에서 서버와 1:1로 연결을 유지하는 컴포넌트입니다. 메시지 라우팅, 권한 관리, 상태 추적을 담당합니다.

### 3. Server (서버)
실제로 데이터나 기능을 제공하는 프로그램입니다. GitHub MCP 서버라면 이슈 조회, PR 생성 같은 기능을 노출하고, PostgreSQL MCP 서버라면 SQL 쿼리 실행 기능을 제공합니다.

## MCP가 제공하는 세 가지 기본 요소

MCP 서버는 다음 세 가지 유형의 기능(primitives)을 호스트에 노출할 수 있습니다.

### Resources (리소스)
LLM이 읽을 수 있는 **읽기 전용 데이터**입니다. 파일 내용, 데이터베이스 스키마, API 응답 등이 해당됩니다. URI 형태로 식별되며 (`file:///path/to/file`, `postgres://table/users`), 호스트가 컨텍스트로 모델에 주입합니다.

### Tools (도구)
LLM이 **실행할 수 있는 함수**입니다. 파일 작성, API 호출, 코드 실행 등 부수 효과(side effect)가 있는 작업을 수행합니다. 각 도구는 JSON Schema로 입력 파라미터를 정의합니다.

### Prompts (프롬프트)
사용자가 선택할 수 있는 **재사용 가능한 프롬프트 템플릿**입니다. 슬래시 명령(`/summarize`, `/review`)이나 메뉴 형태로 노출되어 일관된 작업 흐름을 제공합니다.

## 통신 방식

MCP는 두 가지 전송(transport) 방식을 지원합니다:

- **stdio**: 로컬 프로세스 간 표준 입출력으로 통신. 보안성이 높고 구현이 간단해 로컬 도구에 주로 사용
- **HTTP + SSE(Server-Sent Events)**: 원격 서버와 통신. 클라우드 기반 서비스 연동에 적합

모든 메시지는 JSON-RPC 2.0 규격을 따르며, 초기화 시 서버와 클라이언트가 **capability negotiation**(기능 협상)을 통해 서로 지원하는 기능을 합의합니다.

## 실제 활용 사례

Anthropic은 공식 발표와 함께 다양한 **레퍼런스 서버**를 오픈소스로 공개했습니다:

- **GitHub/GitLab**: 저장소 검색, 이슈 관리, PR 생성
- **Google Drive**: 문서 검색 및 읽기
- **Slack**: 메시지 조회 및 전송
- **PostgreSQL/SQLite**: 읽기 전용 SQL 쿼리
- **Filesystem**: 로컬 파일 시스템 접근
- **Puppeteer**: 웹 브라우저 자동화

Block(전 Square), Apollo, Sourcegraph, Replit 같은 기업들이 초기부터 MCP를 자사 제품에 도입했고, 2025년에는 OpenAI와 Google DeepMind도 MCP 지원을 발표하면서 사실상 **업계 표준**으로 자리 잡고 있습니다.

## 간단한 MCP 서버 예시

Python SDK를 사용하면 매우 간단하게 서버를 만들 수 있습니다:

```python
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Weather Server")

@mcp.tool()
def get_weather(city: str) -> str:
    """도시 이름을 받아 현재 날씨를 반환합니다."""
    # 실제 API 호출 로직
    return f"{city}의 날씨는 맑음, 기온 22°C"

if __name__ == "__main__":
    mcp.run()
```

이 서버를 Claude Desktop의 설정 파일(`claude_desktop_config.json`)에 등록하면, Claude가 자동으로 이 도구를 인식하고 사용자가 날씨를 물어볼 때 호출하게 됩니다.

## MCP의 장점

1. **표준화**: 한 번 구현한 서버를 Claude, Cursor, Zed 등 모든 MCP 호환 호스트에서 사용 가능
2. **모듈성**: 필요한 기능만 골라서 조합 가능
3. **보안**: 서버가 사용자의 로컬 환경에서 실행되므로 민감한 데이터를 외부로 보내지 않아도 됨
4. **오픈소스**: 프로토콜 사양과 SDK 모두 MIT 라이선스로 공개
5. **언어 독립적**: TypeScript, Python, Java, Kotlin, C# 등 다양한 SDK 제공

## 한계와 고려사항

MCP가 만능은 아닙니다. 도입 전 다음 사항을 고려해야 합니다:

- **보안 위험**: 악의적인 MCP 서버는 사용자 데이터에 접근하거나 위험한 명령을 실행할 수 있습니다. 검증된 서버만 사용해야 합니다.
- **프롬프트 인젝션**: 외부 데이터에 숨겨진 지시문이 LLM의 동작을 왜곡할 수 있습니다.
- **인증 표준 미성숙**: 원격 서버 인증을 위한 OAuth 통합이 2025년 들어 정식화되었지만, 여전히 발전 중입니다.
- **성능**: 도구가 많아질수록 LLM이 어떤 도구를 선택할지 판단하는 비용이 증가합니다.

## 마치며

MCP는 단순한 기술 사양을 넘어 **AI 생태계의 인터페이스 표준**으로 빠르게 자리 잡고 있습니다. 웹의 HTTP, 데이터베이스의 ODBC처럼, AI 에이전트가 외부 세계와 상호작용하는 공통 언어가 될 가능성이 높습니다.

개발자라면 지금이 학습하기 좋은 시점입니다. 공식 문서([modelcontextprotocol.io](https://modelcontextprotocol.io))에서 시작하여, 본인의 업무 흐름에 맞는 작은 MCP 서버를 만들어 보는 것을 추천합니다. AI를 단순한 챗봇이 아닌 **실제 시스템과 연결된 에이전트**로 활용하는 첫걸음이 될 것입니다.