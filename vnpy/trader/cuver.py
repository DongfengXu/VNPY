import pyqtgraph as pg

def enableCrossHairs(self, plot, curves=[]):
    """
    Enables crosshairs on the specified plot

    .. tabularcolumns:: |p{3cm}|p{11cm}|

    ===============  ============================================================================================
    **Arguments**
    ===============  ============================================================================================
    plot             The plot to activate this feature on
    ===============  ============================================================================================
    """

    plot.setTitle('')
    vLine = pg.InfiniteLine(angle=90, movable=False, pen=[100, 100, 200, 200])
    plot.addItem(vLine, ignoreBounds=True)
    hLine = pg.InfiniteLine(angle=0, movable=False, pen=[100, 100, 200, 200])
    plot.addItem(hLine, ignoreBounds=True)
    plot.hLine = hLine;
    plot.vLine = vLine
    crossHairPartial = functools.partial(self.crossHairEvent, plot)
    proxy = pg.SignalProxy(plot.scene().sigMouseClicked, rateLimit=60, slot=crossHairPartial)
    plot.proxy = proxy
    plot.mousePoint = None

enableCrossHairs()