
import tkinter as tk
from tkinter import ttk, messagebox

BLANCO = "□"
LIMITE = 100


class Cinta:
    def __init__(self):
        self.celdas = {}
        self.cabezal = 0

    def leer(self):
        return self.celdas.get(self.cabezal, BLANCO)

    def leer_posicion(self, posicion):
        return self.celdas.get(posicion, BLANCO)

    def escribir(self, simbolo):
        if simbolo == BLANCO:
            self.celdas.pop(self.cabezal, None)
        else:
            self.celdas[self.cabezal] = simbolo

    def mover(self, direccion):
        if direccion == "R":
            self.cabezal += 1
        elif direccion == "L":
            self.cabezal -= 1
        elif direccion != "S":
            raise ValueError(f"Movimiento desconocido: {direccion}")

    def cargar(self, texto):
        self.celdas.clear()
        self.cabezal = 0
        for i, simbolo in enumerate(texto):
            if simbolo != BLANCO:
                self.celdas[i] = simbolo


class MaquinaTuring:
    def __init__(self, ventana):
        self.ventana = ventana
        self.ventana.title("Maquina de Turing de tres cintas")

       
        self.ventana.update_idletasks()
        ancho = self.ventana.winfo_screenwidth()
        alto = self.ventana.winfo_screenheight()

        ancho_ventana = min(1200, max(760, ancho - 40))
        alto_ventana = min(850, max(540, alto - 100))

        x = max(0, (ancho - ancho_ventana) // 2)
        y = max(0, (alto - alto_ventana) // 2)

        self.ventana.geometry(
            f"{ancho_ventana}x{alto_ventana}+{x}+{y}"
        )
        self.ventana.minsize(700, 500)
        self.ventana.protocol("WM_DELETE_WINDOW", self.cerrar)

        self.cintas = [Cinta(), Cinta(), Cinta()]
        self.estado = "q0"
        self.pasos = []
        self.indice = 0
        self.ejecutando = False
        self.after_id = None

        self.numero_a = 0
        self.numero_b = 0
        self.op = "+"
        self.resultado_finalizado = False

        self.crear_interfaz()
        self.dibujar_cintas()

    

    def crear_interfaz(self):
        principal = ttk.Frame(self.ventana, padding=8)
        principal.pack(fill="both", expand=True)

        principal.rowconfigure(2, weight=1)
        principal.columnconfigure(0, weight=1)

        ttk.Label(
            principal,
            text="MAQUINA DE TURING MULTICINTA",
            font=("Arial", 17, "bold")
        ).grid(row=0, column=0, sticky="ew", pady=(0, 6))

        # Entradas compactas.
        entrada = ttk.LabelFrame(
            principal, text="Datos de entrada", padding=8
        )
        entrada.grid(row=1, column=0, sticky="ew", pady=4)

        for columna in range(7):
            entrada.columnconfigure(columna, weight=1)

        ttk.Label(entrada, text="Numero A").grid(
            row=0, column=0, padx=3
        )
        self.a = tk.StringVar(value="7")
        ttk.Entry(
            entrada, textvariable=self.a, width=8
        ).grid(row=1, column=0, padx=3, sticky="ew")

        ttk.Label(entrada, text="Operacion").grid(
            row=0, column=1, padx=3
        )
        self.operacion = tk.StringVar(value="+")
        ttk.Combobox(
            entrada,
            textvariable=self.operacion,
            values=["+", "-", "*", "/"],
            state="readonly",
            width=5
        ).grid(row=1, column=1, padx=3, sticky="ew")

        ttk.Label(entrada, text="Numero B").grid(
            row=0, column=2, padx=3
        )
        self.b = tk.StringVar(value="3")
        ttk.Entry(
            entrada, textvariable=self.b, width=8
        ).grid(row=1, column=2, padx=3, sticky="ew")

        ttk.Button(
            entrada, text="Preparar", command=self.preparar
        ).grid(row=1, column=3, padx=4, sticky="ew")

        ttk.Button(
            entrada, text="▶ Ejecutar", command=self.iniciar
        ).grid(row=1, column=4, padx=4, sticky="ew")

        ttk.Button(
            entrada, text="Paso siguiente", command=self.paso
        ).grid(row=1, column=5, padx=4, sticky="ew")

        ttk.Button(
            entrada, text="Pausar", command=self.pausar
        ).grid(row=1, column=6, padx=4, sticky="ew")

        
        barra = ttk.Frame(principal)
        barra.grid(row=2, column=0, sticky="nsew", pady=4)
        barra.columnconfigure(0, weight=1)
        barra.rowconfigure(1, weight=1)

        info = ttk.Frame(barra)
        info.grid(row=0, column=0, sticky="ew", pady=4)

        self.estado_label = ttk.Label(
            info, text="Estado: q0", font=("Arial", 10, "bold")
        )
        self.estado_label.pack(side="left", padx=5)

        self.pasos_label = ttk.Label(info, text="Pasos: 0/0")
        self.pasos_label.pack(side="left", padx=8)

        self.resultado_label = ttk.Label(
            info, text="Resultado: —", font=("Arial", 11, "bold")
        )
        self.resultado_label.pack(side="left", padx=8)

        ttk.Label(info, text="Velocidad").pack(
            side="left", padx=(12, 3)
        )
        self.velocidad = tk.IntVar(value=400)
        ttk.Scale(
            info,
            from_=50,
            to=1200,
            variable=self.velocidad,
            orient="horizontal",
            length=110
        ).pack(side="left", padx=3)

        ttk.Button(
            info, text="Reiniciar", command=self.reiniciar
        ).pack(side="right", padx=3)

        
        self.pestanas = ttk.Notebook(barra)
        self.pestanas.grid(
            row=1, column=0, sticky="nsew", pady=4
        )

        pesta_cintas = ttk.Frame(self.pestanas, padding=8)
        pesta_reglas = ttk.Frame(self.pestanas, padding=5)
        pesta_historial = ttk.Frame(self.pestanas, padding=5)

        self.pestanas.add(pesta_cintas, text="Cintas")
        self.pestanas.add(pesta_reglas, text="Reglas de transicion")
        self.pestanas.add(pesta_historial, text="Historial")

        self.crear_panel_cintas(pesta_cintas)
        self.crear_panel_reglas(pesta_reglas)
        self.crear_panel_historial(pesta_historial)

        ttk.Label(
            principal,
            text=(
                "□ blanco | 1 unidad unaria | X marca procesada | "
                "R derecha | L izquierda | S permanecer"
            ),
            font=("Arial", 9)
        ).grid(row=3, column=0, sticky="ew", pady=(4, 0))

    def crear_panel_cintas(self, panel):
        panel.columnconfigure(0, weight=1)

        ttk.Label(
            panel,
            text="Visualizacion de las tres cintas",
            font=("Arial", 11, "bold")
        ).pack(anchor="w", pady=(0, 8))

        self.lienzos = []
        self.etiquetas_cabezal = []

        for i in range(3):
            fila = ttk.Frame(panel)
            fila.pack(fill="x", pady=8)

            ttk.Label(
                fila,
                text=f"Cinta {i + 1}",
                width=9,
                font=("Arial", 10, "bold")
            ).pack(side="left")

            lienzo = tk.Canvas(
                fila,
                height=82,
                background="white",
                highlightthickness=1,
                highlightbackground="#999999"
            )
            lienzo.pack(side="left", fill="x", expand=True)

            etiqueta = ttk.Label(
                fila, text="Cabezal: 0", width=11
            )
            etiqueta.pack(side="left", padx=5)

            self.lienzos.append(lienzo)
            self.etiquetas_cabezal.append(etiqueta)

            
            lienzo.bind(
                "<Configure>",
                lambda evento: self.dibujar_cintas()
            )

        ttk.Label(
            panel,
            text=(
                "La celda azul indica la posicion actual del cabezal. "
                "Los numeros inferiores indican las posiciones."
            ),
            wraplength=800
        ).pack(anchor="w", pady=8)

    def crear_panel_reglas(self, panel):
        panel.rowconfigure(0, weight=1)
        panel.columnconfigure(0, weight=1)

        columnas = (
            "numero", "estado", "lee", "escribe",
            "movimientos", "siguiente", "descripcion"
        )

        self.tabla_reglas = ttk.Treeview(
            panel,
            columns=columnas,
            show="headings"
        )

        encabezados = {
            "numero": "Paso",
            "estado": "Estado actual",
            "lee": "Lee C1/C2/C3",
            "escribe": "Escribe C1/C2/C3",
            "movimientos": "Movimientos",
            "siguiente": "Estado siguiente",
            "descripcion": "Accion"
        }

        anchos = {
            "numero": 45,
            "estado": 90,
            "lee": 100,
            "escribe": 110,
            "movimientos": 100,
            "siguiente": 100,
            "descripcion": 270
        }

        for columna in columnas:
            self.tabla_reglas.heading(
                columna, text=encabezados[columna]
            )
            self.tabla_reglas.column(
                columna,
                width=anchos[columna],
                minwidth=45,
                stretch=(columna == "descripcion"),
                anchor="center"
            )

        scroll_y = ttk.Scrollbar(
            panel, orient="vertical",
            command=self.tabla_reglas.yview
        )
        scroll_x = ttk.Scrollbar(
            panel, orient="horizontal",
            command=self.tabla_reglas.xview
        )

        self.tabla_reglas.configure(
            yscrollcommand=scroll_y.set,
            xscrollcommand=scroll_x.set
        )

        self.tabla_reglas.grid(
            row=0, column=0, sticky="nsew"
        )
        scroll_y.grid(row=0, column=1, sticky="ns")
        scroll_x.grid(row=1, column=0, sticky="ew")

        self.tabla_reglas.tag_configure(
            "actual", background="#bfdbfe"
        )

    def crear_panel_historial(self, panel):
        panel.rowconfigure(0, weight=1)
        panel.columnconfigure(0, weight=1)

        self.historial = tk.Text(
            panel,
            font=("Consolas", 10),
            wrap="word",
            state="disabled"
        )

        scroll_y = ttk.Scrollbar(
            panel,
            orient="vertical",
            command=self.historial.yview
        )
        scroll_x = ttk.Scrollbar(
            panel,
            orient="horizontal",
            command=self.historial.xview
        )

        self.historial.configure(
            yscrollcommand=scroll_y.set,
            xscrollcommand=scroll_x.set
        )

        self.historial.grid(
            row=0, column=0, sticky="nsew"
        )
        scroll_y.grid(row=0, column=1, sticky="ns")
        scroll_x.grid(row=1, column=0, sticky="ew")

        botones = ttk.Frame(panel)
        botones.grid(row=2, column=0, columnspan=2, sticky="ew", pady=5)

        ttk.Button(
            botones,
            text="Limpiar historial",
            command=self.limpiar_historial
        ).pack(side="left")

  

    def registrar(self, mensaje):
        self.historial.configure(state="normal")
        self.historial.insert("end", mensaje + "\n")
        self.historial.see("end")
        self.historial.configure(state="disabled")

    def limpiar_historial(self):
        self.historial.configure(state="normal")
        self.historial.delete("1.0", "end")
        self.historial.configure(state="disabled")

  

    def preparar(self):
        self.pausar()

        try:
            texto_a = self.a.get().strip()
            texto_b = self.b.get().strip()

            if not texto_a.isdecimal() or not texto_b.isdecimal():
                raise ValueError(
                    "Introduce numeros enteros no negativos."
                )

            a = int(texto_a)
            b = int(texto_b)
            op = self.operacion.get()

            if a > LIMITE or b > LIMITE:
                raise ValueError(
                    f"Los operandos deben estar entre 0 y {LIMITE}."
                )

            if op == "-" and a < b:
                raise ValueError(
                    "La resta produciria un resultado negativo."
                )

            if op == "/" and b == 0:
                raise ValueError("No se puede dividir entre cero.")

        except ValueError as error:
            messagebox.showerror("Entrada incorrecta", str(error))
            return

        self.reiniciar()

        self.numero_a = a
        self.numero_b = b
        self.op = op

        entrada_unaria = "1" * a + "#" + op + "#" + "1" * b
        self.cintas[0].cargar(entrada_unaria)
        self.cintas[1].cargar("")
        self.cintas[2].cargar("")

        self.pasos = self.generar_pasos(a, b, op)
        self.indice = 0
        self.estado = "q0"
        self.resultado_finalizado = False

        self.resultado_label.config(text="Resultado: pendiente")

        self.registrar("=== MAQUINA PREPARADA ===")
        self.registrar(f"Entrada: {a} {op} {b}")
        self.registrar(f"Cinta 1: {entrada_unaria}")
        self.registrar("Cinta 2: espacio de trabajo")
        self.registrar("Cinta 3: salida")
        self.registrar(f"Acciones planificadas: {len(self.pasos)}")
        self.registrar("")

        self.cargar_reglas_transicion()
        self.actualizar_estado()
        self.dibujar_cintas()

        self.pestanas.select(0)

   

    def generar_pasos(self, a, b, op):
        pasos = []

        def agregar(estado, descripcion, cinta=None,
                    simbolo=None, movimiento="S"):
            pasos.append(
                (estado, descripcion, cinta, simbolo, movimiento)
            )

        agregar("q0", "Iniciar y leer la entrada.")
        agregar("q1", "Recorrer el primer operando.", 0, None, "R")
        agregar("q2", "Preparar la cinta de trabajo.", 1, None, "R")
        agregar("q3", "Identificar la operacion.")
        agregar("q4", "Recorrer el segundo operando.", 0, None, "R")

        if op == "+":
            for i in range(a):
                agregar("q5", f"Copiar unidad {i + 1} de A.",
                        1, "1", "R")
            for i in range(b):
                agregar("q6", f"Copiar unidad {i + 1} de B.",
                        2, "1", "R")

        elif op == "-":
            for i in range(b):
                agregar("q5", f"Procesar unidad {i + 1} de B.",
                        1, "X", "R")
            for i in range(a - b):
                agregar("q6", f"Copiar unidad restante {i + 1}.",
                        2, "1", "R")

        elif op == "*":
            for grupo in range(b):
                agregar("q5", f"Iniciar grupo {grupo + 1}.",
                        1, None, "R")
                for marca in range(a):
                    agregar(
                        "q6",
                        f"Copiar unidad {marca + 1} del grupo {grupo + 1}.",
                        2, "1", "R"
                    )

        elif op == "/":
            cociente = a // b
            residuo = a % b

            for grupo in range(cociente):
                agregar(
                    "q5", f"Procesar grupo {grupo + 1} del divisor.",
                    1, "X", "R"
                )
                for marca in range(b):
                    agregar(
                        "q6",
                        f"Registrar unidad {marca + 1} del grupo {grupo + 1}.",
                        2, "1", "R"
                    )

            agregar("q7", f"Registrar el residuo: {residuo}.")

        agregar("qf", "Terminar la secuencia de acciones.")
        return pasos


    def cargar_reglas_transicion(self):
        for elemento in self.tabla_reglas.get_children():
            self.tabla_reglas.delete(elemento)

        estado_actual = "q0"

        for numero, paso in enumerate(self.pasos, start=1):
            estado_siguiente, descripcion, indice_cinta, simbolo, movimiento = paso

            escrituras = ["=", "=", "="]
            movimientos = ["S", "S", "S"]

            if indice_cinta is not None:
                if simbolo is not None:
                    escrituras[indice_cinta] = simbolo
                movimientos[indice_cinta] = movimiento

            self.tabla_reglas.insert(
                "",
                "end",
                iid=str(numero),
                values=(
                    numero,
                    estado_actual,
                    "* / * / *",
                    " / ".join(escrituras),
                    " / ".join(movimientos),
                    estado_siguiente,
                    descripcion
                )
            )

            estado_actual = estado_siguiente

    def resaltar_regla_actual(self):
        for elemento in self.tabla_reglas.get_children():
            self.tabla_reglas.item(elemento, tags=())

        numero = str(max(1, self.indice))

        if self.tabla_reglas.exists(numero):
            self.tabla_reglas.item(numero, tags=("actual",))
            self.tabla_reglas.selection_set(numero)
            self.tabla_reglas.focus(numero)
            self.tabla_reglas.see(numero)

   

    def iniciar(self):
        if not self.pasos:
            messagebox.showinfo("Informacion", "Pulsa Preparar primero.")
            return

        if self.indice >= len(self.pasos) or self.ejecutando:
            return

        self.ejecutando = True
        self.pestanas.select(0)
        self.ejecutar_automatico()

    def ejecutar_automatico(self):
        if not self.ejecutando:
            return

        self.ejecutar_un_paso()

        if self.ejecutando and self.indice < len(self.pasos):
            demora = max(30, int(self.velocidad.get()))
            self.after_id = self.ventana.after(
                demora, self.ejecutar_automatico
            )
        else:
            self.ejecutando = False
            self.after_id = None

    def paso(self):
        self.pausar()

        if not self.pasos:
            messagebox.showinfo("Informacion", "Pulsa Preparar primero.")
            return

        self.ejecutar_un_paso()

    def ejecutar_un_paso(self):
        if self.indice >= len(self.pasos):
            return

        estado_siguiente, descripcion, indice_cinta, simbolo, movimiento = (
            self.pasos[self.indice]
        )

        estado_anterior = self.estado
        lecturas = [cinta.leer() for cinta in self.cintas]

        escrituras = ["=", "=", "="]
        movimientos = ["S", "S", "S"]

        if indice_cinta is not None:
            cinta = self.cintas[indice_cinta]

            if simbolo is not None:
                cinta.escribir(simbolo)
                escrituras[indice_cinta] = simbolo

            movimientos[indice_cinta] = movimiento
            cinta.mover(movimiento)

        self.estado = estado_siguiente
        self.indice += 1

        self.registrar(
            f"Paso {self.indice}: {estado_anterior} -> {estado_siguiente}"
        )
        self.registrar("Lee C1/C2/C3: " + " / ".join(lecturas))
        self.registrar("Escribe: " + " / ".join(escrituras))
        self.registrar("Movimientos: " + " / ".join(movimientos))
        self.registrar("Accion: " + descripcion)
        self.registrar("")

        self.resaltar_regla_actual()
        self.actualizar_estado()
        self.dibujar_cintas()

        if self.indice >= len(self.pasos):
            self.finalizar()



    def finalizar(self):
        if self.resultado_finalizado:
            return

        a, b, op = self.numero_a, self.numero_b, self.op

        if op == "+":
            resultado = a + b
            texto = str(resultado)
        elif op == "-":
            resultado = a - b
            texto = str(resultado)
        elif op == "*":
            resultado = a * b
            texto = str(resultado)
        else:
            resultado = a // b
            residuo = a % b
            texto = f"Cociente = {resultado}, residuo = {residuo}"

        self.cintas[2].cargar("1" * resultado)
        self.cintas[2].cabezal = 0

        self.estado = "q_accept"
        self.resultado_finalizado = True

        self.resultado_label.config(text="Resultado: " + texto)
        self.registrar("=== EJECUCION FINALIZADA ===")
        self.registrar("Estado final: q_accept")
        self.registrar("Resultado: " + texto)
        self.registrar(
            "Salida unaria: " +
            ("1" * resultado if resultado > 0 else "ε (vacia)")
        )
        self.registrar("")

        self.actualizar_estado()
        self.dibujar_cintas()

        if self.ejecutando:
            self.ejecutando = False
            if self.after_id is not None:
                try:
                    self.ventana.after_cancel(self.after_id)
                except tk.TclError:
                    pass
                self.after_id = None

        self.pestanas.select(0)

    def actualizar_estado(self):
        self.estado_label.config(text=f"Estado: {self.estado}")
        self.pasos_label.config(
            text=f"Pasos: {self.indice}/{len(self.pasos)}"
        )

    def pausar(self):
        self.ejecutando = False

        if self.after_id is not None:
            try:
                self.ventana.after_cancel(self.after_id)
            except tk.TclError:
                pass

        self.after_id = None

    def reiniciar(self):
        self.pausar()

        for cinta in self.cintas:
            cinta.celdas.clear()
            cinta.cabezal = 0

        self.estado = "q0"
        self.pasos = []
        self.indice = 0
        self.resultado_finalizado = False

        self.estado_label.config(text="Estado: q0")
        self.pasos_label.config(text="Pasos: 0/0")
        self.resultado_label.config(text="Resultado: —")

        if hasattr(self, "historial"):
            self.limpiar_historial()

        if hasattr(self, "tabla_reglas"):
            for elemento in self.tabla_reglas.get_children():
                self.tabla_reglas.delete(elemento)

        self.dibujar_cintas()

   

    def dibujar_cintas(self):
        if not hasattr(self, "lienzos"):
            return

        for cinta, lienzo, etiqueta in zip(
            self.cintas, self.lienzos, self.etiquetas_cabezal
        ):
            lienzo.delete("all")

            ancho = lienzo.winfo_width()
            if ancho < 100:
                ancho = 500

            celda = 36
            cantidad = max(5, min(30, (ancho - 10) // celda))
            inicio = cinta.cabezal - cantidad // 2

            for i in range(cantidad):
                posicion = inicio + i
                x0 = 5 + i * celda
                x1 = x0 + celda - 3
                y0, y1 = 12, 46

                simbolo = cinta.leer_posicion(posicion)
                es_cabezal = posicion == cinta.cabezal

                lienzo.create_rectangle(
                    x0, y0, x1, y1,
                    fill="#bfdbfe" if es_cabezal else "white",
                    outline="#2563eb" if es_cabezal else "#94a3b8",
                    width=2 if es_cabezal else 1
                )

                lienzo.create_text(
                    (x0 + x1) / 2,
                    (y0 + y1) / 2,
                    text=simbolo,
                    font=("Consolas", 12, "bold")
                )

                lienzo.create_text(
                    (x0 + x1) / 2,
                    60,
                    text=str(posicion),
                    fill="#64748b",
                    font=("Consolas", 8)
                )

            etiqueta.config(text=f"Cabezal: {cinta.cabezal}")

    def cerrar(self):
        self.pausar()
        self.ventana.destroy()


def main():
    ventana = tk.Tk()
    MaquinaTuring(ventana)
    ventana.mainloop()


if __name__ == "__main__":
    main()
