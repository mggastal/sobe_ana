#!/usr/bin/env python3
"""
Dashboard Ana — Sobé Estratégias
Gera data.json para o template-vendas-perpetuo.html em sobe-template
"""

import pandas as pd, json, re, hashlib, requests
from datetime import date
from pathlib import Path

# ══════════════════════════════════════════════════════
# CONFIG
# ══════════════════════════════════════════════════════
SHEET_ID         = "1rY6i930k9WkzYGSUrbQeGk-L7pU-hkdLOUFB9RqvVg8"
OUTPUT_JSON      = "data.json"

NOME_CLIENTE     = "Ana"
LOGO_LETRA       = "ANA"
COR_ACENTO       = "#0ea5e9"

LANCAMENTO_COD   = "EST01"
USAR_PESQUISA    = True
USAR_GOOGLE      = False

FUNIL_IMPRESSOES  = True
FUNIL_LINK_CLICKS = True
FUNIL_PAGE_VIEW   = True
FUNIL_LEADS       = True

MOEDA            = "BRL"

_MOEDA_MAP = {
    "BRL": {"simbolo": "R$", "locale": "pt-BR"},
    "USD": {"simbolo": "$",  "locale": "en-US"},
    "EUR": {"simbolo": "€",  "locale": "de-DE"},
    "ARS": {"simbolo": "$",  "locale": "es-AR"},
}
_moeda_cfg    = _MOEDA_MAP.get(MOEDA, _MOEDA_MAP["BRL"])
MOEDA_SIMBOLO = _moeda_cfg["simbolo"]
MOEDA_LOCALE  = _moeda_cfg["locale"]

CPL_BOM          = 2.0
CPL_MEDIO        = 3.0
CTR_BOM          = 1.2
CTR_MEDIO        = 1.0
CR_BOM           = 40.0
CR_MEDIO         = 25.0
TX_CONV_BOM      = 30.0
TX_CONV_MEDIO    = 15.0
CPM_BOM          = 5.0
CPM_MEDIO        = 12.0

# ══════════════════════════════════════════════════════
def sheet_url(t): return f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={t}"
URL_META = sheet_url("meta-ads")
URL_GA   = sheet_url("breakdown-gender-age")
URL_PT   = sheet_url("breakdown-platform")

def to_num(s):
    if pd.api.types.is_numeric_dtype(s): return s.fillna(0)
    clean = s.astype(str).str.strip().str.replace("R$","",regex=False).str.strip()
    if clean.str.contains(r"\d,\d", regex=True).any():
        clean = clean.str.replace(".","",regex=False).str.replace(",",".",regex=False)
    return pd.to_numeric(clean, errors="coerce").fillna(0)

def safe(v):
    if v is None or (isinstance(v,float) and pd.isna(v)): return None
    return round(float(v),2) if float(v)!=0 else None

def download_thumb(url, d):
    if not url or str(url)=="nan": return ""
    try:
        ext=".png" if ".png" in url.lower() else ".jpg"
        fname=hashlib.md5(url.encode()).hexdigest()[:16]+ext
        fp=d/fname
        if not fp.exists():
            r=requests.get(url,timeout=10,headers={"User-Agent":"Mozilla/5.0"})
            if r.status_code==200: fp.write_bytes(r.content)
            else: return ""
        return "imgs/"+fname
    except: return ""

# ══ META ADS ══════════════════════════════════════════
CONV_COLS = ["Action Leads"]
SALES_COLS = ["Action Omni Purchase"]

