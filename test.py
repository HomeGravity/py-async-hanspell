from async_hanspell.spell_checker import *
import asyncio

async def main1():
    SpellChecker = AsyncSpellChecker()
    tasks = [
        SpellChecker.spell_check(
            text="안녕 하세요. 저는 한국인 입니다. 이문장은 한글로 작성됬습니다.", 
            async_delay=2
        ),
        
        SpellChecker.spell_check(
            text="안녕 하세요. 저는 한국인 입니다. 이문장은 한글로 작성됬습니다.", 
            async_delay=2
        )
    ]

    # 비동기 작업을 병렬로 실행하고 완료된 순서대로 결과를 처리
    for completed in asyncio.as_completed(tasks):
        result = await completed
        if result is not None:
            await SpellChecker.spell_check_output(result)

    # 세션 종료
    await SpellChecker.close()


async def main2():
    SpellChecker = AsyncSpellChecker()
    
    word1 = await SpellChecker.spell_check(
            text=["안녕 하세요. 저는 한국인 입니다. 이문장은 한글로 작성됬습니다." *50, "안녕"],
            async_delay=2
    )

    word2 = await SpellChecker.spell_check(
            text="안녕 하세요. 저는 한국인 입니다. 이문장은 한글로 작성됬습니다.", 
            async_delay=2
    )

    word3 = await SpellChecker.spell_check(
            text="안녕 하세요. 저는 한국인 입니다. 이문장은 한글로 작성됬습니다.", 
            async_delay=2
    )
    
    for word in [word1, word2, word3]:
        if word is not None:
            await SpellChecker.spell_check_output(word)

    # 세션 종료
    await SpellChecker.close()

# 비동기 이벤트 루프 실행
if __name__ == '__main__':
    # asyncio.run(main())
    asyncio.run(main2())