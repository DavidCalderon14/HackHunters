// backend/static/app.js
console.log("🔥 app.js cargado correctamente");


let validations = []; // almacena resultados de todos los archivos

const jsonInput = document.getElementById("json-input");
const fileListDiv = document.getElementById("file-list");
const btnValidate = document.getElementById("btn-validate");
const btnReset = document.getElementById("btn-reset");
const statusBar = document.getElementById("validation-status");
const resultsContainer = document.getElementById("results-container");

const pdfInput = document.getElementById("pdf-input");
const btnConvertPdf = document.getElementById("btn-convert-pdf");
const pdfJsonOutput = document.getElementById("pdf-json-output");

const btnExportJson = document.getElementById("btn-export-json");
const btnExportXml = document.getElementById("btn-export-xml");
const btnExportPdf = document.getElementById("btn-export-pdf");

const btnScrollExports = document.getElementById("btn-scroll-exports");
const btnScrollSupport = document.getElementById("btn-scroll-support");

// Scroll helpers
btnScrollExports?.addEventListener("click", () => {
  document.getElementById("exports-section")?.scrollIntoView({ behavior: "smooth" });
});
btnScrollSupport?.addEventListener("click", () => {
  document.getElementById("support-section")?.scrollIntoView({ behavior: "smooth" });
});

// Mostrar lista de archivos
jsonInput?.addEventListener("change", () => {
  const files = Array.from(jsonInput.files || []);
  if (!files.length) {
    fileListDiv.textContent = "No hay archivos seleccionados.";
    return;
  }

  fileListDiv.innerHTML = "";
  files.forEach((f) => {
    const row = document.createElement("div");
    row.className = "file-item";
    row.innerHTML = `
      <i class="bx bx-file"></i>
      <span>${f.name}</span>
      <span style="margin-left:auto;opacity:.7">${(f.size / 1024).toFixed(1)} KB</span>
    `;
    fileListDiv.appendChild(row);
  });
});

// Validar archivos
btnValidate?.addEventListener("click", async () => {
  const files = Array.from(jsonInput.files || []);
  if (!files.length) {
    alert("Selecciona al menos un archivo JSON primero.");
    return;
  }

  statusBar.textContent = "Procesando archivos...";
  btnValidate.disabled = true;

  try {
    const formData = new FormData();
    files.forEach((f) => formData.append("files", f));

    const resp = await fetch("/api/validar", {
      method: "POST",
      body: formData,
    });

    if (!resp.ok) {
      throw new Error("Error en la petición al backend.");
    }

    const data = await resp.json();
    validations = (data.resultados || []).map((r) => {
      const detalle = r.detalle || {};
      const resultadoTexto = detalle.resultado || r.estado || "Sin estado";

      // "JSON corregido" de ejemplo: incluye errores como sugerencias
      const jsonCorregido = {
        archivo: r.filename,
        resultado: resultadoTexto,
        errores: detalle.errores || [],
      };

      return {
        filename: r.filename,
        estado: r.estado,
        detalle,
        jsonCorregido,
      };
    });

    renderResults();
    statusBar.textContent = `Validación completada. Archivos procesados: ${validations.length}`;
  } catch (err) {
    console.error(err);
    statusBar.textContent = "Ocurrió un error al validar los archivos.";
    alert(err.message);
  } finally {
    btnValidate.disabled = false;
  }
});

// Limpiar
btnReset?.addEventListener("click", () => {
  jsonInput.value = "";
  validations = [];
  fileListDiv.innerHTML = "No hay archivos seleccionados.";
  resultsContainer.innerHTML = "";
  statusBar.textContent = "";
});

// Render de tarjetas de resultado
function renderResults() {
  resultsContainer.innerHTML = "";

  if (!validations.length) {
    resultsContainer.innerHTML = `<p style="font-size:13px;color:#9ca3af;">No hay resultados todavía. Sube y valida archivos JSON.</p>`;
    return;
  }

  validations.forEach((item, index) => {
    const card = document.createElement("article");
    card.className = "result-card";

    const ok = (item.estado || "").toLowerCase().includes("cumple");

    const errores = item.detalle.errores || [];

    card.innerHTML = `
      <div class="result-header">
        <div class="result-header-left">
          <i class="bx ${ok ? "bx-check-circle" : "bx-error-circle"}"></i>
          <div>
            <div class="result-filename">${item.filename}</div>
            <div style="font-size:11px;opacity:.75">${ok ? "Cumple con los criterios" : "Se encontraron observaciones"}</div>
          </div>
        </div>
        <span class="result-status ${ok ? "ok" : "bad"}">
          ${item.estado}
        </span>
      </div>
      <div class="result-body">
        ${
          errores.length
            ? `<span>Errores / sugerencias:</span>
               <ul class="error-list">
                 ${errores
                   .map(
                     (e) => `
                   <li>
                     <span class="error-field">${e.campo || "Campo"}</span>: 
                     ${e.motivo || ""} 
                     ${
                       e.sugerencia
                         ? `<br/><span style="opacity:.7">Sugerencia: ${e.sugerencia}</span>`
                         : ""
                     }
                   </li>`
                   )
                   .join("")}
               </ul>`
            : `<span>Sin errores reportados por la función de validación.</span>`
        }
      </div>
      <div class="result-actions">
        <button class="btn ghost btn-download-json" data-index="${index}">
          <i class="bx bx-download"></i>
          Descargar JSON corregido
        </button>
      </div>
    `;

    resultsContainer.appendChild(card);
  });

  // Botones de descarga de JSON corregido
  document.querySelectorAll(".btn-download-json").forEach((btn) => {
    btn.addEventListener("click", () => {
      const idx = parseInt(btn.dataset.index, 10);
      descargarJsonCorregido(idx);
    });
  });
}

