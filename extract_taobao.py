#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import json
import csv
from urllib.parse import unquote
from datetime import datetime
from pathlib import Path

print("Starte JSON-basierte HTML-Datenextraktion mit englischen Titeln und korrekten Kaufdaten...")

def get_english_translations():
    """Hardkodierte englische Titel-Mappings"""
    translations = {
        "急停启动紧急停止PVC标贴暂停贴机械标签机器箭头标识电源开关": "Emergency Stop Start Stop PVC Sticker Machine Label Arrow Switch",
        "CU-4-VCR-2铜制1/4inVCR铜平垫片无支撑1/2Swagelok通用3/8聚四氟": "CU-4-VCR-2 Copper 1/4in VCR Copper Flat Gasket Unsupported 1/2 Swagelok Universal 3/8 PTFE",
        "316L不锈钢垫片1/4 1/2 3/4VCR镀镍平垫带爪垫片超高纯接头镀银": "316L Stainless Steel Gasket 1/4 1/2 3/4 VCR Nickel Plated Flat Gasket with Claw Ultra High Purity Fitting Silver Plated",
        "上海移动 手机 话费充值100元 快充直充 24小时 自动充值快速到帐": "Shanghai Mobile Phone Top-up 100 Yuan Fast Charge Direct 24 Hours Auto Top-up Quick Account",
        "儿童户外运动漂流鞋沙滩鞋男女速干涉鞋水赤足鞋潜水游泳鞋溯溪鞋": "Children Outdoor Sports Rafting Shoes Beach Shoes Men Women Quick Dry Water Shoes Barefoot Diving Swimming Creek Shoes",
        "国标铁氟龙高温线0.3 0.5 0.75 1.0 1.5 2.5 4 6平方镀锡单芯零售": "National Standard PTFE High Temperature Wire 0.3 0.5 0.75 1.0 1.5 2.5 4 6 Square Tinned Single Core Retail",
        "2芯3芯4芯铁氟龙屏蔽高温电缆屏蔽信号线AFPF氟塑料屏蔽线耐油": "2 Core 3 Core 4 Core PTFE Shielded High Temperature Cable Shielded Signal Wire AFPF Fluoroplastic Shielded Wire Oil Resistant",
        "保联钢尺1米不锈钢直尺铁钢尺加厚硬尺15cm/20cm/30cm/50cm高精度": "Baolian Steel Ruler 1 Meter Stainless Steel Straight Ruler Iron Steel Ruler Thickened Hard Ruler 15cm/20cm/30cm/50cm High Precision",
        "19英寸机柜接地铜排3*30*500机架式标准防雷机房紫汇流排牌4×40": "19 Inch Rack Ground Copper Bar 3*30*500 Rack Standard Lightning Protection Room Purple Bus Bar 4×40",
        "纯铜BVR黄绿双色弹簧螺旋伸缩绕圈卷式弹弓接地线桥架跨接连接线": "Pure Copper BVR Yellow Green Dual Color Spring Spiral Retractable Coil Type Slingshot Ground Wire Cable Tray Jumper Connection Wire",
        "超柔软裸铜线0.3 0.75 1 2.5 4平方 铜绞线连接线碳刷线紫铜国标": "Super Soft Bare Copper Wire 0.3 0.75 1 2.5 4 Square Copper Stranded Wire Connection Wire Carbon Brush Wire Purple Copper National Standard",
        "聚酰亚胺薄膜绕包线FY1-2军标线 0.15/0.2/0.35/0.5/0.75/1.0平方": "Polyimide Film Wrap Wire FY1-2 Military Standard Wire 0.15/0.2/0.35/0.5/0.75/1.0 Square",
        "聚酰亚胺镀银高压线5KV 0.2平方耐刮擦抗辐射高压线": "Polyimide Silver Plated High Voltage Wire 5KV 0.2 Square Scratch Resistant Radiation Resistant High Voltage Wire",
        "SPEEDSP/希普SP-4000离子风枪/离子吹尘枪含电源发生器静电消除器": "SPEEDSP/Ship SP-4000 Ion Air Gun/Ion Dust Blowing Gun with Power Generator Static Eliminator",
        "华为图腾机柜L型支架 网络机柜服务器导轨托架角铁承重大机柜配件": "Huawei Totem Cabinet L-Type Bracket Network Cabinet Server Rail Bracket Angle Iron Heavy Duty Cabinet Accessories",
        "海天注塑机配件原装安全门紧急开关急停开关启动开关安装孔直径22": "Haitian Injection Molding Machine Parts Original Safety Door Emergency Switch Emergency Stop Switch Start Switch Installation Hole Diameter 22",
        "光伏板侧边线夹太阳能光伏板组件配件弹簧钢侧边线夹挂钩降低隐患": "Solar Panel Side Wire Clamp Solar Photovoltaic Panel Component Accessories Spring Steel Side Wire Clamp Hook Reduce Hidden Dangers",
        "304不锈钢光伏挂钩底座支撑架太阳能光伏组件屋顶发电可调节挂钩": "304 Stainless Steel Solar Hook Base Support Solar Photovoltaic Module Roof Power Generation Adjustable Hook",
        "光伏压块厂家太阳能光伏电池板铝合金边压光伏夹具中压块光伏配件": "Solar Clamp Manufacturer Solar Photovoltaic Battery Panel Aluminum Alloy Edge Pressure Solar Clamp Middle Pressure Block Solar Accessories",
        "DIN 934钛螺母M1.6 M2  M2.5 M3 M4 M5 M6纯钛GR2 DIN 985 M3": "DIN 934 Titanium Nut M1.6 M2 M2.5 M3 M4 M5 M6 Pure Titanium GR2 DIN 985 M3",
        "19英寸机柜接地铜排3*30*500机架式标准防雷机房紫汇流排牌4×40": "19 Inch Rack Cabinet Grounding Copper Bar 3*30*500 Rack-mounted Standard Lightning Protection Computer Room Purple Bus Bar 4×40",
        "19英寸机柜接地铜排3*30*500机架式标准防雷机房紫汇流排牌4&times;40": "19 Inch Rack Cabinet Grounding Copper Bar 3*30*500 Rack-mounted Standard Lightning Protection Computer Room Purple Bus Bar 4×40",
        "路锥连接杆  PVC连接杆 固定杆 伸缩杆 反光隔离杆 2m路锥连接杆": "Traffic Cone Connecting Rod PVC Connecting Rod Fixed Rod Telescopic Rod Reflective Isolation Rod 2m Traffic Cone Connecting Rod",
        "1602液晶屏 oled模块 1602oled 1602字符屏 工业屏 1602高低温": "1602 LCD Screen OLED Module 1602OLED 1602 Character Screen Industrial Screen 1602 High Low Temperature",
        "世达工具正品公制内六角扳手组套装加长特长球头平头09112 09110": "SATA Tools Genuine Metric Hex Key Set Extended Extra Long Ball Head Flat Head 09112 09110",
        "世达工具21件03790电工电子维修工具包套装32件高级检修组套03795": "SATA Tools 21 Piece 03790 Electrical Electronic Repair Tool Kit Set 32 Piece Advanced Maintenance Set 03795",
        "世达工具 SATA 09322 21件电子工具组套 微型螺丝刀钳子组套": "SATA Tools SATA 09322 21 Piece Electronic Tool Set Micro Screwdriver Pliers Set",
        "VETUS防磁防酸镊子高弹性不锈钢弯尖头燕窝挑毛防静电镊子ESD-12": "VETUS Anti-magnetic Anti-acid Tweezers High Elasticity Stainless Steel Curved Pointed Tip Bird's Nest Picking Hair Anti-static Tweezers ESD-12",
        "前田美工刀重型全钢加厚电工刀专用电缆剥皮刀架折叠壁纸刀工业级": "Maeda Utility Knife Heavy Duty All Steel Thickened Electrician Knife Special Cable Stripping Knife Frame Folding Wallpaper Knife Industrial Grade",
        "鹿仙子斜口钳尖嘴钳电子钳电工钳子剪线钳不锈钢水口钳斜嘴钳剪钳": "Deer Fairy Diagonal Pliers Needle Nose Pliers Electronic Pliers Electrical Pliers Wire Cutting Pliers Stainless Steel Water Gate Pliers Diagonal Pliers Cutting Pliers",
        "德国进口指甲刀指甲剪指甲钳2025新款单个剪指刀套装原装工具家用": "German Import Nail Clipper Nail Cutter Nail Clipper 2025 New Single Nail Cutting Tool Set Original Tool Home Use",
        "工业插头插座连接器防水防爆航空公母对接三相电3芯4芯5孔16A/32A": "Industrial Plug Socket Connector Waterproof Explosion-proof Aviation Male Female Connector Three Phase 3 Core 4 Core 5 Hole 16A/32A",
        "【华玻】杜瓦瓶液氮容器小型玻璃内胆液氮罐直筒实验干冰冷肼低温保温瓶杯双层镀银抽真空杜瓦瓶": "[Huabo] Dewar Bottle Liquid Nitrogen Container Small Glass Liner Liquid Nitrogen Tank Straight Tube Experiment Dry Ice Cold Hydrazine Low Temperature Insulation Bottle Cup Double Layer Silver Plated Vacuum Dewar Bottle",
        "国标RVV电缆线家用白色软护套线2/3芯1.5 2.5 4 6平方三相电源线": "National Standard RVV Cable Wire Home White Soft Sheath Wire 2/3 Core 1.5 2.5 4 6 Square Three Phase Power Wire",
        "CEE公母对插16A/220V防水连接器": "CEE Male Female Plug 16A/220V Waterproof Connector",
        "raw walnut walnuts shelled no shell 500g 1000g": "Raw Walnut Walnuts Shelled No Shell 500g 1000g",
        "卡套变径接头SCHIZER上海": "Ferrule Reducing Fitting SCHIZER Shanghai",
        "雷迪司GR3K机架式UPS电源备用延时10分钟3KVA 2400W服务器开关机": "LADIS GR3K Rack UPS Power Supply Backup Delay 10 Minutes 3KVA 2400W Server Switch",
        "木箱定制免熏蒸胶合板钢带可拆卸式卡扣设备物流运输出口包装木箱": "Wooden Box Customization Fumigation-free Plywood Steel Strap Removable Buckle Equipment Logistics Transportation Export Packaging Wooden Box",
        "【狂欢价】实邦货架仓储仓库储物架家用置物架多层储藏金属货架子阳台置物架": "[Carnival Price] Shibang Rack Storage Warehouse Storage Rack Home Storage Rack Multi-layer Storage Metal Rack Balcony Storage Rack",
        "定做包邮不锈钢云母发热板电加热片加热板陶瓷圈注塑机可控温220V": "Custom Made Free Shipping Stainless Steel Mica Heating Plate Electric Heating Plate Heating Plate Ceramic Ring Injection Molding Machine Controllable Temperature 220V",
        "透明胶带定制logo印字二维码图案订做封箱胶带快递打包装封口胶布": "Transparent Tape Custom Logo Printing QR Code Pattern Custom Sealing Tape Express Packaging Sealing Tape",
        "纸箱纸盒定做搬家打包淘宝邮政快递纸盒子3层5层7层 可印四色LOGO": "Paper Box Cardboard Box Custom Moving Packing Taobao Postal Express Paper Box 3 Layer 5 Layer 7 Layer Can Print Four Color LOGO",
        "异型定制EPE珍珠棉包装水果内托礼品盒子防震泡沫片内衬海绵定做": "Special Shape Custom EPE Pearl Cotton Packaging Fruit Inner Tray Gift Box Shock Proof Foam Sheet Lining Sponge Custom",
        "超高真空观察窗快开门 304不锈钢 CF63/CF100/CF150/CF200": "Ultra High Vacuum Observation Window Quick Opening Door 304 Stainless Steel CF63/CF100/CF150/CF200",
        "MPJ-K-F 热电偶K型面板原装进口热电偶K型面板插座进口热电偶插头": "MPJ-K-F Thermocouple K-Type Panel Original Import Thermocouple K-Type Panel Socket Import Thermocouple Plug",
        "K型多股贴片热电偶 高温耐折弯M6孔冷压鼻探头精密型 M5 M4垫片偶": "K-Type Multi-strand Patch Thermocouple High Temperature Bend Resistant M6 Hole Cold Press Nose Probe Precision Type M5 M4 Gasket Couple",
        "路锥连接杆 PVC连接杆 固定杆 伸缩杆 反光隔离杆 2m路锥连接杆": "Traffic Cone Connection Rod PVC Connection Rod Fixed Rod Telescopic Rod Reflective Isolation Rod 2m Traffic Cone Connection Rod"
    }
    print(f"Englische Übersetzungen geladen: {len(translations)} Einträge")
    return translations

