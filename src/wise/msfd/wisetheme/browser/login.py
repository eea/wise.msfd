# -*- coding: utf-8 -*-
"""Login helpers for mixed local and Authomatic authentication."""

from __future__ import absolute_import

try:
    from pas.plugins.authomatic.utils import authomatic_cfg
except ImportError:  # pragma: no cover
    authomatic_cfg = None

from plone.registry.interfaces import IRegistry
from Products.CMFPlone.browser.login.login import LoginForm
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from zope.component import queryUtility

from ..interfaces import IWiseThemeLoginSettings


CUSTOM_LOGIN_TEMPLATE = ViewPageTemplateFile("pt/login.pt")


class AuthomaticLoginSupport(object):
    """Keep the default login form and expose an extra Authomatic action."""

    AUTHOMATIC_PATHS = (
        u"login-authomatic/{provider}",
        u"authomatic-handler/{provider}",
    )

    def render(self):
        """Render the WISE login template instead of redirecting externally."""
        # pas.plugins.authomatic sets ``plone.external_login_url`` globally,
        # which would otherwise replace the classic login form entirely.
        # WISE needs the local user/password form
        # plus an external login button.
        return CUSTOM_LOGIN_TEMPLATE.__get__(self, self.__class__)()

    def _login_settings(self):
        """Return login-related WISE registry settings."""
        registry = queryUtility(IRegistry)
        if registry is None:
            return None
        return registry.forInterface(
            IWiseThemeLoginSettings,
            prefix="wise.theme.login",
            check=False,
        )

    def authomatic_provider(self):
        """Return the preferred external provider id from registry."""
        settings = self._login_settings()
        provider = (
            getattr(settings, "authomatic_provider", u"")
            if settings
            else u""
        )
        return (provider or u"").strip()

    def authomatic_button_label(self):
        """Return the fallback label for external login."""
        settings = self._login_settings()
        label = (
            getattr(settings, "authomatic_button_label", u"Log in with Entra")
            if settings
            else u"Log in with Entra"
        )
        return (label or u"Log in with Entra").strip()

    def authomatic_login_url(self):
        """Return the first provider url or the generic Authomatic view."""
        providers = self.authomatic_providers()
        if providers:
            return providers[0]["url"]
        if authomatic_cfg is None:
            return u""
        return u"{}/@@authomatic-handler".format(
            self.portal_state.portal_url()
        )

    def authomatic_providers(self):
        """Return the configured Authomatic providers for the login UI."""
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
            title = display.get("title", identifier)
            providers.append(
                {
                    "identifier": identifier,
                    "title": title,
                    "url": u"{}/@@authomatic-handler/{}".format(
                        portal_url, identifier
                    ),
                }
            )
        return providers

    def _authomatic_path(self):
        """Return a traversable legacy Authomatic path when available."""
        provider = self.authomatic_provider()
        if not provider:
            return u""

        portal = self.portal_state.portal()
        for path_template in self.AUTHOMATIC_PATHS:
            path = path_template.format(provider=provider)
            if portal.unrestrictedTraverse(path, None) is not None:
                return path
        return u""

    def show_authomatic_login(self):
        """Tell the template whether Authomatic support is installed."""
        return authomatic_cfg is not None


class WiseLoginForm(AuthomaticLoginSupport, LoginForm):
    """Layer-specific login view kept for compatibility."""


def patch_plone_login_form():
    """Patch the global Plone login form so modal and direct login match."""
    LoginForm.render = AuthomaticLoginSupport.render
    LoginForm._login_settings = AuthomaticLoginSupport._login_settings
    LoginForm.authomatic_provider = AuthomaticLoginSupport.authomatic_provider
    LoginForm.authomatic_button_label = (
        AuthomaticLoginSupport.authomatic_button_label
    )
    LoginForm.authomatic_login_url = (
        AuthomaticLoginSupport.authomatic_login_url
    )
    LoginForm.authomatic_providers = (
        AuthomaticLoginSupport.authomatic_providers
    )
    LoginForm._authomatic_path = AuthomaticLoginSupport._authomatic_path
    LoginForm.show_authomatic_login = (
        AuthomaticLoginSupport.show_authomatic_login
    )


patch_plone_login_form()