def load_meta():
    print("  Lendo meta-ads...")
    df=pd.read_csv(URL_META)
    df=df.rename(columns={
        "Date":"date","Campaign Name":"campaign","Adset Name":"adset",
        "Ad Name":"ad","Thumbnail URL":"thumb","Status":"status",
        "Spend (Cost, Amount Spent)":"spend","Impressions":"impressions",
        "Action Link Clicks":"link_clicks","Action Landing Page View":"page_view",
        "Clicks":"clicks","Reach (Estimated)":"reach",
        "Action Post Engagement":"engagement","Action Post Shares":"shares",
        "Action Post Comments":"comments",
        "Action Post Save (Onsite Conversion)":"saves",
        "Video Thruplay Watched Actions":"thruplay",
    })
    df["date"]=pd.to_datetime(df["date"],errors="coerce")
    if "status" not in df.columns: df["status"]=""
    df["status"]=df["status"].astype(str).str.strip().str.upper()
    for c in ["spend","impressions","link_clicks","page_view","clicks"]:
        if c in df.columns: df[c]=to_num(df[c])
    if "clicks" not in df.columns: df["clicks"]=df["link_clicks"]
    for _col in ["reach","engagement","shares","comments","saves","thruplay"]:
        if _col not in df.columns: df[_col]=0
        else: df[_col]=to_num(df[_col])
    df["leads"]=sum(to_num(df[c]) for c in CONV_COLS if c in df.columns)
    print(f"     Coluna leads: {', '.join(c for c in CONV_COLS if c in df.columns)}")
    df["sales"]=sum(to_num(df[c]) for c in SALES_COLS if c in df.columns) if any(c in df.columns for c in SALES_COLS) else 0
    print(f"     Coluna vendas: {', '.join(c for c in SALES_COLS if c in df.columns) or 'não encontrada'}")
    df["is_lct"]=df["campaign"].str.contains(LANCAMENTO_COD,na=False,case=False) if LANCAMENTO_COD else True
    df=df.dropna(subset=["date"])
    print(f"     {len(df)} linhas | {df['date'].min().date()} → {df['date'].max().date()}")
    print(f"     Total leads: {df['leads'].sum():.0f} | Total vendas: {df['sales'].sum():.0f}")
    return df

def calc_kpis(p):
    sp=float(p["spend"].sum()); imp=float(p["impressions"].sum())
    lc=float(p["link_clicks"].sum()); pv=float(p["page_view"].sum())
    ld=float(p["leads"].sum()); cl=float(p["clicks"].sum()) if "clicks" in p.columns else lc
    return {"spend":round(sp,2),"impressions":int(imp),"link_clicks":int(lc),
        "clicks":int(cl),"page_view":int(pv),"leads":int(ld),
        "ctr":round(lc/imp*100,2) if imp>0 else None,
        "ctr_all":round(cl/imp*100,2) if imp>0 else None,
        "connect_rate":round(pv/lc*100,2) if lc>0 else None,
        "tx_conv":round(ld/pv*100,2) if pv>0 else None,
        "cpl":round(sp/ld,2) if ld>0 else None,
        "cpm":round(sp/imp*1000,2) if imp>0 else None}

def meta_kpis(df):
    return {"lct":calc_kpis(df[df["is_lct"]]),"all":calc_kpis(df)}

