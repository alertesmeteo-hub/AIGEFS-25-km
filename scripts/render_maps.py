"""Vector isobands: retain readable text when zooming."""
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap,BoundaryNorm
import shapefile

REGIONS={'france':(-6,10.5,41,52),'europe':(-25,45,30,72)}
PRODUCTS={
 'precipitation':{'label':'Précipitations totales depuis le run (équivalent eau)','unit':'mm','column':12,'period':'run','levels':[0,.1,1,2,5,10,20,30,50,75,100,150,200,300]},
 'rain6':{'label':'Précipitations sur les 6 dernières heures','unit':'mm','column':2,'period':6,'levels':[0,.1,1,2,5,10,20,30,50,75,100,150,200,300]},
 'temperature':{'label':'Température à 2 m','unit':'°C','column':0,'levels':list(range(-30,43,3))},
 'vent':{'label':'Vent à 10 m','unit':'km/h','column':4,'levels':list(range(0,125,5))},
 'pressure':{'label':'Pression au niveau de la mer','unit':'hPa','column':7,'levels':list(range(950,1055,5))},
}
LABELS={'mean':'Moyenne','median':'Médiane','p10':'Percentile 10','p90':'Percentile 90'}

def render(lon,lat,values,product,stat,region,run,step,destination):
    spec=PRODUCTS[product];west,east,south,north=REGIONS[region]
    fig,ax=plt.subplots(figsize=(12,8))
    x=(lon>=west-1)&(lon<=east+1);y=(lat>=south-1)&(lat<=north+1)
    options={'cmap':'turbo'}
    if product in ('precipitation','rain6'):
        cmap=ListedColormap(['#fff','#e1f1ff','#a3d2ff','#4aa1ef','#2064d2','#19babb','#19b34b','#94d925','#f5e42a','#ffac27','#f35d25','#dc1640','#aa168d'])
        cmap.set_under('#fff');cmap.set_over('#650075')
        options={'cmap':cmap,'norm':BoundaryNorm(spec['levels'],cmap.N)}
    contour=ax.contourf(lon[x],lat[y],values[np.ix_(y,x)],levels=spec['levels'],extend='both',**options)
    for name in ('ne_50m_coastline','ne_50m_admin_0_boundary_lines_land'):
        with shapefile.Reader(str(Path('config/natural-earth')/name)) as reader:
            for shape in reader.shapes():
                if shape.bbox[2]<west or shape.bbox[0]>east or shape.bbox[3]<south or shape.bbox[1]>north:continue
                points=np.asarray(shape.points);parts=list(shape.parts)+[len(points)]
                for a,b in zip(parts,parts[1:]):ax.plot(points[a:b,0],points[a:b,1],color='#314b56',linewidth=.45)
    ax.set(xlim=(west,east),ylim=(south,north));ax.set_aspect(1/np.cos(np.deg2rad((south+north)/2)))
    ax.set_xticks([]);ax.set_yticks([])
    from datetime import timedelta
    valid=run+timedelta(hours=step)
    period=''
    if 'period' in spec:
        start=run if spec['period']=='run' else valid-timedelta(hours=spec['period'])
        period=f'\nPériode : {start:%d/%m %H} UTC → {valid:%d/%m %H} UTC'
    ax.set_title(f"AIGEFS 0,25° · {spec['label']} ({spec['unit']})\n{LABELS[stat]} des 31 membres · {run:%d/%m/%Y %H} UTC · H+{step}"+period,fontsize=10)
    bar=fig.colorbar(contour,ax=ax,fraction=.04,pad=.02);bar.set_label(spec['unit'])
    if bar.solids is not None:bar.solids.set_rasterized(False)
    fig.canvas.draw();center=ax.get_position().x0+ax.get_position().width/2
    fig.text(center,.06,'www.alertes-meteo.com',ha='center',color='#ff3333',weight='bold',bbox={'facecolor':'black','pad':5})
    fig.text(center,.02,'NOAA/NCEP · AIGEFS opérationnel · grille diffusée 0,25°',ha='center',fontsize=8)
    destination=Path(destination);destination.parent.mkdir(parents=True,exist_ok=True)
    fig.savefig(destination,facecolor='white',bbox_inches='tight',pad_inches=.12);plt.close(fig)
