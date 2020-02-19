# encoding: UTF-8

import json
import csv
import time
import pyqtgraph as pg
from collections import OrderedDict

from six import text_type

from vnpy.event import *
from .vtEvent import *
from .vtEngine import DataEngine
from .vtFunction import *
from .vtGateway import *
from .import vtText
from .uiQt import QtGui, QtWidgets, QtCore, BASIC_FONT
from .vtFunction import jsonPathDict
from .vtConstant import *

COLOR_RED = QtGui.QColor('red')
COLOR_GREEN = QtGui.QColor('green')
COLOR_YELLOW = QtGui.QColor('#808001')
COLOR_BROWN = QtGui.QColor('#E5A82E')
COLOR_WHITE = QtGui.QColor('white')
TREE_COLOR_RED = QtGui.QBrush(QtGui.QColor('red'))
TREE_COLOR_GREEN = QtGui.QBrush(QtGui.QColor('green'))
TREE_COLOR_YELLOW = QtGui.QBrush(QtGui.QColor('#808001'))
TREE_COLOR_BROWN = QtGui.QBrush(QtGui.QColor('#E5A82E'))
TREE_COLOR_NONE =  QtGui.QBrush(QtGui.QColor('Pink'))

LOCKPOSITION = {}
DEFAULT_OPEM = {}
subscribeDefault = json.load(open('./subscribeDefault.json', 'r'))
for subscribe in subscribeDefault:
    #确定锁仓
    if subscribe['symbol'] != u''and subscribe['lock_Position'] != u'':
        LOCKPOSITION[subscribe['symbol']] = int(subscribe['lock_Position'])
    if subscribe['symbol'] != u''and subscribe['default_Open'] != u'':
        DEFAULT_OPEM[subscribe['symbol']] = int(subscribe['default_Open'])
# 定义键盘字典
DEFINE_KEY = {'Space': 57, '0': 11, '1': 2, '2': 3, '3': 4, '4': 5,
               '5': 6, '6': 7, '7': 8, '8': 9, '9': 10, 'F1': 59, 'F2': 60, 'F3': 61,
               'F4': 62, 'F5': 63, 'F6': 64, 'F7': 65, 'F8': 66, 'F9': 67, 'F10': 68
            , 'F11': 87, 'F12': 88, u'小键盘0': 82, u'小键盘1': 79, u'小键盘2': 80, u'小键盘3': 81,
               u'小键盘4': 75, u'小键盘5': 76, u'小键盘6': 77, u'小键盘7': 71, u'小键盘8': 72, u'小键盘9': 73, '': ''}
HOTKEY = {}
hotkeyDefault = json.load(open('./hotKey.json', 'r'))
for hk in hotkeyDefault:
    HOTKEY[DEFINE_KEY[hk['hotkey']]] = hk
########################################################################
class BasicCell(QtWidgets.QTableWidgetItem):
    """基础的单元格"""

    #----------------------------------------------------------------------
    def __init__(self, text=None, mainEngine=None):
        """Constructor"""
        super(BasicCell, self).__init__()
        self.data = None
        if text:
            self.setContent(text)

    #----------------------------------------------------------------------
    def setContent(self, text):
        """设置内容"""
        if text == '0' or text == '0.0':
            self.setText('')
        else:
            self.setText(text)


########################################################################
class HotKeyBasicCell(QtWidgets.QTableWidgetItem):
    """基础的单元格"""

    # ----------------------------------------------------------------------
    def __init__(self, text=None, mainEngine=None):
        """Constructor"""
        super(HotKeyBasicCell, self).__init__()
        self.data = None
        if text:
            self.setContent(text)
#----------------------------------------------------------------------
    def setContent(self, text):
        """设置内容"""
        self.setText(text)
########################################################################
class NumCell(QtWidgets.QTableWidgetItem):
    """用来显示数字的单元格"""

    #----------------------------------------------------------------------
    def __init__(self, text=None, mainEngine=None):
        """Constructor"""
        super(NumCell, self).__init__()
        self.data = None
        if text:
            self.setContent(text)
    
    #----------------------------------------------------------------------
    def setContent(self, text):
        """设置内容"""
        # 考虑到NumCell主要用来显示OrderID和TradeID之类的整数字段，
        # 这里的数据转化方式使用int类型。但是由于部分交易接口的委托
        # 号和成交号可能不是纯数字的形式，因此补充了一个try...except
        try:
            num = int(text)
            self.setData(QtCore.Qt.DisplayRole, num)
        except ValueError:
            self.setText(text)
            
class ProfitCell(QtWidgets.QTableWidgetItem):
    """用来显示盈利的单元格"""

    # ----------------------------------------------------------------------
    def __init__(self, text=None, mainEngine=None):
        """Constructor"""
        super(ProfitCell, self).__init__()
        self.data = None
        if text:
            self.setContent(text)
    # ----------------------------------------------------------------------
    def setContent(self, text):
        """设置内容"""
        try:
            if float(text) > 0.0:
                self.setForeground(QtGui.QColor('red'))
            else:
                self.setForeground(QtGui.QColor('green'))
            num = int(text)
            self.setData(QtCore.Qt.DisplayRole, num)
        except ValueError:
            self.setText(text)

########################################################################
class DirectionCell(QtWidgets.QTableWidgetItem):
    """用来显示买卖方向的单元格"""
    #----------------------------------------------------------------------
    def __init__(self, text=None, mainEngine=None):
        """Constructor"""
        super(DirectionCell, self).__init__()
        self.data = None
        if text:
            self.setContent(text)
        
    #----------------------------------------------------------------------
    def setContent(self, text):
        """设置内容"""
        if text == DIRECTION_LONG or text == DIRECTION_NET:
            self.setForeground(QtGui.QColor('red'))
        elif text == DIRECTION_SHORT:
            self.setForeground(QtGui.QColor('green'))
        self.setText(text)
########################################################################
class NameCell(QtWidgets.QTableWidgetItem):
    """用来显示合约中文的单元格"""

    #----------------------------------------------------------------------
    def __init__(self, text=None, mainEngine=None):
        """Constructor"""
        super(NameCell, self).__init__()
        
        self.mainEngine = mainEngine
        self.data = None
        
        if text:
            self.setContent(text)
        
    #----------------------------------------------------------------------
    def setContent(self, text):
        """设置内容"""
        if self.mainEngine:
            # 首先尝试正常获取合约对象
            contract = self.mainEngine.getContract(text)
            
            # 如果能读取合约信息
            if contract:
                self.setText(contract.name)


########################################################################
class BidCell(QtWidgets.QTableWidgetItem):
    """买价单元格"""

    #----------------------------------------------------------------------
    def __init__(self, text=None, mainEngine=None):
        """Constructor"""
        super(BidCell, self).__init__()
        self.data = None

        self.setForeground(QtGui.QColor('black'))
        self.setBackground(QtGui.QColor(255,174,201))
        
        if text:
            self.setContent(text)
    
    #----------------------------------------------------------------------
    def setContent(self, text):
        """设置内容"""
        self.setText(text)


########################################################################
class AskCell(QtWidgets.QTableWidgetItem):
    """卖价单元格"""

    #----------------------------------------------------------------------
    def __init__(self, text=None, mainEngine=None):
        """Constructor"""
        super(AskCell, self).__init__()
        self.data = None

        self.setForeground(QtGui.QColor('black'))
        self.setBackground(QtGui.QColor(160,255,160))
        
        if text:
            self.setContent(text)
    
    #----------------------------------------------------------------------
    def setContent(self, text):
        """设置内容"""
        self.setText(text)


########################################################################
class PnlCell(QtWidgets.QTableWidgetItem):
    """显示盈亏的单元格"""

    #----------------------------------------------------------------------
    def __init__(self, text=None, mainEngine=None):
        """Constructor"""
        super(PnlCell, self).__init__()
        self.data = None
        self.color = ''
        if text:
            self.setContent(text)
    
    #----------------------------------------------------------------------
    def setContent(self, text):
        """设置内容"""
        self.setText(text)

        try:
            value = float(text)
            if value >= 0 and self.color != 'red':
                self.color = 'red'
                self.setForeground(COLOR_RED)
            elif value < 0 and self.color != 'green':
                self.color = 'green'
                self.setForeground(COLOR_GREEN)
        except ValueError:
            pass

########################################################################

class OrderStatusCell(QtWidgets.QTableWidgetItem):
    """显示委托的单元格"""

    # ----------------------------------------------------------------------
    def __init__(self, text=None, mainEngine=None):
        """Constructor"""
        super(OrderStatusCell, self).__init__()
        self.data = None
        self.color = ''
        if text:
            self.setContent(text)

    # ----------------------------------------------------------------------
    def setContent(self, text):
        """设置内容"""
        self.setText(text)
        try:
            value = text
            if value == u'已撤单' and self.color != 'brown':
                self.color = 'brown'
                self.setForeground(COLOR_BROWN)
            elif value == u'全部成交' and self.color != 'green':
                self.color = 'green'
                self.setForeground(COLOR_GREEN)
            elif value == u'未成交'and self.color != 'yellow':
                self.color = 'yellow'
                self.setForeground(COLOR_YELLOW)
            elif value == u'部分成交'and self.color != 'yellow':
                self.color = 'yellow'
                self.setForeground(COLOR_YELLOW)

        except ValueError:
            pass


########################################################################
class TradeStatusCell(QtWidgets.QTableWidgetItem):
    """显示委托的单元格"""

    # ----------------------------------------------------------------------
    def __init__(self, text=None, mainEngine=None):
        """Constructor"""
        super(TradeStatusCell, self).__init__()
        self.data = None
        self.color = ''
        if text:
            self.setContent(text)

    # ----------------------------------------------------------------------
    def setContent(self, text):
        """设置内容"""
        self.setText(text)
        try:
            value = text
            if value == u'已撤销' and self.color != 'brown':
                self.color = 'brown'
                self.setForeground(COLOR_BROWN)
            elif value == u'全部成交' and self.color != 'green':
                self.color = 'green'
                self.setForeground(COLOR_GREEN)
            elif value == u'未成交'and self.color != 'yellow':
                self.color = 'yellow'
                self.setForeground(COLOR_YELLOW)
            elif value == u'部分成交'and self.color != 'yellow':
                self.color = 'yellow'
                self.setForeground(COLOR_YELLOW)

        except ValueError:
            pass
########################################################################

