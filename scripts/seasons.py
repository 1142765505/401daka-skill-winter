"""Select season-specific references without inventing unseen clothes."""
import json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def season_for(command="",room="401",override=None):
    winter=bool(re.search(r"冬",command));legacy=bool(re.search(r"春|秋",command))
    if winter and legacy:raise ValueError("同时包含冬季与春秋要求，请只选择一种衣服版本")
    if override not in (None,"winter","spring_autumn","legacy"):raise ValueError("未知季节版本")
    chosen=override or ("spring_autumn" if legacy else "winter" if winter or room=="401" else "legacy")
    if override and ((winter and override!="winter") or (legacy and override!="spring_autumn")):raise ValueError("命令季节与参数冲突")
    if room=="403":
        if chosen=="winter":raise ValueError("403没有冬季参考库，不能借用401衣服")
        return "legacy"
    return chosen

def without_season(command):
    return re.sub(r"(?:春秋|冬季|冬天|冬装|春季|秋季|春装|秋装|春|秋|冬)(?:衣服|服装|版本|版)?", "",command).strip(" ，,;；")

def person_reference(room,ident,season=None,root=ROOT):
    active=season_for("",room,season)
    roster=json.loads((root/"references/private/roster.json").read_text(encoding="utf-8"))
    p=next((p for p in roster[room]["people"] if p["id"]==ident),None)
    if p is None:raise ValueError("未知人物编号")
    ref=p.get("seasonal_references",{}).get(active,p if active=="legacy" else None)
    if ref is None or ref.get("status") in ("missing","uncertain"):raise ValueError(f"{room}的{ident}号缺少{active}服装参考，请补充；人物身份沿用旧版，不自动改用旧服装")
    return ref
