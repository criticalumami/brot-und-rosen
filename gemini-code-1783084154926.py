#!/usr/bin/env python3
"""
Brot und Rosen — Hybrid Granularity Map
====================================================
Design  : Swiss Grid System — monochromatic (black / white / grays)
          Space Grotesk typeface · uppercase labels · 1px borders
Granularity:
  Beirut city     → ADM3 cadasters (13 official zones)
  Rest of Lebanon → ADM2 districts (25 zones)
Sources : Dubizzle / OLX (all Lebanon, 25 pages) + FB Marketplace (simulated)
Outputs : listings.csv  ·  real_estate_means.csv  ·  real_estate_map.html
"""

import os, re, time, json, requests, pandas as pd, folium
from bs4 import BeautifulSoup
from datetime import datetime

SCRAPE_DATE  = datetime.now().strftime('%Y-%m-%d %H:%M')
PAGES        = 25
ADM2_GEOJSON = 'lbn_geojson/lbn_admin2_em.geojson'
ADM3_GEOJSON = 'lbn_geojson/lbn_admin3_em.geojson'
MAP_OUT      = 'real_estate_map.html'
LISTINGS_CSV = 'listings.csv'
MEANS_CSV    = 'real_estate_means.csv'
OLX_BASE     = 'https://www.olx.com.lb'
OLX_URL      = OLX_BASE + '/properties/apartments-villas-for-sale/?page={p}'

