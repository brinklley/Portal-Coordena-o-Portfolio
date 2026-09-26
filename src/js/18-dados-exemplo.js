/* ---------------- dados de exemplo ---------------- */
function demoTables(){
  let seed = 7; const rnd = () => (seed = (seed * 16807) % 2147483647) / 2147483647;
  const pick = a => a[Math.floor(rnd() * a.length)];
  const addD = (d, n) => new Date(d.getFullYear(), d.getMonth(), d.getDate() + n);
  const stI = ["Materialização da Oportunidade ou Solicitação","Análise de Viabilidade","Priorizada","Em Execução","Concluído"];
  const stR = ["Inventário de Opções de Valor","Refinamento","Planejada","Em Desenvolvimento","Homologação","Entregue"];
  const stE = ["Backlog","Refinamento","Em Desenvolvimento","Homologação","Fechado"];
  const stT = ["Backlog","Refinamento","READY / PRONTO PARA DEV","Em Desenvolvimento","Code Review","Testes","Pronto para Deploy","Fechado"];
  const flowDates = (stages, upto, start) => { let d = start; return stages.map((s,k) => { if (k > upto) return null; if (k) d = addD(d, 3 + Math.floor(rnd()*14)); return d > TODAY ? null : d; }); };
  const iniT = ["Novo app de investimentos","Pix Automático para cooperados","Cartão de crédito com limite dinâmico","Onboarding digital PJ",
    "Open Finance: agregação de contas","Renegociação de dívidas no app","Consórcio 100% digital","Seguro prestamista integrado ao crédito","Assembleia digital das cooperativas"];
  const relT = ["MVP","Piloto em 3 cooperativas","Escala nacional","Integração com o core bancário","Jornada no app","Operação e back office"];
  const epiT = ["Tela de simulação","API de limites","Motor de regras de elegibilidade","Notificações push","Conciliação diária","Painel de acompanhamento do BO",
    "Autenticação biométrica","Termos e aceite digital","Integração com bureau de crédito","Relatórios regulatórios","Extrato unificado","Gestão de consentimentos",
    "Cálculo de tarifas","Fila de análise manual","Componente de assinatura","Monitoramento de fraudes"];
  const opT = ["Ajustar contrato da API","Criar componente de card","Teste de carga do endpoint","Tratar timeout na integração","Mapear campos do layout",
    "Revisar regra de arredondamento","Criar tela de confirmação","Ajustar massa de testes","Log de auditoria","Corrigir exibição em telas pequenas",
    "Job de reprocessamento","Configurar feature flag","Validação de CPF/CNPJ","Mensageria de retorno","Documentar endpoint"];
  const sems = ["2026 1º Semestre","2026 2º Semestre","2027 1º Semestre"];
  const people = ["Ana Ribeiro","Bruno Kist","Carla Menezes","Diego Farias","Elisa Tonin"];
  const teams = ["TIME CORE","TIME IB","TIME BO","TIME MOBILE"];

  const I = [["ID","Title","AnoSemestreRoadmap","Assigned To","Area Path",...stI]];
  const R = [["ID","Title","Parent","Assigned To",...stR]];
  const E = [["ID","Title","Parent","Target Date",...stE]];
  const TM = Object.fromEntries(teams.map(t => [t, [["ID","ID_EPICO_UNICRED","Title","Work Item Type",...stT]]]));
  let rid = 2001, eid = 3001, oid = 40101;
  const base = new Date(TODAY.getFullYear(), TODAY.getMonth() - 9, 1);

  iniT.forEach((t, k) => {
    const id = 1001 + k; const sem = sems[k % 3];
    const semStart = new Date(+sem.slice(0,4), sem.includes("1º") ? 0 : 6, 1);
    const ist = k === 8 ? 0 : k === 5 ? 4 : Math.min(3, Math.floor(rnd()*4));
    I.push([id, t, sem, people[k % people.length] + " <portal@coop.com.br>", "Portfólio\\Negócios", ...flowDates(stI, ist, addD(base, Math.floor(rnd()*60)))]);
    if (k === 8) return; // iniciativa sem release (higiene)
    const nR = 1 + Math.floor(rnd()*3);
    for (let r = 0; r < nR; r++){
      const relId = rid++;
      const rst = Math.min(5, Math.max(0, ist + Math.floor(rnd()*3) - 1));
      R.push([relId, `${relT[(k + r) % relT.length]}`, id, pick(people) + " <" + "portal@coop.com.br>", ...flowDates(stR, rst, addD(base, 20 + Math.floor(rnd()*60)))]);
      const nE = 1 + Math.floor(rnd()*3);
      for (let e = 0; e < nE; e++){
        const epId = eid++;
        const est = Math.min(4, Math.floor(rnd()*5));
        const off = rnd() < 0.86 ? Math.floor(rnd()*150) : 190 + Math.floor(rnd()*120);
        E.push([epId, pick(epiT), relId, addD(semStart, off), ...flowDates(stE, est, addD(base, 40 + Math.floor(rnd()*90)))]);
        const nO = est === 0 ? Math.floor(rnd()*2) : 1 + Math.floor(rnd()*4);
        for (let o = 0; o < nO; o++){
          const team = teams[Math.floor(rnd()*teams.length)];
          const ost = Math.min(7, Math.floor(rnd()*8));
          const start = addD(TODAY, -(8 + Math.floor(rnd()*70)));
          TM[team].push([oid++, epId, pick(opT), pick(["User Story","User Story","Bug","Task"]), ...flowDates(stT, ost, start)]);
        }
      }
    }
  });
  // casos de higiene
  E.push([eid++, "Épico sem release correspondente", 2999, addD(TODAY, 40), TODAY, null, null, null, null]);
  TM["TIME BO"].push([oid++, 99999, "Item apontando para épico inexistente", "Task", addD(TODAY,-12), null, null, null, null, null, null, null]);
  TM["TIME IB"].push([oid++, null, "Item sem ID_EPICO_UNICRED", "Bug", addD(TODAY,-5), null, null, null, null, null, null, null]);

  const toT = aoa => ({headers: aoa[0], rows: aoa.slice(1)});
  const out = {"Iniciativa": toT(I), "Release": toT(R), "Épico": toT(E)};
  teams.forEach(t => out[t] = toT(TM[t]));
  return out;
}

