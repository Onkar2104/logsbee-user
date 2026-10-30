from fastapi import HTTPException, status


ADMIN_ROLES = {"admin", "super admin"}


def get_user_role(current_user) -> str:
    return (
        current_user.user_role.name.strip().lower()
        if current_user.user_role
        else ""
    )


def check_user_role(current_user):

    if get_user_role(current_user) not in ADMIN_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission denied. Admin access required.",
        )


def check_user_access(current_user, requested_user_id):

    is_same_user = current_user.id == requested_user_id
    is_admin = get_user_role(current_user) in ADMIN_ROLES

    if not is_same_user and not is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission denied.",
        )