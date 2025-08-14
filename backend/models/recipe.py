from typing import Dict, Any, Optional
from datetime import date

class Recipe:
    def __init__(
        self, 
        recipe_id: Optional[str],
        user_id: str,
        tarif_adi: str,
        malzemeler: str,
        kalori: str,
        tarih: str,
        diyet_tipi: str,
        full_recipe_markdown: str,
        hazirlik_suresi: Optional[str] = None,
        pisirme_suresi: Optional[str] = None,
        porsiyon: Optional[str] = None,
    ):
        self.recipe_id = recipe_id
        self.user_id = user_id
        self.tarif_adi = tarif_adi
        self.malzemeler = malzemeler
        self.kalori = kalori
        self.tarih = tarih
        self.diyet_tipi = diyet_tipi
        self.full_recipe_markdown = full_recipe_markdown
        self.hazirlik_suresi = hazirlik_suresi
        self.pisirme_suresi = pisirme_suresi
        self.porsiyon = porsiyon

    def to_dict(self) -> Dict[str, Any]:
        return {
            "user_id": self.user_id,
            "tarif_adi": self.tarif_adi,
            "malzemeler": self.malzemeler,
            "kalori": self.kalori,
            "tarih": self.tarih,
            "diyet_tipi": self.diyet_tipi,
            "full_recipe_markdown": self.full_recipe_markdown,
            "hazirlik_suresi": self.hazirlik_suresi,
            "pisirme_suresi": self.pisirme_suresi,
            "porsiyon": self.porsiyon,
        }

    @staticmethod
    def from_dict(source: Dict[str, Any], recipe_id: Optional[str] = None):
        return Recipe(
            recipe_id=recipe_id,
            user_id=source["user_id"],
            tarif_adi=source["tarif_adi"],
            malzemeler=source["malzemeler"],
            kalori=source["kalori"],
            tarih=source["tarih"],
            diyet_tipi=source["diyet_tipi"],
            full_recipe_markdown=source["full_recipe_markdown"],
            hazirlik_suresi=source.get("hazirlik_suresi"),
            pisirme_suresi=source.get("pisirme_suresi"),
            porsiyon=source.get("porsiyon"),
        )

