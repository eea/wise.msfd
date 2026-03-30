# -*- coding: utf-8 -*-

from __future__ import absolute_import

from plone.registry.interfaces import IRegistry
from Products.CMFPlone.browser.login.login import LoginForm
from urllib import parse
from zope.component import queryUtility

from ..interfaces import IWiseThemeLoginSettings


class WiseLoginForm(LoginForm):
    """Keep the default login form and expose an extra Authomatic action."""

    AUTHOMATIC_PATHS = (
        u"login-authomatic/{provider}",
        u"authomatic-handler/{provider}",
    )

    def render(self):
        # pas.plugins.authomatic sets ``plone.external_login_url`` globally,
        # which would otherwise replace the classic login form entirely.
        # WISE needs the local user/password form plus an external login button.
        return self.index()

    def _login_settings(self):
        registry = queryUtility(IRegistry)
        if registry is None:
            return None
        return registry.forInterface(
            IWiseThemeLoginSettings,
            prefix="wise.theme.login",
            check=False,
        )

    def authomatic_provider(self):
        settings = self._login_settings()
        provider = getattr(settings, "authomatic_provider", u"") if settings else u""
        return (provider or u"").strip()

    def authomatic_button_label(self):
        settings = self._login_settings()
        label = (
            getattr(settings, "authomatic_button_label", u"Log in with Entra")
            if settings
            else u"Log in with Entra"
        )
        return (label or u"Log in with Entra").strip()

    def authomatic_login_url(self):
        provider = self.authomatic_provider()
        if not provider:
            return u""

        portal_url = self.portal_state.portal_url()
        base_path = self._authomatic_path()
        if not base_path:
            return u""
        base = u"{}/{}".format(portal_url, base_path)

        params = {}
        came_from = self.get_came_from()
        if came_from:
            params["came_from"] = came_from

        if not params:
            return base
        return u"{}?{}".format(base, parse.urlencode(params))

    def _authomatic_path(self):
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
        return bool(self._authomatic_path())
