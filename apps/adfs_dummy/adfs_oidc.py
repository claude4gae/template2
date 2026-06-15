"""OIDC/ADFS 더미 엔드포인트입니다."""

from __future__ import annotations

import hashlib
import html
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any, Dict

import jwt
from fastapi import APIRouter, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from adfs_settings import (
    AUTO_SIGN_IN,
    CLIENT_ID,
    DEFAULT_BUSNAME,
    DEFAULT_DEPT,
    DEFAULT_DEPTID,
    DEFAULT_EMAIL,
    DEFAULT_EMPLOYEETYPE,
    DEFAULT_GIVENNAME,
    DEFAULT_GRDNAME,
    DEFAULT_GRDNAME_EN,
    DEFAULT_INTCODE,
    DEFAULT_INTNAME,
    DEFAULT_LOGINID,
    DEFAULT_NAME,
    DEFAULT_ORIGINCOMP,
    DEFAULT_SABUN,
    DEFAULT_SURNAME,
    DEFAULT_USERNAME_EN,
    ISSUER,
    LOGOUT_REDIRECT,
    PRIVATE_KEY,
)

router = APIRouter()


def render_login_form(request: Request) -> str:
    params = request.query_params
    email = html.escape(params.get("email") or DEFAULT_EMAIL)
    name = html.escape(params.get("name") or DEFAULT_NAME)
    loginid = html.escape(params.get("loginid") or DEFAULT_LOGINID)
    sabun = html.escape(params.get("sabun") or DEFAULT_SABUN)
    deptname = html.escape(params.get("deptname") or DEFAULT_DEPT)
    deptid = html.escape(params.get("deptid") or DEFAULT_DEPTID)

    username_en = html.escape(params.get("username_en") or DEFAULT_USERNAME_EN)
    surname = html.escape(params.get("surname") or DEFAULT_SURNAME)
    givenname = html.escape(params.get("givenname") or DEFAULT_GIVENNAME)
    grd_name = html.escape(params.get("grdName") or DEFAULT_GRDNAME)
    grdname_en = html.escape(params.get("grdname_en") or DEFAULT_GRDNAME_EN)
    busname = html.escape(params.get("busname") or DEFAULT_BUSNAME)
    intcode = html.escape(params.get("intcode") or DEFAULT_INTCODE)
    intname = html.escape(params.get("intname") or DEFAULT_INTNAME)
    origincomp = html.escape(params.get("origincomp") or DEFAULT_ORIGINCOMP)
    employeetype = html.escape(params.get("employeetype") or DEFAULT_EMPLOYEETYPE)
    state = html.escape(params.get("state") or "")
    nonce = html.escape(params.get("nonce") or secrets.token_urlsafe(16))
    redirect_uri = html.escape(params.get("redirect_uri") or "")
    client_id = html.escape(params.get("client_id") or "")

    return f"""
    <html>
      <head>
        <title>Dummy ADFS Login</title>
        <style>
          body {{ font-family: sans-serif; padding: 2rem; background: #f5f5f5; }}
          form {{ max-width: 440px; margin: auto; padding: 1.5rem; background: white; border-radius: 12px; box-shadow: 0 10px 30px rgba(0,0,0,0.08); }}
          label {{ display: block; font-weight: 600; margin-bottom: 0.25rem; }}
          input {{ width: 100%; padding: 0.5rem; margin-bottom: 1rem; border-radius: 8px; border: 1px solid #d4d4d8; }}
          button {{ width: 100%; padding: 0.75rem; background: #2563eb; color: white; font-weight: 600; border: none; border-radius: 8px; cursor: pointer; }}
          button:hover {{ background: #1d4ed8; }}
          .hint {{ margin-top: 1rem; font-size: 0.85rem; color: #4b5563; text-align: center; }}
          details {{ margin-bottom: 1rem; }}
          summary {{ font-weight: 600; margin-bottom: 0.75rem; cursor: pointer; }}
        </style>
      </head>
      <body>
        <form method="post" action="/authorize">
          <h1>Dummy ADFS</h1>
          <p class="hint">입력값을 조정한 뒤 "Sign in"을 누르면 콜백으로 리다이렉트합니다.</p>
          <label for="email">Email</label>
          <input id="email" name="email" value="{email}" type="email" required />
          <label for="loginid">Login ID (loginid / KNOX ID)</label>
          <input id="loginid" name="loginid" value="{loginid}" type="text" required />
          <label for="sabun">Sabun (사번)</label>
          <input id="sabun" name="sabun" value="{sabun}" type="text" required />
          <label for="name">Username (한글 이름)</label>
          <input id="name" name="name" value="{name}" type="text" required />
          <label for="deptname">Dept name (deptname)</label>
          <input id="deptname" name="deptname" value="{deptname}" type="text" />
          <label for="deptid">Dept ID (deptid)</label>
          <input id="deptid" name="deptid" value="{deptid}" type="text" />

          <details>
            <summary>More claims (optional)</summary>
            <label for="surname">Surname (EN)</label>
            <input id="surname" name="surname" value="{surname}" type="text" />
            <label for="givenname">Given name (EN)</label>
            <input id="givenname" name="givenname" value="{givenname}" type="text" />
            <label for="username_en">Username (EN)</label>
            <input id="username_en" name="username_en" value="{username_en}" type="text" />
            <label for="grdName">Grade (grdName)</label>
            <input id="grdName" name="grdName" value="{grd_name}" type="text" />
            <label for="grdname_en">Grade (EN) (grdname_en)</label>
            <input id="grdname_en" name="grdname_en" value="{grdname_en}" type="text" />
            <label for="busname">Business name (busname)</label>
            <input id="busname" name="busname" value="{busname}" type="text" />
            <label for="intcode">Internal code (intcode)</label>
            <input id="intcode" name="intcode" value="{intcode}" type="text" />
            <label for="intname">Internal name (intname)</label>
            <input id="intname" name="intname" value="{intname}" type="text" />
            <label for="origincomp">Origin company (origincomp)</label>
            <input id="origincomp" name="origincomp" value="{origincomp}" type="text" />
            <label for="employeetype">Employee type (employeetype)</label>
            <input id="employeetype" name="employeetype" value="{employeetype}" type="text" />
          </details>

          <input type="hidden" name="state" value="{state}" />
          <input type="hidden" name="nonce" value="{nonce}" />
          <input type="hidden" name="redirect_uri" value="{redirect_uri}" />
          <input type="hidden" name="client_id" value="{client_id}" />
          <button type="submit">Sign in</button>
        </form>
      </body>
    </html>
    """


