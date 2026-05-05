---
category: AI
date: 2025-01-22
excerpt: Anthropic이 공개한 MCP는 AI 모델이 외부 데이터와 도구에 안전하게 접근할 수 있도록 돕는 개방형 표준입니다. 이 글에서는
  MCP의 개념, 작동 원리, 실제 활용 사례까지 체계적으로 정리합니다.
tags:
- MCP
- AI
- Anthropic
- Claude
- 개발자도구
title: 'MCP(Model Context Protocol) 완벽 가이드: AI와 외부 세계를 연결하는 표준 프로토콜'
---

## MCP란 무엇인가?

**MCP(Model Context Protocol)** 는 2024년 11월 Anthropic이 발표한 **개방형 표준 프로토콜**입니다. AI 모델(특히 LLM)이 외부 데이터 소스, 도구, 서비스와 일관된 방식으로 통신할 수 있도록 설계되었습니다.

지금까지 AI 어시스턴트가 데이터베이스, GitHub, Slack, 로컬 파일 시스템 등 외부 자원에 접근하려면 각 서비스마다 별도의 통합 코드를 작성해야 했습니다. MCP는 이를 **"AI를 위한 USB-C 포트"** 처럼 표준화하는 것을 목표로 합니다. 즉, 한 번 MCP 서버를 구현하면 MCP를 지원하는 모든 AI 클라이언트가 동일한 방식으로 그 자원을 활용할 수 있습니다.

## 왜 MCP가 필요한가?

LLM은 본질적으로 학습 시점까지의 데이터만 알고 있으며, 실시간 정보나 사용자의 개인 데이터에는 접근하지 못합니다. 이 한계를 극복하기 위해 그동안 다양한 방식이 사용되어 왔습니다.

- **Function Calling**: OpenAI, Google 등 각 모델 제공사마다 사양이 달라 호환성이 낮음
- **플러그인 시스템**: 플랫폼에 종속적이며 확장성이 제한적
- **RAG**: 정적 문서 검색에는 유용하지만 동적인 작업 수행에는 한계

이런 분절된 환경을 해결하기 위해 등장한 것이 MCP입니다. **"M개의 모델 × N개의 도구"** 라는 N×M 통합 문제를, **"M+N"** 으로 단순화한다는 점이 핵심 가치입니다.

## MCP의 기본 아키텍처

MCP는 **클라이언트-서버 아키텍처**를 따릅니다. JSON-RPC 2.0을 기반으로 메시지를 주고받으며, 다음 세 가지 주요 구성 요소가 있습니다.

### 1. Host (호스트)
사용자가 직접 사용하는 AI 애플리케이션입니다. 예: **Claude Desktop**, Cursor, Zed, Continue 같은 IDE 플러그인.

### 2. Client (클라이언트)
호스트 내부에서 서버와 1:1 연결을 관리하는 컴포넌트로, 메시지를 송수신하고 권한을 처리합니다.

### 3. Server (서버)
실제 기능을 제공하는 프로세스입니다. 파일 시스템, 데이터베이스, API 등 다양한 자원을 노출합니다.

## MCP가 제공하는 세 가지 핵심 기능

MCP 서버는 다음 세 종류의 기능을 클라이언트에게 노출할 수 있습니다.

### 📁 Resources (리소스)
파일, 데이터베이스 레코드, API 응답처럼 **읽을 수 있는 데이터**를 제공합니다. 모델이 컨텍스트로 활용할 정적/반정적 정보입니다.

### 🛠️ Tools (도구)
모델이 호출할 수 있는 **실행 가능한 함수**입니다. 데이터베이스 쿼리, 이메일 전송, 코드 실행 등 부수 효과(side effect)가 있는 작업을 수행합니다.

### 💬 Prompts (프롬프트)
재사용 가능한 **프롬프트 템플릿**입니다. 사용자가 슬래시 명령처럼 호출하여 특정 워크플로를 시작할 수 있습니다.

## 통신 방식: 두 가지 전송 방법

MCP는 두 가지 표준 전송 메커니즘을 지원합니다.

1. **stdio (Standard I/O)**: 로컬 프로세스 간 통신. 사용자 PC에서 실행되는 도구에 적합합니다.
2. **HTTP + SSE (Server-Sent Events)**: 원격 서버와의 통신에 사용되며, 최근에는 **Streamable HTTP** 방식도 도입되었습니다.

모든 메시지는 JSON-RPC 2.0 형식을 따르므로 언어와 플랫폼에 독립적입니다.

## 실제 사용 예시: Claude Desktop과 파일 시스템 연동

