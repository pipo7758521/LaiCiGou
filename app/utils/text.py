# 列表去重并保持原来的顺序，返回不同元素的个数
def remove_duplicate_elements(l):
    n = list(set(l))
    n.sort(key=l.index)
    return n
