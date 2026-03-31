# -*- coding: utf-8 -*-
"""Login helpers for local and Authomatic authentication."""

from __future__ import absolute_import

try:
    from pas.plugins.authomatic.utils import authomatic_cfg
except ImportError:  # pragma: no cover
    authomatic_cfg = None

from Products.CMFPlone.browser.login.login import LoginForm
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile


CUSTOM_LOGIN_TEMPLATE = ViewPageTemplateFile("pt/login.pt")


class AuthomaticLoginSupport:
    """Add Authomatic provider links to the standard login form."""

    def render(self):
        """Render the WISE login template."""
        return CUSTOM_LOGIN_TEMPLATE.__get__(self, self.__class__)()

    def authomatic_login_url(self):
        """Return the first provider url or the generic Authomatic view."""
        providers = self.authomatic_providers()
        if providers:
            return providers[0]["url"]
        if authomatic_cfg is None:
            return ""
        return "{}/@@authomatic-handler".format(
            self.portal_state.portal_url()
        )

    def authomatic_providers(self):
        """Return configured Authomatic providers for the login template."""
        if authomatic_cfg is None:
            return []

        try:
            cfgs = authomatic_cfg() or {}
        except Exception:
            return []

        portal_url = self.portal_state.portal_url()
        providers = []
        for identifier, cfg in cfgs.items():
            display = cfg.get("display", {})
            providers.append(
                {
                    "identifier": identifier,
                    "title": display.get("title", identifier),
                    "url": "{}/@@authomatic-handler/{}".format(
                        portal_url, identifier
                    ),
                }
            )
        return providers

    def show_authomatic_login(self):
        """Tell the template whether Authomatic support is installed."""
        return authomatic_cfg is not None


class WiseLoginForm(AuthomaticLoginSupport, LoginForm):
    """Layer-specific login view kept for compatibility."""


def patch_plone_login_form():
    """Patch Plone's global login form to use the WISE template."""
    LoginForm.render = AuthomaticLoginSupport.render
    LoginForm.authomatic_login_url = (
        AuthomaticLoginSupport.authomatic_login_url
    )
    LoginForm.authomatic_providers = (
        AuthomaticLoginSupport.authomatic_providers
    )
    LoginForm.show_authomatic_login = (
        AuthomaticLoginSupport.show_authomatic_login
    )


patch_plone_login_form()
