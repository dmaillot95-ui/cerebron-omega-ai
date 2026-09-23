const $ = (s) => document.querySelector(s);
const $$ = (s) => [...document.querySelectorAll(s)];
let activeMission = null;
let poller = null;
let farmCache = [];

async function api(path, options) {
  const response = await fetch(path, options);
  const data = await response.json();
  if (!response.ok) throw new Error(data.error || `HTTP ${response.status}`);
  return data;
}
function esc(value='') { const d=document.createElement('div'); d.textContent=String(value); return d.innerHTML; }
function clock(){ $('#clock').textContent=new Date().toLocaleTimeString('fr-FR',{hour12:false})+' UTC'; }
setInterval(clock,1000); clock();

$$('.nav').forEach(button => button.addEventListener('click', async () => {
  $$('.nav,.view').forEach(el => el.classList.remove('active'));
  button.classList.add('active');
  $(`#${button.dataset.view}`).classList.add('active');
  await loaders[button.dataset.view]?.();
}));

async function loadHealth(){
  try{
    const h=await api('/api/health');
    $('#healthDot').className='dot ok'; $('#healthLabel').textContent='Système opérationnel'; $('#farmCount').textContent=h.farm_count;
    $('#healthGrid').innerHTML=[['API','HEALTHY'],['Registre',`${h.farm_count} FERMES`],['Base','SQLITE ACTIVE'],['Modèle',h.model.status],['Coût',h.cost_policy]].map(([a,b])=>`<article class="health-card"><small>${esc(a)}</small><h3>${esc(b)}</h3></article>`).join('');
  }catch(e){ $('#healthDot').className='dot bad'; $('#healthLabel').textContent='Indisponible'; }
}
async function loadFarms(){
  if(!farmCache.length) farmCache=(await api('/api/farms')).farms;
  renderFarms($('#farmSearch')?.value||'');
}
function renderFarms(query){
  const q=query.toLowerCase();
  $('#farmGrid').innerHTML=farmCache.filter(f=>`${f.farm_id} ${f.domain} ${f.repo}`.toLowerCase().includes(q)).map(f=>`<article class="farm-card"><header><b>${f.farm_id}</b><small>${esc(f.status||'DECLARED')}</small></header><p>${esc(f.domain)}</p><small>${esc(f.repo)}</small><div class="unavailable">WORKER · UNAVAILABLE</div></article>`).join('');
}
$('#farmSearch').addEventListener('input',e=>renderFarms(e.target.value));
async function loadModels(){
  const [{models},{roles}]=await Promise.all([api('/api/models'),api('/api/roles')]);
  $('#modelGrid').innerHTML=models.map(m=>`<article class="model-card ${m.status==='ACTIVE_WORKER'?'real':''}"><span class="tag ${m.status==='UNAVAILABLE'?'unavailable':''}">${esc(m.status)}</span><h3>${esc(m.model_id||m.provider)}</h3><small>${esc(m.provider)} · ${esc(m.runtime)}</small><p class="meta">revision ${esc(m.revision||'—')}</p><p>${esc((m.capabilities||[]).join(' · ')||'Aucune capacité active')}</p></article>`).join('');
  $('#roleGrid').innerHTML=roles.map(r=>`<article class="role-card"><span class="tag unavailable">${r.type}</span><h3>${esc(r.name)}</h3><small>MODEL · ${esc(r.model||'UNBOUND')}</small></article>`).join('');
}
async function loadAgora(){
  const {capsules}=await api('/api/agora');
  $('#agoraList').innerHTML=capsules.length?capsules.map(c=>`<article><header><b>${esc(c.kind)}</b><span class="tag">${esc(c.state)}</span></header><p>${esc(c.content)}</p><code>${esc(c.sha)}</code></article>`).join(''):'<div class="empty">Aucune capsule créée par une mission.</div>';
}
async function loadMemory(){
  const {levels}=await api('/api/memory');
  $('#memoryGrid').innerHTML=levels.map(m=>`<article class="memory-card"><small>${m.id}</small><h3>${esc(m.name)}</h3><b>${esc(m.status)}</b></article>`).join('');
}
async function loadEvidence(){
  const {evidence}=await api('/api/evidence');
  $('#evidenceList').innerHTML=evidence.length?evidence.map(e=>`<article><header><b>${esc(e.kind)}</b><span class="tag">${esc(e.maturity)}</span></header><p>${esc(e.source)}</p><code>${esc(e.sha)}</code></article>`).join(''):'<div class="empty">Aucune preuve produite.</div>';
}
const loaders={farms:loadFarms,models:loadModels,agora:loadAgora,memory:loadMemory,evidence:loadEvidence,health:loadHealth};

