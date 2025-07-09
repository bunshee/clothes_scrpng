from enum import StrEnum

class SpiderName(StrEnum):
    PULLANDBEAR = "pullandbear"
    HM = "hm"
    JULES = "jules"
    PRIMARK = "primark"
    CANDA = "canda"
    NIKE = "nike"
    BERSHKA = "bershka"
    CELIO = "celio"

class PageType(StrEnum):
    PRODUCT = "product"
    CATEGORY = "category"
    OTHER = "other"