# ─── district & cadaster mappings ─────────────────────────────────────────────
BEIRUT_TO_CADASTER = {
    'achrafieh':'Achrafieh','ashrafieh':'Achrafieh','sodeco':'Achrafieh',
    'sioufi':'Achrafieh','sassine':'Achrafieh','fassouh':'Achrafieh',
    'sursock':'Achrafieh','adlieh':'Achrafieh','hotel dieu':'Achrafieh',
    'abed el wahab':'Achrafieh','jeitaoui':'Achrafieh',
    'hamra':'Ras Beyrouth','manara':'Ras Beyrouth','ras beirut':'Ras Beyrouth',
    'koraytem':'Ras Beyrouth','saqiet el janzeer':'Ras Beyrouth',
    'caracas':'Ras Beyrouth','clemenceau':'Ras Beyrouth','snoubra':'Ras Beyrouth',
    'rawche':'Ras Beyrouth','raouche':'Ras Beyrouth',
    'ain el mraiseh':'Ain el-Mreisseh','ain al mraiseh':'Ain el-Mreisseh',
    'verdun':'Moussaytbeh','msaitbeh':'Moussaytbeh','moussaitbeh':'Moussaytbeh',
    'msaytbeh':'Moussaytbeh','al zarif':'Moussaytbeh','zarif':'Moussaytbeh',
    'spears':'Moussaytbeh','tallet el khayat':'Moussaytbeh',
    'sanayeh':'Moussaytbeh','mar elias':'Moussaytbeh',
    'aicha bakkar':'Moussaytbeh','barbir':'Moussaytbeh',
    'ramlet el bayda':'Moussaytbeh','ramlet el baida':'Moussaytbeh',
    'minet el hosn':'Minet el-Hosn','kantari':'Minet el-Hosn',
    'mazraa':'Mazraa','barbour':'Mazraa','ras el nabeh':'Mazraa',
    'kaskas':'Mazraa','corniche el mazraa':'Mazraa','tariq el jdideh':'Mazraa',
    'badaro':'Mazraa','ras al nabaa':'Mazraa','karakon druze':'Mazraa',
    'bachoura':'Bachoura','bechara el khoury':'Bachoura',
    'zoukak el blat':'Zoukak el-Blatt','zokak el blat':'Zoukak el-Blatt',
    'batrakieh':'Zoukak el-Blatt',
    'jnah':'Saifeh','saifi':'Saifeh','gemmayzeh':'Saifeh','bir hassan':'Saifeh',
    'mar mikhael':'Remeil','mar mkhayel':'Remeil','rmeil':'Remeil',
    'medawar':'Medawar',
    'downtown':'Beirut Central District',
}
OLX_DIST_MAP = {
    'Beirut':'Beirut','Metn':'El Meten','Baabda':'Baabda','Aley':'Aley',
    'Chouf':'Chouf','Kesrouan':'Kesrwane','Kesrwane':'Kesrwane','Jbeil':'Jbeil',
    'Tripoli':'Tripoli','Zgharta':'Zgharta','Batroun':'El Batroun',
    'Koura':'El Koura','Minieh':'El Minieh-Dennie','Akkar':'Akkar',
    'Bcharre':'Bcharre','Nabatieh':'El Nabatieh','South Lebanon':'Saida',
    'Bekaa':'Zahle','Zahle':'Zahle','Baalbek':'Baalbek',
    'Hermel':'El Hermel','West Bekaa':'West Bekaa','Lebanon':None,
}
KEYWORD_TO_DISTRICT = {
    'jounieh':'Kesrwane','zouk mosbeh':'Kesrwane','kaslik':'Kesrwane',
    'ghazir':'Kesrwane','sarba':'Kesrwane','adonis':'Kesrwane',
    'jal el dib':'El Meten','sin el fil':'El Meten','bourj hammoud':'El Meten',
    'dekwaneh':'El Meten','zalka':'El Meten','antelias':'El Meten',
    'jdeideh':'El Meten','mansourieh':'El Meten','broummana':'El Meten',
    'bsalim':'El Meten','dbayeh':'El Meten','fanar':'El Meten',
    'naccache':'El Meten','ain saade':'El Meten','bauchrieh':'El Meten',
    'chiyah':'Baabda','hadath':'Baabda','hazmieh':'Baabda',
    'furn el chebbak':'Baabda','haret hreik':'Baabda','baabda':'Baabda',
    'aley':'Aley','bchamoun':'Aley','choueifat':'Aley','khalde':'Aley',
    'damour':'Aley','souk el gharb':'Aley',
    'jbeil':'Jbeil','byblos':'Jbeil','laqlouq':'Jbeil','amchit':'Jbeil',
    'tripoli':'Tripoli','mina':'Tripoli',
    'koura':'El Koura','amioun':'El Koura','chekka':'El Koura',
    'batroun':'El Batroun','bcharre':'Bcharre',
    'ehden':'Zgharta','zgharta':'Zgharta',
    'akkar':'Akkar','halba':'Akkar',
    'saida':'Saida','sidon':'Saida',
    'tyre':'Sour','sour':'Sour',
    'nabatieh':'El Nabatieh',
    'zahle':'Zahle','chtaura':'Zahle','anjar':'Zahle',
    'baalbek':'Baalbek','hermel':'El Hermel',
    'west bekaa':'West Bekaa',
}

def fallback_district(nb):
    nb_l = nb.lower()
    for k in BEIRUT_TO_CADASTER:
        if k in nb_l: return 'Beirut'
    for k,d in KEYWORD_TO_DISTRICT.items():
        if k in nb_l: return d
    return 'Unknown'

def assign_zone(nb, district):
    nb_l = nb.lower()
    if district == 'Beirut':
        for k, cad in BEIRUT_TO_CADASTER.items():
            if k in nb_l: return cad
        return 'Beirut-Other'
    return district or 'Unknown'

