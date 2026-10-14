// ═══ HOTMART — Fechamento Geral (exclusivo deste cliente) ═══════════════
// Injetado pelo index.html depois do template compartilhado. Lê DASH_DATA.HOTMART
// (gerado pelo dashboard.py) e usa Chart.js + helpers globais do template
// (DARK, TXT, GRID, bo, CH, dc, showLabels, labelSize, goPage, rerenderActive).
(function(){
  const HM = window.DASH_DATA && window.DASH_DATA.HOTMART;
  if(!HM) return;

  // paleta categórica validada (light / dark) — cor segue o produto, nunca o rank do mês
  const PAL_L=['#2a78d6','#eb6834','#1baf7a','#eda100','#e87ba4','#008300'];
  const PAL_D=['#3987e5','#d95926','#199e70','#c98500','#d55181','#008300'];
  const cor=i=>(DARK()?PAL_D:PAL_L)[i%PAL_L.length];
  const META_COR=()=>DARK()?'#94a3b8':'#64748b';

  const brl=v=>'R$ '+Number(v||0).toLocaleString('pt-BR',{minimumFractionDigits:2,maximumFractionDigits:2});
  const brl0=v=>'R$ '+Number(v||0).toLocaleString('pt-BR',{maximumFractionDigits:0});
  const k=v=>Math.abs(v)>=1000?'R$ '+(v/1000).toLocaleString('pt-BR',{maximumFractionDigits:1})+'k':brl0(v);
  const int=v=>Number(v||0).toLocaleString('pt-BR');
  const pct=v=>Number(v||0).toLocaleString('pt-BR',{maximumFractionDigits:1})+'%';
  let mode='bruto', modeAc='bruto';

  // ── estilos ──
  const css=document.createElement('style');
  css.textContent=`
  .hm-tbl{width:100%;border-collapse:collapse;font-size:12px}
  .hm-tbl th{font-size:9px;text-transform:uppercase;letter-spacing:1px;color:var(--muted);font-weight:600;text-align:right;padding:8px 10px;border-bottom:1px solid var(--border);white-space:nowrap}
  .hm-tbl th:first-child,.hm-tbl td:first-child{text-align:left}
  .hm-tbl td{padding:9px 10px;border-bottom:1px solid var(--border);text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}
  .hm-tbl tr.tot td{font-weight:700;border-bottom:none}
  .hm-sw{display:inline-block;width:9px;height:9px;border-radius:3px;margin-right:8px;vertical-align:middle}
  .hm-bar{height:5px;border-radius:3px;background:var(--border);margin-top:4px;overflow:hidden}
  .hm-bar>i{display:block;height:100%;border-radius:3px}
  .hm-note{font-size:10px;color:var(--muted);margin-top:8px;line-height:1.5}
  .hm-wrap{overflow-x:auto}
  #page-hotmart .k6{grid-template-columns:repeat(6,1fr)}
  @media(max-width:1100px){#page-hotmart .k6{grid-template-columns:repeat(3,1fr)}}
  @media(max-width:768px){#page-hotmart .k6{grid-template-columns:repeat(2,1fr)}#page-hotmart .g2{grid-template-columns:1fr}}`;
  document.head.appendChild(css);

  // ── sidebar ──
  const grp=document.createElement('div');
  grp.className='sb-platform-group'; grp.style.marginTop='8px';
  grp.innerHTML=`<div class="sb-platform-hd">
      <div class="sb-platform-icon" style="background:#F04E23;border-radius:5px">H</div>
      <span class="sb-platform-lbl">Hotmart</span></div>
    <a href="#" class="sb-item" id="sbHotmart" onclick="goPage('hotmart',this);return false;">Fechamento Geral</a>`;
  const anchor=document.getElementById('sbConsolidadoGroup')||document.querySelector('.sb-google-group');
  anchor.parentNode.insertBefore(grp, anchor);

  // ── página ──
  const K=HM.kpis;
  const sec=document.createElement('div');
  sec.className='page-section'; sec.id='page-hotmart';
  sec.innerHTML=`
    <div style="margin-bottom:16px">
      <div style="font-family:'Syne',sans-serif;font-size:17px;font-weight:700;margin-bottom:3px">Hotmart — Fechamento Geral</div>
      <div style="font-size:12px;color:var(--muted)">${K.ini} → ${K.fim} · ${K.produtos} produtos · todo o histórico (não usa o filtro de período)</div>
    </div>
    <div class="krow k6 mb14" id="hmK1"></div>

    <div class="cc mb14">
      <div style="display:flex;justify-content:space-between;align-items:flex-start;gap:8px;flex-wrap:wrap">
        <div><div class="cc-t">Faturamento mensal por produto</div>
        <div class="cc-s" id="hmMensalSub"></div></div>
        <div class="period-bar">
          <button class="pb active" id="hmModeBru" onclick="hmSetMode('bruto')" style="font-size:10px;padding:3px 9px">R$ Bruto</button>
          <button class="pb" id="hmModeLiq" onclick="hmSetMode('liq')" style="font-size:10px;padding:3px 9px">R$ Líquido</button>
          <button class="pb" id="hmModeVen" onclick="hmSetMode('vendas')" style="font-size:10px;padding:3px 9px">Nº de vendas</button>
        </div>
      </div>
      <div class="cw" style="height:260px"><canvas id="chHmMensal"></canvas></div>
    </div>

    <div class="cc mb14">
      <div style="display:flex;justify-content:space-between;align-items:flex-start;gap:8px;flex-wrap:wrap">
        <div><div class="cc-t">Faturamento acumulado por produto</div>
        <div class="cc-s" id="hmAcumSub"></div></div>
        <div class="period-bar">
          <button class="pb active" id="hmAcBru" onclick="hmSetAcum('bruto')" style="font-size:10px;padding:3px 9px">R$ Bruto</button>
          <button class="pb" id="hmAcLiq" onclick="hmSetAcum('liq')" style="font-size:10px;padding:3px 9px">R$ Líquido</button>
        </div>
      </div>
      <div class="cw" style="height:260px"><canvas id="chHmAcum"></canvas></div>
    </div>

    <div class="g2">
      <div class="cc"><div class="cc-t">Participação no faturamento</div><div class="cc-s">% do faturamento líquido total</div>
        <div class="cw" style="height:260px"><canvas id="chHmShare"></canvas></div></div>
      <div class="cc"><div class="cc-t">Vendas × ticket médio por produto</div><div class="cc-s">Nº de vendas (barras) · ticket médio líquido no rótulo</div>
        <div class="cw" style="height:260px"><canvas id="chHmVendas"></canvas></div></div>
    </div>

    <div class="cc mb14">
      <div class="cc-t">Faturamento bruto × investimento Meta Ads</div>
      <div class="cc-s">Mesmo eixo em R$ · ROAS do mês no rótulo/tooltip · investimento = todas as campanhas Meta no mês</div>
      <div class="cw" style="height:240px"><canvas id="chHmRoas"></canvas></div>
    </div>

    <div class="g2">
      <div class="cc"><div class="cc-t">Forma de pagamento</div><div class="cc-s">% das vendas · Cartão inclui Apple Pay</div>
        <div class="cw" style="height:180px"><canvas id="chHmPgto"></canvas></div></div>
      <div class="cc"><div class="cc-t" style="margin-bottom:10px">Forma de pagamento — detalhe</div><div class="hm-wrap" id="hmPgtoTbl"></div></div>
    </div>

    <div class="cc mb14">
      <div class="cc-t" style="margin-bottom:10px">Resumo por produto</div>
      <div class="hm-wrap" id="hmTabela"></div>
      <div class="hm-note">Status considerados: Completo e Aprovado. ${K.intl} vendas internacionais (recebidas em USD) convertidas para R$ pela taxa da própria transação.
      Faturamento líquido = valor do(a) produtor(a) após taxas Hotmart.</div>
    </div>`;
  document.querySelector('.content').appendChild(sec);

  function kpi(lbl,val,sub,c,small){return `<div class="kpi" style="--kc:${c||'var(--accent)'}"><div class="kpi-lbl">${lbl}</div><div class="kpi-val"${small?' style="font-size:14px;line-height:1.25"':''}>${val}</div><div class="kpi-sub">${sub||''}</div></div>`;}
  function renderKpis(){
    document.getElementById('hmK1').innerHTML=
      kpi('Investimento Meta Ads',brl0(K.meta_spend),'no mesmo período','#64748b')+
      kpi('Faturamento bruto',brl0(K.bruto),'antes das taxas Hotmart','#F04E23')+
      kpi('Faturamento líquido',brl0(K.liq),pct(K.liq/K.bruto*100)+' do bruto','#F04E23')+
      kpi('Vendas',int(K.vendas),K.produtos+' produtos')+
      kpi('Ticket médio',brl(K.ticket_bruto),'bruto · líquido '+brl(K.ticket))+
      kpi('ROAS',K.roas_bruto?K.roas_bruto.toLocaleString('pt-BR')+'x':'—','fat. bruto ÷ invest. Meta','#2BB673');
  }

  function lbls(fmt,onlyLast){
    return {display:ctx=>{
        if(!showLabels) return false;
        if(onlyLast) return ctx.datasetIndex===ctx.chart.data.datasets.length-1;
        return true;},
      color:TXT(),font:{size:labelSize,weight:'bold'},anchor:'end',align:'end',offset:2,clip:false,formatter:fmt};
  }

  function renderMensal(){
    dc('chHmMensal');
    const M=HM.mensal, isV=mode==='vendas';
    const ds=HM.produtos.map(p=>({label:p.nome,data:M.por_prod[p.nome][mode],
      backgroundColor:cor(p.ci),borderColor:DARK()?'#111827':'#fff',borderWidth:{top:2,bottom:0,left:0,right:0},borderRadius:4,borderSkipped:'bottom',stack:'s'}));
    const tot=M[mode];
    const o=bo({plugins:{...bo().plugins,
      legend:{position:'bottom',labels:{color:TXT(),boxWidth:9,padding:10,font:{size:10}}},
      tooltip:{...bo().plugins.tooltip,filter:i=>i.raw>0,callbacks:{
        label:c=>' '+c.dataset.label+': '+(isV?int(c.raw)+' vendas':brl(c.raw)),
        footer:it=>'Total: '+(isV?int(tot[it[0].dataIndex])+' vendas':brl(tot[it[0].dataIndex]))}},
      datalabels:{display:ctx=>showLabels&&ctx.datasetIndex===ctx.chart.data.datasets.length-1,
        color:TXT(),font:{size:labelSize,weight:'bold'},anchor:'end',align:'end',offset:2,clip:false,
        formatter:(v,ctx)=>isV?int(tot[ctx.dataIndex]):k(tot[ctx.dataIndex])}},
      scales:{x:{stacked:true,ticks:{color:TXT()},grid:{display:false}},
              y:{stacked:true,ticks:{color:TXT(),callback:v=>isV?v:k(v)},grid:{color:GRID()},grace:'10%'}}});
    CH['chHmMensal']=new Chart(document.getElementById('chHmMensal'),{type:'bar',data:{labels:M.lbl,datasets:ds},options:o});
    document.getElementById('hmMensalSub').textContent=({bruto:'Faturamento bruto (R$)',liq:'Faturamento líquido (R$)',vendas:'Nº de vendas'})[mode]+' · barras empilhadas por produto';
  }
  window.hmSetMode=function(m){mode=m;
    document.getElementById('hmModeBru').classList.toggle('active',m==='bruto');
    document.getElementById('hmModeLiq').classList.toggle('active',m==='liq');
    document.getElementById('hmModeVen').classList.toggle('active',m==='vendas');
    renderMensal();};

  function renderAcum(){
    dc('chHmAcum');
    const A=HM.acum;
    const ds=HM.produtos.map(p=>({label:p.nome,data:(modeAc==='bruto'?A.prod_bruto:A.prod)[p.nome],borderColor:cor(p.ci),backgroundColor:cor(p.ci),
      borderWidth:2,pointRadius:0,pointHoverRadius:5,tension:0,stepped:false,fill:false}));
    const o=bo({plugins:{...bo().plugins,
      legend:{position:'bottom',labels:{color:TXT(),boxWidth:9,padding:10,font:{size:10}}},
      tooltip:{...bo().plugins.tooltip,itemSort:(a,b)=>b.raw-a.raw,callbacks:{label:c=>' '+c.dataset.label+': '+brl(c.raw)}},
      datalabels:{display:ctx=>showLabels&&ctx.dataIndex===ctx.dataset.data.length-1,
        color:TXT(),font:{size:labelSize,weight:'bold'},anchor:'end',align:'left',offset:4,clip:false,formatter:v=>k(v)}},
      scales:{x:{ticks:{color:TXT(),maxTicksLimit:10},grid:{display:false}},
              y:{ticks:{color:TXT(),callback:v=>k(v)},grid:{color:GRID()}}}});
    CH['chHmAcum']=new Chart(document.getElementById('chHmAcum'),{type:'line',data:{labels:A.dias,datasets:ds},options:o});
    document.getElementById('hmAcumSub').textContent='Como cada produto construiu seu faturamento ao longo do período (R$ '+(modeAc==='bruto'?'bruto':'líquido')+' acumulado)';
  }
  window.hmSetAcum=function(m){modeAc=m;
    document.getElementById('hmAcBru').classList.toggle('active',m==='bruto');
    document.getElementById('hmAcLiq').classList.toggle('active',m==='liq');
    renderAcum();};

  function renderShare(){
    dc('chHmShare');
    const P=HM.produtos;
    CH['chHmShare']=new Chart(document.getElementById('chHmShare'),{type:'doughnut',
      data:{labels:P.map(p=>p.nome),datasets:[{data:P.map(p=>p.liq),backgroundColor:P.map(p=>cor(p.ci)),borderColor:DARK()?'#111827':'#fff',borderWidth:2}]},
      options:{responsive:true,maintainAspectRatio:false,cutout:'58%',
        plugins:{legend:{position:'bottom',labels:{color:TXT(),boxWidth:9,padding:8,font:{size:10}}},
          tooltip:{...bo().plugins.tooltip,callbacks:{label:c=>' '+brl(c.raw)+' ('+pct(P[c.dataIndex].share)+')'}},
          datalabels:{display:ctx=>showLabels&&P[ctx.dataIndex].share>=5,color:'#fff',font:{size:labelSize+1,weight:'bold'},
            formatter:(v,ctx)=>pct(P[ctx.dataIndex].share)}}}});
  }

  function renderVendas(){
    dc('chHmVendas');
    const P=[...HM.produtos].sort((a,b)=>b.vendas-a.vendas);
    const o=bo({indexAxis:'y',interaction:{mode:'nearest',intersect:false,axis:'y'},
      plugins:{...bo().plugins,legend:{display:false},
        tooltip:{...bo().plugins.tooltip,callbacks:{label:c=>' '+int(c.raw)+' vendas · ticket '+brl(P[c.dataIndex].ticket)}},
        datalabels:{display:()=>showLabels,color:TXT(),font:{size:labelSize,weight:'bold'},anchor:'end',align:'end',offset:3,clip:false,
          formatter:(v,ctx)=>int(v)+' · '+brl0(P[ctx.dataIndex].ticket)}},
      scales:{x:{ticks:{color:TXT()},grid:{color:GRID()},grace:'35%'},y:{ticks:{color:TXT(),font:{size:10}},grid:{display:false}}}});
    CH['chHmVendas']=new Chart(document.getElementById('chHmVendas'),{type:'bar',
      data:{labels:P.map(p=>p.nome.length>24?p.nome.slice(0,23)+'…':p.nome),datasets:[{data:P.map(p=>p.vendas),backgroundColor:P.map(p=>cor(p.ci)),borderRadius:4,borderSkipped:'start',barThickness:16}]},options:o});
  }

  function renderRoas(){
    dc('chHmRoas');
    const M=HM.mensal;
    const roas=M.bruto.map((v,i)=>M.meta[i]?v/M.meta[i]:null);
    const o=bo({plugins:{...bo().plugins,
      legend:{position:'bottom',labels:{color:TXT(),boxWidth:9,padding:10,font:{size:10}}},
      tooltip:{...bo().plugins.tooltip,callbacks:{label:c=>' '+c.dataset.label+': '+brl(c.raw),
        footer:it=>roas[it[0].dataIndex]!=null?'ROAS: '+roas[it[0].dataIndex].toFixed(2).replace('.',',')+'x':''}},
      datalabels:{display:ctx=>showLabels&&ctx.datasetIndex===0,color:TXT(),font:{size:labelSize,weight:'bold'},anchor:'end',align:'end',offset:2,clip:false,
        formatter:(v,ctx)=>roas[ctx.dataIndex]!=null?roas[ctx.dataIndex].toFixed(1).replace('.',',')+'x':''}},
      scales:{x:{ticks:{color:TXT()},grid:{display:false}},y:{ticks:{color:TXT(),callback:v=>k(v)},grid:{color:GRID()},grace:'10%'}}});
    CH['chHmRoas']=new Chart(document.getElementById('chHmRoas'),{type:'bar',data:{labels:M.lbl,datasets:[
      {label:'Faturamento bruto',data:M.bruto,backgroundColor:'#F04E23',borderRadius:4,borderSkipped:'bottom',maxBarThickness:34},
      {label:'Investimento Meta Ads',data:M.meta,backgroundColor:META_COR(),borderRadius:4,borderSkipped:'bottom',maxBarThickness:34}]},options:o});
  }

  function renderPgto(){
    dc('chHmPgto');
    const D=HM.pgto, tv=D.vendas.reduce((a,b)=>a+b,0), tl=D.liq.reduce((a,b)=>a+b,0);
    const PC=DARK()?['#3987e5','#199e70','#94a3b8']:['#2a78d6','#1baf7a','#94a3b8'];
    const c=l=>PC[l==='Cartão'?0:l==='Pix'?1:2];
    CH['chHmPgto']=new Chart(document.getElementById('chHmPgto'),{type:'doughnut',
      data:{labels:D.lbl,datasets:[{data:D.vendas,backgroundColor:D.lbl.map(c),borderColor:DARK()?'#111827':'#fff',borderWidth:2}]},
      options:{responsive:true,maintainAspectRatio:false,cutout:'60%',
        plugins:{legend:{position:'right',labels:{color:TXT(),boxWidth:9,padding:8,font:{size:10}}},
          tooltip:{...bo().plugins.tooltip,callbacks:{label:x=>' '+int(x.raw)+' vendas ('+pct(x.raw/tv*100)+') · '+brl(D.liq[x.dataIndex])}},
          datalabels:{display:x=>showLabels&&x.raw/tv>=.05,color:'#fff',font:{size:labelSize+1,weight:'bold'},formatter:v=>pct(v/tv*100)}}}});
    document.getElementById('hmPgtoTbl').innerHTML=`<table class="hm-tbl"><thead><tr><th>Forma</th><th>Vendas</th><th>% vendas</th><th>Fat. líquido</th><th>% fat.</th></tr></thead><tbody>
      ${D.lbl.map((l,i)=>`<tr><td><span class="hm-sw" style="background:${c(l)}"></span>${l}</td><td>${int(D.vendas[i])}</td><td>${pct(D.vendas[i]/tv*100)}</td><td>${brl(D.liq[i])}</td><td>${pct(D.liq[i]/tl*100)}</td></tr>`).join('')}
      </tbody></table><div class="hm-note">"Outros" = NuPay, boleto, PayPal, MB WAY.</div>`;
  }

  function renderTabela(){
    const P=HM.produtos, max=Math.max(...P.map(p=>p.liq));
    const rows=P.map(p=>`<tr>
      <td><span class="hm-sw" style="background:${cor(p.ci)}"></span>${p.nome}
        <div class="hm-bar" style="width:140px;margin-left:17px"><i style="width:${p.liq/max*100}%;background:${cor(p.ci)}"></i></div></td>
      <td>${int(p.vendas)}</td><td>${brl(p.bruto)}</td><td><b>${brl(p.liq)}</b></td><td>${pct(p.share)}</td>
      <td>${brl(p.ticket_bruto)}</td><td>${brl(p.ticket)}</td><td>${pct(p.pix)}</td><td>${pct(p.parcelado)}</td><td>${pct(p.meta_pct)}</td>
      <td>${p.ini}</td><td>${p.fim}</td></tr>`).join('');
    document.getElementById('hmTabela').innerHTML=`<table class="hm-tbl"><thead><tr>
      <th>Produto</th><th>Vendas</th><th>Fat. bruto</th><th>Fat. líquido</th><th>% total</th><th>Ticket bruto</th><th>Ticket líq.</th>
      <th>% Pix</th><th>% Parcelado</th><th>% via Meta Ads</th><th>1ª venda</th><th>Última venda</th></tr></thead>
      <tbody>${rows}<tr class="tot"><td>Total</td><td>${int(K.vendas)}</td><td>${brl(K.bruto)}</td><td>${brl(K.liq)}</td><td>100%</td>
      <td>${brl(K.ticket_bruto)}</td><td>${brl(K.ticket)}</td><td colspan="5"></td></tr></tbody></table>`;
  }

  function renderHotmart(){
    renderKpis(); renderMensal(); renderAcum(); renderShare(); renderVendas(); renderRoas();
    renderPgto();
    renderTabela();
  }

  // ── integra com a navegação do template ──
  const _goPage=window.goPage, _rerender=window.rerenderActive;
  const filtros=()=>document.querySelectorAll('.topbar .period-bar, .topbar .date-range');
  window.goPage=function(p,btn){
    _goPage(p,btn);
    filtros().forEach(e=>e.style.visibility=p==='hotmart'?'hidden':'');
    if(p==='hotmart'){
      document.getElementById('pageTitle').innerHTML='<span style="display:inline-flex;align-items:center;gap:7px"><span style="background:#F04E23;color:#fff;border-radius:4px;font-size:11px;font-weight:800;padding:1px 6px">H</span> Hotmart — Fechamento Geral</span>';
      renderHotmart();
      setTimeout(()=>{Object.values(CH).forEach(c=>{try{c.resize();}catch(e){}});},80);
    }
  };
  window.rerenderActive=function(){
    _rerender();
    if(document.getElementById('page-hotmart').classList.contains('active')) renderHotmart();
  };
})();
