#!/bin/bash

# Qwen2.5-VL API 서버 시작 스크립트
# 필요한 환경 변수:
# - MODEL_DIR: 모델 디렉토리 경로
# - MODEL_ID: 사용할 모델 ID (선택적)

# 작업 디렉토리 설정 - 심볼릭 링크 처리를 위한 개선된 방법
REAL_SOURCE="${BASH_SOURCE[0]}"
while [ -L "$REAL_SOURCE" ]; do
    REAL_DIR="$(cd -P "$(dirname "$REAL_SOURCE")" && pwd)"
    REAL_SOURCE="$(readlink "$REAL_SOURCE")"
    [[ $REAL_SOURCE != /* ]] && REAL_SOURCE="$REAL_DIR/$REAL_SOURCE"
done
SCRIPT_DIR="$(cd -P "$(dirname "$REAL_SOURCE")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_ROOT" || exit 1

echo "스크립트 디렉토리: $SCRIPT_DIR"
echo "프로젝트 루트: $PROJECT_ROOT"

# 환경 변수 및 디렉토리 설정
MODELS_DIR="${MODEL_DIR:-$PROJECT_ROOT/models}"
LOGS_DIR="$PROJECT_ROOT/logs"
API_LOG_FILE="$LOGS_DIR/api_server.log"
DEFAULT_PORT=8000

# 로그 디렉토리 생성
mkdir -p "$LOGS_DIR"

# 오류 처리 함수
handle_error() {
    echo "오류: $1"
    exit 1
}

# 가상환경 활성화 함수
activate_venv() {
    if [ -d "$PROJECT_ROOT/venv" ]; then
        echo "가상환경 활성화: $PROJECT_ROOT/venv"
        source "$PROJECT_ROOT/venv/bin/activate" || handle_error "가상환경 활성화 실패"
    else
        handle_error "가상환경이 존재하지 않습니다. setup.sh 스크립트를 먼저 실행하세요."
    fi
}

# 환경 정보 출력
print_env_info() {
    echo "====== 환경 정보 ======"
    echo "Python 버전: $(python --version 2>&1)"
    echo "작업 디렉토리: $(pwd)"
    echo "모델 디렉토리: $MODELS_DIR"
    
    # 설치된 패키지 확인
    echo "====== 설치된 주요 패키지 ======"
    pip list | grep -E "mlx|transformers|fastapi|uvicorn" || echo "패키지 정보를 가져올 수 없습니다."
    echo "========================"
}

# MLX 모델 확인 및 선택
check_models() {
    echo "MLX 모델 확인 중..."
    
    if [ ! -d "$MODELS_DIR" ]; then
        handle_error "모델 디렉토리가 존재하지 않습니다: $MODELS_DIR"
    fi
    
    # 먼저 mlx_models 디렉토리 체크
    MLX_MODELS_DIR="$MODELS_DIR/mlx_models"
    if [ -d "$MLX_MODELS_DIR" ]; then
        echo "MLX 모델 디렉토리 발견됨: $MLX_MODELS_DIR"
        # mlx_models 디렉토리 내의 모델 검색
        MLX_MODELS=$(find "$MLX_MODELS_DIR" -maxdepth 1 -type d | grep -v "^$MLX_MODELS_DIR$" | xargs -n1 basename | sort)
    else
        echo "mlx_models 디렉토리를 찾을 수 없습니다. 모델 디렉토리에서 직접 검색합니다."
        # 기존 방식으로 검색
        MLX_MODELS=$(find "$MODELS_DIR" -maxdepth 1 -type d -name "*-mlx" | xargs -n1 basename | sort)
    fi
    
    echo "찾은 모델 목록: $MLX_MODELS"
    
    if [ -z "$MLX_MODELS" ]; then
        handle_error "MLX 모델을 찾을 수 없습니다. convert_to_mlx.sh 스크립트를 먼저 실행하세요."
    fi
    
    # 모델 선택 또는 환경 변수 사용
    if [ -n "$MODEL_ID" ]; then
        echo "환경 변수에서 모델 ID를 가져왔습니다: $MODEL_ID"
        if [ -d "$MLX_MODELS_DIR/$MODEL_ID" ]; then
            MODEL_PATH="$MLX_MODELS_DIR/$MODEL_ID"
        elif [ -d "$MODELS_DIR/$MODEL_ID" ]; then
            MODEL_PATH="$MODELS_DIR/$MODEL_ID"
        else
            echo "경고: 지정된 모델이 존재하지 않습니다. 사용 가능한 모델 중에서 선택합니다."
            MODEL_ID=""
            MODEL_PATH=""
        fi
    fi
    
    if [ -z "$MODEL_ID" ]; then
        echo "사용 가능한 MLX 모델:"
        PS3="모델을 선택하세요 (번호): "
        select MODEL_ID in $MLX_MODELS; do
            if [ -n "$MODEL_ID" ]; then
                break
            else
                echo "유효하지 않은 선택입니다. 다시 시도하세요."
            fi
        done
        
        # 선택된 모델 경로 설정
        if [ -d "$MLX_MODELS_DIR/$MODEL_ID" ]; then
            MODEL_PATH="$MLX_MODELS_DIR/$MODEL_ID"
        else
            MODEL_PATH="$MODELS_DIR/$MODEL_ID"
        fi
    fi
    
    echo "선택된 모델: $MODEL_ID"
    echo "모델 경로: $MODEL_PATH"
    
    # 모델 파일 확인
    if [ ! -f "$MODEL_PATH/tokenizer.json" ] || [ ! -f "$MODEL_PATH/config.json" ]; then
        handle_error "선택한 모델이 유효하지 않습니다. 필요한 파일이 누락되었습니다."
    fi
}

# 포트 설정
set_port() {
    read -p "API 서버 포트 (기본값: $DEFAULT_PORT): " PORT
    PORT=${PORT:-$DEFAULT_PORT}
    
    if ! [[ "$PORT" =~ ^[0-9]+$ ]] || [ "$PORT" -lt 1 ] || [ "$PORT" -gt 65535 ]; then
        echo "경고: 유효하지 않은 포트 번호입니다. 기본 포트 $DEFAULT_PORT를 사용합니다."
        PORT=$DEFAULT_PORT
    fi
    
    echo "설정된 포트: $PORT"
}

# 메인 실행 로직
main() {
    echo "====== Qwen-VL API 서버 시작 ======"
    
    # 가상환경 활성화
    activate_venv
    
    # 환경 정보 출력
    print_env_info
    
    # 모델 확인 및 선택
    check_models
    
    # 포트 설정
    set_port
    
    # API 서버 시작
    echo "Qwen-VL API 서버를 시작합니다..."
    echo "로그 파일: $API_LOG_FILE"
    echo "모델: $MODEL_ID"
    echo "모델 경로: $MODEL_PATH"
    echo "포트: $PORT"
    echo "서버를 중지하려면 Ctrl+C를 누르세요."
    
    # 환경 변수로 모델 ID와 디렉토리 설정
    export MODEL_DIR="$MODELS_DIR"
    export MODEL_ID="$MODEL_ID"
    
    # API 서버 실행
    PYTHONPATH="$PROJECT_ROOT" python -m app.api.server \
        --model-dir "$MODELS_DIR" \
        --model-id "$MODEL_ID" \
        --port "$PORT" \
        2>&1 | tee -a "$API_LOG_FILE"
    
    echo "API 서버가 종료되었습니다."
    
    # Open Web UI 연결 정보
    echo "====== API 서버 연결 정보 ======"
    echo "API 서버 URL: http://localhost:$PORT"
    echo "Open Web UI 연결:"
    echo "1. Open Web UI에서 'Admin -> Models -> New Model'"
    echo "2. 이름: Qwen-VL"
    echo "3. Base URL: http://localhost:$PORT"
    echo "4. Api Key: 공백으로 둠"
    echo "5. 저장 후 사용"
}

# 스크립트 실행
main 