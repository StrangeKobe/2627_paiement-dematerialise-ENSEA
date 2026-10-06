"""Browser entry points; no fake authentication or unvalidated identity input."""

import secrets
import time
from urllib.parse import urlencode

from cas import CASClientV3
from django.conf import settings
from django.contrib.auth import authenticate, login
from django.contrib.auth import views as auth_views
from django.shortcuts import redirect, render
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET

from .cas_auth import cas_ready, issuer_url


class LoginView(auth_views.LoginView):
    template_name = "caisse/login.html"

    def dispatch(self, request, *args, **kwargs):
        if cas_ready():
            return redirect("cas_login")
        return super().dispatch(request, *args, **kwargs)


class LogoutView(auth_views.LogoutView):
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        if cas_ready():
            # Do not automatically re-enter an active CAS SSO session on logout.
            return render(request, "caisse/cas_logged_out.html")
        return response


def failure(request, status=403):
    return render(request, "caisse/cas_error.html", status=status)


@never_cache
@require_GET
def cas_login(request):
    if not cas_ready():
        return redirect("login")
    state = secrets.token_urlsafe(32)
    service = settings.CAS_CALLBACK_URL + "?" + urlencode({"state": state})
    request.session["cas_pending"] = {"state": state, "service": service, "time": time.time()}
    client = CASClientV3(server_url=issuer_url(), service_url=service)
    return redirect(client.get_login_url())


@never_cache
@require_GET
def cas_callback(request):
    if not cas_ready():
        return failure(request, 503)
    pending = request.session.pop("cas_pending", None)
    state = request.GET.get("state", "")
    if (not pending or not state.isascii() or len(request.GET.getlist("state")) != 1
            or not secrets.compare_digest(state, pending["state"])):
        return failure(request)
    if not 0 <= time.time() - pending["time"] <= 300:
        return failure(request)
    tickets = request.GET.getlist("ticket")
    if len(tickets) != 1 or not tickets[0].startswith("ST-") or len(tickets[0]) > 4096:
        return failure(request)
    user = authenticate(request, cas_ticket_secret=tickets[0], cas_service=pending["service"])
    if user is None:
        return failure(request)
    # Django may keep a session for the same user; require the code again anyway.
    request.session.pop("code_verifie", None)
    login(request, user)
    return redirect("verifier_code")