class BasicTreeMonitor(QtWidgets.QTreeWidget):
    """
    基础监控

    headerDict中的值对应的字典格式如下
    {'chinese': u'中文名', 'cellType': BasicCell}

    """
    signal = QtCore.Signal(type(Event()))
    signalTrade = QtCore.Signal(type(Event()))

    # ----------------------------------------------------------------------
    def __init__(self, mainEngine=None, eventEngine=None, parent=None):
        """Constructor"""
        super(BasicTreeMonitor, self).__init__(parent)

        self.mainEngine = mainEngine
        self.eventEngine = eventEngine

        # 保存表头标签用
        self.headerDict = OrderedDict()  # 有序字典，key是英文名，value是对应的配置字典
        self.headerList = []  # 对应self.headerDict.keys()

        # 保存相关数据用
        self.dataDict = {}  # 字典，key是字段对应的数据，value是保存相关单元格的字典
        self.dataKey = ''  # 字典键对应的数据字段

        # 监控的事件类型
        self.eventType = ''

        # 列宽调整状态（只在第一次更新数据时调整一次列宽）
        self.columnResized = False

        # 字体
        self.font = None

        # 保存数据对象到单元格
        self.saveData = False

        # 初始化右键菜单
        self.initMenu()

    # ----------------------------------------------------------------------
    def setHeaderDict(self, headerDict):
        """设置表头有序字典"""
        self.headerDict = headerDict
        self.headerList = headerDict.keys()

    # ----------------------------------------------------------------------
    def setFont(self, font):
        """设置字体"""
        self.font = font

    # ----------------------------------------------------------------------
    def setSaveData(self, saveData):
        """设置是否要保存数据到单元格"""
        self.saveData = saveData
    # ----------------------------------------------------------------------
    def initTable(self):
        """初始化表格"""
        self.setIndentation(6)
        # 设置列表头
        labels = [d['chinese'] for d in self.headerDict.values()]
        self.setHeaderLabels(labels)

        # 设为不可编辑
        self.setEditTriggers(self.NoEditTriggers)
        #self.setStyleSheet("QTreeWidget::item{border:1px solid}")
        self.childDict = {}
        self.parentDict = {}
    # ----------------------------------------------------------------------
    def registerEvent(self):
        """注册GUI更新相关的事件监听"""
        pass
    # ----------------------------------------------------------------------
    def importData(self, data):
        """将数据更新到表格中"""
        if data['level'] is EMPTY_INT:

            if data['orderID'] in self.parentDict.keys():
                parent = self.parentDict[data['orderID']]
            else:
                parent = QtWidgets.QTreeWidgetItem()
                self.insertTopLevelItem(0,parent)
        else:
            # 设置子项
            if data['orderChildID'] in self.childDict.keys():
                parent = self.childDict[data['orderChildID']]
            else:
                if data['orderID'] not in self.parentDict.keys():
                    pass
                else:
                    self.childDict[data['orderChildID']] = QtWidgets.QTreeWidgetItem(self.parentDict[data['orderID']])
                    parent = self.childDict[data['orderChildID']]

        if data['orderID'] == data['tradeID']:
            #如果报单不存在，则新增报单
            try:
                self.setItem(parent, data)
                if data['orderID'] not in self.parentDict.keys():
                    self.parentDict[data['orderID']] = parent
            except UnboundLocalError:
                print "local variable 'parent' referenced before assignment"
                pass
        else:
            try:
                self.setItem(parent,data)
                if data['complete'] and data['offset'] is OFFSET_CLOSETODAY:
                    priceTick = self.getContract(data['vtSymbol']).__getattribute__('priceTick')
                    size = self.getContract(data['vtSymbol']).size
                    parent.parent().setBackground(5,TREE_COLOR_GREEN)
                    parent.parent().setForeground(5, COLOR_GREEN)

                    ProfitSize = EMPTY_FLOAT #每单盈亏
                    #汇总子目录的盈亏到总盈亏，注意：总盈亏是以盈亏点来计算
                    #价差 = 盈亏 / （成交量 * size）
                    #盈亏点 = 价差 / priceTick
                    for i in range(0,parent.parent().childCount()):
                        ProfitSize = ProfitSize + float(parent.parent().child(i).text(4).encode("utf-8"))
                    ProfitSize = round(ProfitSize / (int(parent.parent().text(8).encode("utf-8")) *  size),1)
                    #j计算平仓价格
                    if data['direction'] is DIRECTION_SHORT:
                        CloseBookPrice = (float(parent.parent().text(6).encode("utf-8"))) + ProfitSize
                    elif data['direction'] is DIRECTION_LONG:
                        CloseBookPrice = (float(parent.parent().text(6).encode("utf-8"))) - ProfitSize
                    parent.parent().setText(7, str(CloseBookPrice))
                    parent.parent().setText(4, str(ProfitSize))
            except UnboundLocalError:
                print "local variable 'parent' referenced before assignment"
                pass

        # 调整列宽
        if not self.columnResized:
            for i in range(0,10):
                self.resizeColumnToContents(i)
            self.columnResized = True

    def setItem(self, parent, data):
        parent.setText(0, data['tradeTime'])
        parent.setText(1, data['symbol'])
        parent.setText(2, data['direction'])
        parent.setText(3, data['offset'])
        parent.setText(4, str(data['closeProfit']))
        parent.setTextAlignment(4, -1)
        parent.setText(5, data['status'])
        font = self.setFont(data['status'])
        if font is not None:
            parent.setForeground(5, font)
            if parent.parent() is None:
                parent.setForeground(5, COLOR_WHITE)
        background = self.setBackGround(data['offset'], data['status'])
        if background is not None:
            parent.setBackground(5, background)
            if background is TREE_COLOR_RED:
                parent.setForeground(5, COLOR_RED)
        parent.setText(6, str(data['book_price']))
        parent.setText(7, str(data['close_book_price']))
        parent.setText(8, str(data['volume']))
        parent.setText(9, data['tradeID'])
        parent.setText(10, data['gatewayName'])
    def setBackGround(self, offset, status):
        if status is STATUS_CANCELLED and offset is OFFSET_OPEN:
            return  None
        elif status is STATUS_ALLTRADED and offset is OFFSET_OPEN:
            return TREE_COLOR_RED
        elif status is STATUS_NOTTRADED and offset is OFFSET_OPEN:
            return None
        elif status is STATUS_PARTTRADED and offset is OFFSET_OPEN:
            return None
        else:
            return None
    def setFont(self, value):
        if value == u'已撤单':
            return COLOR_BROWN
        elif value == u'全部成交':
            return COLOR_GREEN
        elif value == u'未成交':
            return COLOR_YELLOW
        elif value == u'部分成交':
            return COLOR_YELLOW
        else:
            return None

    def getContract(self, vtSymbol):
        " 获取contract"
        contract = self.mainEngine.getContract(vtSymbol)
        return contract
    # ----------------------------------------------------------------------
    def saveToCsv(self):
        """保存表格内容到CSV文件"""
        # 先隐藏右键菜单
        self.menu.close()
        now = int(time.time())
        timeStruct = time.localtime(now)
        strTime = time.strftime("%Y%m%d", timeStruct)
        saveDir = "D:\VNPY\交易记录\/" +  strTime + "\/"
        if os.path.exists(safeUnicode(saveDir)) is False:
            os.makedirs(safeUnicode(saveDir))
        fileNameToSave = "D:\VNPY\交易记录\/" +  strTime + "\/" + vtText.TRADE +"_" + strTime
        # 获取想要保存的文件名
        path = QtWidgets.QFileDialog.getSaveFileName(self, vtText.SAVE_DATA, fileNameToSave, 'CSV(*.csv)')
        try:
            # if not path.isEmpty():
            if path:
                with open(safeUnicode(path[0]), 'wb') as f:
                    writer = csv.writer(f)
                    # 保存标签
                    VTTEXT = []
                    for CHN in self.headerDict.values():
                        VTTEXT.append(CHN['chinese'])
                    headers = [header.encode('gbk') for header in VTTEXT]
                    writer.writerow(headers)
                    # 保存每行内容
                    iterator = QtWidgets.QTreeWidgetItemIterator(self)
                    while iterator.value():
                        if iterator.value().parent() is None:
                            rowdata = []
                            for column in range(self.columnCount()):
                                rowdata.append(
                                    unicode(iterator.value().text(column)).encode('gbk'))
                            writer.writerow(rowdata)
                        iterator += 1
        except IOError:
            print "IOError"

    # ----------------------------------------------------------------------
    def initMenu(self):
        """初始化右键菜单"""
        self.menu = QtWidgets.QMenu(self)

        saveAction = QtWidgets.QAction(vtText.SAVE_DATA, self)
        saveAction.triggered.connect(self.saveToCsv)

        self.menu.addAction(saveAction)

    # ----------------------------------------------------------------------
    def contextMenuEvent(self, event):
        """右键点击事件"""
        self.menu.popup(QtGui.QCursor.pos())

########################################################################

class BasicMonitor(QtWidgets.QTableWidget):
    """
    基础监控
    
    headerDict中的值对应的字典格式如下
    {'chinese': u'中文名', 'cellType': BasicCell}
    
    """
    signal = QtCore.Signal(type(Event()))

    #----------------------------------------------------------------------
    def __init__(self, mainEngine=None, eventEngine=None, parent=None):
        """Constructor"""
        super(BasicMonitor, self).__init__(parent)
        
        self.mainEngine = mainEngine
        self.eventEngine = eventEngine
        
        # 保存表头标签用
        self.headerDict = OrderedDict()  # 有序字典，key是英文名，value是对应的配置字典
        self.headerList = []             # 对应self.headerDict.keys()
        
        # 保存相关数据用
        self.dataDict = {}  # 字典，key是字段对应的数据，value是保存相关单元格的字典
        self.dataKey = ''   # 字典键对应的数据字段
        
        # 监控的事件类型
        self.eventType = ''
        
        # 列宽调整状态（只在第一次更新数据时调整一次列宽）
        self.columnResized = False
        
        # 字体
        self.font = None
        
        # 保存数据对象到单元格
        self.saveData = False
        
        # 默认不允许根据表头进行排序，需要的组件可以开启
        self.sorting = False
        
        # 初始化右键菜单
        self.initMenu()

        # csv文件保存名
        self.fileNameToSave = EMPTY_STRING
        
    #----------------------------------------------------------------------
    def setHeaderDict(self, headerDict):
        """设置表头有序字典"""
        self.headerDict = headerDict
        self.headerList = headerDict.keys()
        
    #----------------------------------------------------------------------
    def setDataKey(self, dataKey):
        """设置数据字典的键"""
        self.dataKey = dataKey
        
    #----------------------------------------------------------------------
    def setEventType(self, eventType):
        """设置监控的事件类型"""
        self.eventType = eventType
        
    #----------------------------------------------------------------------
    def setFont(self, font):
        """设置字体"""
        self.font = font
    
    #----------------------------------------------------------------------
    def setSaveData(self, saveData):
        """设置是否要保存数据到单元格"""
        self.saveData = saveData
        
    #----------------------------------------------------------------------
    def initTable(self):
        """初始化表格"""
        # 设置表格的列数
        col = len(self.headerDict)
        self.setColumnCount(col)
        
        # 设置列表头
        labels = [d['chinese'] for d in self.headerDict.values()]
        self.setHorizontalHeaderLabels(labels)
        
        # 关闭左边的垂直表头
        self.verticalHeader().setVisible(False)
        
        # 设为不可编辑
        self.setEditTriggers(self.NoEditTriggers)
        
        # 设为行交替颜色
        self.setAlternatingRowColors(True)
        
        # 设置允许排序
        self.setSortingEnabled(self.sorting)


        #----------------------------------------------------------------------
    def registerEvent(self):
        """注册GUI更新相关的事件监听"""
        self.signal.connect(self.updateEvent)
        self.eventEngine.register(self.eventType, self.signal.emit)
        
    #----------------------------------------------------------------------
    def updateEvent(self, event):
        """收到事件更新"""
        data = event.dict_['data']
        self.updateData(data)
    
    #----------------------------------------------------------------------
    def updateData(self, data):
        """将数据更新到表格中"""
        # 如果允许了排序功能，则插入数据前必须关闭，否则插入新的数据会变乱
        if self.sorting:
            self.setSortingEnabled(False)

        # 如果设置了dataKey，则采用存量更新模式
        if self.dataKey:
            key = data.__getattribute__(self.dataKey)
            # 如果键在数据字典中不存在，则先插入新的一行，并创建对应单元格
            if key not in self.dataDict:
                self.insertRow(0)
                d = {}
                for n, header in enumerate(self.headerList):                  
                    content = safeUnicode(data.__getattribute__(header))
                    cellType = self.headerDict[header]['cellType']
                    cell = cellType(content, self.mainEngine)
                    if self.font:
                        cell.setFont(self.font)  # 如果设置了特殊字体，则进行单元格设置
                    
                    if self.saveData:            # 如果设置了保存数据对象，则进行对象保存
                        cell.data = data
                        
                    self.setItem(0, n, cell)
                    d[header] = cell
                self.dataDict[key] = d
            # 否则如果已经存在，则直接更新相关单元格
            else:
                d = self.dataDict[key]
                for header in self.headerList:
                    content = safeUnicode(data.__getattribute__(header))
                    cell = d[header]
                    cell.setContent(content)
                    
                    if self.saveData:            # 如果设置了保存数据对象，则进行对象保存
                        cell.data = data
        # 否则采用增量更新模式
        else:
            self.insertRow(0)  
            for n, header in enumerate(self.headerList):
                content = safeUnicode(data.__getattribute__(header))
                cellType = self.headerDict[header]['cellType']
                cell = cellType(content, self.mainEngine)
                
                if self.font:
                    cell.setFont(self.font)

                if self.saveData:
                    cell.data = data                

                self.setItem(0, n, cell)

        # 调整列宽
        if not self.columnResized:
            self.resizeColumns()
            self.columnResized = True
        
        # 重新打开排序
        if self.sorting:
            self.setSortingEnabled(True)
    
    #----------------------------------------------------------------------
    def resizeColumns(self):
        """调整各列的大小"""
        self.horizontalHeader().resizeSections(QtWidgets.QHeaderView.ResizeToContents)    
        
    #----------------------------------------------------------------------
    def setSorting(self, sorting):
        """设置是否允许根据表头排序"""
        self.sorting = sorting
        
    #----------------------------------------------------------------------
    def saveToCsv(self):
        """保存表格内容到CSV文件"""
        # 先隐藏右键菜单
        self.menu.close()
        # 获取想要保存的文件名
        path = QtWidgets.QFileDialog.getSaveFileName(self, vtText.SAVE_DATA, self.fileNameToSave, 'CSV(*.csv)')
        try:
            #if not path.isEmpty():
            if path:
                with open(safeUnicode(path[0]), 'wb') as f:
                    writer = csv.writer(f)
                    # 保存标签
                    VTTEXT = []
                    for CHN in self.headerDict.values():
                        VTTEXT.append(CHN['chinese'])
                    headers = [header.encode('gbk') for header in VTTEXT]
                    writer.writerow(headers)
                    # 保存每行内容
                    for row in range(self.rowCount()):
                        rowdata = []
                        for column in range(self.columnCount()):
                            item = self.item(row, column)
                            if item is not None:
                                rowdata.append(
                                    unicode(item.text()).encode('gbk'))
                            else:
                                rowdata.append('')
                        writer.writerow(rowdata)
        except IOError:
            print "IOError"

    #----------------------------------------------------------------------
    def initMenu(self):
        """初始化右键菜单"""
        self.menu = QtWidgets.QMenu(self)    
        
        resizeAction = QtWidgets.QAction(vtText.RESIZE_COLUMNS, self)
        resizeAction.triggered.connect(self.resizeColumns)        
        
        saveAction = QtWidgets.QAction(vtText.SAVE_DATA, self)
        saveAction.triggered.connect(self.saveToCsv)
        
        self.menu.addAction(resizeAction)
        self.menu.addAction(saveAction)
    #----------------------------------------------------------------------
    def contextMenuEvent(self, event):
        """右键点击事件"""
        self.menu.popup(QtGui.QCursor.pos())

########################################################################
class MarketMonitor(BasicMonitor):
    """市场监控组件"""

    #----------------------------------------------------------------------
    def __init__(self, mainEngine, eventEngine, parent=None):
        """Constructor"""
        super(MarketMonitor, self).__init__(mainEngine, eventEngine, parent)

        # 设置表头有序字典
        d = OrderedDict()
        d['time'] = {'chinese': vtText.TIME, 'cellType': BasicCell}
        d['symbol'] = {'chinese':vtText.CONTRACT_SYMBOL, 'cellType':BasicCell}
        d['vtSymbol'] = {'chinese':vtText.CONTRACT_NAME, 'cellType':NameCell}
        d['lastPrice'] = {'chinese':vtText.LAST_PRICE, 'cellType':BasicCell}
        d['preClosePrice'] = {'chinese':vtText.PRE_CLOSE_PRICE, 'cellType':BasicCell}
        d['volume'] = {'chinese':vtText.VOLUME, 'cellType':BasicCell}
        d['openInterest'] = {'chinese':vtText.OPEN_INTEREST, 'cellType':BasicCell}
        d['openPrice'] = {'chinese':vtText.OPEN_PRICE, 'cellType':BasicCell}
        d['highPrice'] = {'chinese':vtText.HIGH_PRICE, 'cellType':BasicCell}
        d['lowPrice'] = {'chinese':vtText.LOW_PRICE, 'cellType':BasicCell}
        d['bidPrice1'] = {'chinese':vtText.BID_PRICE_1, 'cellType':BidCell}
        d['bidVolume1'] = {'chinese':vtText.BID_VOLUME_1, 'cellType':BidCell}
        d['askPrice1'] = {'chinese':vtText.ASK_PRICE_1, 'cellType':AskCell}
        d['askVolume1'] = {'chinese':vtText.ASK_VOLUME_1, 'cellType':AskCell}
        d['gatewayName'] = {'chinese':vtText.GATEWAY, 'cellType':BasicCell}
        self.setHeaderDict(d)

        # 设置数据键
        self.setDataKey('vtSymbol')
        # 设置监控事件类型
        self.setEventType(EVENT_TICK)
        
        # 设置字体
        self.setFont(BASIC_FONT)
        
        # 设置排序
        self.setSorting(False)

        self.setSaveData(True)
        # 初始化表格
        self.initTable()
        
        # 注册事件监听
        self.registerEvent()

