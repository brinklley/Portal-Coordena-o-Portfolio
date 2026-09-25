
"use strict";
/* =====================================================================
   Regras do Portal (resumo):
   Iniciativa --Parent--> Release --Parent--> Épico --ID_EPICO_UNICRED--> Registro do Time
   Fluxos identificados pelo NOME das colunas inicial e final.
   Status = última coluna do fluxo preenchida.
   READY = "READY / PRONTO PARA DEV"; DEPLOY = "Pronto para Deploy".
   Ag. Deploy do Épico só quando TODOS os registros têm Deploy.
   Roadmap Executivo = Iniciativa.AnoSemestreRoadmap; Interno = semestre do Target Date do Épico.
   Com Time selecionado, cálculos do Épico usam somente registros daquele Time.
   ===================================================================== */
const FLOW = {
  ini:{start:"Materialização da Oportunidade ou Solicitação", end:"Concluído"},
  rel:{start:"Inventário de Opções de Valor", end:"Entregue"},
  epi:{start:"Backlog", end:"Fechado"},
  op:{start:"Backlog", end:"Fechado"}
};