// Descargar JSON corregido de un archivo
function descargarJsonCorregido(index) {
  const item = validations[index];
  if (!item) return;

  const blob = new Blob([JSON.stringify(item.jsonCorregido, null, 2)], {
    type: "application/json",
  });

  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `json_corregido_${item.filename.replace(/\.[^.]+$/, "")}.json`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

// ----------------- PDF -> JSON (placeholder) -----------------
btnConvertPdf?.addEventListener("click", async () => {
  const file = pdfInput.files?.[0];
  if (!file) {
    alert("Selecciona un archivo PDF primero.");
    return;
  }

  pdfJsonOutput.textContent = "Procesando PDF...";

  try {
    const formData = new FormData();
    formData.append("file", file);

    const resp = await fetch("/api/convertir-pdf", {
      method: "POST",
      body: formData,
    });

    if (!resp.ok) throw new Error("Error al convertir el PDF.");

    const data = await resp.json();
    pdfJsonOutput.textContent = JSON.stringify(data, null, 2);
  } catch (err) {
    console.error(err);
    pdfJsonOutput.textContent =
      "Ocurrió un error al convertir el PDF. Revisa la consola.";
  }
});

// ----------------- EXPORT CONSOLIDADO JSON -----------------
btnExportJson?.addEventListener("click", () => {
  if (!validations.length) {
    alert("Aún no hay resultados para exportar.");
    return;
  }

  const payload = {
    proyecto: "Hackhunters - Validación avanzada DIAN",
    generado_en: new Date().toISOString(),
    cantidad_archivos: validations.length,
    archivos: validations.map((v) => ({
      archivo: v.filename,
      estado: v.estado,
      detalle: v.detalle,
    })),
  };

  const blob = new Blob([JSON.stringify(payload, null, 2)], {
    type: "application/json",
  });

  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = "validacion_dian_consolidado.json";
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
});

// ----------------- EXPORT CONSOLIDADO XML -----------------
btnExportXml?.addEventListener("click", () => {
  if (!validations.length) {
    alert("Aún no hay resultados para exportar.");
    return;
  }

  const esc = (str) =>
    String(str)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;");

  let xml = `<?xml version="1.0" encoding="UTF-8"?>\n<Validaciones proyecto="Hackhunters" generado="${new Date().toISOString()}">\n`;

  validations.forEach((v) => {
    xml += `  <Archivo nombre="${esc(v.filename)}" estado="${esc(v.estado)}">\n`;
    (v.detalle.errores || []).forEach((e) => {
      xml += `    <Error campo="${esc(e.campo || "")}">\n`;
      xml += `      <Motivo>${esc(e.motivo || "")}</Motivo>\n`;
      if (e.sugerencia) {
        xml += `      <Sugerencia>${esc(e.sugerencia)}</Sugerencia>\n`;
      }
      xml += `    </Error>\n`;
    });
    xml += `  </Archivo>\n`;
  });

  xml += `</Validaciones>\n`;

  const blob = new Blob([xml], { type: "application/xml" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = "validacion_dian_consolidado.xml";
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
});

// ----------------- EXPORT REPORTE PDF -----------------
btnExportPdf?.addEventListener("click", () => {
  if (!validations.length) {
    alert("Aún no hay resultados para exportar.");
    return;
  }

  const { jsPDF } = window.jspdf;
  const doc = new jsPDF();

  doc.setFontSize(14);
  doc.text("Hackhunters - Reporte de Validación DIAN", 10, 15);
  doc.setFontSize(10);
  doc.text(`Generado: ${new Date().toLocaleString()}`, 10, 22);

  let y = 30;

  validations.forEach((v, idx) => {
    if (y > 270) {
      doc.addPage();
      y = 20;
    }

    const title = `${idx + 1}. ${v.filename} [${v.estado}]`;
    doc.setFont(undefined, "bold");
    doc.text(title, 10, y);
    y += 5;

    doc.setFont(undefined, "normal");

    const errores = v.detalle.errores || [];
    if (!errores.length) {
      doc.text("- Sin errores reportados.", 12, y);
      y += 6;
    } else {
      errores.forEach((e) => {
        const line = `- ${e.campo || "Campo"}: ${e.motivo || ""}${
          e.sugerencia ? " | Sugerencia: " + e.sugerencia : ""
        }`;
        const wrapped = doc.splitTextToSize(line, 180);
        doc.text(wrapped, 12, y);
        y += wrapped.length * 4 + 2;
        if (y > 270) {
          doc.addPage();
          y = 20;
        }
      });
    }

    y += 2;
  });

  doc.save("reporte_validacion_dian.pdf");
});