def build_daily(p):
    has_clicks="clicks" in p.columns
    agg_cols=dict(spend=("spend","sum"),impressions=("impressions","sum"),
        link_clicks=("link_clicks","sum"),page_view=("page_view","sum"),leads=("leads","sum"),
        engagement=("engagement","sum"),reach=("reach","sum"),
        shares=("shares","sum"),comments=("comments","sum"),
        saves=("saves","sum"),thruplay=("thruplay","sum"),sales=("sales","sum"))
    if has_clicks: agg_cols["clicks"]=("clicks","sum")
    agg=p.groupby("date").agg(**agg_cols).reset_index().sort_values("date")
    out={k:[] for k in ["days","spend","impressions","link_clicks","clicks","page_view","leads",
                         "ctr","ctr_all","connect_rate","tx_conv","cpl","cpm",
                         "reach","engagement","cpe","shares","comments","saves","thruplay",
                         "sales","cps","tx_conv_lp"]}
    for _,r in agg.iterrows():
        sp=float(r["spend"]); imp=float(r["impressions"]); lc=float(r["link_clicks"])
        pv=float(r["page_view"]); ld=float(r["leads"])
        cl=float(r["clicks"]) if has_clicks else lc
        eng=float(r["engagement"]) if "engagement" in r.index else 0
        sl=float(r["sales"]) if "sales" in r.index else 0
        out["days"].append(r["date"].strftime("%d/%m/%Y"))
        out["spend"].append(round(sp,2)); out["impressions"].append(int(imp))
        out["link_clicks"].append(int(lc)); out["clicks"].append(int(cl))
        out["page_view"].append(int(pv)); out["leads"].append(int(ld))
        out["reach"].append(int(r["reach"]) if "reach" in r.index else 0)
        out["engagement"].append(int(eng))
        out["cpe"].append(round(sp/eng,2) if eng>0 else None)
        out["shares"].append(int(r["shares"]) if "shares" in r.index else 0)
        out["comments"].append(int(r["comments"]) if "comments" in r.index else 0)
        out["saves"].append(int(r["saves"]) if "saves" in r.index else 0)
        out["thruplay"].append(int(r["thruplay"]) if "thruplay" in r.index else 0)
        out["sales"].append(int(sl))
        out["cps"].append(round(sp/sl,2) if sl>0 else None)
        out["tx_conv_lp"].append(round(sl/pv*100,2) if pv>0 else None)
        out["ctr"].append(round(lc/imp*100,2) if imp>0 else None)
        out["ctr_all"].append(round(cl/imp*100,2) if imp>0 else None)
        out["connect_rate"].append(round(pv/lc*100,2) if lc>0 else None)
        out["tx_conv"].append(round(ld/pv*100,2) if pv>0 else None)
        out["cpl"].append(round(sp/ld,2) if ld>0 else None)
        out["cpm"].append(round(sp/imp*1000,2) if imp>0 else None)
    return out

def meta_daily(df):
    return {"lct":build_daily(df[df["is_lct"]]),"all":build_daily(df)}

def meta_daily_camps(df):
    result={"lct":{},"all":{}}
    for key,subset in [("lct",df[df["is_lct"]]),("all",df)]:
        for camp in subset["campaign"].unique():
            result[key][camp]=build_daily(subset[subset["campaign"]==camp])
    return result

_STATUS_PRIORITY={"ACTIVE":0,"WITH_ISSUES":1,"PAUSED":2,"ADSET_PAUSED":3,"CAMPAIGN_PAUSED":4,"ARCHIVED":5}

def _pick_status(group):
    if "status" not in group.columns: return ""
    g=group[group["status"].notna()&(group["status"]!="")&(group["status"]!="NAN")]
    if len(g)==0: return ""
    last_date=g["date"].max(); last=g[g["date"]==last_date]
    if (last["status"]=="ACTIVE").any(): return "ACTIVE"
    statuses=last["status"].unique().tolist()
    statuses.sort(key=lambda s:_STATUS_PRIORITY.get(s,99))
    return statuses[0]

def meta_raw(df):
    rows=[]; has_status="status" in df.columns
    camp_st={k:_pick_status(g) for k,g in df.groupby("campaign")} if has_status else {}
    adset_st={(c,a):_pick_status(g) for (c,a),g in df.groupby(["campaign","adset"])} if has_status else {}
    agg=df.groupby(["date","campaign","adset","is_lct"]).agg(
        spend=("spend","sum"),leads=("leads","sum"),
        impressions=("impressions","sum"),link_clicks=("link_clicks","sum"),
        clicks=("clicks","sum"),page_view=("page_view","sum"),sales=("sales","sum")
    ).reset_index()
    for _,r in agg.iterrows():
        rows.append({"d":r["date"].strftime("%d/%m/%Y"),"c":str(r["campaign"]),"a":str(r["adset"]),
            "lct":bool(r["is_lct"]),"sp":round(float(r["spend"]),2),
            "ld":int(r["leads"]),"imp":int(r["impressions"]),
            "lc":int(r["link_clicks"]),"cl":int(r["clicks"]),"pv":int(r["page_view"]),
            "sl":int(r["sales"]),
            "sc":camp_st.get(str(r["campaign"]),""),
            "sa":adset_st.get((str(r["campaign"]),str(r["adset"])),"")})
    return rows

