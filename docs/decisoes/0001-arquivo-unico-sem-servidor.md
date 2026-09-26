# 0001 · Portal em arquivo único, sem servidor

**Contexto.** O portal precisa rodar na máquina do usuário, sem instalação nem servidor, e sem que os dados saiam do computador.
**Decisão.** Um único HTML com CSS, JavaScript e a biblioteca SheetJS embutidos. Código-fonte dividido em `src/` e juntado pelo build.
**Consequências.** Sem dependências em tempo de execução; atenção ao tamanho do arquivo e à proibição de `</script>` no código.