$('#missionForm').addEventListener('submit',async e=>{
  e.preventDefault(); const prompt=$('#prompt').value.trim(); if(!prompt)return;
  $('#conversation').insertAdjacentHTML('beforeend',`<article class="message user-msg"><span>UTILISATEUR</span><p>${esc(prompt)}</p></article>`);
  const created=await api('/api/missions',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({prompt})});
  activeMission=created.mission_id; $('#missionId').textContent=activeMission; pollMission(); clearInterval(poller); poller=setInterval(pollMission,700);
});
async function pollMission(){
  if(!activeMission)return; const m=await api(`/api/missions/${activeMission}`);
  const state=m.status.toLowerCase(); $('#missionStatus').textContent=m.status; $('#missionStatus').className=`state ${state}`; $('#missionDomain').textContent=m.domain||'Routage…'; $('#taskCount').textContent=m.tasks.length; $('#evidenceCount').textContent=m.evidence.length;
  const done=m.tasks.filter(t=>['COMPLETED','FAILED'].includes(t.status)).length; $('#progressBar').style.width=`${m.status==='COMPLETED'?100:Math.min(92,10+done*16)}%`;
  const farms=[...new Set(m.tasks.map(t=>t.farm_id).filter(Boolean))]; $('#coalition').textContent=`${farms.length} FERME${farms.length>1?'S':''}`;
  $('#tasks').innerHTML=m.tasks.length?m.tasks.map(t=>`<article class="task ${t.status.toLowerCase()}"><strong>${esc(t.role)}</strong><small>F${String(t.farm_id).padStart(3,'0')} · ${esc(t.worker)}</small><small>${esc(t.model||t.tool||'—')}</small><code>${esc((t.output_sha||t.input_sha||'').slice(0,16))}…</code></article>`).join(''):'<div class="empty">Décomposition en cours…</div>';
  $('#eventLog').innerHTML=m.events.map(ev=>`<p><time>${new Date(ev.time*1000).toLocaleTimeString('fr-FR')}</time> ${esc(ev.message)}</p>`).join(''); $('#eventLog').scrollTop=$('#eventLog').scrollHeight;
  if(['COMPLETED','FAILED'].includes(m.status)){
    clearInterval(poller);
    const result=m.result||{}; const calc=result.calculation?.results; const coalition=result.coalition;
    let summary;
    if(m.status!=='COMPLETED'){
      summary=`Mission échouée : ${m.error}`;
    }else if(calc){
      summary=`Mission terminée. Calcul réel : force ${calc.traction_force_n} N, puissance électrique ${calc.electrical_power_w} W. Niveau E2, pas une validation physique.`;
    }else if(result.answer){
      const units=(coalition?.plan?.selected_units||[]).join(', ')||'—';
      summary=`${result.answer} · Coalition: ${units} · Claim ceiling: ${result.claim_ceiling||'UNSPECIFIED'}.`;
    }else{
      summary='Mission routée sans sortie exécutable vérifiée.';
    }
    const artifact=result.artifact||coalition?.artifact;
    $('#conversation').insertAdjacentHTML('beforeend',`<article class="message system-msg"><span>CÉRÉBRON · ${esc(m.status)}</span><p>${esc(summary)}</p>${artifact?`<p><a href="${artifact.url}">Télécharger l’artifact</a> · SHA ${esc(artifact.sha.slice(0,16))}…</p>`:''}</article>`);
    $('#conversation').scrollTop=$('#conversation').scrollHeight; await Promise.all([loadAgora(),loadEvidence()]);
  }
}
loadHealth();