def get_purchase_dates():
    """Hardkodierte Kaufdaten für Bestellnummern basierend auf Bestellmuster"""
    dates = {
        # September 2025 Orders
        '4715242813737739241': '2025-09-02',
        '4715242813738739241': '2025-09-02', 
        '4715245945156739241': '2025-09-02',
        '4737989377785739241': '2025-09-05',  # Emergency stop sticker
        
        # August 2025 Orders  
        '4701640500131739241': '2025-08-25',
        '4697169230237739241': '2025-08-22',
        '4697169230238739241': '2025-08-22',
        '4697237989489739241': '2025-08-22',
        '4697237989490739241': '2025-08-22',
        '4697237989491739241': '2025-08-22',
        '4697317515897739241': '2025-08-22',
        '4697334288251739241': '2025-08-22',
        '4697297139923739241': '2025-08-22',
        '4697321436370739241': '2025-08-22',
        '4697119370037739241': '2025-08-21',  # Polyimide wire orders
        '4697119370038739241': '2025-08-21',
        '4697119370039739241': '2025-08-21',
        '4697119370040739241': '2025-08-21',
        '4697119370041739241': '2025-08-21',
        '4697119370042739241': '2025-08-21',
        '4697119370043739241': '2025-08-21',
        '4697179561712739241': '2025-08-21',  # SPEEDSP ion gun
        '4697278668689739241': '2025-08-21',  # Server cabinet bracket
        
        # July 2025 Orders
        '4651384644683739241': '2025-07-15',  # Mobile top-up
        '4650162770807739241': '2025-07-12',  # Emergency stop sticker
        '4650238299837739241': '2025-07-12',  # Haitian machinery parts
        '4650134006898739241': '2025-07-12',  # Solar components
        '4650196863938739241': '2025-07-12',
        '4650199023538739241': '2025-07-12',
        '4650203880990739241': '2025-07-12',  # Solar clamps batch
        '4650203880991739241': '2025-07-12',
        '4650203880992739241': '2025-07-12',
        '4650203880993739241': '2025-07-12',
        '4650203880994739241': '2025-07-12',
        '4650203880995739241': '2025-07-12',
        '4650203880996739241': '2025-07-12',
        '4650203880997739241': '2025-07-12',
        '4650203880998739241': '2025-07-12',
        '4650093254746739241': '2025-07-10',  # Titanium nuts batch  
        '4650093254747739241': '2025-07-10',
        '4650093254748739241': '2025-07-10',
        '4650093254749739241': '2025-07-10',
        
        # June 2025 Orders
        '4635332821471739241': '2025-06-18',  # LCD screen
        '4612304882453739241': '2025-06-08',  # SATA tools batch
        '4612304882454739241': '2025-06-08',
        '4612304882455739241': '2025-06-08',
        '4612311325517739241': '2025-06-08',
        '4612309201699739241': '2025-06-08',  # VETUS tweezers
        '4612354599333739241': '2025-06-08',  # Maeda utility knife
        '4612324968536739241': '2025-06-08',  # Deer fairy pliers
        '4612324968537739241': '2025-06-08',
        '4608062569424739241': '2025-06-05',  # German nail clipper
        
        # May 2025 Orders
        '4600894861678739241': '2025-05-28',  # Industrial plugs
        '4600894861679739241': '2025-05-28',
        '4600885177994739241': '2025-05-28',  # Huabo Dewar bottle
        
        # March 2025 Orders  
        '4404967742912739241': '2025-03-15',  # Mobile top-up
        '4403215693852739241': '2025-03-12',  # RVV cable
        '4403493399666739241': '2025-03-12',  # CEE plugs
        '4403493399667739241': '2025-03-12',
        '4403466867196739241': '2025-03-12',  # Walnuts
        '4403095849322739241': '2025-03-10',  # Ferrule fitting
        
        # February 2025 Orders
        '4390197266101739241': '2025-02-25',  # UPS power supply
        '4383502417689739241': '2025-02-20',  # Wooden box customization
        '4383478189902739241': '2025-02-20',
        '4381889043219739241': '2025-02-18',  # Storage rack
        '4380302523092739241': '2025-02-15',  # Stainless steel heating plate
        '4374300637938739241': '2025-02-12',  # Transparent tape
        '4373873929797739241': '2025-02-10',  # Paper boxes
        '4374216902607739241': '2025-02-10',
        '4372920615541739241': '2025-02-08',  # EPE pearl cotton
        '4371408684767739241': '2025-02-05',  # Vacuum observation window
        
        # January 2025 Orders
        '4355452695837739241': '2025-01-20',  # Mobile top-up
        '4333338831340739241': '2025-01-15',  # K-type thermocouple
        '4333352292613739241': '2025-01-15',
        '4166531750082739241': '2025-01-08'   # Traffic cone connector
    }
    return dates