########################################################################
class LogMonitor(BasicMonitor):
    """日志监控"""

    #----------------------------------------------------------------------
    def __init__(self, mainEngine, eventEngine, parent=None):
        """Constructor"""
        super(LogMonitor, self).__init__(mainEngine, eventEngine, parent)
        
        d = OrderedDict()        
        d['logTime'] = {'chinese':vtText.TIME, 'cellType':BasicCell}
        d['logContent'] = {'chinese':vtText.CONTENT, 'cellType':BasicCell}
        d['gatewayName'] = {'chinese':vtText.GATEWAY, 'cellType':BasicCell}
        self.setHeaderDict(d)
        
        self.setEventType(EVENT_LOG)
        self.setFont(BASIC_FONT)        
        self.initTable()
        self.registerEvent()

    #----------------------------------------------------------------------
    def updateData(self, data):
        """"""
        super(LogMonitor, self).updateData(data)
        self.resizeRowToContents(0)                 # 调整行高


########################################################################
class ErrorMonitor(BasicMonitor):
    """错误监控"""

    #----------------------------------------------------------------------
    def __init__(self, mainEngine, eventEngine, parent=None):
        """Constructor"""
        super(ErrorMonitor, self).__init__(mainEngine, eventEngine, parent)
        
        d = OrderedDict()       
        d['errorTime']  = {'chinese':vtText.TIME, 'cellType':BasicCell}
        d['errorID'] = {'chinese':vtText.ERROR_CODE, 'cellType':BasicCell}
        d['errorMsg'] = {'chinese':vtText.ERROR_MESSAGE, 'cellType':BasicCell}
        d['gatewayName'] = {'chinese':vtText.GATEWAY, 'cellType':BasicCell}
        self.setHeaderDict(d)
        
        self.setEventType(EVENT_ERROR)
        self.setFont(BASIC_FONT)
        self.initTable()
        self.registerEvent()
########################################################################
class TradeMonitor(BasicTreeMonitor):
    """策略回合"""
    #----------------------------------------------------------------------
    def __init__(self, mainEngine, eventEngine, parent=None):
        """Constructor"""
        super(TradeMonitor, self).__init__(mainEngine, eventEngine, parent)
        
        d = OrderedDict()
        d['tradeTime'] = {'chinese': vtText.TRADE_TIME, 'cellType': BasicCell}      #成交时间
        d['symbol'] = {'chinese':vtText.CONTRACT_SYMBOL, 'cellType':BasicCell}      #合约代码
        #d['vtSymbol'] = {'chinese':vtText.CONTRACT_NAME, 'cellType':NameCell}      #交易所代码
        d['direction'] = {'chinese':vtText.DIRECTION, 'cellType':DirectionCell}     #成交方向
        d['offset'] = {'chinese':vtText.OFFSET, 'cellType':BasicCell}               #开平仓
        d['closeProfit'] = {'chinese': vtText.PROFIT_SIZE, 'cellType': BasicCell}  # 盈亏点/平仓盈亏
        d['status'] = {'chinese': vtText.ORDER_STATUS, 'cellType': OrderStatusCell}
        d['book_price'] = {'chinese':vtText.BOOK_PRICE, 'cellType':BasicCell}                 #开仓价格
        d['close_book_price'] = {'chinese': vtText.CLOSE_BOOK_PRICE, 'cellType': BasicCell}  # 平仓价格
        d['volume'] = {'chinese':vtText.VOLUME, 'cellType':BasicCell}
        d['tradeID'] = {'chinese': vtText.TRADE_ID, 'cellType': NumCell}            #成交编号
        #d['orderID'] = {'chinese': vtText.ORDER_ID, 'cellType': NumCell}  # 委托编号
        d['gatewayName'] = {'chinese': vtText.GATEWAY, 'cellType': BasicCell}        # 接口

        self.setHeaderDict(d)
        self.setFont(BASIC_FONT)
        self.initTable()
        self.registerEvent()
        self.orderPosition = {}
        self.closeYesterday = []
        self.dataEngine = DataEngine(eventEngine)
        self.orderPositionLong = {}
        self.orderPositionShort = {}
    def registerEvent(self):
        """注册GUI更新相关的事件监听"""
        self.signal.connect(self.updateOrderEvent)
        self.eventEngine.register(EVENT_ORDER, self.signal.emit)

        self.signalTrade.connect(self.updateOrderDict)
        self.signalTrade.connect(self.updateTradeEvent)

        self.eventEngine.register(EVENT_TRADE, self.signalTrade.emit)

    def updateTradeEvent(self, event):
        data = event.dict_['data']
        orderDict = {}
        orderDict['symbol'] = data.__getattribute__('symbol')
        orderDict['gatewayName'] = data.__getattribute__('exchange')
        orderDict['tradeTime'] = data.__getattribute__('tradeTime')
        orderDict['vtSymbol'] = data.__getattribute__('vtSymbol')
        orderDict['direction'] = data.__getattribute__('direction')
        orderDict['offset'] = data.__getattribute__('offset')
        orderDict['closeProfit'] = EMPTY_FLOAT
        orderDict['volume'] = data.__getattribute__('volume')
        orderDict['orderID'] = data.__getattribute__('orderID')
        orderDict['orderChildID'] = data.__getattribute__('orderID')
        orderDict['tradeID'] = data.__getattribute__('tradeID')
        orderDict['vtOrderID'] = data.__getattribute__('vtOrderID')
        orderDict['status'] = STATUS_ALLTRADED
        orderDict['level'] = 1
        orderDict['complete'] = False
        positionDetail = self.dataEngine.getPositionDetail(orderDict['vtSymbol'])
        # 今仓对冲
        volume = data.__getattribute__('volume')
        orderDict = self.unlockOrLockToday(orderDict, volume)
        #锁仓处理
        orderDict = self.unlockYesterday(orderDict,data.__getattribute__('vtSymbol'))

        if orderDict['offset'] is OFFSET_CLOSETODAY :
            orderDict['close_book_price'] = data.__getattribute__('price')
            orderDict['book_price'] = u'-'
        else:
            orderDict['book_price'] = data.__getattribute__('price')
            orderDict['close_book_price'] = u'-'

        if orderDict['offset'] is OFFSET_OPEN:
            orderDict['level'] = 0
            self.importData(orderDict)

        if orderDict['offset'] is OFFSET_CLOSETODAY:
            #平空或者平多
            if orderDict['direction'] is DIRECTION_LONG:
                self.orderPosition = self.orderPositionShort
            elif orderDict['direction'] is DIRECTION_SHORT:
                self.orderPosition = self.orderPositionLong
            size = self.getContract(data.__getattribute__('vtSymbol')).size
            if orderDict['symbol'] not in self.orderPosition.keys():
                pass
            orderIDPriceArray = self.orderPosition[orderDict['symbol']]
            #pop orderIDPrice最后一个字典[orderID : orderPrice]
            v = orderDict['volume']
            if positionDetail.__getattribute__('shortNetPos') and data.__getattribute__('offset') is OFFSET_CLOSEYESTERDAY:
                if positionDetail.__getattribute__('shortNetPos') < orderDict['volume']:
                    v = positionDetail.__getattribute__('shortNetPos')
                    orderDict['offset'] = OFFSET_OPEN
                    orderDict['level'] = 0
                    orderDict['volume'] = orderDict['volume'] - positionDetail.__getattribute__('shortNetPos')
                    self.importData(orderDict)
                    orderDict['offset'] = OFFSET_CLOSETODAY
                    orderDict['level'] = 1
            elif positionDetail.__getattribute__('longNetPos') and data.__getattribute__('offset') is OFFSET_CLOSEYESTERDAY:
                if positionDetail.__getattribute__('longNetPos') < orderDict['volume']:
                    v = positionDetail.__getattribute__('longNetPos')
                    orderDict['offset'] = OFFSET_OPEN
                    orderDict['level'] = 0
                    orderDict['volume'] = orderDict['volume'] - positionDetail.__getattribute__('shortNetPos')
                    self.importData(orderDict)
                    orderDict['offset'] = OFFSET_CLOSETODAY
                    orderDict['level'] = 1

            k = EMPTY_INT
            orderDict['orderID'] = orderIDPriceArray[-1].keys()[0]
            #平仓逻辑while循环平仓
            while v is not 0:
                orderIDDict = orderIDPriceArray.pop()
                #如果当前仓位已经平完，则进行下一仓位减仓
                if orderDict['orderID'] is not orderIDDict.keys()[0]:
                    orderDict['volume'] = k
                    k = EMPTY_INT

                    orderDict['complete'] = True
                    self.importData(orderDict)
                    orderDict['complete'] = False
                    # 将pop删除掉的补回去，进行下一个子仓位的减仓
                    orderIDPriceArray.append(orderIDDict)
                    orderDict['orderID'] = orderIDDict.keys()[0]
                    orderDict['orderChildID'] = orderIDDict.keys()[0]
                    orderDict['volume'] = v
                    continue
                v = v - 1
                k = k + 1

                self.orderPosition[orderDict['symbol']] = orderIDPriceArray
                #所有仓位了结
                if len(self.orderPosition[orderDict['symbol']]) is EMPTY_INT:
                    if orderDict['direction'] is DIRECTION_LONG:
                        del self.orderPositionShort[orderDict['symbol']]
                    elif orderDict['direction'] is DIRECTION_SHORT:
                        del self.orderPositionLong[orderDict['symbol']]
                    orderDict['complete'] = True
                # 当前子仓位已经了结
                else:
                    if orderDict['orderID'] is not orderIDPriceArray[-1].keys()[0]:
                        orderDict['complete'] = True

                # 计算盈亏
                if orderDict['direction'] is DIRECTION_LONG:
                    orderDict['closeProfit'] = k * (orderIDDict[orderDict['orderID']] - orderDict['close_book_price']) * size
                elif orderDict['direction'] is DIRECTION_SHORT:
                    orderDict['closeProfit'] = k * (orderDict['close_book_price'] - orderIDDict[orderDict['orderID']]) * size

                self.importData(orderDict)
                orderDict['complete'] = False

    #构造策略回合所需的symbol - orderID - Price字典
    def updateOrderDict(self,event):
        data = event.dict_['data']
        orderDict = {}
        orderDict['offset'] = data.__getattribute__('offset')
        orderDict['direction'] = data.__getattribute__('direction')
        orderDict['volume'] = data.__getattribute__('volume')
        orderDict['price'] = data.__getattribute__('price')
        orderDict['orderID'] = data.__getattribute__('orderID')
        orderDict['symbol'] = data.__getattribute__('symbol')
        orderDict['status'] = STATUS_ALLTRADED
        # 今仓对冲
        volume = data.__getattribute__('volume')
        orderDict = self.unlockOrLockToday(orderDict, volume)
        # 锁仓处理
        orderDict = self.unlockYesterday(orderDict,data.__getattribute__('vtSymbol'))

        if orderDict['offset'] is OFFSET_OPEN:
            orderIDPrice = []
            v = orderDict['volume']
            while v is not 0:
                d = {}
                d[orderDict['orderID']] = orderDict['price']
                orderIDPrice.append(d)
                v = v - 1
            if orderDict['direction'] is DIRECTION_LONG and orderDict['symbol'] in self.orderPositionLong.keys():
                orderIDPrice = self.orderPositionLong[orderDict['symbol']] + orderIDPrice
                self.orderPositionLong[orderDict['symbol']] = orderIDPrice
            elif orderDict['direction'] is DIRECTION_SHORT and orderDict['symbol'] in self.orderPositionShort.keys():
                orderIDPrice = self.orderPositionShort[orderDict['symbol'] ] + orderIDPrice
                self.orderPositionShort[orderDict['symbol']] = orderIDPrice
            else:
                if orderDict['direction'] is DIRECTION_LONG:
                    self.orderPositionLong[orderDict['symbol'] ] = orderIDPrice
                elif orderDict['direction'] is DIRECTION_SHORT:
                    self.orderPositionShort[orderDict['symbol']] = orderIDPrice
