// Renders scene files (written by scenes.py) to PNG line-and-shade drawings.
//   node render.js <three.min.js> <scene folder> <output folder>
// Uses the headless browser's WebGL. Each scene is JSON: parts (triangles, colour,
// position), dashed guide lines for exploded views, and text labels with leaders.
const fs = require('fs');
const path = require('path');
const { chromium } = require('playwright');

const PAGE = (three) => `<!doctype html><html><body style="margin:0;background:#fff">
<script src="file://${three}"></script>
<script>
function b64f32(s){const b=atob(s);const u=new Uint8Array(b.length);for(let i=0;i<b.length;i++)u[i]=b.charCodeAt(i);return new Float32Array(u.buffer);}
function b64u32(s){const b=atob(s);const u=new Uint8Array(b.length);for(let i=0;i<b.length;i++)u[i]=b.charCodeAt(i);return new Uint32Array(u.buffer);}
window.renderScene = function(sc){
  const SS=2;                                      // draw at twice the size, then shrink: smooth, bold lines
  const W=sc.width*SS,H=sc.height*SS;
  const renderer=new THREE.WebGLRenderer({antialias:true,preserveDrawingBuffer:true,alpha:false});
  renderer.setPixelRatio(1);renderer.setSize(W,H);renderer.setClearColor(0xffffff,1);
  const scene=new THREE.Scene();
  scene.add(new THREE.AmbientLight(0xffffff,1.25));
  const meshes=[];
  const az=sc.view[0]*Math.PI/180, el=sc.view[1]*Math.PI/180;
  const dir=new THREE.Vector3(Math.cos(el)*Math.cos(az),Math.cos(el)*Math.sin(az),Math.sin(el));
  const pts=[];
  for(const p of sc.parts){
    const g=new THREE.BufferGeometry();
    const pos=b64f32(p.v);
    g.setAttribute('position',new THREE.BufferAttribute(pos,3));
    g.setIndex(new THREE.BufferAttribute(b64u32(p.f),1));
    g.computeVertexNormals();
    const col=new THREE.Color(p.color[0],p.color[1],p.color[2]);
    const mat=new THREE.MeshLambertMaterial({color:col,polygonOffset:true,polygonOffsetFactor:1.5,polygonOffsetUnits:1.5,
      transparent:p.alpha<1,opacity:p.alpha,side:THREE.DoubleSide});
    const m=new THREE.Mesh(g,mat);m.position.set(p.pos[0],p.pos[1],p.pos[2]);scene.add(m);meshes.push(m);
    const eg=new THREE.EdgesGeometry(g,p.edge_angle||30);
    const ec=new THREE.Color(p.edge[0],p.edge[1],p.edge[2]);
    const ln=new THREE.LineSegments(eg,new THREE.LineBasicMaterial({color:ec,transparent:p.alpha<1,opacity:Math.min(1,p.alpha+0.25)}));
    ln.position.copy(m.position);scene.add(ln);
    for(let i=0;i<pos.length;i+=3)pts.push(new THREE.Vector3(pos[i]+p.pos[0],pos[i+1]+p.pos[1],pos[i+2]+p.pos[2]));
  }
  for(const g of sc.guides||[]){
    const geo=new THREE.BufferGeometry().setFromPoints([new THREE.Vector3(...g.a),new THREE.Vector3(...g.b)]);
    const l=new THREE.Line(geo,new THREE.LineDashedMaterial({color:0xd9541e,dashSize:g.dash||3,gapSize:g.gap||2.2,depthTest:false}));
    l.computeLineDistances();l.renderOrder=10;scene.add(l);
    pts.push(new THREE.Vector3(...g.a),new THREE.Vector3(...g.b));
  }
  // orthographic camera fitted to everything
  const up=new THREE.Vector3(0,0,1);
  let right=new THREE.Vector3().crossVectors(up,dir);
  if(right.length()<1e-6)right.set(1,0,0);           // looking straight down: X to the right
  right.normalize();
  const cu=new THREE.Vector3().crossVectors(dir,right).normalize();
  let minx=1e9,maxx=-1e9,miny=1e9,maxy=-1e9,mind=1e9,maxd=-1e9;
  for(const v of pts){const d=v.dot(dir);if(d<mind)mind=d;if(d>maxd)maxd=d;}
  let fit=pts;
  if(sc.focus){fit=[];const f=sc.focus;                // frame just this box: xmin,xmax,ymin,ymax,zmin,zmax
    for(const x of [f[0],f[1]])for(const y of [f[2],f[3]])for(const z of [f[4],f[5]])fit.push(new THREE.Vector3(x,y,z));}
  for(const v of fit){const x=v.dot(right),y=v.dot(cu);
    if(x<minx)minx=x;if(x>maxx)maxx=x;if(y<miny)miny=y;if(y>maxy)maxy=y;}
  const pad=sc.pad||[0.12,0.12,0.12,0.12];           // left, right, top, bottom, as a share of the picture
  const w=(maxx-minx),h=(maxy-miny);
  let fw=w/(1-pad[0]-pad[1]),fh=h/(1-pad[2]-pad[3]);   // frame that leaves the asked-for margins
  const aspect=W/H;
  let left=minx-pad[0]*fw, bottom=miny-pad[3]*fh;
  if(fw/fh<aspect){const nw=fh*aspect;left-=(nw-fw)/2;fw=nw;}
  else{const nh=fw/aspect;bottom-=(nh-fh)/2;fh=nh;}
  const cam=new THREE.OrthographicCamera(left,left+fw,bottom+fh,bottom,-(maxd-mind)-2000,(maxd-mind)+2000);
  cam.up.copy(cu);
  cam.position.copy(dir.clone().multiplyScalar(maxd+500));
  cam.lookAt(dir.clone().multiplyScalar(maxd+500).sub(dir));
  cam.updateMatrixWorld();cam.updateProjectionMatrix();
  const key=new THREE.DirectionalLight(0xffffff,1.75);
  key.position.copy(dir.clone().multiplyScalar(2).add(cu.clone().multiplyScalar(1.6)).add(right.clone().multiplyScalar(-1.3)));scene.add(key);
  renderer.render(scene,cam);
  // thicken the outlines: redraw only the lines, nudged a pixel or two, hidden parts still hidden
  renderer.autoClear=false;
  for(const m of meshes)m.material.colorWrite=false;
  for(const [ox,oy] of [[1,0],[0,1],[1,1],[2,1],[1,2]]){
    renderer.clearDepth();cam.setViewOffset(W,H,ox,oy,W,H);cam.updateProjectionMatrix();renderer.render(scene,cam);}
  cam.clearViewOffset();cam.updateProjectionMatrix();
  // 2D overlay: labels, arrows
  const cv=document.createElement('canvas');cv.width=W;cv.height=H;const c=cv.getContext('2d');
  c.drawImage(renderer.domElement,0,0);
  const proj=(a)=>{const v=new THREE.Vector3(...a).project(cam);return [(v.x+1)/2*W,(1-v.y)/2*H];};
  const S=(sc.scale||1)*SS;
  for(const a of sc.arrows||[]){
    const p=proj(a.a),q=proj(a.b);
    c.strokeStyle=a.color||'#d9541e';c.fillStyle=c.strokeStyle;c.lineWidth=5*S;c.lineCap='round';
    c.beginPath();c.moveTo(p[0],p[1]);c.lineTo(q[0],q[1]);c.stroke();
    const an=Math.atan2(q[1]-p[1],q[0]-p[0]),L=20*S;
    c.beginPath();c.moveTo(q[0]+Math.cos(an)*L*0.5,q[1]+Math.sin(an)*L*0.5);
    c.lineTo(q[0]-Math.cos(an-0.5)*L,q[1]-Math.sin(an-0.5)*L);c.lineTo(q[0]-Math.cos(an+0.5)*L,q[1]-Math.sin(an+0.5)*L);c.closePath();c.fill();
  }
  const out=[];
  for(const l of sc.labels||[]){
    const p=proj(l.at);const tx=p[0]+l.dx*S,ty=p[1]+l.dy*S;
    c.font=(l.bold?'600 ':'')+Math.round((l.size||36)*S)+'px Helvetica, Arial, sans-serif';
    const lines=l.text.split('\\n');const lh=(l.size||36)*S*1.22;
    let tw=0;for(const s of lines)tw=Math.max(tw,c.measureText(s).width);
    const bw=tw+18*S,bh=lh*lines.length+10*S;
    let bx=tx-(l.dx<0?bw:0),by=ty-bh/2;
    bx=Math.max(4,Math.min(W-bw-4,bx));by=Math.max(4,Math.min(H-bh-4,by));
    const ax=Math.max(bx,Math.min(bx+bw,p[0])),ay=Math.max(by,Math.min(by+bh,p[1]));
    c.strokeStyle='#30363d';c.lineWidth=2*S;c.beginPath();c.moveTo(p[0],p[1]);c.lineTo(l.dx<0?bx+bw:bx,by+bh/2);c.stroke();
    c.fillStyle='#30363d';c.beginPath();c.arc(p[0],p[1],4.5*S,0,7);c.fill();
    c.fillStyle=l.fill||'#ffffff';c.strokeStyle=l.stroke||'#30363d';c.lineWidth=2*S;
    c.beginPath();c.roundRect(bx,by,bw,bh,7*S);c.fill();c.stroke();
    c.fillStyle='#111';c.textBaseline='middle';
    lines.forEach((s,i)=>c.fillText(s,bx+9*S,by+5*S+lh*(i+0.5)));
    out.push([bx,by,bw,bh]);
  }
  const small=document.createElement('canvas');small.width=sc.width;small.height=sc.height;
  const sc2=small.getContext('2d');sc2.imageSmoothingQuality='high';sc2.drawImage(cv,0,0,sc.width,sc.height);
  return small.toDataURL('image/png');
};
</script></body></html>`;

(async () => {
  const [three, sceneDir, outDir] = process.argv.slice(2).map((p) => path.resolve(p));
  const only = process.argv.slice(5);
  fs.mkdirSync(outDir, { recursive: true });
  const pageFile = path.join(sceneDir, '_page.html');
  fs.writeFileSync(pageFile, PAGE(three));
  const browser = await chromium.launch({ args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
  const page = await browser.newPage();
  page.on('pageerror', (e) => console.log('page error:', e.message));
  await page.goto('file://' + pageFile);
  for (const f of fs.readdirSync(sceneDir).filter((n) => n.endsWith('.json')).sort()) {
    if (only.length && !only.includes(f.replace('.json', ''))) continue;
    const sc = JSON.parse(fs.readFileSync(path.join(sceneDir, f)));
    const url = await page.evaluate((s) => window.renderScene(s), sc);
    fs.writeFileSync(path.join(outDir, f.replace('.json', '.png')), Buffer.from(url.split(',')[1], 'base64'));
    console.log('rendered', f.replace('.json', '.png'));
  }
  await browser.close();
})();