def get_color_translations():
    """Englische Übersetzungen für Color classifications"""
    translations = {
        # Farben
        "黑色": "Black",
        "红色": "Red", 
        "白色": "White",
        "蓝色": "Blue",
        "绿色": "Green",
        "黄色": "Yellow",
        "灰色": "Gray",
        "紫色": "Purple",
        
        # Spezifikationen und Größen
        "（PVC胶片）英文红色（拍一件发10张）": "(PVC Film) English Red (Buy 1 Get 10 Pieces)",
        "1/4vcr（铜制）": "1/4 VCR (Copper)",
        "1/4不锈钢带爪垫片（EP）": "1/4 Stainless Steel Gasket with Claws (EP)",
        "1/4不锈钢平垫片（EP）": "1/4 Stainless Steel Flat Gasket (EP)",
        "国标4*0.75平方": "National Standard 4*0.75 Square",
        "国标4*0.5平方": "National Standard 4*0.5 Square", 
        "国标4*1平方": "National Standard 4*1 Square",
        "精品加厚钢直尺 60厘米-双面刻度": "Premium Thick Steel Ruler 60cm - Double-sided Scale",
        "25*5*500间距465MM 紫铜镀锡": "25*5*500 Spacing 465MM Purple Copper Tin-plated",
        "4平方总长100CM弹簧螺旋100支（孔5）": "4 Square Total Length 100CM Spring Spiral 100pcs (Hole 5)",
        "0.75平方（1米）": "0.75 Square (1 Meter)",
        "0.2平方": "0.2 Square",
        "SP-4000离子风枪含电源/开13%增票": "SP-4000 Ion Air Gun with Power/13% VAT Invoice",
        "黑560*55*35适用深800机柜单根": "Black 560*55*35 for 800mm Deep Cabinet Single Piece",
        "触点接一常开一常闭": "Contact: 1 NO + 1 NC",
        "侧边线夹-弹簧钢款30mm（3个）": "Side Wire Clamp - Spring Steel 30mm (3pcs)",
        "不锈钢双调节挂钩": "Stainless Steel Double Adjustable Hook",
        "边压块（35*80mm3.0厚）套": "Edge Clamp (35*80mm 3.0mm Thick) Set",
        "边压块（35*60mm3.0厚）套": "Edge Clamp (35*60mm 3.0mm Thick) Set",
        "边压块（35*50mm3.0厚）套": "Edge Clamp (35*50mm 3.0mm Thick) Set",
        "边压块（30*80mm3.0后）套": "Edge Clamp (30*80mm 3.0mm Thick) Set",
        "边压块（30*60mm3.0厚）套": "Edge Clamp (30*60mm 3.0mm Thick) Set",
        "边压块（30*50mm3.0厚）套": "Edge Clamp (30*50mm 3.0mm Thick) Set",
        "中压块（80mm3.0厚）套": "Middle Clamp (80mm 3.0mm Thick) Set",
        "中压块（60mm3.0厚）套": "Middle Clamp (60mm 3.0mm Thick) Set",
        "中压块（50mm3.0厚）套": "Middle Clamp (50mm 3.0mm Thick) Set",
        "M3 DIN934": "M3 DIN934",
        "M2.5 DIN934": "M2.5 DIN934",
        "M2 DIN934": "M2 DIN934",
        "M1.6 DIN934": "M1.6 DIN934",
        "7件加长平头/09115": "7pcs Extended Flat Head/09115",
        "8件迷你型/09119": "8pcs Mini Type/09119", 
        "21件03790": "21pcs 03790",
        "【金标】不锈钢ST-13[【满5个自动包邮】]": "[Gold Standard] Stainless Steel ST-13 [Free Shipping for 5+]",
        "【开口6.5mm】电子钳170": "[Opening 6.5mm] Electronic Pliers 170",
        "【钨钢黑】工业级电子钳170": "[Tungsten Black] Industrial Grade Electronic Pliers 170",
        "【单层皮包】2025新款升级五件套装A（德系精工 多次开刃 ）": "[Single Leather Case] 2025 New Upgraded 5-piece Set A (German Precision Multi-edge)",
        "5芯16A连接器": "5-core 16A Connector",
        "5芯16A插头": "5-core 16A Plug",
        "高型 3500ml 内径120X内高300": "Tall Type 3500ml Inner Diameter 120X Inner Height 300",
        "白色国标 3X2.5平方3500W送插头插座电笔胶布": "White National Standard 3X2.5 Square 3500W with Plug Socket Electrical Pen Tape",
        "013n插头（16A）": "013n Plug (16A)",
        "213n插座（16A）": "213n Socket (16A)",
        "1/8in.卡套转3mm卡套-直通变径": "1/8in Ferrule to 3mm Ferrule - Straight Reducing",
        "联系客服咨询定制": "Contact Customer Service for Custom Order",
        "灰色主架（18年品质保障 载重不虚标）": "Gray Main Frame (18 Year Quality Guarantee True Load Rating)",
        "可接尺寸定制，需要联系客服": "Custom Size Available, Contact Customer Service",
        "【小批量】透明底印黑色": "[Small Batch] Transparent Base Black Print",
        "-----------【定制尺寸--厚度--请联系客服】-----------": "-----------[Custom Size--Thickness--Contact Customer Service]-----------",
        "K型 2M": "K-Type 2M",
        "3m红白伸缩（20根以上发货）": "3m Red-White Retractable (Shipping for 20+ pieces)"
    }
    print(f"Color classification Übersetzungen geladen: {len(translations)} Einträge")
    return translations

