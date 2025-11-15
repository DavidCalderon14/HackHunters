# backend/app.py
from fastapi import FastAPI, UploadFile, File, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from typing import List
import json
import os

from backend.validar_factura import validar_factura
from backend.pdf_to_json import pdf_to_json

app = FastAPI(title="Hackhunters - Validación avanzada DIAN")

# ===============================================================
#  BASE DIR (ruta absoluta del proyecto)
# ===============================================================
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATIC_DIR = os.path.join(BASE_DIR, "static")
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")

print("BASE_DIR:", BASE_DIR)
print("STATIC_DIR:", STATIC_DIR)
print("TEMPLATES_DIR:", TEMPLATES_DIR)

# ===============================================================
#  CORS
# ===============================================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ===============================================================
#  MONTAR STATIC Y TEMPLATES CON RUTAS REALES
# ===============================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))   # backend/
ROOT_DIR = os.path.dirname(BASE_DIR)                   # HackHunters/

STATIC_DIR = os.path.join(ROOT_DIR, "static")
TEMPLATES_DIR = os.path.join(ROOT_DIR, "templates")

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
templates = Jinja2Templates(directory=TEMPLATES_DIR)

# ===============================================================
#  RUTA PRINCIPAL
# ===============================================================
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


# ===============================================================
#  VALIDACIÓN DE JSON DE FACTURAS
# ===============================================================
@app.post("/api/validar")
async def validar_archivos(files: List[UploadFile] = File(...)):
    resultados = []

    for file in files:
        try:
            contents = await file.read()
            data = json.loads(contents.decode("utf-8"))
            resultado = validar_factura(data)

            estado = (
                resultado.get("resultado")
                or resultado.get("status")
                or "Sin estado"
            )

            resultados.append(
                {
                    "filename": file.filename,
                    "estado": estado,
                    "detalle": resultado,
                }
            )

        except json.JSONDecodeError:
            resultados.append(
                {
                    "filename": file.filename,
                    "estado": "Error",
                    "detalle": {
                        "resultado": "No cumple",
                        "errores": [
                            {
                                "campo": "Archivo",
                                "motivo": "El archivo no es un JSON válido.",
                                "sugerencia": "Revise la estructura del JSON.",
                            }
                        ],
                    },
                }
            )

        except Exception as e:
            resultados.append(
                {
                    "filename": file.filename,
                    "estado": "Error",
                    "detalle": {
                        "resultado": "Error interno",
                        "errores": [
                            {
                                "campo": "Sistema",
                                "motivo": str(e),
                                "sugerencia": "Contacte al administrador.",
                            }
                        ],
                    },
                }
            )

    return JSONResponse(content={"resultados": resultados})


# ===============================================================
#  CONVERTIR PDF → JSON
# ===============================================================
@app.post("/api/convertir-pdf")
async def convertir_pdf(file: UploadFile = File(...)):
    pdf_bytes = await file.read()
    json_data = pdf_to_json(pdf_bytes)
    return JSONResponse(content={"filename": file.filename, "json": json_data})
