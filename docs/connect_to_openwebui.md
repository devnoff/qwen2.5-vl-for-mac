# Open Web UI에 Qwen2.5-VL MLX 모델 연결하기

이 문서에서는 Qwen2.5-VL MLX 모델을 Open Web UI에 연결하는 방법을 안내합니다.

## 사전 요구사항

1. API 서버가 실행 중이어야 합니다. (`scripts/start_api_server.sh` 스크립트 실행 완료)
2. Open Web UI가 설치되어 있어야 합니다.

## 연결 단계

### 1. Open Web UI 접속

웹 브라우저에서 Open Web UI에 접속합니다. 일반적으로 다음 URL 중 하나를 사용합니다:
- 로컬 설치: `http://localhost:3000`
- 도커 설치: `http://localhost:8080`

### 2. 새 모델 추가

1. Open Web UI 대시보드에서 상단 메뉴의 "모델" 또는 "Models"를 클릭합니다.
2. "모델 추가" 또는 "Add a model" 버튼을 클릭합니다.

### 3. 모델 설정

다음과 같이 모델 정보를 입력합니다:

- **모델 이름**: `Qwen2.5-VL-MLX` (또는 원하는 이름)
- **API 유형**: `OpenAI API`
- **API 키**: 아무 문자열 (예: `mlx-api`)
- **API 기본 URL**: `http://localhost:8000/v1` (포트는 API 서버 실행 시 선택한 포트로 변경)
- **모델 ID**: `qwen2.5-vl-7B-mlx` (또는 선택한 모델명)
- **사용 가능한 기능**: `chat, vision` (멀티모달 지원을 위해 vision 확인)

### 4. 고급 설정 (선택사항)

- **컨텍스트 길이**: `4096` (또는 모델에 적합한 값)
- **이미지 업로드 활성화**: 반드시 체크 (시각 기능 사용을 위해 필요)
- **스트리밍 활성화**: 원하는 대로 설정

### 5. 저장 및 테스트

1. "저장" 또는 "Save" 버튼을 클릭합니다.
2. 홈 화면으로 돌아가 새로 추가한 모델을 선택합니다.
3. 채팅 창에 메시지를 입력하고 이미지를 업로드하여 모델이 제대로 작동하는지 테스트합니다.

## 문제 해결

연결에 문제가 있는 경우 다음을 확인하세요:

1. API 서버가 실행 중인지 확인:
   ```bash
   ps -ef | grep "python.*app.api.server"
   ```

2. API 서버 로그 확인:
   ```bash
   tail -f ~/workspace/llm/qwen2.5vl/logs/api_server.log
   ```

3. 설정한 포트가 방화벽에 막혀있지 않은지 확인
4. Open Web UI와 API 서버가 동일한 네트워크에 있는지 확인

## 장점

- **로컬 프라이버시**: 모든 데이터가 로컬에서 처리되어 개인정보가 보호됩니다.
- **비용 절감**: 클라우드 API 비용이 없습니다.
- **오프라인 사용**: 인터넷 연결 없이도 사용 가능합니다.
- **시각 이해 기능**: 이미지를 업로드하여 분석하고 이해할 수 있습니다.

## 추가 정보

- Qwen2.5-VL MLX 모델에 대한 자세한 내용은 [Qwen 공식 문서](https://github.com/QwenLM/Qwen2.5-VL)를 참조하세요.
- MLX 프레임워크에 대한 자세한 내용은 [MLX 문서](https://github.com/ml-explore/mlx)를 참조하세요.
- Open Web UI에 대한 자세한 내용은 [Open Web UI 공식 문서](https://docs.openwebui.com/)를 참조하세요. 