########################################################################
    def updateOrderEvent(self, event):
        """收到事件更新"""
        data = event.dict_['data']
        orderDict = {}
        orderDict['symbol'] = data.__getattribute__('symbol')
        orderDict['gatewayName'] = data.__getattribute__('exchange')
        orderDict['tradeTime'] = data.__getattribute__('orderTime')
        #orderDict['vtSymbol'] = data.__getattribute__('vtSymbol')
        orderDict['direction'] = data.__getattribute__('direction')
        orderDict['offset'] = data.__getattribute__('offset')
        orderDict['closeProfit'] = EMPTY_FLOAT
        orderDict['volume'] = EMPTY_INT
        orderDict['orderID'] = data.__getattribute__('orderID')
        orderDict['orderChildID'] = data.__getattribute__('orderID')
        orderDict['tradeID'] = data.__getattribute__('orderID')
        orderDict['vtOrderID'] = data.__getattribute__('vtOrderID')
        orderDict['status'] = data.__getattribute__('status')
        orderDict['level'] = EMPTY_INT
        orderDict['complete'] = False
        # 今仓对冲
        volume = EMPTY_INT
        orderDict = self.unlockOrLockToday(orderDict, volume)
        # 锁仓处理
        orderDict = self.unlockYesterday(orderDict,data.__getattribute__('vtSymbol'))

        if orderDict['offset'] is not OFFSET_OPEN:
            orderDict['book_price'] = u'-'
            orderDict['close_book_price'] = data.__getattribute__('price')
        else:
            orderDict['book_price'] = data.__getattribute__('price')
            orderDict['close_book_price'] = u'-'

        # 拒单或者未知，直接隐藏
        if orderDict['status'] is STATUS_REJECTED or orderDict['status'] is STATUS_UNKNOWN:
            pass
        else:
            # 平空
            if orderDict['direction'] is DIRECTION_LONG:
                self.orderPosition = self.orderPositionShort
            # 平多
            elif orderDict['direction'] is DIRECTION_SHORT:
                self.orderPosition = self.orderPositionLong
            #将平仓委托，插入到历史的开仓parent中，并不改变symbol - orderID - Price字典
            if orderDict['offset'] is OFFSET_CLOSETODAY and orderDict['symbol'] in self.orderPosition.keys():
                orderIDPrice = self.orderPosition[orderDict['symbol']]
                orderID = orderIDPrice[-1].keys()[0]
                orderDict['orderID'] = orderID
                orderDict['tradeID'] = orderID
                orderDict['level'] = 1
            if orderDict['symbol'] not in self.orderPosition.keys():
                orderDict['level'] = 0

            self.importData(orderDict)
    def unlockOrLockToday(self, orderDict, volume):
        if orderDict['symbol'] in self.orderPositionLong.keys():
            longPositionSize = len(self.orderPositionLong[orderDict['symbol']])
        else:
            longPositionSize = 0

        if orderDict['symbol'] in self.orderPositionShort.keys():
            shortPositionSize = len(self.orderPositionShort[orderDict['symbol']])
        else:
            shortPositionSize = 0
        if orderDict['offset'] is OFFSET_OPEN and orderDict['direction'] is DIRECTION_LONG:
            if shortPositionSize - volume >= longPositionSize and volume is not 0:
                orderDict['offset'] = OFFSET_CLOSETODAY
                return orderDict
        if orderDict['offset'] is OFFSET_OPEN and orderDict['direction'] is DIRECTION_SHORT:
            if longPositionSize - volume >= shortPositionSize and volume is not 0:
                orderDict['offset'] = OFFSET_CLOSETODAY
                return orderDict
        if orderDict['offset'] is OFFSET_CLOSETODAY and orderDict['direction'] is DIRECTION_LONG:
            if longPositionSize + volume > shortPositionSize:
                orderDict['offset'] = OFFSET_OPEN
                return orderDict
        if orderDict['offset'] is OFFSET_CLOSETODAY and orderDict['direction'] is DIRECTION_SHORT:
            if shortPositionSize + volume > longPositionSize:
                orderDict['offset'] = OFFSET_OPEN
                return orderDict
        return orderDict
    def unlockYesterday(self, orderDict, vtSymbol):
        positionDetail = self.dataEngine.getPositionDetail(vtSymbol)
        if orderDict['offset'] is OFFSET_CLOSEYESTERDAY:
            if positionDetail.__getattribute__('longNetPos') is EMPTY_INT and positionDetail.__getattribute__('shortNetPos') is EMPTY_INT:
                orderDict['offset'] = OFFSET_OPEN
                orderDict['level'] = 0

            if orderDict['orderID'] in self.closeYesterday:
                orderDict['level'] = 1
                orderDict['offset'] = OFFSET_CLOSETODAY
                return orderDict

            if positionDetail.__getattribute__('longNetPos'):
                if orderDict['direction'] is DIRECTION_LONG:
                    orderDict['offset'] = OFFSET_OPEN
                    orderDict['level'] = 0
                elif orderDict['direction'] is DIRECTION_SHORT:
                    orderDict['offset'] = OFFSET_CLOSETODAY
                    self.closeYesterday.append(orderDict['orderID'])

            if positionDetail.__getattribute__('shortNetPos'):
                if orderDict['direction'] is DIRECTION_LONG:
                    orderDict['offset'] = OFFSET_CLOSETODAY
                    self.closeYesterday.append(orderDict['orderID'])
                elif orderDict['direction'] is DIRECTION_SHORT:
                    orderDict['offset'] = OFFSET_OPEN
                    orderDict['level'] = 0

        return orderDict
########################################################################
class OrderMonitor(BasicMonitor):
    """委托监控"""
    #----------------------------------------------------------------------
    def __init__(self, mainEngine, eventEngine, parent=None):
        """Constructor"""
        super(OrderMonitor, self).__init__(mainEngine, eventEngine, parent)
        self.mainEngine = mainEngine
        d = OrderedDict()
        d['orderTime'] = {'chinese': vtText.ORDER_TIME, 'cellType': BasicCell}
        d['symbol'] = {'chinese':vtText.CONTRACT_SYMBOL, 'cellType':BasicCell}
        d['vtSymbol'] = {'chinese':vtText.CONTRACT_NAME, 'cellType':NameCell}
        d['direction'] = {'chinese':vtText.DIRECTION, 'cellType':DirectionCell}
        d['offset'] = {'chinese':vtText.OFFSET, 'cellType':BasicCell}
        d['price'] = {'chinese':vtText.PRICE, 'cellType':BasicCell}
        d['totalVolume'] = {'chinese':vtText.ORDER_VOLUME, 'cellType':BasicCell}
        d['tradedVolume'] = {'chinese':vtText.TRADED_VOLUME, 'cellType':BasicCell}
        d['status'] = {'chinese':vtText.ORDER_STATUS, 'cellType':OrderStatusCell}
        #d['cancelTime'] = {'chinese':vtText.CANCEL_TIME, 'cellType':BasicCell}
        d['orderID'] = {'chinese': vtText.ORDER_ID, 'cellType': NumCell}
        #d['frontID'] = {'chinese':vtText.FRONT_ID, 'cellType':BasicCell}         # 考虑到在vn.trader中，ctpGateway的报单号应该是始终递增的，因此这里可以忽略
        #d['sessionID'] = {'chinese':vtText.SESSION_ID, 'cellType':BasicCell}
        d['gatewayName'] = {'chinese':vtText.GATEWAY, 'cellType':BasicCell}
        self.setHeaderDict(d)
        
        self.setDataKey('vtOrderID')
        self.setEventType(EVENT_ORDER)
        self.setFont(BASIC_FONT)
        self.setSaveData(True)
        self.setSorting(True)
        
        self.initTable()
        self.registerEvent()
        self.connectSignal()

    def saveToCsv(self):
        now = int(time.time())
        timeStruct = time.localtime(now)
        strTime = time.strftime("%Y%m%d", timeStruct)
        saveDir = "D:\VNPY\交易记录\/" + strTime + "\/"
        if os.path.exists(safeUnicode(saveDir)) is False:
            os.makedirs(safeUnicode(saveDir))
        self.fileNameToSave = "D:\VNPY\交易记录\/" + strTime + "\/" + vtText.ORDER + "_" + strTime
        super(OrderMonitor, self).saveToCsv()
    #----------------------------------------------------------------------
    def connectSignal(self):
        """连接信号"""
        # 双击单元格撤单
        self.itemDoubleClicked.connect(self.cancelOrder) 
    
    #----------------------------------------------------------------------
    def cancelOrder(self, cell):
        """根据单元格的数据撤单"""
        order = cell.data
        
        req = VtCancelOrderReq()
        req.symbol = order.symbol
        req.exchange = order.exchange
        req.frontID = order.frontID
        req.sessionID = order.sessionID
        req.orderID = order.orderID
        self.mainEngine.cancelOrder(req, order.gatewayName)
        
########################################################################
class AccountMonitor(BasicMonitor):
    """账户监控"""

    #----------------------------------------------------------------------
    def __init__(self, mainEngine, eventEngine, parent=None):
        """Constructor"""
        super(AccountMonitor, self).__init__(mainEngine, eventEngine, parent)
        d = OrderedDict()
        d['totalProfit'] = {'chinese': vtText.TOTAL_PROFIT, 'cellType': ProfitCell}
        d['preBalance'] = {'chinese':vtText.PRE_BALANCE, 'cellType':BasicCell}
        d['balance'] = {'chinese':vtText.BALANCE, 'cellType':BasicCell}
        d['available'] = {'chinese':vtText.AVAILABLE, 'cellType':BasicCell}
        d['commission'] = {'chinese':vtText.COMMISSION, 'cellType':BasicCell}
        d['margin'] = {'chinese':vtText.MARGIN, 'cellType':BasicCell}
        d['closeProfit'] = {'chinese':vtText.CLOSE_PROFIT, 'cellType':PnlCell}
        d['positionProfit'] = {'chinese':vtText.POSITION_PROFIT, 'cellType':PnlCell}
        d['accountID'] = {'chinese': vtText.ACCOUNT_ID, 'cellType': BasicCell}
        d['gatewayName'] = {'chinese':vtText.GATEWAY, 'cellType':BasicCell}
        self.setHeaderDict(d)
        self.setDataKey('vtAccountID')
        self.setEventType(EVENT_ACCOUNT)
        self.setFont(BASIC_FONT)
        self.initTable()

        self.registerEvent()
    def saveToCsv(self):
        now = int(time.time())
        timeStruct = time.localtime(now)
        strTime = time.strftime("%Y%m%d", timeStruct)
        saveDir = "D:\VNPY\交易记录\/" + strTime + "\/"
        if os.path.exists(safeUnicode(saveDir)) is False:
            os.makedirs(safeUnicode(saveDir))
        self.fileNameToSave = "D:\VNPY\交易记录\/" + strTime + "\/" + vtText.ACCOUNT + "_" + strTime
        super(AccountMonitor, self).saveToCsv()
