from database.requests import get_user


async def admin_check(tg_id: int) -> bool:
    if (await get_user(tg_id)).user_status == 3:
        return True
    else:
        return False


async def manager_check(tg_id: int) -> bool:
    if (await get_user(tg_id)).user_status > 1:
        return True
    else:
        return False


async def user_check(tg_id: int) -> bool:
    if (await get_user(tg_id)).user_status > 0:
        return True
    else:
        return False
