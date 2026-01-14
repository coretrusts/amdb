"""
国际化支持模块
支持多语言环境
"""

import locale
import gettext
import os
from typing import Dict, Optional


class I18nManager:
    """国际化管理器"""
    
    def __init__(self, locale_dir: str = None, default_locale: str = 'en_US'):
        """
        Args:
            locale_dir: 语言文件目录
            default_locale: 默认语言环境
        """
        self.locale_dir = locale_dir or os.path.join(
            os.path.dirname(__file__), '..', 'locale'
        )
        self.default_locale = default_locale
        self.current_locale = self._detect_locale()
        self.translations: Dict[str, gettext.GNUTranslations] = {}
        self._load_translations()
    
    def _detect_locale(self) -> str:
        """检测系统语言环境"""
        try:
            sys_locale, _ = locale.getlocale()
            if sys_locale:
                return sys_locale.replace('-', '_')
        except Exception:
            pass
        return self.default_locale
    
    def _load_translations(self):
        """加载翻译文件"""
        # 尝试加载当前语言
        success = self._load_locale(self.current_locale)
        # 如果失败，加载默认语言
        if not success and self.current_locale != self.default_locale:
            self._load_locale(self.default_locale)
    
    def _load_locale(self, locale_name: str) -> bool:
        """加载指定语言的翻译"""
        try:
            lang = locale_name.split('_')[0]
            trans = gettext.translation(
                'amdb',
                localedir=self.locale_dir,
                languages=[locale_name, lang],
                fallback=True
            )
            self.translations[locale_name] = trans
            return True
        except Exception as e:
            # 如果翻译文件不存在，使用空翻译
            import gettext
            null_trans = gettext.NullTranslations()
            self.translations[locale_name] = null_trans
            return False
    
    def set_locale(self, locale_name: str):
        """设置语言环境"""
        self.current_locale = locale_name
        self._load_translations()
    
    def gettext(self, message: str) -> str:
        """获取翻译文本"""
        if self.current_locale in self.translations:
            return self.translations[self.current_locale].gettext(message)
        return message
    
    def _(self, message: str) -> str:
        """翻译快捷方法"""
        return self.gettext(message)


# 全局实例
_i18n = I18nManager()


def set_locale(locale_name: str):
    """设置全局语言环境"""
    _i18n.set_locale(locale_name)


def _(message: str) -> str:
    """全局翻译函数"""
    return _i18n.gettext(message)


# 常用消息定义
class Messages:
    """消息常量"""
    DB_INITIALIZED = _("Database initialized")
    DB_CLOSED = _("Database closed")
    KEY_NOT_FOUND = _("Key not found")
    INVALID_VERSION = _("Invalid version")
    TRANSACTION_COMMITTED = _("Transaction committed")
    TRANSACTION_ABORTED = _("Transaction aborted")
    DATA_VERIFIED = _("Data verified")
    DATA_INVALID = _("Data invalid")

