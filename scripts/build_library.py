"""Build a local reference library from all photos, without training or API calls."""
import hashlib
import json
from pathlib import Path
from PIL import Image, ImageOps, ImageDraw

ROOT = Path(__file__).resolve().parents[1]


def build(root=ROOT):
    if not (root/"references/private/roster.json").is_file():
        raise FileNotFoundError("请先按 references/people.md 配置姓名编号表 references/private/roster.json")
    roster = json.loads((root/"references/private/roster.json").read_text(encoding="utf-8"))
    private = root/"references/private"
    for room, data in roster.items():
        if not (root/(room+"照片")).is_dir():
            raise FileNotFoundError(f"请将原始标注照片放入 {root/(room+'照片')}")
        for person in data["people"]:
            if not (root/person["identity_source"]).is_file():
                raise FileNotFoundError("缺少编号参考源图：" + person["identity_source"])
    private.mkdir(parents=True, exist_ok=True)
    catalog = []
    for room, data in roster.items():
        photos = sorted((f for f in (root/(room+"照片")).iterdir() if f.suffix.lower() in (".png", ".jpg", ".jpeg", ".webp")), key=lambda f:(0,int(f.stem)) if f.stem.isdigit() else (1,f.name))
        for f in photos:
            with Image.open(f) as im:
                catalog.append({"room":room,"file":f.relative_to(root).as_posix(),"width":im.width,"height":im.height,"sha256":hashlib.sha256(f.read_bytes()).hexdigest()})
        for start in range(0,len(photos),6):
            sheet=Image.new("RGB",(1500,990),"#eeeeee"); draw=ImageDraw.Draw(sheet)
            for i,f in enumerate(photos[start:start+6]):
                with Image.open(f) as im: thumb=ImageOps.contain(im.convert("RGB"),(744,292))
                x=i%2*750;y=i//2*330;sheet.paste(thumb,(x,y+30));draw.text((x+8,y+6),room+"/"+f.name,fill="black")
            sheet.save(private/(room+"-sheet-"+str(start//6+1)+".jpg"),quality=93)
        target=private/"identities"/room;target.mkdir(parents=True,exist_ok=True)
        for person in data["people"]:
            with Image.open(root/person["identity_source"]) as im:
                box=person["identity_box"]
                if len(box)!=4 or not 0<=box[0]<box[2]<=1 or not 0<=box[1]<box[3]<=1: raise ValueError("无效身份裁图范围")
                crop=im.crop(tuple(round(v*(im.width if i%2==0 else im.height)) for i,v in enumerate(box)))
                crop.save(target/(str(person["id"])+".png"))
            for index, ref in enumerate(person.get("identity_references", []), 1):
                with Image.open(root/ref["source"]) as im:
                    box = ref["box"]
                    if len(box)!=4 or not 0<=box[0]<box[2]<=1 or not 0<=box[1]<box[3]<=1:
                        raise ValueError("无效补充身份裁图范围")
                    im.crop(tuple(round(v*(im.width if i%2==0 else im.height)) for i,v in enumerate(box))).save(target/(str(person["id"])+"-ref-"+str(index)+".png"))
    catalog.extend(build_winter(root, roster))
    (private/"catalog.json").write_text(json.dumps(catalog,ensure_ascii=False,indent=2),encoding="utf-8")
    return {"photo_count":len(catalog),"rooms":{room:sum(item["room"]==room for item in catalog) for room in roster},"method":"reference-library; no model training"}

def build_winter(root, roster):
    private=root/"references/private"
    folder=root/"401照片冬季"
    if not folder.is_dir(): raise FileNotFoundError("缺少401照片冬季文件夹")
    photos=sorted(p for p in folder.iterdir() if p.suffix.lower() in (".jpg",".jpeg",".png",".webp"))
    catalog=[]
    for f in photos:
        with Image.open(f) as im:catalog.append({"room":"401","season":"winter","file":f.relative_to(root).as_posix(),"width":im.width,"height":im.height,"sha256":hashlib.sha256(f.read_bytes()).hexdigest()})
    for start in range(0,len(photos),6):
        sheet=Image.new("RGB",(1500,990),"#eeeeee");draw=ImageDraw.Draw(sheet)
        for i,f in enumerate(photos[start:start+6]):
            with Image.open(f) as im:thumb=ImageOps.contain(im.convert("RGB"),(744,292))
            sheet.paste(thumb,(i%2*750,i//2*330+30));draw.text((i%2*750+8,i//2*330+6),"401 WINTER / "+f.name.split("_")[-2],fill="black")
        sheet.save(private/("401-winter-sheet-"+str(start//6+1)+".jpg"),quality=93)
    target=private/"identities/401/winter";target.mkdir(parents=True,exist_ok=True)
    clothing=private/"clothing/401/winter";clothing.mkdir(parents=True,exist_ok=True)
    def crop(source,box,destination):
        if len(box)!=4 or not 0<=box[0]<box[2]<=1 or not 0<=box[1]<box[3]<=1:raise ValueError("无效冬季裁图范围")
        with Image.open(root/source) as im:
            im.crop(tuple(round(v*(im.width if i%2==0 else im.height)) for i,v in enumerate(box))).save(destination)
    expected=set()
    for person in roster["401"]["people"]:
        ref=person["seasonal_references"]["winter"]
        legacy=person["seasonal_references"]["spring_autumn"]
        ident=str(person["id"])
        # Compatibility aliases contain ONLY canonical old identity pixels.
        expected.add(ident+".png")
        crop(legacy["identity_source"],legacy["identity_box"],target/(ident+".png"))
        if ref.get("clothing_box"):
            crop(ref["clothing_source"],ref["clothing_box"],clothing/(ident+".png"))
        for index,extra in enumerate(legacy.get("identity_references",[]),1):
            name=ident+"-ref-"+str(index)+".png";expected.add(name)
            crop(extra["source"],extra["box"],target/name)
    # Drop obsolete generated winter-face crops, confined to this derived folder.
    for old in target.glob("*.png"):
        if old.name not in expected and old.parent.resolve()==target.resolve():old.unlink()
    atlas=Image.new("RGB",(1600,800),"white");draw=ImageDraw.Draw(atlas)
    for i,person in enumerate(roster["401"]["people"]):
        x=i%5*320;y=i//5*400;f=target/(str(person["id"])+".png")
        draw.text((x+8,y+8),"401 LEGACY IDENTITY / PERSON "+str(person["id"]),fill="black")
        with Image.open(f) as im:thumb=ImageOps.contain(im.convert("RGB"),(300,350))
        atlas.paste(thumb,(x+(320-thumb.width)//2,y+35))
    atlas.save(private/"401-winter-identity-atlas.jpg",quality=93)
    return catalog

if __name__=="__main__":
    print(json.dumps(build(),ensure_ascii=False,indent=2))
