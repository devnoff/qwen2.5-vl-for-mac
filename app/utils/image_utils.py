#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import base64
import requests
import logging
from io import BytesIO
from PIL import Image
import numpy as np

logger = logging.getLogger(__name__)

def decode_base64_image(base64_string):
    """
    Base64 인코딩된 이미지 문자열을 PIL Image 객체로 변환합니다.
    
    Args:
        base64_string (str): Base64 인코딩된 이미지 문자열
        
    Returns:
        PIL.Image: 디코딩된 이미지 객체
    """
    try:
        # Base64 접두사 제거 (있는 경우)
        if "base64," in base64_string:
            base64_string = base64_string.split("base64,")[1]
        
        # 이미지 디코딩
        image_data = base64.b64decode(base64_string)
        image = Image.open(BytesIO(image_data))
        return image
    except Exception as e:
        logger.error(f"Base64 이미지 디코딩 중 오류 발생: {e}")
        return None

def load_image_from_url(image_url):
    """
    URL에서 이미지를 다운로드하여 PIL Image 객체로 변환합니다.
    
    Args:
        image_url (str): 이미지 URL
        
    Returns:
        PIL.Image: 다운로드된 이미지 객체
    """
    try:
        response = requests.get(image_url, stream=True, timeout=10)
        response.raise_for_status()
        image = Image.open(BytesIO(response.content))
        return image
    except Exception as e:
        logger.error(f"URL에서 이미지 로드 중 오류 발생: {e}")
        return None

def process_image_from_data_url(data_url):
    """
    데이터 URL에서 이미지를 처리합니다.
    
    Args:
        data_url (str): 데이터 URL (base64 인코딩 등)
        
    Returns:
        PIL.Image: 처리된 이미지 객체
    """
    try:
        # 데이터 URL 형식 확인
        if data_url.startswith("data:"):
            # Base64 인코딩된  이미지인 경우
            return decode_base64_image(data_url)
        elif data_url.startswith(("http://", "https://")):
            # 웹 URL인 경우
            return load_image_from_url(data_url)
        else:
            # 로컬 파일 경로인 경우
            if os.path.exists(data_url):
                return Image.open(data_url)
            else:
                logger.error(f"이미지 파일이 존재하지 않습니다: {data_url}")
                return None
    except Exception as e:
        logger.error(f"이미지 처리 중 오류 발생: {e}")
        return None

def create_empty_image(width=512, height=512, color=(200, 200, 200)):
    """
    지정된 크기와 색상의 빈 이미지를 생성합니다.
    
    Args:
        width (int): 이미지 너비
        height (int): 이미지 높이
        color (tuple): RGB 색상 튜플
        
    Returns:
        PIL.Image: 생성된 빈 이미지
    """
    return Image.new("RGB", (width, height), color) 