가장 간단한 MCP 활용 예시는 Claude Desktop에 파일 시스템 서버를 연결하는 것입니다. 설정 파일(`claude_desktop_config.json`)에 다음과 같이 추가합니다.

```json
{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-filesystem",
        "/Users/username/Documents"
      ]
    }
  }
}
```

이후 Claude에게 *"Documents 폴더에 있는 PDF 파일들을 요약해줘"* 라고 요청하면, Claude가 MCP를 통해 실제 파일을 읽고 작업을 수행합니다.

## 공식 SDK와 생태계

Anthropic은 다양한 언어로 SDK를 제공합니다.

- **TypeScript / JavaScript**
- **Python**
- **Java / Kotlin**
- **C#**
- **Swift**
- **Rust**

또한 GitHub의 [modelcontextprotocol/servers](https://github.com/modelcontextprotocol/servers) 저장소에는 공식·커뮤니티 서버가 다수 공개되어 있습니다.

- **GitHub MCP Server**: 이슈, PR, 코드 검색
- **Slack MCP Server**: 메시지 읽기·전송
- **PostgreSQL MCP Server**: 읽기 전용 SQL 쿼리
- **Google Drive, Brave Search, Puppeteer** 등

## MCP를 채택한 주요 도구들

2025년 현재, MCP는 빠르게 표준 지위를 확보하고 있습니다.

- **Anthropic Claude Desktop / Claude Code**
- **OpenAI**: 2025년 3월 ChatGPT와 Agents SDK에서 MCP 공식 지원 발표
- **Google DeepMind**: Gemini SDK에서 MCP 지원
- **Cursor, Windsurf, Zed, Replit** 등 주요 AI 코드 에디터
- **Block(구 Square), Apollo** 등 기업 사용 사례 다수

특히 **OpenAI와 Google이 모두 MCP를 채택**한 것은 이 프로토콜이 사실상 산업 표준으로 자리 잡고 있음을 보여주는 강력한 신호입니다.

## 보안과 주의 사항

MCP 서버는 사용자의 데이터와 시스템에 접근하므로 **보안이 매우 중요**합니다. 알려진 위험 요소는 다음과 같습니다.

- **Prompt Injection**: 외부 데이터에 숨겨진 악의적 지시가 모델을 조종할 수 있음
- **과도한 권한**: 서버가 필요 이상의 권한을 요구할 수 있음
- **검증되지 않은 서드파티 서버**: 악성 서버를 설치하면 민감 정보가 유출될 수 있음

따라서 다음 원칙을 지키는 것이 좋습니다.

1. **신뢰할 수 있는 출처**의 서버만 설치
2. **최소 권한 원칙**에 따라 접근 범위를 제한
3. 중요한 작업에 대해 **사용자 승인(Human-in-the-loop)** 을 요구
4. 민감 데이터를 다루는 서버는 **로컬 stdio 방식**을 우선 고려

## MCP의 한계와 발전 방향

MCP는 강력하지만 아직 발전 중인 표준입니다.

- **인증/권한 모델**: OAuth 통합이 점진적으로 추가되는 중
- **세션 관리**: 장시간 작업을 위한 상태 관리 개선 필요
- **표준화된 디스커버리**: 서버를 찾고 신뢰성을 검증하는 메커니즘이 미흡

Anthropic과 커뮤니티는 이를 해결하기 위해 **MCP 레지스트리**, **OAuth 2.1 기반 인증**, **Streamable HTTP** 등을 빠르게 도입하고 있습니다.

## 결론: 왜 지금 MCP를 알아야 하는가?

MCP는 단순한 라이브러리가 아니라, **AI 에이전트 시대의 인터페이스 표준**으로 자리 잡고 있습니다. 웹의 HTTP, 언어 도구의 LSP(Language Server Protocol)가 그러했듯, MCP는 AI 시스템과 현실 세계를 연결하는 공통 언어가 될 가능성이 큽니다.

개발자라면 자신의 서비스나 도구를 MCP 서버로 노출함으로써 **수많은 AI 호스트와 즉시 통합**될 수 있고, 사용자라면 자신의 워크플로에 맞는 서버를 조합하여 **개인화된 AI 어시스턴트**를 구성할 수 있습니다.

지금은 MCP 생태계가 폭발적으로 성장하는 초기 시점입니다. 직접 공식 문서([modelcontextprotocol.io](https://modelcontextprotocol.io))를 살펴보고, 간단한 서버를 만들어보는 것만으로도 다가오는 AI 통합 시대를 한발 앞서 준비하는 좋은 출발점이 될 것입니다.