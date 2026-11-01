class WuxingEngine:
    WUXING_CYCLE = {"木": "火", "火": "土", "土": "金", "金": "水", "水": "木"}
    WUXING_OVERCYCLE = {"木": "土", "火": "金", "土": "水", "金": "木", "水": "火"}

    def analyze(self, element):
        sheng = self.WUXING_CYCLE.get(element)
        ke = self.WUXING_OVERCYCLE.get(element)
        return {
            "element": element,
            "generates": sheng,
            "controls": ke,
            "generated_by": [k for k, v in self.WUXING_CYCLE.items() if v == element],
            "controlled_by": [k for k, v in self.WUXING_OVERCYCLE.items() if v == element]
        }