def meta_tables_period(df, p, img_dir):
    def ag(sub,cols):
        agg_d=dict(spend=("spend","sum"),impressions=("impressions","sum"),
            link_clicks=("link_clicks","sum"),clicks=("clicks","sum"),
            page_view=("page_view","sum"),leads=("leads","sum"))
        if "reach" in sub.columns: agg_d["reach"]=("reach","sum")
        if "engagement" in sub.columns: agg_d["engagement"]=("engagement","sum")
        if "sales" in sub.columns: agg_d["sales"]=("sales","sum")
        return sub.groupby(cols).agg(**agg_d).reset_index()
    def calc_row(r):
        sp=round(float(r["spend"]),2); imp=int(r["impressions"]); lc=int(r["link_clicks"])
        cl=int(r["clicks"]) if "clicks" in r.index else lc
        pv=int(r["page_view"]); ld=int(r["leads"])
        eng=int(r["engagement"]) if "engagement" in r.index else 0
        rch=int(r["reach"]) if "reach" in r.index else 0
        sl=int(r["sales"]) if "sales" in r.index else 0
        return {"spend":sp,"imp":imp,"lc":lc,"cl":cl,"pv":pv,"ld":ld,"reach":rch,"engagement":eng,"sl":sl,
            "ctr":round(lc/imp*100,2) if imp>0 else None,
            "ctr_all":round(cl/imp*100,2) if imp>0 else None,
            "cr":round(pv/lc*100,2) if lc>0 else None,
            "tx_cv":round(ld/pv*100,2) if pv>0 else None,
            "cpl":round(sp/ld,2) if ld>0 else None,
            "cpm":round(sp/imp*1000,2) if imp>0 else None,
            "cpe":round(sp/eng,2) if eng>0 else None,
            "cps":round(sp/sl,2) if sl>0 else None,
            "tx_cv_lp":round(sl/pv*100,2) if pv>0 else None}
    camp_st={k:_pick_status(g) for k,g in df.groupby("campaign")}
    adset_st={(c,a):_pick_status(g) for (c,a),g in df.groupby(["campaign","adset"])}
    ad_st={(c,a,n):_pick_status(g) for (c,a,n),g in df.groupby(["campaign","adset","ad"])}
    camps_agg=ag(p,"campaign")
    camps=[{"n":str(r["campaign"]),"status":camp_st.get(str(r["campaign"]),""),**calc_row(r)} for _,r in camps_agg.sort_values("leads",ascending=False).iterrows()]
    adsets_agg=ag(p,["campaign","adset"])
    adsets=[{"n":str(r["adset"]),"camp":str(r["campaign"]),"status":adset_st.get((str(r["campaign"]),str(r["adset"])),""),**calc_row(r)} for _,r in adsets_agg.sort_values("leads",ascending=False).iterrows()]
    df_full_thumb=df[df["thumb"].notna()&(df["thumb"].astype(str)!="nan")] if "thumb" in df.columns else pd.DataFrame()
    thumb_map={}
    for _,r in df_full_thumb.iterrows():
        k=(str(r["ad"]),str(r["adset"]),str(r["campaign"]))
        if k not in thumb_map: thumb_map[k]=download_thumb(str(r["thumb"]),img_dir)
    ads_extra={}
    for _c in ["reach","engagement","shares","comments","saves","thruplay","sales"]:
        if _c in p.columns: ads_extra[_c]=(_c,"sum")
    ads_agg=p.groupby(["ad","adset","campaign"]).agg(spend=("spend","sum"),impressions=("impressions","sum"),link_clicks=("link_clicks","sum"),clicks=("clicks","sum"),leads=("leads","sum"),page_view=("page_view","sum"),**ads_extra).reset_index().sort_values("leads",ascending=False)
    ads=[]
    for _,r in ads_agg.iterrows():
        sp=round(float(r["spend"]),2); imp=int(r["impressions"])
        lc=int(r["link_clicks"]); cl=int(r["clicks"]) if "clicks" in r.index else lc; ld=int(r["leads"])
        pv=int(r["page_view"]) if "page_view" in r.index else 0
        k=(str(r["ad"]),str(r["adset"]),str(r["campaign"]))
        _eng=int(r["engagement"]) if "engagement" in r.index else 0
        _sl=int(r["sales"]) if "sales" in r.index else 0
        ads.append({"n":str(r["ad"]),"adset":str(r["adset"]),"camp":str(r["campaign"]),
            "status":ad_st.get((str(r["campaign"]),str(r["adset"]),str(r["ad"])),""),
            "thumb":thumb_map.get(k,""),"spend":sp,"imp":imp,"lc":lc,"cl":cl,"ld":ld,"pv":pv,
            "reach":int(r["reach"]) if "reach" in r.index else 0,"engagement":_eng,
            "shares":int(r["shares"]) if "shares" in r.index else 0,
            "comments":int(r["comments"]) if "comments" in r.index else 0,
            "saves":int(r["saves"]) if "saves" in r.index else 0,
            "thruplay":int(r["thruplay"]) if "thruplay" in r.index else 0,
            "sl":_sl,
            "ctr":round(lc/imp*100,2) if imp>0 else None,
            "ctr_all":round(cl/imp*100,2) if imp>0 else None,
            "cpl":round(sp/ld,2) if ld>0 else None,
            "cpm":round(sp/imp*1000,2) if imp>0 else None,
            "cpe":round(sp/_eng,2) if _eng>0 else None,
            "cps":round(sp/_sl,2) if _sl>0 else None,
            "tx_cv_lp":round(_sl/pv*100,2) if pv>0 else None})
    return {"camps":camps,"adsets":adsets,"ads":ads}

