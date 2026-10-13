#!/usr/bin/env python3
"""Find which Simplified-Chinese-only glyphs survive a CP932 whitelist.

CP932 is a superset of the Japanese repertoire (it carries NEC/IBM legacy
characters that modern Japanese never uses but which map to simplified
Chinese forms).  This prints, for a list of common Mainland-Chinese
characters, those that CP932 would wrongly accept -- the residual denylist.
"""
import re
import sys

CJK = re.compile(r'[㐀-䶿一-鿿豈-﫿]')

KNOWN = set()
for b in range(0x81, 0xFF):
    for b2 in list(range(0x40, 0x7F)) + list(range(0x80, 0xFD)):
        try:
            s = bytes([b, b2]).decode('cp932')
        except Exception:
            continue
        KNOWN |= set(CJK.findall(s))

# common Mainland-Chinese prose characters that are NOT the Japanese shinjitai
# form of the same word (i.e. real look-alike leaks, not shared kanji)
SUSPECT = (
    '厂区华协单卖卫厅历厉压厌厨厦县参双发变叙叠叶号叹吗员呐呕响哑唤'
    '啰喷团园围国图圆圣场坏块坚坛坟坠垄垒垦垫墙壮声壳处备复够头夸夹夺'
    '奋奖妆妇妈姗娄娇娱婴孙学宁宝实宠审宪宫宽宾对寻导寿将尔尘尽层届属'
    '岁岛岭岳峡崭岗卢师帐带帮广庄庆库应庙废开异弃张弯弹强归当录彻径御'
    '忧怀态怜总恋恳恼悦惊惧惨愿战户执扩扫扬扰抚抛抢护报担拟拢拣拦拧拨择'
    '挂挚挤挥损换据掷掺摆摇敌敛数斗断无旧时旷显晋晒晓晕暂术机杀杂权条来'
    '极构枢标栋栏树样档桥梦检楼欢欧残殴毁毕气汇汉污汤沟没沦沪泪泽洁洒浅'
    '测济浏浓涂涌涛润涨渐渔温湾湿溃滚满滤滥滨潜灭灯灵灾炉点炼烛烟烧热'
    '爱爷牵状独狭狮犹狱猎猫献玛环现玺珑琐琼瑶璃瓒电画畅疗疮疯痒痪痴瘾'
    '皱盐监盖盗盘瞒矫矿码砖础硕确碍礼祸禄离秃种积称税稳穷窃窍竖竞笔笼'
    '筑筛签简类粮紧纠红纤约级纪纬纯纲纳纵纷纸纹线练组细织终经结给络绝统'
    '继续维绵综绿缓编缘缝缠缩网罗罚罢羁翘耻聂聋职联聪肃肠肤肿胀胁胆胜脉脑'
    '脚脱脸腊腾舆舰艰艳艺节芜苇苍苏苹茎茧荐荡荣药莱获莹萤营萧蓝虏虑虚虫'
    '虽虾蚁蚀蚁蚕蛮蜡蝇蝉补衬袄装裤见观规觅视览觉触誉计订认讥讨让训议讯'
    '记讲许论讼讽设访证识诉诊词译试诗诚话诞询该详语误说读课谁调谈谋谎'
    '谐谓谜谢谣谦谨谱贝贞负贡财责贤败账货质贩贪贫购贮贯贱贴贵贷贸费贺'
    '贼贾贿赁资赋赌赎赏赔赖赚赛赞赠赢赣赵赶趋跃践踊踪蹑躯车轧轨轩转轮'
    '软轰轻载较辅辆辈辉辍辐输辕辖辗辙辞辩辫边辽达迁过迈运还这进远违连'
    '迟迹适选逊递逻遗邓邮郑酝释里鉴钟钢钥钦钩钮钱钳钻铁铃铅铜铝铠铡铣'
    '铨铭银铸铺链销锁锂锄锋锐错锡锣锤锦键锯镇镜镰镶长门闪闭问闯闲间闷闻'
    '阀阁阅阔队阳阴阵阶际陆陈陨险随隐难雏雾霉静鞑韦韧韩韬韵页顶顷项顺须'
    '顽顾顿颁颂预领颇颈颊颈频颓颖题颜额颠风飘飞饥饭饮饰饱饲饼饿馆馒马驱'
    '驳驴驶驸驹驻驼驾骂骄骆验骏骑骗骚鱼鲁鲜鲤鲨鲸鳄鳖鸟鸠鸡鸣鸥鸦鸭鸯'
    '鸳鸽鹅鹉鹊鹏鹤鹦鹰麦黄黑齐齿龄龙龚龟够这说门车长问题东开关间还为见'
    '风书马鸟厂商效果网络价格性能够家当号级这'
)

bad = [c for c in SUSPECT if c in KNOWN]
print(f'CP932 kanji repertoire: {len(KNOWN)}')
print(f'suspect chars: {len(set(SUSPECT))}')
print(f'STILL ACCEPTED by CP932 ({len(bad)}): {"".join(bad)}')
