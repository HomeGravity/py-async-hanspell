from headers import *
import aiohttp
import asyncio
import re
from pprint import pprint
from cachetools import TTLCache
from urllib import parse


# 토큰 요청을 줄이기 위해 캐시로 저장합니다.
cache = TTLCache(maxsize=10, ttl=3600)

class AsyncSpellChecker:
    def __init__(self) -> None:
        # 매개 변수 정의
        self.token_url = token_url
        self.spell_checker_url = spell_checker_url
        self.token_requests_headers = token_requests_headers
        self.spell_checker_requests_headers = spell_checker_requests_headers
        
        self.token = None
        
        # 세션 생성
        self.session = aiohttp.ClientSession()
        
    # 토큰을 생성합니다.
    async def _create_token(self):
        self.token = await self._get_token()
    
    async def _read_token(self):
        # 토큰이 있는경우 > 계속 사용
        try:
            self.token = cache.get('PASSPORT_TOKEN')
            
        # 토큰이 없는경우 > 새로 생성
        except KeyError:
            self.token = await self._get_token()
    
    
    # 토큰 생성을 요청합니다.
    async def _get_token(self):
        # 토큰 요청
        async with self.session.get(self.token_url, headers=self.token_requests_headers) as response:
            response.raise_for_status()  # 상태 코드가 200이 아닐 경우 예외 발생
            token_text = await response.text()
            
            # 토큰 업데이트
            return await self._token_update(token_text)
    
    # 받은 토큰 텍스트를 Parse (구문 분석) 합니다.
    async def _token_update(self, token):
            match = re.search('passportKey=([a-zA-Z0-9]+)', token)
            if match is not None:
                # parse.unquote는 URL 디코딩 함수입니다.
                token_update  = parse.unquote(match.group(1))
                cache['PASSPORT_TOKEN'] = token_update
                
            return token_update 


    # 맞춤법 검사기 요청 함수입니다.
    async def _get_response(self, text):
        spell_checker_payload.update({
            "passportKey" : self.token,
            "q": text
        })
        
        
        # 맞춤법 검사기에 텍스트 교정 요청을 보냅니다.
        async with self.session.get(self.spell_checker_url, headers=self.spell_checker_requests_headers, params=spell_checker_payload) as response:
            response.raise_for_status()  # 상태 코드가 200이 아닐 경우 예외 발생
            
            return await response.json()

    async def _initialize_token(self):
        # 토큰을 생성합니다.
        await self._create_token() if self.token is None else await self._read_token() # 토큰을 불러옵니다.
    
    # 매개변수로 받은 텍스트를 맞춤법 검사를 진행합니다.
    async def spell_check(self, text, delay):
        # 리스트나 튜플을 texts 변수에 할당, 단일 텍스트를 리스트로 변환
        texts = text if isinstance(text, (list, tuple)) else [text]
        await self._initialize_token()  # 토큰 초기화
        
        spell_checked_list = []  # 교정된 텍스트를 저장할 리스트
        
        # 각 텍스트에 대해 토큰 초기화 및 응답 가져오기
        for txt in texts:
            await self._initialize_token()  # 각 텍스트에 대해 토큰 초기화
            spell_checked_list.append(await self._get_response(txt))  # 응답 가져와서 저장
            print(f"{delay}초 대기")
            await asyncio.sleep(delay)  # 2초 대기
            
        return spell_checked_list
        
    # 세션 종료.
    async def close(self):
        await self.session.close()
            


async def main():
    test = AsyncSpellChecker()
    # test1 = await test.spell_check("안녕하세요.", 2)
    # test2 = await test.spell_check(["안녕하세요", "저는"], 1)
    # test3 = await test.spell_check("아니", 3)
    
    # spell_check를 병렬로 실행
    test1, test2, test3 = await asyncio.gather(
        test.spell_check("안녕하세요.", 2),
        test.spell_check(["안녕하세요", "저는"], 2),
        test.spell_check("아니", 3)
    )
    
    
    for x in [test1, test2, test3]:
        for y in x:
            print(y)

    await test.close()
    
# 비동기 이벤트 루프 실행
if __name__ == '__main__':
    asyncio.run(main())