def meta_tables(df, img_dir):
    hoje=pd.Timestamp(date.today()); ontem=hoje-pd.Timedelta(days=1)
    result={"lct":{},"all":{}}
    period_ranges={"1":(ontem,ontem),"7":(hoje-pd.Timedelta(days=6),hoje),
        "14":(hoje-pd.Timedelta(days=13),hoje),"30":(hoje-pd.Timedelta(days=29),hoje),"all":(None,None)}
    for key,subset in [("lct",df[df["is_lct"]]),("all",df)]:
        for pname,(start,end) in period_ranges.items():
            p=subset if start is None else subset[(subset["date"]>=start)&(subset["date"]<=end)]
            result[key][pname]=meta_tables_period(df,p,img_dir)
            print(f"     [{key}][{pname}]: {len(result[key][pname]['camps'])} camps | {len(result[key][pname]['ads'])} ads")
    return result

def meta_breakdowns(df):
    print("  Lendo breakdowns...")
    hoje_bd=pd.Timestamp(date.today()); AGE_ORDER=["18-24","25-34","35-44","45-54","55-64","65+"]
    CONV_COLS_BD=["Action Leads"]
    def seg(agg,dim):
        agg=agg[agg["spend"]>0].copy()
        agg["cpl"]=(agg["spend"]/agg["leads"]).where(agg["leads"]>0).round(2)
        return [{"n":str(r[dim]),"spend":round(float(r["spend"]),2),"ld":int(r["leads"]),"cpl":safe(r["cpl"])} for _,r in agg.iterrows()]
    try:
        df_ga=pd.read_csv(URL_GA); df_ga["date"]=pd.to_datetime(df_ga["Date"],errors="coerce")
        df_ga["spend"]=to_num(df_ga["Spend (Cost, Amount Spent)"])
        available=[c for c in CONV_COLS_BD if c in df_ga.columns]
        print(f"     GA colunas de conv: {available}")
        df_ga["leads"]=sum(to_num(df_ga[c]) for c in available) if available else pd.Series(0,index=df_ga.index)
        df_ga["age"]=df_ga["Age (Breakdown)"].astype(str)
        df_ga["gender"]=df_ga["Gender (Breakdown)"].astype(str)
        df_ga["is_lct"]=df_ga["Campaign Name"].str.contains(LANCAMENTO_COD,na=False,case=False) if "Campaign Name" in df_ga.columns and LANCAMENTO_COD else True
        df_ga=df_ga.dropna(subset=["date"])
    except Exception as e: print(f"  Aviso GA: {e}"); df_ga=pd.DataFrame()
    try:
        df_pt=pd.read_csv(URL_PT); df_pt["date"]=pd.to_datetime(df_pt["Date"],errors="coerce")
        df_pt["spend"]=to_num(df_pt["Spend (Cost, Amount Spent)"])
        available_pt=[c for c in CONV_COLS_BD if c in df_pt.columns]
        print(f"     PT colunas de conv: {available_pt}")
        df_pt["leads"]=sum(to_num(df_pt[c]) for c in available_pt) if available_pt else pd.Series(0,index=df_pt.index)
        df_pt["platform"]=df_pt["Platform Position (Breakdown)"].astype(str)
        df_pt["is_lct"]=df_pt["Campaign Name"].str.contains(LANCAMENTO_COD,na=False,case=False) if "Campaign Name" in df_pt.columns and LANCAMENTO_COD else True
        df_pt=df_pt.dropna(subset=["date"])
    except Exception as e: print(f"  Aviso PT: {e}"); df_pt=pd.DataFrame()
    result={}
    for pname,n in [("1",1),("7",7),("14",14),("30",30),("all",0)]:
        start=hoje_bd-pd.Timedelta(days=n-1) if n>0 else None
        for lname,lct_filter in [("lct",True),("all",None)]:
            pga=df_ga if lct_filter is None else (df_ga[df_ga["is_lct"]] if len(df_ga)>0 else df_ga)
            ppt=df_pt if lct_filter is None else (df_pt[df_pt["is_lct"]] if len(df_pt)>0 else df_pt)
            if n>0:
                pga=pga[(pga["date"]>=start)&(pga["date"]<=hoje_bd)] if len(pga)>0 else pga
                ppt=ppt[(ppt["date"]>=start)&(ppt["date"]<=hoje_bd)] if len(ppt)>0 else ppt
            age_d=[]; gen_d=[]; plat_d=[]
            if len(pga)>0:
                ag_age=pga[pga["age"].isin(AGE_ORDER)].groupby("age").agg(spend=("spend","sum"),leads=("leads","sum")).reset_index()
                ag_age["_o"]=ag_age["age"].apply(lambda x:AGE_ORDER.index(x) if x in AGE_ORDER else 99)
                age_d=seg(ag_age.sort_values("_o"),"age")
                ag_gen=pga[pga["gender"].isin(["female","male"])].groupby("gender").agg(spend=("spend","sum"),leads=("leads","sum")).reset_index().sort_values("leads",ascending=False)
                gen_d=seg(ag_gen,"gender")
            if len(ppt)>0:
                ag_pt=ppt.groupby("platform").agg(spend=("spend","sum"),leads=("leads","sum")).reset_index().sort_values("leads",ascending=False).head(8)
                plat_d=seg(ag_pt,"platform")
            if lname not in result: result[lname]={}
            result[lname][pname]={"age":age_d,"gender":gen_d,"platform":plat_d}
    raw_ga=[]
    if len(df_ga)>0:
        for _,r in df_ga.iterrows():
            if pd.isna(r['date']): continue
            raw_ga.append({'d':r['date'].strftime('%d/%m/%Y'),'age':str(r['age']),'gen':str(r['gender']),
                           'sp':round(float(r['spend']),2),'ld':int(r['leads']),
                           'lct':bool(r['is_lct']),
                           'camp':str(r['Campaign Name']) if 'Campaign Name' in r.index else ''})
    raw_pt=[]
    if len(df_pt)>0:
        for _,r in df_pt.iterrows():
            if pd.isna(r['date']): continue
            raw_pt.append({'d':r['date'].strftime('%d/%m/%Y'),'plat':str(r['platform']),
                           'sp':round(float(r['spend']),2),'ld':int(r['leads']),
                           'lct':bool(r['is_lct']),
                           'camp':str(r['Campaign Name']) if 'Campaign Name' in r.index else ''})
    result['_raw_ga']=raw_ga
    result['_raw_pt']=raw_pt
    return result