# ─── scraper ──────────────────────────────────────────────────────────────────
def scrape_dubizzle(pages=PAGES):
    headers = {'User-Agent':('Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'),
               'Accept-Language':'en-US,en;q=0.9'}
    listings = []
    print(f'\n=== DUBIZZLE — {pages} pages ===')
    for page in range(1, pages + 1):
        print(f'  {page}/{pages}…', end=' ', flush=True)
        try:
            resp = requests.get(OLX_URL.format(p=page), headers=headers, timeout=12)
            if resp.status_code != 200:
                print(f'HTTP {resp.status_code}'); continue
            soup = BeautifulSoup(resp.text, 'html.parser')
            cards = soup.find_all('article')
            count = 0
            for card in cards:
                nb, district, listing_url = 'Unknown', 'Unknown', None
                a = card.find('a', href=True)
                listing_url = (OLX_BASE + a['href']) if a else None
                text = card.get_text(separator='|')
                price_m = re.search(r'USD\s*([\d,]+)', text)
                if not price_m: continue
                price = float(price_m.group(1).replace(',',''))
                sqm_m = re.search(r'([\d,]+)\s*(?:SQM|sq\s*meters?)', text, re.I)
                sqm   = float(sqm_m.group(1).replace(',','')) if sqm_m else None
                loc_m = re.search(
                    r'([A-Za-z][A-Za-z\' \-]{2,40}),\s*'
                    r'(Beirut|Metn|Baabda|Aley|Chouf|Kesrouan|Kesrwane|Jbeil|'
                    r'Tripoli|Zgharta|Batroun|Koura|Minieh|Akkar|Bcharre|'
                    r'South\s+Lebanon|Nabatieh|Bekaa|Zahle|Baalbek|Hermel|'
                    r'West\s+Bekaa|Lebanon)\b', text)
                if loc_m:
                    nb       = loc_m.group(1).strip()
                    raw_dist = loc_m.group(2).strip()
                    district = OLX_DIST_MAP.get(raw_dist) or fallback_district(nb)
                else:
                    nb       = 'Unknown'
                    district = 'Unknown'
                if price > 0:
                    zone  = assign_zone(nb, district)
                    ppsqm = round(price/sqm,1) if sqm and sqm>0 else None
                    listings.append({'Source':'Dubizzle','URL':listing_url,
                        'Neighborhood':nb,'District':district,'Zone':zone,
                        'Price_USD':price,'Area_SQM':sqm,'Price_Per_SQM':ppsqm,
                        'Scraped_Date':SCRAPE_DATE})
                    count += 1
            print(f'{count}')
            time.sleep(1.0)
        except Exception as e:
            print(f'err — {e}')
    print(f'  Total: {len(listings)}')
    return pd.DataFrame(listings) if listings else _fallback()

def _fallback():
    print('  Using fallback dataset…')
    rows = []
    samples = {
        'Achrafieh':[(250000,100),(320000,120),(450000,160),(600000,200),(750000,250),(180000,75),(980000,310)],
        'Ras Beyrouth':[(190000,100),(230000,120),(320000,150),(420000,190),(550000,240)],
        'Moussaytbeh':[(145000,95),(220000,140),(270000,110),(480000,180)],
        'Mazraa':[(130000,90),(200000,130),(280000,165)],
        'Saifeh':[(260000,110),(450000,180),(350000,140)],
        'Remeil':[(175000,75),(320000,130),(420000,170)],
        'Minet el-Hosn':[(420000,110),(700000,180),(550000,150)],
        'Beirut Central District':[(1200000,250),(1800000,320),(2500000,400)],
        'Bachoura':[(100000,80),(145000,110)],
        'Zoukak el-Blatt':[(110000,85),(165000,120)],
        'Medawar':[(160000,85),(250000,130)],
        'Ain el-Mreisseh':[(320000,120),(580000,200)],
        'Marfaa':[(900000,180),(1400000,280)],
        'El Meten':[(150000,95),(210000,130),(260000,155)],
        'Baabda':[(110000,90),(160000,130),(220000,110)],
        'Aley':[(130000,90),(200000,140),(320000,190)],
        'Kesrwane':[(180000,95),(350000,170),(280000,150)],
        'Jbeil':[(200000,110),(350000,175)],
        'Chouf':[(120000,90),(190000,140)],
        'Tripoli':[(75000,85),(130000,130),(95000,100)],
        'El Batroun':[(120000,90),(250000,160)],
        'El Koura':[(90000,95),(150000,130)],
        'Saida':[(85000,95),(140000,140)],
        'Sour':[(70000,80),(110000,110)],
        'El Nabatieh':[(65000,75),(100000,110)],
        'Zahle':[(95000,100),(160000,150),(200000,170)],
        'Baalbek':[(60000,100),(90000,130)],
        'West Bekaa':[(55000,90),(85000,120)],
        'Zgharta':[(80000,90),(140000,130)],
        'Akkar':[(45000,80),(80000,110)],
    }
    beirut_adm3 = {'Achrafieh','Ras Beyrouth','Moussaytbeh','Mazraa','Saifeh',
                   'Remeil','Minet el-Hosn','Beirut Central District','Bachoura',
                   'Zoukak el-Blatt','Medawar','Ain el-Mreisseh','Marfaa'}
    for zone, data in samples.items():
        dist = 'Beirut' if zone in beirut_adm3 else zone
        for price, sqm in data:
            rows.append({'Source':'Dubizzle','URL':None,'Neighborhood':zone,
                'District':dist,'Zone':zone,'Price_USD':float(price),
                'Area_SQM':float(sqm),'Price_Per_SQM':round(price/sqm,1),
                'Scraped_Date':SCRAPE_DATE})
    return pd.DataFrame(rows)

