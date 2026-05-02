"""
imports.py — resolvedor central de módulos.
Cada página faz: from imports import db, auth, email_alert, barcode_lookup
"""
import sys, os

_BASE = os.path.dirname(os.path.abspath(__file__))

def _add_path(p):
    if p not in sys.path:
        sys.path.insert(0, p)

_add_path(_BASE)

# Descobre qual pasta usar
_utils   = os.path.join(_BASE, "utils")
_utilit  = os.path.join(_BASE, "utilitarios")

if os.path.isdir(_utils):
    _pkg = "utils"
elif os.path.isdir(_utilit):
    _pkg = "utilitarios"
else:
    raise ImportError("Nenhuma pasta utils ou utilitarios encontrada!")

import importlib
database      = importlib.import_module(f"{_pkg}.database")
auth          = importlib.import_module(f"{_pkg}.auth")
email_alert   = importlib.import_module(f"{_pkg}.email_alert")
barcode_lookup= importlib.import_module(f"{_pkg}.barcode_lookup")

# Garante que 'utils.X' sempre funcione como alias
for _sub, _mod in [("database",database),("auth",auth),
                   ("email_alert",email_alert),("barcode_lookup",barcode_lookup)]:
    sys.modules[f"utils.{_sub}"]       = _mod
    sys.modules[f"utilitarios.{_sub}"] = _mod

if "utils" not in sys.modules:
    import types
    _m = types.ModuleType("utils")
    _m.__path__ = [_utils if os.path.isdir(_utils) else _utilit]
    sys.modules["utils"] = _m

if "utilitarios" not in sys.modules:
    import types
    _m = types.ModuleType("utilitarios")
    _m.__path__ = [_utilit if os.path.isdir(_utilit) else _utils]
    sys.modules["utilitarios"] = _m
