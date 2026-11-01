from fastapi import FastAPI

from core.database import engine
from models.base import Base
# Import every model before create_all so SQLAlchemy registers its table.
from models.account_model import Account
from models.user_model import User
from models.user_role_model import UserRole
from models.otp_verification_model import VerificationOTP
from models.password_reset_otp_model import PasswordResetOTP

from routers.user_router import router as user_router
from routers.account_router import router as account_router
from routers.verification_router import router as verification_router
from routers.forgot_password_router import router as forgot_password_router
from routers.auth_router import router as auth_router
from core.role_seed import seed_roles
from core.limiter import limiter

from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded


app = FastAPI(title="User Management API")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# For a new database this creates the schema. Existing databases must first
# run the SQL migration in migrations/001_account_multi_tenancy_mysql.sql.
Base.metadata.create_all(bind=engine)
seed_roles()

app.include_router(account_router)
app.include_router(user_router)
app.include_router(verification_router)
app.include_router(forgot_password_router)
app.include_router(auth_router)


@app.get("/health")
def health_check():
    return {"status": "healthy"}