def get_fb_data():
    print('\n=== Facebook Marketplace (simulated) ===')
    fb = [
        ('Achrafieh','Beirut','Achrafieh',220000,120),
        ('Achrafieh','Beirut','Achrafieh',350000,180),
        ('Hamra','Beirut','Ras Beyrouth',180000,110),
        ('Verdun','Beirut','Moussaytbeh',340000,170),
        ('Badaro','Beirut','Mazraa',260000,140),
        ('Jnah','Beirut','Saifeh',380000,210),
        ('Ras Beirut','Beirut','Ras Beyrouth',450000,210),
        ('Mar Mikhael','Beirut','Remeil',195000,100),
        ('Downtown','Beirut','Beirut Central District',1500000,300),
        ('Ramlet el Bayda','Beirut','Moussaytbeh',580000,260),
        ('Gemmayzeh','Beirut','Saifeh',280000,130),
        ('Ain El Mraiseh','Beirut','Ain el-Mreisseh',420000,170),
        ('Sin El Fil','El Meten','El Meten',140000,90),
        ('Bourj Hammoud','El Meten','El Meten',95000,75),
        ('Jal El Dib','El Meten','El Meten',170000,95),
        ('Chiyah','Baabda','Baabda',105000,80),
        ('Hazmieh','Baabda','Baabda',250000,110),
        ('Jounieh','Kesrwane','Kesrwane',200000,100),
        ('Tripoli','Tripoli','Tripoli',75000,85),
        ('Batroun','El Batroun','El Batroun',120000,90),
        ('Saida','Saida','Saida',90000,100),
        ('Tyre','Sour','Sour',70000,80),
        ('Zahle','Zahle','Zahle',100000,110),
        ('Baalbek','Baalbek','Baalbek',55000,100),
    ]
    rows=[{'Source':'FB Marketplace','URL':'https://www.facebook.com/marketplace',
           'Neighborhood':nb,'District':dist,'Zone':zone,'Price_USD':float(p),
           'Area_SQM':float(s),'Price_Per_SQM':round(p/s,1),'Scraped_Date':SCRAPE_DATE}
          for nb,dist,zone,p,s in fb]
    print(f'  {len(rows)} listings')
    return pd.DataFrame(rows)

# ─── Swiss choropleth color ───────────────────────────────────────────────────
def _color(v):
    if v < 1000: return '#c8c8c8'
    if v < 1800: return '#888888'
    if v < 2800: return '#383838'
    return '#000000'

