import json

import streamlit as st

from history import create_operation, delete_operation, get_operations, initialize_database, update_description
from numerical_methods import solve


st.set_page_config(
    page_title="Números | Calculadora numérica",
    page_icon=":material/functions:",
    layout="wide",
)

initialize_database()

METHODS = {
    "Bisección": "bisection",
    "Newton-Raphson": "newton",
    "Trapecio compuesto": "trapezoid",
    "Simpson 1/3 compuesto": "simpson",
}

with st.sidebar:
    st.title("∑ Números")
    st.caption("Laboratorio de métodos numéricos")
    section = st.radio(
        "Sección",
        ["Calculadora", "Historial"],
        key="section",
        horizontal=True,
    )
    st.caption("Proyecto académico · Cálculo numérico")

st.title("Calculadora numérica")
st.write("Resuelve ecuaciones e integrales con métodos numéricos.")

operations = get_operations()
metric_one, metric_two, metric_three = st.columns(3)
metric_one.metric("Cálculos guardados", len(operations), border=True)
metric_two.metric("Métodos disponibles", len(METHODS), border=True)
metric_three.metric(
    "Último cálculo",
    operations[0]["created_at"][:16].replace("T", " ") if operations else "Aún no hay",
    border=True,
)

if section == "Calculadora":
    calculator_column, guide_column = st.columns([1.5, 1], gap="large")

    with calculator_column:
        st.subheader("Nuevo cálculo")
        with st.form("calculation_form"):
            method_name = st.selectbox("Método numérico", list(METHODS))
            expression = st.text_input(
                "Función f(x)",
                value="x**2 - 2",
                help="Ejemplos: x**2 - 2, sin(x), exp(-x) o log(x).",
            )

            parameters: dict[str, int | float] = {}
            if METHODS[method_name] == "newton":
                parameters["x0"] = st.number_input(
                    "Aproximación inicial x₀", value=1.0, format="%.6f"
                )
            else:
                first, second = st.columns(2)
                parameters["a"] = first.number_input("Límite a", value=0.0, format="%.6f")
                parameters["b"] = second.number_input("Límite b", value=2.0, format="%.6f")

            if METHODS[method_name] in {"bisection", "newton"}:
                tolerance_column, iteration_column = st.columns(2)
                parameters["tolerance"] = tolerance_column.number_input(
                    "Tolerancia",
                    min_value=0.000000001,
                    value=0.000001,
                    format="%.9f",
                )
                parameters["max_iterations"] = iteration_column.number_input(
                    "Máximo de iteraciones",
                    min_value=1,
                    max_value=1000,
                    value=100,
                    step=1,
                )

            if METHODS[method_name] in {"trapezoid", "simpson"}:
                parameters["intervals"] = st.number_input(
                    "Número de subintervalos",
                    min_value=1,
                    max_value=100000,
                    value=100,
                    step=1,
                    help="Simpson 1/3 requiere un número par de subintervalos.",
                )

            submitted = st.form_submit_button(
                "Calcular y guardar",
                type="primary",
                icon=":material/functions:",
                width="stretch",
            )

        if submitted:
            try:
                result = solve(METHODS[method_name], expression, parameters)
                description = f"{method_name}: {expression}"
                operation_id = create_operation(
                    method=method_name,
                    expression=expression,
                    parameters=parameters,
                    result=result,
                    description=description,
                )
                st.session_state["last_result"] = {
                    "id": operation_id,
                    "method": method_name,
                    "expression": expression,
                    "result": result,
                }
            except (ValueError, ArithmeticError) as error:
                st.error(str(error))

        last_result = st.session_state.get("last_result")
        if last_result:
            result_data = last_result["result"]
            with st.container(border=True):
                st.badge("Cálculo guardado", icon=":material/check_circle:", color="green")
                st.subheader(last_result["method"])
                st.caption(f"f(x) = {last_result['expression']}")
                st.metric("Resultado", f"{result_data['value']:.12g}")
                if "iterations" in result_data:
                    st.caption(
                        f"Iteraciones: {result_data['iterations']} · "
                        f"Residuo estimado: {result_data['residual']:.3g}"
                    )

    with guide_column:
        st.subheader("Guía rápida")
        with st.container(border=True):
            st.markdown(
                """
                **Raíces**
                - **Bisección:** busca una raíz entre `a` y `b`; la función debe cambiar de signo.
                - **Newton-Raphson:** parte de una aproximación inicial `x₀`.

                **Integrales definidas**
                - **Trapecio compuesto:** aproxima el área bajo la curva.
                - **Simpson 1/3:** usa parábolas; necesita un número par de subintervalos.

                **Funciones permitidas**

                `sin(x)`, `cos(x)`, `tan(x)`, `exp(x)`, `log(x)`, `sqrt(x)`,
                `abs(x)`, además de `pi` y `e`. Usa `**` para potencias.
                """
            )
        st.caption(
            "Cada cálculo se guarda automáticamente y puedes consultar, editar "
            "su descripción o eliminarlo desde el historial."
        )

else:
    st.subheader("Historial de cálculos")
    st.caption("Consulta y administra tus operaciones guardadas.")

    if not operations:
        st.info("Todavía no hay cálculos. Haz una operación en la sección Calculadora.")
    else:
        table_rows = [
            {
                "ID": item["id"],
                "Fecha": item["created_at"].replace("T", " "),
                "Método": item["method"],
                "Función": item["expression"],
                "Resultado": f"{json.loads(item['result_json'])['value']:.12g}",
                "Descripción": item["description"],
            }
            for item in operations
        ]
        st.dataframe(
            table_rows,
            column_config={
                "ID": st.column_config.NumberColumn("ID", format="%d"),
                "Resultado": st.column_config.TextColumn("Resultado"),
            },
            hide_index=True,
            alt="Historial de cálculos numéricos guardados",
        )

        options = [item["id"] for item in operations]
        selected_id = st.selectbox(
            "Selecciona un registro para editar o eliminar",
            options,
            format_func=lambda item_id: (
                f"#{item_id} · "
                f"{next(item['method'] for item in operations if item['id'] == item_id)} · "
                f"{next(item['expression'] for item in operations if item['id'] == item_id)}"
            ),
        )
        selected_operation = next(item for item in operations if item["id"] == selected_id)

        edit_column, delete_column = st.columns([2, 1], vertical_alignment="bottom")
        with edit_column:
            with st.form(f"edit_form_{selected_id}"):
                new_description = st.text_input(
                    "Descripción",
                    value=selected_operation["description"],
                    max_chars=120,
                )
                update_submitted = st.form_submit_button(
                    "Guardar cambios",
                    icon=":material/save:",
                    type="primary",
                )
            if update_submitted:
                update_description(selected_id, new_description.strip())
                st.success("Descripción actualizada.")
                st.rerun()

        with delete_column:
            if st.button(
                "Eliminar registro",
                icon=":material/delete:",
                key=f"delete_{selected_id}",
                width="stretch",
            ):
                delete_operation(selected_id)
                st.success("Registro eliminado.")
                st.rerun()