def render_callback_form(*, redirect_uri: str, id_token: str, state: str) -> str:
    """OIDC form_post callback으로 자동 제출되는 HTML을 생성합니다."""

    return f"""
    <html>
      <head>
        <title>ADFS redirect</title>
      </head>
      <body>
        <form id="callback-form" method="post" action="{html.escape(redirect_uri)}">
          <input type="hidden" name="id_token" value="{html.escape(id_token)}" />
          <input type="hidden" name="state" value="{html.escape(state)}" />
        </form>
        <script>document.getElementById('callback-form').submit();</script>
      </body>
    </html>
    """


def build_id_token(
    *,
    email: str,
    name: str,
    sabun: str,
    loginid: str,
    nonce: str,
    deptname: str = DEFAULT_DEPT,
    deptid: str = DEFAULT_DEPTID,
    username_en: str = DEFAULT_USERNAME_EN,
    givenname: str = DEFAULT_GIVENNAME,
    surname: str = DEFAULT_SURNAME,
    grd_name: str = DEFAULT_GRDNAME,
    grdname_en: str = DEFAULT_GRDNAME_EN,
    busname: str = DEFAULT_BUSNAME,
    intcode: str = DEFAULT_INTCODE,
    intname: str = DEFAULT_INTNAME,
    origincomp: str = DEFAULT_ORIGINCOMP,
    employeetype: str = DEFAULT_EMPLOYEETYPE,
) -> str:
    now = datetime.now(timezone.utc)
    stable_id = sabun or loginid or email
    subject = hashlib.sha256(stable_id.encode("utf-8")).hexdigest()[:32]

    payload: Dict[str, Any] = {
        "aud": CLIENT_ID,
        "iss": ISSUER,
        "sub": subject,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=5)).timestamp()),
        "nonce": nonce,
        "mail": email,
        "email": email,
        "userid": email,
        "upn": email,
        "loginid": loginid,
        "username": name,
        "name": name,
        "deptname": deptname,
        "deptid": deptid,
        "sabun": sabun,
        "grdName": grd_name,
        "grdname_en": grdname_en,
        "busname": busname,
        "username_en": username_en,
        "givenname": givenname,
        "surname": surname,
        "intcode": intcode,
        "intname": intname,
        "origincomp": origincomp,
        "employeetype": employeetype,
        "jti": secrets.token_hex(16),
    }

    return jwt.encode(payload, PRIVATE_KEY, algorithm="RS256")


