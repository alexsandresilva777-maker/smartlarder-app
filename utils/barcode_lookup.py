"""
Lookup de EAN via APIs públicas gratuitas.
Ordem: Open Food Facts → Open Beauty Facts → Open Products Facts → UPC Item DB
"""
import requests, time

TIMEOUT = 7
HEADERS = {"User-Agent": "SmartLarder-Pro/3.0 (open-source)"}

def _s(v) -> str:
    return str(v).strip() if v else ""

def _categoria(cats: str) -> str:
    if not cats:
        return "Alimentos"
    txt = " ".join(p.split(":")[-1] for p in cats.replace(",",";").split(";")).lower()
    if any(w in txt for w in ["bebida","drink","juice","soda","refrigerante","suco","agua",
                               "cerveja","vinho","leite","cha","cafe","iogurte","achocolatado"]):
        return "Bebidas"
    if any(w in txt for w in ["higiene","sabonete","shampoo","creme","dental","desodorante",
                               "perfume","cosmet","cabelo","pele","maquiagem"]):
        return "Higiene"
    if any(w in txt for w in ["limpeza","detergente","sabao","desinfet","alvejante",
                               "amaciante","multiuso","esponja"]):
        return "Limpeza"
    if any(w in txt for w in ["medic","farmac","suplement","vitam","mineral","proteina"]):
        return "Medicamentos"
    return "Alimentos"

def _parse_off(data: dict, cat_force=None) -> dict | None:
    p    = data.get("product", {})
    nome = (_s(p.get("product_name_pt")) or _s(p.get("product_name"))
            or _s(p.get("abbreviated_product_name")))
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
    return {
        "nome":                nome_final,
        "nome_curto":          nome,
        "marca":               marca,
        "categoria":           cat,
        "quantidade_embalagem": qtd,
        "fornecedor":          marca,
        "imagem_url":          _s(p.get("image_small_url") or p.get("image_url","")),
        "nutriscore":          _s(p.get("nutriscore_grade","")).upper(),
        "fonte":               "Open Food Facts",
    }

def buscar_por_ean(codigo: str) -> dict | None:
    codigo = str(codigo).strip()
    if len(codigo) < 6:
        return None

    fields = ("product_name,product_name_pt,brands,categories,quantity,"
              "image_small_url,image_url,nutriscore_grade,abbreviated_product_name")

    # 1 — Open Food Facts
    for lc in ["pt", ""]:
        try:
            lc_p = f"&lc={lc}" if lc else ""
            url  = f"https://world.openfoodfacts.org/api/v2/product/{codigo}.json?fields={fields}{lc_p}"
            r = requests.get(url, timeout=TIMEOUT, headers=HEADERS)
            if r.status_code == 200 and r.json().get("status") == 1:
                res = _parse_off(r.json())
                if res:
                    return res
        except Exception:
            pass

    # 2 — Open Beauty Facts
    try:
        url = f"https://world.openbeautyfacts.org/api/v2/product/{codigo}.json?fields={fields}"
        r = requests.get(url, timeout=TIMEOUT, headers=HEADERS)
        if r.status_code == 200 and r.json().get("status") == 1:
            res = _parse_off(r.json(), cat_force="Higiene")
            if res:
                res["fonte"] = "Open Beauty Facts"; return res
    except Exception:
        pass
    time.sleep(0.1)

    # 3 — Open Products Facts
    try:
        url = f"https://world.openproductsfacts.org/api/v2/product/{codigo}.json?fields={fields}"
        r = requests.get(url, timeout=TIMEOUT, headers=HEADERS)
        if r.status_code == 200 and r.json().get("status") == 1:
            res = _parse_off(r.json())
            if res:
                res["fonte"] = "Open Products Facts"; return res
    except Exception:
        pass

    # 4 — UPC Item DB
    try:
        url = f"https://api.upcitemdb.com/prod/trial/lookup?upc={codigo}"
        r = requests.get(url, timeout=TIMEOUT, headers=HEADERS)
        if r.status_code == 200:
            items = r.json().get("items", [])
            if items:
                item = items[0]
                nome = _s(item.get("title",""))
                if nome:
                    marca = _s(item.get("brand",""))
                    imgs  = item.get("images") or [""]
                    return {
                        "nome":                f"{nome}{' — '+marca if marca else ''}",
                        "nome_curto":          nome,
                        "marca":               marca,
                        "categoria":           _categoria(item.get("category","")),
                        "quantidade_embalagem": "",
                        "fornecedor":          marca,
                        "imagem_url":          imgs[0] if imgs else "",
                        "nutriscore":          "",
                        "fonte":               "UPC Item DB",
                    }
    except Exception:
        pass

    return None
