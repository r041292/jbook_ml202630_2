"""Contenido de desplegables bajo demanda y caché temporal compartida por workers.

Los datos científicos no se modifican. El navegador recibe el cuerpo de cada
desplegable solo al abrirlo. No se usa validation_layout con el árbol completo.
"""
import copy
import gzip
import hashlib
import json
import re
import time
from pathlib import Path

from dash import Input, Output, MATCH, html, no_update
from flask import request
from plotly.utils import PlotlyJSONEncoder

PROJECT = hashlib.sha256(str(Path(__file__).resolve().parent).encode()).hexdigest()[:16]
CACHE_DIR = Path(__file__).resolve().parent / '.ui_cache'
FACTORIES = {}


def lazy_factory(label,factory,key):
    """Factorías estáticas registradas en cada worker; no hacen fit/predict."""
    token=hashlib.sha256(('factory:'+PROJECT+':'+key).encode()).hexdigest()
    FACTORIES[token]=factory
    return html.Details([html.Summary(label,id={'type':'lazy-detail-toggle','key':token},n_clicks=0),
                         html.Div(id={'type':'lazy-detail-body','key':token})],
                        id={'type':'lazy-detail-container','key':token},open=False,className='details')


def _serialize(value):
    return json.dumps(value,cls=PlotlyJSONEncoder,ensure_ascii=False,separators=(',',':'))


def _save(body,scope):
    payload=_serialize(body)
    token=hashlib.sha256((scope+'\0'+payload).encode('utf-8')).hexdigest()
    CACHE_DIR.mkdir(exist_ok=True)
    target=CACHE_DIR/(token+'.json')
    if not target.exists():
        # Todos los escritores del mismo hash producen los mismos bytes.
        # Evita renombrados bloqueados por algunos entornos Windows.
        target.write_text(payload,encoding='utf-8')
    return token


def defer_details(value,scope='page',path='root'):
    """Devuelve un árbol nuevo; no muta los componentes/figuras originales."""
    if isinstance(value,(list,tuple)):
        return [defer_details(v,scope,path+'.'+str(i)) for i,v in enumerate(value)]
    if isinstance(value,dict) and 'namespace' in value and 'type' in value:
        props=value.get('props',{})
        kind=value['type']
        children=props.get('children')
        is_details=kind=='Details' and value['namespace']=='dash_html_components'
        if is_details and not props.get('open'):
            items=children if isinstance(children,list) else [children]
            if items and isinstance(items[0],dict) and items[0].get('type')=='Summary':
                summary=copy.deepcopy(items[0]);summary_props=summary.setdefault('props',{})
                if not summary_props.get('id'):
                    token=_save(items[1:],scope+':'+path)
                    summary_props.update(id={'type':'lazy-detail-toggle','key':token},n_clicks=0)
                    result=copy.deepcopy(value)
                    result['props']['children']=[summary,html.Div(id={'type':'lazy-detail-body','key':token})]
                    result['props'].update(id={'type':'lazy-detail-container','key':token},open=False)
                    return result
        result={**value,'props':dict(props)}
        if value['namespace']=='dash_core_components' and kind in ('Dropdown','RadioItems','Input','Slider'):
            result['props'].setdefault('persistence',True)
            result['props'].setdefault('persistence_type','session')
        if children is not None:result['props']['children']=defer_details(children,scope,path+'.children')
        return result
    if hasattr(value,'to_plotly_json') and hasattr(value,'children'):
        if isinstance(value,html.Details) and not getattr(value,'open',False):
            children=value.children if isinstance(value.children,(list,tuple)) else [value.children]
            if children and isinstance(children[0],html.Summary) and not getattr(children[0],'id',None):
                token=_save(children[1:],scope+':'+path)
                summary=copy.copy(children[0]);summary.id={'type':'lazy-detail-toggle','key':token};summary.n_clicks=0
                result=copy.copy(value)
                result.children=[summary,html.Div(id={'type':'lazy-detail-body','key':token})]
                result.id={'type':'lazy-detail-container','key':token};result.open=False
                return result
        result=copy.copy(value)
        if 'persistence' in getattr(value,'_prop_names',[]):
            result.persistence=getattr(value,'persistence',True)
            result.persistence_type=getattr(value,'persistence_type','session')
        result.children=defer_details(value.children,scope,path+'.children')
        return result
    if hasattr(value,'to_plotly_json') and 'persistence' in getattr(value,'_prop_names',[]):
        result=copy.copy(value)
        result.persistence=getattr(value,'persistence',True)
        result.persistence_type=getattr(value,'persistence_type','session')
        return result
    return value


def load_detail(token):
    if not isinstance(token,str) or not re.fullmatch('[0-9a-f]{64}',token):
        raise ValueError('Identificador de detalle no válido.')
    if token in FACTORIES:
        return defer_details(FACTORIES[token](),scope=token)
    path=CACHE_DIR/(token+'.json')
    if not path.exists():
        return html.P('Vuelve a abrir esta pestaña para cargar el detalle actualizado.')
    for attempt in range(10):
        try:
            body=json.loads(path.read_text(encoding='utf-8'))
            return defer_details(body,scope=token)
        except json.JSONDecodeError:
            if attempt==9:raise
            time.sleep(.03)


def install(app):
    @app.callback(Output({'type':'lazy-detail-body','key':MATCH},'children'),
                  Output({'type':'lazy-detail-container','key':MATCH},'open'),
                  Input({'type':'lazy-detail-toggle','key':MATCH},'n_clicks'),
                  prevent_initial_call=True)
    def detail(clicks):
        from dash import ctx
        if not clicks:return no_update,no_update
        # El cierre elimina los gráficos del DOM y libera sus recursos.
        return (load_detail(ctx.triggered_id['key']),True) if clicks%2 else ([],False)

    @app.server.after_request
    def compress_json(response):
        if response.mimetype=='application/json':response.vary.add('Accept-Encoding')
        if (response.status_code==200 and response.mimetype=='application/json'
                and request.method!='HEAD' and 'gzip' in request.headers.get('Accept-Encoding','')
                and not response.headers.get('Content-Encoding') and not response.direct_passthrough):
            raw=response.get_data()
            if len(raw)>1024:
                packed=gzip.compress(raw,compresslevel=5,mtime=0)
                if len(packed)<len(raw):
                    response.set_data(packed)
                    response.headers['Content-Encoding']='gzip'
                    response.vary.add('Accept-Encoding')
        return response
