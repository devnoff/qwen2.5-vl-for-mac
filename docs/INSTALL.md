# Qwen-2.5-VL 모델 설치 가이드

이 가이드는 Apple Silicon M4 Pro 48GB 환경에서 Qwen-2.5-VL 모델을 설치하고 구성하는 과정을 자세히 설명합니다.

## 사전 요구 사항

시작하기 전에 다음 요구 사항이 충족되었는지 확인하세요:

1. **시스템 요구 사항**:
   - Apple Silicon M4 Pro (또는 M1/M2/M3) Mac
   - 최소 32GB RAM (48GB 이상 권장)
   - 60GB 이상의 여유 저장 공간
   - macOS Sonoma 또는 최신 버전

2. **소프트웨어 요구 사항**:
   - Python 3.12
   - Git
   - Homebrew (선택 사항)

3. **Open Web UI**:
   - localhost:3000에서 실행 중인 Open Web UI 인스턴스 (API 연결에 필요)

## 설치 단계

### 1. Python 3.12 설치

```bash
# Homebrew를 사용하여 Python 3.12 설치
brew install python@3.12

# 설치 확인
python3.12 --version
```

### 2. 저장소 복제 또는 디렉토리 생성

```bash
# 옵션 1: 저장소에서 복제한 경우
git clone https://your-repository-url/qwen2.5vl.git
cd qwen2.5vl

# 옵션 2: 수동으로 디렉토리 생성 및 파일 복사한 경우
mkdir -p ~/qwen2.5vl
cd ~/qwen2.5vl
# 모든 스크립트 파일을 이 디렉토리에 복사
```

### 3. 전체 설치 프로세스 시작

자동 설치 프로세스를 시작합니다:

```bash
./setup_qwen_vl.sh
```

이 스크립트는 대화형으로 진행되며 다음 단계를 안내합니다:
- Python 3.12 환경 설정
- 모델 다운로드
- MLX 변환 (Apple Silicon 최적화)
- API 서버 설정 (Open Web UI 연결)

### 4. 단계별 수동 설치 (선택 사항)

전체 스크립트 대신 개별 단계를 수동으로 실행하려면:

#### a. 환경 설정

```bash
./setup_environment.sh
```

이 단계에서는 다음 작업을 수행합니다:
- Python 3.12 가상 환경 생성
- MLX 및 관련 라이브러리 설치
- 작업 디렉토리 구조 생성

#### b. 모델 다운로드

```bash
source ~/qwen2.5vl/venv/bin/activate  # 가상 환경 활성화
./download_model.sh
```

이 단계에서는:
- Git LFS를 사용하여 선택한 Qwen-2.5-VL 모델 다운로드
- 3B, 7B, 32B 중 선택 가능

#### c. MLX 변환 (Apple Silicon 최적화)

```bash
source ~/qwen2.5vl/venv/bin/activate  # 가상 환경 활성화
./convert_to_mlx.sh
```

이 단계에서는:
- Hugging Face 모델을 MLX 형식으로 변환
- 선택적으로 모델을 양자화하여 메모리 사용량 줄이기
- 테스트 스크립트 생성

#### d. API 서버 설정

```bash
source ~/qwen2.5vl/venv/bin/activate  # 가상 환경 활성화
./scripts/start_api_server.sh
```

이 단계에서는:
- FastAPI 기반 API 서버 생성
- OpenAI 호환 API 엔드포인트 설정
- API 서버 백그라운드 실행

### 6. Open Web UI 연결

API 서버를 실행한 후:

```bash
cat connect_to_openwebui.md
```

이 문서는 localhost:3000에서 실행 중인 Open Web UI를 API 서버에 연결하는 단계를 안내합니다.

## API 서버 관리

### API 서버 상태 확인

```bash
ps -ef | grep "python.*app.api.server"
```

### API 서버 중지

```bash
pkill -f "python.*app.api.server"
```

### API 서버 로그 확인

```bash
cat ~/qwen2.5vl/logs/api_server.log
# 또는 실시간 로그 보기
tail -f ~/qwen2.5vl/logs/api_server.log
```

### API 서버 재시작

```bash
cd ~/qwen2.5vl
./scripts/start_api_server.sh
```

## 모델 테스트

### MLX 모델 직접 테스트

```bash
source ~/qwen2.5vl/venv/bin/activate
python ~/qwen2.5vl/tests/test_api.py
```

## 문제 해결

### 일반적인 문제

1. **메모리 부족 오류**:
   - 더 작은 모델 크기 선택 (예: 32B → 7B → 3B)
   - 모델 양자화 적용

2. **설치 오류**:
   - Python 3.12가 설치되어 있는지 확인 
   - 가상 환경이 올바르게 활성화되었는지 확인
   - 모든 필수 패키지가 설치되었는지 확인

3. **모델 다운로드 오류**:
   - 인터넷 연결 확인
   - Git LFS가 설치되어 있는지 확인
   - 충분한 디스크 공간 확인

4. **API 연결 실패**:
   - API 서버가 실행 중인지 확인
   - 포트 설정 확인
   - 로그 파일 검토 (`~/qwen2.5vl/logs/api_server.log`)

## 다음 단계

- 프롬프트 엔지니어링으로 성능 향상
- 더 좋은 이미지 품질 또는 해상도 설정을 위한 API 서버 매개변수 조정 