"""Simulador educativo de una máquina de Turing determinista de una cinta."""
import tkinter as tk
import json
import csv
from tkinter import ttk, messagebox, filedialog

EJEMPLO = """# Estado Lee Escribe Movimiento Siguiente
q0 0 X R q1
q0 Y Y R q3
q0 _ _ S aceptar
q1 0 0 R q1
q1 Y Y R q1
q1 1 Y L q2
q2 0 0 L q2
q2 Y Y L q2
q2 X X R q0
q3 Y Y R q3
q3 _ _ S aceptar
"""


def leer_reglas(texto):
    reglas = {}
    for numero, linea in enumerate(texto.splitlines(), 1):
        linea = linea.split("#", 1)[0].strip()
        if not linea:
            continue
        partes = linea.split()
        if len(partes) != 5:
            raise ValueError(f"Línea {numero}: se requieren cinco campos.")
        estado, lee, escribe, movimiento, siguiente = partes
        if len(lee) != 1 or len(escribe) != 1:
            raise ValueError(f"Línea {numero}: cada símbolo debe ser un carácter.")
        if movimiento not in ("L", "R", "S"):
            raise ValueError(f"Línea {numero}: movimiento válido: L, R o S.")
        if (estado, lee) in reglas:
            raise ValueError(f"Línea {numero}: transición duplicada para {estado}, {lee}.")
        reglas[estado, lee] = (escribe, movimiento, siguiente)
    if not reglas:
        raise ValueError("Escribe al menos una transición.")
    return reglas


class Maquina:
    def __init__(self, entrada, reglas, inicial="q0", acepta="aceptar", rechaza="rechazar"):
        if not inicial or not acepta or not rechaza or acepta == rechaza:
            raise ValueError("Los estados deben tener nombre; aceptación y rechazo deben diferir.")
        self.cinta = {i: c for i, c in enumerate(entrada) if c != "_"}
        self.reglas = reglas
        self.estado, self.acepta, self.rechaza = inicial, acepta, rechaza
        self.cabezal = self.pasos = 0
        self.motivo = ""
        self.historial = []

    @property
    def resultado(self):
        if self.estado == self.acepta:
            return "ACEPTADA"
        if self.estado == self.rechaza:
            return "RECHAZADA"
        if self.motivo:
            return "DETENIDA: " + self.motivo
        return "EN EJECUCIÓN"

    @property
    def terminada(self):
        return self.estado in (self.acepta, self.rechaza) or bool(self.motivo)

    def paso(self):
        if self.terminada:
            return None
        lee = self.cinta.get(self.cabezal, "_")
        self.historial.append((self.estado, self.cabezal, lee, self.pasos, self.motivo))
        regla = self.reglas.get((self.estado, lee))
        if regla is None:
            self.motivo = f"sin regla para ({self.estado}, {lee})"
            return self.motivo
        escribe, movimiento, siguiente = regla
        mensaje = f"{self.pasos + 1}: ({self.estado}, {lee}) → ({siguiente}, {escribe}, {movimiento})"
        if escribe == "_":
            self.cinta.pop(self.cabezal, None)
        else:
            self.cinta[self.cabezal] = escribe
        self.cabezal += {"L": -1, "R": 1, "S": 0}[movimiento]
        self.estado = siguiente
        self.pasos += 1
        return mensaje

    def retroceder(self):
        if not self.historial:
            return False
        estado, posicion, simbolo, pasos, motivo = self.historial.pop()
        if simbolo == "_":
            self.cinta.pop(posicion, None)
        else:
            self.cinta[posicion] = simbolo
        self.estado, self.cabezal, self.pasos, self.motivo = estado, posicion, pasos, motivo
        return True