def meta_monthly(df):
    PT_MONTHS={"Jan":"Jan","Feb":"Fev","Mar":"Mar","Apr":"Abr","May":"Mai","Jun":"Jun",
               "Jul":"Jul","Aug":"Ago","Sep":"Set","Oct":"Out","Nov":"Nov","Dec":"Dez"}
    df=df.copy(); df["ym"]=df["date"].dt.to_period("M"); months=sorted(df["ym"].unique())
    out={"lbl":[],"totalS":[],"totalL":[],"cplG":[],"cpmG":[],"ctrG":[],"camps":[]}
    for m in months:
        p=df[df["ym"]==m]; sp=round(float(p["spend"].sum()),2); ld=int(p["leads"].sum())
        imp=float(p["impressions"].sum()); lc=float(p["link_clicks"].sum())
        raw_lbl=pd.Period(m,"M").strftime("%b/%y"); pt_lbl=PT_MONTHS.get(raw_lbl[:3],raw_lbl[:3])+raw_lbl[3:]
        out["lbl"].append(pt_lbl); out["totalS"].append(sp); out["totalL"].append(ld)
        out["cplG"].append(round(sp/ld,2) if ld>0 else None)
        out["cpmG"].append(round(sp/imp*1000,2) if imp>0 else None)
        out["ctrG"].append(round(lc/imp*100,2) if imp>0 else None)
        ag=p.groupby("campaign").agg(spend=("spend","sum"),leads=("leads","sum"),
            impressions=("impressions","sum"),link_clicks=("link_clicks","sum")).reset_index()
        for _,r in ag.iterrows():
            out["camps"].append({"n":str(r["campaign"]),"spend":round(float(r["spend"]),2),
                "leads":int(r["leads"]),"imp":int(r["impressions"]),"lc":int(r["link_clicks"])})
    print(f"     Meta Mensal: {len(months)} meses"); return out

