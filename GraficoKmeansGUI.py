# --- Librerías para la Ejecución del Sistema e Interfaz Gráfica ---
import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext

# --- Librerías para Minería de Datos y Visualización ---
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from sklearn.cluster import KMeans

class GraficoKmeansGUI:
    """
    Clase que gestiona la interfaz gráfica y la lógica del análisis K-Means.
    """
    def __init__(self, root):
        """
        Constructor de la clase.
        Inicializa la ventana principal, variables de estado y configura la interfaz.
        """
        self.root = root
        self.root.title("Análisis de Clusters K-Means")
        self.root.geometry("1200x800")

        pd.set_option('display.float_format', lambda x: '{:,.2f}'.format(x))

        self.df = None
        self.df_clean = None
        self.kmeans_models = {}

        self.setup_ui()

    def setup_ui(self):
        """
        Configura y distribuye todos los elementos visuales de la interfaz gráfica.
        """
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        control_frame = ttk.LabelFrame(main_frame, text="Menú de Operaciones", padding="10")
        control_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))

        ttk.Button(control_frame, text="1. Cargar Datos", command=self.cargar_datos).pack(fill=tk.X, pady=5)
        ttk.Button(control_frame, text="2. Limpiar Datos", command=self.limpiar_datos).pack(fill=tk.X, pady=5)
        ttk.Button(control_frame, text="3. Analizar Clusters (K-Means)", command=self.analizar_clusters_gui).pack(fill=tk.X, pady=5)
        ttk.Separator(control_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=10)
        ttk.Button(control_frame, text="Salir", command=self.root.quit).pack(fill=tk.X, pady=5)

        content_frame = ttk.Frame(main_frame)
        content_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        self.notebook = ttk.Notebook(content_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        self.tab_data = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_data, text="Vista de Datos")
        
        self.tree = ttk.Treeview(self.tab_data)
        scrollbar = ttk.Scrollbar(self.tab_data, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.tab_graphs = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_graphs, text="Gráficos")
        self.graph_frame = ttk.Frame(self.tab_graphs)
        self.graph_frame.pack(fill=tk.BOTH, expand=True)

        log_frame = ttk.LabelFrame(content_frame, text="Detalle del Proceso / Logs", padding="5")
        log_frame.pack(fill=tk.X, side=tk.BOTTOM)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=10, state='disabled', font=("Consolas", 10))
        self.log_text.pack(fill=tk.BOTH, expand=True)

    def log(self, message):
        """Agrega un mensaje al panel de logs."""
        self.log_text.config(state='normal')
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.log_text.config(state='disabled')

    def update_treeview(self, dataframe):
        """Actualiza la tabla con los datos de un DataFrame.
        Asegura numeración única y evita conflictos si el DataFrame ya trae una columna 'N°'.
        """
        # Copia para no mutar el original
        df_view = dataframe.copy()
        # Evitar duplicidad si ya existiera una columna llamada 'N°'
        if 'N°' in df_view.columns:
            df_view.drop(columns=['N°'], inplace=True)

        # Limpieza previa de filas del tree
        self.tree.delete(*self.tree.get_children())

        # Definir columnas (numeral + columnas del DF)
        cols = ["N°"] + list(df_view.columns)
        self.tree["columns"] = cols
        self.tree["show"] = "headings"

        # Configurar columna de numeración
        self.tree.heading("N°", text="N°")
        self.tree.column("N°", width=50, anchor="center")

        # Configurar resto de columnas
        for col in df_view.columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=100, anchor="center")

        # Insertar filas con número secuencial real
        for i, (_, row) in enumerate(df_view.iterrows(), start=1):
            self.tree.insert("", "end", values=[i] + list(row))

    def clear_graph(self):
        """Limpia el área de gráficos."""
        for widget in self.graph_frame.winfo_children():
            widget.destroy()

    def cargar_datos(self):
        """
        Paso 1: Carga de Datos.
        Intenta cargar un archivo Excel y normaliza columnas relevantes.
        Si no, carga datos de prueba.
        """
        self.log("--- 1. CARGA DE DATOS ---")
        # Preferimos el archivo existente en el directorio
        archivo_defecto = 'Propiedades_Precios.xlsx'
        archivo = None
        
        if os.path.exists(archivo_defecto):
            respuesta = messagebox.askyesno("Archivo encontrado", f"Se encontró '{archivo_defecto}'. ¿Desea cargarlo?")
            if respuesta:
                archivo = archivo_defecto
        
        if not archivo:
            archivo = filedialog.askopenfilename(filetypes=[("Excel files", "*.xlsx *.xlsm *.xls")])
        
        if archivo:
            try:
                self.df = pd.read_excel(archivo)
                self.log(f"✅ Archivo '{os.path.basename(archivo)}' cargado exitosamente.")
                # Renombrado inteligente de columnas según diferentes fuentes
                column_map = {
                    'precio_usd': 'Valor',
                    'metros_cuad': 'Superficie',
                    'precio': 'Valor',
                    'superficietotal_pies2': 'Superficie',
                }
                existentes = {k: v for k, v in column_map.items() if k in self.df.columns}
                if existentes:
                    self.df.rename(columns=existentes, inplace=True)
                    self.log("ℹ️  Columnas relevantes renombradas a 'Valor' y 'Superficie'.")
                else:
                    self.log("⚠️  No se encontraron columnas esperadas para 'Valor'/'Superficie'. Use el botón 'Limpiar Datos' solo si las columnas existen o seleccione otro archivo.")
            except Exception as e:
                self.log(f"❌ Error al cargar el archivo: {e}")
                messagebox.showerror("Error de Carga", f"No se pudo cargar el archivo:\n{e}")
                return
        else:
            self.log("⚠️  No se seleccionó archivo. Generando datos de prueba para demostración...")
            # Generamos datos aleatorios simulando 3 grupos naturales
            np.random.seed(42)
            # Grupo Económico
            g1_sup = np.random.normal(60, 15, 100)
            g1_val = g1_sup * 1500 + np.random.normal(0, 5000, 100)
            # Grupo Medio
            g2_sup = np.random.normal(120, 20, 100)
            g2_val = g2_sup * 2200 + np.random.normal(0, 10000, 100)
            # Grupo Lujo
            g3_sup = np.random.normal(250, 40, 100)
            g3_val = g3_sup * 3500 + np.random.normal(0, 20000, 100)
            
            self.df = pd.DataFrame({
                'Superficie': np.concatenate([g1_sup, g2_sup, g3_sup]),
                'Valor': np.concatenate([g1_val, g2_val, g3_val])
            })
            self.log(f"Datos de prueba generados: {self.df.shape[0]} registros.")

        self.update_treeview(self.df)
        self.log("\n--- Estadísticas Iniciales ---")
        self.log(str(self.df.describe()))
        self.notebook.select(self.tab_data)

    def limpiar_datos(self):
        """
        Paso 2: Limpieza de Datos.
        Elimina registros con valores nulos y outliers para mejorar el análisis.
        """
        if self.df is None:
            messagebox.showerror("Error", "Primero debe cargar los datos.")
            return

        if 'Superficie' not in self.df.columns or 'Valor' not in self.df.columns:
            messagebox.showerror("Error de Columnas", "El DataFrame no contiene las columnas 'Superficie' y/o 'Valor'.\nAsegúrese de que el archivo cargado tenga las columnas correctas (ej: 'metros_cuad', 'precio_usd') o que los datos de prueba se generaron correctamente.")
            return

        self.log("\n--- 2. LIMPIEZA DE DATOS ---")
        self.log("Iniciando proceso de limpieza para asegurar la calidad de los datos:")
        self.log(" 1. Se eliminarán filas con valores nulos (NaN).")
        self.log(" 2. Se descartarán registros con valores ilógicos (Superficie <= 10 o Valor <= 0).")
        self.log(" 3. Se filtrarán outliers o valores atípicos (Superficie >= 1000 m²).")
        self.log(" 4. Se eliminarán filas duplicadas (exactas) si existen.")
        self.log(" 5. Validaciones de consistencia de superficies según reglas de negocio:")
        self.log("    • F (superficieliving_pies2) ≈ M + N (base + arriba)")
        self.log("    • F (superficieliving_pies2) <= G (superficietotal_pies2)")
        self.log("    • Si H (nro_pisos) == 1 entonces N (superficie_arriba_pies2) ≈ 0")
        self.log("-" * 60)
        
        conteo_inicial = self.df.shape[0]
        
        # Limpieza (Crucial para K-Means)
        self.df_clean = self.df.dropna().copy()
        nulos_eliminados = conteo_inicial - self.df_clean.shape[0]

        # Detección y eliminación de duplicados (exactos)
        duplicados_totales = self.df_clean.duplicated().sum()
        self.df_clean = self.df_clean.drop_duplicates()
        tras_eliminar_dup_exactos = self.df_clean.shape[0]
        duplicados_eliminados = (conteo_inicial - nulos_eliminados) - tras_eliminar_dup_exactos

        # Duplicados por id casa: conservar el registro más reciente por 'fecha' si ambas columnas existen
        duplicados_id = 0
        if {'id casa', 'fecha'}.issubset(self.df_clean.columns):
            # Normalizar fecha a datetime para ordenar correctamente
            df_tmp = self.df_clean.copy()
            df_tmp['__fecha_dt'] = pd.to_datetime(df_tmp['fecha'], errors='coerce')
            antes = df_tmp.shape[0]
            df_tmp.sort_values(['id casa', '__fecha_dt'], ascending=[True, False], inplace=True)
            df_tmp = df_tmp.drop_duplicates(subset=['id casa'], keep='first')
            duplicados_id = antes - df_tmp.shape[0]
            self.df_clean = df_tmp.drop(columns=['__fecha_dt'])

        # Coerción a numérico de precio y pisos para detectar errores de fórmula o texto
        if 'Valor' in self.df_clean.columns:
            self.df_clean['Valor'] = pd.to_numeric(self.df_clean['Valor'], errors='coerce')
        if 'nro_pisos' in self.df_clean.columns:
            self.df_clean['nro_pisos'] = pd.to_numeric(self.df_clean['nro_pisos'], errors='coerce')

        temp_len = self.df_clean.shape[0]
        self.df_clean = self.df_clean[(self.df_clean['Superficie'] > 10) & (self.df_clean['Valor'] > 0)]
        logicos_eliminados = temp_len - self.df_clean.shape[0]

        # Pisos negativos (regla: nro_pisos >= 0)
        pisos_eliminados = 0
        if 'nro_pisos' in self.df_clean.columns:
            temp_len = self.df_clean.shape[0]
            self.df_clean = self.df_clean[self.df_clean['nro_pisos'] >= 0]
            pisos_eliminados = temp_len - self.df_clean.shape[0]

        # Validaciones de consistencia basadas en columnas del Excel si existen
        cons_inconsistentes = 0
        cons_restr_total = 0
        cons_pisos = 0
        tol = 1e-6
        cols = self.df_clean.columns
        # F = superficieliving_pies2, M = superficie_base_pies2, N = superficie_arriba_pies2
        if {'superficieliving_pies2', 'superficie_base_pies2', 'superficie_arriba_pies2'}.issubset(cols):
            mask_sum = (self.df_clean['superficieliving_pies2'] - (self.df_clean['superficie_base_pies2'] + self.df_clean['superficie_arriba_pies2'])).abs() <= tol
            cons_inconsistentes = (~mask_sum).sum()
            self.df_clean = self.df_clean[mask_sum]

        # F <= G (superficietotal_pies2)
        if {'superficieliving_pies2', 'superficietotal_pies2'}.issubset(cols):
            mask_total = self.df_clean['superficieliving_pies2'] <= self.df_clean['superficietotal_pies2']
            cons_restr_total = (~mask_total).sum()
            self.df_clean = self.df_clean[mask_total]

        # Si H (nro_pisos) == 1 => N ≈ 0
        if {'nro_pisos', 'superficie_arriba_pies2'}.issubset(cols):
            mask_pisos = ~((self.df_clean['nro_pisos'] == 1) & (self.df_clean['superficie_arriba_pies2'].abs() > tol))
            cons_pisos = (~mask_pisos).sum()
            self.df_clean = self.df_clean[mask_pisos]

        # Filtrado de outliers para mejor visualización
        # Detectar precios ilógicos mediante precio por superficie total (IQR)
        outliers_ilogicos = 0
        if {'Valor', 'Superficie'}.issubset(self.df_clean.columns):
            # Evitar división por cero
            df_pps = self.df_clean[self.df_clean['Superficie'] > 0].copy()
            df_pps['precio_por_superficie'] = df_pps['Valor'] / df_pps['Superficie']
            q1 = df_pps['precio_por_superficie'].quantile(0.25)
            q3 = df_pps['precio_por_superficie'].quantile(0.75)
            iqr = q3 - q1
            low = q1 - 1.5 * iqr
            high = q3 + 1.5 * iqr
            mask_pps = (df_pps['precio_por_superficie'] >= low) & (df_pps['precio_por_superficie'] <= high)
            outliers_ilogicos = (~mask_pps).sum()
            self.df_clean = df_pps[mask_pps].drop(columns=['precio_por_superficie'])

        # Outliers por tamaño extremo de superficie usando percentiles (1%-99%) para no sesgar por unidades
        outliers_eliminados = 0
        if 'Superficie' in self.df_clean.columns and self.df_clean.shape[0] > 0:
            q01 = self.df_clean['Superficie'].quantile(0.01)
            q99 = self.df_clean['Superficie'].quantile(0.99)
            temp_len = self.df_clean.shape[0]
            self.df_clean = self.df_clean[(self.df_clean['Superficie'] >= q01) & (self.df_clean['Superficie'] <= q99)]
            outliers_eliminados = temp_len - self.df_clean.shape[0]
        
        conteo_final = self.df_clean.shape[0]
        
        self.log(f"Registros originales: {conteo_inicial}")
        self.log(f"Eliminados por nulos: {nulos_eliminados}")
        self.log(f"Duplicados detectados (exactos): {duplicados_totales}")
        if 'id casa' in self.df.columns:
            self.log(f"Duplicados por 'id casa': {duplicados_id}")
        self.log(f"Eliminados por duplicados: {duplicados_eliminados}")
        self.log(f"Eliminados por valores ilógicos (Sup <= 10 o Valor <= 0): {logicos_eliminados}")
        if 'nro_pisos' in self.df.columns:
            self.log(f"Pisos < 0 eliminados: {pisos_eliminados}")
        self.log(f"Precio/superficie fuera de rango (IQR) eliminados: {outliers_ilogicos}")
        if {'superficieliving_pies2', 'superficie_base_pies2', 'superficie_arriba_pies2'}.issubset(self.df.columns):
            self.log(f"Eliminados por inconsistencia F != M+N: {cons_inconsistentes}")
        if {'superficieliving_pies2', 'superficietotal_pies2'}.issubset(self.df.columns):
            self.log(f"Eliminados por F > G (living > total): {cons_restr_total}")
        if {'nro_pisos', 'superficie_arriba_pies2'}.issubset(self.df.columns):
            self.log(f"Eliminados por pisos=1 con arriba>0: {cons_pisos}")
        self.log(f"Eliminados por outliers Superficie (1%-99%): {outliers_eliminados}")
        self.log(f"Registros finales: {conteo_final}")
        
        self.update_treeview(self.df_clean)
        self.log("✅ Datos limpios actualizados en la tabla.")
        self.log("\n--- Estadísticas Después de Limpieza ---")
        self.log(str(self.df_clean.describe()))

        # Resumen compacto
        self.log("\n=== Resumen de Limpieza ===")
        self.log(f"Total inicial: {conteo_inicial} | Final: {conteo_final}")
        self.log(f"Nulos: {nulos_eliminados} | Duplicados exactos: {duplicados_eliminados} | Duplicados por id: {duplicados_id}")
        self.log(f"Ilógicos (Sup<=10 o Valor<=0): {logicos_eliminados}")
        if 'nro_pisos' in self.df.columns:
            self.log(f"Pisos < 0: {pisos_eliminados}")
        self.log(f"Precio/superficie (IQR): {outliers_ilogicos}")
        if {'superficieliving_pies2', 'superficie_base_pies2', 'superficie_arriba_pies2'}.issubset(self.df.columns):
            self.log(f"Consistencia F≈M+N eliminados: {cons_inconsistentes}")
        if {'superficieliving_pies2', 'superficietotal_pies2'}.issubset(self.df.columns):
            self.log(f"Restricción F≤G eliminados: {cons_restr_total}")
        if {'nro_pisos', 'superficie_arriba_pies2'}.issubset(self.df.columns):
            self.log(f"Pisos=1 con arriba>0 eliminados: {cons_pisos}")
        self.log(f"Outliers Superficie (1%-99%): {outliers_eliminados}")
        self.log("===========================\n")

    def analizar_clusters_gui(self):
        """
        Paso 3: Ejecución Comparativa de Clusters (K-Means).
        Muestra gráficos para K=2, 3 y 4 y el método del codo.
        """
        if self.df_clean is None:
            messagebox.showerror("Error", "Primero debe limpiar los datos.")
            return

        self.log("\n--- 3. ANÁLISIS COMPARATIVO DE CLUSTERS (K-MEANS) ---")
        X = self.df_clean[['Superficie', 'Valor']]
        inercias = []
        k_ranges = [2, 3, 4]

        self.clear_graph()

        # --- Contenedor para los dos gráficos ---
        container = ttk.Frame(self.graph_frame)
        container.pack(fill=tk.BOTH, expand=True)

        # --- Gráfico Comparativo de K-Means ---
        fig_clusters, axes = plt.subplots(1, 3, figsize=(18, 5))
        fig_clusters.suptitle('Comparación de K-Means con K=2, 3, 4', fontsize=14)

        for i, k in enumerate(k_ranges):
            kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
            kmeans.fit(X)
            labels = kmeans.labels_
            centroides = kmeans.cluster_centers_
            inercias.append(kmeans.inertia_)
            self.kmeans_models[k] = kmeans

            ax = axes[i]
            ax.scatter(self.df_clean['Superficie'], self.df_clean['Valor'], c=labels, cmap='viridis', alpha=0.6)
            ax.scatter(centroides[:, 0], centroides[:, 1], c='red', s=200, marker='X', label='Centroides')
            ax.set_title(f'K = {k}')
            ax.set_xlabel('Superficie (m²)')
            ax.set_ylabel('Valor ($)')
            ax.legend()
            ax.grid(True)
            
            self.log(f"\n--- Análisis con K={k} ---")
            self.log(f"Inercia: {kmeans.inertia_:,.2f}")
            self.log("Centroides (Superficie, Valor):")
            for c_idx, center in enumerate(centroides):
                self.log(f"  Cluster {c_idx}: ({center[0]:,.2f}, {center[1]:,.2f})")

        fig_clusters.tight_layout(rect=[0, 0.03, 1, 0.95])
        
        canvas_clusters = FigureCanvasTkAgg(fig_clusters, master=container)
        canvas_clusters.draw()
        canvas_clusters.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        # --- Gráfico del Codo ---
        fig_codo, ax_codo = plt.subplots(figsize=(8, 4))
        ax_codo.plot(k_ranges, inercias, marker='o')
        ax_codo.set_title('Comparación de Inercia (Método del Codo)')
        ax_codo.set_xlabel('Número de Clusters (K)')
        ax_codo.set_ylabel('Inercia')
        ax_codo.set_xticks(k_ranges)
        ax_codo.grid()
        
        canvas_codo = FigureCanvasTkAgg(fig_codo, master=container)
        canvas_codo.draw()
        canvas_codo.get_tk_widget().pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True, pady=(10,0))

        self.notebook.select(self.tab_graphs)
        self.log("\n✅ Gráficos de K-Means y Método del Codo generados.")


if __name__ == "__main__":
    root = tk.Tk()
    app = GraficoKmeansGUI(root)
    root.mainloop()
