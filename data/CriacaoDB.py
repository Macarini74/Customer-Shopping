import sqlite3
import pandas as pd

def criarTable():
    # 1. Lê o CSV
    df = pd.read_csv("data/shopping_trends.csv", sep=',', encoding='utf-8')

    # 2. Remove valores nulos e duplicatas
    df.dropna(inplace=True)
    df.drop_duplicates(inplace=True)

    # 3. Renomeia colunas para formato compatível com SQL (snake_case e sem caracteres especiais)
    df.rename(columns=lambda x: x.strip().lower().replace(' ', '_').replace('(', '').replace(')', ''), inplace=True)

    # 4. Converte tipos de dados quando necessário
    df['age'] = df['age'].astype(int)
    df['purchase_amount_usd'] = df['purchase_amount_usd'].astype(float)
    df['review_rating'] = df['review_rating'].astype(float)
    df['previous_purchases'] = df['previous_purchases'].astype(int)

    # 5. Cria conexão SQLite
    conn = sqlite3.connect("data/shopping.db")
    cursor = conn.cursor()

    # 6. Cria a tabela se não existir
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS shopping (
        customer_id TEXT,
        age INTEGER,
        gender TEXT,
        item_purchased TEXT,
        category TEXT,
        purchase_amount_usd REAL,
        location TEXT,
        size TEXT,
        color TEXT,
        season TEXT,
        review_rating REAL,
        subscription_status TEXT,
        payment_method TEXT,
        shipping_type TEXT,
        discount_applied TEXT,
        promo_code_used TEXT,
        previous_purchases INTEGER,
        preferred_payment_method TEXT,
        frequency_of_purchases TEXT
    )
    ''')

    # 7. Insere os dados no banco
    df.to_sql("shopping", conn, if_exists="replace", index=False)

    # 8. Finaliza
    conn.commit()
    conn.close()

