import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import time
import random

# スマホ向け設定
st.set_page_config(page_title="株リサーチ", page_icon="📱", layout="centered")

# --- スクレイピング関数 ---
@st.cache_data(ttl=3600) # 1時間キャッシュ（サーバー負荷軽減）
def get_stock_data(code):
    url = f"https://kabutan.jp/stock/?code={code}"
    # スマホのブラウザに見せかける
    headers = {
        "User-Agent": "Mozilla/5.0 (Linux; Android 10; Mobile) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Mobile Safari/537.36"
    }
    
    try:
        time.sleep(1) # マナー待機
        response = requests.get(url, headers=headers)
        response.encoding = response.apparent_encoding
        
        if response.status_code != 200: return None
        soup = BeautifulSoup(response.text, 'html.parser')

        # データ取得
        name_tag = soup.find('div', class_='company_block')
        name = name_tag.find('h3').text.replace(str(code), "").strip() if name_tag else "-"
        
        price_tag = soup.find('span', class_='kabuka')
        price = price_tag.text.strip() if price_tag else "-"
        
        # 配当利回りを探す
        div_yield = "-"
        try:
            target = soup.find('div', id='stockinfo_i3')
            if target:
                tds = target.find_all('td')
                # 構造が変わる可能性があるため簡易探索
                for td in tds:
                    if "%" in td.text:
                        div_yield = td.text.strip()
                        break
        except: pass

        # 優待有無
        yutai = "なし"
        if "株主優待" in response.text:
            yutai = "あり"

        return {
            "コード": code, "銘柄": name, "現在値": price,
            "利回り": div_yield, "優待": yutai
        }
    except:
        return None

# --- アプリ画面 ---
st.title("📱 スマホ株リサーチ")
st.caption("株探データ簡易表示版")

input_codes = st.text_input("銘柄コード (カンマ区切り)", "7203, 8591, 9432")

if st.button("検索開始", type="primary"):
    codes = [c.strip() for c in input_codes.split(',') if c.strip()]
    
    if not codes:
        st.warning("コードを入力してください")
    else:
        results = []
        bar = st.progress(0)
        
        for i, code in enumerate(codes):
            data = get_stock_data(code)
            if data:
                results.append(data)
            bar.progress((i + 1) / len(codes))
            
        bar.empty()
        
        if results:
            df = pd.DataFrame(results)
            # スマホで見やすいようにカード形式で表示
            for index, row in df.iterrows():
                with st.container():
                    st.markdown(f"**{row['铭柄']} ({row['コード']})**")
                    col1, col2, col3 = st.columns(3)
                    col1.metric("株価", row['現在値'])
                    col2.metric("利回り", row['利回り'])
                    col3.write(f"優待: {row['優待']}")
                    st.divider()
        else:
            st.error("取得できませんでした")
