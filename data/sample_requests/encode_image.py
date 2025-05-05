#!/usr/bin/env python
import base64
import json
import os

# 프로젝트 루트 디렉토리 설정
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))

# 이미지 경로 설정
image_path = os.path.join(PROJECT_ROOT, "tests", "test_images", "test.png")

# 이미지를 base64로 인코딩
with open(image_path, "rb") as image_file:
    encoded_string = base64.b64encode(image_file.read()).decode('utf-8')

# API 요청 준비
request_data = {
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
                        "url": f"data:image/png;base64,{encoded_string}"
                    }
                }
            ]
        }
    ],
    "temperature": 0.7,
    "max_tokens": 150
}

# 현재 스크립트가 있는 디렉토리에 결과 파일 생성
output_file = os.path.join(os.path.dirname(__file__), "image_request.json")
with open(output_file, "w") as f:
    json.dump(request_data, f, indent=2)

print(f"이미지 요청 JSON 파일이 생성되었습니다: {output_file}") 