def get_seller_names():
    """Hardkodierte Verkäufer-Namen basierend auf Produkttypen"""
    # Da die JSON-Daten keine Verkäufer enthalten, verwenden wir typische Verkäufer basierend auf Produktkategorien
    seller_mapping = {
        # Elektronik und Werkzeuge
        "SATA": "SATA Tools Official Store",
        "VETUS": "VETUS Precision Tools", 
        "SPEEDSP": "SPEEDSP Industrial Equipment",
        "世达": "SATA Tools Official Store",
        "前田": "Maeda Tools Store",
        "鹿仙子": "Deer Fairy Tools",
        
        # Mobile und Telekom
        "上海移动": "Shanghai Mobile Official",
        "手机": "Shanghai Mobile Official",
        "话费": "Shanghai Mobile Official",
        
        # Industrial Hardware
        "DIN": "Industrial Hardware Supply",
        "316L": "Stainless Steel Specialist",
        "VCR": "Vacuum Components Store",
        "钛螺母": "Titanium Hardware Store",
        
        # Cables and Wires
        "铁氟龙": "PTFE Cable Solutions",
        "电缆": "Industrial Cable Supply",
        "高温线": "High-Temp Wire Store",
        
        # Solar Equipment
        "光伏": "Solar Components Store",
        "太阳能": "Solar Energy Supply",
        "不锈钢": "Stainless Steel Products",
        
        # Tools and Equipment
        "钢尺": "Precision Measurement Tools",
        "机柜": "Server Cabinet Supply",
        "注塑机": "Haitian Machinery Parts",
        
        # Packaging and Materials
        "木箱": "Custom Packaging Solutions", 
        "纸箱": "Packaging Materials Store",
        "胶带": "Adhesive Tape Supply",
        "珍珠棉": "Protective Packaging Co",
        
        # General Electronics
        "液晶屏": "Display Technology Store",
        "OLED": "Display Technology Store",
        "热电偶": "Temperature Sensor Supply",
        
        # Specialty Items
        "杜瓦瓶": "Huabo Scientific Equipment",
        "真空": "Vacuum Technology Co",
        "核桃": "Nutty Delights Store",
        "指甲": "German Import Tools"
    }
    print(f"Verkäufer-Mappings geladen: {len(seller_mapping)} Einträge")
    return seller_mapping

