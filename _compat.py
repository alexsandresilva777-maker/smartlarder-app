"""
Compatibilidade de imports: garante que 'utils' funcione
mesmo que a pasta esteja nomeada como 'utilitarios' no deploy.
Importar este módulo no início do app.py resolve o problema.
"""
import sys
import os

_base = os.path.dirname(os.path.abspath(__file__))

# Se existe pasta 'utilitarios' mas não 'utils', cria alias no sys.modules
_utils_path = os.path.join(_base, "utils")
_util_path2 = os.path.join(_base, "utilitarios")

if not os.path.isdir(_utils_path) and os.path.isdir(_util_path2):
    # Adiciona 'utilitarios' como 'utils' no path de módulos
    import importlib
    import importlib.util
    import types

    # Cria módulo virtual 'utils' apontando para 'utilitarios'
    utils_mod = types.ModuleType("utils")
    utils_mod.__path__ = [_util_path2]
    utils_mod.__package__ = "utils"
    sys.modules["utils"] = utils_mod

    # Mapeia cada submódulo
    for mod_name in ["database", "auth", "email_alert", "barcode_lookup"]:
        full_src = f"utilitarios.{mod_name}"
        full_dst = f"utils.{mod_name}"
        try:
            src = importlib.import_module(full_src)
            sys.modules[full_dst] = src
        except Exception:
            pass