class Aplicacion:
    def __init__(self, root):
        self.root, self.maquina, self.ejecutando = root, None, False
        root.title("Simulador de máquina de Turing")
        root.geometry("1000x760")
        root.minsize(680, 580)
        principal = ttk.Frame(root, padding=16)
        principal.pack(fill="both", expand=True)
        ttk.Label(principal, text="MÁQUINA DE TURING", font=("Segoe UI", 20, "bold")).pack(anchor="w")
        ttk.Label(principal, text="Cinta infinita · Cabezal de lectura/escritura · Reglas editables").pack(anchor="w", pady=(0, 12))
        datos = ttk.Frame(principal)
        datos.pack(fill="x")
        self.entrada = tk.StringVar(value="0011")
        self.inicial = tk.StringVar(value="q0")
        self.acepta = tk.StringVar(value="aceptar")
        self.rechaza = tk.StringVar(value="rechazar")
        for col, (label, variable) in enumerate([
            ("Entrada", self.entrada), ("Estado inicial", self.inicial),
            ("Aceptación", self.acepta), ("Rechazo", self.rechaza)
        ]):
            ttk.Label(datos, text=label).grid(row=0, column=col, sticky="w")
            ttk.Entry(datos, textvariable=variable).grid(row=1, column=col, sticky="ew", padx=(0, 8))
            datos.columnconfigure(col, weight=1)
        self.canvas = tk.Canvas(principal, height=125, bg="#eef3fa", highlightthickness=0)
        self.canvas.pack(fill="x", pady=12)
        self.canvas.bind("<Configure>", lambda event: self.dibujar())
        self.estado = tk.StringVar()
        ttk.Label(principal, textvariable=self.estado, font=("Segoe UI", 11, "bold")).pack(anchor="w")
        botones = ttk.Frame(principal)
        botones.pack(fill="x", pady=10)
        for texto, funcion in [("Cargar / reiniciar", self.cargar), ("Paso", self.paso),
                               ("Ejecutar", self.ejecutar), ("Pausar", self.pausar)]:
            ttk.Button(botones, text=texto, command=funcion).pack(side="left", padx=(0, 5))
        self.limite = tk.StringVar(value="10000")
        ttk.Label(botones, text="Máx. pasos:").pack(side="left")
        ttk.Entry(botones, textvariable=self.limite, width=8).pack(side="left")
        self.velocidad = tk.IntVar(value=250)
        ttk.Label(principal, text="Demora entre pasos (milisegundos)").pack(anchor="w")
        tk.Scale(principal, from_=20, to=1000, orient="horizontal",
                 variable=self.velocidad).pack(fill="x")
        ttk.Label(principal, text="Reglas: estado  lee  escribe  L/R/S  siguiente.  _ = blanco; # = comentario").pack(anchor="w")
        self.reglas = tk.Text(principal, height=12, font=("Consolas", 11), undo=True)
        self.reglas.pack(fill="both", expand=True, pady=5)
        self.reglas.insert("1.0", EJEMPLO)
        ttk.Label(principal, text="Última transición").pack(anchor="w")
        self.ultimo = tk.StringVar(value="Listo.")
        ttk.Label(principal, textvariable=self.ultimo, wraplength=900).pack(anchor="w")
        ttk.Label(principal, text="Ejemplo 0ⁿ1ⁿ: acepta 01, 0011, 000111 y la cadena vacía; detiene 0101 o 001.").pack(anchor="w", pady=(8, 0))
        self.cargar()

    def cargar(self):
        self.pausar()
        try:
            nueva = Maquina(self.entrada.get(), leer_reglas(self.reglas.get("1.0", "end")),
                            self.inicial.get().strip(), self.acepta.get().strip(),
                            self.rechaza.get().strip())
        except ValueError as error:
            messagebox.showerror("Configuración inválida", str(error))
            return
        self.maquina = nueva
        self.ultimo.set("Configuración cargada. Los cambios requieren cargar de nuevo.")
        self.dibujar()

    def dibujar(self):
        if not self.maquina:
            return
        m = self.maquina
        self.canvas.delete("all")
        ancho = max(self.canvas.winfo_width(), 100)
        cantidad = max(1, int(ancho // 54))
        if cantidad % 2 == 0:
            cantidad -= 1
        inicio = m.cabezal - cantidad // 2
        offset = (ancho - cantidad * 54) / 2
        for n in range(cantidad):
            indice, x = inicio + n, offset + n * 54
            activo = indice == m.cabezal
            self.canvas.create_rectangle(x, 28, x + 50, 78,
                                         fill="#c8e4ff" if activo else "white", outline="#8294ab")
            self.canvas.create_text(x + 25, 53, text=m.cinta.get(indice, "_"), font=("Consolas", 18, "bold"))
            self.canvas.create_text(x + 25, 91, text=str(indice), fill="#566477")
            if activo:
                self.canvas.create_text(x + 25, 14, text="▼", fill="#136ac1")
        self.estado.set(f"Estado: {m.estado}   |   Cabezal: {m.cabezal}   |   Pasos: {m.pasos}   |   {m.resultado}")

    def paso(self):
        self.pausar()
        self.avanzar()

    def avanzar(self):
        if not self.maquina or self.maquina.terminada:
            return False
        try:
            limite = int(self.limite.get())
            if limite <= 0:
                raise ValueError
        except ValueError:
            self.pausar()
            messagebox.showerror("Límite inválido", "El máximo de pasos debe ser un entero positivo.")
            return False
        if self.maquina.pasos >= limite:
            self.pausar()
            self.ultimo.set("Límite alcanzado. Aumenta el máximo para continuar; no implica rechazo.")
            return False
        self.ultimo.set(self.maquina.paso())
        self.dibujar()
        return not self.maquina.terminada

    def ejecutar(self):
        if not self.ejecutando:
            self.ejecutando = True
            self.tick()

    def tick(self):
        self.tarea = None
        if self.ejecutando:
            if self.avanzar():
                self.tarea = self.root.after(self.velocidad.get(), self.tick)
            else:
                self.ejecutando = False

    def pausar(self):
        self.ejecutando = False
        if getattr(self, "tarea", None):
            self.root.after_cancel(self.tarea)
            self.tarea = None


EJEMPLOS = {
    "Igual cantidad: 0ⁿ1ⁿ": ("0011", EJEMPLO,
        "Empareja cada 0 con un 1. X e Y marcan los símbolos procesados. Acepta también la cadena vacía."),
    "Incrementar número binario": ("1011", """q0 0 0 R q0
q0 1 1 R q0
q0 _ _ L suma
suma 1 0 L suma
suma 0 1 S aceptar
suma _ 1 S aceptar
""", "Suma uno a un número binario. Ejemplo: 1011 → 1100. La entrada vacía produce 1."),
    "Invertir bits": ("101100", """q0 0 1 R q0
q0 1 0 R q0
q0 _ _ S aceptar
""", "Cambia cada 0 por 1 y cada 1 por 0. Ejemplo: 101100 → 010011."),
    "Cantidad par de unos": ("10101", """q0 0 0 R q0
q0 1 1 R impar
q0 _ _ S aceptar
impar 0 0 R impar
impar 1 1 R q0
impar _ _ S rechazar
""", "Acepta cadenas binarias con una cantidad par de unos, incluido cero.")
}


def validar_configuracion(datos):
    if not isinstance(datos, dict) or datos.get("version") != 1:
        raise ValueError("Archivo de máquina inválido o versión incompatible.")
    campos = ("entrada", "reglas", "inicial", "acepta", "rechaza")
    if any(not isinstance(datos.get(c), str) for c in campos):
        raise ValueError("Faltan campos de texto de la máquina.")
    Maquina(datos["entrada"], leer_reglas(datos["reglas"]), datos["inicial"],
            datos["acepta"], datos["rechaza"])
    return datos


class AplicacionMejorada(Aplicacion):
    def __init__(self, root):
        self.root, self.maquina, self.ejecutando = root, None, False
        self.tarea = None
        root.title("Turing Lab — Simulador educativo")
        root.geometry("1120x820")
        root.minsize(850, 690)
        root.configure(bg="#eef3fa")
        estilo = ttk.Style(root)
        estilo.theme_use("clam")
        estilo.configure("TFrame", background="#eef3fa")
        estilo.configure("TLabel", background="#eef3fa", foreground="#18304d")
        estilo.configure("TButton", padding=(10, 7))
        estilo.configure("Treeview", rowheight=27, font=("Segoe UI", 10))
        principal = ttk.Frame(root, padding=18)
        principal.pack(fill="both", expand=True)
        titulo = ttk.Frame(principal)
        titulo.pack(fill="x")
        ttk.Label(titulo, text="TURING LAB", font=("Segoe UI", 24, "bold")).pack(side="left")
        for texto, accion in [("Abrir máquina", self.abrir), ("Guardar máquina", self.guardar),
                              ("Exportar historial", self.exportar)]:
            ttk.Button(titulo, text=texto, command=accion).pack(side="right", padx=4)
        ttk.Label(principal, text="Explora cómo una máquina lee, escribe y cambia de estado.").pack(anchor="w", pady=(4, 10))
        ejemplos = ttk.Frame(principal)
        ejemplos.pack(fill="x")
        ttk.Label(ejemplos, text="Ejemplo:").pack(side="left")
        self.ejemplo = tk.StringVar(value=next(iter(EJEMPLOS)))
        selector = ttk.Combobox(ejemplos, textvariable=self.ejemplo, values=list(EJEMPLOS), state="readonly", width=32)
        selector.pack(side="left", padx=8)
        selector.bind("<<ComboboxSelected>>", self.seleccionar)
        self.descripcion = tk.StringVar(value=EJEMPLOS[self.ejemplo.get()][2])
        ttk.Label(principal, textvariable=self.descripcion, wraplength=1000).pack(anchor="w", pady=8)
        datos = ttk.Frame(principal)
        datos.pack(fill="x")
        self.entrada = tk.StringVar(value="0011")
        self.inicial, self.acepta, self.rechaza = tk.StringVar(value="q0"), tk.StringVar(value="aceptar"), tk.StringVar(value="rechazar")
        for col, (label, variable) in enumerate([("Entrada", self.entrada), ("Estado inicial", self.inicial),
                                                ("Aceptación", self.acepta), ("Rechazo", self.rechaza)]):
            ttk.Label(datos, text=label).grid(row=0, column=col, sticky="w")
            ttk.Entry(datos, textvariable=variable).grid(row=1, column=col, sticky="ew", padx=(0, 10))
            datos.columnconfigure(col, weight=1)
        self.canvas = tk.Canvas(principal, height=115, bg="#eef3fa", highlightthickness=0)
        self.canvas.pack(fill="x", pady=5)
        self.canvas.bind("<Configure>", lambda event: self.dibujar())
        self.estado, self.ultimo = tk.StringVar(), tk.StringVar()
        ttk.Label(principal, textvariable=self.estado, font=("Segoe UI", 11, "bold")).pack(anchor="w")
        self.salida = tk.StringVar()
        ttk.Label(principal, textvariable=self.salida, font=("Consolas", 11), wraplength=1000).pack(anchor="w", pady=5)
        controles = ttk.Frame(principal)
        controles.pack(fill="x")
        for texto, accion in [("Reiniciar / aplicar", self.cargar), ("← Retroceder", self.atras),
                              ("Paso →", self.paso), ("▶ Ejecutar", self.ejecutar), ("Pausar", self.pausar)]:
            ttk.Button(controles, text=texto, command=accion).pack(side="left", padx=(0, 5))
        self.limite = tk.StringVar(value="10000")
        ttk.Label(controles, text="Máx. pasos").pack(side="left", padx=5)
        ttk.Entry(controles, textvariable=self.limite, width=8).pack(side="left")
        velocidad = ttk.Frame(principal)
        velocidad.pack(fill="x", pady=5)
        ttk.Label(velocidad, text="Demora (ms):").pack(side="left")
        self.velocidad = tk.IntVar(value=250)
        tk.Scale(velocidad, from_=20, to=1000, orient="horizontal", variable=self.velocidad,
                 bg="#eef3fa", highlightthickness=0, length=300).pack(side="left")
        ttk.Label(velocidad, text="Los cambios en entrada o reglas se aplican al reiniciar.").pack(side="left", padx=12)
        tabs = ttk.Notebook(principal)
        tabs.pack(fill="both", expand=True)
        editor, historial, ayuda = ttk.Frame(tabs, padding=10), ttk.Frame(tabs, padding=10), ttk.Frame(tabs, padding=10)
        tabs.add(editor, text="  Reglas de transición  ")
        tabs.add(historial, text="  Historial de ejecución  ")
        tabs.add(ayuda, text="  Cómo funciona  ")
        ttk.Label(editor, text="Estado · Lee · Escribe · Dirección (L/R/S) · Siguiente estado").pack(anchor="w")
        zona = ttk.Frame(editor)
        zona.pack(fill="both", expand=True, pady=5)
        self.reglas = tk.Text(zona, height=9, font=("Consolas", 12), undo=True, bg="#ffffff", fg="#18304d")
        barra = ttk.Scrollbar(zona, command=self.reglas.yview)
        self.reglas.configure(yscrollcommand=barra.set)
        barra.pack(side="right", fill="y")
        self.reglas.pack(fill="both", expand=True)
        self.reglas.tag_configure("activa", background="#c8e4ff")
        self.reglas.insert("1.0", EJEMPLO)
        self.tabla = ttk.Treeview(historial, columns=("paso", "estado", "pos", "lee", "escribe", "dir", "sig"), show="headings")
        for columna, nombre in zip(self.tabla["columns"], ["Paso", "Estado", "Posición", "Lee", "Escribe", "Dirección", "Siguiente"]):
            self.tabla.heading(columna, text=nombre)
            self.tabla.column(columna, width=100, anchor="center")
        scroll = ttk.Scrollbar(historial, command=self.tabla.yview)
        self.tabla.configure(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y")
        self.tabla.pack(fill="both", expand=True)
        ttk.Label(ayuda, text=(
            "1. Selecciona un ejemplo o escribe tus propias reglas.\n"
            "2. Introduce la cadena y pulsa Reiniciar / aplicar.\n"
            "3. Usa Paso para observar una transición o Ejecutar para animarla.\n"
            "4. Retroceder deshace la última transición, incluso después de detenerse.\n\n"
            "_ representa una celda en blanco. Cada símbolo ocupa un carácter.\n"
            "L mueve a la izquierda; R a la derecha; S mantiene el cabezal.\n"
            "La cinta se extiende en ambas direcciones; la vista sigue al cabezal.\n"
            "La regla resaltada es la próxima que se aplicará.\n"
            "Sin una regla aplicable, la máquina se detiene sin declarar rechazo.\n"
            "Alcanzar el máximo de pasos solo pausa la ejecución.\n"
            "Guardar máquina conserva la configuración, no una sesión en curso.\n"
            "Exportar historial guarda las transiciones de la trayectoria actual en CSV."
        ), justify="left", wraplength=950).pack(anchor="w")
        ttk.Label(principal, textvariable=self.ultimo, wraplength=1000).pack(anchor="w", pady=(8, 0))
        root.protocol("WM_DELETE_WINDOW", self.cerrar)
        self.cargar()

    def cargar(self):
        anterior = self.maquina
        super().cargar()
        if self.maquina is not anterior:
            self.tabla.delete(*self.tabla.get_children())

    def dibujar(self):
        super().dibujar()
        if not self.maquina:
            return
        m = self.maquina
        indices = sorted(m.cinta)
        if indices:
            a, b = indices[0], indices[-1]
            fin = min(b + 1, a + 120)
            texto = "".join(m.cinta.get(i, "_") for i in range(a, fin))
            if fin <= b:
                texto += "…"
            self.salida.set(f"Cinta [{a}…{b}]: {texto}")
        else:
            self.salida.set("Cinta: vacía (todas las celdas están en blanco)")
        self.reglas.tag_remove("activa", "1.0", "end")
        if not m.terminada:
            for numero, linea in enumerate(self.reglas.get("1.0", "end").splitlines(), 1):
                partes = linea.split("#", 1)[0].split()
                if len(partes) == 5 and tuple(partes[:2]) == (m.estado, m.cinta.get(m.cabezal, "_")):
                    self.reglas.tag_add("activa", f"{numero}.0", f"{numero}.end")
                    break

    def avanzar(self):
        m = self.maquina
        antes = m.pasos
        estado, pos, lee = m.estado, m.cabezal, m.cinta.get(m.cabezal, "_")
        regla = m.reglas.get((estado, lee))
        continuar = super().avanzar()
        if m.pasos > antes:
            escribe, direccion, siguiente = regla
            item = self.tabla.insert("", "end", values=(m.pasos, estado, pos, lee, escribe, direccion, siguiente))
            self.tabla.see(item)
            verbo = {"L": "a la izquierda", "R": "a la derecha", "S": "sin desplazamiento"}[direccion]
            self.ultimo.set(f"Lee {lee}, escribe {escribe}, mueve el cabezal {verbo} y cambia de {estado} a {siguiente}.")
        return continuar

    def atras(self):
        self.pausar()
        antes = self.maquina.pasos
        if self.maquina.retroceder():
            if self.maquina.pasos < antes:
                filas = self.tabla.get_children()
                if filas:
                    self.tabla.delete(filas[-1])
            self.ultimo.set("Se restauró la configuración anterior.")
            self.dibujar()
        else:
            self.ultimo.set("Ya estás en la configuración inicial.")

    def seleccionar(self, event=None):
        self.pausar()
        entrada, reglas, descripcion = EJEMPLOS[self.ejemplo.get()]
        self.entrada.set(entrada)
        self.inicial.set("q0")
        self.acepta.set("aceptar")
        self.rechaza.set("rechazar")
        self.reglas.delete("1.0", "end")
        self.reglas.insert("1.0", reglas)
        self.descripcion.set(descripcion)
        self.cargar()

    def configuracion(self):
        return validar_configuracion(dict(version=1, entrada=self.entrada.get(),
            reglas=self.reglas.get("1.0", "end").strip(), inicial=self.inicial.get().strip(),
            acepta=self.acepta.get().strip(), rechaza=self.rechaza.get().strip()))

    def guardar(self):
        self.pausar()
        try:
            datos = self.configuracion()
            ruta = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("Máquina de Turing", "*.json")])
            if ruta:
                with open(ruta, "w", encoding="utf-8") as archivo:
                    json.dump(datos, archivo, ensure_ascii=False, indent=2)
                self.ultimo.set("Máquina guardada.")
        except (OSError, ValueError) as error:
            messagebox.showerror("No se pudo guardar", str(error))

    def abrir(self):
        self.pausar()
        ruta = filedialog.askopenfilename(filetypes=[("Máquina de Turing", "*.json")])
        if not ruta:
            return
        try:
            with open(ruta, encoding="utf-8") as archivo:
                datos = validar_configuracion(json.load(archivo))
            for campo in ("entrada", "inicial", "acepta", "rechaza"):
                getattr(self, campo).set(datos[campo])
            self.reglas.delete("1.0", "end")
            self.reglas.insert("1.0", datos["reglas"])
            self.ejemplo.set("")
            self.descripcion.set("Máquina personalizada cargada desde un archivo.")
            self.cargar()
        except (OSError, ValueError) as error:
            messagebox.showerror("No se pudo abrir", str(error))

    def exportar(self):
        self.pausar()
        ruta = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("Historial CSV", "*.csv")])
        if not ruta:
            return
        try:
            with open(ruta, "w", newline="", encoding="utf-8-sig") as archivo:
                escritor = csv.writer(archivo)
                escritor.writerow(["Paso", "Estado", "Posición", "Lee", "Escribe", "Dirección", "Siguiente"])
                for fila in self.tabla.get_children():
                    escritor.writerow(self.tabla.item(fila, "values"))
            self.ultimo.set("Historial exportado.")
        except OSError as error:
            messagebox.showerror("No se pudo exportar", str(error))

    def cerrar(self):
        self.pausar()
        self.root.destroy()


if __name__ == "__main__":
    ventana = tk.Tk()
    AplicacionMejorada(ventana)
    ventana.mainloop()