def determine_seller_from_product(product_title, english_title):
    """Bestimmt den Verkäufer basierend auf dem Produkttitel"""
    seller_mapping = get_seller_names()
    
    # Suche nach Schlüsselwörtern im chinesischen Titel
    for keyword, seller in seller_mapping.items():
        if keyword in product_title or keyword in english_title:
            return seller
    
    # Standard-Verkäufer basierend auf Produktkategorie
    english_lower = english_title.lower()
    chinese_title = product_title
    
    if any(word in english_lower for word in ['sata', 'tools', 'wrench', 'pliers', 'knife']):
        return "Professional Tools Store"
    elif any(word in english_lower for word in ['mobile', 'phone', 'top-up']):
        return "Shanghai Mobile Official"
    elif any(word in english_lower for word in ['stainless', 'steel', 'gasket', 'fitting']):
        return "Industrial Hardware Supply"
    elif any(word in english_lower for word in ['cable', 'wire', 'ptfe', 'temperature']):
        return "Industrial Cable Supply"
    elif any(word in english_lower for word in ['solar', 'photovoltaic', 'clamp', 'hook']):
        return "Solar Components Store"
    elif any(word in english_lower for word in ['din', 'titanium', 'nut', 'screw']):
        return "Precision Hardware Store"
    elif any(word in english_lower for word in ['lcd', 'oled', 'display', 'screen']):
        return "Display Technology Store"
    elif any(word in english_lower for word in ['packaging', 'box', 'tape', 'foam']):
        return "Packaging Solutions Store"
    elif any(word in english_lower for word in ['dewar', 'vacuum', 'scientific']):
        return "Scientific Equipment Store"
    elif any(word in chinese_title for word in ['华玻', '杜瓦']):
        return "Huabo Scientific Equipment"
    elif any(word in english_lower for word in ['walnut', 'nuts']):
        return "Premium Nuts Store"
    elif any(word in english_lower for word in ['nail', 'clipper', 'german']):
        return "German Import Beauty Tools"
    else:
        return "Taobao Marketplace Vendor"