# ══ PESQUISA ══════════════════════════════════════════
def load_pesquisa():
    print("  Lendo pesquisa..."); return pd.read_csv(sheet_url("Pesquisa"))

def pesquisa_process(df, total_leads):
    UTM_COLS=["utm_source","utm_medium","utm_campaign","utm_content"]
    SKIP_COLS=set(UTM_COLS+["Carimbo de data/hora","Timestamp","Email","email",
                             "Qual seu e-mail de cadastro no evento?",
                             "Qual seu primeiro nome?","Qual seu whatsapp?",
                             "Nome","nome","ID","id","Unnamed: 0"])
    PERGUNTAS=[c for c in df.columns
               if c not in SKIP_COLS and not c.lower().startswith("unnamed")
               and str(c).strip() and pd.api.types.is_string_dtype(df[c])
               and df[c].nunique()<=50]
    graficos=[]
    for p in PERGUNTAS:
        if p not in df.columns: continue
        vc=df[p].value_counts(); total=vc.sum()
        graficos.append({"pergunta":p,"opcoes":[{"label":str(k),"qtd":int(v),"pct":round(v/total*100,1)} for k,v in vc.items()]})
    filtros={}
    for col in UTM_COLS:
        if col in df.columns:
            filtros[col]=sorted([v for v in df[col].dropna().unique().tolist() if v and str(v)!="nan"])
    rows=[]
    for _,r in df.iterrows():
        row={}
        for p in PERGUNTAS: row[p]=str(r[p]) if p in df.columns and pd.notna(r.get(p)) else None
        for col in UTM_COLS: row[col]=str(r[col]) if col in df.columns and pd.notna(r.get(col)) else None
        rows.append(row)
    return {"total":len(df),"total_leads":int(total_leads),"graficos":graficos,"filtros":filtros,"rows":rows,"perguntas":PERGUNTAS}

