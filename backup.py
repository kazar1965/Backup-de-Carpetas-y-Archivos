#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import shutil
import threading
from pathlib import Path

try:
    import customtkinter as ctk
    from tkinter import filedialog, messagebox
except ImportError:
    print("ERROR: No tienes instalada la libreria 'customtkinter'.")
    print("   Installala ejecutando: pip install customtkinter")
    exit(1)

# Configuracion de apariencia
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")


class CopiaCarpetasApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Kazar Python: Copia de Carpetas y Archivos")
        self.geometry("850x820")
        self.resizable(False, False)

        # Variables
        self.ruta_origen = ctk.StringVar()
        self.ruta_destino = ctk.StringVar(value=str(Path.cwd()))
        self.procesando = False

        # Lista de elementos disponibles y seleccionados
        self.elementos_disponibles = []
        self.checkboxes = {}
        self.elementos_seleccionados = []

        self._crear_interfaz()

    def _crear_interfaz(self):
        """Crea toda la interfaz grafica"""
        
        # Titulo
        self.label_title = ctk.CTkLabel(
            self, 
            text="Copia de Carpetas y Archivos", 
            font=("Roboto", 22, "bold")
        )
        self.label_title.pack(pady=(15, 0))

        # Subtitulo
        self.label_subtitulo = ctk.CTkLabel(
            self, 
            text="Selecciona un directorio de origen y elige que copiar", 
            font=("Roboto", 10),
            text_color="gray"
        )
        self.label_subtitulo.pack(pady=(0, 10))

        # Frame de origen y destino (compacto)
        config_frame = ctk.CTkFrame(self)
        config_frame.pack(pady=5, padx=20, fill="x")

        # Origen
        ctk.CTkLabel(
            config_frame, 
            text="Directorio de ORIGEN:", 
            font=("Roboto", 11, "bold")
        ).pack(pady=(10, 2), anchor="w", padx=15)

        entry_origen = ctk.CTkFrame(config_frame, fg_color="transparent")
        entry_origen.pack(fill="x", padx=15, pady=2)

        self.entry_origen = ctk.CTkEntry(
            entry_origen, 
            textvariable=self.ruta_origen,
            placeholder_text="Selecciona el directorio de origen...",
            width=550
        )
        self.entry_origen.pack(side="left", padx=(0, 10))

        self.btn_origen = ctk.CTkButton(
            entry_origen, 
            text="Seleccionar Origen", 
            command=self._seleccionar_origen,
            width=150
        )
        self.btn_origen.pack(side="left")

        # Destino
        ctk.CTkLabel(
            config_frame, 
            text="Directorio de DESTINO:", 
            font=("Roboto", 11, "bold")
        ).pack(pady=(8, 2), anchor="w", padx=15)

        entry_destino = ctk.CTkFrame(config_frame, fg_color="transparent")
        entry_destino.pack(fill="x", padx=15, pady=2)

        self.entry_destino = ctk.CTkEntry(
            entry_destino, 
            textvariable=self.ruta_destino,
            placeholder_text="Selecciona el directorio de destino...",
            width=550
        )
        self.entry_destino.pack(side="left", padx=(0, 10))

        self.btn_destino = ctk.CTkButton(
            entry_destino, 
            text="Seleccionar Destino", 
            command=self._seleccionar_destino,
            width=150
        )
        self.btn_destino.pack(side="left")

        # Opciones
        opciones_frame = ctk.CTkFrame(config_frame, fg_color="transparent")
        opciones_frame.pack(fill="x", padx=15, pady=5)

        self.check_sobrescribir = ctk.CTkCheckBox(
            opciones_frame, 
            text="Sobrescribir archivos/carpetas existentes en el destino", 
            font=("Roboto", 10)
        )
        self.check_sobrescribir.pack(anchor="w")

        # Frame de lista de elementos
        lista_frame = ctk.CTkFrame(self)
        lista_frame.pack(pady=5, padx=20, fill="both", expand=True)

        ctk.CTkLabel(
            lista_frame, 
            text="Elementos disponibles (selecciona los que quieras copiar):", 
            font=("Roboto", 11, "bold")
        ).pack(pady=(8, 2), anchor="w", padx=15)

        # Scrollable frame para los elementos (REDUCIDO de 280 a 200)
        self.scroll_frame = ctk.CTkScrollableFrame(
            lista_frame, 
            width=770, 
            height=200
        )
        self.scroll_frame.pack(padx=15, pady=2, fill="both", expand=True)

        # Label cuando no hay elementos
        self.label_vacio = ctk.CTkLabel(
            self.scroll_frame, 
            text="Selecciona un directorio de origen para ver su contenido", 
            font=("Roboto", 11),
            text_color="gray"
        )
        self.label_vacio.pack(pady=40)

        # Botones de seleccion rapida
        botones_sel = ctk.CTkFrame(lista_frame, fg_color="transparent")
        botones_sel.pack(fill="x", padx=15, pady=2)

        self.btn_todas = ctk.CTkButton(
            botones_sel, 
            text="Seleccionar Todas", 
            command=self._seleccionar_todas,
            width=140,
            fg_color="#00bcd4",
            state="disabled"
        )
        self.btn_todas.pack(side="left", padx=5)

        self.btn_ninguna = ctk.CTkButton(
            botones_sel, 
            text="Deseleccionar Todas", 
            command=self._deseleccionar_todas,
            width=140,
            fg_color="#ff5f57",
            state="disabled"
        )
        self.btn_ninguna.pack(side="left", padx=5)

        # Info de seleccion
        self.label_info = ctk.CTkLabel(
            lista_frame, 
            text="Elementos seleccionados: 0", 
            font=("Roboto", 11, "bold"),
            text_color="gray"
        )
        self.label_info.pack(pady=(2, 5), anchor="w", padx=15)

        # Boton de copia
        self.btn_copiar = ctk.CTkButton(
            self, 
            text="Iniciar Copia", 
            command=self._iniciar_copia,
            fg_color="green",
            hover_color="darkgreen",
            font=("Roboto", 15, "bold"),
            height=40
        )
        self.btn_copiar.pack(pady=8)

        # Barra de progreso
        self.progress = ctk.CTkProgressBar(self, width=750)
        self.progress.set(0)
        self.progress.pack(pady=3)

        # Label de estado
        self.label_estado = ctk.CTkLabel(
            self, 
            text="Listo para copiar", 
            font=("Roboto", 11)
        )
        self.label_estado.pack(pady=2)

        # Log de actividad (REDUCIDO de 120 a 90)
        self.log_text = ctk.CTkTextbox(self, width=800, height=90, font=("Consolas", 9))
        self.log_text.pack(pady=5)
        self.log_text.insert("0.0", "Copia de Carpetas y Archivos - Kazar Python Hub\n")
        self.log_text.insert("end", "Selecciona un directorio de origen para comenzar.\n\n")

    def _seleccionar_origen(self):
        """Abre el dialogo para seleccionar directorio de origen"""
        ruta = filedialog.askdirectory(
            title="Seleccionar directorio de origen"
        )
        
        if ruta:
            self.ruta_origen.set(ruta)
            self._log(f"Origen seleccionado: {ruta}")
            self._cargar_elementos(ruta)

    def _seleccionar_destino(self):
        """Abre el dialogo para seleccionar directorio de destino"""
        ruta = filedialog.askdirectory(
            title="Seleccionar directorio de destino"
        )
        
        if ruta:
            self.ruta_destino.set(ruta)
            self._log(f"Destino seleccionado: {ruta}")

    def _cargar_elementos(self, ruta):
        """Carga todos los elementos (carpetas y archivos) del directorio"""
        # Limpiar checkboxes anteriores
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()
        self.checkboxes.clear()
        self.elementos_disponibles.clear()

        try:
            directorio = Path(ruta)
            items = list(directorio.iterdir())
            
            # Separar carpetas y archivos, ordenados
            carpetas = sorted([
                item for item in items if item.is_dir()
            ], key=lambda x: x.name.lower())
            
            archivos = sorted([
                item for item in items if item.is_file()
            ], key=lambda x: x.name.lower())

            # Combinar: primero carpetas, luego archivos
            self.elementos_disponibles = carpetas + archivos

            if not self.elementos_disponibles:
                self.label_vacio = ctk.CTkLabel(
                    self.scroll_frame, 
                    text="El directorio esta vacio", 
                    font=("Roboto", 11),
                    text_color="gray"
                )
                self.label_vacio.pack(pady=40)
                self._log("El directorio esta vacio.")
                return

            # Crear checkboxes para cada elemento
            for elemento in self.elementos_disponibles:
                # Icono segun tipo
                if elemento.is_dir():
                    icono = "[CARPETA] "
                else:
                    icono = "[ARCHIVO] "
                
                var = ctk.BooleanVar(value=False)
                cb = ctk.CTkCheckBox(
                    self.scroll_frame, 
                    text=icono + elemento.name, 
                    variable=var,
                    font=("Roboto", 10),
                    command=self._actualizar_contador
                )
                cb.pack(anchor="w", padx=10, pady=1)
                self.checkboxes[elemento.name] = {
                    'var': var,
                    'path': elemento,
                    'tipo': 'carpeta' if elemento.is_dir() else 'archivo'
                }

            # Habilitar botones
            self.btn_todas.configure(state="normal")
            self.btn_ninguna.configure(state="normal")

            num_carpetas = len(carpetas)
            num_archivos = len(archivos)
            self._log(f"Se encontraron {num_carpetas} carpetas y {num_archivos} archivos.")
            self._actualizar_contador()
            
        except Exception as e:
            self._log(f"Error al cargar elementos: {e}")

    def _seleccionar_todas(self):
        """Selecciona todos los elementos"""
        for info in self.checkboxes.values():
            info['var'].set(True)
        self._actualizar_contador()

    def _deseleccionar_todas(self):
        """Deselecciona todos los elementos"""
        for info in self.checkboxes.values():
            info['var'].set(False)
        self._actualizar_contador()

    def _actualizar_contador(self):
        """Actualiza el contador de elementos seleccionados"""
        seleccionados = sum(1 for info in self.checkboxes.values() if info['var'].get())
        self.label_info.configure(
            text=f"Elementos seleccionados: {seleccionados}",
            text_color="cyan" if seleccionados > 0 else "gray"
        )

    def _log(self, mensaje):
        """Anade un mensaje al log de forma thread-safe"""
        self.after(0, lambda: self._log_threadsafe(mensaje))

    def _log_threadsafe(self, mensaje):
        """Inserta texto en el log de forma segura para threads"""
        self.log_text.insert("end", mensaje + "\n")
        self.log_text.see("end")

    def _obtener_tamano(self, ruta):
        """Calcula el tamano de un archivo o carpeta en MB"""
        try:
            if ruta.is_file():
                return ruta.stat().st_size / (1024 * 1024)
            elif ruta.is_dir():
                total = 0
                for archivo in ruta.rglob("*"):
                    if archivo.is_file():
                        total += archivo.stat().st_size
                return total / (1024 * 1024)
        except:
            pass
        return 0

    def _iniciar_copia(self):
        """Inicia el proceso de copia en un hilo separado"""
        if self.procesando:
            self._log("Ya hay un proceso en ejecucion...")
            return

        # Obtener elementos seleccionados
        self.elementos_seleccionados = [
            (nombre, info) for nombre, info in self.checkboxes.items() 
            if info['var'].get()
        ]

        if not self.elementos_seleccionados:
            messagebox.showwarning(
                "Advertencia", 
                "Por favor, selecciona al menos un elemento para copiar."
            )
            return

        # Validar origen
        ruta_origen = Path(self.ruta_origen.get().strip())
        if not ruta_origen.exists() or not ruta_origen.is_dir():
            messagebox.showerror(
                "Error", 
                "El directorio de origen no existe o no es valido."
            )
            return

        # Validar destino
        ruta_destino = Path(self.ruta_destino.get().strip())
        if not ruta_destino.exists() or not ruta_destino.is_dir():
            messagebox.showerror(
                "Error", 
                "El directorio de destino no existe o no es valido."
            )
            return

        # Verificar que origen y destino no sean el mismo
        if ruta_origen.resolve() == ruta_destino.resolve():
            messagebox.showerror(
                "Error", 
                "El directorio de origen y destino no pueden ser el mismo."
            )
            return

        # Deshabilitar controles
        self.procesando = True
        self.btn_copiar.configure(state="disabled", text="Copiando...")
        self.btn_origen.configure(state="disabled")
        self.btn_destino.configure(state="disabled")
        self.btn_todas.configure(state="disabled")
        self.btn_ninguna.configure(state="disabled")
        self.check_sobrescribir.configure(state="disabled")
        for widget in self.scroll_frame.winfo_children():
            if isinstance(widget, ctk.CTkCheckBox):
                widget.configure(state="disabled")
        
        self.progress.set(0)
        self.log_text.delete("0.0", "end")

        # Iniciar hilo
        hilo = threading.Thread(
            target=self._ejecutar_copia, 
            args=(ruta_origen, ruta_destino)
        )
        hilo.daemon = True
        hilo.start()

    def _ejecutar_copia(self, ruta_origen, ruta_destino):
        """Ejecuta la copia en segundo plano"""
        total = len(self.elementos_seleccionados)
        exitosos = 0
        fallidos = 0
        omitidos = 0

        self._log("=" * 50)
        self._log("INICIANDO COPIA DE ELEMENTOS")
        self._log("=" * 50)
        self._log(f"Origen: {ruta_origen}")
        self._log(f"Destino: {ruta_destino}")
        self._log(f"Total de elementos: {total}")
        self._log("")

        for i, (nombre, info) in enumerate(self.elementos_seleccionados, 1):
            elemento_origen = info['path']
            elemento_destino = ruta_destino / nombre
            tipo = info['tipo']

            # Actualizar estado
            msg = f"[{i}/{total}] {nombre}"
            self.after(0, lambda m=msg: 
                      self.label_estado.configure(text=m))
            
            # Actualizar progreso
            progreso = (i - 1) / total
            self.after(0, lambda p=progreso: self.progress.set(p))

            self._log(f"------------------------------")
            self._log(f"[{i}/{total}] Copiando: {nombre} ({tipo})")

            # Calcular tamano
            tamano_mb = self._obtener_tamano(elemento_origen)
            self._log(f"   Tamano: {tamano_mb:.2f} MB")

            # Verificar si ya existe
            if elemento_destino.exists():
                if self.check_sobrescribir.get():
                    self._log(f"   Ya existe. Sobrescribiendo...")
                    try:
                        if tipo == 'carpeta':
                            shutil.rmtree(elemento_destino)
                        else:
                            elemento_destino.unlink()
                    except Exception as e:
                        self._log(f"   ERROR al eliminar: {e}")
                        fallidos += 1
                        continue
                else:
                    self._log(f"   Ya existe. Omitiendo...")
                    omitidos += 1
                    continue

            # Copiar elemento
            try:
                self._log(f"   Copiando...")
                if tipo == 'carpeta':
                    shutil.copytree(
                        str(elemento_origen), 
                        str(elemento_destino)
                    )
                else:
                    shutil.copy2(
                        str(elemento_origen), 
                        str(elemento_destino)
                    )
                self._log(f"   Copia correcta!")
                exitosos += 1
            except PermissionError:
                self._log(f"   ERROR: No tienes permisos.")
                fallidos += 1
            except Exception as e:
                self._log(f"   ERROR: {e}")
                fallidos += 1

            self._log("")

        # Actualizar progreso al 100%
        self.after(0, lambda: self.progress.set(1.0))

        # Resumen final
        self._log("")
        self._log("=" * 50)
        self._log("RESUMEN FINAL")
        self._log("=" * 50)
        self._log(f"Total procesados: {total}")
        self._log(f"Exitosos: {exitosos}")
        self._log(f"Omitidos: {omitidos}")
        self._log(f"Fallidos: {fallidos}")
        self._log("=" * 50)
        self._log("COPIA COMPLETADA")
        self._log("=" * 50)

        # Reactivar controles
        self.after(0, lambda: self.btn_copiar.configure(
            state="normal", text="Iniciar Copia"
        ))
        self.after(0, lambda: self.btn_origen.configure(state="normal"))
        self.after(0, lambda: self.btn_destino.configure(state="normal"))
        self.after(0, lambda: self.btn_todas.configure(state="normal"))
        self.after(0, lambda: self.btn_ninguna.configure(state="normal"))
        self.after(0, lambda: self.check_sobrescribir.configure(state="normal"))
        for widget in self.scroll_frame.winfo_children():
            if isinstance(widget, ctk.CTkCheckBox):
                widget.configure(state="normal")
        self.after(0, lambda: self.label_estado.configure(
            text="Copia completada"
        ))
        self.procesando = False


if __name__ == "__main__":
    try:
        app = CopiaCarpetasApp()
        app.mainloop()
    except Exception as e:
        print(f"\nERROR CRITICO: {e}")
        import traceback
        traceback.print_exc()
        input("\nPresiona ENTER para cerrar...")