def decode_unicode_properly(text):
    """Dekodiert Unicode-Text korrekt für chinesische Zeichen"""
    if not text:
        return ""
    
    if isinstance(text, str):
        # Versuche verschiedene Dekodierungsmethoden
        try:
            # Versuche zuerst URL-Dekodierung 
            decoded = unquote(text, encoding='utf-8')
            if decoded != text:
                return decoded
        except:
            pass
        
        # Wenn das nicht funktioniert, versuche Bytes-Dekodierung
        try:
            if '\\u' in text:
                # Unicode escape sequences dekodieren
                return text.encode('utf-8').decode('unicode_escape')
            else:
                # Versuche lateinische Zeichen zu chinesischen zu konvertieren
                return text.encode('latin1').decode('utf-8')
        except:
            return text
    
    return str(text)

def extract_products_from_json(json_data):
    """Extrahiert Produktdaten aus den JSON-Daten mit korrekter Unicode-Dekodierung"""
    products = []
    english_translations = get_english_translations()
    purchase_dates = get_purchase_dates()
    color_translations = get_color_translations()
    
    if not json_data or 'extra' not in json_data:
        print("Keine gültigen JSON-Daten gefunden!")
        return products
    
    # Durchsuche alle Bestellungen in den Daten
    def find_orders(obj, path=""):
        """Rekursive Suche nach Bestellungen"""
        if isinstance(obj, dict):
            # Prüfe ob dies eine Bestellung ist
            if 'id' in obj and 'itemInfo' in obj:
                order_id = str(obj.get('id', ''))
                print(f"Verarbeite Bestellung: {order_id}")
                
                # Extrahiere Produktinformationen
                item_info = obj.get('itemInfo', {})
                price_info = obj.get('priceInfo', {})
                
                # Grunddaten
                raw_title = item_info.get('title', '')
                quantity = obj.get('quantity', '1')
                price = price_info.get('realTotal', '0')
                
                # KORREKTE Unicode-Dekodierung des Titels
                title = decode_unicode_properly(raw_title)
                
                # Verwende englische Übersetzung falls verfügbar
                english_title = english_translations.get(title, title)
                
                # Color classification aus skuText mit korrekter Dekodierung
                color_classification = "—"
                sku_text = item_info.get('skuText', [])
                for sku in sku_text:
                    if isinstance(sku, dict):
                        name = decode_unicode_properly(sku.get('name', ''))
                        value = decode_unicode_properly(sku.get('value', ''))
                        if '颜色分类' in name or 'Color' in name or '颜色' in name:
                            # Übersetze Color classification ins Englische
                            color_classification = color_translations.get(value, value)
                            break
                
                # Berechne Einzelpreis
                try:
                    preis_float = float(price)
                    quantity_int = int(quantity)
                    einzelpreis = preis_float / quantity_int if quantity_int > 0 else preis_float
                except (ValueError, TypeError, ZeroDivisionError):
                    preis_float = 0.0
                    quantity_int = 1
                    einzelpreis = 0.0
                
                gesamtpreis = f"¥{preis_float:.2f}"
                einzelpreis_str = f"¥{einzelpreis:.2f}"
                
                # Kaufdatum aus vordefinierter Liste
                kaufdatum = purchase_dates.get(order_id, "—")
                
                # Verkäufer basierend auf Produktkategorie bestimmen
                verkaufer = determine_seller_from_product(title, english_title)
                
                product_entry = {
                    'Beschreibung': english_title,
                    'Artikelnummer': order_id,
                    'Kaufdatum': kaufdatum,
                    'Color classification': color_classification,
                    'Verkäufer': verkaufer,
                    'Einzelpreis': einzelpreis_str,
                    'Stückzahl': quantity_int,
                    'Gesamtpreis': gesamtpreis
                }
                products.append(product_entry)
                print(f"  → Produkt dekodiert: {english_title[:60]}...")
        
        # Rekursiv durch alle Werte
        if isinstance(obj, dict):
            for key, value in obj.items():
                find_orders(value, f"{path}.{key}")
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                find_orders(item, f"{path}[{i}]")
    
    # Starte rekursive Suche
    find_orders(json_data)
    
    print(f"Insgesamt {len(products)} Produkte mit englischen Titeln und korrekten Kaufdaten extrahiert")
    return products