# ══ MAIN ═══════════════════════════════════════════════
def main():
    print("="*60)
    print(f"Gerando data.json — {NOME_CLIENTE} / {LANCAMENTO_COD or 'Todos'}")
    print("="*60)
    img_dir=Path("imgs"); img_dir.mkdir(exist_ok=True)

    print("\n[META ADS]")
    df_meta=load_meta()
    m_k=meta_kpis(df_meta); m_d=meta_daily(df_meta)
    m_dc=meta_daily_camps(df_meta); m_raw=meta_raw(df_meta)
    m_t=meta_tables(df_meta,img_dir); m_bd=meta_breakdowns(df_meta)
    m_month=meta_monthly(df_meta)
    total_leads=m_k["lct"]["leads"] if LANCAMENTO_COD else m_k["all"]["leads"]
    print(f"  ✓ {total_leads} leads | {MOEDA_SIMBOLO} {m_k['lct']['spend']:,.2f} invest.")

    print("\n[GOOGLE ADS]")
    print("  (desativado)")
    g_daily={"days":[],"spend":[],"conversions":[],"cpa":[],"ctr":[],"cpc":[]}
    g_kpis={}; g_camps={}; g_kw={}; g_bd={}
    g_month={"lbl":[],"totalS":[],"totalConv":[],"cpaG":[],"cpcG":[],"ctrG":[],"camps":[]}
    g_raw=[]

    print("\n[PESQUISA]")
    if USAR_PESQUISA:
        df_pes=load_pesquisa()
        pes=pesquisa_process(df_pes, total_leads)
        print(f"  ✓ {pes['total']} respostas")
    else:
        pes=False
        print("  (desativada)")

    # ══ MONTAR data.json ══════════════════════════════
    data = {
        "META_KPIS":         m_k,
        "META_DAILY":        m_d,
        "META_DAILY_CAMPS":  m_dc,
        "META_RAW_CAMP":     m_raw,
        "META_TABLES":       m_t,
        "META_BD":           m_bd,
        "META_MONTHLY":      m_month,
        "PESQUISA":          pes,
        "GOOGLE_DAILY":      g_daily,
        "GOOGLE_KPIS":       g_kpis,
        "GOOGLE_CAMPS":      g_camps,
        "GOOGLE_KW":         g_kw,
        "GOOGLE_BD":         g_bd,
        "GOOGLE_MONTHLY":    g_month,
        "GOOGLE_RAW":        g_raw,
        "NOME_CLIENTE":      NOME_CLIENTE,
        "LOGO_LETRA":        LOGO_LETRA,
        "COR_ACENTO":        COR_ACENTO,
        "LANCAMENTO_COD":    LANCAMENTO_COD,
        "USAR_GOOGLE":       USAR_GOOGLE,
        "FUNIL_IMPRESSOES":  FUNIL_IMPRESSOES,
        "FUNIL_LINK_CLICKS": FUNIL_LINK_CLICKS,
        "FUNIL_PAGE_VIEW":   FUNIL_PAGE_VIEW,
        "FUNIL_LEADS":       FUNIL_LEADS,
        "MOEDA_SIMBOLO":     MOEDA_SIMBOLO,
        "MOEDA_COD":         MOEDA,
        "CPL_BOM":           CPL_BOM,
        "CPL_MEDIO":         CPL_MEDIO,
        "CTR_BOM":           CTR_BOM,
        "CTR_MEDIO":         CTR_MEDIO,
        "CR_BOM":            CR_BOM,
        "CR_MEDIO":          CR_MEDIO,
        "TX_CONV_BOM":       TX_CONV_BOM,
        "TX_CONV_MEDIO":     TX_CONV_MEDIO,
        "CPM_BOM":           CPM_BOM,
        "CPM_MEDIO":         CPM_MEDIO,
        "DATA_GERACAO":      date.today().strftime("%Y-%m-%d"),
    }

    Path(OUTPUT_JSON).write_text(
        json.dumps(data, ensure_ascii=False, separators=(',', ':')),
        encoding="utf-8"
    )
    size=Path(OUTPUT_JSON).stat().st_size//1024
    print(f"\n✓ {OUTPUT_JSON} ({size}KB)")
    print("="*60)

if __name__=="__main__":
    main()
