#!/usr/bin/env node
/**
 * Asigna o revoca el rol de moderación usando Firebase Admin SDK.
 * Se ejecuta únicamente por el propietario desde Cloud Shell/servidor con IAM.
 * No se debe llamar desde el navegador ni alojar credenciales en GitHub.
 *
 * Uso:
 *   node firebase/asignar-moderador.mjs --email correo@gmail.com --grant
 *   node firebase/asignar-moderador.mjs --email correo@gmail.com --grant --apply
 *   node firebase/asignar-moderador.mjs --email correo@gmail.com --revoke --apply
 *
 * Sin --apply solo muestra la operación prevista: no cambia permisos.
 */
import { initializeApp, applicationDefault } from 'firebase-admin/app';
import { getAuth } from 'firebase-admin/auth';

const PROJECT_ID = 'cdmx-al-memento';
const args=process.argv.slice(2);
const has=(v)=>args.includes(v);
const index=args.indexOf('--email');
const rawEmail=index>=0?args[index+1]:'';
const email=typeof rawEmail==='string'?rawEmail.trim().toLowerCase():'';
const grant=has('--grant');
const revoke=has('--revoke');
const apply=has('--apply');

function stop(message){
 console.error('Error:',message);
 process.exitCode=1;
}
if(!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)){
 stop('Proporciona --email con la cuenta Google que iniciará sesión en Mi comunidad.');
}else if(grant===revoke){
 stop('Indica exactamente una acción: --grant o --revoke.');
}else if((process.env.GOOGLE_CLOUD_PROJECT||process.env.GCLOUD_PROJECT||PROJECT_ID)!==PROJECT_ID){
 stop('La sesión apunta a otro proyecto. Selecciona cdmx-al-memento antes de continuar.');
}else{
 try{
  const app=initializeApp({credential:applicationDefault(),projectId:PROJECT_ID});
  const auth=getAuth(app);
  const user=await auth.getUserByEmail(email);
  const verifiedGoogle=user.emailVerified &&
   user.providerData.some(provider=>provider.providerId==='google.com');
  if(!verifiedGoogle){
   stop('El usuario no tiene una cuenta Google verificada dentro de este proyecto Firebase.');
  }else{
   const current={...(user.customClaims||{})};
   const next={...current};
   if(grant)next.moderator=true;
   else delete next.moderator;
   console.log('Proyecto:',PROJECT_ID);
   console.log('Cuenta Google verificada:',user.email);
   console.log('Acción:',grant?'Conceder moderación':'Revocar moderación');
   console.log('Conservar otras claims:',Object.keys(current).filter(k=>k!=='moderator').length);
   if(!apply){
    console.log('SIMULACIÓN. No se cambió ningún permiso.');
    console.log('Para aplicar, añade --apply al comando después de verificar la cuenta.');
   }else if((current.moderator===true)===grant){
    console.log('La cuenta ya tenía el rol solicitado. No se requiere ningún cambio.');
   }else{
    await auth.setCustomUserClaims(user.uid,next);
    console.log('Rol actualizado. Cierra la sesión del foro y vuelve a entrar con Google.');
   }
  }
 }catch(error){
  stop('No se pudo consultar o actualizar Firebase Auth: '+(error?.message||String(error)));
 }
}