########################################################################
class TradingWidget(QtWidgets.QFrame):
    """简单交易组件"""
    signal = QtCore.Signal(type(Event()))
    
    directionList = [DIRECTION_LONG,
                     DIRECTION_SHORT]

    offsetList = [OFFSET_OPEN,
                  OFFSET_CLOSE,
                  OFFSET_CLOSEYESTERDAY,
                  OFFSET_CLOSETODAY]
    
    priceTypeList = [PRICETYPE_LIMITPRICE,
                     PRICETYPE_MARKETPRICE,
                     PRICETYPE_FAK,
                     PRICETYPE_FOK]
    
    exchangeList = [EXCHANGE_NONE,
                    EXCHANGE_CFFEX,
                    EXCHANGE_SHFE,
                    EXCHANGE_DCE,
                    EXCHANGE_CZCE,
                    EXCHANGE_SSE,
                    EXCHANGE_SZSE,
                    EXCHANGE_SGE,
                    EXCHANGE_HKEX,
                    EXCHANGE_HKFE,
                    EXCHANGE_SMART,
                    EXCHANGE_ICE,
                    EXCHANGE_CME,
                    EXCHANGE_NYMEX,
                    EXCHANGE_LME,
                    EXCHANGE_GLOBEX,
                    EXCHANGE_IDEALPRO]
    
    currencyList = [CURRENCY_NONE,
                    CURRENCY_CNY,
                    CURRENCY_HKD,
                    CURRENCY_USD]
    
    productClassList = [PRODUCT_NONE,
                        PRODUCT_EQUITY,
                        PRODUCT_FUTURES,
                        PRODUCT_OPTION,
                        PRODUCT_FOREX]
    
    gatewayList = ['']

    #----------------------------------------------------------------------
    def __init__(self, mainEngine, eventEngine, parent=None):
        """Constructor"""
        super(TradingWidget, self).__init__(parent)
        self.mainEngine = mainEngine
        self.eventEngine = eventEngine
        
        self.symbol = ''
        
        # 添加交易接口
        l = mainEngine.getAllGatewayDetails()
        gatewayNameList = [d['gatewayName'] for d in l]
        self.gatewayList.extend(gatewayNameList)

        self.initUi()
        self.connectSignal()
    #----------------------------------------------------------------------
    def initUi(self):
        """初始化界面"""
        self.setWindowTitle(vtText.TRADING)
        #self.setMaximumWidth(330)
        #self.setMaximumHeight(300)
        #self.setEnabled(True)
        self.setFrameShape(self.Box)    # 设置边框
        self.setLineWidth(1)

        # 左边部分
        labelSymbol = QtWidgets.QLabel(vtText.CONTRACT_SYMBOL)
        labelName =  QtWidgets.QLabel(vtText.CONTRACT_NAME)
        labelDirection = QtWidgets.QLabel(vtText.DIRECTION)
        labelOffset = QtWidgets.QLabel(vtText.OFFSET)
        labelPrice = QtWidgets.QLabel(vtText.PRICE)
        self.checkFixed = QtWidgets.QCheckBox(u'')  # 价格固定选择框
        labelVolume = QtWidgets.QLabel(vtText.VOLUME)
        labelVolume.setVisible(False)
        labelPriceType = QtWidgets.QLabel(vtText.PRICE_TYPE)
        labelPriceType.setVisible(False)
        labelExchange = QtWidgets.QLabel(vtText.EXCHANGE)
        labelExchange.setVisible(False)
        labelCurrency = QtWidgets.QLabel(vtText.CURRENCY)
        labelCurrency.setVisible(False)
        labelProductClass = QtWidgets.QLabel(vtText.PRODUCT_CLASS)
        labelProductClass.setVisible(False)
        labelGateway = QtWidgets.QLabel(vtText.GATEWAY)
        labelGateway.setVisible(False)

        self.lineSymbol = QtWidgets.QLineEdit()
        self.lineName = QtWidgets.QLineEdit()

        self.comboDirection = QtWidgets.QComboBox()
        self.comboDirection.addItems(self.directionList)

        self.comboOffset = QtWidgets.QComboBox()
        self.comboOffset.addItems(self.offsetList)

        self.spinPrice = QtWidgets.QDoubleSpinBox()
        self.spinPrice.setDecimals(4)
        self.spinPrice.setMinimum(0)
        self.spinPrice.setMaximum(100000)

        self.spinVolume = QtWidgets.QSpinBox()
        self.spinVolume.setVisible(False)
        self.spinVolume.setMinimum(0)
        self.spinVolume.setMaximum(1000000)

        self.comboPriceType = QtWidgets.QComboBox()
        self.comboPriceType.setVisible(False)
        self.comboPriceType.addItems(self.priceTypeList)
        
        self.comboExchange = QtWidgets.QComboBox()
        self.comboExchange.setVisible(False)
        self.comboExchange.addItems(self.exchangeList)      
        
        self.comboCurrency = QtWidgets.QComboBox()
        self.comboCurrency.setVisible(False)
        self.comboCurrency.addItems(self.currencyList)
        
        self.comboProductClass = QtWidgets.QComboBox()
        self.comboProductClass.setVisible(False)
        self.comboProductClass.addItems(self.productClassList)     
        
        self.comboGateway = QtWidgets.QComboBox()
        self.comboGateway.setVisible(False)
        self.comboGateway.addItems(self.gatewayList)          

        gridleft = QtWidgets.QGridLayout()
        gridleft.addWidget(labelSymbol, 0, 0)
        gridleft.addWidget(labelName, 1, 0)
        gridleft.addWidget(labelDirection, 2, 0)
        gridleft.addWidget(labelOffset, 3, 0)
        gridleft.addWidget(labelPrice, 4, 0)
        gridleft.addWidget(labelVolume, 5, 0)
        gridleft.addWidget(labelPriceType, 6, 0)
        gridleft.addWidget(labelExchange, 7, 0)
        gridleft.addWidget(labelCurrency, 8, 0)
        gridleft.addWidget(labelProductClass, 9, 0)   
        gridleft.addWidget(labelGateway, 10, 0)
        
        gridleft.addWidget(self.lineSymbol, 0, 1, 1, -1)
        gridleft.addWidget(self.lineName, 1, 1, 1, -1)
        gridleft.addWidget(self.comboDirection, 2, 1, 1, -1)
        gridleft.addWidget(self.comboOffset, 3, 1, 1, -1)
        gridleft.addWidget(self.checkFixed, 4, 1)
        gridleft.addWidget(self.spinPrice, 4, 2)
        gridleft.addWidget(self.spinVolume, 5, 1, 1, -1)
        gridleft.addWidget(self.comboPriceType, 6, 1, 1, -1)
        gridleft.addWidget(self.comboExchange, 7, 1, 1, -1)
        gridleft.addWidget(self.comboCurrency, 8, 1, 1, -1)
        gridleft.addWidget(self.comboProductClass, 9, 1, 1, -1)
        gridleft.addWidget(self.comboGateway, 10, 1, 1, -1)

        # 右边部分
        labelBid1 = QtWidgets.QLabel(vtText.BID_1)
        labelBid1.setVisible(False)
        labelBid2 = QtWidgets.QLabel(vtText.BID_2)
        labelBid2.setVisible(False)
        labelBid3 = QtWidgets.QLabel(vtText.BID_3)
        labelBid3.setVisible(False)
        labelBid4 = QtWidgets.QLabel(vtText.BID_4)
        labelBid4.setVisible(False)
        labelBid5 = QtWidgets.QLabel(vtText.BID_5)
        labelBid5.setVisible(False)

        labelAsk1 = QtWidgets.QLabel(vtText.ASK_1)
        labelAsk1.setVisible(False)
        labelAsk2 = QtWidgets.QLabel(vtText.ASK_2)
        labelAsk2.setVisible(False)
        labelAsk3 = QtWidgets.QLabel(vtText.ASK_3)
        labelAsk3.setVisible(False)
        labelAsk4 = QtWidgets.QLabel(vtText.ASK_4)
        labelAsk4.setVisible(False)
        labelAsk5 = QtWidgets.QLabel(vtText.ASK_5)
        labelAsk5.setVisible(False)


        self.labelBidPrice1 = QtWidgets.QLabel()
        self.labelBidPrice1.setVisible(False)
        self.labelBidPrice2 = QtWidgets.QLabel()
        self.labelBidPrice2.setVisible(False)
        self.labelBidPrice3 = QtWidgets.QLabel()
        self.labelBidPrice3.setVisible(False)
        self.labelBidPrice4 = QtWidgets.QLabel()
        self.labelBidPrice4.setVisible(False)
        self.labelBidPrice5 = QtWidgets.QLabel()
        self.labelBidPrice5.setVisible(False)
        self.labelBidVolume1 = QtWidgets.QLabel()
        self.labelBidVolume1.setVisible(False)
        self.labelBidVolume2 = QtWidgets.QLabel()
        self.labelBidVolume2.setVisible(False)
        self.labelBidVolume3 = QtWidgets.QLabel()
        self.labelBidVolume3.setVisible(False)
        self.labelBidVolume4 = QtWidgets.QLabel()
        self.labelBidVolume4.setVisible(False)
        self.labelBidVolume5 = QtWidgets.QLabel()
        self.labelBidVolume5.setVisible(False)

        self.labelAskPrice1 = QtWidgets.QLabel()
        self.labelAskPrice1.setVisible(False)
        self.labelAskPrice2 = QtWidgets.QLabel()
        self.labelAskPrice2.setVisible(False)
        self.labelAskPrice3 = QtWidgets.QLabel()
        self.labelAskPrice3.setVisible(False)
        self.labelAskPrice4 = QtWidgets.QLabel()
        self.labelAskPrice4.setVisible(False)
        self.labelAskPrice5 = QtWidgets.QLabel()
        self.labelAskPrice5.setVisible(False)
        self.labelAskVolume1 = QtWidgets.QLabel()
        self.labelAskVolume1.setVisible(False)
        self.labelAskVolume2 = QtWidgets.QLabel()
        self.labelAskVolume2.setVisible(False)
        self.labelAskVolume3 = QtWidgets.QLabel()
        self.labelAskVolume3.setVisible(False)
        self.labelAskVolume4 = QtWidgets.QLabel()
        self.labelAskVolume4.setVisible(False)
        self.labelAskVolume5 = QtWidgets.QLabel()
        self.labelAskVolume5.setVisible(False)

        labelLast = QtWidgets.QLabel(vtText.LAST)
        self.labelLastPrice = QtWidgets.QLabel()
        self.labelReturn = QtWidgets.QLabel()

        self.labelLastPrice.setMinimumWidth(60)
        self.labelReturn.setMinimumWidth(60)

        gridRight = QtWidgets.QGridLayout()
        gridRight.addWidget(labelAsk5, 0, 0)
        gridRight.addWidget(labelAsk4, 1, 0)
        gridRight.addWidget(labelAsk3, 2, 0)
        gridRight.addWidget(labelAsk2, 3, 0)
        gridRight.addWidget(labelAsk1, 4, 0)
        gridRight.addWidget(labelLast, 5, 0)
        gridRight.addWidget(labelBid1, 6, 0)
        gridRight.addWidget(labelBid2, 7, 0)
        gridRight.addWidget(labelBid3, 8, 0)
        gridRight.addWidget(labelBid4, 9, 0)
        gridRight.addWidget(labelBid5, 10, 0)

        gridRight.addWidget(self.labelAskPrice5, 0, 1)
        gridRight.addWidget(self.labelAskPrice4, 1, 1)
        gridRight.addWidget(self.labelAskPrice3, 2, 1)
        gridRight.addWidget(self.labelAskPrice2, 3, 1)
        gridRight.addWidget(self.labelAskPrice1, 4, 1)
        gridRight.addWidget(self.labelLastPrice, 5, 1)
        gridRight.addWidget(self.labelBidPrice1, 6, 1)
        gridRight.addWidget(self.labelBidPrice2, 7, 1)
        gridRight.addWidget(self.labelBidPrice3, 8, 1)
        gridRight.addWidget(self.labelBidPrice4, 9, 1)
        gridRight.addWidget(self.labelBidPrice5, 10, 1)	

        gridRight.addWidget(self.labelAskVolume5, 0, 2)
        gridRight.addWidget(self.labelAskVolume4, 1, 2)
        gridRight.addWidget(self.labelAskVolume3, 2, 2)
        gridRight.addWidget(self.labelAskVolume2, 3, 2)
        gridRight.addWidget(self.labelAskVolume1, 4, 2)
        gridRight.addWidget(self.labelReturn, 5, 2)
        gridRight.addWidget(self.labelBidVolume1, 6, 2)
        gridRight.addWidget(self.labelBidVolume2, 7, 2)
        gridRight.addWidget(self.labelBidVolume3, 8, 2)
        gridRight.addWidget(self.labelBidVolume4, 9, 2)
        gridRight.addWidget(self.labelBidVolume5, 10, 2)

        # 发单按钮
        buttonSendOrder = QtWidgets.QPushButton(vtText.SEND_ORDER)
        buttonSendOrder.setVisible(False)
        buttonCancelAll = QtWidgets.QPushButton(vtText.CANCEL_ALL)
        buttonCancelAll.setVisible(False)


        size = buttonSendOrder.sizeHint()
        buttonSendOrder.setMinimumHeight(size.height()*2)   # 把按钮高度设为默认两倍
        buttonCancelAll.setMinimumHeight(size.height()*2)

        # 整合布局
        hbox = QtWidgets.QHBoxLayout()
        hbox.addLayout(gridleft)
        hbox.addLayout(gridRight)

        vbox = QtWidgets.QVBoxLayout()
        vbox.addLayout(hbox)
        vbox.addWidget(buttonSendOrder)
        vbox.addWidget(buttonCancelAll)
        vbox.addStretch()

        self.setLayout(vbox)

        # 关联更新
        buttonSendOrder.clicked.connect(self.sendOrder)
        buttonCancelAll.clicked.connect(self.cancelAll)
        self.lineSymbol.returnPressed.connect(self.updateSymbol)
        #.add_hotkey('F1',self.sendOrder)

    #----------------------------------------------------------------------
    def updateSymbol(self):
        """合约变化"""
        # 读取组件数据
        symbol = str(self.lineSymbol.text())
        exchange = unicode(self.comboExchange.currentText())
        currency = unicode(self.comboCurrency.currentText())
        productClass = unicode(self.comboProductClass.currentText())           
        gatewayName = unicode(self.comboGateway.currentText())
        
        # 查询合约
        if exchange:
            vtSymbol = '.'.join([symbol, exchange])
            contract = self.mainEngine.getContract(vtSymbol)
        else:
            vtSymbol = symbol
            contract = self.mainEngine.getContract(symbol)   
        
        if contract:
            vtSymbol = contract.vtSymbol
            gatewayName = contract.gatewayName
            self.lineName.setText(contract.name)
            exchange = contract.exchange    # 保证有交易所代码
            
        # 清空价格数量
        self.spinPrice.setValue(0)
        self.spinVolume.setValue(0)

        # 清空行情显示
        self.labelBidPrice1.setText('')
        self.labelBidPrice2.setText('')
        self.labelBidPrice3.setText('')
        self.labelBidPrice4.setText('')
        self.labelBidPrice5.setText('')
        self.labelBidVolume1.setText('')
        self.labelBidVolume2.setText('')
        self.labelBidVolume3.setText('')
        self.labelBidVolume4.setText('')
        self.labelBidVolume5.setText('')	
        self.labelAskPrice1.setText('')
        self.labelAskPrice2.setText('')
        self.labelAskPrice3.setText('')
        self.labelAskPrice4.setText('')
        self.labelAskPrice5.setText('')
        self.labelAskVolume1.setText('')
        self.labelAskVolume2.setText('')
        self.labelAskVolume3.setText('')
        self.labelAskVolume4.setText('')
        self.labelAskVolume5.setText('')
        self.labelLastPrice.setText('')
        self.labelReturn.setText('')

        # 重新注册事件监听
        self.eventEngine.unregister(EVENT_TICK + self.symbol, self.signal.emit)
        self.eventEngine.register(EVENT_TICK + vtSymbol, self.signal.emit)

        # 订阅合约
        req = VtSubscribeReq()
        req.symbol = symbol
        req.exchange = exchange
        req.currency = currency
        req.productClass = productClass

        # 默认跟随价
        self.checkFixed.setChecked(False)
        self.mainEngine.subscribe(req, gatewayName)

        # 更新组件当前交易的合约
        self.symbol = vtSymbol

    #----------------------------------------------------------------------
    def updateTick(self, event):
        """更新行情"""
        tick = event.dict_['data']
        if tick.vtSymbol == self.symbol:
            if not self.checkFixed.isChecked():
                self.spinPrice.setValue(tick.lastPrice)
            self.labelBidPrice1.setText(str(tick.bidPrice1))
            self.labelAskPrice1.setText(str(tick.askPrice1))
            self.labelBidVolume1.setText(str(tick.bidVolume1))
            self.labelAskVolume1.setText(str(tick.askVolume1))

            if tick.bidPrice2:
                self.labelBidPrice2.setText(str(tick.bidPrice2))
                self.labelBidPrice3.setText(str(tick.bidPrice3))
                self.labelBidPrice4.setText(str(tick.bidPrice4))
                self.labelBidPrice5.setText(str(tick.bidPrice5))
    
                self.labelAskPrice2.setText(str(tick.askPrice2))
                self.labelAskPrice3.setText(str(tick.askPrice3))
                self.labelAskPrice4.setText(str(tick.askPrice4))
                self.labelAskPrice5.setText(str(tick.askPrice5))
    
                self.labelBidVolume2.setText(str(tick.bidVolume2))
                self.labelBidVolume3.setText(str(tick.bidVolume3))
                self.labelBidVolume4.setText(str(tick.bidVolume4))
                self.labelBidVolume5.setText(str(tick.bidVolume5))
                
                self.labelAskVolume2.setText(str(tick.askVolume2))
                self.labelAskVolume3.setText(str(tick.askVolume3))
                self.labelAskVolume4.setText(str(tick.askVolume4))
                self.labelAskVolume5.setText(str(tick.askVolume5))	

            self.labelLastPrice.setText(str(tick.lastPrice))
            
            if tick.preClosePrice:
                rt = (tick.lastPrice/tick.preClosePrice)-1
                self.labelReturn.setText(('%.2f' %(rt*100))+'%')
            else:
                self.labelReturn.setText('')
    #----------------------------------------------------------------------
    def connectSignal(self):
        """连接Signal"""
        self.signal.connect(self.updateTick)

    #----------------------------------------------------------------------
    def sendOrder(self):
        """发单"""
        symbol = str(self.lineSymbol.text())
        exchange = unicode(self.comboExchange.currentText())
        currency = unicode(self.comboCurrency.currentText())
        productClass = unicode(self.comboProductClass.currentText())           
        gatewayName = unicode(self.comboGateway.currentText())        

        # 查询合约
        if exchange:
            vtSymbol = '.'.join([symbol, exchange])
            contract = self.mainEngine.getContract(vtSymbol)
        else:
            vtSymbol = symbol
            contract = self.mainEngine.getContract(symbol)
        if contract:
            gatewayName = contract.gatewayName
            exchange = contract.exchange    # 保证有交易所代码
            
        req = VtOrderReq()
        req.symbol = symbol
        req.exchange = exchange
        req.vtSymbol = contract.vtSymbol
        req.price = self.spinPrice.value()
        req.volume = self.spinVolume.value()
        req.direction = unicode(self.comboDirection.currentText())
        req.priceType = unicode(self.comboPriceType.currentText())
        req.offset = unicode(self.comboOffset.currentText())
        req.currency = currency
        req.productClass = productClass

        self.mainEngine.sendOrder(req, gatewayName)


    #----------------------------------------------------------------------
    def cancelAll(self):
        """一键撤销所有委托"""
        l = self.mainEngine.getAllWorkingOrders()
        for order in l:
            req = VtCancelOrderReq()
            req.symbol = order.symbol
            req.exchange = order.exchange
            req.frontID = order.frontID
            req.sessionID = order.sessionID
            req.orderID = order.orderID
            self.mainEngine.cancelOrder(req, order.gatewayName)
            
    #----------------------------------------------------------------------
    def closePosition(self, cell):
        """根据持仓信息自动填写交易组件"""
        # 读取持仓数据，cell是一个表格中的单元格对象
        pos = cell.data
        if type(pos) is dict:
            symbol = pos['symbol']
        else:
            symbol = safeUnicode(pos.__getattribute__('symbol'))

        # 更新交易组件的显示合约
        self.lineSymbol.setText(symbol)
        self.updateSymbol()

        # 价格留待更新后由用户输入，防止有误操作
