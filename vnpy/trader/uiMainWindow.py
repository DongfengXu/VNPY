# encoding: UTF-8

import psutil
import traceback
from vnpy.trader.vtFunction import loadIconPath
from vnpy.trader.vtGlobal import globalSetting
from vnpy.trader.uiBasicWidget import *
from .vtEngine import DataEngine
from PyQt5 import Qt


########################################################################
class MainWindow(QtWidgets.QMainWindow):
    """主窗口"""
    signalStatusBar = QtCore.Signal(type(Event()))

    # ----------------------------------------------------------------------
    def __init__(self, mainEngine, eventEngine):
        """Constructor"""
        super(MainWindow, self).__init__()

        self.mainEngine = mainEngine
        self.eventEngine = eventEngine

        l = self.mainEngine.getAllGatewayDetails()
        self.gatewayNameList = [d['gatewayName'] for d in l]

        self.widgetDict = {}  # 用来保存子窗口的字典

        # 获取主引擎中的上层应用信息
        self.appDetailList = self.mainEngine.getAllAppDetails()

        self.initUi()

        self.loadWindowSettings('custom')
        # 键盘策略，在vnpy主窗口置顶时，快捷键有效
        self.setChildrenFocusPolicy(QtCore.Qt.StrongFocus)

    # ----------------------------------------------------------------------
    def initUi(self):
        """初始化界面"""
        self.setWindowTitle('VnTrader')
        # self.setWindowFlags(QtCore.Qt.FramelessWindowHint)
        self.initCentral()
        self.initMenu()
        self.initStatusBar()

    # ----------------------------------------------------------------------
    def initCentral(self):
        """初始化中心区域"""
        self.widgetGraphM, dockMarketM = self.createDock(MainGraph, vtText.PriceW, QtCore.Qt.RightDockWidgetArea)
        self.widgetMarketM, dockMarketM = self.createDock(MarketMonitor, vtText.MARKET_DATA,
                                                          QtCore.Qt.BottomDockWidgetArea)

        widgetLogM, dockLogM = self.createDock(LogMonitor, vtText.LOG, QtCore.Qt.BottomDockWidgetArea)
        widgetErrorM, dockErrorM = self.createDock(ErrorMonitor, vtText.ERROR, QtCore.Qt.BottomDockWidgetArea)
        self.widgetTradeM, dockTradeM = self.createDock(TradeMonitor, vtText.TRADE, QtCore.Qt.RightDockWidgetArea)
        widgetOrderM, dockOrderM = self.createDock(OrderMonitor, vtText.ORDER, QtCore.Qt.BottomDockWidgetArea)
        self.widgetWorkingOrderM, dockWorkingOrderM = self.createDock(WorkingOrderMonitor, vtText.WORKING_ORDER,
                                                                      QtCore.Qt.BottomDockWidgetArea)
        self.widgetPositionM, dockPositionM = self.createDock(PositionMonitor, vtText.POSITION,
                                                              QtCore.Qt.BottomDockWidgetArea)
        widgetAccountM, dockAccountM = self.createDock(AccountMonitor, vtText.ACCOUNT, QtCore.Qt.BottomDockWidgetArea)
        self.widgetTradingW, dockTradingW = self.createDock(TradingWidget, vtText.TRADING, QtCore.Qt.LeftDockWidgetArea)

        self.tabifyDockWidget(dockTradeM, dockErrorM)
        self.tabifyDockWidget(dockTradeM, dockLogM)
        self.tabifyDockWidget(dockPositionM, dockAccountM)
        self.tabifyDockWidget(dockPositionM, dockWorkingOrderM)

        dockTradeM.raise_()
        dockPositionM.raise_()

        # 连接组件之间的信号
        self.widgetPositionM.itemDoubleClicked.connect(self.widgetTradingW.closePosition)  # 双击持仓，更改交易品种
        self.widgetMarketM.itemClicked.connect(self.widgetTradingW.closePosition)  # 双击行情，更改交易品种

        self.widgetMarketM.itemClicked.connect(self.updateGraphSymbol)  # 双击行情监控，更改图表监控品种
        self.widgetPositionM.itemDoubleClicked.connect(self.updateGraphSymbol)  # 双击持仓更改图表监控品种
        self.widgetWorkingOrderM.signal.connect(self.widgetGraphM.updateOrdingGraph)  # 更新挂单图
        self.widgetTradeM.signal.connect(self.widgetGraphM.updatePosition)  # 更新持仓图
        #self.widgetMarketM.signal.connect(self.widgetGraphM.updatePosition)  # 每接收一个tick，更新一次持仓图表

        self.widgetTradingW.lineSymbol.returnPressed.connect(self.updateGraphSymbol)  # 更改图表监控品种
        # 策略报单（委托状态）更新 策略回合（委托状态）

        # self.widgetGraphM.(self.clickOrding)
        # 保存默认设置
        self.saveWindowSettings('default')

    #def updateGraphPosition(self):
    #    self.widgetGraphM.AllPosition = self.widgetPositionM.AllPosition

    def updateGraphSymbol(self):
        symbol = str(self.widgetTradingW.lineSymbol.text())
        self.widgetGraphM.updateSymbol(symbol)

    def setChildrenFocusPolicy(self, policy):
        def recursiveSetChildFocusPolicy(parentQWidget):
            for childQWidget in parentQWidget.findChildren(QtWidgets.QWidget):
                childQWidget.setFocusPolicy(policy)
                recursiveSetChildFocusPolicy(childQWidget)

        recursiveSetChildFocusPolicy(self)

    # 定义键盘事件
    def keyPressEvent(self, eventQKeyEvent):
        # 发单撤单指令
        if eventQKeyEvent.nativeScanCode() in DEFINE_KEY.values():
            if eventQKeyEvent.nativeScanCode() not in HOTKEY.keys():
                return
            orderHotkey = HOTKEY[eventQKeyEvent.nativeScanCode()]
            # 如果开平为撤单，则直接执行撤单命令
            if orderHotkey['offset'] is not None:
                if orderHotkey['offset'] == u'撤单':
                    l = self.widgetTradingW.mainEngine.getAllWorkingOrders()
                    for order in l:
                        req = VtCancelOrderReq()
                        req.symbol = order.symbol
                        req.exchange = order.exchange
                        req.frontID = order.frontID
                        req.sessionID = order.sessionID
                        req.orderID = order.orderID
                        self.mainEngine.cancelOrder(req, order.gatewayName)

                else:  # 当开平为开仓/平仓时，则执行发单命令
                    # 开仓前先撤单
                    l = self.widgetTradingW.mainEngine.getAllWorkingOrders()
                    for order in l:
                        if order.direction == orderHotkey['direction']:
                            req = VtCancelOrderReq()
                            req.symbol = order.symbol
                            req.exchange = order.exchange
                            req.frontID = order.frontID
                            req.sessionID = order.sessionID
                            req.orderID = order.orderID
                            self.mainEngine.cancelOrder(req, order.gatewayName)
                        time.sleep(0.004)
                    symbol = str(self.widgetTradingW.lineSymbol.text())  # 合约
                    exchange = unicode(self.widgetTradingW.comboExchange.currentText())  # 交易所
                    currency = unicode(self.widgetTradingW.comboCurrency.currentText())  # 货币
                    productClass = unicode(self.widgetTradingW.comboProductClass.currentText())  # 产品类型
                    gatewayName = unicode(self.widgetTradingW.comboGateway.currentText())  # 接口

                    # 查询合约
                    if exchange:
                        vtSymbol = '.'.join([symbol, exchange])
                        contract = self.widgetTradingW.mainEngine.getContract(vtSymbol)
                    else:
                        vtSymbol = symbol
                        contract = self.widgetTradingW.mainEngine.getContract(symbol)
                    if contract:
                        gatewayName = contract.gatewayName
                        exchange = contract.exchange  # 保证有交易所代码
                    self.req = VtOrderReq()
                    self.req.symbol = symbol  # 合约
                    self.req.exchange = exchange  # 交易所
                    self.req.vtSymbol = contract.vtSymbol  # 合约名称

                    # 如果未设置锁仓，默认锁仓0
                    if symbol not in LOCKPOSITION.keys():
                        LOCKPOSITION[symbol] = 0
                    if symbol not in DEFAULT_OPEM.keys():
                        DEFAULT_OPEM[symbol] = 1

                    if orderHotkey['direction'] is not None:
                        self.req.direction = orderHotkey['direction']
                        if orderHotkey['limit_price'] is not None and orderHotkey['direction'] == u'多':
                            self.req.price = float(
                                self.widgetTradingW.labelBidPrice1.text()) + self.widgetGraphM.priceTick * float(orderHotkey['limit_price'])
                        elif orderHotkey['limit_price'] is not None and orderHotkey['direction'] == u'空':
                            self.req.price = float(
                                self.widgetTradingW.labelAskPrice1.text()) - self.widgetGraphM.priceTick * float(
                                orderHotkey['limit_price'])
                    if orderHotkey['volume'] is not None:
                        self.req.volume = int(orderHotkey['volume']) * DEFAULT_OPEM[symbol]
                    self.req.priceType = unicode(u'限价')
                    self.req.currency = currency  # 货币
                    self.req.productClass = productClass

                    # 查询开仓合约是否有持仓，如果有持仓，则改为平仓
                    # 获取持仓信息
                    positionDetail = self.widgetPositionM.dataEngine.getPositionDetail(contract.vtSymbol)
                    positionLong = positionDetail.__getattribute__('longTd')
                    positionShort = positionDetail.__getattribute__('shortTd')
                    ydPositionLong = positionDetail.__getattribute__('longYd')
                    ydPositionShort = positionDetail.__getattribute__('shortYd')
                    shortNetPos = positionDetail.__getattribute__('shortNetPos')
                    longNetPos = positionDetail.__getattribute__('longNetPos')
                    if positionDetail.__getattribute__('longPos') is 0 and positionDetail.__getattribute__('shortPos') is 0:
                        shortNetPos = 0
                        longNetPos = 0

                    if orderHotkey['offset'] == u'平昨':
                        self.req.offset = unicode(orderHotkey['offset'])
                        self.widgetTradingW.mainEngine.sendOrder(self.req, gatewayName)
                        return
                    # 如果是开多，但是有空单时，优先平空(支持锁仓对数)
                    elif self.req.symbol == positionDetail.__getattribute__('symbol') and orderHotkey['direction'] == u'多':
                        if positionLong + int(orderHotkey['volume']) * DEFAULT_OPEM[symbol]<= LOCKPOSITION[symbol]:
                            # 优先平昨
                            if ydPositionShort is not 0:
                                self.req.offset = u'平昨'
                                if self.req.volume > shortNetPos and shortNetPos:
                                    content = u'净空持仓不足'
                                    self.mainEngine.writeLog(content)
                                    return
                            else:
                                self.req.offset = unicode(orderHotkey['offset'])
                            self.widgetTradingW.mainEngine.sendOrder(self.req, gatewayName)
                            return
                        elif positionLong + int(orderHotkey['volume']) * DEFAULT_OPEM[symbol] > LOCKPOSITION[symbol]:
                            if positionShort <= LOCKPOSITION[symbol]:
                                # 优先平昨
                                if ydPositionShort is not 0:
                                    self.req.offset = u'平昨'
                                    if self.req.volume > shortNetPos and shortNetPos:
                                        content = u'净空持仓不足'
                                        self.mainEngine.writeLog(content)
                                        return
                                else:
                                    self.req.offset = unicode(orderHotkey['offset'])
                                self.widgetTradingW.mainEngine.sendOrder(self.req, gatewayName)
                                return

                            elif positionShort > LOCKPOSITION[symbol]:
                                if positionLong + int(orderHotkey['volume']) * DEFAULT_OPEM[symbol] >= positionShort:
                                    self.req.volume = int(orderHotkey['volume']) * DEFAULT_OPEM[symbol]  - positionShort + LOCKPOSITION[symbol]
                                    if self.req.volume > 0:
                                        self.req.offset = unicode(orderHotkey['offset'])
                                        self.widgetTradingW.mainEngine.sendOrder(self.req, gatewayName)
                                    self.req.volume = positionShort - LOCKPOSITION[symbol]
                                    #避免降低锁仓对数时，出现平仓超出预期委托量（根据下单快捷键）
                                    if int(orderHotkey['volume']) * DEFAULT_OPEM[symbol] <= self.req.volume:
                                        self.req.volume = int(orderHotkey['volume']) *  DEFAULT_OPEM[symbol]
                                    #优先平昨
                                    self.req.offset = unicode(orderHotkey['offset'])
                                    if ydPositionShort is not 0:
                                        self.req.offset = u'平昨'
                                        if self.req.volume > shortNetPos and shortNetPos:
                                            content = u'净空持仓不足'
                                            self.mainEngine.writeLog(content)
                                            return
                                    elif ydPositionShort is 0:
                                        self.req.offset = u'平今'
                                    self.widgetTradingW.mainEngine.sendOrder(self.req, gatewayName)
                                else:
                                    self.req.volume = LOCKPOSITION[symbol] - positionLong
                                    if self.req.volume > 0:
                                        self.req.offset = unicode(orderHotkey['offset'])
                                        self.widgetTradingW.mainEngine.sendOrder(self.req, gatewayName)

                                    self.req.volume = int(orderHotkey['volume']) * DEFAULT_OPEM[symbol] - LOCKPOSITION[symbol] + positionLong
                                    # 避免降低锁仓对数时，出现平仓超出预期委托量（根据下单快捷键）
                                    if int(orderHotkey['volume']) * DEFAULT_OPEM[symbol]<= self.req.volume:
                                        self.req.volume = int(orderHotkey['volume']) * DEFAULT_OPEM[symbol]
                                    self.req.offset = unicode(orderHotkey['offset']) * DEFAULT_OPEM[symbol]
                                    # 优先平昨
                                    if ydPositionShort is not 0:
                                        self.req.offset = u'平昨'
                                        if self.req.volume > shortNetPos and shortNetPos:
                                            content = u'净空持仓不足'
                                            self.mainEngine.writeLog(content)
                                            return
                                    elif ydPositionShort is 0:
                                        self.req.offset = u'平今'

                                    self.widgetTradingW.mainEngine.sendOrder(self.req, gatewayName)
                                return

                    # 如果是开空，但是有多单时，优先平多（支持锁仓）
                    elif self.req.symbol == positionDetail.__getattribute__('symbol') and orderHotkey['direction'] == u'空':
                        if positionShort + int(orderHotkey['volume']) * DEFAULT_OPEM[symbol] <= LOCKPOSITION[symbol]:
                            # 优先平昨
                            if ydPositionLong is not 0:
                                self.req.offset = u'平昨'
                                if self.req.volume > longNetPos and longNetPos:
                                    content = u'净多持仓不足'
                                    self.mainEngine.writeLog(content)
                                    return
                            else:
                                self.req.offset = unicode(orderHotkey['offset'])
                            self.widgetTradingW.mainEngine.sendOrder(self.req, gatewayName)
                            return
                        elif positionShort + int(orderHotkey['volume']) * DEFAULT_OPEM[symbol] > LOCKPOSITION[symbol]:
                            if positionLong <= LOCKPOSITION[symbol]:
                                # 优先平昨
                                if ydPositionLong is not 0:
                                    self.req.offset = u'平昨'
                                    if self.req.volume > longNetPos and longNetPos:
                                        content = u'净多持仓不足'
                                        self.mainEngine.writeLog(content)
                                        return
                                else:
                                    self.req.offset = unicode(orderHotkey['offset'])
                                self.widgetTradingW.mainEngine.sendOrder(self.req, gatewayName)
                                return

                            elif positionLong > LOCKPOSITION[symbol]:
                                if positionShort + int(orderHotkey['volume']) * DEFAULT_OPEM[symbol] >= positionLong:
                                    self.req.volume = int(orderHotkey['volume']) * DEFAULT_OPEM[symbol] - positionLong + LOCKPOSITION[
                                        symbol]
                                    if self.req.volume > 0:
                                        self.req.offset = unicode(orderHotkey['offset'])
                                        self.widgetTradingW.mainEngine.sendOrder(self.req, gatewayName)

                                    self.req.volume = positionLong - LOCKPOSITION[symbol]
                                    # 避免降低锁仓对数时，出现平仓超出预期委托量（根据下单快捷键）
                                    if int(orderHotkey['volume']) * DEFAULT_OPEM[symbol] <= self.req.volume:
                                        self.req.volume = int(orderHotkey['volume']) * DEFAULT_OPEM[symbol]
                                    self.req.offset = unicode(orderHotkey['offset'])
                                    # 优先平昨
                                    if ydPositionLong is not 0:
                                        self.req.offset = u'平昨'
                                        if self.req.volume > longNetPos and longNetPos:
                                            content = u'净多持仓不足'
                                            self.mainEngine.writeLog(content)
                                            return
                                    elif ydPositionLong is 0:
                                        self.req.offset = u'平今'
                                    self.widgetTradingW.mainEngine.sendOrder(self.req, gatewayName)
                                else:
                                    self.req.volume = LOCKPOSITION[symbol] - positionShort
                                    if self.req.volume > 0:
                                        self.req.offset = unicode(orderHotkey['offset'])
                                        self.widgetTradingW.mainEngine.sendOrder(self.req, gatewayName)

                                    self.req.volume = int(orderHotkey['volume'])  * DEFAULT_OPEM[symbol] - LOCKPOSITION[symbol] + positionShort
                                    # 避免降低锁仓对数时，出现平仓超出预期委托量（根据下单快捷键）
                                    if int(orderHotkey['volume']) *  DEFAULT_OPEM[symbol] <= self.req.volume:
                                        self.req.volume = int(orderHotkey['volume'])  * DEFAULT_OPEM[symbol]
                                    self.req.offset = unicode(orderHotkey['offset'])
                                    # 优先平昨
                                    if ydPositionLong is not 0:
                                        self.req.offset = u'平昨'
                                        if self.req.volume > longNetPos and longNetPos:
                                            content = u'净多持仓不足'
                                            self.mainEngine.writeLog(content)
                                            return
                                    elif ydPositionLong is 0:
                                        self.req.offset = u'平今'
                                    self.widgetTradingW.mainEngine.sendOrder(self.req, gatewayName)
                                return

    # ----------------------------------------------------------------------
    def initMenu(self):
        """初始化菜单"""
        # 创建菜单
        menubar = self.menuBar()

        # 设计为只显示存在的接口
        gatewayDetails = self.mainEngine.getAllGatewayDetails()

        sysMenu = menubar.addMenu(vtText.SYSTEM)

        for d in gatewayDetails:
            if d['gatewayType'] == GATEWAYTYPE_FUTURES:
                self.addConnectAction(sysMenu, d['gatewayName'], d['gatewayDisplayName'])
        sysMenu.addSeparator()

        for d in gatewayDetails:
            if d['gatewayType'] == GATEWAYTYPE_EQUITY:
                self.addConnectAction(sysMenu, d['gatewayName'], d['gatewayDisplayName'])
        sysMenu.addSeparator()

        for d in gatewayDetails:
            if d['gatewayType'] == GATEWAYTYPE_INTERNATIONAL:
                self.addConnectAction(sysMenu, d['gatewayName'], d['gatewayDisplayName'])
        sysMenu.addSeparator()

        for d in gatewayDetails:
            if d['gatewayType'] == GATEWAYTYPE_BTC:
                self.addConnectAction(sysMenu, d['gatewayName'], d['gatewayDisplayName'])
        sysMenu.addSeparator()

        for d in gatewayDetails:
            if d['gatewayType'] == GATEWAYTYPE_DATA:
                self.addConnectAction(sysMenu, d['gatewayName'], d['gatewayDisplayName'])

        sysMenu.addSeparator()
        sysMenu.addAction(
            self.createAction(vtText.CONNECT_DATABASE, self.mainEngine.dbConnect, loadIconPath('database.ico')))
        sysMenu.addSeparator()
        sysMenu.addAction(self.createAction(vtText.EXIT, self.close, loadIconPath('exit.ico')))

        # 功能应用
        appMenu = menubar.addMenu(vtText.APPLICATION)

        for appDetail in self.appDetailList:
            function = self.createOpenAppFunction(appDetail)
            action = self.createAction(appDetail['appDisplayName'], function, loadIconPath(appDetail['appIco']))
            appMenu.addAction(action)

        # 帮助
        helpMenu = menubar.addMenu(vtText.HELP)
        helpMenu.addAction(self.createAction(vtText.CONTRACT_SEARCH, self.openContract, loadIconPath('contract.ico')))
        helpMenu.addAction(self.createAction(vtText.EDIT_SETTING, self.openSettingEditor, loadIconPath('editor.ico')))
        helpMenu.addSeparator()
        helpMenu.addAction(self.createAction(vtText.RESTORE, self.restoreWindow, loadIconPath('restore.ico')))
        helpMenu.addAction(self.createAction(vtText.ABOUT, self.openAbout, loadIconPath('about.ico')))
        helpMenu.addAction(
            self.createAction(vtText.SUBSCRIBE_DEFAULT, self.openSubscribeDefault, loadIconPath('subscribDefault.ico')))
        helpMenu.addSeparator()
        helpMenu.addAction(self.createAction(vtText.TEST, self.test, loadIconPath('test.ico')))
        helpMenu.addAction(self.createAction(vtText.HOTKEY, self.openHotKeyEditor, loadIconPath('hotkey.ico')))

    # ----------------------------------------------------------------------
    def initStatusBar(self):
        """初始化状态栏"""
        self.statusLabel = QtWidgets.QLabel()
        self.statusLabel.setAlignment(QtCore.Qt.AlignLeft)

        self.statusBar().addPermanentWidget(self.statusLabel)
        self.statusLabel.setText(self.getCpuMemory())

        self.sbCount = 0
        self.sbTrigger = 10  # 10秒刷新一次
        self.signalStatusBar.connect(self.updateStatusBar)
        self.eventEngine.register(EVENT_TIMER, self.signalStatusBar.emit)

    # ----------------------------------------------------------------------
    def updateStatusBar(self, event):
        """在状态栏更新CPU和内存信息"""
        self.sbCount += 1

        if self.sbCount == self.sbTrigger:
            self.sbCount = 0
            self.statusLabel.setText(self.getCpuMemory())

    # ----------------------------------------------------------------------
    def getCpuMemory(self):
        """获取CPU和内存状态信息"""
        cpuPercent = psutil.cpu_percent()
        memoryPercent = psutil.virtual_memory().percent
        return vtText.CPU_MEMORY_INFO.format(cpu=cpuPercent, memory=memoryPercent)

    # ----------------------------------------------------------------------
    def addConnectAction(self, menu, gatewayName, displayName=''):
        """增加连接功能"""
        if gatewayName not in self.gatewayNameList:
            return

        def connect():
            self.mainEngine.connect(gatewayName)

        if not displayName:
            displayName = gatewayName

        actionName = vtText.CONNECT + displayName
        connectAction = self.createAction(actionName, connect,
                                          loadIconPath('connect.ico'))
        menu.addAction(connectAction)

    # ----------------------------------------------------------------------
    def createAction(self, actionName, function, iconPath=''):
        """创建操作功能"""
        action = QtWidgets.QAction(actionName, self)
        action.triggered.connect(function)

        if iconPath:
            icon = QtGui.QIcon(iconPath)
            action.setIcon(icon)

        return action

    # ----------------------------------------------------------------------
    def createOpenAppFunction(self, appDetail):
        """创建打开应用UI的函数"""

        def openAppFunction():
            appName = appDetail['appName']
            try:
                self.widgetDict[appName].show()
            except KeyError:
                appEngine = self.mainEngine.getApp(appName)
                self.widgetDict[appName] = appDetail['appWidget'](appEngine, self.eventEngine)
                self.widgetDict[appName].show()

        return openAppFunction

    # ----------------------------------------------------------------------
    def test(self):
        """测试按钮用的函数"""
        # 有需要使用手动触发的测试函数可以写在这里
        pass

    # ----------------------------------------------------------------------
    def openAbout(self):
        """打开关于"""
        try:
            self.widgetDict['aboutW'].show()
        except KeyError:
            self.widgetDict['aboutW'] = AboutWidget(self)
            self.widgetDict['aboutW'].show()

    # ----------------------------------------------------------------------
    def openContract(self):
        """打开合约查询"""
        try:
            self.widgetDict['contractM'].show()
        except KeyError:
            self.widgetDict['contractM'] = ContractManager(self.mainEngine)
            self.widgetDict['contractM'].show()

    # ----------------------------------------------------------------------
    def openSettingEditor(self):
        """打开配置编辑"""
        try:
            self.widgetDict['settingEditor'].show()
        except KeyError:
            self.widgetDict['settingEditor'] = SettingEditor(self.mainEngine)
            self.widgetDict['settingEditor'].show()

    # ----------------------------------------------------------------------
    def openSubscribeDefault(self):
        """打开默认订阅编辑"""
        try:
            self.widgetDict['subscribeDefault'].show()
        except KeyError:
            self.widgetDict['subscribeDefault'] = SubscribeDefaultWidget(self)
            self.widgetDict['subscribeDefault'].show()

    # ----------------------------------------------------------------------
    def openHotKeyEditor(self):
        """打开快捷键编辑"""
        try:
            self.widgetDict['hotKeyEditor'].show()
        except KeyError:
            self.widgetDict['hotKeyEditor'] = HotKeyWidget(self)
            self.widgetDict['hotKeyEditor'].show()

    # ----------------------------------------------------------------------
    def closeEvent(self, event):
        """关闭事件"""
        reply = QtWidgets.QMessageBox.question(self, vtText.EXIT,
                                               vtText.CONFIRM_EXIT, QtWidgets.QMessageBox.Yes |
                                               QtWidgets.QMessageBox.No, QtWidgets.QMessageBox.No)

        if reply == QtWidgets.QMessageBox.Yes:
            for widget in self.widgetDict.values():
                widget.close()
            self.saveWindowSettings('custom')

            self.mainEngine.exit()
            event.accept()
        else:
            event.ignore()

    # ----------------------------------------------------------------------
    def createDock(self, widgetClass, widgetName, widgetArea):
        """创建停靠组件"""
        widget = widgetClass(self.mainEngine, self.eventEngine)
        dock = QtWidgets.QDockWidget(widgetName)
        dock.setWidget(widget)
        dock.setObjectName(widgetName)
        dock.setFeatures(dock.DockWidgetFloatable | dock.DockWidgetMovable)
        self.addDockWidget(widgetArea, dock)
        return widget, dock

    # ----------------------------------------------------------------------
    def saveWindowSettings(self, settingName):
        """保存窗口设置"""
        settings = QtCore.QSettings('vn.trader', settingName)
        settings.setValue('state', self.saveState())
        settings.setValue('geometry', self.saveGeometry())

    # ----------------------------------------------------------------------
    def loadWindowSettings(self, settingName):
        """载入窗口设置"""
        settings = QtCore.QSettings('vn.trader', settingName)
        state = settings.value('state')
        geometry = settings.value('geometry')

        # 尚未初始化
        if state is None:
            return
        # 老版PyQt
        elif isinstance(state, QtCore.QVariant):
            self.restoreState(state.toByteArray())
            self.restoreGeometry(geometry.toByteArray())
        # 新版PyQt
        elif isinstance(state, QtCore.QByteArray):
            self.restoreState(state)
            self.restoreGeometry(geometry)
        # 异常
        else:
            content = u'载入窗口配置异常，请检查'
            self.mainEngine.writeLog(content)

    # ----------------------------------------------------------------------
    def restoreWindow(self):
        """还原默认窗口设置（还原停靠组件位置）"""
        self.loadWindowSettings('default')
        self.showMaximized()


########################################################################
class AboutWidget(QtWidgets.QDialog):
    """显示关于信息"""

    # ----------------------------------------------------------------------
    def __init__(self, parent=None):
        """Constructor"""
        super(AboutWidget, self).__init__(parent)

        self.initUi()

    # ----------------------------------------------------------------------
    def initUi(self):
        """"""
        self.setWindowTitle(vtText.ABOUT + 'VnTrader')

        text = u"""
            Developed by Traders, for Traders.

            License：MIT

            Website：www.vnpy.org

            Github：www.github.com/vnpy/vnpy

            """

        label = QtWidgets.QLabel()
        label.setText(text)
        label.setMinimumWidth(500)

        vbox = QtWidgets.QVBoxLayout()
        vbox.addWidget(label)

        self.setLayout(vbox)




