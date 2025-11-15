#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Motor de validación de factura de importación - DIAN Colombia (CT-COA-0124)

Este script valida una factura comercial de importación en formato JSON, comprobando 
los campos obligatorios según la normativa DIAN. Genera un reporte de errores por campo 
(con motivos y sugerencias) y clasifica la factura como 'Cumple' o 'No cumple'.

Uso:
    python validar_factura.py <archivo_factura.json>

Ejemplo:
    python validar_factura.py FACTURA_58846.json

Salida:
  - Muestra en consola el resultado de la validación y los errores encontrados.
  - Genera un archivo JSON con el reporte de validación (mismo nombre de factura con sufijo "_resultado.json").

"""
import sys
import json
from datetime import datetime
import re

def parse_numeric(num_str):
    """
    Convierte una cadena con formato numérico en un float.
    Acepta comas y puntos como separadores de miles o decimales.
    Devuelve None si no es posible interpretar la cadena como número.
    """
    if num_str is None:
        return None
    s = str(num_str).strip()
    if s == "":
        return None
    # Contar separadores
    dot_count = s.count('.')
    comma_count = s.count(',')
    if comma_count > 0 and dot_count > 0:
        # Si contiene ambos separadores, determinar cuál es decimal según posición
        last_dot = s.rfind('.')
        last_comma = s.rfind(',')
        if last_comma > last_dot:
            # Coma aparece después del punto -> coma es separador decimal, punto separador de miles
            s_clean = s.replace('.', '')
            s_clean = s_clean.replace(',', '.')
        else:
            # Punto aparece después de coma -> punto es separador decimal, coma separador de miles
            s_clean = s.replace(',', '')
        try:
            return float(s_clean)
        except:
            return None
    elif comma_count > 0 and dot_count == 0:
        # Solo coma presente: asumir coma como separador decimal (formato es_ES)
        parts = s.split(',')
        if len(parts) == 2:
            int_part, frac_part = parts
            if len(frac_part) <= 2:
                # Ej: "123,45" -> 123.45
                s_clean = s.replace(',', '.')
            else:
                # Ej: "1,2345" (frac > 2 dígitos) o "1,234,567" -> tratar comas como miles
                s_clean = s.replace(',', '')
        else:
            # Múltiples comas (ej: "1,234,567") -> eliminar todas (separadores de miles)
            s_clean = s.replace(',', '')
        try:
            return float(s_clean)
        except:
            return None
    elif dot_count > 0 and comma_count == 0:
        # Solo punto presente: asumir punto como separador decimal (formato en_US)
        try:
            return float(s)
        except:
            return None
    else:
        # Sin coma ni punto, debería ser solo dígitos (posiblemente entero)
        if re.fullmatch(r'-?\d+', s):
            try:
                return float(s)
            except:
                return None
        else:
            return None

def es_fecha_valida(fecha_str):
    """
    Verifica si una cadena corresponde a una fecha válida.
    Acepta formatos comunes DD/MM/AAAA, MM/DD/AAAA, YYYY-MM-DD, etc.
    Devuelve True si la fecha es válida, False en caso contrario.
    """
    if fecha_str is None:
        return False
    s = fecha_str.strip()
    if s == "":
        return False
    # Probar varios formatos de fecha
    formatos = ["%d/%m/%Y", "%m/%d/%Y", "%Y-%m-%d", "%d-%m-%Y", "%m-%d-%Y"]
    for fmt in formatos:
        try:
            datetime.strptime(s, fmt)
            return True  # Formato válido
        except:
            continue
    return False

def validar_campos_principales(campos):
    """
    Valida los campos principales obligatorios de la factura.
    'campos' es un diccionario con los datos de cabecera de la factura.
    Devuelve una lista de errores (diccionarios) encontrados en estos campos.
    """
    errores = []
    # Extraer campos requeridos de cabecera
    exp_nombre = campos.get("Supplier")            # Nombre exportador
    exp_dir    = campos.get("SupplierAddress")     # Dirección exportador
    exp_id     = campos.get("SupplierTaxID")       # NIT/ID exportador
    imp_nombre = campos.get("Customer")            # Nombre importador
    imp_dir    = campos.get("CustomerAddress")     # Dirección importador
    imp_id     = campos.get("CustomerTaxID")       # NIT/ID importador
    num_fact   = campos.get("InvoiceNumber")       # Número de factura
    fecha_fact = campos.get("InvoiceDate")         # Fecha de factura
    incoterm   = campos.get("Incoterm")            # Incoterm
    puerto_carga = campos.get("PortOfLoading")     # Puerto de carga
    puerto_desc  = campos.get("PortOfDischarge")   # Puerto de descarga
    origen     = campos.get("CountryOfOrigin")     # País de origen
    pago       = campos.get("PaymentTerms")        # Condiciones de pago
    moneda     = campos.get("Currency")            # Moneda
    valor_total= campos.get("TotalInvoiceValue")   # Valor total factura

    def esta_vacio(valor):
        """Comprueba si un campo (valor) está vacío o no fue proporcionado."""
        if valor is None:
            return True
        if isinstance(valor, str):
            # Considerar "N/A", "none" como vacíos también
            if valor.strip() == "" or valor.strip().lower() in ["n/a", "na", "none"]:
                return True
        return False

    # Validar datos del Exportador (vendedor)
    if esta_vacio(exp_nombre):
        errores.append({
            "campo": "Exportador - Nombre",
            "motivo": "No se proporcionó el nombre o razón social del exportador.",
            "sugerencia": "Incluya el nombre completo o la razón social del exportador."
        })
    if esta_vacio(exp_dir):
        errores.append({
            "campo": "Exportador - Dirección",
            "motivo": "No se proporcionó la dirección del exportador.",
            "sugerencia": "Incluya la dirección (ciudad, país) completa del exportador."
        })
    if esta_vacio(exp_id):
        errores.append({
            "campo": "Exportador - NIT/ID",
            "motivo": "No se proporcionó la identificación fiscal (NIT o equivalente) del exportador.",
            "sugerencia": "Incluya el NIT del exportador o su número de identificación fiscal extranjero."
        })
    # Validar datos del Importador (comprador)
    if esta_vacio(imp_nombre):
        errores.append({
            "campo": "Importador - Nombre",
            "motivo": "No se proporcionó el nombre o razón social del importador.",
            "sugerencia": "Incluya el nombre completo o la razón social del importador."
        })
    if esta_vacio(imp_dir):
        errores.append({
            "campo": "Importador - Dirección",
            "motivo": "No se proporcionó la dirección del importador.",
            "sugerencia": "Incluya la dirección (ciudad, país) completa del importador."
        })
    if esta_vacio(imp_id):
        errores.append({
            "campo": "Importador - NIT/ID",
            "motivo": "No se proporcionó la identificación fiscal (NIT o equivalente) del importador.",
            "sugerencia": "Incluya el NIT del importador (si es en Colombia) o su identificación fiscal en el exterior."
        })
    # Validar datos de la factura (número, fecha, incoterm, puertos, origen, pago, moneda, valor total)
    if esta_vacio(num_fact):
        errores.append({
            "campo": "Número de Factura",
            "motivo": "No se proporcionó el número de la factura comercial.",
            "sugerencia": "Incluya el número o código identificador de la factura."
        })
    if esta_vacio(fecha_fact):
        errores.append({
            "campo": "Fecha de Factura",
            "motivo": "No se proporcionó la fecha de expedición de la factura.",
            "sugerencia": "Incluya la fecha de emisión de la factura en formato DD/MM/AAAA."
        })
    elif not es_fecha_valida(fecha_fact):
        errores.append({
            "campo": "Fecha de Factura",
            "motivo": f"El formato de la fecha '{fecha_fact}' no es válido.",
            "sugerencia": "Use un formato de fecha válido, por ejemplo DD/MM/AAAA."
        })
    if esta_vacio(incoterm):
        errores.append({
            "campo": "Incoterm",
            "motivo": "No se especificó el Incoterm (término de entrega) de la transacción.",
            "sugerencia": "Incluya el Incoterm acordado (por ejemplo FOB, CIF, CIP), junto con el lugar pactado."
        })
    else:
        # Validar que el Incoterm esté entre los reconocidos
        incoterm_code = str(incoterm).strip().upper()
        incoterms_validos = {"EXW","FCA","FAS","FOB","CFR","CIF","CPT","CIP","DAP","DPU","DDP","DAT"}
        if incoterm_code not in incoterms_validos:
            errores.append({
                "campo": "Incoterm",
                "motivo": f"El Incoterm '{incoterm}' no es reconocido.",
                "sugerencia": "Verifique el Incoterm. Debe ser uno de: EXW, FCA, FAS, FOB, CFR, CIF, CPT, CIP, DAP, DPU, DDP, etc."
            })
    if esta_vacio(puerto_carga):
        errores.append({
            "campo": "Puerto de Carga",
            "motivo": "No se especificó el puerto o lugar de carga (embarque) de la mercancía.",
            "sugerencia": "Indique el puerto o lugar de origen desde donde se embarca la mercancía."
        })
    if esta_vacio(puerto_desc):
        errores.append({
            "campo": "Puerto de Descarga",
            "motivo": "No se especificó el puerto o lugar de descarga/destino de la mercancía.",
            "sugerencia": "Indique el puerto o lugar de destino donde llegará la mercancía."
        })
    if esta_vacio(origen):
        errores.append({
            "campo": "País de Origen",
            "motivo": "No se indicó el país de origen de la mercancía.",
            "sugerencia": "Especifique el país de origen de las mercancías listadas en la factura."
        })
    if esta_vacio(pago):
        errores.append({
            "campo": "Condiciones de Pago",
            "motivo": "No se indicaron las condiciones de pago de la factura.",
            "sugerencia": "Indique las condiciones o plazo de pago acordados (por ejemplo, pago a 30 días, contra entrega, etc.)."
        })
    if esta_vacio(moneda):
        errores.append({
            "campo": "Moneda",
            "motivo": "No se especificó la moneda en que está expresada la factura.",
            "sugerencia": "Indique la moneda de la transacción (por ejemplo USD, EUR, COP)."
        })
    else:
        # Verificar que la moneda tenga un formato válido (ISO 4217 de 3 letras)
        moneda_code = str(moneda).strip()
        if not re.fullmatch(r'^[A-Za-z]{3}$', moneda_code):
            errores.append({
                "campo": "Moneda",
                "motivo": f"El valor '{moneda}' no parece un código de moneda válido.",
                "sugerencia": "Use el código de moneda de tres letras (p.ej. USD, EUR, COP) correspondiente a la divisa de la factura."
            })
    if esta_vacio(valor_total):
        errores.append({
            "campo": "Valor Total",
            "motivo": "No se indicó el valor total de la factura.",
            "sugerencia": "Incluya el valor total de la factura (suma de todos los ítems, en la moneda indicada)."
        })
    else:
        # Verificar que el valor total sea numérico
        total_num = parse_numeric(valor_total)
        if total_num is None:
            errores.append({
                "campo": "Valor Total",
                "motivo": f"El valor total '{valor_total}' no es un número válido.",
                "sugerencia": "Asegúrese de usar solo dígitos y punto/coma decimal en el valor total (ej: 12345.67)."
            })
    return errores

def validar_items(items, moneda_factura=None, total_factura=None):
    """
    Valida los campos obligatorios de cada ítem (producto) en la factura.
    'items' es una lista de diccionarios, cada uno con la información de un producto.
    'moneda_factura' es el código de moneda de la factura (para verificar consistencia en los ítems).
    'total_factura' es el valor total de la factura como número (para verificar sumatoria).
    Devuelve una lista de errores encontrados en los ítems.
    """
    errores = []
    suma_items = 0.0
    for idx, item in enumerate(items, start=1):
        # Extraer campos del producto
        desc     = item.get("Description")         # Descripción
        qty      = item.get("Quantity")            # Cantidad
        unit     = item.get("UnitOfMeasurement")   # Unidad de medida
        price    = item.get("UnitPrice")           # Precio unitario
        subtotal = item.get("NetValuePerItem")     # Valor total del ítem (subtotal)
        hs       = item.get("HSCode")              # Código HS
        weight   = item.get("Weight")              # Peso
        packages = item.get("NumberOfPackagesBoxes")  # Número de paquetes/cajas

        def esta_vacio(valor):
            """Determina si un campo de ítem está vacío o sin valor."""
            if valor is None:
                return True
            if isinstance(valor, str):
                if valor.strip() == "" or valor.strip().lower() in ["n/a", "na", "none"]:
                    return True
            return False

        # Validaciones por campo del producto
        if esta_vacio(desc):
            errores.append({
                "campo": f"Descripción (Producto {idx})",
                "motivo": "No se proporcionó la descripción del producto.",
                "sugerencia": f"Incluya una descripción detallada para el producto {idx}."
            })
        if esta_vacio(qty):
            errores.append({
                "campo": f"Cantidad (Producto {idx})",
                "motivo": "No se proporcionó la cantidad del producto.",
                "sugerencia": f"Incluya la cantidad del producto {idx} en la unidad indicada."
            })
        else:
            qty_val = parse_numeric(qty)
            if qty_val is None:
                errores.append({
                    "campo": f"Cantidad (Producto {idx})",
                    "motivo": f"La cantidad '{qty}' del producto {idx} no es numérica.",
                    "sugerencia": "Indique una cantidad numérica (solo dígitos, puede incluir decimales si aplica)."
                })
        if esta_vacio(unit):
            errores.append({
                "campo": f"Unidad (Producto {idx})",
                "motivo": "No se indicó la unidad de medida del producto.",
                "sugerencia": f"Incluya la unidad de medida (ej. Kg, piezas, cajas) para el producto {idx}."
            })
        if esta_vacio(price):
            errores.append({
                "campo": f"Precio Unitario (Producto {idx})",
                "motivo": "No se proporcionó el precio unitario del producto.",
                "sugerencia": f"Incluya el precio unitario del producto {idx} en la moneda de la factura."
            })
        else:
            price_val = parse_numeric(price)
            if price_val is None:
                errores.append({
                    "campo": f"Precio Unitario (Producto {idx})",
                    "motivo": f"El precio unitario '{price}' del producto {idx} no es un número válido.",
                    "sugerencia": "Verifique el formato; el precio unitario debe ser un valor numérico (ej: 123.45)."
                })
        if esta_vacio(subtotal):
            errores.append({
                "campo": f"Valor Total Ítem (Producto {idx})",
                "motivo": "No se proporcionó el valor total (subtotal) para el ítem.",
                "sugerencia": f"Incluya el valor total (cantidad × precio) para el producto {idx}."
            })
        else:
            subtotal_val = parse_numeric(subtotal)
            if subtotal_val is None:
                errores.append({
                    "campo": f"Valor Total Ítem (Producto {idx})",
                    "motivo": f"El valor total '{subtotal}' del producto {idx} no es un número válido.",
                    "sugerencia": "Verifique el formato; el subtotal del producto debe ser numérico."
                })
        if esta_vacio(hs):
            errores.append({
                "campo": f"Código HS (Producto {idx})",
                "motivo": "No se proporcionó el código arancelario (HS) del producto.",
                "sugerencia": f"Incluya el código HS (6 dígitos o más) correspondiente al producto {idx}."
            })
        else:
            hs_code = str(hs).strip()
            # Permitir formato con puntos (ej. "1234.56"), pero al final deben ser dígitos
            if not re.fullmatch(r'^\d+(\.\d+)*$', hs_code) or not re.fullmatch(r'^\d+$', hs_code.replace('.', '')):
                errores.append({
                    "campo": f"Código HS (Producto {idx})",
                    "motivo": f"El código HS '{hs}' del producto {idx} tiene un formato inválido.",
                    "sugerencia": "Verifique el código; debe consistir solo de números (puede separarlo en grupos con puntos)."
                })
        if esta_vacio(weight):
            errores.append({
                "campo": f"Peso (Producto {idx})",
                "motivo": "No se proporcionó el peso del producto.",
                "sugerencia": f"Incluya el peso (neto o bruto, según corresponda) del producto {idx}."
            })
        else:
            weight_val = parse_numeric(weight)
            if weight_val is None:
                errores.append({
                    "campo": f"Peso (Producto {idx})",
                    "motivo": f"El peso '{weight}' del producto {idx} no es un valor numérico válido.",
                    "sugerencia": "Verifique el valor; el peso debe ser numérico (puede incluir decimales)."
                })
        if esta_vacio(packages):
            errores.append({
                "campo": f"Número de Paquetes (Producto {idx})",
                "motivo": "No se indicó el número de paquetes o cajas del producto.",
                "sugerencia": f"Incluya la cantidad de paquetes, cajas u otras unidades de empaque para el producto {idx}."
            })
        else:
            packages_val = parse_numeric(packages)
            # Esperamos un entero para número de paquetes
            if packages_val is None or packages_val != int(packages_val):
                errores.append({
                    "campo": f"Número de Paquetes (Producto {idx})",
                    "motivo": f"El valor '{packages}' para los paquetes del producto {idx} no es un número entero válido.",
                    "sugerencia": "Verifique el número de paquetes; debe ser un número entero (ej: 1, 5, 10)."
                })
        # Verificar consistencia de moneda en el ítem (si cada ítem tiene campo moneda, debe coincidir con la moneda de la factura)
        item_currency = item.get("Currency")
        if item_currency and moneda_factura:
            if str(item_currency).strip().upper() != str(moneda_factura).strip().upper():
                errores.append({
                    "campo": f"Moneda (Producto {idx})",
                    "motivo": f"La moneda del producto {idx} ({item_currency}) difiere de la moneda de la factura ({moneda_factura}).",
                    "sugerencia": "Asegúrese de que todos los ítems estén expresados en la misma moneda que la factura."
                })
        # Acumular subtotal para comparación con total factura
        try:
            if 'subtotal_val' in locals() and subtotal_val is not None:
                suma_items += subtotal_val
            elif 'qty_val' in locals() and 'price_val' in locals() and subtotal_val is None and qty_val is not None and price_val is not None:
                # Si el subtotal no fue numérico pero cantidad y precio sí, sumamos cantidad*precio
                suma_items += (qty_val * price_val)
        except:
            # Ignorar cualquier error en acumulación
            pass
        # Verificar coherencia: cantidad × precio = subtotal (dentro de una tolerancia de centavos)
        if ('qty_val' in locals() and 'price_val' in locals() and 'subtotal_val' in locals() 
                and qty_val is not None and price_val is not None and subtotal_val is not None):
            expected_subtotal = round(qty_val * price_val, 2)
            if abs(subtotal_val - expected_subtotal) > 0.01:  # más de 0.01 de diferencia
                errores.append({
                    "campo": f"Valor Total Ítem (Producto {idx})",
                    "motivo": f"El valor total del producto {idx} ({subtotal}) no coincide con cantidad × precio unitario.",
                    "sugerencia": f"Corrija el subtotal del producto {idx}: {qty} × {price} debería ser aproximadamente {expected_subtotal:.2f}."
                })
    # Tras iterar todos los ítems, verificar suma de subtotales vs valor total de factura
    if total_factura is not None:
        suma_redondeada = round(suma_items, 2)
        if abs(suma_redondeada - total_factura) > 0.01:
            errores.append({
                "campo": "Valor Total vs Suma Ítems",
                "motivo": f"La suma de los valores de los ítems ({suma_redondeada}) no coincide con el valor total de la factura ({total_factura}).",
                "sugerencia": "Verifique que la suma de todos los subtotales de productos coincida exactamente con el valor total de la factura."
            })
    return errores

def validar_factura(data):
    """
    Realiza la validación completa de la factura comercial.
    'data' es el contenido de la factura (dict cargado desde JSON).
    Retorna un diccionario con el resultado ('Cumple' o 'No cumple') y la lista de errores.
    """
    errores_totales = []
    # Convertir lista de campos (si viene como lista) a diccionario para fácil acceso
    campos = {}
    if "Fields" in data and isinstance(data["Fields"], list):
        for item in data["Fields"]:
            # Algunos JSON podrían usar claves diferentes, cubrir opciones comunes
            key = item.get("Fields") or item.get("Field") or item.get("Nombre") or item.get("name")
            value = item.get("Value") or item.get("Valor") or item.get("value")
            if key:
                campos[key] = value
    else:
        # Si ya está en formato dict
        campos = data.get("Fields", data)
    # Obtener lista de ítems de la factura
    items = []
    if "Table" in data:
        items = data["Table"]
    elif "Items" in data:
        items = data["Items"]
    elif "Productos" in data:
        items = data["Productos"]
    # Validar campos principales y de ítems
    errores_totales.extend(validar_campos_principales(campos))
    # Obtener valor numérico del total de factura (si posible) para verificar sumas
    total_factura_val = None
    if campos.get("TotalInvoiceValue") is not None:
        total_factura_val = parse_numeric(campos.get("TotalInvoiceValue"))
    errores_totales.extend(validar_items(items, moneda_factura=campos.get("Currency"), total_factura=total_factura_val))
    # Determinar cumplimiento global
    cumple = (len(errores_totales) == 0)
    resultado_str = "Cumple" if cumple else "No cumple"
    # Preparar resultado final
    return {
        "resultado": resultado_str,
        "errores": errores_totales
    }

if __name__ == "__main__":
    # Leer parámetro de archivo JSON de factura
    if len(sys.argv) < 2:
        print("Uso: python validar_factura.py <archivo_factura.json>")
        sys.exit(1)
    archivo = sys.argv[1]
    try:
        with open(archivo, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"Error: No se encontró el archivo {archivo}")
        sys.exit(1)
    except json.JSONDecodeError:
        print(f"Error: El archivo {archivo} no es un JSON válido.")
        sys.exit(1)
    # Ejecutar validación
    resultado = validar_factura(data)
    # Mostrar resultado en consola
    if resultado["resultado"] == "Cumple":
        print("La factura cumple con los requisitos obligatorios de DIAN.")
    else:
        print("La factura NO cumple con algunos requisitos obligatorios:")
        for err in resultado["errores"]:
            campo = err.get("campo", "Campo desconocido")
            motivo = err.get("motivo", "")
            sugerencia = err.get("sugerencia", "")
            print(f"- {campo}: {motivo} " + (f"Sugerencia: {sugerencia}" if sugerencia else ""))
    # Guardar resultado en un archivo JSON de salida
    nombre_salida = archivo
    if nombre_salida.lower().endswith(".json"):
        nombre_salida = nombre_salida[:-5]  # quitar extensión .json
    nombre_salida += "_resultado.json"
    try:
        with open(nombre_salida, 'w', encoding='utf-8') as fout:
            json.dump(resultado, fout, ensure_ascii=False, indent=2)
        print(f"\nReporte de validación guardado en: {nombre_salida}")
    except Exception as e:
        print(f"Error al guardar el archivo de resultado: {e}")
