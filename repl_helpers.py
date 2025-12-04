def display_article(article: dict):
    print("{")
    for k, v in article.items():
        print(f"{k}: {truncate_str(v, 32)}")
    print("}")

def truncate_str(string: str, max_len: int):
    if (max_len <= 0) or (len(string) <= max_len):
        return string
    if len(string) > max_len:
        result = string[:max_len]
    if len(result) > 3:
        result = result[:-3] + "..."
    return result