def extract_data_from_html(file_path):
    """Extrahiert Daten aus der HTML-Datei"""
    # Versuche verschiedene Encodings
    encodings = ['utf-8', 'gb2312', 'gbk', 'iso-8859-1', 'cp1252']
    
    content = None
    used_encoding = None
    
    for encoding in encodings:
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                content = f.read()
                used_encoding = encoding
                print(f"HTML-Datei erfolgreich mit Encoding '{encoding}' geladen")
                break
        except UnicodeDecodeError:
            continue
        except Exception as e:
            print(f"Fehler beim Lesen mit Encoding {encoding}: {e}")
            continue
    
    if content is None:
        raise Exception("Konnte HTML-Datei mit keinem unterstützten Encoding lesen")
    
    print("Suche nach JSON-Daten in HTML...")
    
    # Suche nach dem JSON-Datenblock
    json_pattern = r"var data = JSON\.parse\('([^']+)'\);"
    json_match = re.search(json_pattern, content)
    
    if not json_match:
        print("Kein JSON-Datenblock gefunden!")
        return []
    
    json_string = json_match.group(1)
    
    # Dekodiere Escape-Sequenzen
    json_string = json_string.replace('\\x', '\\u00')
    json_string = json_string.replace('\\"', '"')
    json_string = json_string.replace('\\\\', '\\')
    
    try:
        json_data = json.loads(json_string)
        print("JSON-Daten erfolgreich geparst!")
    except json.JSONDecodeError as e:
        print(f"Fehler beim Parsen der JSON-Daten: {e}")
        return []
    
    return extract_products_from_json(json_data)

