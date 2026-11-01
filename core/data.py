class StaticData:
    TIANGAN = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
    DIZHI = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]
    SHENGXIAO = ["鼠", "牛", "虎", "兔", "龙", "蛇", "马", "羊", "猴", "鸡", "狗", "猪"]
    WUXING = {"甲": "木", "乙": "木", "丙": "火", "丁": "火",
              "戊": "土", "己": "土", "庚": "金", "辛": "金", "壬": "水", "癸": "水"}

    @classmethod
    def get_wuxing(cls, gan):
        return cls.WUXING.get(gan, "土")

    @classmethod
    def get_shengxiao(cls, year):
        return cls.SHENGXIAO[(year - 4) % 12]
