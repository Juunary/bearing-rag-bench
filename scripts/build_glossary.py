"""Write data/glossary.json: ko/de surface forms -> standard English engineering term.

[EN]
- Role: term hints for the English-pivot translation prompts (ragbench.translate). A hint for an entry
  is added to a prompt only when one of its ko/de forms occurs in the text being translated.
- Source: written by hand for this corpus (bearings, seals, lubrication, wear, drivetrain). All surface
  forms are kept because questions may use variants that the corpus does not (e.g. "니들 롤러 베어링");
  an entry is dropped only if none of its forms occurs in the corpus at all.
- Usage: uv run python scripts/build_glossary.py

[KO]
- 역할: 영어 피벗 번역 프롬프트(ragbench.translate)에 넣는 용어 힌트. 번역할 텍스트에 항목의 ko/de 표기
  중 하나가 나올 때만 그 항목의 힌트를 프롬프트에 붙인다.
- 출처: 이 코퍼스(베어링, 밀봉, 윤활, 마모, 구동계)에 맞춰 직접 작성. 질문이 코퍼스에 없는 변형 표기
  (예: "니들 롤러 베어링")를 쓸 수 있어 표기는 모두 남기고, 어떤 표기도 코퍼스에 없는 항목만 뺀다.
- 사용: uv run python scripts/build_glossary.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ragbench.ingest import REPO, load_docs  # noqa: E402

ENTRIES = [
 ("rolling bearing", ["구름 베어링", "롤링 베어링"], ["Wälzlager"]),
 ("plain bearing", ["미끄럼 베어링", "슬라이딩 베어링", "평 베어링"], ["Gleitlager"]),
 ("ball bearing", ["볼 베어링"], ["Kugellager"]),
 ("roller bearing", ["롤러 베어링"], ["Rollenlager"]),
 ("needle roller bearing", ["니들 롤러 베어링", "바늘 롤러 베어링"], ["Nadellager"]),
 ("tapered roller bearing", ["테이퍼 롤러 베어링"], ["Kegelrollenlager"]),
 ("cylindrical roller bearing", ["원통 롤러 베어링"], ["Zylinderrollenlager"]),
 ("deep groove ball bearing", ["깊은 홈 볼 베어링"], ["Rillenkugellager"]),
 ("angular contact ball bearing", ["앵귤러 콘택트"], ["Schrägkugellager"]),
 ("self-aligning ball bearing", ["자동 조심"], ["Pendelkugellager"]),
 ("thrust bearing", ["스러스트 베어링"], ["Axiallager"]),
 ("radial bearing", ["레이디얼 베어링", "래디얼 베어링"], ["Radiallager"]),
 ("linear bearing", ["리니어 베어링"], ["Linearlager"]),
 ("rolling element", ["전동체", "롤링 요소"], ["Wälzkörper"]),
 ("cage", ["케이지", "리테이너"], ["Käfig"]),
 ("inner ring", ["내륜"], ["Innenring"]),
 ("outer ring", ["외륜"], ["Außenring"]),
 ("raceway", ["레이스", "궤도"], ["Laufbahn", "Laufring"]),
 ("service life", ["수명"], ["Lebensdauer"]),
 ("load capacity", ["하중 용량", "부하 용량"], ["Tragfähigkeit", "Tragzahl"]),
 ("friction", ["마찰"], ["Reibung"]),
 ("rolling friction", ["구름 마찰"], ["Rollreibung"]),
 ("sliding friction", ["미끄럼 마찰"], ["Gleitreibung"]),
 ("mixed friction", ["혼합 마찰"], ["Mischreibung"]),
 ("fluid friction", ["유체 마찰"], ["Flüssigkeitsreibung"]),
 ("solid friction", ["고체 마찰"], ["Festkörperreibung"]),
 ("wear", ["마모"], ["Verschleiß"]),
 ("fatigue", ["피로"], ["Ermüdung"]),
 ("material fatigue", ["재료 피로"], ["Materialermüdung"]),
 ("endurance limit", ["피로 한도", "내구 한도"], ["Dauerfestigkeit"]),
 ("fretting", ["프레팅"], ["Passungsrost", "Reibkorrosion"]),
 ("brinelling", ["브리넬링", "브리넬"], []),
 ("galling", ["갈링"], ["Fressen"]),
 ("corrosion", ["부식"], ["Korrosion"]),
 ("lubrication", ["윤활"], ["Schmierung"]),
 ("lubricant", ["윤활유", "윤활제"], ["Schmierstoff", "Schmiermittel"]),
 ("grease", ["그리스"], ["Schmierfett"]),
 ("lubricating film", ["유막"], ["Schmierfilm"]),
 ("viscosity", ["점도"], ["Viskosität"]),
 ("thickener", ["증주제", "증점제"], ["Verdicker", "Eindicker"]),
 ("base oil", ["기유"], ["Grundöl"]),
 ("additive", ["첨가제"], ["Additiv"]),
 ("seal", ["씰", "밀봉"], ["Dichtung"]),
 ("radial shaft seal", ["오일 씰", "래디얼 샤프트 씰", "레이디얼 샤프트 씰"], ["Wellendichtring", "Radialwellendichtring"]),
 ("sealing lip", ["실링 립"], ["Dichtlippe"]),
 ("labyrinth seal", ["래버린스", "라비린스"], ["Labyrinthdichtung"]),
 ("shaft", ["샤프트"], ["Welle"]),
 ("housing", ["하우징"], ["Gehäuse"]),
 ("differential", ["차동", "디퍼렌셜"], ["Differential", "Ausgleichsgetriebe"]),
 ("drive shaft", ["구동축", "드라이브 샤프트"], ["Antriebswelle", "Kardanwelle"]),
 ("universal joint", ["유니버설 조인트", "십자축"], ["Kreuzgelenk"]),
 ("constant-velocity joint", ["등속 조인트"], ["homokinetisch"]),
 ("axle", ["차축"], ["Achse"]),
 ("preload", ["예압"], ["Vorspannung"]),
 ("bearing clearance", ["틈새", "간극"], ["Lagerluft", "Lagerspiel"]),
 ("contact angle", ["접촉각"], ["Druckwinkel"]),
 ("radial load", ["반경 하중", "레이디얼 하중"], ["Radialkraft", "Radiallast"]),
 ("axial load", ["축 하중", "축방향 하중", "스러스트 하중"], ["Axialkraft", "Axiallast"]),
 ("rotational speed", ["회전 속도", "회전수"], ["Drehzahl"]),
 ("Hertzian contact stress", ["헤르츠"], ["Hertzsche Pressung"]),
 ("tribology", ["트라이볼로지", "마찰학"], ["Tribologie"]),
 ("Stribeck curve", ["스트리벡"], ["Stribeck"]),
 ("ceramic", ["세라믹"], ["Keramik"]),
 ("silicon nitride", ["질화규소", "질화 규소"], ["Siliziumnitrid"]),
 ("hardness", ["경도"], ["Härte"]),
 ("fixed bearing", ["고정 베어링"], ["Festlager"]),
 ("floating bearing", ["유동 베어링", "자유 베어링"], ["Loslager"]),
 ("bushing", ["부시", "부싱"], ["Buchse", "Lagerbuchse"]),
 ("shrink fit", ["열박음", "수축 끼워맞춤"], ["Aufschrumpfen"]),
 ("abrasion", ["연마 마모", "마멸"], ["Abrasion"]),
 ("adhesive wear", ["응착 마모", "접착 마모"], ["Adhäsion"]),
 ("surface fatigue", ["표면 피로"], ["Oberflächenermüdung", "Grübchen"]),
 ("pitting", ["피팅"], ["Pitting"]),
 ("oil", ["오일", "기름"], ["Öl"]),
 ("grease change interval", ["교체 주기", "교체 간격"], ["Nachschmierintervall", "Schmierintervall"]),
]


def main() -> None:
    docs = load_docs()
    corpus = {"ko": " ".join(d["text"] for d in docs if d["lang"] == "ko"),
              "de": " ".join(d["text"] for d in docs if d["lang"] == "de").lower()}
    out, dropped = [], []
    for en, ko, de in ENTRIES:
        # 표기는 모두 남기되, 어떤 표기도 코퍼스에 없는 항목은 뺀다
        if any(t in corpus["ko"] for t in ko) or any(t.lower() in corpus["de"] for t in de):
            out.append({"en": en, "ko": ko, "de": de})
        else:
            dropped.append(en)
    path = REPO / "data" / "glossary.json"
    path.write_text(json.dumps({"note": "a term hint is added to a translation prompt only when one of its ko/de forms occurs in the text",
                                "entries": out}, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{len(ENTRIES)} entries -> {len(out)} written; dropped (no form in corpus): {dropped}")


if __name__ == "__main__":
    main()
