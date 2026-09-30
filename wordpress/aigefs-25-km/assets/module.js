(() => {'use strict';
document.querySelectorAll('[data-aigefs]').forEach(async (root,index) => {
 const $=s=>root.querySelector(s), base=root.dataset.source.replace(/\/$/,''),status=$('[data-status]');
 const load=async path=>{const response=await fetch(base+'/'+path,{cache:'no-cache'});if(!response.ok)throw Error('Données indisponibles (HTTP '+response.status+').');return response.json();};
 const add=(select,value,label)=>{const option=document.createElement('option');option.value=value;option.textContent=label;select.append(option);};
 const integer=v=>new Intl.NumberFormat('fr-FR',{maximumFractionDigits:0}).format(Math.round(v));
 const number=(v,unit,key)=>{if(!Number.isFinite(v))return '—';if(key==='temperature'){const low=Math.floor(v),high=Math.ceil(v);return (low===high?integer(low):integer(low)+' à '+integer(high))+' °C';}if(unit==='km/h')return integer(Math.ceil(v/5)*5)+' km/h';if(unit==='%'||unit==='hPa')return integer(v)+' '+unit;return new Intl.NumberFormat('fr-FR',{maximumFractionDigits:1}).format(v)+' '+unit;};
 try {
  const manifest=await load('index.json');
  if(manifest.members!==31||manifest.status!=='ok')throw Error('Publication AIGEFS incomplète.');
  status.textContent='Run '+new Date(manifest.run).toLocaleString('fr-FR',{timeZone:'Europe/Paris'})+' · 31 membres · '+manifest.commune_count+' communes';
  Object.entries(manifest.products).forEach(([key,spec])=>add($('[data-product]'),key,spec.label));
  manifest.steps.forEach(h=>add($('[data-step]'),h,'H+'+h));
  if(manifest.steps.includes(24))$('[data-step]').value='24';
  const refresh=()=>{const product=$('[data-product]').value,stat=$('[data-stat]').value,region=$('[data-region]').value;
   const spec=manifest.products[product],allowed=spec.steps||manifest.steps,oldStep=Number($('[data-step]').value);$('[data-step]').replaceChildren();allowed.forEach(h=>add($('[data-step]'),h,'H+'+h));$('[data-step]').value=String(allowed.includes(oldStep)?oldStep:allowed[0]);const step=$('[data-step]').value;
   const img=$('[data-map]');img.hidden=false;img.src=base+'/maps/'+region+'-'+product+'-'+stat+'-'+step+'.svg';img.alt=manifest.products[product].label+' · '+$('[data-stat]').selectedOptions[0].textContent+' · H+'+step;
   img.onerror=()=>{img.hidden=true;$('[data-period]').textContent='Carte indisponible pour cette sélection.';};
   const end=Date.parse(manifest.run)+Number(step)*3600000,format=t=>new Date(t).toLocaleString('fr-FR',{timeZone:'Europe/Paris'});
   $('[data-period]').textContent=spec.period?'Période : '+format(spec.period==='run'?Date.parse(manifest.run):end-spec.period*3600000)+' → '+format(end):'Validité : '+format(end);};
  ['region','product','stat','step'].forEach(key=>$('[data-'+key+']').addEventListener('change',refresh));
  $('[data-zoom]').addEventListener('input',event=>$('[data-map]').style.width='calc(min(100%, 1100px) * '+Number(event.target.value)+')');refresh();
  const cities=await load('communes.json'), list=$('datalist');list.id='aigefs-cities-'+index;$('[data-city]').setAttribute('list',list.id);
  const search=()=>{list.replaceChildren();const query=$('[data-city]').value.toLocaleLowerCase('fr');if(query.length<2)return;cities.filter(c=>(c[1]+' '+c[0]).toLocaleLowerCase('fr').includes(query)).slice(0,40).forEach(c=>add(list,c[1]+' ('+c[0]+')',c[1]+' ('+c[0]+')'));};
  $('[data-city]').addEventListener('input',search);
  let requestId=0,locationId=0,selectedCity=null;
  const displayCity=async c=>{const id=++requestId;try{
   selectedCity=c;
   $('[data-head]').replaceChildren();$('[data-body]').replaceChildren();
   $('[data-city-status]').textContent='Chargement…';const dep=await load('departements/'+c[2]+'.json');const commune=dep.communes.find(row=>row[0]===c[0]);if(!commune)throw Error('Commune absente de la publication.');
   if(id!==requestId)return;
   $('[data-head]').replaceChildren();$('[data-body]').replaceChildren();const hr=document.createElement('tr'),shortLabels={precipitation:'Cumul (mm)',rain6:'Pluie 6 h',temperature:'T° à 2 m',vent:'Vent 10 m',nuages:'Nuages',humidity:'Humidité',pressure:'Pression'};const dayHead=document.createElement('th'),timeHead=document.createElement('th');dayHead.textContent='Jour';dayHead.className='aigefs-day-head';timeHead.textContent='Heure';timeHead.className='aigefs-time-head';hr.append(dayHead);hr.append(timeHead);Object.entries(manifest.products).forEach(([key,p])=>{const th=document.createElement('th');th.textContent=shortLabels[key]||p.label;th.title=p.label+' ('+p.unit+')';hr.append(th);});$('[data-head]').append(hr);
   const stat=$('[data-table-stat]').value,forecast=stat==='mean'?dep.forecast:dep.forecast_statistics?.[stat];if(!forecast)throw Error('Cette statistique communale sera disponible après la prochaine production.');const dayCounts=new Map();forecast.forEach(([date])=>{const key=new Date(date).toLocaleDateString('fr-CA',{timeZone:'Europe/Paris'});dayCounts.set(key,(dayCounts.get(key)||0)+1);});let previousDay='',dayIndex=-1;
   forecast.forEach(([date,rows])=>{const tr=document.createElement('tr'),valid=new Date(date),dayKey=valid.toLocaleDateString('fr-CA',{timeZone:'Europe/Paris'});if(dayKey!==previousDay){dayIndex++;previousDay=dayKey;}tr.className='aigefs-day-'+dayIndex%4;if(dayCounts.has(dayKey)){const dayCell=document.createElement('td'),weekday=document.createElement('strong'),shortDate=document.createElement('span'),label=valid.toLocaleDateString('fr-FR',{timeZone:'Europe/Paris',weekday:'short'});dayCell.className='aigefs-forecast-day';dayCell.rowSpan=dayCounts.get(dayKey);weekday.textContent=label.charAt(0).toLocaleUpperCase('fr-FR')+label.slice(1);shortDate.textContent=valid.toLocaleDateString('fr-FR',{timeZone:'Europe/Paris',day:'2-digit',month:'2-digit'});dayCell.append(weekday);dayCell.append(shortDate);tr.append(dayCell);dayCounts.delete(dayKey);}const timeCell=document.createElement('td');timeCell.className='aigefs-forecast-time';timeCell.textContent=valid.toLocaleTimeString('fr-FR',{timeZone:'Europe/Paris',hour:'2-digit',minute:'2-digit'});tr.append(timeCell);Object.entries(manifest.products).forEach(([key,p])=>{const cell=document.createElement('td');cell.textContent=number(rows[commune[6]][p.column],p.unit,key);tr.append(cell);});$('[data-body]').append(tr);});
   $('[data-city-status]').textContent=c[1]+' · maille la plus proche · '+$('[data-table-stat]').selectedOptions[0].textContent.toLocaleLowerCase('fr');
  }catch(error){if(id===requestId)$('[data-city-status]').textContent=error.message;}};
  const show=()=>{locationId++;const query=$('[data-city]').value.trim(),matches=cities.filter(c=>query===c[0]||query===c[1]+' ('+c[0]+')'||query.toLocaleLowerCase('fr')===c[1].toLocaleLowerCase('fr'));
   if(matches.length!==1){requestId++;$('[data-head]').replaceChildren();$('[data-body]').replaceChildren();$('[data-city-status]').textContent=matches.length?'Plusieurs communes portent ce nom : choisissez dans la liste.':'Saisissez une commune puis choisissez une proposition dans la liste.';return;}displayCity(matches[0]);};
  $('[data-show]').disabled=false;$('[data-show]').addEventListener('click',show);
  $('[data-table-stat]').addEventListener('change',()=>{if(selectedCity)displayCity(selectedCity);});
  $('[data-city]').addEventListener('keydown',event=>{if(event.key==='Enter'){event.preventDefault();show();}});
  const locate=$('[data-locate]');let placesPromise;
  locate.disabled=false;
  locate.addEventListener('click',()=>{
   if(!window.isSecureContext||!navigator.geolocation){$('[data-city-status]').textContent='Géolocalisation indisponible : utilisez une connexion HTTPS ou choisissez votre commune.';return;}
   const id=++locationId;requestId++;locate.disabled=true;$('[data-city-status]').textContent='Localisation en cours… Autorisez la demande du navigateur.';
   navigator.geolocation.getCurrentPosition(async position=>{try{
    if(id!==locationId)return;
    if(!placesPromise)placesPromise=fetch(root.dataset.places).then(response=>{if(!response.ok)throw Error('Catalogue de localisation indisponible.');return response.json();}).catch(error=>{placesPromise=null;throw error;});
    const places=await placesPromise;if(id!==locationId)return;
    const {latitude,longitude}=position.coords,rad=Math.PI/180;let nearest=null,best=Infinity;
    if(!Number.isFinite(latitude)||!Number.isFinite(longitude))throw Error('Position indisponible : choisissez votre commune.');
    const available=new Set(cities.map(c=>c[0]));
    for(const point of places){if(!available.has(point[0]))continue;const a=Math.sin((point[1]-latitude)*rad/2)**2+Math.cos(latitude*rad)*Math.cos(point[1]*rad)*Math.sin((point[2]-longitude)*rad/2)**2;const distance=6371*2*Math.asin(Math.sqrt(Math.min(1,a)));if(distance<best){best=distance;nearest=point;}}
    if(!nearest||best>50)throw Error('Position hors de la zone couverte (France métropolitaine et Corse). Choisissez une commune manuellement.');
    const city=cities.find(c=>c[0]===nearest[0]);$('[data-city]').value=city[1]+' ('+city[0]+')';await displayCity(city);
   }catch(error){if(id===locationId)$('[data-city-status]').textContent=error.message;}finally{locate.disabled=false;}},error=>{
    locate.disabled=false;if(id!==locationId)return;
    $('[data-city-status]').textContent=error.code===1?'Localisation refusée. Vous pouvez choisir votre commune manuellement.':error.code===3?'La localisation a expiré. Réessayez ou choisissez votre commune.':'Position indisponible. Choisissez votre commune manuellement.';
   },{enableHighAccuracy:false,timeout:15000,maximumAge:300000});
  });
 }catch(error){status.textContent=error.message+' Aucune valeur fictive affichée.';}
});})();
