from fastapi import HTTPException, status


ADMIN_ROLES = {"admin", "super admin"}


def get_user_role(current_user) -> str:
    return (
        current_user.user_role.name.strip().lower()
        if current_user and current_user.user_role
        else ""
    )


def is_super_admin(current_user) -> bool:
    return get_user_role(current_user) == "super admin" and current_user.account_id is None


def is_account_admin(current_user) -> bool:
    return get_user_role(current_user) == "admin" and current_user.account_id is not None


def has_permission(current_user, permission_code: str) -> bool:
    if is_super_admin(current_user) or is_account_admin(current_user):
        return True
    role = getattr(current_user, "user_role", None)
    if not role or current_user.account_id is None or role.account_id != current_user.account_id:
        return False
    return any(permission.code == permission_code for permission in role.permissions)


def check_permission(current_user, permission_code: str) -> None:
    if not has_permission(current_user, permission_code):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Permission denied. Required permission: {permission_code}",
        )


def check_super_admin(current_user) -> None:
    if not is_super_admin(current_user):
        raise HTTPException(status_code=403, detail="Platform Super Admin access required.")


def check_user_role(current_user) -> None:
    if not (is_super_admin(current_user) or is_account_admin(current_user)):
        raise HTTPException(status_code=403, detail="Account Admin access required.")


def check_user_access(current_user, target_user) -> None:
    if current_user.id == target_user.id or is_super_admin(current_user):
        return
    if current_user.account_id is not None and current_user.account_id == target_user.account_id:
        check_permission(current_user, "users.view")
        return
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Permission denied. You cannot access users outside your account.",
    )