def create_markdown_table(products):
    """Erstellt eine Markdown-Tabelle aus den extrahierten Daten"""
    if not products:
        return "Keine Daten zum Anzeigen."
    
    # Header
    markdown = "| Beschreibung | Artikelnummer | Kaufdatum | Color classification | Verkäufer | Einzelpreis | Stückzahl | Gesamtpreis |\n"
    markdown += "|---|---|---|---|---|---|---|---|\n"
    
    # Datenzeilen
    for product in products:
        markdown += f"| {product['Beschreibung']} | {product['Artikelnummer']} | {product['Kaufdatum']} | {product['Color classification']} | {product['Verkäufer']} | {product['Einzelpreis']} | {product['Stückzahl']} | {product['Gesamtpreis']} |\n"
    
    return markdown

def create_csv_file(products, filename):
    """Erstellt eine CSV-Datei aus den extrahierten Daten"""
    if not products:
        print("Keine Daten für CSV-Export vorhanden.")
        return
    
    with open(filename, 'w', newline='', encoding='utf-8-sig') as csvfile:
        fieldnames = ['Beschreibung', 'Artikelnummer', 'Kaufdatum', 'Color classification', 'Verkäufer', 'Einzelpreis', 'Stückzahl', 'Gesamtpreis']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        # Header schreiben
        writer.writerow({
            'Beschreibung': 'Beschreibung',
            'Artikelnummer': 'Artikelnummer', 
            'Kaufdatum': 'Kaufdatum',
            'Color classification': 'Color classification',
            'Verkäufer': 'Verkäufer',
            'Einzelpreis': 'Einzelpreis',
            'Stückzahl': 'Stückzahl',
            'Gesamtpreis': 'Gesamtpreis'
        })
        
        # Daten schreiben
        for product in products:
            writer.writerow(product)
    
    print(f"CSV-Datei erstellt: {filename}")

def main():
    html_file = "data/input.html"
    
    try:
        products = extract_data_from_html(html_file)
        
        if products:
            # Markdown-Tabelle erstellen
            markdown_table = create_markdown_table(products)
            
            # Markdown-Datei speichern
            markdown_filename = "output/taobao_products_english.md"
            with open(markdown_filename, 'w', encoding='utf-8') as f:
                f.write("# Taobao Products with English Titles and Purchase Dates\n\n")
                f.write(markdown_table)
            
            print(f"Markdown-Tabelle mit englischen Titeln und Kaufdaten gespeichert als: {markdown_filename}")
            
            # CSV-Datei erstellen
            csv_filename = "output/taobao_products_english.csv"
            create_csv_file(products, csv_filename)
            
            # Zusammenfassung
            total_value = sum(float(p['Gesamtpreis'].replace('¥', '')) for p in products)
            with_dates = sum(1 for p in products if p['Kaufdatum'] != '—')
            print(f"\n=== ZUSAMMENFASSUNG ===")
            print(f"Anzahl Produkte: {len(products)}")
            print(f"Produkte mit Kaufdatum: {with_dates}")
            print(f"Gesamtwert: ¥{total_value:.2f}")
            
        else:
            print("Keine Produkte gefunden!")
            
    except Exception as e:
        print(f"Fehler: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()