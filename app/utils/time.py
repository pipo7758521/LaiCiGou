import datetime


# 计算两个时间之间差值, 返回总的间隔秒数
def dif_time(d1: str, d2: str) -> float:
    da = datetime.datetime.strptime(d1, '%Y-%m-%d %H:%M:%S')
    db = datetime.datetime.strptime(d2, '%Y-%m-%d %H:%M:%S')
    total_seconds = (da - db).total_seconds()  # 总间隔秒数
    return abs(total_seconds)


# 判断两个时间是否相差大于半天
def greater_than_half_a_day(d1: str, d2: str) -> bool:
    return dif_time(d1, d2) >= 12 * 60 * 60
