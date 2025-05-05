# Qwen2.5-VL MLX 프로젝트

Apple Silicon 기기에서 MLX 프레임워크를 사용하여 [Qwen2.5-VL](https://huggingface.co/Qwen/Qwen2.5-VL) 모델을 실행하는 프로젝트입니다.

## 개요

이 프로젝트는 다음 구성 요소를 포함합니다:

- Qwen2.5-VL 모델의 MLX 변환
- OpenAI 호환 API 서버
- 이미지-텍스트 처리 기능

## 시스템 요구사항

- Apple Silicon Mac (M1/M2/M3/M4)
- macOS 12 이상
- Python 3.10 이상
- 최소 16GB RAM (7B 모델), 32GB RAM (32B 모델 권장)

## 디렉토리 구조

```
qwen2.5vl/
├── app/                   # API 서버 애플리케이션 
│   ├── api/               # API 엔드포인트 및 모델
│   └── utils/             # 유틸리티 함수
├── scripts/               # 스크립트 
│   ├── setup_qwen_vl.sh   # 메인 설치 스크립트
│   ├── setup_environment.sh # 환경 설정 스크립트
│   ├── download_model.sh  # 모델 다운로드 스크립트  
│   ├── convert_to_mlx.sh  # MLX 변환 스크립트
│   ├── start_api_server.sh # API 서버 시작 스크립트
│   └── utils/             # 스크립트 유틸리티
├── docs/                  # 문서 파일들
│   ├── INSTALL.md         # 설치 가이드
│   ├── connect_to_openwebui.md # Open Web UI 연결 가이드
│   └── plan.md            # 프로젝트 계획
├── tests/                 # 테스트 코드
│   └── test_images/       # 테스트용 이미지
├── models/                # 모델 저장 디렉토리
├── data/                  # 데이터 파일
│   └── sample_requests/   # 샘플 요청 데이터
├── logs/                  # 로그 파일
├── setup.sh               # 메인 설치 스크립트 (심볼릭 링크)
└── venv/                  # 가상환경 (이미 존재)
```

## 설치 방법

1. 저장소 클론:
   ```bash
   git clone https://github.com/yourusername/qwen2.5vl.git
   cd qwen2.5vl
   ```

2. 설치 스크립트 실행:
   ```bash
   ./setup.sh
   ```

또는 각 단계를 개별적으로 실행할 수 있습니다:

```bash
# 환경 설정
./scripts/setup_environment.sh

# 모델 다운로드
./scripts/download_model.sh

# MLX 변환
./scripts/convert_to_mlx.sh
```

자세한 설치 방법은 [설치 가이드](docs/INSTALL.md)를 참조하세요.

## 사용 방법

### API 서버 실행

```bash
./scripts/start_api_server.sh
```

이 스크립트는 다음을 수행합니다:
- 사용 가능한 MLX 모델 확인
- 서버 포트 설정
- OpenAI 호환 API 서버 시작

### API 테스트

```bash
python -m tests.test_api --url http://localhost:8000
```

### 주요 엔드포인트

- `GET /v1/models`: 사용 가능한 모델 목록
- `POST /v1/chat/completions`: 채팅 완료 API

## OpenAI 호환 API 예제

### 텍스트 생성

```python
import requests

api_url = "http://localhost:8000"
headers = {"Content-Type": "application/json"}

payload = {
    "model": "qwen2.5-vl-7B-mlx",
    "messages": [
        {"role": "user", "content": "안녕하세요! 오늘 날씨는 어떤가요?"}
    ],
    "temperature": 0.7,
    "max_tokens": 100
}

response = requests.post(f"{api_url}/v1/chat/completions", 
                        headers=headers, 
                        json=payload)
print(response.json())
```

### 이미지-텍스트 생성

```python
import requests
import base64

def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

api_url = "http://localhost:8000"
image_path = "tests/test_images/test.png"
base64_image = encode_image(image_path)

payload = {
    "model": "qwen2.5-vl-7B-mlx",
    "messages": [
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "이 이미지에 대해 설명해 주세요."
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/png;base64,{base64_image}"
                    }
                }
            ]
        }
    ],
    "temperature": 0.7,
    "max_tokens": 150
}

response = requests.post(f"{api_url}/v1/chat/completions", 
                        headers={"Content-Type": "application/json"}, 
                        json=payload)
print(response.json())
```

또는 제공된 스크립트를 사용하여 이미지 요청 JSON을 생성할 수 있습니다:

```bash
# 이미지 요청 JSON 생성
python data/sample_requests/encode_image.py

# 생성된 JSON으로 API 요청
curl -X POST "http://localhost:8000/v1/chat/completions" \
     -H "Content-Type: application/json" \
     -d @data/sample_requests/image_request.json
```

## Open Web UI 연결

Open Web UI 연결 방법은 [연결 가이드](docs/connect_to_openwebui.md)를 참조하세요.

## 라이센스

이 프로젝트는 [MIT 라이센스](LICENSE)에 따라 배포됩니다.

## 참고 자료

- [Qwen2.5-VL 모델](https://huggingface.co/Qwen/Qwen2.5-VL)
- [MLX 프레임워크](https://github.com/ml-explore/mlx)
- [MLX-Examples](https://github.com/ml-explore/mlx-examples) 