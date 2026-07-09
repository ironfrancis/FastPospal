"""向后兼容导出，请优先使用 ``fastpospal.raw.client``。"""
from fastpospal.raw.client import PospalApiError, PospalAuthError, PospalClient

__all__ = ["PospalApiError", "PospalAuthError", "PospalClient"]
