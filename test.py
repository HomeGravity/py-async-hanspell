from async_hanspell.spell_checker import *
import asyncio
import time

async def main1():
    SpellChecker = AsyncSpellChecker()
    await SpellChecker.initialize_token() # 토큰 초기화 메소드 입니다. 반드시 호출해야합니다.
    
    tasks = [
        SpellChecker.spell_check(
            text="안녕 하세요. 저는 한국인 입니다. 이문장은 한글로 작성됬습니다.", 
            async_delay=2,
            is_output = True
        ),

    ]

    start_time = time.time()
    
    # asyncio.gather를 사용하여 모든 작업을 동시에 실행
    results = await asyncio.gather(*tasks)
    
    # # 결과 출력
    # for result in results:
    #     print(result)
        
    print(f"\n\n소요 시간: {time.time() - start_time:.4f}초")



    # 세션 종료
    await SpellChecker.close()

async def main2():
    SpellChecker = AsyncSpellChecker()
    await SpellChecker.initialize_token() # 토큰 초기화 메소드 입니다. 반드시 호출해야합니다.
    start_time = time.time()
    word1 = await SpellChecker.spell_check(
            text= ["이것인 신입니다."*5000, "안녕 하세요. 저는 한국인 입니다. 이문장은 한글로 작성됬습니다"],
            async_delay=0,
            is_output = True
    )
    print(word1)
    print(f"\n\n소요 시간: {time.time() - start_time:.4f}초")
    
    # start_time = time.time()
    # for txt in ["이것은 비동기 마춤범 검사기 테스트 문장 임니다.", "안녕 하세요. 저는 한국인 입니다. 이문장은 한글로 작성됬습니다"]:
    #     word2 = await SpellChecker.spell_check(
    #             text=txt,
    #             async_delay=0,
    #             is_output=True
    #     )
        
    #     print(word2)
    # print(f"\n\n소요 시간: {time.time() - start_time:.4f}초")
    
    # 세션 종료
    await SpellChecker.close()



# 비동기 이벤트 루프 실행
if __name__ == '__main__':
    asyncio.run(main1())
    # asyncio.run(main2())