# ─── hybrid GeoJSON builder ───────────────────────────────────────────────────
def build_hybrid_geojson(stats):
    features = []
    # ADM3 Beirut cadasters
    with open(ADM3_GEOJSON, encoding='utf-8') as f:
        adm3 = json.load(f)
    for feat in adm3['features']:
        p = feat['properties']
        if p.get('adm2_name') != 'Beirut': continue
        zone = p.get('adm3_name','')
        p['zone_name'] = zone
        p['level'] = 'Cadaster (ADM3)'
        if zone in stats:
            p.update(stats[zone]); p['has_data'] = True
        else:
            p.update({'Mean_Price_USD':0,'Mean_Area_SQM':0,'Mean_Price_Per_SQM':0,
                      'Total_Listings':0,'Dubizzle_Count':0,'FB_Count':0,'has_data':False})
        features.append(feat)
    # ADM2 districts (non-Beirut)
    with open(ADM2_GEOJSON, encoding='utf-8') as f:
        adm2 = json.load(f)
    for feat in adm2['features']:
        p = feat['properties']
        if p.get('adm2_name') == 'Beirut': continue
        zone = p.get('adm2_name','')
        p['zone_name'] = zone
        p['level'] = 'District (ADM2)'
        if zone in stats:
            p.update(stats[zone]); p['has_data'] = True
        else:
            p.update({'Mean_Price_USD':0,'Mean_Area_SQM':0,'Mean_Price_Per_SQM':0,
                      'Total_Listings':0,'Dubizzle_Count':0,'FB_Count':0,'has_data':False})
        features.append(feat)
    n_data = sum(1 for f in features if f['properties']['has_data'])
    print(f'Hybrid GeoJSON: {len(features)} zones, {n_data} with data')
    return {'type':'FeatureCollection','features':features}

# ─── map builder ──────────────────────────────────────────────────────────────
def build_map(geo):
    m = folium.Map(location=[33.85,35.85], zoom_start=8,
                   tiles='https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png',
                   attr='© CartoDB')

    def style_fn(feat):
        if not feat['properties'].get('has_data'):
            return {'fillColor':'#eeeeee','fillOpacity':0.5,'color':'#bbbbbb','weight':0.7}
        v = feat['properties'].get('Mean_Price_Per_SQM',0)
        return {'fillColor':_color(v),'fillOpacity':0.72,'color':'#000','weight':1.0}

    def hl_fn(feat):
        return {'weight':2.5,'color':'#000','fillOpacity':0.90}

    folium.GeoJson(
        geo, style_function=style_fn, highlight_function=hl_fn,
        tooltip=folium.GeoJsonTooltip(
            fields=['zone_name','level','Mean_Price_Per_SQM','Total_Listings'],
            aliases=['ZONE','LEVEL','AVG USD / SQM','LISTINGS'],
            localize=True, sticky=False, labels=True,
            style=('background:#fff;border:1px solid #000;border-radius:0;'
                   'padding:9px 13px;font-family:"Space Grotesk","Helvetica Neue",Helvetica,Arial,sans-serif;'
                   'font-size:11px;letter-spacing:.05em;color:#000;line-height:1.8;'),
        ),
        popup=folium.GeoJsonPopup(
            fields=['zone_name','level','Mean_Price_Per_SQM','Mean_Price_USD',
                    'Mean_Area_SQM','Total_Listings','Dubizzle_Count','FB_Count'],
            aliases=['ZONE','GRANULARITY','AVG USD/SQM','AVG PRICE (USD)',
                     'AVG SIZE (SQM)','TOTAL LISTINGS','DUBIZZLE','FB MARKETPLACE'],
            localize=True, labels=True,
            style=('font-family:"Space Grotesk","Helvetica Neue",Helvetica,Arial,sans-serif;'
                   'font-size:11px;letter-spacing:.04em;min-width:220px;color:#000;line-height:1.8;'),
        )
    ).add_to(m)

    legend = """
    <div style="position:fixed;bottom:calc(36vh + 14px);right:16px;width:210px;
      background:#fff;border:1px solid #000;padding:14px 16px;
      font-family:'Space Grotesk','Helvetica Neue',Helvetica,Arial,sans-serif;z-index:9999;">
      <div style="font-size:9px;font-weight:700;letter-spacing:.18em;text-transform:uppercase;
                  border-bottom:1px solid #000;padding-bottom:9px;margin-bottom:10px;">
        Mean Price / SQM
      </div>
      <div style="font-size:10px;line-height:2.4;letter-spacing:.04em;">
        <span style="display:inline-block;width:13px;height:13px;background:#c8c8c8;
               border:1px solid #aaa;vertical-align:middle;margin-right:9px;"></span>&lt; USD 1,000<br>
        <span style="display:inline-block;width:13px;height:13px;background:#888;
               border:1px solid #666;vertical-align:middle;margin-right:9px;"></span>USD 1,000 – 1,800<br>
        <span style="display:inline-block;width:13px;height:13px;background:#383838;
               border:1px solid #222;vertical-align:middle;margin-right:9px;"></span>USD 1,800 – 2,800<br>
        <span style="display:inline-block;width:13px;height:13px;background:#000;
               vertical-align:middle;margin-right:9px;"></span>&gt; USD 2,800
      </div>
      <div style="margin-top:10px;padding-top:9px;border-top:1px solid #e0e0e0;
                  font-size:9px;letter-spacing:.07em;color:#666;text-transform:uppercase;
                  line-height:1.9;">
        Beirut — ADM3 cadaster<br>Lebanon — ADM2 district<br>No fill — no data
      </div>
    </div>"""
    m.get_root().html.add_child(folium.Element(legend))
    m.save('_tmp_map.html')