class BasicGraph(QtWidgets.QWidget):
    """
    基础监控

    headerDict中的值对应的字典格式如下
    {'chinese': u'中文名', 'cellType': BasicCell}

    """
    STATUS_COMPLETED = [STATUS_ALLTRADED, STATUS_CANCELLED, STATUS_REJECTED]
    WORKING_STATUS = [STATUS_NOTTRADED, STATUS_PARTTRADED]
    signal = QtCore.Signal(type(Event()))
    # ----------------------------------------------------------------------
    def __init__(self, mainEngine=None, eventEngine=None, parent=None):
        """Constructor"""
        super(BasicGraph, self).__init__(parent)

        self.mainEngine = mainEngine
        self.eventEngine = eventEngine
        # 监控的事件类型
        self.eventType = ''
        self.vtSymbol = EMPTY_STRING
        self.dataEngine = DataEngine(eventEngine)
    def setEventType(self, eventType):
        """设置监控的事件类型"""
        self.eventType = eventType
    # ----------------------------------------------------------------------
    def registerEvent(self):
        """注册GUI更新相关的事件监听"""
        self.signal.connect(self.updateEvent)
        self.eventEngine.register(self.eventType, self.signal.emit)

    def initUi(self):
        """初始化界面"""
        self.setMinimumHeight(300)
        self.labelSymbol = QtWidgets.QLabel(vtText.CONTRACT_SYMBOL)
        self.gridleft = QtWidgets.QGridLayout()
        #self.gridleft.addWidget(self.labelSymbol, 0, 0)
        self.lineSymbol = QtWidgets.QLineEdit()
        self.plot = pg.PlotWidget()
        #self.plot.setTitle('vtymbol')
        self.plot.setMouseEnabled(x = False, y = False)
        self.plot.invertY()
        self.plot.setYRange(-40, 80)
        #self.plot.showGrid(x=True, y=True, alpha=1)

        self.workingOrderGraph = pg.BarGraphItem(x = [0],height = [0],width = 0, brush='r',pen='r')
        self.clickBar = pg.BarGraphItem(x=[2], height=[90], width=1, brush='#2E2608',pen = '#63B155')
        #活动委托
        self.workingOrderDict = {}

        self.plot.showAxis(axis='top',show=True)
        yaxticks = [[(0, '0'),(10, '10'), (20, '20'), (30, '30'), (40, '50'), (50, '100'), (60, '200'), (70, '300'),(80, '500'),(90, '1000'),(100, '2000'),(110, '3000'),(120, '5000'),(130, '10000')]]
        yax = self.plot.getAxis('left')
        yax.setTicks(yaxticks)

        #self.gridleft.addWidget(self.lineSymbol, 0, 1, 1, -1)
        self.gridleft.addWidget(self.plot, 1, 0, 1, -1)
        hbox = QtWidgets.QHBoxLayout()
        hbox.addLayout(self.gridleft)
        vbox = QtWidgets.QVBoxLayout()
        vbox.addLayout(hbox)
        self.setLayout(vbox)
        self.updateSymbolCount = 0
        self.k = 0
        self.i = 0
        self.j = 0
        self.barCount = 0
        self.priceTick = EMPTY_FLOAT
        self.symbol = EMPTY_STRING
        self.leftPrice = 0
        self.now = 0
        self.positionSymbol = EMPTY_STRING

        #捕捉鼠标点击屏幕开单
        #事件过滤
        #self.installEventFilter(self)
    def mousePressEvent(self,event):
        #if event.type() == QtCore.QEvent.MouseButtonPress:
        # 根据weidget的局部坐标以及该坐标的点，对应到plot的坐标
        PositionX = (event.x() - 45) * (self.plot.viewRect().right() - self.plot.viewRect().left()) / (
                self.width() - 45) + self.plot.viewRect().left()
        PositionY = (event.y() - 30) * (self.plot.viewRect().bottom() - self.plot.viewRect().top()) / (
                self.height() - 30) + self.plot.viewRect().top() + 5
        if PositionX > 1 and PositionY > 0 and PositionY < 80:
            if (PositionX - 0.30 * self.priceTick) < self.bidPrice1:
                price = round((PositionX + 0.15 * self.priceTick) / self.priceTick) * self.priceTick
                self.clickBar.setOpts(x=[price], width=self.priceTick, brush='#2E2608', pen='#63B155')
            if (PositionX + 0.65 * self.priceTick) > self.askPrice1:
                price = round((PositionX + 0.3 * self.priceTick) / self.priceTick) * self.priceTick
                self.clickBar.setOpts(x=[price], width=self.priceTick, brush='#0A2E08', pen='#63B155')
            self.barCount = 1
        ##需要修改pyqtgraph/widgets/GraphicsView.py 将mouseReleaseEvent的内容替换为mousePressEvent的内容
    def mouseDoubleClickEvent(self, event):
        #获取昨持仓

        #if event.type() == QtCore.QEvent.MouseButtonDblClick:
        # 根据weidget的局部坐标以及该坐标的点，对应到plot的坐标
        PositionX = (event.x() - 45) * (self.plot.viewRect().right() - self.plot.viewRect().left()) / (self.width() - 45) + self.plot.viewRect().left()
        PositionY = (event.y() - 30) * (self.plot.viewRect().bottom() - self.plot.viewRect().top()) / (self.height() - 30) + self.plot.viewRect().top() + 5
        # print("PositionX", (event.x() - 45) * (self.plot.viewRect().right() - self.plot.viewRect().left())/ (self.width()  - 45 ) + self.plot.viewRect().left())
        # print("PositionY", (event.y() - 30) * (self.plot.viewRect().bottom() - self.plot.viewRect().top())/ (self.height()  - 30 ) + self.plot.viewRect().top() + 5)
        if PositionX > 1 and PositionY > 0 and PositionY < 80:
            hotkeyJson = json.load(open('./hotKey.json', 'r'))
            symbol = self.symbol  # 合约
            exchange = EMPTY_STRING  # 交易所
            currency = EMPTY_STRING  # 货币
            productClass = EMPTY_STRING  # 产品类型
            gatewayName = EMPTY_STRING  # 接口

            # 查询合约
            if exchange:
                vtSymbol = '.'.join([symbol, exchange])
                contract = self.mainEngine.getContract(vtSymbol)
            else:
                vtSymbol = symbol
                contract = self.mainEngine.getContract(symbol)
            if contract:
                vtSymbol = contract.vtSymbol
                gatewayName = contract.gatewayName
                exchange = contract.exchange  # 保证有交易所代码
            for Hotkey in hotkeyJson:
                self.req = VtOrderReq()
                self.req.symbol = symbol  # 合约
                self.req.exchange = exchange  # 交易所
                self.req.vtSymbol = contract.vtSymbol  # 合约名称
                self.req.priceType = unicode(u'限价')
                self.req.currency = currency  # 货币
                self.req.productClass = productClass
                if symbol not in DEFAULT_OPEM.keys():
                    DEFAULT_OPEM[symbol] = 1
                if (PositionX - 0.30 * self.priceTick) < self.bidPrice1:
                    if Hotkey[u'hotkey'] == u'小键盘1':
                        self.req.price = round(
                            (PositionX + 0.15 * self.priceTick) / self.priceTick) * self.priceTick
                        self.req.direction = Hotkey['direction']
                        self.req.volume = int(Hotkey['volume']) * DEFAULT_OPEM[symbol]
                        self.req.offset = Hotkey['offset']
                        if self.symbol == self.AllPosition.__getattribute__('symbol'):
                            if self.AllPosition.__getattribute__('shortNetPos') != 0:
                                self.req.offset = unicode(u'平今')
                            if self.AllPosition.__getattribute__('shortYd') != 0:
                                self.req.offset = unicode(u'平昨')
                        self.mainEngine.sendOrder(self.req, gatewayName)
                if (PositionX + 0.65 * self.priceTick) > self.askPrice1:
                    if Hotkey[u'hotkey'] == u'小键盘3':
                        self.req.price = round((PositionX + 0.2 * self.priceTick) / self.priceTick) * self.priceTick
                        self.req.direction = Hotkey['direction']
                        self.req.volume = int(Hotkey['volume'])* DEFAULT_OPEM[symbol]
                        self.req.offset = Hotkey['offset']
                        if self.symbol == self.AllPosition.__getattribute__('symbol'):
                            if self.AllPosition.__getattribute__('longNetPos') != 0:
                                self.req.offset = unicode(u'平今')
                            if self.AllPosition.__getattribute__('longYd') != 0:
                                self.req.offset = unicode(u'平昨')
                        self.mainEngine.sendOrder(self.req, gatewayName)

    def updateSymbol(self, symbol):
        self.vtSymbol = symbol
        self.i = 0
        self.updateSymbolCount += 1
        #重置历史价格记录
        self.j = 0
        self.leftPRICE = []
        self.rightPRICE = []
        self.PRICEY = {}
    def updateEvent(self, event):
        """收到事件更新"""
        self.now = pg.ptime.time()
        data = event.dict_['data']
        if self.vtSymbol == data.__getattribute__('symbol'):
            self.updateData(data)
            self.updatePosition(event)

    # ----------------------------------------------------------------------
    def updateData(self,data):
        """更新数据到图表"""
        self.symbol = data.__getattribute__('symbol')
        #print self.lineSymbol.currentText()
        #self.bidPrice1.__setattr__(str(data.__getattribute__('bidPrice1')))
        self.lineSymbol.setText(data.__getattribute__('symbol'))
        self.lastPrice = data.__getattribute__('lastPrice')
        self.bidPrice1 = data.__getattribute__('bidPrice1')
        self.bidVolume1 = data.__getattribute__('bidVolume1')
        self.askPrice1 = data.__getattribute__('askPrice1')
        self.askVolume1 = data.__getattribute__('askVolume1')
        self.highPrice = data.__getattribute__('highPrice')
        self.lowPrice = data.__getattribute__('lowPrice')
        self.volume = data.__getattribute__('volume')

        self.now = pg.ptime.time()

        if self.i ==1:
            self.ASKPRICE1[self.askPrice1] = self.adapter(self.askVolume1)
            self.BIDPRICE1[self.bidPrice1] = self.adapter(self.bidVolume1)
            for key in self.ASKPRICE1.keys():
                if key < self.askPrice1:
                    self.ASKPRICE1.pop(key)
            for key in self.BIDPRICE1.keys():
                if key > self.bidPrice1:
                    self.BIDPRICE1.pop(key)
            self.opts = self.bg01.setOpts(x=self.ASKPRICE1.keys(), height=self.ASKPRICE1.values())
            self.bg02.setOpts(x=self.BIDPRICE1.keys(),height=self.BIDPRICE1.values())

            self.j += 1
            self.PRICEY[self.j + 1] = (-5 - 2 * self.j)
            #历史成交价
            #如果成交量未发生变化，将柱子宽度设置为0
            if self.totalVolume == self.volume:
                self.leftPRICE.insert(0,self.lastPrice)
                self.rightPRICE.insert(0,self.lastPrice)
            else:
                self.leftPRICE.insert(0,self.lastPrice - 0.5 * self.priceTick)
                self.rightPRICE.insert(0,self.lastPrice + 0.5 * self.priceTick)
            self.bglastPrice0.setOpts(x0=self.leftPRICE,x1=self.rightPRICE, y1=self.PRICEY.values())
            self.totalVolume = self.volume
            # 当前成交价
            self.bglastPrice1.setOpts(x=[self.lastPrice])
            if self.barCount != 5:
                self.barCount += 1
            else:
                self.clickBar.setOpts(x=[0], width=self.priceTick, brush='#0A2E08', pen='#63B155')
                self.barCount = 1

            self.bghighPrice.setOpts(x=[self.highPrice + 0.5 * self.priceTick])
            self.bglowPrice.setOpts(x=[self.lowPrice - 0.5 * self.priceTick])

            if self.j == 101:
                self.leftPRICE.pop()
                self.rightPRICE.pop()
                self.PRICEY.pop(102)
                self.j = 100

            self.bgbidRegion.setOpts(x0=[self.bidPrice1 - 50.5 * self.priceTick],x1=[self.bidPrice1 + 0.5 * self.priceTick])
            self.bgaskRegion.setOpts(x0=[self.askPrice1 + 50.5 * self.priceTick], x1=[self.askPrice1 - 0.5 * self.priceTick])
            self.textbg01.setText(str(self.bidVolume1))
            self.textbg02.setText(str(self.askVolume1))
            self.textbg01.setPos(self.bidPrice1, 0)
            self.textbg02.setPos(self.askPrice1, 0)
            if (self.leftPrice + 10 * self.priceTick) >= self.bidPrice1:
                self.plot.setXRange(self.bidPrice1 - 10 * self.priceTick, self.bidPrice1 + 50 * self.priceTick)
                self.leftPrice = self.bidPrice1 - 10 * self.priceTick
            elif (self.leftPrice + 50 * self.priceTick) <= self.askPrice1:
                self.plot.setXRange(self.askPrice1 - 50 * self.priceTick , self.askPrice1 + 10 * self.priceTick)
                self.leftPrice = self.askPrice1 - 50 * self.priceTick
            #self.i = 1

        elif self.i == 0:
            #重置图表
            if self.updateSymbolCount != 1:
                try:
                    self.plot.removeItem(self.bgbidRegion)
                    self.plot.removeItem(self.bgaskRegion)
                    self.plot.removeItem(self.bglastPrice0)
                    self.plot.removeItem(self.bglastPrice1)
                    self.plot.removeItem(self.clickBar)
                    self.plot.removeItem(self.bg01)
                    self.plot.removeItem(self.bg02)
                    self.plot.removeItem(self.workingOrderGraph)
                    self.plot.removeItem(self.textbg01)
                    self.plot.removeItem(self.textbg02)
                    self.plot.removeItem(self.bghighPrice)
                    self.plot.removeItem(self.bglowPrice)
                except AttributeError:
                    print "Error: Duplicated subscribe symbols"
                pass
            #获取最小合约，并放入字典中{symbol:tickPrice}
            l = self.mainEngine.getAllContracts()
            priceTick = {}
            for contract in l:
                priceTick[contract.symbol] = contract.__getattribute__('priceTick')
            #Tick数据
            self.priceTick = priceTick[self.symbol] #
            self.ASKPRICE1 = {self.askPrice1 : self.adapter(self.askVolume1)}#查询指定合约最小价格TICK
            self.BIDPRICE1 = {self.bidPrice1 : self.adapter(self.bidVolume1)}
            self.plot.setXRange(self.lastPrice-30 * self.priceTick, self.lastPrice + 30 * self.priceTick)
            #self.leftPrice用于第二次及以后设置窗口位置的定位
            self.leftPrice = self.lastPrice - 30*self.priceTick
            #历史成交价的左边缘以及右边缘
            self.leftPRICE = [self.lastPrice - 0.5 * self.priceTick]
            self.rightPRICE = [self.lastPrice + 0.5 * self.priceTick]
            self.PRICEY = {}
            self.PRICEY[1] = -4
            self.totalVolume = self.volume

            self.bg01 = pg.BarGraphItem(x=self.ASKPRICE1.keys(), height=self.ASKPRICE1.values(), width=self.priceTick, brush='#B5DDC7')
            self.bg02 = pg.BarGraphItem(x=self.BIDPRICE1.keys(), height=self.BIDPRICE1.values(), width=self.priceTick, brush='#FFCFE9')
            #print self.ASKPRICE1.keys()

            #历史成交价
            self.bglastPrice0 = pg.BarGraphItem(x0=self.leftPRICE, x1=self.rightPRICE, y=-5, height=2,brush='#FFB90F')

            #当前成交价
            self.bglastPrice1 = pg.BarGraphItem(x=[self.lastPrice], y = -4, height=2, width=self.priceTick, brush='#1A1A1A')
            #五档背景图
            self.bgbidRegion = pg.BarGraphItem(x0=[self.bidPrice1 - 50.5 * self.priceTick],x1=[self.bidPrice1 + 0.5 * self.priceTick] ,y0=0, y1=500 ,brush='#2E2608',pen='#2E2608' )
            self.bgaskRegion = pg.BarGraphItem(x0=[self.askPrice1 + 50.5 * self.priceTick], x1=[self.askPrice1 - 0.5 *self.priceTick], y0=0, y1=500,brush='#0A2E08',pen='#0A2E08' )
            #买单红#FFCFE9  卖单绿#B5DDC7  买单背景棕#2E2608  卖单背景绿#0A2E08，最低价绿#06E001  最高价黄#919C03
            #self.bgbidRegion.Horizontal()
            self.bghighPrice = pg.BarGraphItem(x=[self.highPrice + 0.5 * self.priceTick], height=300, width=0,pen='#919C03')
            self.bglowPrice = pg.BarGraphItem(x=[self.lowPrice - 0.5 * self.priceTick], height=300, width=0,pen='#06E001')

            self.textbg01 = pg.TextItem(anchor=(0.5, 0))
            self.textbg02 = pg.TextItem(anchor=(0.5, 0),color='#FFFFFF')

            self.textbg01.setText(str(self.bidVolume1))
            self.textbg02.setText(str(self.askVolume1))
            self.textbg01.setPos(self.bidPrice1, 0)
            self.textbg02.setPos(self.askPrice1, 0)

            self.plot.addItem(self.bgbidRegion)
            self.plot.addItem(self.bgaskRegion)
            self.plot.addItem(self.bglastPrice0)
            self.plot.addItem(self.bglastPrice1)
            self.plot.addItem(self.clickBar)
            self.plot.addItem(self.bg01)
            self.plot.addItem(self.bg02)
            self.plot.addItem(self.workingOrderGraph)
            self.plot.addItem(self.textbg01)
            self.plot.addItem(self.textbg02)
            self.plot.addItem(self.bghighPrice)
            self.plot.addItem(self.bglowPrice)
            self.i += 1

    def updatePosition(self,event):
        data = event.dict_['data']
        symbol = data.__getattribute__('symbol')
        vtSymbol = data.__getattribute__('vtSymbol')
        self.AllPosition = self.dataEngine.getPositionDetail(vtSymbol)
        longNetPos = self.AllPosition.__getattribute__('longNetPos')
        shortNetPos = self.AllPosition.__getattribute__('shortNetPos')
        if self.AllPosition.__getattribute__('longPos') is 0 and self.AllPosition.__getattribute__('shortPos') is 0:
            longNetPos = 0
            shortNetPos = 0
        if self.symbol == symbol:
            #当前订阅的行情，如果有持仓，则显示持仓盈亏
            if self.priceTick != 0.0:
                if symbol == self.AllPosition.__getattribute__('symbol'):
                    # 第一个Tick
                    if self.k == 0:
                        self.LongPositionBar = pg.BarGraphItem(x0=[self.bidPrice1], x1=[self.bidPrice1], y=-1,
                                                               height=-1.4, brush='#000000', pen='#000000')
                        self.plot.addItem(self.LongPositionBar)
                        self.k = 1
                        self.positionSymbol = symbol

                    if self.k == 1 and self.positionSymbol != symbol and self.symbol != self.positionSymbol:
                        self.plot.removeItem(self.LongPositionBar)
                        self.LongPositionBar = pg.BarGraphItem(x0=[self.bidPrice1], x1=[self.bidPrice1], y=-1,
                                                               height=-1.4, brush='#000000', pen='#000000')
                        self.plot.addItem(self.LongPositionBar)
                        self.positionSymbol = symbol

                    if longNetPos is 0 and shortNetPos is 0:
                        self.LongPositionBar.setOpts(x0=[self.bidPrice1], x1=[self.bidPrice1], brush='#000000',
                                                     pen='#000000')

                    # 多单跟踪
                    elif longNetPos is not 0 and shortNetPos is 0:
                        # 盈利
                        if self.AllPosition.__getattribute__('longNetPrice') < self.bidPrice1:
                            self.LongPositionBar.setOpts(x0=[self.AllPosition.__getattribute__('longNetPrice')], x1=[self.bidPrice1],brush='r', pen='r')
                        # 亏损
                        else:
                            self.LongPositionBar.setOpts(x0=[self.AllPosition.__getattribute__('longNetPrice')], x1=[self.bidPrice1],
                                                         brush='b', pen='b')
                    #空单跟踪
                    elif longNetPos is 0 and shortNetPos is not 0:
                        #盈利
                        if self.AllPosition.__getattribute__('shortNetPrice') > self.askPrice1:
                            self.LongPositionBar.setOpts(x0=[self.AllPosition.__getattribute__('shortNetPrice')], x1=[self.askPrice1],
                                                         brush='r', pen='r')
                        # 亏损
                        else:
                            self.LongPositionBar.setOpts(x0=[self.AllPosition.__getattribute__('shortNetPrice')], x1=[self.askPrice1],
                                                         brush='b', pen='b')
                    #锁仓跟踪
                    elif longNetPos is not 0 and shortNetPos is not 0:
                        pass
                        #print self.AllPosition[symbol]


    ##适配五档买卖量映射到坐标轴
    def adapter(self,num):
        numbers = {
            num in range(0, 31): num,
            num in range(31, 51): 30 + (num - 30) / 2,
            num in range(51, 101): 40 + (num - 50) / 5,
            num in range(101, 301): 50 + (num - 100) / 10,
            num in range(301, 501): 70 + (num - 300) / 20,
            num in range(501, 1001): 80 + (num - 500) / 50,
            num in range(1001, 3001): 90 + (num - 1000) / 100,
            num > 3000: num
        }
        return numbers[True]
    def updateOrdingGraph(self,event):
        order = event.dict_['data']
        # 将活动委托缓存下来
        if order.status in self.WORKING_STATUS:
            self.workingOrderDict[order.vtOrderID] = order
        # 移除缓存中已经完成的委托
        else:
            if order.vtOrderID in self.workingOrderDict:
                del self.workingOrderDict[order.vtOrderID]

        #如果该委托已完成，则隐藏该行
        if order.status in self.STATUS_COMPLETED and order.vtOrderID in self.workingOrderDict.keys():
            del self.workingOrderDict[order.vtOrderID]

        #绘制挂单量
        priceOrder = {}
        i = 0
        symbol = EMPTY_STRING
        totalVolume = EMPTY_INT
        if self.workingOrderDict != {}:
            for workingOrdingDict in self.workingOrderDict.values():
                if i == 0 or symbol != workingOrdingDict.symbol:
                    totalVolume = workingOrdingDict.leftVolume
                    priceOrder[workingOrdingDict.price] = self.adapter(totalVolume)
                    symbol = workingOrdingDict.symbol
                    i = 1
                elif workingOrdingDict.price in priceOrder.keys():
                    priceOrder[workingOrdingDict.price] +=  workingOrdingDict.leftVolume
                else:
                    priceOrder[workingOrdingDict.price] = workingOrdingDict.leftVolume

        if priceOrder != {} and self.priceTick is not EMPTY_FLOAT:
            self.workingOrderGraph.setOpts(x = priceOrder.keys(), height = priceOrder.values(),width = self.priceTick)
        else:
            self.workingOrderGraph.setOpts(x=[0], height=[0], width=self.priceTick)

