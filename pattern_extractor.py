import re
import pandas as pd

def extract_where_clause(sql_query):
    if pd.isnull(sql_query):
        return ""
    match = re.search(r'\bWHERE\b(.*)', str(sql_query), re.IGNORECASE)
    return match.group(1).strip() if match else str(sql_query).strip()

def normalize_pattern(clause):
    clause = str(clause).strip()

    clause = re.sub(r'%27', "'", clause)
    clause = re.sub(r'%20', ' ', clause)

    clause = clause.replace('\n', ' ').replace('\r', ' ').replace('\t', ' ')

    clause = re.sub(r'(--|#|/\*.*?\*/)', ' COMMENT ', clause)

    clause = re.sub(r'union\s+select', ' UNION_SELECT ', clause, flags=re.IGNORECASE)
    clause = re.sub(r'\b(or|and)\s+["\']?\w+["\']?\s*=\s*["\']?\w+["\']?', ' TAUTOLOGY ', clause, flags=re.IGNORECASE)
    clause = re.sub(r'\b(or|and)\s+1\s*=\s*1', ' TAUTOLOGY ', clause, flags=re.IGNORECASE)

    clause = re.sub(r';', ' SEMI ', clause)

    clause = re.sub(r"'[^']*'", ' STR ', clause)
    clause = re.sub(r'"[^"]*"', ' STR ', clause)

    clause = re.sub(r'\b\d+\b', ' NUM ', clause)

    replacements = {
        r'\b(and)\b': 'AND',
        r'\b(or)\b': 'OR',
        r'\b(select)\b': 'SELECT',
        r'\b(from)\b': 'FROM',
        r'\b(where)\b': 'WHERE',
        r'\b(like)\b': 'LIKE',
        r'\b(exists)\b': 'EXISTS',
        r'\b(not)\b': 'NOT',
        r'\b(null)\b': 'NULL',
        r'\b(is)\b': 'IS',
        r'\b(true|false)\b': lambda m: m.group(1).upper(),
        r'=': ' EQ ',
        r'<>|!=': ' NEQ ',
        r'>=': ' GTE ',
        r'<=': ' LTE ',
        r'>': ' GT ',
        r'<': ' LT ',
    }

    for pattern, repl in replacements.items():
        clause = re.sub(pattern, repl, clause, flags=re.IGNORECASE)

    clause = re.sub(
        r'\b(?!AND|OR|SELECT|FROM|WHERE|LIKE|UNION_SELECT|EXISTS|NOT|NULL|IS|EQ|NEQ|GTE|LTE|GT|LT|STR|NUM|COMMENT|SEMI|TRUE|FALSE|TAUTOLOGY|USER|PASS|ID)\w+\b',
        'VAR', clause
    )

    clause = re.sub(r'\s+', ' ', clause).strip()
    return clause

def process_csv(input_path, output_path):
    print(f"📂 Reading from {input_path}")
    df = pd.read_csv(input_path, encoding='utf-8', on_bad_lines='skip', engine='python', quoting=3)

    df.columns = df.columns.str.strip()
    if 'Query' not in df.columns or 'Label' not in df.columns:
        raise ValueError("CSV must contain 'Query' and 'Label' columns")

    df.dropna(subset=['Query', 'Label'], inplace=True)

    # ✅ Accept flexible label values
    df = df[df['Label'].isin([0, 1, '0', '1', 'Safe', 'Attack'])]
    df['Label'] = df['Label'].map({'0': 0, '1': 1, 'Safe': 0, 'Attack': 1, 0: 0, 1: 1})
    df.dropna(subset=['Label'], inplace=True)
    df['Label'] = df['Label'].astype(int)

    print(f"🔄 Extracting and normalizing patterns for {len(df)} queries...")
    df['where_clause'] = df['Query'].apply(extract_where_clause)
    df['pattern'] = df['where_clause'].apply(normalize_pattern)

    # 🐞 Debug preview
    print("\n🧪 Sample normalized patterns:")
    print(df[['Query', 'where_clause', 'pattern']].head(5))

    # Optional: remove long or empty patterns
    # df = df[df['pattern'].str.len() < 1000]
    df = df[df['pattern'].str.strip() != ""]

    df['Label'] = df['Label'].map({0: 'Safe', 1: 'Attack'})

    df_clean = df[['pattern', 'Label']]
    print(f"\n💾 Saving cleaned dataset with {len(df_clean)} rows to {output_path}")
    df_clean.to_csv(output_path, index=False, encoding='utf-8-sig')
    print("✅ Cleaning completed.")

if __name__ == "__main__":
    process_csv("Train.csv", "dataset.csv")
