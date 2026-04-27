import hashlib
import hmac
import os
import secrets
from typing import Any

import mysql.connector
from fastapi import APIRouter, Cookie, HTTPException, Response
from pydantic import BaseModel

router = APIRouter(tags=["auth"])

SESSION_COOKIE_NAME = "infosearch_session"
SESSION_COOKIE_SECURE = os.getenv("SESSION_COOKIE_SECURE", "false").strip().lower() in {"1", "true", "yes", "on"}
SESSION_COOKIE_SAMESITE = os.getenv("SESSION_COOKIE_SAMESITE", "lax").strip().lower()
SESSION_MAX_AGE = int(os.getenv("SESSION_MAX_AGE", "604800"))


class LoginRequest(BaseModel):
    username: str
    password: str


class UserResponse(BaseModel):
    id: int
    username: str
    display_name: str | None = None
    role: str
    is_admin: bool


class LoginResponse(BaseModel):
    user: UserResponse



def _db_config() -> dict[str, Any]:
    return {
        "host": os.getenv("MYSQL_HOST", "mysql"),
        "port": int(os.getenv("MYSQL_PORT", "3306")),
        "database": os.getenv("MYSQL_DATABASE", "InfoSearch"),
        "user": os.getenv("MYSQL_USER", "user"),
        "password": os.getenv("MYSQL_PASSWORD", "pass"),
    }



def _hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()



def _verify_password(password: str, password_hash: str) -> bool:
    return hmac.compare_digest(_hash_password(password), password_hash)



def _build_user_response(row: dict[str, Any]) -> UserResponse:
    return UserResponse(
        id=int(row["id"]),
        username=row["username"],
        display_name=row.get("display_name"),
        role=row["role"],
        is_admin=row["role"] == "admin",
    )



def get_current_user_from_token(session_token: str | None) -> UserResponse:
    if not session_token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    conn = mysql.connector.connect(**_db_config())
    try:
        with conn.cursor(dictionary=True) as cursor:
            cursor.execute(
                """
                SELECT u.id, u.role, u.display_name, lu.username
                FROM tblLocalSessions s
                JOIN tblLocalUsers lu ON lu.id = s.local_user_id
                JOIN tblUsers u ON u.id = lu.user_id
                WHERE s.session_token = %s AND s.expires_at > UTC_TIMESTAMP()
                """,
                (session_token,),
            )
            row = cursor.fetchone()
            if not row:
                raise HTTPException(status_code=401, detail="Not authenticated")
            return _build_user_response(row)
    finally:
        conn.close()


@router.post("/auth/login", response_model=LoginResponse)
def login(payload: LoginRequest, response: Response) -> LoginResponse:
    conn = mysql.connector.connect(**_db_config())
    try:
        with conn.cursor(dictionary=True) as cursor:
            cursor.execute(
                """
                SELECT lu.id, lu.username, lu.password_hash, u.id AS user_id, u.role, u.display_name
                FROM tblLocalUsers lu
                JOIN tblUsers u ON u.id = lu.user_id
                WHERE lu.username = %s AND lu.is_active = 1
                """,
                (payload.username,),
            )
            row = cursor.fetchone()
            if not row or not _verify_password(payload.password, row["password_hash"]):
                raise HTTPException(status_code=401, detail="Ongeldige gebruikersnaam of wachtwoord")

            session_token = secrets.token_urlsafe(32)
            cursor.execute(
                """
                INSERT INTO tblLocalSessions (local_user_id, session_token, expires_at)
                VALUES (%s, %s, DATE_ADD(UTC_TIMESTAMP(), INTERVAL %s SECOND))
                """,
                (row["id"], session_token, SESSION_MAX_AGE),
            )
            conn.commit()

        response.set_cookie(
            key=SESSION_COOKIE_NAME,
            value=session_token,
            httponly=True,
            secure=SESSION_COOKIE_SECURE,
            samesite=SESSION_COOKIE_SAMESITE,
            max_age=SESSION_MAX_AGE,
            path="/",
        )

        user = _build_user_response(
            {
                "id": row["user_id"],
                "username": row["username"],
                "display_name": row.get("display_name"),
                "role": row["role"],
            }
        )
        return LoginResponse(user=user)
    finally:
        conn.close()


@router.post("/auth/logout")
def logout(response: Response, infosearch_session: str | None = Cookie(default=None)) -> dict[str, str]:
    if infosearch_session:
        conn = mysql.connector.connect(**_db_config())
        try:
            with conn.cursor() as cursor:
                cursor.execute("DELETE FROM tblLocalSessions WHERE session_token = %s", (infosearch_session,))
                conn.commit()
        finally:
            conn.close()

    response.delete_cookie(key=SESSION_COOKIE_NAME, path="/")
    return {"status": "ok"}


@router.get("/auth/me", response_model=UserResponse)
def auth_me(infosearch_session: str | None = Cookie(default=None)) -> UserResponse:
    return get_current_user_from_token(infosearch_session)
