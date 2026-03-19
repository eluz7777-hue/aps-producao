# ===============================
# 📊 PEDIDOS POR CLIENTE
# ===============================
st.subheader("📊 Pedidos por Cliente (Mensal)")

if "Cliente" in df.columns:

    df["Mes"] = df["Data"].dt.strftime("%Y-%m")

    pedidos_cliente = (
        df.groupby(["Mes","Cliente"])["PV"]
        .nunique()
        .reset_index(name="Qtd PV")
    )

    fig_cliente = px.bar(
        pedidos_cliente,
        x="Mes",
        y="Qtd PV",
        color="Cliente",
        barmode="group",
        text="Qtd PV"
    )

    fig_cliente.update_traces(textposition="outside")

    st.plotly_chart(fig_cliente, use_container_width=True)