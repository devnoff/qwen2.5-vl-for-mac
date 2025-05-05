# Qwen-2.5-VL MLX API 서버와 Open Web UI 연결 계획

## 프로젝트 목표

Apple Silicon M4 Pro 48GB 환경에서 Qwen-2.5-VL 모델을 MLX로 최적화하고, 이를 Open Web UI와 연결하여 이미지 업로드 및 분석 기능을 구현합니다.

## 단계별 계획

### 1. 개발 환경 설정

- [x] Python 3.12 가상 환경 설정
- [x] MLX 및 관련 라이브러리 설치
- [x] 필요한 디렉토리 구조 생성
- [x] 실행 권한 설정 스크립트 생성

### 2. 모델 다운로드

- [x] Hugging Face Hub API로 Qwen-2.5-VL 모델 다운로드 지원
- [x] Git LFS를 사용한 대체 다운로드 방식 지원
- [x] 3B, 7B, 32B 모델 크기 옵션 제공

### 3. MLX 모델 변환

- [x] Hugging Face 모델을 MLX 형식으로 변환
- [x] 선택적 int4 양자화 지원 (메모리 사용량 감소)
- [x] 변환된 모델 테스트 스크립트 생성

### 4. API 서버 구현

- [x] FastAPI 기반 API 서버 구현
- [x] OpenAI 호환 API 엔드포인트 (/v1/chat/completions)
- [x] 이미지 처리 기능 구현 (Base64 디코딩)
- [x] 백그라운드 실행 및 로깅 설정

### 5. Open Web UI 연결

- [x] 연결 가이드 문서 작성
- [x] API 키 설정 및 엔드포인트 구성 안내
- [x] 모델 설정 및 이미지 지원 활성화 방법 설명
- [x] 문제 해결 가이드 제공

### 6. 디렉토리 구조 리팩토링

- [x] 앱 구조 재구성 (app/ 디렉토리)
- [x] 스크립트 통합 및 정리 (scripts/ 디렉토리)
- [x] 테스트 코드 정리 (tests/ 디렉토리)
- [x] 문서 업데이트

## 기술 스택

- **언어**: Python 3.12
- **모델 프레임워크**: MLX (Apple Silicon 최적화)
- **API 서버**: FastAPI + uvicorn
- **UI**: Open Web UI (localhost:3000)
- **모델**: Qwen-2.5-VL (3B, 7B, 32B 옵션)

## 시스템 아키텍처

```
+------------------+            +--------------------+
|                  |  HTTP/JSON |                    |
|   Open Web UI    +----------->+    MLX API 서버     |
| (localhost:3000) |            | (localhost:8000)   |
|                  |<-----------+                    |
+------------------+            +----------+---------+
                                           |
                                           | 모델 로드
                                           v
                               +-------------------------+
                               |                         |
                               |   Qwen-2.5-VL MLX 모델  |
                               |                         |
                               +-------------------------+
```

## 디렉토리 구조

```
qwen2.5vl/
├── app/                   # API 서버 애플리케이션 
│   ├── api/               # API 엔드포인트 및 모델
│   └── utils/             # 유틸리티 함수
├── scripts/               # 스크립트 
│   └── utils/             # 스크립트 유틸리티
├── tests/                 # 테스트 코드
│   └── test_images/       # 테스트용 이미지
├── models/                # 모델 저장 디렉토리
├── data/                  # 데이터 파일
│   └── sample_requests/   # 샘플 요청 데이터
└── logs/                  # 로그 파일
```

## API 엔드포인트

### 기본 엔드포인트 
- `http://localhost:8000/v1/chat/completions`

### 헬스 체크
- `http://localhost:8000/health`

### 사용 가능한 모델 목록
- `http://localhost:8000/v1/models`

## 연결 과정

1. API 서버 실행 (`./scripts/start_api_server.sh`)
2. Open Web UI 접속 (localhost:3000)
3. 모델 설정에서 다음을 구성:
   - 이름: Qwen-2.5-VL-MLX
   - 모델 유형: OpenAI
   - 엔드포인트: http://localhost:8000/v1
   - 이미지 지원: 활성화
4. 모델 선택 후 채팅 시작

## 향후 개선 사항

- [ ] 다양한 모델 양자화 옵션 추가 (int8, float16 등)
- [ ] 더 많은 비전 기능 지원 (이미지 생성 등)
- [ ] API 서버 성능 최적화 및 캐싱
- [ ] 시스템 프롬프트 사용자 정의 지원
- [ ] 자동 업데이트 메커니즘 구현 