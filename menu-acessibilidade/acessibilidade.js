(()=>{
  const menu=document.querySelector('#accessibility-menu'),status=document.querySelector('#accessibility-status');
  const KEY='painel-acessibilidade',cs=matchMedia('(prefers-color-scheme: dark)'),mq=matchMedia('(prefers-reduced-motion: reduce)'),modes=['normal','medio','grande'];
  const sysTheme=()=>cs.matches?'escuro':'claro';
  const def=()=>({theme:null,font:'normal',contrast:false,lines:'normal',letters:'normal',underline:false,motion:null});
  const read=()=>{try{const p=JSON.parse(localStorage.getItem(KEY)||'{}')||{};return{theme:['claro','escuro'].includes(p.theme)?p.theme:null,font:['normal','grande','maior'].includes(p.font)?p.font:'normal',contrast:p.contrast===true,lines:modes.includes(p.lines)?p.lines:'normal',letters:modes.includes(p.letters)?p.letters:'normal',underline:p.underline===true,motion:typeof p.motion==='boolean'?p.motion:null};}catch{return def();}};
  let prefs=read();
  const motion=()=>prefs.motion===null?mq.matches:prefs.motion;
  function sync(){const r=document.documentElement,p=prefs,theme=p.theme||sysTheme(),m=motion();
    r.dataset.theme=theme;r.dataset.font=p.font;r.dataset.contrast=p.contrast?'alto':'normal';r.dataset.lines=p.lines;r.dataset.letters=p.letters;r.dataset.underline=p.underline?'sim':'nao';r.dataset.motion=m?'reduzido':'normal';
    [['theme-choice',theme],['font-choice',p.font],['lines-choice',p.lines],['letters-choice',p.letters]].forEach(([k,v])=>document.querySelectorAll('[data-'+k+']').forEach(b=>b.setAttribute('aria-pressed',String(b.getAttribute('data-'+k)===v))));
    const sw={contrast:p.contrast,underline:p.underline,motion:m};
    menu.querySelectorAll('[data-switch]').forEach(s=>{const on=sw[s.dataset.switch];s.setAttribute('aria-checked',String(on));const st=s.parentNode.querySelector('.a11y-state');if(st)st.textContent=on?'Ligado':'Desligado';});}
  function save(next){prefs=next;sync();status.textContent='';try{localStorage.setItem(KEY,JSON.stringify(next));}catch{}}
  [['theme-choice','theme'],['font-choice','font'],['lines-choice','lines'],['letters-choice','letters']].forEach(([a,k])=>document.querySelectorAll('[data-'+a+']').forEach(b=>b.addEventListener('click',()=>save({...prefs,[k]:b.getAttribute('data-'+a)}))));
  menu.querySelectorAll('[data-switch]').forEach(s=>s.addEventListener('click',()=>{const k=s.dataset.switch,cur=k==='motion'?motion():prefs[k];save({...prefs,[k]:!cur});}));
  menu.querySelector('[data-accessibility-reset]').addEventListener('click',()=>{try{localStorage.removeItem(KEY);}catch{}prefs=def();sync();status.textContent='Preferências restauradas ao padrão. Tema e movimento seguem as configurações do sistema.';});
  const onSys=()=>{if(!prefs.theme||prefs.motion===null)sync();};
  [cs,mq].forEach(q=>q.addEventListener?q.addEventListener('change',onSys):q.addListener&&q.addListener(onSys));
  sync();
})();