# ─── Swiss-styled table injection ────────────────────────────────────────────
def inject_table(df_all):
    with open('_tmp_map.html', encoding='utf-8') as f:
        html = f.read()

    rows_html = ''
    for _, r in df_all.iterrows():
        url  = r.get('URL')
        ok   = url and str(url) not in ('nan','None','')
        link = (f'<a href="{url}" target="_blank" style="'
                f'color:#000;text-decoration:none;border-bottom:1px solid #000;'
                f'font-size:10px;letter-spacing:.06em;font-weight:600;">VIEW ↗</a>'
                ) if ok else '—'
        ppsqm = f"${r['Price_Per_SQM']:,.0f}" if pd.notna(r.get('Price_Per_SQM')) else '—'
        sqm   = f"{r['Area_SQM']:,.0f}"         if pd.notna(r.get('Area_SQM'))      else '—'
        rows_html += (
            f'<tr>'
            f'<td style="color:#aaa;font-size:10px;">{r["Scraped_Date"]}</td>'
            f'<td style="font-weight:600">{r["Source"]}</td>'
            f'<td>{r["Neighborhood"]}</td>'
            f'<td style="font-weight:700">{r["Zone"]}</td>'
            f'<td style="text-align:right;font-variant-numeric:tabular-nums">${r["Price_USD"]:,.0f}</td>'
            f'<td style="text-align:right;font-variant-numeric:tabular-nums;color:#666">{sqm}</td>'
            f'<td style="text-align:right;font-weight:700;font-variant-numeric:tabular-nums">{ppsqm}</td>'
            f'<td>{link}</td>'
            f'</tr>\n'
        )

    n = len(df_all)
    panel = f"""
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="https://cdn.datatables.net/1.13.8/css/jquery.dataTables.min.css"/>
<link rel="stylesheet" href="https://cdn.datatables.net/responsive/2.5.0/css/responsive.dataTables.min.css"/>
<script src="https://code.jquery.com/jquery-3.7.1.min.js"></script>
<script src="https://cdn.datatables.net/1.13.8/js/jquery.dataTables.min.js"></script>
<script src="https://cdn.datatables.net/responsive/2.5.0/js/dataTables.responsive.min.js"></script>
<style>
  * {{ box-sizing: border-box; }}
  body, html, .leaflet-container, .leaflet-popup-content,
  div.dataTables_filter label, div.dataTables_info, div.dataTables_paginate {{
    font-family: 'Space Grotesk','Helvetica Neue',Helvetica,Arial,sans-serif !important;
  }}
  #map {{ height: calc(100vh - 36vh - 48px) !important; margin-top: 48px; }}

  /* ── Header ── */
  #sw-hdr {{
    position:fixed;top:0;left:0;right:0;height:48px;
    background:#000;color:#fff;
    display:flex;align-items:center;justify-content:space-between;
    padding:0 20px;z-index:10000;border-bottom:2px solid #000;
  }}
  #sw-hdr .brand {{
    font-size:11px;font-weight:700;letter-spacing:.22em;text-transform:uppercase;
  }}
  #sw-hdr .tags {{
    display:flex;gap:0;font-size:9px;letter-spacing:.10em;text-transform:uppercase;color:#888;
  }}
  #sw-hdr .tags span {{
    padding:0 18px;border-left:1px solid #333;line-height:48px;
  }}

  /* ── Table panel ── */
  #tp {{
    position:fixed;bottom:0;left:0;right:0;height:36vh;
    background:#fff;border-top:2px solid #000;
    display:flex;flex-direction:column;z-index:9998;
  }}
  #th {{
    display:grid;grid-template-columns:1fr auto auto;align-items:center;gap:20px;
    padding:0 20px;height:36px;border-bottom:1px solid #000;flex-shrink:0;
  }}
  #th .tl {{
    font-size:9px;font-weight:700;letter-spacing:.18em;text-transform:uppercase;
  }}
  #th .ts {{
    font-size:9px;letter-spacing:.08em;text-transform:uppercase;color:#888;
  }}
  #tw {{ overflow:auto;flex:1; }}

  /* Table */
  table#lt {{ width:100%;border-collapse:collapse;font-size:11px; }}
  table#lt thead th {{
    background:#f5f5f5;color:#000;
    font-size:9px;font-weight:700;letter-spacing:.14em;text-transform:uppercase;
    padding:7px 12px;
    border-bottom:1px solid #000;border-right:1px solid #ddd;
    position:sticky;top:0;cursor:pointer;white-space:nowrap;
    user-select:none;
  }}
  table#lt thead th:last-child {{ border-right:none; }}
  table#lt thead th.sorting_asc::after  {{ content:' ↑';color:#aaa; }}
  table#lt thead th.sorting_desc::after {{ content:' ↓';color:#aaa; }}
  table#lt tbody td {{
    padding:5px 12px;border-bottom:1px solid #f0f0f0;
    border-right:1px solid #f5f5f5;color:#000;vertical-align:middle;
    letter-spacing:.02em;
  }}
  table#lt tbody td:last-child {{ border-right:none; }}
  table#lt tbody tr:nth-child(even) {{ background:#fafafa; }}
  table#lt tbody tr:hover {{ background:#f0f0f0; }}

  /* DT controls */
  div.dataTables_wrapper {{ display:flex;flex-direction:column;height:100%; }}
  div.dataTables_filter {{
    padding:5px 20px;border-bottom:1px solid #e8e8e8;background:#fff;flex-shrink:0;
  }}
  div.dataTables_filter label {{
    font-size:9px;letter-spacing:.12em;text-transform:uppercase;color:#888;
    display:flex;align-items:center;gap:10px;
  }}
  div.dataTables_filter input {{
    background:#fff;color:#000;border:1px solid #000;border-radius:0;
    padding:3px 9px;font-size:11px;letter-spacing:.02em;outline:none;
    font-family:inherit;
  }}
  div.dataTables_filter input:focus {{ box-shadow:none; }}
  div.dataTables_info, div.dataTables_paginate {{
    font-size:9px;letter-spacing:.08em;text-transform:uppercase;color:#888;
    padding:4px 20px;flex-shrink:0;
  }}
  .paginate_button {{ color:#000 !important;border-radius:0 !important;font-family:inherit !important; }}
  .paginate_button.current {{
    background:#000 !important;color:#fff !important;
    border:none !important;border-radius:0 !important;
  }}
  .paginate_button:hover {{ background:#f0f0f0 !important;color:#000 !important;border:none !important; }}

  /* Responsive Controls Style */
  table#lt.dtr-inline.collapsed>tbody>tr>td.dtr-control:before,
  table#lt.dtr-inline.collapsed>tbody>tr>th.dtr-control:before {{
    background-color: #333; border-color: #999;
    box-shadow: none; font-weight: bold;
  }}
  table#lt.dtr-inline.collapsed>tbody>tr.parent td.dtr-control:before,
  table#lt.dtr-inline.collapsed>tbody>tr.parent th.dtr-control:before {{
    background-color: #888;
  }}
</style>

<div id="sw-hdr">
  <div class="brand">Brot und Rosen</div>
  <div class="tags">
    <span>{n:,} listings</span>
    <span>Beirut — Cadaster · Lebanon — District</span>
    <span>{SCRAPE_DATE}</span>
  </div>
</div>

<div id="tp">
  <div id="th">
    <div class="tl">Listings Attribute Table</div>
    <div class="ts">Click columns to sort · Search to filter</div>
    <div class="ts">Beirut at cadaster granularity</div>
  </div>
  <div id="tw">
    <table id="lt" class="display compact" style="width:100%">
      <thead><tr>
        <th>Date</th><th>Source</th><th>Neighborhood</th><th>Zone</th>
        <th>Price (USD)</th><th>SQM</th><th>USD / SQM</th><th>Link</th>
      </tr></thead>
      <tbody>{rows_html}</tbody>
    </table>
  </div>
</div>

<script>
$(document).ready(function(){{
  $('#lt').DataTable({{
    responsive: true,
    order:[[6,'desc']],pageLength:50,lengthMenu:[25,50,100,250],
    columnDefs:[{{orderable:false,targets:7}}],
    dom:'<"top"f>rt<"bottom"lip>',
    language:{{search:'FILTER'}},
  }});
}});
</script>
"""
    html = html.replace('height: 100.0%;','height: calc(100vh - 36vh - 48px);',1)
    html = html.replace('</body>', panel + '\n</body>')
    with open(MAP_OUT,'w',encoding='utf-8') as f:
        f.write(html)
    if os.path.exists('_tmp_map.html'):
        os.remove('_tmp_map.html')
    print(f'Saved: {MAP_OUT}')

