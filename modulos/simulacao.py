def simular_fluxo(renda, despesas, parcela, valor_emp, saldo_ini):
    saldo = saldo_ini + valor_emp
    for i in range(len(renda)):
        saldo += renda[i] - despesas[i]
        saldo -= parcela
        if saldo < 0:
            return saldo, False
    return saldo, True

def calcular_saldo_mensal(renda, despesas, parcela, valor_emp, saldo_ini):
    saldo = saldo_ini + valor_emp
    saldos = [saldo]
    for i in range(len(renda)):
        saldo += renda[i] - despesas[i]
        saldo -= parcela
        saldos.append(saldo)
    return saldos