class MainGraph(BasicGraph):
    """Tick界面组件"""
    signal = QtCore.Signal(type(Event()))
    # ----------------------------------------------------------------------
    def __init__(self, mainEngine, eventEngine, parent=None):
        """Constructor"""
        super(MainGraph, self).__init__(mainEngine,eventEngine,parent)

        # 初始化tick图
        self.initUi()

        #self.setDataKey()
        # 设置监控事件类型
        self.setEventType(EVENT_TICK)
        # 注册事件监听
        self.registerEvent()

########################################################################
class ContractMonitor(BasicMonitor):
    """合约查询"""

    #----------------------------------------------------------------------
    def __init__(self, mainEngine, parent=None):
        """Constructor"""
        super(ContractMonitor, self).__init__(parent=parent)
        
        self.mainEngine = mainEngine
        
        d = OrderedDict()
        d['symbol'] = {'chinese':vtText.CONTRACT_SYMBOL, 'cellType':BasicCell}
        d['exchange'] = {'chinese':vtText.EXCHANGE, 'cellType':BasicCell}
        d['vtSymbol'] = {'chinese':vtText.VT_SYMBOL, 'cellType':BasicCell}
        d['name'] = {'chinese':vtText.CONTRACT_NAME, 'cellType':BasicCell}
        d['productClass'] = {'chinese':vtText.PRODUCT_CLASS, 'cellType':BasicCell}
        d['size'] = {'chinese':vtText.CONTRACT_SIZE, 'cellType':BasicCell}
        d['priceTick'] = {'chinese':vtText.PRICE_TICK, 'cellType':BasicCell}
        
        d['underlyingSymbol'] = {'chinese':vtText.UNDERLYING_SYMBOL, 'cellType':BasicCell}
        d['optionType'] = {'chinese':vtText.OPTION_TYPE, 'cellType':BasicCell}  
        d['expiryDate'] = {'chinese':vtText.EXPIRY_DATE, 'cellType':BasicCell}
        d['strikePrice'] = {'chinese':vtText.STRIKE_PRICE, 'cellType':BasicCell}
        self.setHeaderDict(d)
        
        # 过滤显示用的字符串
        self.filterContent = EMPTY_STRING
        
        self.initUi()
        
    #----------------------------------------------------------------------
    def initUi(self):
        """初始化界面"""
        self.setMinimumSize(800, 800)
        self.setFont(BASIC_FONT)
        self.initTable()
        self.addMenuAction()
    
    #----------------------------------------------------------------------
    def showAllContracts(self):
        """显示所有合约数据"""
        l = self.mainEngine.getAllContracts()
        d = {'.'.join([contract.exchange, contract.symbol]):contract for contract in l}
        l2 = d.keys()
        l2.sort(reverse=True)

        self.setRowCount(len(l2))
        row = 0
        
        for key in l2:
            # 如果设置了过滤信息且合约代码中不含过滤信息，则不显示
            if self.filterContent and self.filterContent not in key:
                continue
            
            contract = d[key]
            
            for n, header in enumerate(self.headerList):
                content = safeUnicode(contract.__getattribute__(header))
                cellType = self.headerDict[header]['cellType']
                cell = cellType(content)
                
                if self.font:
                    cell.setFont(self.font)  # 如果设置了特殊字体，则进行单元格设置
                    
                self.setItem(row, n, cell)          
            
            row = row + 1        
    
    #----------------------------------------------------------------------
    def refresh(self):
        """刷新"""
        self.menu.close()   # 关闭菜单
        self.clearContents()
        self.setRowCount(0)
        self.showAllContracts()
    
    #----------------------------------------------------------------------
    def addMenuAction(self):
        """增加右键菜单内容"""
        refreshAction = QtWidgets.QAction(vtText.REFRESH, self)
        refreshAction.triggered.connect(self.refresh)
        
        self.menu.addAction(refreshAction)
    
    #----------------------------------------------------------------------

    def show(self):
        """显示"""
        super(ContractMonitor, self).show()
        self.refresh()
        
    #----------------------------------------------------------------------
    def setFilterContent(self, content):
        """设置过滤字符串"""
        self.filterContent = content
    

########################################################################
class ContractManager(QtWidgets.QWidget):
    """合约管理组件"""

    #----------------------------------------------------------------------
    def __init__(self, mainEngine, parent=None):
        """Constructor"""
        super(ContractManager, self).__init__(parent=parent)
        
        self.mainEngine = mainEngine
        
        self.initUi()
    
    #----------------------------------------------------------------------
    def initUi(self):
        """初始化界面"""
        self.setWindowTitle(vtText.CONTRACT_SEARCH)
        
        self.lineFilter = QtWidgets.QLineEdit()
        self.buttonFilter = QtWidgets.QPushButton(vtText.SEARCH)
        self.buttonFilter.clicked.connect(self.filterContract)        
        self.monitor = ContractMonitor(self.mainEngine)
        self.monitor.refresh()
        
        hbox = QtWidgets.QHBoxLayout()
        hbox.addWidget(self.lineFilter)
        hbox.addWidget(self.buttonFilter)
        hbox.addStretch()
        
        vbox = QtWidgets.QVBoxLayout()
        vbox.addLayout(hbox)
        vbox.addWidget(self.monitor)
        
        self.setLayout(vbox)
        
    #----------------------------------------------------------------------
    def filterContract(self):
        """显示过滤后的合约"""
        content = str(self.lineFilter.text())
        self.monitor.setFilterContent(content)
        self.monitor.refresh()

########################################################################
class WorkingOrderMonitor(OrderMonitor):
    """活动委托监控"""
    STATUS_COMPLETED = [STATUS_ALLTRADED, STATUS_CANCELLED, STATUS_REJECTED]

    #----------------------------------------------------------------------
    def __init__(self, mainEngine, eventEngine, parent=None):
        """Constructor"""
        super(WorkingOrderMonitor, self).__init__(mainEngine, eventEngine, parent)
        
    #----------------------------------------------------------------------
    def updateData(self, data):
        """更新数据"""
        super(WorkingOrderMonitor, self).updateData(data)

        # 如果该委托已完成，则隐藏该行
        if data.status in self.STATUS_COMPLETED:
            vtOrderID = data.vtOrderID
            cellDict = self.dataDict[vtOrderID]
            cell = cellDict['status']
            row = self.row(cell)
            self.hideRow(row)
        ########################################################################