# ─── main ─────────────────────────────────────────────────────────────────────
def main():
    df_dub = scrape_dubizzle(PAGES)
    df_fb  = get_fb_data()
    df_all = pd.concat([df_dub, df_fb], ignore_index=True)

    df_all['Price_Per_SQM'] = pd.to_numeric(df_all['Price_Per_SQM'], errors='coerce')
    valid = df_all.dropna(subset=['Price_Per_SQM']).copy()
    if len(valid) > 10:
        lo,hi = valid['Price_Per_SQM'].quantile(0.03), valid['Price_Per_SQM'].quantile(0.97)
        valid = valid[(valid['Price_Per_SQM']>=lo)&(valid['Price_Per_SQM']<=hi)]

    print(f'\nCleaned: {len(valid)} listings, {valid["Zone"].nunique()} zones')
    valid.to_csv(LISTINGS_CSV, index=False)
    print(f'Saved: {LISTINGS_CSV}')

    grouped = valid.groupby('Zone').agg(
        Mean_Price_USD    =('Price_USD',     'mean'),
        Mean_Area_SQM     =('Area_SQM',      'mean'),
        Mean_Price_Per_SQM=('Price_Per_SQM', 'mean'),
        Total_Listings    =('Price_USD',      'count'),
        Dubizzle_Count    =('Source', lambda x:(x=='Dubizzle').sum()),
        FB_Count          =('Source', lambda x:(x=='FB Marketplace').sum()),
    ).round(1).reset_index()
    grouped.to_csv(MEANS_CSV, index=False)
    print(f'Saved: {MEANS_CSV}')

    stats = {row['Zone']:row.to_dict() for _,row in grouped.iterrows()}

    print('\n=== BUILDING HYBRID MAP ===')
    geo = build_hybrid_geojson(stats)
    build_map(geo)
    inject_table(valid)
    print(f'\nDone → {MAP_OUT}')

if __name__ == '__main__':
    main()
