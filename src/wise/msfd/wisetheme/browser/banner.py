# pylint: skip-file
from plone.app.layout.viewlets import ViewletBase
from plone.app.registry.browser.controlpanel import RegistryEditForm
from plone.app.registry.browser.controlpanel import ControlPanelFormWrapper
from plone.registry.interfaces import IRegistry
from zope.component import getUtility
from wise.msfd.wisetheme.interfaces import IBannerSettings


class BannerViewlet(ViewletBase):

    _settings = None

    @property
    def settings(self):
        if self._settings is None:
            registry = getUtility(IRegistry)
            try:
                self._settings = registry.forInterface(IBannerSettings)
            except Exception:
                self._settings = None
        return self._settings

    def available(self):
        settings = self.settings
        if settings is None or not settings.banner_visible:
            return False
        if not settings.banner_text:
            return False
        if self.request.get("wise_banner_dismissed"):
            return False
        return True

    @property
    def banner_text(self):
        settings = self.settings
        return settings.banner_text or u"" if settings else u""

    @property
    def banner_type(self):
        settings = self.settings
        return settings.banner_type or u"info" if settings else u"info"

    @property
    def banner_cookie_days(self):
        settings = self.settings
        return settings.banner_cookie_days or 7 if settings else 7


class BannerSettingsControlPanel(RegistryEditForm, ControlPanelFormWrapper):
    schema = IBannerSettings
    schema_prefix = "wise.msfd.wisetheme.interfaces.IBannerSettings"
    label = u"Banner Settings (MSFD)"
    description = u"Configure the site-wide banner message."

    def updateWidgets(self):
        super().updateWidgets()
        widget = self.widgets.get("banner_text")
        if widget is not None:
            widget.klass = (widget.klass or "") + " pat-tinymce"
