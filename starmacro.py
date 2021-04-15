from PySide import QtCore, QtGui
import Part

from pivy.coin import *
import FreeCAD as App
import FreeCADGui as Gui
import Sketcher, math

class Ui_Dialog(object):
   def setupUi(self, Dialog):
       #print('In SetupUI')
       Dialog.setObjectName("Dialog")
       Dialog.resize(187, 178)
       self.title = QtGui.QLabel(Dialog)
       self.title.setGeometry(QtCore.QRect(10, 10, 271, 16))
       self.title.setObjectName("title")
       self.label_npoints = QtGui.QLabel(Dialog)
       self.label_npoints.setGeometry(QtCore.QRect(10, 90, 57, 16))
       self.label_npoints.setObjectName("label_npoints")
       self.npoints = QtGui.QLineEdit(Dialog)
       self.npoints.setGeometry(QtCore.QRect(60, 80, 111, 26))
       self.npoints.setObjectName("npoints")
       self.create = QtGui.QPushButton(Dialog)
       self.create.setGeometry(QtCore.QRect(50, 140, 83, 26))
       self.create.setObjectName("create")

       self.retranslateUi(Dialog)
       QtCore.QObject.connect(self.create,QtCore.SIGNAL("pressed()"),self.createStar)
       QtCore.QMetaObject.connectSlotsByName(Dialog)

   def retranslateUi(self, Dialog):
       Dialog.setWindowTitle("Dialog")
       self.title.setText("Star creator")
       self.label_npoints.setText("No. Pts.")
       self.create.setText("OK")

   def createStar(self):
       try:
           # first we check if valid numbers have been entered
           ns = int(self.npoints.text())
           print('Read ns')
       except ValueError:
           print("Error! No. of sides must be an integer!")
       else:
           print('no. points', ns)
           starpts(ns)
           
           

class star():
  def __init__(self):
      self.d = QtGui.QWidget()
      self.ui = Ui_Dialog()
#      print('In star')
      self.ui.setupUi(self.d)
#      print('In star, setupUi done')
#      print('Has show mwthod', dir(self.d).__contains__('show'))
      self.d.show()
#      print('In star, showing widget done')




class starpts():

    """This class will create a star after the user clicked 2 points on the screen"""

    def __init__(self, nsides):
#        print('In starpts')
        self.view = Gui.ActiveDocument.ActiveView
        self.stack = []
        self.nsides = nsides
        self.callback = self.view.addEventCallbackPivy(SoMouseButtonEvent.getClassTypeId(), self.getpoint)

    def getpoint(self, event_cb):
        event = event_cb.getEvent()
        if event.getState() == SoMouseButtonEvent.DOWN:
            pos = event.getPosition()
            point = self.view.getPoint(pos[0], pos[1])
            self.stack.append(point)
            if len(self.stack) == 2:
                print('center',self.stack[0], 'vertex',self.stack[1])
               # l = Part.LineSegment(self.stack[0], self.stack[1])
               # shape = l.toShape()
               # Part.show(shape)
                self.view.removeEventCallbackPivy(SoMouseButtonEvent.getClassTypeId(), self.callback)
                construction = False
                sk = Gui.ActiveDocument.getInEdit().Object
                centerPoint = self.stack[0]
                firstCornerPoint = self.stack[1]
                self.makeRegularStar(sk, self.nsides, centerPoint, firstCornerPoint, construction)
                sk.recompute()
    
    @staticmethod
    def makeRegularStar(
        sketch, 
        sides, 
        centerPoint=App.Vector(0,0,0), 
        firstCornerPoint=App.Vector(-20.00,34.64,0),
        construction=False):

        if not sketch:
            App.Console.PrintError("No sketch specified in 'makeRegularStar'")
            return
        if sides < 2:
            App.Console.PrintError("Number of sides must be at least 2 in 'makeRegularStar'")
            return

        diffVec = firstCornerPoint - centerPoint
        diffVec.z = 0
        angular_diff = 2*math.pi/sides
        pointListOuter = []
        for i in range(0,sides):
            cos_v = math.cos( angular_diff * i )
            sin_v = math.sin( angular_diff * i )
            pointListOuter.append( centerPoint+
            App.Vector(
               cos_v * diffVec.x - sin_v * diffVec.y,
               cos_v * diffVec.y + sin_v * diffVec.x,
               0 ))
        pointListInner = []
        for i in range(0,sides):
            cos_v = math.cos( angular_diff * (i + 0.5) )
            sin_v = math.sin( angular_diff * (i + 0.5) )
            pointListInner.append( centerPoint+
            App.Vector(
               0.5*(cos_v * diffVec.x - sin_v * diffVec.y),
               0.5*(cos_v * diffVec.y + sin_v * diffVec.x),
               0 ))

        geoList = []
        for i in range(0,sides-1): 
            geoList.append(Part.LineSegment(pointListOuter[i],pointListInner[i]))
            geoList.append(Part.LineSegment(pointListInner[i],pointListOuter[i+1]))
        geoList.append(Part.LineSegment(pointListOuter[sides-1],pointListInner[sides-1]))
        geoList.append(Part.LineSegment(pointListInner[sides-1],pointListOuter[0]))
        geoList.append(Part.Circle(centerPoint,App.Vector(0,0,1),diffVec.Length))
        geoList.append(Part.Circle(centerPoint,App.Vector(0,0,1),0.4*diffVec.Length))
        geoIndices = sketch.addGeometry(geoList,construction)

        sketch.setConstruction(geoIndices[-1],True)
        sketch.setConstruction(geoIndices[-2],True)
        #print(geoList)
        #geoList is 2*sides line segments, the outer then inner construction circles
        conList = []
        #sides all equal
        for i in range(0,2*sides-1):
            conList.append(Sketcher.Constraint('Equal',geoIndices[0],geoIndices[i+1]))
        #print(conList)
        #put vertices on construction circles
        for i in range(0,2*sides,2):
            conList.append(Sketcher.Constraint('PointOnObject',geoIndices[i],2,geoIndices[-2]))
            conList.append(Sketcher.Constraint('PointOnObject',geoIndices[i+1],2,geoIndices[-1]))
        #print(conList)
        #glue line segments
        for i in range(0,2*sides-1):
            conList.append(Sketcher.Constraint(
                'Coincident', geoIndices[i],2, geoIndices[i+1],1))
        conList.append(Sketcher.Constraint(
            'Coincident', geoIndices[2*sides-1],2, geoIndices[0],1))
        #circle centers coincident
        conList.append(Sketcher.Constraint(
            'Coincident', geoIndices[2*sides],3, geoIndices[2*sides+1],3))
        #print(conList)
        sketch.addConstraint(conList)
        return

#print("Starting execution")
st = star()

