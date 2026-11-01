from fastapi import HTTPException, status


ADMIN_ROLES = {"admin", "super admin"}


def get_user_role(current_user) -> str:
    return (
        current_user.user_role.name.strip().lower()
        if current_user and current_user.user_role
        else ""
    )


def is_super_admin(current_user) -> bool:
    return get_user_role(current_user) == "super admin"


def is_account_admin(current_user) -> bool:
    return (
        get_user_role(current_user) == "admin"
        and current_user.account_id is not None
    )


def check_super_admin(current_user) -> None:
    if not is_super_admin(current_user) or current_user.account_id is not None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Platform Super Admin access required.",
        )


def check_user_role(current_user) -> None:
    if not (is_super_admin(current_user) or is_account_admin(current_user)):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission denied. Account Admin access required.",
        )


def check_user_access(current_user, target_user) -> None:
    if current_user.id == target_user.id:
        return

    if is_super_admin(current_user):
        return

    if (
        is_account_admin(current_user)
        and current_user.account_id == target_user.account_id
    ):
        return

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Permission denied. You cannot access users outside your account.",
    )