class PositionMonitor(BasicMonitor):
    """持仓监控"""
    # ----------------------------------------------------------------------
    def __init__(self, mainEngine, eventEngine, parent=None):
        """Constructor"""
        super(PositionMonitor, self).__init__(mainEngine, eventEngine, parent)
        d = OrderedDict()
        d['symbol'] = {'chinese':vtText.CONTRACT_SYMBOL, 'cellType':BasicCell}
        d['vtSymbol'] = {'chinese':vtText.CONTRACT_NAME, 'cellType':NameCell}
        #d['direction'] = {'chinese':vtText.DIRECTION, 'cellType':DirectionCell}
        #d['position'] = {'chinese':vtText.POSITION, 'cellType':BasicCell}
        d['longNetPos'] = {'chinese': vtText.TD_POSITION_NET_LONG, 'cellType': BasicCell}
        d['shortNetPos'] = {'chinese': vtText.TD_POSITION_NET_SHORT, 'cellType': BasicCell}
        d['longTd'] = {'chinese': vtText.TD_POSITION_LONG, 'cellType': BasicCell}
        d['shortTd'] = {'chinese': vtText.TD_POSITION_SHORT, 'cellType': BasicCell}

        #d['ydPosition'] = {'chinese': vtText.YD_POSITION, 'cellType': BasicCell}
        d['longYd'] = {'chinese': vtText.YD_POSITION_LONG, 'cellType': BasicCell}
        d['shortYd'] = {'chinese':vtText.YD_POSITION_SHORT, 'cellType':BasicCell}

        d['longNetPrice'] = {'chinese': vtText.LONGPRICE_NET, 'cellType': BasicCell}
        d['shortNetPrice'] = {'chinese': vtText.SHORTPRICE_NET, 'cellType': BasicCell}
        d['longPrice'] = {'chinese':vtText.LONGPRICE, 'cellType':BasicCell}
        d['shortPrice'] = {'chinese': vtText.SHORTPRICE, 'cellType': BasicCell}

        d['longNetPnl'] = {'chinese': vtText.POSITION_NET_LONG_PROFIT, 'cellType': PnlCell}
        d['shortNetPnl'] = {'chinese': vtText.POSITION_NET_SHORT_PROFIT, 'cellType': PnlCell}
        d['longPnl'] = {'chinese':vtText.POSITION_LONG_PROFIT, 'cellType':PnlCell}
        d['shortPnl'] = {'chinese': vtText.POSITION_SHORT_PROFIT, 'cellType': PnlCell}
        #d['longPosFrozen'] = {'chinese': vtText.LONGFROZEN, 'cellType': BasicCell}
        #d['shortPosFrozen'] = {'chinese': vtText.SHORTFROZEN, 'cellType': BasicCell}
        #d['frozen'] = {'chinese': vtText.FROZEN, 'cellType': BasicCell}
        #d['gatewayName'] = {'chinese':vtText.GATEWAY, 'cellType':BasicCell}
        self.setHeaderDict(d)

        self.setDataKey('vtSymbol')
        self.setFont(BASIC_FONT)
        #self.setEventType(EVENT_POSITION)
        self.setSaveData(True)
        self.initTable()
        self.AllPosition = {}
        self.dataEngine = DataEngine(eventEngine)
        # 注册事件监听
        self.registerEvent()

    def registerEvent(self):
        """注册GUI更新相关的事件监听"""
        self.signal.connect(self.updateEvent) #持仓
        self.eventEngine.register(EVENT_TICK, self.signal.emit)
        self.eventEngine.register(EVENT_TRADE, self.signal.emit)
    #----------------------------------------------------------------------

    def updateEvent(self, event):
        """收到事件更新"""
        AllPositionDetails = self.dataEngine.getAllPositionDetails()
        event_data = event.dict_['data']
        if event_data.__getattribute__('vtSymbol') in AllPositionDetails.keys():
            for detail in AllPositionDetails.values():
                positionDict = {}
                positionDict['symbol'] = detail.__getattribute__('symbol')
                positionDict['positionLong'] = detail.__getattribute__('longTd')
                positionDict['longNetPos'] = detail.__getattribute__('longNetPos')
                positionDict['positionShort'] = detail.__getattribute__('shortTd')
                positionDict['shortNetPos'] = detail.__getattribute__('shortNetPos')
                positionDict['longPrice'] = detail.__getattribute__('longPrice')
                positionDict['longNetPrice'] = detail.__getattribute__('longNetPrice')
                positionDict['shortPrice'] = detail.__getattribute__('shortPrice')
                positionDict['shortNetPrice'] = detail.__getattribute__('shortNetPrice')
                positionDict['longNetPnl'] = detail.__getattribute__('longNetPnl')
                positionDict['shortNetPnl'] = detail.__getattribute__('shortNetPnl')
                positionDict['shortYd'] = detail.__getattribute__('shortYd')
                positionDict['longYd'] = detail.__getattribute__('longYd')
                self.AllPosition[detail.__getattribute__('symbol')] = positionDict
                data = detail
                self.updateData(data)
    def updateData(self, data):
        """更新数据"""
        super(PositionMonitor,self).updateData(data)
        #若果多，空持仓都为0，则隐藏
        if data.__getattribute__('longPos') is 0 and data.__getattribute__('shortPos') is 0:
            vtSymbol = data.vtSymbol
            cellDict = self.dataDict[vtSymbol]
            cell = cellDict['vtSymbol']
            row = self.row(cell)
            self.hideRow(row)
        else:
            vtSymbol = data.vtSymbol
            cellDict = self.dataDict[vtSymbol]
            cell = cellDict['vtSymbol']
            row = self.row(cell)
            self.showRow(row)
########################################################################
class SettingEditor(QtWidgets.QWidget):
    """配置编辑器"""

    #----------------------------------------------------------------------
    def __init__(self, mainEngine, parent=None):
        """Constructor"""
        super(SettingEditor, self).__init__(parent)
        
        self.mainEngine = mainEngine
        self.currentFileName = ''
        
        self.initUi()
    
    #----------------------------------------------------------------------
    def initUi(self):
        """初始化界面"""
        self.setWindowTitle(vtText.EDIT_SETTING)
        
        self.comboFileName = QtWidgets.QComboBox()
        self.comboFileName.addItems(jsonPathDict.keys())
        
        buttonLoad = QtWidgets.QPushButton(vtText.LOAD)
        buttonSave = QtWidgets.QPushButton(vtText.SAVE)
        buttonLoad.clicked.connect(self.loadSetting)
        buttonSave.clicked.connect(self.saveSetting)
        
        self.editSetting = QtWidgets.QTextEdit()
        self.labelPath = QtWidgets.QLabel()
        
        hbox = QtWidgets.QHBoxLayout()
        hbox.addWidget(self.comboFileName)
        hbox.addWidget(buttonLoad)
        hbox.addWidget(buttonSave)
        hbox.addStretch()
        
        vbox = QtWidgets.QVBoxLayout()
        vbox.addLayout(hbox)
        vbox.addWidget(self.editSetting)
        vbox.addWidget(self.labelPath)
        
        self.setLayout(vbox)
        
    #----------------------------------------------------------------------
    def loadSetting(self):
        """加载配置"""
        self.currentFileName = str(self.comboFileName.currentText())
        filePath = jsonPathDict[self.currentFileName]
        self.labelPath.setText(filePath)
        
        with open(filePath) as f:
            self.editSetting.clear()
            
            for line in f:
                line = line.replace('\n', '')   # 移除换行符号
                line = line.decode('UTF-8')
                self.editSetting.append(line)
    
    #----------------------------------------------------------------------
    def saveSetting(self):
        """保存配置"""
        if not self.currentFileName:
            return
        
        filePath = jsonPathDict[self.currentFileName]
        
        with open(filePath, 'w') as f:
            content = self.editSetting.toPlainText()
            content = content.encode('UTF-8')
            f.write(content)
        
    #----------------------------------------------------------------------
    def show(self):
        """显示"""
        # 更新配置文件下拉框
        self.comboFileName.clear()
        self.comboFileName.addItems(jsonPathDict.keys())
        
        # 显示界面
        super(SettingEditor, self).show()

class SubscribeDefaultWidget(BasicMonitor):
    """显示默认订阅信息"""
    # ----------------------------------------------------------------------
    def __init__(self, parent=None):
        """Constructor"""
        super(SubscribeDefaultWidget, self).__init__(parent)
        # 设置表头有序字典
        d = OrderedDict()
        d['symbol'] = {'chinese': vtText.CONTRACT_SYMBOL, 'cellType': BasicCell}
        d['lock_Position'] = {'chinese': vtText.LOCK_POSITION, 'cellType': BasicCell}
        d['default_Open'] = {'chinese': vtText.DEFAULT_OPEN, 'cellType': BasicCell}
        self.setHeaderDict(d)
        # 设置字体
        self.setFont(BASIC_FONT)

        # 设置排序
        self.setSorting(False)

        # 初始化表格
        self.initTable()
        self.setEditTriggers(self.DoubleClicked)
        self.setUpdatesEnabled(True)

        self.initUi()
        self.updateData()

    def updateData(self):
        # 如果允许了排序功能，则插入数据前必须关闭，否则插入新的数据会变乱
        if self.sorting:
            self.setSortingEnabled(False)

        #从json文件中读取快捷键字典的列表，更新到表格中
        data = json.load(open('./subscribeDefault.json','r'))
        data.reverse()
        for hotkey in data:
            self.insertRow(0)
            d = {}
            for n, header in enumerate(self.headerList):
                content = hotkey[header]
                cellType = self.headerDict[header]['cellType']
                cell = cellType(content)
                self.setItem(0, n, cell)
        # 调整列宽
        if not self.columnResized:
            self.resizeColumns()
            self.columnResized = True

        # 重新打开排序
        if self.sorting:
            self.setSortingEnabled(True)
    # ----------------------------------------------------------------------
    def saveToCsv(self):
        #将表格中的快捷键信息，保存到快捷键的json文件
        rowdata = []
        for row in range(self.rowCount()):
            data = {}
            for head, column in [('symbol',0),('lock_Position',1),('default_Open',2)]:
                item = self.item(row, column)
                if item is not None:
                    data[head] = item.text()
                else:
                    data[head] = ''
            rowdata.append(data)
        json.dump(rowdata, open('./subscribeDefault.json', 'w'))

        subscribeDefault = json.load(open('./subscribeDefault.json', 'r'))

        for subscribe in subscribeDefault:
            # 确定锁仓
            if subscribe['symbol'] != u''and subscribe['lock_Position'] != u'':
                LOCKPOSITION[subscribe['symbol']] = int(subscribe['lock_Position'])
            if subscribe['symbol'] != u''and subscribe['default_Open'] != u'':
                DEFAULT_OPEM[subscribe['symbol']] = int(subscribe['default_Open'])

    # ----------------------------------------------------------------------
    def initUi(self):
        """"""
        self.setWindowTitle(vtText.EDIT_HOTKEY)
        self.setMinimumSize(450,278)
    # ----------------------------------------------------------------------
    def show(self):
        """显示"""
        super(SubscribeDefaultWidget,self).show()

class HotKeyWidget(BasicMonitor):
    """显示快捷键信息"""
    # ----------------------------------------------------------------------
    def __init__(self, parent=None):
        """Constructor"""
        super(HotKeyWidget, self).__init__(parent)
        # 设置表头有序字典
        d = OrderedDict()
        d['hotkey'] = {'chinese': vtText.HOTKEY, 'cellType': HotKeyBasicCell}
        d['offset'] = {'chinese': vtText.OFFSET, 'cellType': HotKeyBasicCell}
        d['direction'] = {'chinese': vtText.DIRECTION, 'cellType': HotKeyBasicCell}
        d['price_type'] = {'chinese': vtText.PRICE_TYPE, 'cellType': HotKeyBasicCell}
        d['limit_price'] = {'chinese': vtText.LIMIT_PRICE, 'cellType': HotKeyBasicCell}
        d['volume'] = {'chinese': vtText.VOLUME, 'cellType': HotKeyBasicCell}
        self.setHeaderDict(d)
        # 设置字体
        self.setFont(BASIC_FONT)

        # 设置排序
        self.setSorting(False)

        # 初始化表格
        self.initTable()
        self.setEditTriggers(self.DoubleClicked)
        self.setUpdatesEnabled(True)

        self.initUi()
        self.updateData()

    def updateData(self):
        # 如果允许了排序功能，则插入数据前必须关闭，否则插入新的数据会变乱
        if self.sorting:
            self.setSortingEnabled(False)

        #从json文件中读取快捷键字典的列表，更新到表格中
        data = json.load(open('./hotKey.json','r'))
        data.reverse()
        for hotkey in data:
            self.insertRow(0)
            d = {}
            for n, header in enumerate(self.headerList):
                content = hotkey[header]
                cellType = self.headerDict[header]['cellType']
                cell = cellType(content)
                self.setItem(0, n, cell)
        # 调整列宽
        if not self.columnResized:
            self.resizeColumns()
            self.columnResized = True

        # 重新打开排序
        if self.sorting:
            self.setSortingEnabled(True)
    # ----------------------------------------------------------------------
    def saveToCsv(self):
        #将表格中的快捷键信息，保存到快捷键的json文件
        rowdata = []
        for row in range(self.rowCount()):
            data = {}
            for head, column in [('hotkey',0),('offset',1),('direction',2),('price_type',3),('limit_price',4),('volume',5)]:
                item = self.item(row, column)
                if item is not None:
                    data[head] = item.text()
                else:
                    data[head] = ''
            rowdata.append(data)
        json.dump(rowdata, open('./hotKey.json', 'w'))
        hotkeyDefault = json.load(open('./hotKey.json', 'r'))
        for hk in hotkeyDefault:
            HOTKEY[DEFINE_KEY[hk['hotkey']]] = hk
    # ----------------------------------------------------------------------
    def initUi(self):
        """"""
        self.setWindowTitle(vtText.EDIT_HOTKEY)
        self.setMinimumSize(450,278)
    # ----------------------------------------------------------------------
    def show(self):
        """显示"""
        super(HotKeyWidget,self).show()
