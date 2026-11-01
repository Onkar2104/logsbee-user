from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from controllers.account_controller import AccountController
from core.auth_dependencies import get_current_user
from core.database import get_db
from schemas.account_schema import AccountCreate, AccountCreatedResponse

router = APIRouter(prefix="/api/accounts", tags=["Accounts"])


@router.post(
    "/",
    response_model=AccountCreatedResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_account(
    data: AccountCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return AccountController.create_account(db, data, current_user)
