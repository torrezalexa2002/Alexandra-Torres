# Calculadora numérica

Aplicación académica construida con Streamlit para resolver raíces e integrales
definidas mediante métodos numéricos. El historial implementa operaciones CRUD
y guarda los registros en SQLite en el archivo `calculadora_numerica.db`.

## Métodos disponibles

- Bisección
- Newton-Raphson con derivada aproximada numéricamente
- Regla del trapecio compuesto
- Regla de Simpson 1/3 compuesto

Las funciones aceptadas son `sin`, `cos`, `tan`, `exp`, `log`, `sqrt` y `abs`.
También están disponibles las constantes `pi` y `e`; usa `**` para potencias.

## Ejecución en Windows

Desde la carpeta del proyecto, activa el entorno virtual y ejecuta la app:

```powershell
.\venv\Scripts\Activate.ps1
streamlit run app.py
```

La app permite crear cálculos, consultar el historial, editar la descripción de
un registro y eliminarlo.

## Pruebas

```powershell
python -m unittest discover -s tests
```
