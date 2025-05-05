#!/usr/bin/env python
# -*- coding: utf-8 -*-

from typing import List, Optional, Union, Dict, Any, Literal
from pydantic import BaseModel, Field

class ChatMessage(BaseModel):
    """
    채팅 메시지 모델
    
    OpenAI API 형식과 호환되는 채팅 메시지 클래스입니다.
    텍스트 또는 이미지 URL을 포함할 수 있습니다.
    """
    role: str
    content: Union[str, List[Dict[str, Any]]]

class ImageContent(BaseModel):
    """
    이미지 콘텐츠 모델
    
    이미지 URL을 포함하는 콘텐츠 클래스입니다.
    """
    url: str

class ImageUrl(BaseModel):
    """
    이미지 URL 모델
    
    이미지 URL을 나타내는 클래스입니다.
    """
    image_url: ImageContent

class TextContent(BaseModel):
    """
    텍스트 콘텐츠 모델
    
    텍스트를 나타내는 콘텐츠 클래스입니다.
    """
    text: str
    type: str = "text"

class MessageContent(BaseModel):
    """
    메시지 콘텐츠 모델
    
    이미지 URL 또는 텍스트를 포함할 수 있는 메시지 콘텐츠 클래스입니다.
    """
    type: str
    text: Optional[str] = None
    image_url: Optional[Dict[str, str]] = None

class ChatCompletionRequest(BaseModel):
    """
    채팅 완료 요청 모델
    
    OpenAI API 형식과 호환되는 채팅 완료 요청 클래스입니다.
    모델 ID, 메시지 목록, 온도, 최대 토큰 수 등을 포함합니다.
    """
    model: str
    messages: List[Union[ChatMessage, Dict[str, Any]]]
    temperature: Optional[float] = 0.7
    top_p: Optional[float] = 0.95
    n: Optional[int] = 1
    max_tokens: Optional[int] = 800
    stop: Optional[Union[str, List[str]]] = None
    presence_penalty: Optional[float] = 0.0
    frequency_penalty: Optional[float] = 0.0
    user: Optional[str] = None
    stream: Optional[bool] = False

class ChatCompletionResponseChoice(BaseModel):
    """
    채팅 완료 응답 선택 모델
    
    OpenAI API 형식과 호환되는 채팅 완료 응답 선택 클래스입니다.
    생성된 메시지와 종료 이유를 포함합니다.
    """
    index: int
    message: ChatMessage
    finish_reason: str = "stop"

class ChatCompletionResponse(BaseModel):
    """
    채팅 완료 응답 모델
    
    OpenAI API 형식과 호환되는 채팅 완료 응답 클래스입니다.
    생성된 텍스트 선택지와 사용량 정보를 포함합니다.
    """
    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: List[ChatCompletionResponseChoice]
    usage: Dict[str, int]

class ModelList(BaseModel):
    """
    모델 목록 응답 모델
    
    OpenAI API 형식과 호환되는 모델 목록 응답 클래스입니다.
    """
    object: str = "list"
    data: List[Dict[str, Any]] 