from fastapi import FastAPI

from database import engine
from models.base import Base
from routers.user_router import router as user_router
from models.otp_verification_model import VerificationOTP
from models.password_reset_otp_model import PasswordResetOTP
from routers.verification_router import router as verification_router
from routers.forgot_password_router import router as forgot_password_router
from core.role_seed import seed_roles

app = FastAPI(title="User Management API")

Base.metadata.create_all(bind=engine)

seed_roles()

app.include_router(user_router)
app.include_router(verification_router)
app.include_router(forgot_password_router)

@app.get("/health")
def health_check():
    return {"status": "healthy"}