@router.get("/authorize", response_class=HTMLResponse)
async def authorize_form(request: Request) -> HTMLResponse:
    redirect_uri = request.query_params.get("redirect_uri")
    if not redirect_uri:
        raise HTTPException(status_code=400, detail="missing redirect_uri")
    if CLIENT_ID and request.query_params.get("client_id") not in {"", CLIENT_ID}:
        raise HTTPException(status_code=400, detail="invalid_client")
    if AUTO_SIGN_IN:
        params = request.query_params
        id_token = build_id_token(
            email=params.get("email") or DEFAULT_EMAIL,
            name=params.get("name") or DEFAULT_NAME,
            sabun=params.get("sabun") or DEFAULT_SABUN,
            loginid=params.get("loginid") or DEFAULT_LOGINID,
            deptname=params.get("deptname") or DEFAULT_DEPT,
            deptid=params.get("deptid") or DEFAULT_DEPTID,
            username_en=params.get("username_en") or DEFAULT_USERNAME_EN,
            givenname=params.get("givenname") or DEFAULT_GIVENNAME,
            surname=params.get("surname") or DEFAULT_SURNAME,
            grd_name=params.get("grdName") or DEFAULT_GRDNAME,
            grdname_en=params.get("grdname_en") or DEFAULT_GRDNAME_EN,
            busname=params.get("busname") or DEFAULT_BUSNAME,
            intcode=params.get("intcode") or DEFAULT_INTCODE,
            intname=params.get("intname") or DEFAULT_INTNAME,
            origincomp=params.get("origincomp") or DEFAULT_ORIGINCOMP,
            employeetype=params.get("employeetype") or DEFAULT_EMPLOYEETYPE,
            nonce=params.get("nonce") or secrets.token_urlsafe(16),
        )
        return HTMLResponse(
            render_callback_form(
                redirect_uri=redirect_uri,
                id_token=id_token,
                state=params.get("state") or "",
            )
        )
    return HTMLResponse(render_login_form(request))


@router.post("/authorize")
async def authorize(
    email: str = Form(DEFAULT_EMAIL),
    name: str = Form(DEFAULT_NAME),
    sabun: str = Form(DEFAULT_SABUN),
    loginid: str = Form(DEFAULT_LOGINID),
    deptname: str = Form(DEFAULT_DEPT),
    deptid: str = Form(DEFAULT_DEPTID),
    username_en: str = Form(DEFAULT_USERNAME_EN),
    givenname: str = Form(DEFAULT_GIVENNAME),
    surname: str = Form(DEFAULT_SURNAME),
    grdName: str = Form(DEFAULT_GRDNAME),
    grdname_en: str = Form(DEFAULT_GRDNAME_EN),
    busname: str = Form(DEFAULT_BUSNAME),
    intcode: str = Form(DEFAULT_INTCODE),
    intname: str = Form(DEFAULT_INTNAME),
    origincomp: str = Form(DEFAULT_ORIGINCOMP),
    employeetype: str = Form(DEFAULT_EMPLOYEETYPE),
    state: str = Form(""),
    nonce: str = Form(""),
    redirect_uri: str = Form(...),
    client_id: str = Form(""),
) -> HTMLResponse:
    if CLIENT_ID and client_id and client_id != CLIENT_ID:
        raise HTTPException(status_code=400, detail="invalid_client")
    if not redirect_uri:
        raise HTTPException(status_code=400, detail="missing_redirect")

    nonce_value = nonce or secrets.token_urlsafe(16)
    id_token = build_id_token(
        email=email or DEFAULT_EMAIL,
        name=name or DEFAULT_NAME,
        sabun=sabun or DEFAULT_SABUN,
        loginid=loginid or DEFAULT_LOGINID,
        deptname=deptname,
        deptid=deptid,
        username_en=username_en,
        givenname=givenname,
        surname=surname,
        grd_name=grdName,
        grdname_en=grdname_en,
        busname=busname,
        intcode=intcode,
        intname=intname,
        origincomp=origincomp,
        employeetype=employeetype,
        nonce=nonce_value,
    )

    html_body = render_callback_form(
        redirect_uri=redirect_uri,
        id_token=id_token,
        state=state,
    )
    return HTMLResponse(content=html_body)


@router.get("/logout")
async def logout() -> RedirectResponse:
    target = LOGOUT_REDIRECT or "/"
    return RedirectResponse(url=target, status_code=302)


@router.get("/.well-known/openid-configuration")
async def openid_config(request: Request) -> Dict[str, Any]:
    base = str(request.url.replace(path="", query="", fragment=""))[:-1]
    return {
        "issuer": ISSUER,
        "authorization_endpoint": f"{base}/authorize",
        "token_endpoint": f"{base}/token",
        "userinfo_endpoint": f"{base}/userinfo",
        "response_types_supported": ["id_token"],
        "grant_types_supported": ["implicit"],
        "scopes_supported": ["openid", "profile", "email"],
    }
