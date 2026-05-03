# -*- coding: utf-8 -*-
"""
Consulta EAN via APIs públicas gratuitas.
Ordem: Open Food Facts → Open Beauty Facts → Open Products Facts → UPC Item DB
"""
import requests
import time

TIMEOUT = 7
HEADERS = {"User-Agent": "SmartLarder-Pro/3.9"}


def _s(v) -> str:
    return str(v).strip() if v else ""


def _categoria(cats: str) -> str:
    if not cats:
        return "Alimentos"
    txt = " ".join(p.split(":")[-1] for p in cats.replace(",",";").split(";")).lower()
    if any(w in txt for w in ["bebida","drink","juice","soda","refrigerante","suco","agua","cerveja","vinho","leite","cha","cafe","iogurte"]):
        return "Bebidas"
    if any(w in txt for w in ["higiene","sabonete","shampoo","creme","dental","desodorante","perfume","cosmet","cabelo","pele"]):
        return "Higiene"
    if any(w in txt for w in ["limpeza","detergente","sabao","desinfet","alvejante","amaciante","multiuso"]):
        return "Limpeza"
    if any(w in txt for w in ["medic","farmac","suplement","vitam","mineral","proteina"]):
        return "Medicamentos"
    return "Alimentos"


def _parse_off(data: dict, cat_force=None) -> dict | None:
    p    = data.get("product", {})
    nome = _s(p.get("product_name_pt")) or _s(p.get("product_name")) or _s(p.get("abbreviated_product_name"))
    if not nome:
        return None
    marca = _s(p.get("brands","")).split(",")[0].strip()
    qtd   = _s(p.get("quantity",""))
    cat   = cat_force or _categoria(p.get("categories",""))
    nome_final = nome
    if marca and marca.lower() not in nome.lower():
        nome_final = f"{nome} — {marca}"
    if qtd and qtd not in nome_final:
        nome_final = f"{nome_final} {qtd}"
    return {"nome":nome_final,"nome_curto":nome,"marca":marca,"categoria":cat,
            "quantidade_embalagem":qtd,"fornecedor":marca,
            "imagem_url":_s(p.get("image_small_url") or p.get("image_url","")),
            "nutriscore":_s(p.get("nutriscore_grade","")).upper(),"fonte":"Open Food Facts"}


def buscar_por_ean(codigo: str) -> dict | None:
    codigo = str(codigo).strip()
    if len(codigo) < 6:
        return None
    fields = "product_name,product_name_pt,brands,categories,quantity,image_small_url,image_url,nutriscore_grade,abbreviated_product_name"
    for lc in ["pt",""]:
        try:
            lc_p = f"&lc={lc}" if lc else ""
            r = requests.get(f"https://world.openfoodfacts.org/api/v2/product/{codigo}.json?fields={fields}{lc_p}", timeout=TIMEOUT, headers=HEADERS)
            if r.status_code==200 and r.json().get("status")==1:
                res = _parse_off(r.json())
                if res: return res
        except Exception:
            pass
    for base, cat in [("https://world.openbeautyfacts.org","Higiene"),("https://world.openproductsfacts.org",None)]:
        try:
            r = requests.get(f"{base}/api/v2/product/{codigo}.json?fields={fields}", timeout=TIMEOUT, headers=HEADERS)
            if r.status_code==200 and r.json().get("status")==1:
                res = _parse_off(r.json(), cat_force=cat)
                if res: res["fonte"]=base.split("//")[1].split(".")[1].title(); return res
        except Exception:
            pass
        time.sleep(0.1)
    try:
        r = requests.get(f"https://api.upcitemdb.com/prod/trial/lookup?upc={codigo}", timeout=TIMEOUT, headers=HEADERS)
        if r.status_code==200:
            items = r.json().get("items",[])
            if items:
                item=items[0]; nome=_s(item.get("title",""))
                if nome:
                    marca=_s(item.get("brand",""))
                    return {"nome":f"{nome}{' — '+marca if marca else ''}","nome_curto":nome,"marca":marca,
                            "categoria":_categoria(item.get("category","")),"quantidade_embalagem":"",
                            "fornecedor":marca,"imagem_url":(item.get("images") or [""])[0],
                            "nutriscore":"","fonte":"UPC Item DB"}
    except Exception:
        pass
    return None
