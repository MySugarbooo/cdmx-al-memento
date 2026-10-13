'use strict';
/**
 * Pronóstico de referencia por alcaldía: MET Norway Locationforecast 2.0.
 * Datos CC BY 4.0, admiten uso comercial con atribución:
 * https://api.met.no/ ; https://api.met.no/doc/
 * Sin GPS ni clave de pago. Se consultan coordenadas REPRESENTATIVAS, no domicilios.
 */
const BOROUGHS = {
  'La Magdalena Contreras': [19.3083, -99.2417],
  'Álvaro Obregón': [19.3719, -99.2467],
  'Azcapotzalco': [19.4869, -99.1861],
  'Benito Juárez': [19.3806, -99.1625],
  'Coyoacán': [19.3467, -99.1617],
  'Cuajimalpa de Morelos': [19.3597, -99.2892],
  'Cuauhtémoc': [19.4333, -99.1333],
  'Gustavo A. Madero': [19.4978, -99.1256],
  'Iztacalco': [19.3953, -99.0978],
  'Iztapalapa': [19.3574, -99.0926],
  'Miguel Hidalgo': [19.4346, -99.2],
  'Milpa Alta': [19.1928, -99.0236],
  'Tláhuac': [19.2869, -99.0042],
  'Tlalpan': [19.2878, -99.1717],
  'Venustiano Carranza': [19.43, -99.1139],
  'Xochimilco': [19.2578, -99.105]
};

const JSON_HEADERS = {
  'Content-Type': 'application/json; charset=utf-8',
  'X-Content-Type-Options': 'nosniff'
};
function json(body, status=200, ttl=0) {
  return new Response(JSON.stringify(body), {
    status,
    headers:{...JSON_HEADERS,'Cache-Control':ttl?'public, max-age='+ttl+', s-maxage='+ttl:'no-store'}
  });
}
function conditions(symbol){
  const s=String(symbol||'').toLowerCase();
  if(s.includes('thunder'))return {description:'Tormentas',icon:'⛈️'};
  if(s.includes('snow')||s.includes('sleet'))return {description:'Precipitación invernal',icon:'🌨️'};
  if(s.includes('rain')||s.includes('drizzle'))return {description:s.includes('heavy')?'Lluvia intensa':'Posibilidad de lluvia',icon:'🌧️'};
  if(s.includes('fog'))return {description:'Neblina',icon:'🌫️'};
  if(s.includes('cloudy'))return {description:'Nublado',icon:'☁️'};
  if(s.includes('partlycloudy'))return {description:'Parcialmente nublado',icon:'⛅'};
  if(s.includes('fair'))return {description:'Cielo mayormente despejado',icon:'🌤️'};
  if(s.includes('clearsky'))return {description:'Cielo despejado',icon:'☀️'};
  return {description:'Clima variable',icon:'🌸'};
}
function validNumber(x,min,max) {
  const n=Number(x);
  return Number.isFinite(n)&&n>=min&&n<=max?n:null;
}
export async function onRequestGet({request}) {
  const url=new URL(request.url);
  const name=url.searchParams.get('alcaldia')||'Cuauhtémoc';
  if(!Object.hasOwn(BOROUGHS,name))return json({error:'Selecciona una alcaldía válida.'},400);
  const [lat,lon]=BOROUGHS[name];
  const upstream=new URL('https://api.met.no/weatherapi/locationforecast/2.0/compact');
  upstream.searchParams.set('lat',lat.toFixed(4));
  upstream.searchParams.set('lon',lon.toFixed(4));
  try{
    const response=await fetch(upstream.toString(),{
      headers:{
        'User-Agent':'CDMXAlMemento/1.0 (https://cdmx-al-memento.pages.dev/contacto.html)',
        'Accept':'application/json'
      },
      cf:{cacheEverything:true,cacheTtl:1200}
    });
    if(!response.ok)throw Error('MET Norway HTTP '+response.status);
    const responseBody=await response.json();
    const timeseries=responseBody?.properties?.timeseries;
    if(!Array.isArray(timeseries)||!timeseries.length)throw Error('No hay pronóstico meteorológico.');
    const current=timeseries.find(t=>Date.parse(t.time)>=Date.now()-60*60*1000)||timeseries[0];
    const details=current.data?.instant?.details||{};
    const symbol=current.data?.next_1_hours?.summary?.symbol_code||
      current.data?.next_6_hours?.summary?.symbol_code||'';
    const temperature=validNumber(details.air_temperature,-40,55);
    const humidity=validNumber(details.relative_humidity,0,100);
    const windMs=validNumber(details.wind_speed,0,100);
    if(temperature===null)throw Error('Temperatura no disponible');
    const rawExpires=Date.parse(response.headers.get('Expires')||'');
    const seconds=Number.isFinite(rawExpires)?Math.max(300,Math.min(86400,Math.ceil((rawExpires-Date.now())/1000))):1800;
    const {description,icon}=conditions(symbol);
    return json({
      alcaldia:name,
      estimated:true,
      temperature_c:temperature,
      humidity_pct:humidity,
      wind_kmh:windMs===null?null:Math.round(windMs*3.6),
      description,icon,
      forecast_for:current.time,
      source:'MET Norway',
      source_url:'https://api.met.no/',
      // La fecha corresponde a la hora del pronóstico, no a una medición local.
      note:'Pronóstico estimado para una coordenada de referencia; no es medición en calle.'
    },200,seconds);
  }catch(error){
    // No inventar valores ni ocultar que los datos no están disponibles.
    return json({alcaldia:name,error:'No está disponible el pronóstico en este momento.'},503);
  }
}
